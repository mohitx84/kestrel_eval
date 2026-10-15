import pytest
from src.data import (
    ALIAS_MAP,
    CANONICAL_TEAMS,
    canonicalize_team,
    clean_text,
    get_temporal_split,
    load_test_data,
    load_train_data,
)


def test_clean_text_basic():
    assert clean_text("Hello World!") == "hello world!"
    assert clean_text("  extra   spaces  ") == "extra spaces"
    assert clean_text(None) == ""
    assert clean_text("") == ""


def test_clean_text_mojibake_and_accents():
    # Accented vowels
    assert clean_text("urgént: installer did not turn up") == "urgent: installer did not turn up"
    assert clean_text("paymént deducted") == "payment deducted"
    assert clean_text("burnt sméll") == "burnt smell"
    # Mojibake sequences
    assert clean_text("disappointed â€¦") == "disappointed"
    assert clean_text("pls hélp â€“ issue") == "pls help issue"


def test_canonicalize_team_aliases():
    # Historical aliases
    assert canonicalize_team("Installations") == "Installs & Demo"
    assert canonicalize_team("Installs & Demo") == "Installs & Demo"
    assert canonicalize_team("Consumables") == "Filters & Consumables"
    assert canonicalize_team("Filters & Consumables") == "Filters & Consumables"
    # Unchanged teams
    assert canonicalize_team("Repairs") == "Repairs"
    assert canonicalize_team("Billing") == "Billing"
    assert canonicalize_team("Returns & Replacement") == "Returns & Replacement"
    assert canonicalize_team("Warranty Claims") == "Warranty Claims"
    assert canonicalize_team("Product Advice") == "Product Advice"


def test_canonicalize_team_invalid():
    with pytest.raises(ValueError):
        canonicalize_team("Invalid Queue Name")
    with pytest.raises(ValueError):
        canonicalize_team("")


def test_canonical_teams_count():
    assert len(CANONICAL_TEAMS) == 7
    expected = {
        "Billing",
        "Filters & Consumables",
        "Installs & Demo",
        "Product Advice",
        "Repairs",
        "Returns & Replacement",
        "Warranty Claims",
    }
    assert set(CANONICAL_TEAMS) == expected


def test_load_train_data():
    df = load_train_data()
    assert len(df) == 10822
    assert "canonical_team" in df.columns
    assert "cleaned_text" in df.columns
    assert set(df["canonical_team"].unique()).issubset(set(CANONICAL_TEAMS))
    assert df["canonical_team"].isnull().sum() == 0


def test_load_test_data():
    df = load_test_data()
    assert len(df) == 2178
    assert "cleaned_text" in df.columns
    assert "team_label" not in df.columns
    assert df["cleaned_text"].isnull().sum() == 0


def test_temporal_split():
    df = load_train_data()
    train_split, val_split = get_temporal_split(df, cutoff_date="2026-04-01")
    assert len(train_split) == 8687
    assert len(val_split) == 2135
    assert len(train_split) + len(val_split) == len(df)
