"""
Attribute Similarity Pipeline (Stage B)
Calculates independent similarity features for candidate pairs:
- Exact & fuzzy parcel ID
- Survey number agreement
- Owner name similarity (RapidFuzz token sort/partial)
- Address similarity (RapidFuzz token set)
- Relative land area difference & similarity score
- Spatial distance & polygon IoU
- Land-use category agreement
Explicitly tracks missing attributes without penalizing as mismatches.
"""

from typing import Dict, Any, List, Optional
from rapidfuzz import fuzz
from gis.spatial_matching import calculate_spatial_similarity

LAND_USE_COMPATIBILITY = {
    ("AGRICULTURAL", "AGRICULTURE"): 1.0,
    ("RESIDENTIAL", "HOUSING"): 1.0,
    ("COMMERCIAL", "BUSINESS"): 1.0,
    ("AGRICULTURAL", "RURAL_RESIDENTIAL"): 0.5,
    ("RESIDENTIAL", "COMMERCIAL"): 0.3, # Mixed use
    ("RESIDENTIAL", "MIXED"): 0.7,
    ("COMMERCIAL", "MIXED"): 0.7,
    ("INDUSTRIAL", "COMMERCIAL"): 0.3,
    ("AGRICULTURAL", "INDUSTRIAL"): 0.0,
    ("RESIDENTIAL", "INDUSTRIAL"): 0.0,
}

def compare_land_use(cat1: Optional[str], cat2: Optional[str]) -> Optional[float]:
    """
    Returns compatibility score [0.0, 1.0] or None if either is missing.
    """
    if not cat1 or not cat2:
        return None
    c1 = str(cat1).strip().upper()
    c2 = str(cat2).strip().upper()
    if c1 == c2:
        return 1.0
    pair = (c1, c2)
    inv_pair = (c2, c1)
    if pair in LAND_USE_COMPATIBILITY:
        return LAND_USE_COMPATIBILITY[pair]
    if inv_pair in LAND_USE_COMPATIBILITY:
        return LAND_USE_COMPATIBILITY[inv_pair]
    return 0.2 # Slight generic overlap if unknown

