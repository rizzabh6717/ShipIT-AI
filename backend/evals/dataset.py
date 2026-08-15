"""Evaluation dataset loading and validation.

The dataset lives at ``evals/data/matching_eval.json`` and is version
controlled so results are reproducible across machines and time.
"""

from __future__ import annotations

import json
from pathlib import Path

DEFAULT_DATASET_PATH = Path(__file__).parent / "data" / "matching_eval.json"

_REQUIRED_PARCEL_FIELDS = {"pickup_location", "drop_location", "item_description", "weight"}
_REQUIRED_DRIVER_FIELDS = {"id", "name", "vehicle_type", "capacity_kg", "rating", "route"}
_REQUIRED_ROUTE_FIELDS = {"origin", "destination"}


def load_dataset(path: str | Path | None = None) -> dict:
    """Load and validate the evaluation dataset, raising ValueError on error."""
    dataset_path = Path(path) if path else DEFAULT_DATASET_PATH
    with open(dataset_path, encoding="utf-8") as fh:
        data = json.load(fh)

    errors = validate_dataset(data)
    if errors:
        raise ValueError(
            f"Invalid evaluation dataset {dataset_path}:\n" + "\n".join(errors)
        )
    return data


def validate_dataset(data: dict) -> list[str]:
    """Return a list of validation errors (empty list == valid dataset)."""
    errors: list[str] = []

    if not isinstance(data, dict) or "test_cases" not in data:
        return ["Dataset must be an object with a 'test_cases' list"]

    if "version" not in data:
        errors.append("Missing top-level 'version' field")

    cases = data["test_cases"]
    if not isinstance(cases, list) or not cases:
        return ["'test_cases' must be a non-empty list"]

    seen_ids: set[str] = set()
    for i, case in enumerate(cases, start=1):
        prefix = f"test_cases[{i}]"
        if not isinstance(case, dict):
            errors.append(f"{prefix}: expected an object")
            continue

        if "id" not in case or not case.get("id"):
            errors.append(f"{prefix}: missing 'id'")
        elif case["id"] in seen_ids:
            errors.append(f"{prefix}: duplicate id '{case['id']}'")
        else:
            seen_ids.add(case["id"])

        if "name" not in case:
            errors.append(f"{prefix}: missing 'name'")

        parcel = case.get("parcel")
        if not isinstance(parcel, dict):
            errors.append(f"{prefix}: missing 'parcel' object")
        else:
            for field in _REQUIRED_PARCEL_FIELDS:
                if field not in parcel:
                    errors.append(f"{prefix}.parcel: missing '{field}'")

        drivers = case.get("drivers")
        if not isinstance(drivers, list) or not drivers:
            errors.append(f"{prefix}: 'drivers' must be a non-empty list")
        else:
            driver_ids: set[str] = set()
            for j, driver in enumerate(drivers, start=1):
                dprefix = f"{prefix}.drivers[{j}]"
                if not isinstance(driver, dict):
                    errors.append(f"{dprefix}: expected an object")
                    continue
                for field in _REQUIRED_DRIVER_FIELDS:
                    if field not in driver:
                        errors.append(f"{dprefix}: missing '{field}'")
                if driver.get("id") in driver_ids:
                    errors.append(f"{dprefix}: duplicate driver id '{driver.get('id')}'")
                driver_ids.add(driver.get("id"))
                route = driver.get("route")
                if isinstance(route, dict):
                    for field in _REQUIRED_ROUTE_FIELDS:
                        if field not in route:
                            errors.append(f"{dprefix}.route: missing '{field}'")

        expected = case.get("expected_driver")
        driver_ids = {d.get("id") for d in drivers} if isinstance(drivers, list) else set()
        if expected not in driver_ids:
            errors.append(
                f"{prefix}: 'expected_driver' '{expected}' is not among the case drivers"
            )

        for acc in case.get("acceptable_drivers", []) or []:
            if acc not in driver_ids:
                errors.append(f"{prefix}: acceptable_driver '{acc}' is not among the case drivers")

    return errors


def iter_cases(data: dict):
    """Yield each test case in the dataset."""
    yield from data["test_cases"]
