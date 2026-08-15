"""Report builders: structured JSON + human-readable Markdown evaluation reports.

Kept as pure functions of a report dict so they can be unit-tested offline.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from evals.metrics import CaseResult, EvalMetrics

REPORT_SCHEMA_VERSION = "1.0"

_RECOMMENDATIONS = [
    "Deterministic mode is fully offline, zero-cost, and reproducible — keep it as the production default for cost-sensitive or air-gapped deployments.",
    "LLM re-ranking only adds value on the ambiguous / near-tie cases; gate it to the top retrieval results so cost stays bounded (retrieval-first keeps the LLM call small).",
    "Route embeddings are refreshed on creation only. Periodically re-embed (POST /routes/me/embed) after drivers update their routes.",
    "The pickup-detour signal currently falls back to token-overlap when GPS is absent. Adding geocoded waypoints should improve the tie-break cases.",
    "Track match outcomes (accept/reject per ranked driver) in production to build a labeled feedback loop that this offline dataset cannot capture.",
]


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def build_report_dict(
    *,
    mode: str,
    mode_used: str,
    metrics: EvalMetrics,
    cases: list[CaseResult],
    dataset_meta: dict,
    configuration: dict,
    llm_fallback_note: str | None = None,
    comparison: dict | None = None,
    example_ids: list[str] | None = None,
) -> dict:
    """Assemble the complete report structure (JSON-serializable)."""
    correct = [c for c in cases if c.predicted and c.predicted[0] == c.expected]
    incorrect = [c for c in cases if not (c.predicted and c.predicted[0] == c.expected)]
    correct.sort(key=lambda c: c.predicted_scores[0] if c.predicted_scores else 0.0, reverse=True)
    incorrect.sort(key=lambda c: c.total_ms, reverse=True)

    selected = list(example_ids or [])
    example_cases = [c for c in cases if c.case_id in selected]

    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "mode": mode,
        "mode_used": mode_used,
        "llm_fallback_note": llm_fallback_note,
        "dataset": dataset_meta,
        "configuration": configuration,
        "metrics": {
            "num_cases": metrics.num_cases,
            "top1_accuracy": round(metrics.top1_accuracy, 4),
            "top3_accuracy": round(metrics.top3_accuracy, 4),
            "mrr": round(metrics.mrr, 4),
            "avg_match_score": round(metrics.avg_match_score, 4),
            "expected_retrieved_rate": round(metrics.expected_retrieved_rate, 4),
            "correct_count": metrics.correct_count,
        },
        "latency_ms": {
            "avg_retrieval_ms": round(metrics.avg_retrieval_ms, 2),
            "avg_ranking_ms": round(metrics.avg_ranking_ms, 2),
            "avg_total_ms": round(metrics.avg_total_ms, 2),
            "avg_candidates": round(metrics.avg_candidates, 2),
        },
        "comparison": comparison,
        "per_case": [
            {
                "case_id": c.case_id,
                "name": c.name,
                "expected": c.expected,
                "acceptable": c.acceptable,
                "retrieved_count": len(c.retrieved),
                "predicted": [
                    {"driver_id": did, "score": score}
                    for did, score in zip(c.predicted, c.predicted_scores)
                ],
                "top1_correct": bool(c.predicted and c.predicted[0] == c.expected),
                "expected_in_top3": c.expected in c.predicted[:3],
                "reciprocal_rank": round(
                    1.0 / (c.predicted.index(c.expected) + 1)
                    if c.expected in c.predicted
                    else 0.0,
                    4,
                ),
                "ranked_by": c.ranked_by,
                "retrieval_ms": round(c.retrieval_ms, 2),
                "ranking_ms": round(c.ranking_ms, 2),
                "total_ms": round(c.total_ms, 2),
            }
            for c in cases
        ],
        "successes": [_case_label(c) for c in correct[:5]],
        "failures": [_case_label(c) for c in incorrect[:5]],
        "examples": [
            {
                "case_id": c.case_id,
                "name": c.name,
                "parcel": _parcel_summary(c),
                "expected": c.expected,
                "acceptable": c.acceptable,
                "predicted": [
                    {"rank": i, "driver_id": did, "score": score}
                    for i, (did, score) in enumerate(zip(c.predicted, c.predicted_scores), start=1)
                ],
                "reasons": c.reasons,
                "top1_correct": bool(c.predicted and c.predicted[0] == c.expected),
            }
            for c in example_cases
        ],
        "recommendations": list(_RECOMMENDATIONS),
    }


def _parcel_summary(case: CaseResult) -> str:
    if case.pickup_location and case.drop_location:
        return f"{case.pickup_location} \u2192 {case.drop_location}"
    return case.name


def _case_label(case: CaseResult) -> str:
    return f"{case.case_id} ({case.name})"


def _fmt_pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def _fmt_ms(value: float) -> str:
    return f"{value:.1f} ms"


def _fmt_score(value: float) -> str:
    return f"{value:.2f}"


def build_markdown(report: dict) -> str:
    """Render the report dict as a Markdown document."""
    m = report["metrics"]
    lat = report["latency_ms"]
    cfg = report["configuration"]
    ds = report["dataset"]

    lines: list[str] = []
    lines.append("# ShipIT AI Matching Evaluation Report")
    lines.append("")
    lines.append(f"- **Generated:** {report['generated_at']}")
    lines.append(f"- **Mode:** {report['mode']} (used: `{report['mode_used']}`)")
    if report.get("llm_fallback_note"):
        lines.append(f"- **Note:** {report['llm_fallback_note']}")
    lines.append(f"- **Dataset:** `{ds.get('path', 'matching_eval.json')}` v{ds.get('version')}")
    lines.append(f"- **Test cases:** {m['num_cases']}")
    lines.append(f"- **Embedding:** {cfg.get('embedding_provider')} "
                 f"({cfg.get('embedding_model')}, dim {cfg.get('embedding_dimensions')})")
    lines.append(f"- **Ranking:** {cfg.get('llm_provider')} ({cfg.get('llm_model')})")
    lines.append("")

    # Metrics table
    lines.append("## Metrics")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Top-1 Accuracy | {_fmt_pct(m['top1_accuracy'])} ({m['correct_count']}/{m['num_cases']}) |")
    lines.append(f"| Top-3 Accuracy | {_fmt_pct(m['top3_accuracy'])} |")
    lines.append(f"| Mean Reciprocal Rank (MRR) | {m['mrr']:.3f} |")
    lines.append(f"| Average Match Score (top-1) | {_fmt_score(m['avg_match_score'])} |")
    lines.append(f"| Expected driver retrieved | {_fmt_pct(m['expected_retrieved_rate'])} |")
    lines.append("")

    # Latency table
    lines.append("## Latency")
    lines.append("")
    lines.append("| Phase | Average |")
    lines.append("|-------|---------|")
    lines.append(f"| Retrieval (embed + pgvector/HNSW) | {_fmt_ms(lat['avg_retrieval_ms'])} |")
    lines.append(f"| Ranking | {_fmt_ms(lat['avg_ranking_ms'])} |")
    lines.append(f"| Total pipeline | {_fmt_ms(lat['avg_total_ms'])} |")
    lines.append(f"| Candidates retrieved | {lat['avg_candidates']} |")
    lines.append("")

    # Comparison table
    comp = report.get("comparison")
    if comp and any(v is not None for v in comp.values()):
        lines.append("## Deterministic vs LLM Re-ranking")
        lines.append("")
        lines.append("| Mode | Top-1 | Top-3 | MRR | Avg Match Score | Avg Total Latency |")
        lines.append("|------|-------|-------|-----|-----------------|-------------------|")
        for key in ("deterministic", "llm"):
            row = comp.get(key)
            label = {"deterministic": "Deterministic", "llm": "LLM Re-rank"}.get(key, key.title())
            if row is None:
                lines.append(f"| {label} | n/a | n/a | n/a | n/a | n/a |")
            else:
                lines.append(
                    f"| {label} | {_fmt_pct(row['top1_accuracy'])} | "
                    f"{_fmt_pct(row['top3_accuracy'])} | {row['mrr']:.3f} | "
                    f"{_fmt_score(row['avg_match_score'])} | {_fmt_ms(row['avg_total_ms'])} |"
                )
        lines.append("")

    # Per-case table
    lines.append("## Per-Case Results")
    lines.append("")
    lines.append("| Case | Scenario | Expected | Top-1 | Top-3 | RR | Latency |")
    lines.append("|------|----------|----------|-------|-------|-----|---------|")
    for row in report["per_case"]:
        top1 = ":white_check_mark:" if row["top1_correct"] else ":x:"
        top3 = ":white_check_mark:" if row["expected_in_top3"] else ":x:"
        lines.append(
            f"| {row['case_id']} | {row['name']} | {row['expected']} | {top1} | {top3} | "
            f"{row['reciprocal_rank']:.3f} | {_fmt_ms(row['total_ms'])} |"
        )
    lines.append("")

    # Successes / failures
    lines.append("## Successes")
    lines.append("")
    if report["successes"]:
        lines.append(", ".join(report["successes"]))
    else:
        lines.append("_None_")
    lines.append("")
    lines.append("## Failures")
    lines.append("")
    if report["failures"]:
        lines.append(", ".join(report["failures"]))
    else:
        lines.append("_None_")
    lines.append("")

    # Interview-ready examples
    lines.append("## Interview-Ready Examples (Explainability)")
    lines.append("")
    for i, ex in enumerate(report["examples"], start=1):
        lines.append(f"### Example {i} — {ex['name']}")
        lines.append("")
        lines.append(f"**Parcel:** {ex['parcel']}")
        lines.append("")
        lines.append(f"**Expected Driver:** {ex['expected']}")
        if ex.get("acceptable"):
            lines.append(f"**Acceptable Drivers:** {', '.join(ex['acceptable'])}")
        lines.append("")
        lines.append("**Predicted Ranking:**")
        lines.append("")
        for p in ex["predicted"]:
            lines.append(f"{p['rank']}. {p['driver_id']} ({_fmt_score(p['score'])})")
        lines.append("")
        lines.append("**Reason** (top match):")
        lines.append("")
        for r in ex["reasons"]:
            lines.append(f"- {r}")
        verdict = "correct" if ex["top1_correct"] else "incorrect (see failures section)"
        lines.append("")
        lines.append(f"*Verdict: top-1 prediction is **{verdict}**.*")
        lines.append("")

    # Recommendations
    lines.append("## Recommendations")
    lines.append("")
    for r in report["recommendations"]:
        lines.append(f"- {r}")
    lines.append("")

    # Reproducibility
    lines.append("## Reproducibility")
    lines.append("")
    lines.append("```")
    lines.append(f"python backend/evals/evaluate_matching.py --mode {report['mode']}")
    lines.append("```")
    lines.append("")
    lines.append("The dataset is version-controlled and seeded into a disposable "
                "`shipit_eval` database with a fixed deterministic embedding; "
                "reruns are bit-for-bit reproducible in deterministic mode.")

    return "\n".join(lines)


def write_reports(report: dict, results_dir: Path) -> tuple[Path, Path]:
    """Write latest_results.json and latest_results.md, returning their paths."""
    import json

    results_dir.mkdir(parents=True, exist_ok=True)

    json_path = results_dir / "latest_results.json"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    md_path = results_dir / "latest_results.md"
    md_path.write_text(build_markdown(report), encoding="utf-8")

    return json_path, md_path
