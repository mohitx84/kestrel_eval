import json
import os
import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import joblib
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.svm import LinearSVC

from src.data import (
    CANONICAL_TEAMS,
    clean_text,
    get_temporal_split,
    load_train_data,
)


def build_pipeline() -> Pipeline:
    """
    Constructs the feature extraction and classification pipeline.
    Combines cleaned text n-gram TF-IDF and structured intake categorical encoders.
    """
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "text",
                TfidfVectorizer(
                    ngram_range=(1, 2),
                    min_df=2,
                    sublinear_tf=True,
                ),
                "cleaned_text",
            ),
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore"),
                ["channel", "product_family", "warranty_status"],
            ),
        ],
        remainder="drop",
    )

    # Calibrated LinearSVC provides high accuracy, rapid CPU inference, and genuine posterior probabilities
    classifier = CalibratedClassifierCV(
        estimator=LinearSVC(C=0.8, random_state=42, max_iter=2000),
        cv=3,
    )

    return Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", classifier),
    ])


def train_model(save_artifact: bool = True) -> Pipeline:
    """
    Trains the routing model on the complete historical dataset and saves artifacts.
    """
    print("Loading training data...")
    df = load_train_data()
    print(f"Loaded {len(df)} historical requests.")

    # Validation evaluation on temporal split
    df_train_time, df_val_time = get_temporal_split(df, cutoff_date="2026-04-01")
    print(
        f"Evaluating temporal holdout: Train N={len(df_train_time)}, Val N={len(df_val_time)}"
    )

    eval_pipeline = build_pipeline()
    features = ["cleaned_text", "channel", "product_family", "warranty_status"]
    eval_pipeline.fit(df_train_time[features], df_train_time["canonical_team"])

    val_preds = eval_pipeline.predict(df_val_time[features])
    val_acc = accuracy_score(df_val_time["canonical_team"], val_preds)
    val_macro_f1 = f1_score(
        df_val_time["canonical_team"], val_preds, average="macro"
    )

    print(f"Validation Accuracy: {val_acc:.4f} ({val_acc*100:.2f}%)")
    print(f"Validation Macro F1: {val_macro_f1:.4f}")

    # Now train production model on 100% of historical training data
    print("Fitting production model on full training set (10,822 rows)...")
    prod_pipeline = build_pipeline()
    prod_pipeline.fit(df[features], df["canonical_team"])

    if save_artifact:
        models_dir = PROJECT_ROOT / "models"
        models_dir.mkdir(parents=True, exist_ok=True)
        model_path = models_dir / "kestrel_routing_model.joblib"
        joblib.dump(prod_pipeline, model_path)
        print(f"Model artifact successfully saved to: {model_path}")

        metadata = {
            "model_type": "CalibratedClassifierCV(LinearSVC)",
            "pipeline": "TF-IDF(1,2) + OneHotEncoder -> CalibratedLinearSVC",
            "classes": prod_pipeline.named_steps["classifier"].classes_.tolist(),
            "n_train_samples": len(df),
            "temporal_val_accuracy": round(float(val_acc), 4),
            "temporal_val_macro_f1": round(float(val_macro_f1), 4),
            "target_threshold": 0.90,
            "target_achieved": bool(val_acc >= 0.90),
        }
        meta_path = models_dir / "model_metadata.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        print(f"Metadata saved to: {meta_path}")

    return prod_pipeline


if __name__ == "__main__":
    train_model(save_artifact=True)
