"""Unit tests for the matching-evaluation framework utilities.

These tests are pure and offline — no database, no network. They cover the
metric math, dataset validation, and report builders that power
``evals/evaluate_matching.py``.
"""

import pytest

from evals.dataset import load_dataset, validate_dataset
from evals.metrics import CaseResult, compute_metrics, expected_was_retrieved, is_in_top_k, mean, reciprocal_rank
from evals.reports import build_markdown, build_report_dict


# ---------------------------------------------------------------------------
# metrics
# ---------------------------------------------------------------------------
class TestReciprocalRank:
    def test_first_place(self):
        assert reciprocal_rank(["D1", "D2", "D3"], "D1") == 1.0

    def test_second_place(self):
        assert reciprocal_rank(["D1", "D2", "D3"], "D2") == 0.5

    def test_third_place(self):
        assert reciprocal_rank(["D1", "D2", "D3"], "D3") == pytest.approx(1 / 3)

    def test_not_predicted(self):
        assert reciprocal_rank(["D1", "D2"], "D99") == 0.0

    def test_empty_predicted(self):
        assert reciprocal_rank([], "D1") == 0.0


class TestTopK:
    def test_in_top_1(self):
        assert is_in_top_k(["D1", "D2"], "D1", 1)

    def test_in_top_3(self):
        assert is_in_top_k(["D1", "D2", "D3"], "D3", 3)

    def test_outside_top_k(self):
        assert not is_in_top_k(["D1", "D2"], "D2", 1)

    def test_zero_k(self):
        assert not is_in_top_k(["D1"], "D1", 0)


class TestRetrieved:
    def test_retrieved(self):
        assert expected_was_retrieved(["D1", "D2"], "D2")

    def test_not_retrieved(self):
        assert not expected_was_retrieved(["D1"], "D2")


class TestMean:
    def test_basic(self):
        assert mean([1.0, 2.0, 3.0]) == 2.0

    def test_empty(self):
        assert mean([]) == 0.0


def _case(case_id, predicted, expected, scores=None, retrieved=None, **kw):
    return CaseResult(
        case_id=case_id,
        name=case_id,
        expected=expected,
        predicted=predicted,
        predicted_scores=scores or [1.0] * len(predicted),
        retrieved=retrieved if retrieved is not None else predicted,
        **kw,
    )


class TestComputeMetrics:
    def test_all_correct(self):
        cases = [
            _case("a", ["D1", "D2"], "D1", scores=[0.9, 0.8]),
            _case("b", ["D3", "D4"], "D3", scores=[0.8, 0.7]),
        ]
        m = compute_metrics(cases)
        assert m.num_cases == 2
        assert m.top1_accuracy == 1.0
        assert m.top3_accuracy == 1.0
        assert m.mrr == 1.0
        assert m.avg_match_score == pytest.approx(0.85)
        assert m.expected_retrieved_rate == 1.0
        assert m.correct_count == 2

    def test_mixed(self):
        cases = [
            _case("a", ["D1", "D2", "D3"], "D1"),  # correct top-1
            _case("b", ["D5", "D2", "D3"], "D2", scores=[0.9, 0.8, 0.7]),  # correct top-3, rr 0.5
            _case("c", ["D6", "D7"], "D8"),  # not predicted -> rr 0
        ]
        m = compute_metrics(cases)
        assert m.top1_accuracy == pytest.approx(1 / 3)
        assert m.top3_accuracy == pytest.approx(2 / 3)
        assert m.mrr == pytest.approx((1.0 + 0.5 + 0.0) / 3)
        assert m.correct_count == 1

    def test_expected_not_retrieved_still_counts(self):
        cases = [_case("a", ["D1"], "D2", retrieved=["D1", "D3"])]
        m = compute_metrics(cases)
        assert m.expected_retrieved_rate == 0.0
        assert m.top1_accuracy == 0.0

    def test_empty(self):
        m = compute_metrics([])
        assert m.num_cases == 0
        assert m.top1_accuracy == 0.0

    def test_latency_averaging(self):
        cases = [
            _case("a", ["D1"], "D1", retrieval_ms=10.0, ranking_ms=2.0, total_ms=12.0),
            _case("b", ["D2"], "D2", retrieval_ms=20.0, ranking_ms=4.0, total_ms=24.0),
        ]
        m = compute_metrics(cases)
        assert m.avg_retrieval_ms == 15.0
        assert m.avg_ranking_ms == 3.0
        assert m.avg_total_ms == 18.0


# ---------------------------------------------------------------------------
# dataset
# ---------------------------------------------------------------------------
def _valid_case():
    return {
        "id": "eval-001",
        "name": "Noida to Ghaziabad",
        "parcel": {
            "pickup_location": "Noida Sector 62",
            "drop_location": "Vaishali",
            "item_description": "Electronics",
            "weight": 5.0,
        },
        "drivers": [
            {
                "id": "D1",
                "name": "Rahul",
                "vehicle_type": "motorcycle",
                "capacity_kg": 60,
                "rating": 4.9,
                "route": {"origin": "Noida Sector 62", "destination": "Vaishali"},
            },
            {
                "id": "D2",
                "name": "Amit",
                "vehicle_type": "car",
                "capacity_kg": 250,
                "rating": 4.5,
                "route": {"origin": "Gurgaon", "destination": "Dwarka"},
            },
        ],
        "expected_driver": "D1",
        "acceptable_drivers": ["D2"],
    }


