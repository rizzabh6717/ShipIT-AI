"""ShipIT matching-engine evaluation framework.

Pure, offline utilities (metrics, dataset handling, report builders) plus the
``evaluate_matching.py`` CLI that measures match quality against a curated,
version-controlled dataset.

Run from the project root:

    python backend/evals/evaluate_matching.py --mode deterministic
    python backend/evals/evaluate_matching.py --mode llm --compare
"""