def calculate_attribute_similarity(
    rec_a: Dict[str, Any],
    rec_b: Dict[str, Any],
    area_tolerance_ratio: float = 0.30
) -> Dict[str, Any]:
    """
    Computes fine-grained feature similarities between rec_a and rec_b.
    Returns:
      feature_scores: dict of float values in [0.0, 1.0] for present attributes
      raw_metrics: dict of raw measurements (e.g. actual distance in meters, area diff in m²)
      missing_features: list of feature names missing in one or both records
      available_features: list of feature names present in both records
    """
    feature_scores: Dict[str, float] = {}
    raw_metrics: Dict[str, Any] = {}
    missing_features: List[str] = []
    available_features: List[str] = []

    # 1. Survey / Parcel Number
    s_a = rec_a.get("parcel_or_survey_number")
    s_b = rec_b.get("parcel_or_survey_number")
    if s_a and s_b:
        s_a_str = str(s_a).strip().upper()
        s_b_str = str(s_b).strip().upper()
        exact = 1.0 if s_a_str == s_b_str else 0.0
        fuzzy = round(fuzz.ratio(s_a_str, s_b_str) / 100.0, 4)
        
        feature_scores["exact_parcel_id"] = exact
        feature_scores["fuzzy_parcel_id"] = fuzzy
        # Survey agreement can consider token matches
        survey_tok = round(fuzz.token_sort_ratio(s_a_str, s_b_str) / 100.0, 4)
        feature_scores["survey_number_agreement"] = max(exact, survey_tok)
        
        raw_metrics["survey_a"] = s_a_str
        raw_metrics["survey_b"] = s_b_str
        available_features.extend(["exact_parcel_id", "fuzzy_parcel_id", "survey_number_agreement"])
    else:
        missing_features.extend(["exact_parcel_id", "fuzzy_parcel_id", "survey_number_agreement"])

    # 2. Owner Name
    o_a = rec_a.get("owner_name")
    o_b = rec_b.get("owner_name")
    if o_a and o_b:
        o_a_str = str(o_a).strip().upper()
        o_b_str = str(o_b).strip().upper()
        # Token sort ratio handles swapped first/last name
        name_sim = round(fuzz.token_sort_ratio(o_a_str, o_b_str) / 100.0, 4)
        feature_scores["owner_name_similarity"] = name_sim
        raw_metrics["owner_a"] = o_a_str
        raw_metrics["owner_b"] = o_b_str
        available_features.append("owner_name_similarity")
    else:
        missing_features.append("owner_name_similarity")

    # 3. Address / Locality
    addr_a = rec_a.get("property_address") or rec_a.get("village_or_locality")
    addr_b = rec_b.get("property_address") or rec_b.get("village_or_locality")
    if addr_a and addr_b:
        addr_a_str = str(addr_a).strip().upper()
        addr_b_str = str(addr_b).strip().upper()
        addr_sim = round(fuzz.token_set_ratio(addr_a_str, addr_b_str) / 100.0, 4)
        feature_scores["address_similarity"] = addr_sim
        raw_metrics["address_a"] = addr_a_str
        raw_metrics["address_b"] = addr_b_str
        available_features.append("address_similarity")
    else:
        missing_features.append("address_similarity")

    # 4. Land Area
    area_a = rec_a.get("land_area")
    area_b = rec_b.get("land_area")
    if area_a is not None and area_b is not None and area_a > 0 and area_b > 0:
        abs_diff = abs(area_a - area_b)
        rel_diff = abs_diff / max(area_a, area_b)
        raw_metrics["area_a_sqm"] = area_a
        raw_metrics["area_b_sqm"] = area_b
        raw_metrics["area_diff_sqm"] = round(abs_diff, 2)
        raw_metrics["relative_area_difference"] = round(rel_diff, 4)
        
        # Area similarity score: decays linearly up to 2 * area_tolerance_ratio
        area_score = max(0.0, 1.0 - (rel_diff / max(0.01, area_tolerance_ratio)))
        feature_scores["area_similarity"] = round(area_score, 4)
        available_features.append("area_similarity")
    else:
        missing_features.append("area_similarity")

    # 5. Spatial & GIS Features
    spatial_res = calculate_spatial_similarity(
        geom1=rec_a.get("parcel_geometry"),
        geom2=rec_b.get("parcel_geometry"),
        lat1=rec_a.get("latitude"),
        lon1=rec_a.get("longitude"),
        lat2=rec_b.get("latitude"),
        lon2=rec_b.get("longitude"),
    )
    
    if spatial_res["points_available"] or spatial_res["geometries_available"]:
        feature_scores["spatial_proximity"] = spatial_res["spatial_proximity_score"]
        available_features.append("spatial_proximity")
        raw_metrics["distance_meters"] = spatial_res["geographic_distance_meters"]

        if spatial_res["polygon_iou"] is not None:
            feature_scores["polygon_iou"] = spatial_res["polygon_iou"]
            available_features.append("polygon_iou")
            raw_metrics["polygon_iou"] = spatial_res["polygon_iou"]
            raw_metrics["containment_ratio"] = spatial_res["containment_ratio"]
        else:
            missing_features.append("polygon_iou")
    else:
        missing_features.extend(["spatial_proximity", "polygon_iou"])

    # 6. Land Use
    lu_a = rec_a.get("land_use_category")
    lu_b = rec_b.get("land_use_category")
    lu_score = compare_land_use(lu_a, lu_b)
    if lu_score is not None:
        feature_scores["land_use_agreement"] = round(lu_score, 4)
        available_features.append("land_use_agreement")
        raw_metrics["land_use_a"] = lu_a
        raw_metrics["land_use_b"] = lu_b
    else:
        missing_features.append("land_use_agreement")

    return {
        "feature_scores": feature_scores,
        "raw_metrics": raw_metrics,
        "missing_features": missing_features,
        "available_features": available_features
    }

