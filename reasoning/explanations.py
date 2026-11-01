"""
Explainable AI (XAI) Generation for Land Record Matching
Produces transparent, human-readable explanations, feature contributions,
positive/negative evidence lists, and missing data notices.
"""

from typing import Dict, Any, List

LEGAL_DISCLAIMER = (
    "NOTICE: This system provides algorithmic decision-support and data reconciliation. "
    "Correlation, similarity scores, or automated classifications do not declare legal ownership "
    "or substitute for official statutory adjudication."
)

class ExplanationGenerator:
    @staticmethod
    def generate_explanation(
        match_decision: str,
        confidence_score: float,
        feature_scores: Dict[str, float],
        raw_metrics: Dict[str, Any],
        missing_features: List[str],
        triggered_rules: List[Dict[str, Any]],
        effective_weights: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Generates comprehensive explainability payload.
        """
        positive_evidence: List[str] = []
        negative_evidence: List[str] = []
        neutral_or_missing: List[str] = []
        narrative_parts: List[str] = []

        # 1. Survey / Parcel ID
        s_exact = feature_scores.get("exact_parcel_id", 0.0)
        s_fuzzy = feature_scores.get("fuzzy_parcel_id", 0.0)
        if "exact_parcel_id" in feature_scores:
            if s_exact == 1.0:
                positive_evidence.append(f"Exact survey/parcel number agreement ('{raw_metrics.get('survey_a')}')")
                narrative_parts.append("survey numbers agree exactly")
            elif s_fuzzy >= 0.70:
                positive_evidence.append(f"Strong fuzzy survey number similarity ({s_fuzzy*100:.1f}%)")
                narrative_parts.append("survey numbers are closely aligned")
            elif s_fuzzy < 0.40:
                negative_evidence.append(f"Substantial survey identifier divergence: '{raw_metrics.get('survey_a')}' vs '{raw_metrics.get('survey_b')}' ({s_fuzzy*100:.1f}%)")
                narrative_parts.append("survey numbers diverge significantly")

        # 2. Address / Locality
        addr_sim = feature_scores.get("address_similarity")
        if addr_sim is not None:
            if addr_sim >= 0.75:
                positive_evidence.append(f"High address and locality similarity ({addr_sim*100:.1f}%)")
                narrative_parts.append("the village/address matches closely")
            elif addr_sim < 0.40:
                negative_evidence.append(f"Discrepancy in recorded address/locality ({addr_sim*100:.1f}%)")
                narrative_parts.append("recorded addresses differ")

        # 3. Area
        area_sim = feature_scores.get("area_similarity")
        rel_diff = raw_metrics.get("relative_area_difference")
        if area_sim is not None and rel_diff is not None:
            if rel_diff <= 0.10:
                positive_evidence.append(f"Close land area match (only {rel_diff*100:.1f}% relative difference)")
                narrative_parts.append("the area difference is minimal")
            elif rel_diff > 0.25:
                negative_evidence.append(f"Area discrepancy of {rel_diff*100:.1f}% ({raw_metrics.get('area_a_sqm')} m² vs {raw_metrics.get('area_b_sqm')} m²)")
                narrative_parts.append("there is a significant area discrepancy")

        # 4. Spatial / Geometry
        iou = feature_scores.get("polygon_iou")
        dist = raw_metrics.get("distance_meters")
        if iou is not None and iou > 0.0:
            if iou >= 0.50:
                positive_evidence.append(f"Substantial GIS boundary polygon overlap (IoU: {iou*100:.1f}%)")
                narrative_parts.append("parcel boundaries substantially overlap")
            else:
                positive_evidence.append(f"Partial boundary overlap (IoU: {iou*100:.1f}%)")
        elif dist is not None:
            if dist <= 50.0:
                positive_evidence.append(f"Immediate geographic proximity (approx. {dist:.1f}m centroid distance)")
                narrative_parts.append("geographic locations are in tight proximity")
            elif dist >= 500.0:
                negative_evidence.append(f"Substantial geographic separation ({dist:.1f}m apart)")
                narrative_parts.append("geographic locations are distant")

        # 5. Owner Name
        owner_sim = feature_scores.get("owner_name_similarity")
        if owner_sim is not None:
            if owner_sim >= 0.85:
                positive_evidence.append(f"Owner names match closely ({owner_sim*100:.1f}%)")
                narrative_parts.append("owner names are strongly matching")
            elif owner_sim >= 0.55:
                neutral_or_missing.append(f"Owner names show moderate similarity ({owner_sim*100:.1f}%)")
                narrative_parts.append("owner-name similarity is moderate")
            else:
                negative_evidence.append(f"Owner names diverge: '{raw_metrics.get('owner_a')}' vs '{raw_metrics.get('owner_b')}' ({owner_sim*100:.1f}%)")
                narrative_parts.append("owner names differ")

        # 6. Missing evidence
        if missing_features:
            for feat in missing_features:
                clean_name = feat.replace("_", " ").title()
                neutral_or_missing.append(f"No {clean_name} data available across both sources (neutral weight rebalancing applied)")

        # Construct concise natural language summary
        if narrative_parts:
            summary_text = (
                f"{match_decision.replace('_', ' ').title()} candidate (confidence {confidence_score:.2f}) "
                f"because {', '.join(narrative_parts)}."
            )
        else:
            summary_text = f"Candidate evaluated with confidence score {confidence_score:.2f}."

        # Feature contributions: (score * effective_weight)
        feature_contributions = {}
        for feat, score in feature_scores.items():
            wt = effective_weights.get(feat, 0.0)
            feature_contributions[feat] = {
                "score": score,
                "weight": wt,
                "contribution": round(score * wt, 4)
            }

        return {
            "summary": summary_text,
            "match_decision": match_decision,
            "confidence_score": confidence_score,
            "positive_evidence": positive_evidence,
            "negative_evidence": negative_evidence,
            "neutral_or_missing": neutral_or_missing,
            "feature_contributions": feature_contributions,
            "triggered_rules_summary": [
                f"[{r['severity']}] {r['rule_id']}: {r['audit_explanation']}"
                for r in triggered_rules
            ],
            "legal_disclaimer": LEGAL_DISCLAIMER
        }

