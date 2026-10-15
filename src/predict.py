import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import joblib
import numpy as np
import pandas as pd

from src.data import (
    ALLOWED_CHANNELS,
    ALLOWED_PRODUCT_FAMILIES,
    ALLOWED_WARRANTY_STATUSES,
    CANONICAL_TEAMS,
    clean_text,
)


class KestrelPredictor:
    """
    Production inference and explanation engine for Kestrel service-request routing.
    Loads the trained pipeline, computes calibrated probabilities, extracts feature
    attributions, applies Policy §3 safeguards, and flags ambiguous requests for human review.
    """

    def __init__(self, model_path: Optional[Path] = None):
        if model_path is None:
            model_path = PROJECT_ROOT / "models" / "kestrel_routing_model.joblib"
        
        if not model_path.exists():
            raise FileNotFoundError(
                f"Model artifact not found at {model_path}. Please run train.py first."
            )
            
        self.model_path = model_path
        self.pipeline = joblib.load(model_path)
        self.preprocessor = self.pipeline.named_steps["preprocessor"]
        self.classifier = self.pipeline.named_steps["classifier"]
        self.classes_ = list(self.classifier.classes_)
        
        # Precompute mean linear coefficients across calibrated estimators for explanation
        self.feature_names_ = self.preprocessor.get_feature_names_out()
        self.mean_coef_ = np.mean(
            [cc.estimator.coef_ for cc in self.classifier.calibrated_classifiers_],
            axis=0,
        )

    def predict_one(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes prediction and generates evidence-grounded explanations for a single request.
        """
        req_id = request_data.get("request_id", "N/A")
        raw_text = request_data.get("request_text", "")
        cleaned = clean_text(raw_text)

        # Handle optional structured fields with sensible defaults
        channel = request_data.get("channel", "chat")
        if channel not in ALLOWED_CHANNELS:
            channel = "chat"
            
        product_family = request_data.get("product_family", "Water Purifier")
        if product_family not in ALLOWED_PRODUCT_FAMILIES:
            product_family = "Water Purifier"
            
        warranty_status = request_data.get("warranty_status", "in_warranty")
        if warranty_status not in ALLOWED_WARRANTY_STATUSES:
            warranty_status = "in_warranty"

        # Edge case: completely empty text
        if not cleaned:
            return {
                "request_id": req_id,
                "predicted_team": "Repairs",
                "confidence": 0.2891,
                "reasons": [
                    "Input request text was empty or non-informative.",
                    "Defaulted to most frequent queue (Repairs) under high uncertainty.",
                    "Mandatory human review required before queue assignment."
                ],
                "review_recommended": True,
                "runner_up_team": "Billing",
                "runner_up_confidence": 0.1530
            }

        input_df = pd.DataFrame([{
            "cleaned_text": cleaned,
            "channel": channel,
            "product_family": product_family,
            "warranty_status": warranty_status,
        }])

        # Probability distribution across all 7 queues
        probs = self.pipeline.predict_proba(input_df)[0]
        sorted_indices = np.argsort(probs)[::-1]
        
        top_idx = sorted_indices[0]
        runner_up_idx = sorted_indices[1]
        
        pred_team = self.classes_[top_idx]
        confidence = float(probs[top_idx])
        runner_up_team = self.classes_[runner_up_idx]
        runner_up_conf = float(probs[runner_up_idx])

        # Mathematical feature contributions for top predicted class
        X_trans = self.preprocessor.transform(input_df)
        indices = X_trans.indices
        values = X_trans.data
        class_weights = self.mean_coef_[top_idx, indices]
        contributions = values * class_weights

        top_contrib_indices = np.argsort(contributions)[::-1]
        
        reasons: List[str] = []
        
        # Extract top 3 positive contributing signals
        positive_features = []
        for i in top_contrib_indices:
            if contributions[i] > 0.05 and len(positive_features) < 3:
                feat_name = self.feature_names_[indices[i]]
                if feat_name.startswith("text__"):
                    token = feat_name.replace("text__", "")
                    positive_features.append(f"Matching text phrase '{token}'")
                elif feat_name.startswith("cat__"):
                    meta = feat_name.replace("cat__", "").replace("_", " ")
                    positive_features.append(f"Customer metadata: {meta}")

        if positive_features:
            reasons.append("Model signals: " + "; ".join(positive_features) + ".")
        else:
            reasons.append(f"Model identified overall text pattern matching the '{pred_team}' queue.")

        # Policy §3 Check: Billing vs Service/Repair payment
        payment_terms = ["paid", "pay", "payment", "emi", "charged", "deducted"]
        service_terms = ["technician", "install", "installer", "repair", "broken", "leak", "leaking", "service", "slot", "visit"]
        
        has_payment = any(re.search(r"\b" + re.escape(w) + r"\b", cleaned) for w in payment_terms)
        has_service = any(re.search(r"\b" + re.escape(w) + r"\b", cleaned) for w in service_terms)
        
        billing_policy_conflict = False
        if has_payment and has_service:
            billing_policy_conflict = True
            if pred_team == "Billing":
                reasons.append(
                    "Policy §3 Advisory: Customer mentions payment alongside technician/service keywords. "
                    "Per Policy §3, requests belong in Billing only when the payment mechanism itself is disputed. "
                    "Desk review strongly advised to verify whether ticket should be routed to Installs or Repairs."
                )
            else:
                reasons.append(
                    f"Policy §3 Alignment: Customer mentioned payment, but request requires physical service/visit; "
                    f"routed to '{pred_team}' in accordance with Policy §3."
                )

        # Ambiguity check (e.g., 'please call me about purifier')
        vague_terms = ["call back", "call me", "pls call", "please call", "need help", "contact me"]
        is_vague = any(term in cleaned for term in vague_terms) and len(cleaned.split()) <= 7
        if is_vague:
            reasons.append(
                "Ambiguity Notice: Request text contains generic callback request without specific failure symptoms; "
                "historically associated with elevated transfer rates."
            )

        # Review Recommendation criteria
        review_recommended = (
            confidence < 0.65
            or (confidence - runner_up_conf) < 0.15
            or (billing_policy_conflict and pred_team == "Billing")
            or is_vague
        )

        return {
            "request_id": req_id,
            "predicted_team": pred_team,
            "confidence": round(confidence, 4),
            "reasons": reasons,
            "review_recommended": review_recommended,
            "runner_up_team": runner_up_team,
            "runner_up_confidence": round(runner_up_conf, 4),
        }

    def predict_batch(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generates predictions for a dataframe, returning request_id and predicted team."""
        df_copy = df.copy()
        if "cleaned_text" not in df_copy.columns:
            df_copy["cleaned_text"] = df_copy["request_text"].apply(clean_text)
            
        features = ["cleaned_text", "channel", "product_family", "warranty_status"]
        preds = self.pipeline.predict(df_copy[features])
        
        result_df = pd.DataFrame({
            "request_id": df_copy["request_id"],
            "team": preds
        })
        return result_df
