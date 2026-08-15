"""Pure evaluation metrics for the AI matching engine.

These functions are dependency-free so they can be unit-tested offline and
reused by both the CLI runner and CI.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field


@dataclass
class CaseResult:
    """The outcome of one evaluation test case."""

    case_id: str
    name: str
    expected: str
    acceptable: list[str] = field(default_factory=list)
    retrieved: list[str] = field(default_factory=list)
    predicted: list[str] = field(default_factory=list)
    predicted_scores: list[float] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    ranked_by: str = ""
    retrieval_ms: float = 0.0
    ranking_ms: float = 0.0
    total_ms: float = 0.0
    pickup_location: str = ""
    drop_location: str = ""


@dataclass
class EvalMetrics:
    """Aggregate metrics over a set of test cases."""

    num_cases: int
    top1_accuracy: float
    top3_accuracy: float
    mrr: float
    avg_match_score: float
    avg_retrieval_ms: float
    avg_ranking_ms: float
    avg_total_ms: float
    expected_retrieved_rate: float
    avg_candidates: float
    correct_count: int


def reciprocal_rank(predicted: list[str], expected: str) -> float:
    """1/rank of the expected driver, or 0.0 if it is not predicted."""
    for i, driver_id in enumerate(predicted, start=1):
        if driver_id == expected:
            return 1.0 / i
    return 0.0


def is_in_top_k(predicted: list[str], expected: str, k: int) -> bool:
    """True if the expected driver appears in the top ``k`` predictions."""
    if k <= 0:
        return False
    return expected in predicted[:k]


def expected_was_retrieved(retrieved: list[str], expected: str) -> bool:
    """True if the expected driver survived the retrieval phase."""
    return expected in retrieved


def mean(values: list[float]) -> float:
    """Arithmetic mean, 0.0 for an empty list."""
    if not values:
        return 0.0
    return statistics.fmean(values)


def compute_metrics(cases: list[CaseResult]) -> EvalMetrics:
    """Aggregate the required headline metrics from per-case results.

    - Top-1 / Top-3 accuracy: fraction where the expected best driver is
      ranked first / inside the top three.
    - MRR: mean reciprocal rank of the expected driver.
    - Avg match score: mean of the top-1 predicted driver's score.
    - Latencies: mean retrieval / ranking / total pipeline time.
    - Expected-retrieved rate: coverage of the expected driver by retrieval.
    """
    if not cases:
        return EvalMetrics(num_cases=0, top1_accuracy=0.0, top3_accuracy=0.0,
                           mrr=0.0, avg_match_score=0.0, avg_retrieval_ms=0.0,
                           avg_ranking_ms=0.0, avg_total_ms=0.0,
                           expected_retrieved_rate=0.0, avg_candidates=0.0,
                           correct_count=0)

    top1 = sum(is_in_top_k(c.predicted, c.expected, 1) for c in cases)
    top3 = sum(is_in_top_k(c.predicted, c.expected, 3) for c in cases)
    rr = [reciprocal_rank(c.predicted, c.expected) for c in cases]
    scores = [c.predicted_scores[0] for c in cases if c.predicted_scores]
    retrieved_rate = sum(expected_was_retrieved(c.retrieved, c.expected) for c in cases)

    return EvalMetrics(
        num_cases=len(cases),
        top1_accuracy=top1 / len(cases),
        top3_accuracy=top3 / len(cases),
        mrr=mean(rr),
        avg_match_score=mean(scores),
        avg_retrieval_ms=mean([c.retrieval_ms for c in cases]),
        avg_ranking_ms=mean([c.ranking_ms for c in cases]),
        avg_total_ms=mean([c.total_ms for c in cases]),
        expected_retrieved_rate=retrieved_rate / len(cases),
        avg_candidates=mean([float(len(c.retrieved)) for c in cases]),
        correct_count=int(top1),
    )
