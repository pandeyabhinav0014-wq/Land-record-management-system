"""
Tests for Candidate Generation, Attribute Similarity, Rules, Confidence, and Entity Linking
"""

from matching.candidate_generation import CandidateGenerator
from matching.similarity import calculate_attribute_similarity
from matching.confidence import ConfidenceScorer
from matching.entity_linking import CrossSourceEntityLinker
from reasoning.rules import RuleEngine
from reasoning.explanations import ExplanationGenerator

def test_candidate_generation_blocking():
    recs_a = [
        {"source_record_id": "A1", "parcel_or_survey_number": "14/1", "village_or_locality": "RAMPUR", "land_area": 4000.0},
        {"source_record_id": "A2", "parcel_or_survey_number": "99/9", "village_or_locality": "OTHER", "land_area": 1000.0}
    ]
    recs_b = [
        {"source_record_id": "B1", "parcel_or_survey_number": "14/1", "village_or_locality": "RAMPUR", "land_area": 4050.0},
        {"source_record_id": "B2", "parcel_or_survey_number": "88/8", "village_or_locality": "UNKNOWN", "land_area": 5000.0}
    ]
    gen = CandidateGenerator()
    candidates = gen.generate_candidates(recs_a, recs_b)
    
    # Should match A1 and B1 due to exact survey number
    assert len(candidates) >= 1
    matched_ids = [(c[0]["source_record_id"], c[1]["source_record_id"]) for c in candidates]
    assert ("A1", "B1") in matched_ids
    assert ("A2", "B2") not in matched_ids

def test_missing_features_do_not_penalize():
    rec_a = {"parcel_or_survey_number": "14/1", "land_area": 1000.0}
    rec_b = {"parcel_or_survey_number": "14/1", "land_area": 1000.0}
    
    sim = calculate_attribute_similarity(rec_a, rec_b)
    assert "owner_name_similarity" in sim["missing_features"]
    assert "address_similarity" in sim["missing_features"]
    
    # Score without missing features
    scorer = ConfidenceScorer()
    res = scorer.calculate_confidence(sim["feature_scores"])
    # Exact survey and area match should yield high confidence despite missing owner & address
    assert res["final_confidence"] >= 0.85
    assert res["effective_weights"]["survey_number_agreement"] > 0.25 # Renormalized upwards

def test_transitive_conflict_detection_in_linking():
    linker = CrossSourceEntityLinker(transitive_compatibility_tolerance=0.30)
    # A matches B, B matches C, but A and C have vast area discrepancy (1000 vs 5000 sqm)
    accepted_pairs = [
        {"source_record_id_a": "A1", "source_record_id_b": "B1", "final_confidence": 0.85},
        {"source_record_id_a": "B1", "source_record_id_b": "C1", "final_confidence": 0.82}
    ]
    records_lookup = {
        "A1": {"source_name": "S1", "source_record_id": "A1", "land_area": 1000.0, "parcel_or_survey_number": "10"},
        "B1": {"source_name": "S2", "source_record_id": "B1", "land_area": 1200.0, "parcel_or_survey_number": "10"},
        "C1": {"source_name": "S3", "source_record_id": "C1", "land_area": 5000.0, "parcel_or_survey_number": "10"},
    }
    entities = linker.link_entities(accepted_pairs, records_lookup)
    assert len(entities) == 1
    assert entities[0]["has_transitive_conflict"] is True
    assert len(entities[0]["transitive_conflict_notes"]) > 0

