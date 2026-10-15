import pandas as pd
import pytest
from src.data import CANONICAL_TEAMS, PROJECT_ROOT, load_test_data


def test_predictions_csv_exists():
    pred_path = PROJECT_ROOT / "predictions.csv"
    assert pred_path.exists(), "predictions.csv must exist at the repository root"


def test_predictions_schema_and_counts():
    pred_path = PROJECT_ROOT / "predictions.csv"
    df = pd.read_csv(pred_path)
    test_df = load_test_data()

    # 1. Exact row count
    assert len(df) == 2178
    assert len(df) == len(test_df)

    # 2. Exact column schema
    assert list(df.columns) == ["request_id", "team"]

    # 3. No nulls
    assert df["request_id"].isnull().sum() == 0
    assert df["team"].isnull().sum() == 0

    # 4. Exact 1-to-1 matching ID sequence
    assert (df["request_id"] == test_df["request_id"]).all()

    # 5. All teams in canonical active list
    unique_teams = set(df["team"].unique())
    assert unique_teams.issubset(set(CANONICAL_TEAMS))

    # 6. No obsolete aliases
    assert "Installations" not in unique_teams
    assert "Consumables" not in unique_teams
