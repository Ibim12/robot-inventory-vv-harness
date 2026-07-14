import pandas as pd
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from evaluator import (
    calculate_inventory_accuracy,
    calculate_duplicate_rate,
    calculate_missing_scan_rate,
    calculate_precision_recall,
    evaluate_release,
    normalise_ground_truth,
    normalise_scans,
)


def make_ground_truth():
    return pd.DataFrame(
        {
            "shelf_id": ["A-01-01", "A-01-02", "A-01-03"],
            "expected_sku": ["SKU-1", "SKU-2", "SKU-3"],
        }
    )


def test_perfect_scans_have_100_percent_accuracy():
    ground_truth = make_ground_truth()
    scans = pd.DataFrame(
        {
            "shelf_id": ["A-01-01", "A-01-02", "A-01-03"],
            "detected_sku": ["SKU-1", "SKU-2", "SKU-3"],
            "confidence": [0.99, 0.97, 0.98],
        }
    )

    assert calculate_inventory_accuracy(ground_truth, scans) == 1.0


def test_missing_scan_reduces_recall_and_missing_rate():
    ground_truth = make_ground_truth()
    scans = pd.DataFrame(
        {
            "shelf_id": ["A-01-01", "A-01-02"],
            "detected_sku": ["SKU-1", "SKU-2"],
            "confidence": [0.99, 0.97],
        }
    )

    precision, recall = calculate_precision_recall(ground_truth, scans)

    assert precision == 1.0
    assert round(recall, 3) == 0.667
    assert round(calculate_missing_scan_rate(ground_truth, scans), 3) == 0.333


def test_duplicate_records_increase_duplicate_rate():
    scans = pd.DataFrame(
        {
            "shelf_id": ["A-01-01", "A-01-01", "A-01-02"],
            "detected_sku": ["SKU-1", "SKU-1", "SKU-2"],
            "confidence": [0.99, 0.99, 0.97],
        }
    )

    assert round(calculate_duplicate_rate(scans), 3) == 0.333


def test_release_fails_when_accuracy_is_below_threshold():
    metrics = {
        "inventory_accuracy": 0.90,
        "precision": 0.96,
        "recall": 0.90,
        "duplicate_rate": 0.01,
        "missing_scan_rate": 0.04,
        "average_confidence": 0.90,
    }
    requirements = {
        "minimum_inventory_accuracy": 0.95,
        "minimum_precision": 0.95,
        "minimum_recall": 0.93,
        "maximum_duplicate_rate": 0.02,
        "maximum_missing_scan_rate": 0.05,
        "minimum_average_confidence": 0.85,
    }

    result = evaluate_release(metrics, requirements)

    assert result["decision"] == "FAIL"
    assert "inventory_accuracy" in result["failed_checks"]
