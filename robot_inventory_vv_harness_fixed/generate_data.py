"""Generate synthetic inventory-scan data for a small robotics V&V project.

The fictional system is a mobile inventory-scanning robot. The generated CSVs let
us check whether a release candidate meets measurable requirements for accuracy,
recall, duplicate rate, missing-scan rate and confidence.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

RANDOM_SEED = 7
DATA_DIR = Path(__file__).parent / "data"


def make_ground_truth(number_of_shelves: int = 100) -> pd.DataFrame:
    shelves = []
    skus = []

    aisles = ["A", "B", "C", "D"]
    for i in range(number_of_shelves):
        aisle = aisles[i % len(aisles)]
        bay = (i // len(aisles)) + 1
        level = (i % 5) + 1
        shelves.append(f"{aisle}-{bay:02d}-{level:02d}")
        skus.append(f"SKU-{1000 + i}")

    return pd.DataFrame({"shelf_id": shelves, "expected_sku": skus})


def make_scans(
    ground_truth: pd.DataFrame,
    output_path: Path,
    software_version: str,
    miss_rate: float,
    wrong_sku_rate: float,
    duplicate_rate: float,
    low_confidence_rate: float,
) -> pd.DataFrame:
    random.seed(RANDOM_SEED + hash(software_version) % 1000)
    start_time = datetime(2026, 7, 9, 9, 0, 0)
    rows = []

    for index, record in ground_truth.iterrows():
        if random.random() < miss_rate:
            continue

        detected_sku = record["expected_sku"]
        if random.random() < wrong_sku_rate:
            detected_sku = f"SKU-WRONG-{random.randint(1, 99):02d}"

        confidence = round(random.uniform(0.88, 0.99), 3)
        if random.random() < low_confidence_rate:
            confidence = round(random.uniform(0.45, 0.79), 3)

        rows.append(
            {
                "timestamp": (start_time + timedelta(seconds=len(rows))).isoformat(),
                "shelf_id": record["shelf_id"],
                "detected_sku": detected_sku,
                "confidence": confidence,
                "software_version": software_version,
            }
        )

        if random.random() < duplicate_rate:
            rows.append(
                {
                    "timestamp": (start_time + timedelta(seconds=len(rows))).isoformat(),
                    "shelf_id": record["shelf_id"],
                    "detected_sku": detected_sku,
                    "confidence": confidence,
                    "software_version": software_version,
                }
            )

    scans = pd.DataFrame(rows)
    scans.to_csv(output_path, index=False)
    return scans


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)

    ground_truth = make_ground_truth(number_of_shelves=100)
    ground_truth.to_csv(DATA_DIR / "ground_truth.csv", index=False)

    # Baseline is a known-good reference run.
    make_scans(
        ground_truth,
        output_path=DATA_DIR / "scans_baseline.csv",
        software_version="v1.0-baseline",
        miss_rate=0.02,
        wrong_sku_rate=0.01,
        duplicate_rate=0.01,
        low_confidence_rate=0.02,
    )

    # Candidate deliberately has more faults, so the evaluator should catch this.
    make_scans(
        ground_truth,
        output_path=DATA_DIR / "scans_candidate.csv",
        software_version="v1.1-candidate",
        miss_rate=0.07,
        wrong_sku_rate=0.04,
        duplicate_rate=0.03,
        low_confidence_rate=0.08,
    )

    print("Generated synthetic V&V data in the data/ folder.")


if __name__ == "__main__":
    main()
