"""
End-to-End Land Record Matching and Reconciliation Pipeline Service
Integrates blocking, attribute similarity, semantic matching, rule engine,
confidence scoring, explainability, conflict detection, and entity linking.
"""

import time
import uuid
import json
from typing import List, Dict, Any, Optional
from matching.candidate_generation import CandidateGenerator
from matching.similarity import calculate_attribute_similarity
from matching.semantic_matching import SemanticMatcher
from reasoning.rules import RuleEngine
from reasoning.explanations import ExplanationGenerator
from matching.confidence import ConfidenceScorer
from matching.entity_linking import CrossSourceEntityLinker
from reconciliation.conflict_detection import ConflictDetector

class MatchingPipelineService:
    def __init__(
        self,
        rules_file_path: Optional[str] = None,
        source_priority: Optional[List[str]] = None
    ):
        self.rule_engine = RuleEngine(rules_file_path)
        self.semantic_matcher = SemanticMatcher()
        self.conflict_detector = ConflictDetector(source_priority)
        self.entity_linker = CrossSourceEntityLinker()

    def run_matching(
        self,
        records_by_source: Dict[str, List[Dict[str, Any]]],
        high_threshold: float = 0.80,
        medium_threshold: float = 0.55,
        enable_survey_blocking: bool = True,
        enable_spatial_blocking: bool = True,
        enable_locality_area_blocking: bool = True,
        area_tolerance_ratio: float = 0.30,
        custom_weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Executes complete multi-source matching and conflict detection pipeline.
        """
        start_time = time.time()
        candidate_generator = CandidateGenerator(
            enable_survey_blocking=enable_survey_blocking,
            enable_spatial_blocking=enable_spatial_blocking,
            enable_locality_area_blocking=enable_locality_area_blocking,
            area_tolerance_ratio=area_tolerance_ratio
        )
        scorer = ConfidenceScorer(
            weights=custom_weights,
            high_threshold=high_threshold,
            medium_threshold=medium_threshold
        )

        sources = list(records_by_source.keys())
        all_candidate_pairs: List[Dict[str, Any]] = []
        all_conflicts: List[Dict[str, Any]] = []
        all_records_lookup: Dict[str, Dict[str, Any]] = {}

        # Populate all records lookup
        for s_name, recs in records_by_source.items():
            for r in recs:
                rec_id = str(r.get("source_record_id"))
                all_records_lookup[rec_id] = r

        # Cross-source pairwise generation
        raw_candidate_tuples = []
        for i in range(len(sources)):
            for j in range(i + 1, len(sources)):
                src_i = sources[i]
                src_j = sources[j]
                pairs = candidate_generator.generate_candidates(
                    records_by_source[src_i],
                    records_by_source[src_j]
                )
                raw_candidate_tuples.extend(pairs)

        # Process each candidate pair
        accepted_for_linking = []

        for rec_a, rec_b, blocking_reasons in raw_candidate_tuples:
            pair_id = f"PAIR-{uuid.uuid4().hex[:10].upper()}"
            
            # Stage B: Attribute similarity
            sim_result = calculate_attribute_similarity(
                rec_a,
                rec_b,
                area_tolerance_ratio=area_tolerance_ratio
            )
            feature_scores = sim_result["feature_scores"]
            raw_metrics = sim_result["raw_metrics"]
            missing_features = sim_result["missing_features"]

            # Stage C: Semantic matching on addresses & remarks
            addr_a = rec_a.get("property_address") or rec_a.get("village_or_locality")
            addr_b = rec_b.get("property_address") or rec_b.get("village_or_locality")
            sem_sim = self.semantic_matcher.compute_semantic_similarity(addr_a, addr_b)
            if sem_sim is not None:
                feature_scores["semantic_similarity"] = sem_sim
                raw_metrics["semantic_similarity"] = sem_sim
            else:
                missing_features.append("semantic_similarity")

            # Preliminary score
            initial_score_res = scorer.calculate_confidence(feature_scores, rule_adjustment=0.0)
            preliminary_score = initial_score_res["preliminary_score"]

            # Rule-based reasoning
            rule_eval = self.rule_engine.evaluate(
                rec_a,
                rec_b,
                feature_scores,
                raw_metrics,
                preliminary_score
            )
            rule_adjustment = rule_eval["confidence_adjustment"]
            rule_flags = rule_eval["flags"]
            triggered_rules = rule_eval["triggered_rules"]

            # Final confidence & classification
            final_conf_res = scorer.calculate_confidence(
                feature_scores,
                rule_adjustment=rule_adjustment,
                rule_flags=rule_flags
            )

            # Explainable AI payload
            explanation = ExplanationGenerator.generate_explanation(
                match_decision=final_conf_res["match_decision"],
                confidence_score=final_conf_res["final_confidence"],
                feature_scores=feature_scores,
                raw_metrics=raw_metrics,
                missing_features=missing_features,
                triggered_rules=triggered_rules,
                effective_weights=final_conf_res["effective_weights"]
            )

            pair_obj = {
                "pair_id": pair_id,
                "source_record_id_a": rec_a.get("source_record_id"),
                "source_record_id_b": rec_b.get("source_record_id"),
                "source_a_name": rec_a.get("source_name"),
                "source_b_name": rec_b.get("source_name"),
                "record_a": rec_a,
                "record_b": rec_b,
                "blocking_reasons": blocking_reasons,
                "final_confidence": final_conf_res["final_confidence"],
                "preliminary_score": final_conf_res["preliminary_score"],
                "rule_adjustment": rule_adjustment,
                "match_decision": final_conf_res["match_decision"],
                "is_automatic_match": final_conf_res["is_automatic_match"],
                "requires_manual_review": final_conf_res["requires_manual_review"],
                "score_type": final_conf_res["score_type"],
                "feature_scores": feature_scores,
                "effective_weights": final_conf_res["effective_weights"],
                "raw_metrics": raw_metrics,
                "missing_features": missing_features,
                "triggered_rules": triggered_rules,
                "explanation": explanation,
                "reviewer_decision": None,
                "reviewer_id": None,
                "reviewer_notes": None
            }

            all_candidate_pairs.append(pair_obj)

            # If High confidence, queue for cross-source entity linking
            if final_conf_res["is_automatic_match"]:
                accepted_for_linking.append(pair_obj)

            # Conflict Detection
            pair_conflicts = self.conflict_detector.detect_conflicts(
                candidate_pair=pair_obj,
                rec_a=rec_a,
                rec_b=rec_b,
                feature_scores=feature_scores,
                raw_metrics=raw_metrics
            )
            all_conflicts.extend(pair_conflicts)

        # Stage F: Cross-Source Entity Linking
        unified_entities = self.entity_linker.link_entities(
            accepted_for_linking,
            all_records_lookup
        )

        elapsed_seconds = round(time.time() - start_time, 4)

        # Aggregate counts
        high_conf_count = sum(1 for p in all_candidate_pairs if p["match_decision"] == "HIGH_CONFIDENCE")
        med_conf_count = sum(1 for p in all_candidate_pairs if p["match_decision"] == "MEDIUM_CONFIDENCE")
        low_conf_count = sum(1 for p in all_candidate_pairs if p["match_decision"] == "LOW_CONFIDENCE")

        return {
            "execution_time_seconds": elapsed_seconds,
            "total_candidate_pairs": len(all_candidate_pairs),
            "high_confidence_matches": high_conf_count,
            "medium_confidence_reviews": med_conf_count,
            "low_confidence_rejected": low_conf_count,
            "total_conflicts_detected": len(all_conflicts),
            "unified_entities_count": len(unified_entities),
            "candidate_pairs": all_candidate_pairs,
            "conflicts": all_conflicts,
            "unified_entities": unified_entities
        }

