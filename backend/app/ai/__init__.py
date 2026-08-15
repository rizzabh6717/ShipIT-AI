"""AI subsystem: embeddings, vector search, explainable matching."""

from app.ai.embeddings import BaseEmbedder, DeterministicEmbedder, OpenAICompatEmbedder, get_embedder
from app.ai.explainer import ScoreBreakdown, breakdown, estimate_eta, reasons
from app.ai.matcher import Candidate, RankedResult, rank, rank_heuristic, rank_with_llm
from app.ai.vector_store import RouteHit, search_routes_by_embedding, search_routes_fallback

__all__ = [
    "BaseEmbedder",
    "Candidate",
    "DeterministicEmbedder",
    "OpenAICompatEmbedder",
    "RankedResult",
    "RouteHit",
    "ScoreBreakdown",
    "breakdown",
    "estimate_eta",
    "get_embedder",
    "rank",
    "rank_heuristic",
    "rank_with_llm",
    "reasons",
    "search_routes_by_embedding",
    "search_routes_fallback",
]
