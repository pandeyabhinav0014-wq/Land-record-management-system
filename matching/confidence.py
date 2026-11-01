"""
Confidence Scoring and Match Classification (Stages D & E)
Provides transparent, dynamically renormalized weighted scoring and calibrated classification.
Integrates business rule adjustments, component breakdowns, and threshold-based decisions.
"""

from typing import Dict, Any, List, Optional, Tuple
import numpy as np

DEFAULT_FEATURE_WEIGHTS = {
    "survey_number_agreement": 0.25,
    "exact_parcel_id": 0.10,
    "fuzzy_parcel_id": 0.05,
    "address_similarity": 0.15,
    "area_similarity": 0.15,
    "spatial_proximity": 0.15,
    "polygon_iou": 0.15,
    "owner_name_similarity": 0.10,
    "semantic_similarity": 0.05,
    "land_use_agreement": 0.05
}

class ConfidenceScorer:
    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        high_threshold: float = 0.80,
        medium_threshold: float = 0.55,
        calibration_model: Optional[Any] = None
    ):
        self.weights = weights or DEFAULT_FEATURE_WEIGHTS.copy()
        self.high_threshold = high_threshold
        self.medium_threshold = medium_threshold
        self.calibration_model = calibration_model

    def calculate_confidence(
        self,
        feature_scores: Dict[str, float],
        rule_adjustment: float = 0.0,
        rule_flags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Calculates normalized confidence score with transparent component weights.
        Renormalizes weights only over present features to handle missing data gracefully.
        """
        rule_flags = rule_flags or []
        present_features = [f for f in self.weights if f in feature_scores]

        if not present_features:
            return {
                "final_confidence": 0.0,
                "preliminary_score": 0.0,
                "rule_adjustment": rule_adjustment,
                "match_decision": "LOW_CONFIDENCE",
                "is_automatic_match": False,
                "requires_manual_review": True,
                "effective_weights": {},
                "score_type": "heuristic"
            }

        # Calculate sum of weights for available features
        weight_sum = sum(self.weights[f] for f in present_features)
        if weight_sum <= 0:
            weight_sum = 1.0

        # Renormalize weights
        effective_weights = {
            f: round(self.weights[f] / weight_sum, 4)
            for f in present_features
        }

        # Weighted dot product
        raw_weighted_score = sum(
            feature_scores[f] * effective_weights[f]
            for f in present_features
        )
        preliminary_score = round(float(raw_weighted_score), 4)

        # Apply rule deltas
        adjusted_score = float(np.clip(preliminary_score + rule_adjustment, 0.0, 1.0))
        final_confidence = round(adjusted_score, 4)

        score_type = "heuristic"
        # Optional calibration model evaluation
        if self.calibration_model is not None:
            try:
                # Features vector aligned with calibration model
                x_vec = np.array([[final_confidence]])
                calibrated_prob = float(self.calibration_model.predict_proba(x_vec)[0][1])
                final_confidence = round(calibrated_prob, 4)
                score_type = "statistically_calibrated"
            except Exception:
                score_type = "heuristic"

        # Classification decision
        # If critical conflict flag exists, never automatically accept
        has_critical_conflict = any(flag in ["FLAG_GEOMETRY_CONFLICT", "FLAG_MANUAL_REVIEW"] for flag in rule_flags)

        if final_confidence >= self.high_threshold and not has_critical_conflict:
            decision = "HIGH_CONFIDENCE"
            is_auto = True
            req_review = False
        elif final_confidence >= self.medium_threshold or has_critical_conflict:
            decision = "MEDIUM_CONFIDENCE"
            is_auto = False
            req_review = True
        else:
            decision = "LOW_CONFIDENCE"
            is_auto = False
            req_review = False

        return {
            "final_confidence": final_confidence,
            "preliminary_score": preliminary_score,
            "rule_adjustment": rule_adjustment,
            "match_decision": decision,
            "is_automatic_match": is_auto,
            "requires_manual_review": req_review,
            "effective_weights": effective_weights,
            "score_type": score_type
        }

