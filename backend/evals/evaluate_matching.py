#!/usr/bin/env python
"""Evaluate the ShipIT AI matching engine against a curated, reproducible dataset.

Measures match quality (Top-1 / Top-3 / MRR), latency (retrieval vs ranking),
and compares deterministic heuristic ranking against LLM re-ranking.

Usage (from the project root ``D:\\shipit-adv\\shipit1\\project``):

    python backend/evals/evaluate_matching.py --mode deterministic
    python backend/evals/evaluate_matching.py --mode llm
    python backend/evals/evaluate_matching.py --mode deterministic --compare

The deterministic mode is fully offline (deterministic embeddings + heuristic
ranking). LLM mode gracefully falls back to the heuristic if no API key is
configured. Results are written to ``backend/evals/results/``.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from time import perf_counter

# --- Path + environment bootstrap BEFORE importing the app -------------------
BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

EVALS_ROOT = Path(__file__).resolve().parent
DEFAULT_RESULTS_DIR = EVALS_ROOT / "results"
DEFAULT_EVAL_DB_NAME = "shipit_eval"

parser = argparse.ArgumentParser(description="Evaluate the ShipIT AI matching engine.")
parser.add_argument(
    "--mode",
    choices=["deterministic", "llm"],
    default="deterministic",
    help="Ranking mode to evaluate (default: deterministic, fully offline).",
)
parser.add_argument(
    "--compare",
    action="store_true",
    help="Also run the other mode and emit a Deterministic vs LLM comparison table.",
)
parser.add_argument(
    "--dataset",
    default=str(EVALS_ROOT / "data" / "matching_eval.json"),
    help="Path to the evaluation dataset JSON.",
)
parser.add_argument(
    "--db-url",
    default=None,
    help="Postgres URL (asyncpg). Defaults to <DATABASE_URL db>/shipit_eval, auto-created.",
)
parser.add_argument("--limit", type=int, default=None, help="Only run the first N test cases.")
parser.add_argument(
    "--embedding-provider",
    choices=["deterministic", "configured"],
    default="deterministic",
    help="deterministic = offline hash embeddings (reproducible); configured = use .env provider.",
)
parser.add_argument(
    "--global-pool",
    action="store_true",
    help="Evaluate against ALL seeded routes at once. By default each test case is an "
    "isolated scenario (only that case's drivers are available), matching how the "
    "dataset labels were curated.",
)
parser.add_argument("--results-dir", default=str(DEFAULT_RESULTS_DIR), help="Output directory.")
ARGS = parser.parse_args()

if ARGS.embedding_provider == "deterministic":
    os.environ["EMBEDDING_PROVIDER"] = "deterministic"
os.environ.setdefault("EMBEDDING_DIMENSIONS", "1536")

# --- App imports (after env is pinned for reproducibility) -------------------
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.models  # noqa: F401  (register all models on Base.metadata)
from app.ai.matcher import rank
from app.config import settings
from app.database import Base
from app.models import Driver, DriverStatus, Parcel, ParcelSizeTier, Route, User, UserRole, VehicleType
from app.services.matching_service import MatchingService
from app.services.route_service import RouteService, build_route_text

from evals.dataset import load_dataset
from evals.metrics import CaseResult, compute_metrics
from evals.reports import build_markdown, build_report_dict, write_reports


# ---------------------------------------------------------------------------
# Database bootstrap
# ---------------------------------------------------------------------------
def derive_eval_db_url(base_url: str) -> str:
    """Swap the database name in an asyncpg URL for the disposable eval DB."""
    head, _ = base_url.rsplit("/", 1)
    return f"{head}/{DEFAULT_EVAL_DB_NAME}"


async def ensure_database(url: str) -> None:
    """Create the eval database if it does not exist (connecting to 'postgres')."""
    import asyncpg

    clean = url.replace("+asyncpg", "")
    dbname = clean.rsplit("/", 1)[-1]
    if dbname in {"postgres", "template1"}:
        return
    maintenance_dsn = clean.rsplit("/", 1)[0] + "/postgres"
    conn = await asyncpg.connect(maintenance_dsn)
    try:
        exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", dbname)
        if not exists:
            await conn.execute(f'CREATE DATABASE "{dbname}"')
            print(f"[eval] created database '{dbname}'")
    finally:
        await conn.close()


async def setup_schema(engine) -> None:
    """Recreate the schema for a clean, reproducible run.

    NOTE: no approximate (HNSW) index is created on the eval database. pgvector's
    HNSW construction is randomized per build, which makes approximate top-K
    results vary between runs at near-equal distances. With ~161 routes the
    planner uses an exact scan, which is bit-for-bit reproducible. Production
    uses the HNSW index (see alembic migration 0001_initial).
    """
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


# ---------------------------------------------------------------------------
# Seeding (deterministic: fixed public ids, emails, deadlines relative to base)
# ---------------------------------------------------------------------------
async def seed_dataset(session, dataset: dict, base_time: datetime) -> dict[str, Parcel]:
    parcels: dict[str, Parcel] = {}
    for index, case in enumerate(dataset["test_cases"], start=1):
        sender = User(
            public_id=f"U-SND-{index:03d}",
            name=f"Eval Sender {index:03d}",
            email=f"sender.eval.{index:03d}@shipit.local",
            password_hash="<eval>",
            role=UserRole.SENDER,
        )
        session.add(sender)
        await session.flush()

        spec = case["parcel"]
        hours = spec.get("deadline_hours")
        deadline = base_time + timedelta(hours=hours) if hours is not None else None
        parcel = Parcel(
            public_id=f"P-EVAL-{index:03d}",
            sender_id=sender.id,
            pickup_location=spec["pickup_location"],
            drop_location=spec["drop_location"],
            item_description=spec["item_description"],
            item_value=spec.get("item_value", 0.0),
            weight=spec.get("weight", 1.0),
            size_tier=ParcelSizeTier(spec.get("size_tier", "medium")),
            budget=spec.get("budget", 0.0),
            deadline=deadline,
        )
        session.add(parcel)
        await session.flush()

        for dspec in case["drivers"]:
            await _seed_driver(session, dspec, index)

        parcels[case["id"]] = parcel
    await session.commit()
    return parcels


async def _seed_driver(session, dspec: dict, index: int) -> Driver:
    user = User(
        public_id=f"U-{dspec['id']}",
        name=dspec["name"],
        email=f"{dspec['id'].lower()}.{index:03d}@shipit.local",
        password_hash="<eval>",
        role=UserRole.DRIVER,
    )
    session.add(user)
    await session.flush()

    driver = Driver(
        public_id=dspec["id"],
        user_id=user.id,
        vehicle_type=VehicleType(dspec.get("vehicle_type", "van")),
        capacity_kg=dspec.get("capacity_kg", 500.0),
        rating=dspec.get("rating", 4.5),
        on_time_rate=dspec.get("on_time_rate", 0.9),
        status=DriverStatus.AVAILABLE,
        current_city=dspec.get("current_city"),
    )
    session.add(driver)
    await session.flush()

    rspec = dspec["route"]
    waypoints = [{"label": w} for w in rspec.get("waypoints", [])] or None
    route = Route(
        driver_id=driver.id,
        origin=rspec["origin"],
        destination=rspec["destination"],
        waypoints=waypoints,
        route_text=build_route_text(rspec["origin"], rspec["destination"], waypoints),
        is_active=True,
    )
    session.add(route)
    await session.flush()
    await RouteService.embed(session, route)
    return driver


# ---------------------------------------------------------------------------
# Run the existing matching pipeline per case
# ---------------------------------------------------------------------------
async def _isolate_case_routes(session, case: dict) -> None:
    """Make only the current case's drivers available during retrieval.

    Each test case is a self-contained scenario: its labeled best driver was
    chosen from the drivers present in that case, so the candidate pool must
    be restricted to that case (otherwise cross-case drivers leak in).
    """
    from sqlalchemy import select

    case_public = {d["id"] for d in case["drivers"]}
    rows = (
        await session.execute(
            select(Route, Driver.public_id).join(Driver, Route.driver_id == Driver.id)
        )
    ).all()
    for route, public_id in rows:
        route.is_active = public_id in case_public
    await session.flush()


async def run_case(session, parcel: Parcel, case: dict) -> CaseResult:
    """Run retrieval + ranking through the production services with timing."""
    service = MatchingService(session)

    t0 = perf_counter()
    candidates = await service.retrieve_candidates(parcel)
    t1 = perf_counter()
    ranked, ranked_by = await rank(parcel, candidates)
    t2 = perf_counter()

    top = ranked[: settings.ai_match_max_results]
    return CaseResult(
        case_id=case["id"],
        name=case.get("name", case["id"]),
        expected=case["expected_driver"],
        acceptable=list(case.get("acceptable_drivers", []) or []),
        retrieved=[c.driver.public_id for c in candidates],
        predicted=[r.driver.public_id for r in top],
        predicted_scores=[r.score for r in top],
        reasons=list(top[0].reason) if top else [],
        ranked_by=ranked_by,
        retrieval_ms=(t1 - t0) * 1000.0,
        ranking_ms=(t2 - t1) * 1000.0,
        total_ms=(t2 - t0) * 1000.0,
        pickup_location=parcel.pickup_location,
        drop_location=parcel.drop_location,
    )


async def run_mode(session, parcels: dict[str, Parcel], dataset: dict, mode: str) -> tuple[list[CaseResult], str, str | None]:
    """Run every test case in one ranking mode. Returns (results, mode_used, note)."""
    if mode == "deterministic":
        settings.llm_provider = "heuristic"
        os.environ["LLM_PROVIDER"] = "heuristic"

    llm_configured = settings.llm_api_key and settings.llm_provider in {"openrouter", "openai"}
    note = None
    if mode == "llm" and not llm_configured:
        note = (
            "No LLM_API_KEY / LLM_PROVIDER configured — LLM mode fell back to the "
            "deterministic heuristic. Set LLM_PROVIDER=openrouter (or openai) and "
            "LLM_API_KEY in backend/.env to benchmark real LLM re-ranking."
        )

    results: list[CaseResult] = []
    for case in dataset["test_cases"]:
        if not ARGS.global_pool:
            await _isolate_case_routes(session, case)
        parcel = parcels[case["id"]]
        result = await run_case(session, parcel, case)
        results.append(result)
        flag = "OK " if result.predicted and result.predicted[0] == result.expected else "MISS"
        print(
            f"  {result.case_id} [{flag}] expected={result.expected} "
            f"predicted={result.predicted[:3]} "
            f"({result.retrieval_ms:.1f}ms retrieve + {result.ranking_ms:.1f}ms rank)"
        )
    return results, "heuristic" if not llm_configured and mode == "llm" else ("ai" if llm_configured else "heuristic"), note


def _metrics_snapshot(metrics) -> dict:
    return {
        "top1_accuracy": round(metrics.top1_accuracy, 4),
        "top3_accuracy": round(metrics.top3_accuracy, 4),
        "mrr": round(metrics.mrr, 4),
        "avg_match_score": round(metrics.avg_match_score, 4),
        "avg_total_ms": round(metrics.avg_total_ms, 2),
        "num_cases": metrics.num_cases,
    }


def select_examples(cases: list[CaseResult]) -> list[str]:
    """Pick 5 interview-ready examples: highest-scoring correct cases first,
    padded with the best-scoring remaining cases if needed."""
    ordered = sorted(
        cases,
        key=lambda c: (1 if c.predicted and c.predicted[0] == c.expected else 0, c.predicted_scores[0] if c.predicted_scores else 0.0),
        reverse=True,
    )
    return [c.case_id for c in ordered[:5]]


def print_summary(report: dict) -> None:
    print()
    print("=" * 68)
    print("SUMMARY")
    print("=" * 68)
    print(f"{'Mode':<16}{'Top-1':>10}{'Top-3':>10}{'MRR':>8}{'Avg Score':>12}{'Avg Latency':>14}")
    print("-" * 68)

    comp = report.get("comparison")
    if comp:
        for key, row in (("deterministic", comp.get("deterministic")), ("llm", comp.get("llm"))):
            if row is None:
                continue
            print(
                f"{key:<16}{row['top1_accuracy']:>10.3f}{row['top3_accuracy']:>10.3f}"
                f"{row['mrr']:>8.3f}{row['avg_match_score']:>12.3f}{row['avg_total_ms']:>12.1f} ms"
            )
    else:
        m, lat = report["metrics"], report["latency_ms"]
        print(
            f"{report['mode']:<16}{m['top1_accuracy']:>10.3f}{m['top3_accuracy']:>10.3f}"
            f"{m['mrr']:>8.3f}{m['avg_match_score']:>12.3f}{lat['avg_total_ms']:>12.1f} ms"
        )
    print("=" * 68)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
async def main() -> None:
    results_dir = Path(ARGS.results_dir)
    dataset = load_dataset(ARGS.dataset)
    if ARGS.limit:
        dataset["test_cases"] = dataset["test_cases"][: ARGS.limit]

    eval_url = ARGS.db_url or derive_eval_db_url(settings.database_url)
    await ensure_database(eval_url)

    engine = create_async_engine(eval_url, echo=False, pool_pre_ping=True)
    await setup_schema(engine)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    base_time = datetime.now(timezone.utc)
    async with SessionLocal() as session:
        parcels = await seed_dataset(session, dataset, base_time)
        print(f"[eval] seeded {len(dataset['test_cases'])} cases / "
              f"{sum(len(c['drivers']) for c in dataset['test_cases'])} drivers "
              f"into {DEFAULT_EVAL_DB_NAME}")

        det_results: list[CaseResult] = []
        det_metrics = None
        llm_results: list[CaseResult] = []
        llm_metrics = None
        note: str | None = None
        configuration = {
            "embedding_provider": settings.embedding_provider,
            "embedding_model": settings.embedding_model,
            "embedding_dimensions": settings.embedding_dimensions,
            "llm_provider": settings.llm_provider,
            "llm_model": settings.llm_model,
            "top_k": settings.ai_match_top_k,
            "max_results": settings.ai_match_max_results,
            "candidate_pool": "global" if ARGS.global_pool else "isolated-per-case",
        }

        if ARGS.compare:
            print("[eval] running deterministic mode...")
            det_results, _, _ = await run_mode(session, parcels, dataset, "deterministic")
            det_metrics = compute_metrics(det_results)
            print("[eval] running llm mode...")
            llm_results, _, note = await run_mode(session, parcels, dataset, "llm")
            llm_metrics = compute_metrics(llm_results)

            comparison = {"deterministic": _metrics_snapshot(det_metrics), "llm": _metrics_snapshot(llm_metrics)}
            report = build_report_dict(
                mode="comparison",
                mode_used=f"deterministic ({det_metrics.top1_accuracy:.0%} top-1) vs llm ({llm_metrics.top1_accuracy:.0%} top-1)",
                metrics=det_metrics,
                cases=det_results,
                dataset_meta={
                    "path": ARGS.dataset,
                    "version": dataset.get("version"),
                    "num_cases": len(dataset["test_cases"]),
                },
                configuration=configuration,
                llm_fallback_note=note,
                comparison=comparison,
                example_ids=select_examples(det_results),
            )
        else:
            print(f"[eval] running {ARGS.mode} mode...")
            results, mode_used, note = await run_mode(session, parcels, dataset, ARGS.mode)
            metrics = compute_metrics(results)
            report = build_report_dict(
                mode=ARGS.mode,
                mode_used=mode_used,
                metrics=metrics,
                cases=results,
                dataset_meta={
                    "path": ARGS.dataset,
                    "version": dataset.get("version"),
                    "num_cases": len(dataset["test_cases"]),
                },
                configuration=configuration,
                llm_fallback_note=note,
                example_ids=select_examples(results),
            )

    json_path, md_path = write_reports(report, results_dir)
    print(f"[eval] wrote {json_path}")
    print(f"[eval] wrote {md_path}")

    print_summary(report)

    await engine.dispose()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
