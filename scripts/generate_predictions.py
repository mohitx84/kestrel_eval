import os
import sys
from pathlib import Path
from typing import Optional
import pandas as pd

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data import CANONICAL_TEAMS, load_test_data
from src.predict import KestrelPredictor


def generate_predictions(output_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Generates predictions for all rows in test_unlabelled.csv using the production model.
    Saves predictions to root-level predictions.csv adhering to the submission contract.
    """
    if output_path is None:
        output_path = PROJECT_ROOT / "predictions.csv"

    print("Loading unlabelled test data...")
    test_df = load_test_data()
    print(f"Loaded {len(test_df)} test requests.")

    print("Initializing predictor...")
    predictor = KestrelPredictor()

    print("Generating predictions...")
    preds_df = predictor.predict_batch(test_df)

    # Validate output structure
    assert list(preds_df.columns) == ["request_id", "team"], (
        f"Columns mismatch: expected ['request_id', 'team'], got {list(preds_df.columns)}"
    )
    assert len(preds_df) == len(test_df), (
        f"Row count mismatch: expected {len(test_df)}, got {len(preds_df)}"
    )
    assert preds_df["request_id"].equals(test_df["request_id"]), (
        "request_id sequence must exactly match test_unlabelled.csv"
    )
    assert preds_df["team"].isnull().sum() == 0, "No null predictions permitted"
    invalid_teams = set(preds_df["team"]) - set(CANONICAL_TEAMS)
    assert not invalid_teams, f"Found invalid/obsolete team predictions: {invalid_teams}"

    # Save to CSV without index
    preds_df.to_csv(output_path, index=False)
    print(f"Successfully generated predictions at: {output_path}")
    print("\nPredicted Class Distribution:")
    print(preds_df["team"].value_counts())

    return preds_df


if __name__ == "__main__":
    from typing import Optional
    generate_predictions()
