"""
Tests for Conflict Detection, Source-Priority Policies, and Resolution Audit Ledger
"""

from reconciliation.conflict_detection import ConflictDetector
from reconciliation.resolution_service import ConflictResolutionService

def test_conflict_detection_and_source_priority():
    detector = ConflictDetector(source_priority_order=["Revenue Dept", "Municipal Authority"])
    rec_a = {
        "source_name": "Revenue Dept",
        "source_record_id": "R1",
        "parcel_or_survey_number": "14/1",
        "owner_name": "Rameshwar Prasad",
        "land_area": 4046.0
    }
    rec_b = {
        "source_name": "Municipal Authority",
        "source_record_id": "M1",
        "parcel_or_survey_number": "14/1",
        "owner_name": "Ramesh Kumar Sharma", # Divergent name
        "land_area": 2500.0 # Divergent area
    }
    feature_scores = {
        "exact_parcel_id": 1.0,
        "fuzzy_parcel_id": 1.0,
        "owner_name_similarity": 0.45
    }
    raw_metrics = {
        "relative_area_difference": 0.38,
        "area_a_sqm": 4046.0,
        "area_b_sqm": 2500.0,
        "area_diff_sqm": 1546.0
    }
    conflicts = detector.detect_conflicts({}, rec_a, rec_b, feature_scores, raw_metrics)
    
    # Should detect owner name conflict and area mismatch
    categories = [c["category"] for c in conflicts]
    assert "OWNER_NAME_CONFLICT" in categories
    assert "AREA_MISMATCH" in categories

    # Verify administrative source priority preference
    area_conf = next(c for c in conflicts if c["category"] == "AREA_MISMATCH")
    assert "Revenue Dept" in area_conf["suggested_value_rationale"]

def test_resolution_audit_logging():
    res_service = ConflictResolutionService()
    test_conflict = {
        "conflict_id": "CONF-TEST-01",
        "pair_id": "PAIR-01",
        "resolution_status": "PENDING"
    }
    res = res_service.resolve_conflict(
        conflict=test_conflict,
        action="CONFIRM_MATCH",
        reviewer_id="Senior_Reviewer_A",
        reason="Field inspection confirmed boundary revision",
        selected_value="4046.0 m²",
        reviewer_notes="Verified via Cadastral Sheet 4"
    )
    assert res["status"] == "success"
    assert test_conflict["resolution_status"] == "CONFIRM_MATCH"
    assert test_conflict["resolved_value"] == "4046.0 m²"

    # Verify audit trail record
    trail = res_service.get_audit_trail("CONF-TEST-01")
    assert len(trail) == 1
    assert trail[0]["reviewer_id"] == "Senior_Reviewer_A"
    assert trail[0]["previous_state"] == "PENDING"
    assert trail[0]["new_state"] == "CONFIRM_MATCH"

