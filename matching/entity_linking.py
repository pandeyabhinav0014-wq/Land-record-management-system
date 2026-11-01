"""
Cross-Source Entity Linking (Stage F)
Uses NetworkX graph clusters to group records across 2 or more sources into unified parcel entities.
Enforces transitive consistency verification to prevent erroneous chaining (A matches B, B matches C,
but A and C conflict).
"""

from typing import List, Dict, Any, Set, Tuple, Optional
import networkx as nx
from matching.similarity import calculate_attribute_similarity

class CrossSourceEntityLinker:
    def __init__(self, transitive_compatibility_tolerance: float = 0.40):
        self.transitive_tolerance = transitive_compatibility_tolerance

    def link_entities(
        self,
        accepted_pairs: List[Dict[str, Any]],
        all_records_by_id: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Builds entity graph from accepted pairwise matches, validates transitive consistency,
        and constructs unified parcel clusters.
        """
        graph = nx.Graph()

        # Add all accepted match edges
        for pair in accepted_pairs:
            id_a = str(pair.get("source_record_id_a"))
            id_b = str(pair.get("source_record_id_b"))
            conf = pair.get("final_confidence", 0.0)
            graph.add_edge(id_a, id_b, confidence=conf, pair_data=pair)

        # Find connected components
        components = list(nx.connected_components(graph))
        entities: List[Dict[str, Any]] = []
        entity_counter = 1

        for comp in components:
            member_ids = list(comp)
            
            # If 2 members, transitive check is trivial
            if len(member_ids) <= 2:
                entity = self._create_entity(entity_counter, member_ids, all_records_by_id, has_conflict=False)
                entities.append(entity)
                entity_counter += 1
                continue

            # Check pairwise compatibility for 3+ records (Transitive verification)
            is_compatible = True
            conflict_details = []

            for i in range(len(member_ids)):
                for j in range(i + 1, len(member_ids)):
                    rec_i = all_records_by_id.get(member_ids[i])
                    rec_j = all_records_by_id.get(member_ids[j])
                    if not rec_i or not rec_j:
                        continue
                    
                    # Verify area compatibility
                    area_i = rec_i.get("land_area")
                    area_j = rec_j.get("land_area")
                    if area_i and area_j and area_i > 0 and area_j > 0:
                        rel_diff = abs(area_i - area_j) / max(area_i, area_j)
                        if rel_diff > self.transitive_tolerance:
                            is_compatible = False
                            conflict_details.append(
                                f"Transitive area mismatch ({rel_diff*100:.1f}%) between record {member_ids[i]} and {member_ids[j]}"
                            )

            if is_compatible:
                entity = self._create_entity(entity_counter, member_ids, all_records_by_id, has_conflict=False)
                entities.append(entity)
                entity_counter += 1
            else:
                # Flag transitive cluster conflict
                entity = self._create_entity(
                    entity_counter,
                    member_ids,
                    all_records_by_id,
                    has_conflict=True,
                    conflict_notes=conflict_details
                )
                entities.append(entity)
                entity_counter += 1

        return entities

    def _create_entity(
        self,
        entity_id_num: int,
        member_ids: List[str],
        records_lookup: Dict[str, Dict[str, Any]],
        has_conflict: bool = False,
        conflict_notes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Creates a standardized Unified Parcel Entity dictionary."""
        members = [records_lookup.get(mid) for mid in member_ids if mid in records_lookup]
        sources = list(set(m.get("source_name", "UNKNOWN") for m in members if m))
        
        # Pick primary representation
        primary_record = members[0] if members else {}

        return {
            "entity_id": f"PARCEL-ENT-{entity_id_num:04d}",
            "member_record_ids": member_ids,
            "source_count": len(sources),
            "sources": sorted(sources),
            "member_count": len(members),
            "primary_survey_number": primary_record.get("parcel_or_survey_number"),
            "primary_locality": primary_record.get("village_or_locality"),
            "has_transitive_conflict": has_conflict,
            "transitive_conflict_notes": conflict_notes or [],
            "records": members
        }

