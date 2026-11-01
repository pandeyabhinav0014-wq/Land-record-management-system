"""
Integration and Endpoint Logic Tests for Land Record Reconciliation API
Tests route handlers directly in-process.
"""

import pytest
from backend.app.api.routes import (
    get_health,
    list_sources,
    get_matching_results,
    get_candidate_pair_detail,
    resolve_candidate_pair,
    get_conflicts,
    resolve_conflict_item,
    get_evaluation_metrics,
    get_threshold_analysis,
    export_data,
    app_state
)
from backend.app.schemas.record_schema import ConflictResolutionRequest

def test_api_health():
    res = get_health()
    assert res["status"] == "healthy"
    assert res["active_sources"] >= 3
    assert res["candidate_pairs_count"] > 0

def test_list_sources():
    res = list_sources()
    assert len(res["sources"]) >= 3
    source_names = [s["source_name"] for s in res["sources"]]
    assert "Revenue Department" in source_names
    assert "Municipal Property Records" in source_names
    assert "GIS Survey Records" in source_names

def test_matching_results_and_detail():
    res = get_matching_results(decision=None, min_confidence=None, limit=50)
    assert res["total_count"] > 0
    assert len(res["candidate_pairs"]) > 0

    first_pair = res["candidate_pairs"][0]
    pair_id = first_pair["pair_id"]

    detail = get_candidate_pair_detail(pair_id)
    assert detail["candidate_pair"]["pair_id"] == pair_id
    assert "explanation" in detail["candidate_pair"]
    assert "summary" in detail["candidate_pair"]["explanation"]

def test_resolve_candidate_pair():
    pairs = app_state["candidate_pairs"]
    assert len(pairs) > 0
    p = pairs[0]
    pair_id = p["pair_id"]

    req = ConflictResolutionRequest(
        action="CONFIRM_MATCH",
        reviewer_id="Reviewer_Officer_42",
        reason="Field deed records cross-verified against survey map",
        reviewer_notes="High boundary overlap"
    )
    res = resolve_candidate_pair(pair_id, req)
    assert res["status"] == "success"
    assert res["pair"]["reviewer_decision"] == "CONFIRM_MATCH"
    assert res["audit_entry"]["reviewer_id"] == "Reviewer_Officer_42"

def test_conflict_list_and_resolve():
    confs = get_conflicts(severity=None, status=None, limit=50)
    assert confs["total_conflicts"] > 0
    first_c = confs["conflicts"][0]
    c_id = first_c["conflict_id"]

    req = ConflictResolutionRequest(
        action="SELECT_PREFERRED_VALUE",
        reviewer_id="Chief_Reconciler",
        reason="Administrative survey priority applied",
        selected_value=first_c.get("suggested_value") or "Selected Value"
    )
    res = resolve_conflict_item(c_id, req)
    assert res["status"] == "success"
    assert res["conflict"]["resolution_status"] == "SELECT_PREFERRED_VALUE"

def test_evaluation_metrics_endpoint():
    res = get_evaluation_metrics()
    assert "evaluation_metrics" in res
    assert res["labeled_pairs_evaluated"] > 0
    metrics = res["evaluation_metrics"]
    assert "precision" in metrics
    assert "recall" in metrics
    assert "f1_score" in metrics
    assert "confusion_matrix" in metrics

def test_threshold_analysis_endpoint():
    res = get_threshold_analysis()
    assert "threshold_analysis" in res
    assert len(res["threshold_analysis"]) == 5 # 0.50, 0.60, 0.70, 0.80, 0.90
    assert "reproducibility_metadata" in res
    assert res["reproducibility_metadata"]["random_seed"] == 42

def test_export_data():
    csv_resp = export_data("matching", format="csv")
    assert "pair_id" in csv_resp.body.decode("utf-8")

    json_resp = export_data("conflicts", format="json")
    assert isinstance(json_resp, list)