def _valid_dataset():
    return {"version": "1.0.0", "test_cases": [_valid_case()]}


class TestValidateDataset:
    def test_valid(self):
        assert validate_dataset(_valid_dataset()) == []

    def test_loads_default_dataset(self):
        data = load_dataset()
        assert data["version"]
        assert len(data["test_cases"]) >= 30
        for case in data["test_cases"]:
            assert case["expected_driver"] in {d["id"] for d in case["drivers"]}

    def test_missing_parcel_field(self):
        case = _valid_case()
        del case["parcel"]["weight"]
        errors = validate_dataset({"version": "1", "test_cases": [case]})
        assert any("weight" in e for e in errors)

    def test_expected_not_among_drivers(self):
        case = _valid_case()
        case["expected_driver"] = "D99"
        errors = validate_dataset({"version": "1", "test_cases": [case]})
        assert any("expected_driver" in e for e in errors)

    def test_duplicate_case_ids(self):
        case = _valid_case()
        data = {"version": "1", "test_cases": [case, case]}
        errors = validate_dataset(data)
        assert any("duplicate id" in e for e in errors)

    def test_acceptable_not_among_drivers(self):
        case = _valid_case()
        case["acceptable_drivers"] = ["D77"]
        errors = validate_dataset({"version": "1", "test_cases": [case]})
        assert any("acceptable_driver" in e for e in errors)

    def test_non_list_test_cases(self):
        errors = validate_dataset({"version": "1", "test_cases": {}})
        assert errors


# ---------------------------------------------------------------------------
# reports
# ---------------------------------------------------------------------------
def _sample_report():
    cases = [
        _case(
            "eval-001",
            ["D1", "D2"],
            "D1",
            scores=[0.94, 0.81],
            retrieval_ms=10.0,
            ranking_ms=0.5,
            total_ms=10.5,
            pickup_location="Noida Sector 62",
            drop_location="Vaishali",
            reasons=["Route overlap: 86%", "Pickup detour: 0.0 km"],
        ),
        _case(
            "eval-002",
            ["D3", "D1"],
            "D1",
            scores=[0.90, 0.88],
            retrieval_ms=12.0,
            ranking_ms=0.5,
            total_ms=12.5,
            pickup_location="Delhi",
            drop_location="Gurgaon",
            reasons=["Route overlap: 80%"],
        ),
    ]
    metrics = compute_metrics(cases)
    report = build_report_dict(
        mode="deterministic",
        mode_used="heuristic",
        metrics=metrics,
        cases=cases,
        dataset_meta={"path": "matching_eval.json", "version": "1.0.0", "num_cases": 2},
        configuration={"embedding_provider": "deterministic", "llm_provider": "heuristic"},
        example_ids=["eval-001"],
        comparison={
            "deterministic": {"top1_accuracy": 0.5, "top3_accuracy": 1.0, "mrr": 0.75, "avg_match_score": 0.94, "avg_total_ms": 10.5},
            "llm": {"top1_accuracy": 0.5, "top3_accuracy": 1.0, "mrr": 0.75, "avg_match_score": 0.9, "avg_total_ms": 610.0},
        },
    )
    return report


class TestReportBuilders:
    def test_json_structure(self):
        report = _sample_report()
        assert report["schema_version"] == "1.0"
        assert set(report["metrics"]) >= {"top1_accuracy", "top3_accuracy", "mrr"}
        assert report["latency_ms"]["avg_total_ms"] == 11.5
        assert len(report["per_case"]) == 2
        assert report["failures"] == ["eval-002 (eval-002)"]
        assert report["examples"][0]["case_id"] == "eval-001"

    def test_example_renders_predicted_ranking(self):
        report = _sample_report()
        md = build_markdown(report)
        assert "## Metrics" in md
        assert "## Latency" in md
        assert "## Deterministic vs LLM Re-ranking" in md
        assert "## Interview-Ready Examples" in md
        assert "1. D1 (0.94)" in md
        assert "2. D2 (0.81)" in md
        assert "- Route overlap: 86%" in md
        assert "Noida Sector 62 → Vaishali" in md
        assert "Top-1 Accuracy | 50.0% (1/2)" in md

    def test_comparison_table_present(self):
        md = build_markdown(_sample_report())
        assert "| Deterministic | 50.0% | 100.0% | 0.750 | 0.94 | 10.5 ms |" in md
        assert "| LLM Re-rank | 50.0% | 100.0% | 0.750 | 0.90 | 610.0 ms |" in md

    def test_no_comparison_section_when_absent(self):
        cases = [_case("a", ["D1"], "D1")]
        report = build_report_dict(
            mode="deterministic",
            mode_used="heuristic",
            metrics=compute_metrics(cases),
            cases=cases,
            dataset_meta={"path": "x", "version": "1", "num_cases": 1},
            configuration={},
        )
        md = build_markdown(report)
        assert "Deterministic vs LLM" not in md
