# Robot Inventory V&V Harness

This is a small verification and validation project for a simulated autonomous inventory-scanning robot.

It compares robot scan outputs against ground-truth inventory data, calculates performance metrics, checks them against configurable acceptance criteria, and produces a release decision.

This project uses synthetic data and does not attempt to test or reproduce any proprietary robotics system.

# What it is
A configurable Python verification-and-validation harness that evaluates simulated mobile-robot inventory scans against ground truth, measures performance against defined requirements, and produces an automated release decision.

## What it demonstrates

- Translating requirements into measurable acceptance criteria
- Automated test development for a robotics-style data pipeline
- Benchmark metrics for inventory accuracy, precision, recall, duplicate scans, missing scans and confidence
- Release candidate pass/fail decision
- Unit tests for the evaluation logic

## How to run

```bash
pip install pandas pyyaml pytest
python generate_data.py
python evaluator.py --ground-truth data/ground_truth.csv --scans data/scans_candidate.csv --requirements config/requirements.yaml --output outputs/release_report_candidate.json
pytest
```

## Example Release Results



### Baseline Release
Final decision: PASS  
All metrics met the configured acceptance criteria.
----------------------------------------
inventory_accuracy         97.00%  PASS
precision                  98.98%  PASS
recall                     97.00%  PASS
duplicate_rate              0.00%  PASS
missing_scan_rate           2.00%  PASS
average_confidence         92.52%  PASS
----------------------------------------

### Pytest results

collected 4 items                                                                                                                                                                                               

tests\test_evaluator.py ....                                                                                                                                                                              [100%]

============================================================================================== 4 passed in 0.56s ====================================================================================

### Candidate Release
Final decision: FAIL  

Inventory Scan V&V Release Report
----------------------------------------
inventory_accuracy         85.00%  FAIL
precision                  96.59%  PASS
recall                     85.00%  FAIL
duplicate_rate              6.38%  FAIL
missing_scan_rate          12.00%  FAIL
average_confidence         90.37%  PASS
----------------------------------------
FINAL RELEASE DECISION: FAIL

Failed checks: inventory_accuracy, recall, duplicate_rate, missing_scan_rate.


## Verification vs Validation

Verification: checking that the evaluator and test logic behave correctly.  
Example: pytest unit tests confirm that accuracy, recall and release decisions are calculated correctly.

Validation: checking whether the simulated robot output meets operational requirements.  
Example: scan results are compared against ground truth and must meet accuracy, recall, duplicate-rate and missing-scan thresholds.



## Notes

This is an independent educational V&V demonstrator using synthetic data. It does not test, reproduce or make claims about any proprietary robotics system.

