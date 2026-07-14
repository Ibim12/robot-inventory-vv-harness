"""Evaluate simulated inventory-scanning robot outputs against V&V requirements.

This script supports two input styles:
1. Recommended schema:
   ground truth: shelf_id, expected_sku
   scans: timestamp, shelf_id, detected_sku, confidence, software_version

2. Your first simple schema:
   ground truth/scans: rows, number
   This is automatically converted to shelf_id/expected_sku and shelf_id/detected_sku.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd
import yaml




def load_requirements(path: str | Path) -> dict[str, float]:
    with open(path, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)
    return config["acceptance_criteria"]


def normalise_ground_truth(ground_truth: pd.DataFrame) -> pd.DataFrame:
    ground_truth = ground_truth.copy()

    if {"rows", "number"}.issubset(ground_truth.columns):
        ground_truth = ground_truth.rename(
            columns={"rows": "shelf_id", "number": "expected_sku"}
        )

    required_columns = {"shelf_id", "expected_sku"}
    missing = required_columns - set(ground_truth.columns)
    if missing:
        raise ValueError(f"Ground-truth file is missing columns: {sorted(missing)}")

    ground_truth["shelf_id"] = ground_truth["shelf_id"].astype(str)
    ground_truth["expected_sku"] = ground_truth["expected_sku"].astype(str)
    return ground_truth[["shelf_id", "expected_sku"]]


def normalise_scans(scans: pd.DataFrame) -> pd.DataFrame:
    scans = scans.copy()

    if {"rows", "number"}.issubset(scans.columns):
        scans = scans.rename(columns={"rows": "shelf_id", "number": "detected_sku"})

    required_columns = {"shelf_id", "detected_sku"}
    missing = required_columns - set(scans.columns)
    if missing:
        raise ValueError(f"Scan file is missing columns: {sorted(missing)}")

    if "confidence" not in scans.columns:
        # For early hand-written CSVs without confidence values, assume perfect
        # confidence so you can test the basic accuracy logic first.
        scans["confidence"] = 1.0

    scans["shelf_id"] = scans["shelf_id"].astype(str)
    scans["detected_sku"] = scans["detected_sku"].astype(str)
    scans["confidence"] = pd.to_numeric(scans["confidence"], errors="coerce").fillna(0.0)
    return scans


def calculate_duplicate_rate(scans: pd.DataFrame) -> float:
    if len(scans) == 0:
        return 0.0
    duplicate_count = scans.duplicated(subset=["shelf_id"], keep="first").sum()
    return float(duplicate_count / len(scans))


def calculate_missing_scan_rate(ground_truth: pd.DataFrame, scans: pd.DataFrame) -> float:
    expected_shelves = set(ground_truth["shelf_id"])
    scanned_shelves = set(scans["shelf_id"])
    missing_count = len(expected_shelves - scanned_shelves)
    return float(missing_count / len(expected_shelves))


def calculate_average_confidence(scans: pd.DataFrame) -> float:
    if len(scans) == 0:
        return 0.0
    return float(scans["confidence"].mean())


def calculate_precision_recall(ground_truth: pd.DataFrame, scans: pd.DataFrame) -> tuple[float, float]:
    expected = dict(zip(ground_truth["shelf_id"], ground_truth["expected_sku"]))
    unique_scans = scans.drop_duplicates(subset=["shelf_id"], keep="first")

    true_positives = 0
    false_positives = 0

    for _, scan in unique_scans.iterrows():
        shelf_id = scan["shelf_id"]
        detected_sku = scan["detected_sku"]

        if shelf_id in expected and detected_sku == expected[shelf_id]:
            true_positives += 1
        else:
            false_positives += 1

    false_negatives = len(expected) - true_positives

    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) else 0.0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) else 0.0
    return float(precision), float(recall)


def calculate_inventory_accuracy(ground_truth: pd.DataFrame, scans: pd.DataFrame) -> float:
    # In this project, inventory accuracy means the proportion of expected shelf
    # locations where the correct SKU was detected.
    _, recall = calculate_precision_recall(ground_truth, scans)
    return recall


def calculate_metrics(ground_truth: pd.DataFrame, scans: pd.DataFrame) -> dict[str, float]:
    precision, recall = calculate_precision_recall(ground_truth, scans)
    return {
        "inventory_accuracy": calculate_inventory_accuracy(ground_truth, scans),
        "precision": precision,
        "recall": recall,
        "duplicate_rate": calculate_duplicate_rate(scans),
        "missing_scan_rate": calculate_missing_scan_rate(ground_truth, scans),
        "average_confidence": calculate_average_confidence(scans),
    }


def evaluate_release(metrics: dict[str, float], requirements: dict[str, float]) -> dict[str, Any]:
    checks = {
        "inventory_accuracy": metrics["inventory_accuracy"] >= requirements["minimum_inventory_accuracy"],
        "precision": metrics["precision"] >= requirements["minimum_precision"],
        "recall": metrics["recall"] >= requirements["minimum_recall"],
        "duplicate_rate": metrics["duplicate_rate"] <= requirements["maximum_duplicate_rate"],
        "missing_scan_rate": metrics["missing_scan_rate"] <= requirements["maximum_missing_scan_rate"],
        "average_confidence": metrics["average_confidence"] >= requirements["minimum_average_confidence"],
    }

    return {
        "decision": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "failed_checks": [metric for metric, passed in checks.items() if not passed],
    }


def format_percent(value: float) -> str:
    return f"{value * 100:.2f}%"


def print_report(metrics: dict[str, float], decision: dict[str, Any]) -> None:
    print()
    print("Inventory Scan V&V Release Report")
    print("-" * 40)
    for metric, value in metrics.items():
        status = "PASS" if decision["checks"][metric] else "FAIL"
        print(f"{metric:24s} {format_percent(value):>8s}  {status}")

    print("-" * 40)
    print(f"FINAL RELEASE DECISION: {decision['decision']}")
    if decision["failed_checks"]:
        print("Failed checks:", ", ".join(decision["failed_checks"]))


def save_report(metrics: dict[str, float], decision: dict[str, Any], output_path: str | Path) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as file:
        json.dump({"metrics": metrics, "release_decision": decision}, file, indent=2)


def run_evaluation(ground_truth_path: str, scans_path: str, requirements_path: str, output_path: str | None = None) -> dict[str, Any]:
    ground_truth = normalise_ground_truth(pd.read_csv(ground_truth_path))
    scans = normalise_scans(pd.read_csv(scans_path))
    requirements = load_requirements(requirements_path)

    metrics = calculate_metrics(ground_truth, scans)
    decision = evaluate_release(metrics, requirements)
    print_report(metrics, decision)

    if output_path:
        save_report(metrics, decision, output_path)

    return {"metrics": metrics, "release_decision": decision}


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate robot inventory-scan V&V results.")
    parser.add_argument("--ground-truth", required=True, help="Path to ground-truth CSV")
    parser.add_argument("--scans", required=True, help="Path to robot scan-output CSV")
    parser.add_argument("--requirements", required=True, help="Path to requirements YAML")
    parser.add_argument("--output", default="outputs/release_report.json", help="Path to save JSON report")
    args = parser.parse_args()

    run_evaluation(args.ground_truth, args.scans, args.requirements, args.output)


if __name__ == "__main__":
    main()
