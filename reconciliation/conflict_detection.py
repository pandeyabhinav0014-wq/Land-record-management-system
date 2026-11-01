"""
Conflict Detection Service (Section 8)
Detects and categorizes attribute contradictions between linked or candidate records.
Maintains conflict metadata, discrepancies, severity, suggested administrative resolutions,
and auditable evidence.
"""

from typing import List, Dict, Any, Optional, Tuple
import uuid

# Configurable administrative source priority (can be customized via settings)
DEFAULT_SOURCE_PRIORITY = [
    "GIS Survey Records",
    "Revenue Land Records",
    "Municipal Property Records"
]

class ConflictDetector:
    def __init__(self, source_priority_order: Optional[List[str]] = None):
        self.source_priority = source_priority_order or DEFAULT_SOURCE_PRIORITY

    def get_preferred_source_value(self, val_a: Any, src_a: str, val_b: Any, src_b: str) -> Tuple[Any, str]:
        """
        Returns (preferred_value, rationale) based on administrative source priority policy.
        Clearly labeled as administrative preference, NOT legal proof.
        """
        priority_a = self.source_priority.index(src_a) if src_a in self.source_priority else 999
        priority_b = self.source_priority.index(src_b) if src_b in self.source_priority else 999

        if priority_a < priority_b:
            return val_a, f"Administrative preference: source '{src_a}' prioritized over '{src_b}'."
        elif priority_b < priority_a:
            return val_b, f"Administrative preference: source '{src_b}' prioritized over '{src_a}'."
        else:
            return val_a, "Sources have equal administrative priority; source A value selected as default."

    def detect_conflicts(
        self,
        candidate_pair: Dict[str, Any],
        rec_a: Dict[str, Any],
        rec_b: Dict[str, Any],
        feature_scores: Dict[str, float],
        raw_metrics: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Scans a candidate pair for discrepancies and generates structured conflict objects.
        """
        conflicts: List[Dict[str, Any]] = []
        pair_id = candidate_pair.get("pair_id", str(uuid.uuid4()))
        src_a = rec_a.get("source_name", "Source A")
        src_b = rec_b.get("source_name", "Source B")

        # 1. Parcel Identifier Conflict
        s_exact = feature_scores.get("exact_parcel_id", 1.0)
        s_fuzzy = feature_scores.get("fuzzy_parcel_id", 1.0)
        if s_exact == 0.0 and s_fuzzy < 0.60:
            val_a = rec_a.get("parcel_or_survey_number")
            val_b = rec_b.get("parcel_or_survey_number")
            pref_val, pref_msg = self.get_preferred_source_value(val_a, src_a, val_b, src_b)
            conflicts.append({
                "conflict_id": f"CONF-{uuid.uuid4().hex[:8].upper()}",
                "pair_id": pair_id,
                "category": "PARCEL_IDENTIFIER_CONFLICT",
                "field": "parcel_or_survey_number",
                "source_a": src_a,
                "value_a": val_a,
                "source_b": src_b,
                "value_b": val_b,
                "discrepancy_measure": f"Fuzzy identifier similarity is {s_fuzzy*100:.1f}%",
                "severity": "HIGH",
                "supporting_evidence": f"Record identifiers differ markedly between sources.",
                "suggested_value": pref_val,
                "suggested_value_rationale": pref_msg,
                "resolution_status": "PENDING"
            })

        # 2. Owner Name Conflict
        owner_sim = feature_scores.get("owner_name_similarity")
        if owner_sim is not None and owner_sim < 0.60:
            val_a = rec_a.get("owner_name")
            val_b = rec_b.get("owner_name")
            pref_val, pref_msg = self.get_preferred_source_value(val_a, src_a, val_b, src_b)
            conflicts.append({
                "conflict_id": f"CONF-{uuid.uuid4().hex[:8].upper()}",
                "pair_id": pair_id,
                "category": "OWNER_NAME_CONFLICT",
                "field": "owner_name",
                "source_a": src_a,
                "value_a": val_a,
                "source_b": src_b,
                "value_b": val_b,
                "discrepancy_measure": f"Name similarity is {owner_sim*100:.1f}%",
                "severity": "WARNING",
                "supporting_evidence": "Owner names may reflect transfer, co-ownership, or different spelling standards.",
                "suggested_value": pref_val,
                "suggested_value_rationale": pref_msg,
                "resolution_status": "PENDING"
            })

        # 3. Area Mismatch
        rel_diff = raw_metrics.get("relative_area_difference")
        if rel_diff is not None and rel_diff > 0.15:
            area_a = raw_metrics.get("area_a_sqm")
            area_b = raw_metrics.get("area_b_sqm")
            diff_sqm = raw_metrics.get("area_diff_sqm")
            pref_val, pref_msg = self.get_preferred_source_value(area_a, src_a, area_b, src_b)
            severity = "HIGH" if rel_diff > 0.35 else "WARNING"
            conflicts.append({
                "conflict_id": f"CONF-{uuid.uuid4().hex[:8].upper()}",
                "pair_id": pair_id,
                "category": "AREA_MISMATCH",
                "field": "land_area",
                "source_a": src_a,
                "value_a": f"{area_a} m²",
                "source_b": src_b,
                "value_b": f"{area_b} m²",
                "discrepancy_measure": f"Relative discrepancy of {rel_diff*100:.1f}% ({diff_sqm} m² diff)",
                "severity": severity,
                "supporting_evidence": "May reflect parcel sub-division, boundary recalculation, or unit conversion discrepancy.",
                "suggested_value": f"{pref_val} m²",
                "suggested_value_rationale": pref_msg,
                "resolution_status": "PENDING"
            })

        # 4. Address Mismatch
        addr_sim = feature_scores.get("address_similarity")
        if addr_sim is not None and addr_sim < 0.45:
            val_a = rec_a.get("property_address") or rec_a.get("village_or_locality")
            val_b = rec_b.get("property_address") or rec_b.get("village_or_locality")
            pref_val, pref_msg = self.get_preferred_source_value(val_a, src_a, val_b, src_b)
            conflicts.append({
                "conflict_id": f"CONF-{uuid.uuid4().hex[:8].upper()}",
                "pair_id": pair_id,
                "category": "ADDRESS_MISMATCH",
                "field": "property_address",
                "source_a": src_a,
                "value_a": val_a,
                "source_b": src_b,
                "value_b": val_b,
                "discrepancy_measure": f"Address similarity is {addr_sim*100:.1f}%",
                "severity": "WARNING",
                "supporting_evidence": "Addresses recorded across departments use varying street or ward descriptions.",
                "suggested_value": pref_val,
                "suggested_value_rationale": pref_msg,
                "resolution_status": "PENDING"
            })

        # 5. Geographic Boundary Mismatch
        dist = raw_metrics.get("distance_meters")
        iou = raw_metrics.get("polygon_iou")
        if dist is not None and dist > 300.0:
            conflicts.append({
                "conflict_id": f"CONF-{uuid.uuid4().hex[:8].upper()}",
                "pair_id": pair_id,
                "category": "GEOGRAPHIC_BOUNDARY_MISMATCH",
                "field": "coordinates_or_boundary",
                "source_a": src_a,
                "value_a": f"Lat: {rec_a.get('latitude')}, Lon: {rec_a.get('longitude')}",
                "source_b": src_b,
                "value_b": f"Lat: {rec_b.get('latitude')}, Lon: {rec_b.get('longitude')}",
                "discrepancy_measure": f"Centroids are separated by {dist:.1f} meters",
                "severity": "CRITICAL" if dist > 600.0 else "HIGH",
                "supporting_evidence": "Records share identifying traits but spatial locations are geographically distant.",
                "suggested_value": "Flag for GIS field verification",
                "suggested_value_rationale": "Large geographic separation requires manual surveyor review.",
                "resolution_status": "PENDING"
            })
        elif iou is not None and iou < 0.20 and s_exact == 1.0:
            conflicts.append({
                "conflict_id": f"CONF-{uuid.uuid4().hex[:8].upper()}",
                "pair_id": pair_id,
                "category": "GEOGRAPHIC_BOUNDARY_MISMATCH",
                "field": "parcel_geometry",
                "source_a": src_a,
                "value_a": "Polygon Geometry A",
                "source_b": src_b,
                "value_b": "Polygon Geometry B",
                "discrepancy_measure": f"Polygon intersection-over-union is only {iou*100:.1f}%",
                "severity": "HIGH",
                "supporting_evidence": "Identifiers match exactly but GIS boundary shapes show minimal topological overlap.",
                "suggested_value": "Review GIS boundary overlay",
                "suggested_value_rationale": "Administrative boundary dispute or surveying revision.",
                "resolution_status": "PENDING"
            })

        # 6. Land Use Disagreement
        lu_agr = feature_scores.get("land_use_agreement")
        if lu_agr is not None and lu_agr <= 0.10:
            val_a = rec_a.get("land_use_category")
            val_b = rec_b.get("land_use_category")
            pref_val, pref_msg = self.get_preferred_source_value(val_a, src_a, val_b, src_b)
            conflicts.append({
                "conflict_id": f"CONF-{uuid.uuid4().hex[:8].upper()}",
                "pair_id": pair_id,
                "category": "LAND_USE_DISAGREEMENT",
                "field": "land_use_category",
                "source_a": src_a,
                "value_a": val_a,
                "source_b": src_b,
                "value_b": val_b,
                "discrepancy_measure": f"Incompatible zoning/land use: '{val_a}' vs '{val_b}'",
                "severity": "WARNING",
                "supporting_evidence": "May reflect rezoning, pending conversion permits, or differing agency taxonomy.",
                "suggested_value": pref_val,
                "suggested_value_rationale": pref_msg,
                "resolution_status": "PENDING"
            })

        # 7. Missing Information
        if not rec_a.get("owner_name") or not rec_b.get("owner_name"):
            conflicts.append({
                "conflict_id": f"CONF-{uuid.uuid4().hex[:8].upper()}",
                "pair_id": pair_id,
                "category": "MISSING_INFORMATION",
                "field": "owner_name",
                "source_a": src_a,
                "value_a": rec_a.get("owner_name") or "<Missing>",
                "source_b": src_b,
                "value_b": rec_b.get("owner_name") or "<Missing>",
                "discrepancy_measure": "Owner name omitted in one or more records",
                "severity": "INFO",
                "supporting_evidence": "Records are eligible for matching but incomplete owner records exist.",
                "suggested_value": rec_a.get("owner_name") or rec_b.get("owner_name") or "N/A",
                "suggested_value_rationale": "Populate from available source record.",
                "resolution_status": "PENDING"
            })

        return conflicts
