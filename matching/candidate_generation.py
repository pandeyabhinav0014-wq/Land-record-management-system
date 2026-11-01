"""
Candidate Generation (Stage A Blocking)
Filters plausible record pairs across multiple sources using multi-index blocking:
- Exact/normalized survey number agreement
- Survey number root match + locality
- Spatial proximity / bounding box overlap
- Locality + Area similarity
- Locality + High owner name similarity
Prevents full Cartesian product (N * M) while preserving high recall.
"""

from typing import List, Dict, Any, Set, Tuple
from collections import defaultdict
import re
from rapidfuzz import fuzz
from gis.spatial_matching import haversine_distance_meters

class CandidateGenerator:
    def __init__(
        self,
        enable_survey_blocking: bool = True,
        enable_spatial_blocking: bool = True,
        enable_locality_area_blocking: bool = True,
        enable_owner_locality_blocking: bool = True,
        max_spatial_distance_meters: float = 800.0,
        area_tolerance_ratio: float = 0.35,
        min_fuzzy_survey_ratio: float = 75.0,
    ):
        self.enable_survey_blocking = enable_survey_blocking
        self.enable_spatial_blocking = enable_spatial_blocking
        self.enable_locality_area_blocking = enable_locality_area_blocking
        self.enable_owner_locality_blocking = enable_owner_locality_blocking
        self.max_spatial_distance_meters = max_spatial_distance_meters
        self.area_tolerance_ratio = area_tolerance_ratio
        self.min_fuzzy_survey_ratio = min_fuzzy_survey_ratio

    @staticmethod
    def _get_survey_root(survey_no: str) -> str:
        """Extract root number: e.g. '14/2-A' -> '14'"""
        if not survey_no:
            return ""
        m = re.match(r"^(\d+)", survey_no)
        return m.group(1) if m else survey_no[:4]

    def generate_candidates(
        self,
        records_a: List[Dict[str, Any]],
        records_b: List[Dict[str, Any]]
    ) -> List[Tuple[Dict[str, Any], Dict[str, Any], List[str]]]:
        """
        Generate candidate pairs between records_a and records_b.
        Returns list of tuples: (record_a, record_b, [blocking_reasons])
        """
        candidate_map: Dict[Tuple[str, str], Tuple[Dict[str, Any], Dict[str, Any], Set[str]]] = {}

        # Pre-index records_b for fast lookup
        survey_index_b = defaultdict(list)
        root_survey_index_b = defaultdict(list)
        locality_index_b = defaultdict(list)

        for rb in records_b:
            rec_id_b = str(rb.get("source_record_id"))
            s_no = rb.get("parcel_or_survey_number")
            loc = rb.get("village_or_locality")

            if s_no:
                s_norm = str(s_no).strip().upper()
                survey_index_b[s_norm].append(rb)
                root = self._get_survey_root(s_norm)
                if root:
                    root_survey_index_b[root].append(rb)

            if loc:
                loc_norm = str(loc).strip().upper()
                locality_index_b[loc_norm].append(rb)

        for ra in records_a:
            rec_id_a = str(ra.get("source_record_id"))
            s_no_a = ra.get("parcel_or_survey_number")
            loc_a = ra.get("village_or_locality")
            area_a = ra.get("land_area")
            owner_a = ra.get("owner_name")
            lat_a = ra.get("latitude")
            lon_a = ra.get("longitude")

            s_norm_a = str(s_no_a).strip().upper() if s_no_a else ""
            loc_norm_a = str(loc_a).strip().upper() if loc_a else ""

            # 1. Exact survey number match
            if self.enable_survey_blocking and s_norm_a:
                for rb in survey_index_b.get(s_norm_a, []):
                    rec_id_b = str(rb.get("source_record_id"))
                    pair_key = (rec_id_a, rec_id_b)
                    if pair_key not in candidate_map:
                        candidate_map[pair_key] = (ra, rb, set())
                    candidate_map[pair_key][2].add("Exact survey number agreement")

            # 2. Survey root agreement + same locality
            if self.enable_survey_blocking and s_norm_a:
                root_a = self._get_survey_root(s_norm_a)
                if root_a and root_a in root_survey_index_b:
                    for rb in root_survey_index_b[root_a]:
                        rec_id_b = str(rb.get("source_record_id"))
                        pair_key = (rec_id_a, rec_id_b)
                        loc_b = rb.get("village_or_locality")
                        loc_norm_b = str(loc_b).strip().upper() if loc_b else ""
                        
                        # Match if localities agree or are blank
                        if not loc_norm_a or not loc_norm_b or loc_norm_a == loc_norm_b:
                            if pair_key not in candidate_map:
                                candidate_map[pair_key] = (ra, rb, set())
                            candidate_map[pair_key][2].add("Survey root agreement with compatible locality")

            # 3. Locality-based blocking: Area similarity, fuzzy survey, or owner similarity
            if loc_norm_a and loc_norm_a in locality_index_b:
                for rb in locality_index_b[loc_norm_a]:
                    rec_id_b = str(rb.get("source_record_id"))
                    pair_key = (rec_id_a, rec_id_b)

                    # Fuzzy survey match in same locality
                    s_no_b = rb.get("parcel_or_survey_number")
                    if s_norm_a and s_no_b:
                        s_norm_b = str(s_no_b).strip().upper()
                        f_ratio = fuzz.ratio(s_norm_a, s_norm_b)
                        if f_ratio >= self.min_fuzzy_survey_ratio:
                            if pair_key not in candidate_map:
                                candidate_map[pair_key] = (ra, rb, set())
                            candidate_map[pair_key][2].add(f"Fuzzy survey similarity ({f_ratio:.0f}%) in same locality")

                    # Area similarity in same locality
                    if self.enable_locality_area_blocking and area_a is not None:
                        area_b = rb.get("land_area")
                        if area_b is not None and area_a > 0 and area_b > 0:
                            rel_diff = abs(area_a - area_b) / max(area_a, area_b)
                            if rel_diff <= self.area_tolerance_ratio:
                                if pair_key not in candidate_map:
                                    candidate_map[pair_key] = (ra, rb, set())
                                candidate_map[pair_key][2].add(f"Area similarity (diff: {rel_diff*100:.1f}%) in same locality")

                    # Owner name similarity in same locality
                    if self.enable_owner_locality_blocking and owner_a:
                        owner_b = rb.get("owner_name")
                        if owner_b:
                            name_sim = fuzz.token_sort_ratio(str(owner_a), str(owner_b))
                            if name_sim >= 80.0:
                                if pair_key not in candidate_map:
                                    candidate_map[pair_key] = (ra, rb, set())
                                candidate_map[pair_key][2].add(f"Owner name similarity ({name_sim:.0f}%) in same locality")

            # 4. Spatial distance blocking (when coordinates available)
            if self.enable_spatial_blocking and lat_a is not None and lon_a is not None:
                for rb in records_b:
                    lat_b = rb.get("latitude")
                    lon_b = rb.get("longitude")
                    if lat_b is not None and lon_b is not None:
                        rec_id_b = str(rb.get("source_record_id"))
                        pair_key = (rec_id_a, rec_id_b)
                        # Quick bounding box filter before haversine
                        # 1 deg lat ~= 111 km -> 1000m ~= 0.009 deg
                        if abs(lat_a - lat_b) < 0.015 and abs(lon_a - lon_b) < 0.015:
                            dist = haversine_distance_meters(lat_a, lon_a, lat_b, lon_b)
                            if dist <= self.max_spatial_distance_meters:
                                if pair_key not in candidate_map:
                                    candidate_map[pair_key] = (ra, rb, set())
                                candidate_map[pair_key][2].add(f"Spatial proximity ({dist:.1f}m apart)")

        # Convert to list with sorted list of blocking reasons
        results = []
        for (rec_a, rec_b, reasons) in candidate_map.values():
            results.append((rec_a, rec_b, sorted(list(reasons))))
        return results

