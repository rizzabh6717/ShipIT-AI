"""Candidate ranking for AI parcel-driver matching.

Two ranking strategies:

- ``heuristic`` : deterministic, explainable scoring (no API key needed).
- ``llm``      : LangChain ChatOpenAI over OpenRouter/OpenAI that re-ranks
                 candidates and returns structured JSON. Falls back to the
                 heuristic ranking on any failure so the endpoint is robust.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from app.ai.explainer import ScoreBreakdown, breakdown, estimate_eta, reasons
from app.config import settings
from app.models.driver import Driver
from app.models.parcel import Parcel
from app.models.route import Route


@dataclass
class Candidate:
    driver: Driver
    route: Route | None = None
    route_similarity: float = 0.0
    route_overlap: float = 0.0
    pickup_detour_km: float = 0.0


@dataclass
class RankedResult:
    driver: Driver
    score: float
    eta: str
    reason: list[str]
    breakdown: ScoreBreakdown | None = None


def _score(candidate: Candidate, parcel: Parcel) -> tuple[ScoreBreakdown, float]:
    bd = breakdown(
        parcel=parcel,
        driver=candidate.driver,
        route=candidate.route,
        route_overlap=candidate.route_overlap,
        pickup_detour_km=candidate.pickup_detour_km,
    )
    # Keep full precision: rounding to 2dp creates false ties between near-equal
    # candidates that an arbitrary tie-break then resolves non-semantically.
    return bd, min(1.0, max(0.0, bd.total))


def rank_heuristic(parcel: Parcel, candidates: list[Candidate]) -> list[RankedResult]:
    """Deterministic, fully explainable ranking."""
    results: list[RankedResult] = []
    for candidate in candidates:
        bd, score = _score(candidate, parcel)
        results.append(
            RankedResult(
                driver=candidate.driver,
                score=score,
                eta=estimate_eta(candidate.pickup_detour_km),
                reason=reasons(bd, parcel, candidate.driver),
                breakdown=bd,
            )
        )
    return sorted(
        results,
        key=lambda r: (r.score, r.driver.public_id),
        reverse=True,
    )


def _candidate_feature(c: Candidate, parcel: Parcel) -> dict:
    return {
        "driver_id": c.driver.public_id,
        "vehicle_type": c.driver.vehicle_type.value,
        "capacity_kg": c.driver.capacity_kg,
        "rating": c.driver.rating,
        "on_time_rate": c.driver.on_time_rate,
        "completion_rate": c.driver.completion_rate,
        "route_overlap_pct": round(c.route_overlap * 100),
        "pickup_detour_km": c.pickup_detour_km,
        "current_city": c.driver.current_city,
    }


async def rank_with_llm(parcel: Parcel, candidates: list[Candidate]) -> list[RankedResult]:
    """Rank candidates with an LLM through LangChain (OpenRouter/OpenAI)."""
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_openai import ChatOpenAI

    heuristic_results = rank_heuristic(parcel, candidates)
    if not candidates:
        return heuristic_results

    llm = ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url or None,
        temperature=settings.llm_temperature,
        model_kwargs={"response_format": {"type": "json_object"}},
    )

    parcel_desc = (
        f"Parcel {parcel.public_id}: from {parcel.pickup_location} to {parcel.drop_location}, "
        f"{parcel.weight}kg, budget {parcel.budget:.2f}, "
        f"deadline {parcel.deadline.isoformat() if parcel.deadline else 'flexible'}, "
        f"description: {parcel.item_description}"
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an expert logistics dispatcher. Rank the candidate drivers for the "
                "given parcel. Consider route overlap, pickup distance, delivery deadline, "
                "driver reliability, vehicle capacity, and estimated detour. "
                "Return ONLY JSON: {{\"matches\": [{{\"driver_id\": str, \"score\": float 0..1, "
                "\"eta\": str, \"reason\": [str]}}]}} sorted best first.",
            ),
            (
                "human",
                f"PARCEL:\n{parcel_desc}\n\nCANDIDATE DRIVERS:\n"
                + json.dumps([_candidate_feature(c, parcel) for c in candidates], indent=2),
            ),
        ]
    )

    try:
        response = await (prompt | llm).ainvoke({})
        content = response.content if isinstance(response.content, str) else json.dumps(response.content)
        data = json.loads(content)
        by_id = {c.driver.public_id: c for c in candidates}
        llm_results: list[RankedResult] = []
        for item in data.get("matches", []):
            cand = by_id.get(item.get("driver_id"))
            if cand is None:
                continue
            bd, _ = _score(cand, parcel)
            llm_results.append(
                RankedResult(
                    driver=cand.driver,
                    score=round(min(1.0, max(0.0, float(item.get("score", 0)))), 2),
                    eta=item.get("eta") or estimate_eta(cand.pickup_detour_km),
                    reason=item.get("reason") or reasons(bd, parcel, cand.driver),
                    breakdown=bd,
                )
            )
        if llm_results:
            return llm_results
    except Exception:  # pragma: no cover - defensive fallback
        pass

    return heuristic_results


async def rank(parcel: Parcel, candidates: list[Candidate]) -> tuple[list[RankedResult], str]:
    """Entry point: choose the ranking strategy from settings."""
    provider = settings.llm_provider.lower()
    if provider in {"openrouter", "openai"} and settings.llm_api_key:
        results = await rank_with_llm(parcel, candidates)
        return results, "ai"
    return rank_heuristic(parcel, candidates), "heuristic"
