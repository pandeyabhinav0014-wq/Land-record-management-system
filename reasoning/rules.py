"""
Knowledge Representation and Rule-Based Reasoning Engine
Loads external JSON business rules, evaluates them against candidate pairs,
applies confidence adjustments, and produces structured audit records.
"""

import json
import os
from typing import List, Dict, Any, Optional

DEFAULT_RULES_PATH = os.path.join(os.path.dirname(__file__), "rules_config.json")

class RuleEngine:
    def __init__(self, rules_file_path: Optional[str] = None):
        self.rules_file_path = rules_file_path or DEFAULT_RULES_PATH
        self.rules = self.load_rules()

    def load_rules(self) -> List[Dict[str, Any]]:
        """Loads business rules from JSON configuration."""
        if os.path.exists(self.rules_file_path):
            with open(self.rules_file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def evaluate(
        self,
        rec_a: Dict[str, Any],
        rec_b: Dict[str, Any],
        feature_scores: Dict[str, float],
        raw_metrics: Dict[str, Any],
        preliminary_score: float
    ) -> Dict[str, Any]:
        """
        Evaluates candidate pair against all business rules.
        Returns:
          triggered_rules: list of triggered rule objects with audit reasons
          confidence_adjustment: cumulative delta to apply to the confidence score
          flags: set of operational flags (e.g. ROUTE_TO_REVIEW, GEOMETRY_CONFLICT)
        """
        triggered_rules = []
        total_delta = 0.0
        flags = set()

        for rule in self.rules:
            r_id = rule.get("rule_id")
            conds = rule.get("conditions", {})
            action = rule.get("action")
            delta = rule.get("confidence_delta", 0.0)
            is_triggered = False
            audit_explanation = ""

            # Check RULE-01: Exact survey + matching village/locality
            if "exact_survey" in conds:
                exact_s = feature_scores.get("exact_parcel_id", 0.0) == 1.0
                addr_sim = feature_scores.get("address_similarity", 0.0)
                if exact_s and addr_sim >= conds.get("min_address_similarity", 0.65):
                    is_triggered = True
                    audit_explanation = f"Exact survey agreement matched with high address/locality alignment ({addr_sim*100:.1f}%)."

            # Check RULE-02: Large area discrepancy
            elif "min_relative_area_diff" in conds:
                rel_diff = raw_metrics.get("relative_area_difference")
                if rel_diff is not None and rel_diff >= conds["min_relative_area_diff"]:
                    is_triggered = True
                    area_a = raw_metrics.get("area_a_sqm", 0)
                    area_b = raw_metrics.get("area_b_sqm", 0)
                    audit_explanation = f"Significant area mismatch of {rel_diff*100:.1f}% detected between {area_a} m² and {area_b} m²."

            # Check RULE-03: Substantial Polygon IoU
            elif "min_polygon_iou" in conds:
                iou = feature_scores.get("polygon_iou")
                if iou is not None and iou >= conds["min_polygon_iou"]:
                    is_triggered = True
                    audit_explanation = f"Strong GIS polygon boundary overlap confirmed (IoU: {iou*100:.1f}%)."

            # Check RULE-04: Conflicting parcel identifiers
            elif "max_fuzzy_parcel_id" in conds:
                fuzzy_s = feature_scores.get("fuzzy_parcel_id")
                if fuzzy_s is not None and fuzzy_s < conds["max_fuzzy_parcel_id"]:
                    is_triggered = True
                    audit_explanation = f"Conflicting parcel/survey identifiers: '{rec_a.get('parcel_or_survey_number')}' vs '{rec_b.get('parcel_or_survey_number')}' (similarity: {fuzzy_s*100:.1f}%)."

            # Check RULE-05: Missing owner name neutral preservation
            elif "missing_owner_name" in conds:
                owner_a = rec_a.get("owner_name")
                owner_b = rec_b.get("owner_name")
                if not owner_a or not owner_b:
                    is_triggered = True
                    audit_explanation = "Owner name is missing in at least one record; neutral handling applied without rejecting candidate."

            # Check RULE-06: Identifier match but spatial distance mismatch
            elif "min_survey_agreement" in conds and "min_distance_meters" in conds:
                s_agr = feature_scores.get("survey_number_agreement", 0.0)
                dist = raw_metrics.get("distance_meters")
                if s_agr >= conds["min_survey_agreement"] and dist is not None and dist >= conds["min_distance_meters"]:
                    is_triggered = True
                    audit_explanation = f"Strong survey agreement ({s_agr*100:.1f}%) contradicts large geographic distance of {dist:.1f}m."

            # Check RULE-07: Borderline score routed to review
            elif "confidence_range" in conds:
                low_b, high_b = conds["confidence_range"]
                if low_b <= preliminary_score <= high_b:
                    is_triggered = True
                    audit_explanation = f"Match confidence ({preliminary_score:.2f}) falls in ambiguous band [{low_b:.2f}, {high_b:.2f}] requiring reviewer verification."

            # Check RULE-08: Land use disagreement
            elif "max_land_use_agreement" in conds:
                lu = feature_scores.get("land_use_agreement")
                if lu is not None and lu <= conds["max_land_use_agreement"]:
                    is_triggered = True
                    audit_explanation = f"Contradictory land-use classification: '{rec_a.get('land_use_category')}' vs '{rec_b.get('land_use_category')}'."

            if is_triggered:
                triggered_rules.append({
                    "rule_id": r_id,
                    "description": rule.get("description"),
                    "severity": rule.get("severity"),
                    "action": action,
                    "confidence_delta": delta,
                    "evidence_fields": rule.get("evidence_fields"),
                    "audit_explanation": audit_explanation
                })
                total_delta += delta
                if action:
                    flags.add(action)

        return {
            "triggered_rules": triggered_rules,
            "confidence_adjustment": round(total_delta, 4),
            "flags": sorted(list(flags))
        }

