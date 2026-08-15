"""Orchestrates the AI parcel-driver matching pipeline.

Flow:
  1. Build the parcel's text representation and embed it.
  2. Retrieve candidate routes via pgvector cosine similarity (HNSW).
     Falls back to token-overlap search when no embeddings exist yet.
  3. Rank candidates — via LLM (OpenRouter/OpenAI) or the deterministic,
     fully-explainable heuristic.
  4. Persist top matches for transparency/history.
  5. Return structured, human-readable match results.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.embeddings import get_embedder
from app.ai.matcher import Candidate, RankedResult, rank
from app.ai.vector_store import (
    search_routes_by_embedding,
    search_routes_fallback,
)
from app.config import settings
from app.models.match import Match
from app.models.parcel import Parcel
from app.schemas.ai import MatchResult, MatchResponse
from app.schemas.driver import DriverRead
from app.services.ai_service import parcel_to_text
from app.utils.geo import estimate_pickup_detour_km, geographic_route_overlap


class MatchingService:
    """End-to-end AI matching pipeline for a parcel."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def retrieve_candidates(self, parcel: Parcel) -> list[Candidate]:
        """Phase 1 — candidate retrieval. Public so evaluation harnesses and
        observability tooling can time retrieval and ranking separately."""
        parcel_text = parcel_to_text(parcel)
        embedder = get_embedder()
        parcel_vector = (await embedder.embed([parcel_text]))[0]

        hits = await search_routes_by_embedding(
            self.session, parcel_vector, top_k=settings.ai_match_top_k
        )
        if not hits:
            hits = await search_routes_fallback(
                self.session,
                parcel.pickup_location,
                parcel.drop_location,
                top_k=settings.ai_match_top_k,
            )

        candidates: list[Candidate] = []
        for hit in hits:
            route = hit.route
            driver = route.driver
            detour = estimate_pickup_detour_km(parcel, route)
            candidates.append(
                Candidate(
                    driver=driver,
                    route=route,
                    # Embedding similarity is a recall signal (which routes are
                    # worth ranking); the reported/scored "route overlap" is
                    # computed geographically from the actual origin/destination.
                    route_similarity=hit.similarity,
                    route_overlap=geographic_route_overlap(parcel, route),
                    pickup_detour_km=detour,
                )
            )
        return candidates

    async def _persist(self, parcel: Parcel, results: list[RankedResult]) -> None:
        for result in results:
            existing = await self.session.scalar(
                select(Match).where(
                    Match.parcel_id == parcel.id,
                    Match.driver_id == result.driver.id,
                )
            )
            if existing is None:
                existing = Match(parcel_id=parcel.id, driver_id=result.driver.id)
                self.session.add(existing)
            existing.match_score = result.score
            existing.eta = result.eta
            existing.explanation = "\n".join(result.reason)

    async def match_parcel(self, parcel: Parcel, max_results: int | None = None) -> MatchResponse:
        """Run the full pipeline for a parcel and persist/return matches."""
        max_results = max_results or settings.ai_match_max_results
        candidates = await self.retrieve_candidates(parcel)
        ranked, ranked_by = await rank(parcel, candidates)
        # A driver can surface multiple candidate routes; keep their best score
        # so we never persist/return duplicate (parcel, driver) rows.
        best: dict[int, RankedResult] = {}
        for result in ranked:
            prev = best.get(result.driver.id)
            if prev is None or result.score > prev.score:
                best[result.driver.id] = result
        top = sorted(best.values(), key=lambda r: r.score, reverse=True)[:max_results]

        if top:
            await self._persist(parcel, top)
            await self.session.flush()

        matches = [
            MatchResult(
                driver_id=result.driver.public_id,
                score=result.score,
                overlap=(result.breakdown.route_overlap if result.breakdown else 0.0),
                eta=result.eta,
                reason=result.reason,
                detour_km=(result.breakdown.pickup_detour_km if result.breakdown else 0.0),
                driver=DriverRead.model_validate(result.driver),
            )
            for result in top
        ]

        return MatchResponse(
            parcel_id=parcel.public_id,
            matches=matches,
            model=settings.llm_model if ranked_by == "ai" else None,
            provider=settings.llm_provider,
            ranked_by=ranked_by,
        )
