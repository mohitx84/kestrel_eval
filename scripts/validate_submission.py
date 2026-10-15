import os
import sys
from pathlib import Path
from typing import Optional
import pandas as pd

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data import CANONICAL_TEAMS, resolve_data_file


def validate_submission(predictions_path: Optional[Path] = None) -> bool:
    """
    Validates predictions.csv against sample_submission.csv and test_unlabelled.csv.
    Ensures exact schema, row counts, ID coverage, row ordering, and valid canonical labels.
    """
    if predictions_path is None:
        predictions_path = PROJECT_ROOT / "predictions.csv"

    print(f"=== Validating Submission File: {predictions_path} ===")

    if not predictions_path.exists():
        print(f"FAILED: Predictions file not found at {predictions_path}")
        return False

    preds = pd.read_csv(predictions_path)
    sample_sub_path = resolve_data_file("sample_submission.csv")
    sample_sub = pd.read_csv(sample_sub_path)
    test_path = resolve_data_file("test_unlabelled.csv")
    test_df = pd.read_csv(test_path)

    passed = True

    # 1. Row count check
    if len(preds) != len(sample_sub):
        print(f"FAILED: Expected {len(sample_sub)} rows, found {len(preds)}")
        passed = False
    else:
        print(f"PASSED: Row count matches sample_submission ({len(preds)} rows).")

    # 2. Column schema check
    expected_cols = ["request_id", "team"]
    if list(preds.columns) != expected_cols:
        print(f"FAILED: Expected columns {expected_cols}, got {list(preds.columns)}")
        passed = False
    else:
        print(f"PASSED: Column names and order match expected: {expected_cols}.")

    # 3. Missing values check
    null_counts = preds.isnull().sum()
    if null_counts.any():
        print(f"FAILED: Null values detected:\n{null_counts}")
        passed = False
    else:
        print("PASSED: Zero null values detected in predictions.")

    # 4. ID coverage and duplicate check
    preds_ids = preds["request_id"].tolist()
    test_ids = test_df["request_id"].tolist()
    if preds_ids != test_ids:
        print("FAILED: request_id sequence does not exactly match test_unlabelled.csv.")
        missing_ids = set(test_ids) - set(preds_ids)
        extra_ids = set(preds_ids) - set(test_ids)
        if missing_ids:
            print(f"  Missing IDs count: {len(missing_ids)}")
        if extra_ids:
            print(f"  Extra IDs count: {len(extra_ids)}")
        passed = False
    else:
        print("PASSED: request_id sequence matches test_unlabelled.csv exactly (1-to-1 order).")

    # 5. Team label validity
    pred_teams = set(preds["team"].unique())
    invalid_teams = pred_teams - set(CANONICAL_TEAMS)
    if invalid_teams:
        print(f"FAILED: Invalid or obsolete team names found: {invalid_teams}")
        passed = False
    else:
        print(f"PASSED: All predicted teams belong to canonical set ({len(pred_teams)} distinct classes used):")
        for t, count in preds["team"].value_counts().items():
            print(f"   - {t:24s}: {count:4d} ({count/len(preds):.1%})")

    # 6. Check for obsolete aliases specifically
    obsolete_found = pred_teams.intersection({"Installations", "Consumables"})
    if obsolete_found:
        print(f"FAILED: Obsolete team names present in predictions: {obsolete_found}")
        passed = False
    else:
        print("PASSED: Zero obsolete aliases ('Installations', 'Consumables') present.")

    if passed:
        print("\nALL SUBMISSION VALIDATION CHECKS PASSED SUCCESSFULLY!")
    else:
        print("\nSUBMISSION VALIDATION FAILED!")

    return passed


if __name__ == "__main__":
    from typing import Optional
    success = validate_submission()
    if not success:
        sys.exit(1)
