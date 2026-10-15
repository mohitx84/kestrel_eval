import os
import re
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import pandas as pd

# Base project path
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Official Team Aliases to Canonical Current Active Teams (Effective 15 Jan 2026 per Policy §5)
ALIAS_MAP: Dict[str, str] = {
    "Installations": "Installs & Demo",
    "Installs & Demo": "Installs & Demo",
    "Consumables": "Filters & Consumables",
    "Filters & Consumables": "Filters & Consumables",
    "Repairs": "Repairs",
    "Billing": "Billing",
    "Returns & Replacement": "Returns & Replacement",
    "Warranty Claims": "Warranty Claims",
    "Product Advice": "Product Advice",
}

CANONICAL_TEAMS: List[str] = sorted(list(set(ALIAS_MAP.values())))

ALLOWED_CHANNELS = ["chat", "whatsapp", "ivr", "email"]
ALLOWED_PRODUCT_FAMILIES = [
    "Water Purifier",
    "Air Fryer",
    "Mixer Grinder",
    "Induction Cooktop",
    "Room Heater",
    "Ceiling Fan",
    "Robot Vacuum",
]
ALLOWED_WARRANTY_STATUSES = ["in_warranty", "out_of_warranty", "shield"]


def clean_text(text: Optional[str]) -> str:
    """
    Cleans and normalizes incoming service request text.
    Handles legacy Zoho Mojibake, unicode accents, punctuation, and extra whitespace.
    """
    if text is None or not isinstance(text, str):
        return ""
    
    # Fix common UTF-8 Mojibake sequences observed in legacy Zoho desk BEFORE decomposition
    text = text.replace("â€¦", " ").replace("â€“", " ").replace("â€”", " ")
    
    # Unicode NFKD normalization (e.g., 'urgént' -> 'urgent')
    text = unicodedata.normalize("NFKD", text)
    
    # Remove or map remaining non-ascii characters
    text = text.encode("ascii", "ignore").decode("utf-8")
    
    # Lowercase and normalize whitespace
    text = re.sub(r"\s+", " ", text.lower()).strip()
    return text


def canonicalize_team(team_name: str) -> str:
    """Maps historical or raw team names to current active canonical team names."""
    if not isinstance(team_name, str):
        raise ValueError(f"Invalid team name: {team_name}")
    team_clean = team_name.strip()
    if team_clean in ALIAS_MAP:
        return ALIAS_MAP[team_clean]
    raise ValueError(
        f"Unknown team name: '{team_name}'. Must be one of {list(ALIAS_MAP.keys())}"
    )


def resolve_data_file(filename: str) -> Path:
    """Finds a data file either in data/raw/ or data/ with fallback."""
    raw_path = PROJECT_ROOT / "data" / "raw" / filename
    if raw_path.exists():
        return raw_path
    
    direct_path = PROJECT_ROOT / "data" / filename
    if direct_path.exists():
        return direct_path
        
    # Search by suffix in data/
    data_dir = PROJECT_ROOT / "data"
    if data_dir.exists():
        for p in data_dir.glob(f"*{filename}"):
            return p
            
    raise FileNotFoundError(f"Could not locate dataset file '{filename}' in data/ or data/raw/.")


def load_train_data() -> pd.DataFrame:
    """Loads historical training data, cleans text, and maps target to canonical teams."""
    file_path = resolve_data_file("train.csv")
    df = pd.read_csv(file_path)
    df["canonical_team"] = df["team_label"].apply(canonicalize_team)
    df["cleaned_text"] = df["request_text"].apply(clean_text)
    return df


def load_test_data() -> pd.DataFrame:
    """Loads unlabelled test data and applies text preprocessing."""
    file_path = resolve_data_file("test_unlabelled.csv")
    df = pd.read_csv(file_path)
    df["cleaned_text"] = df["request_text"].apply(clean_text)
    return df


def load_resolution_log() -> pd.DataFrame:
    """Loads the historical resolution log."""
    file_path = resolve_data_file("resolution_log.csv")
    df = pd.read_csv(file_path)
    df["first_canonical"] = df["first_team"].apply(canonicalize_team)
    df["final_canonical"] = df["final_team"].apply(canonicalize_team)
    return df


def get_temporal_split(
    df: pd.DataFrame, cutoff_date: str = "2026-04-01"
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Partitions the dataset into a strictly time-aware train/val holdout.
    Default cutoff is 2026-04-01 (holding out the final ~3 months).
    """
    df_copy = df.copy()
    df_copy["dt"] = pd.to_datetime(df_copy["created_at_ist"])
    train_mask = df_copy["dt"] < cutoff_date
    val_mask = df_copy["dt"] >= cutoff_date
    return df_copy[train_mask].drop(columns=["dt"]), df_copy[val_mask].drop(columns=["dt"])
