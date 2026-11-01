"""
FastAPI REST API Routes for Multi-Source Land Record Matching System
"""

import uuid
import json
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query, Response
from fastapi.responses import JSONResponse, PlainTextResponse

from backend.app.schemas.record_schema import (
    MatchingRunConfig,
    ConflictResolutionRequest,
    RuleDefinition
)
from backend.app.services.ingestion_service import IngestionService
from backend.app.services.matching_service import MatchingPipelineService
from backend.app.services.export_service import ExportService
from reconciliation.resolution_service import ConflictResolutionService
from evaluation.ground_truth import generate_benchmark_datasets
from evaluation.metrics import compute_evaluation_metrics
from evaluation.threshold_analysis import ThresholdSensitivityAnalyzer
from reasoning.rules import DEFAULT_RULES_PATH

router = APIRouter(prefix="/api")

# In-memory application state with persistence bridges
app_state = {
    "sources": {},           # source_id -> { "name": ..., "records": [...], "quality_report": ... }
    "candidate_pairs": [],   # list of candidate pair dicts
    "conflicts": [],         # list of conflict dicts
    "unified_entities": [],  # list of unified parcel entities
    "resolution_service": ConflictResolutionService(),
    "matching_service": MatchingPipelineService(),
    "latest_matching_run_meta": None,
    "ground_truth_lookup": {}, # (id_a, id_b) -> bool
}

# Pre-populate state with benchmark ground-truth
def init_sample_data():
    src_a, src_b, src_c, gt_pairs = generate_benchmark_datasets()
    
    # Store ground truth lookup
    for gt in gt_pairs:
        app_state["ground_truth_lookup"][(gt["source_record_id_a"], gt["source_record_id_b"])] = gt["is_match"]
        app_state["ground_truth_lookup"][(gt["source_record_id_b"], gt["source_record_id_a"])] = gt["is_match"]

    # Register benchmark sources
    app_state["sources"]["SRC-REV"] = {
        "source_id": "SRC-REV",
        "source_name": "Revenue Department",
        "file_format": "JSON",
        "records": src_a,
        "quality_report": {
            "source_id": "SRC-REV",
            "source_name": "Revenue Department",
            "total_records": len(src_a),
            "valid_records_count": len(src_a),
            "invalid_records_count": 0,
            "warnings_count": 0,
            "validation_issues": [],
            "sample_records": src_a[:3]
        }
    }

    app_state["sources"]["SRC-MUN"] = {
        "source_id": "SRC-MUN",
        "source_name": "Municipal Property Records",
        "file_format": "JSON",
        "records": src_b,
        "quality_report": {
            "source_id": "SRC-MUN",
            "source_name": "Municipal Property Records",
            "total_records": len(src_b),
            "valid_records_count": len(src_b),
            "invalid_records_count": 0,
            "warnings_count": 1,
            "validation_issues": [
                {
                    "row_index": 2,
                    "source_record_id": "MUN-PROP-882",
                    "is_valid": True,
                    "warnings": ["Potential land-use category variance (RESIDENTIAL vs agricultural)"],
                    "raw_record": src_b[1]
                }
            ],
            "sample_records": src_b[:3]
        }
    }

    app_state["sources"]["SRC-GIS"] = {
        "source_id": "SRC-GIS",
        "source_name": "GIS Survey Records",
        "file_format": "GEOJSON",
        "records": src_c,
        "quality_report": {
            "source_id": "SRC-GIS",
            "source_name": "GIS Survey Records",
            "total_records": len(src_c),
            "valid_records_count": len(src_c),
            "invalid_records_count": 0,
            "warnings_count": 1,
            "validation_issues": [
                {"row_index": 1, "source_record_id": "GIS-CAD-501", "is_valid": True, "warnings": ["Missing owner name"], "raw_record": src_c[0]}
            ],
            "sample_records": src_c[:3]
        }
    }

    # Automatically run initial matching across the default benchmark sources
    records_by_source = {
        s["source_name"]: s["records"] for s in app_state["sources"].values()
    }
    match_res = app_state["matching_service"].run_matching(records_by_source)
    app_state["candidate_pairs"] = match_res["candidate_pairs"]
    app_state["conflicts"] = match_res["conflicts"]
    app_state["unified_entities"] = match_res["unified_entities"]
    app_state["latest_matching_run_meta"] = {
        "execution_time_seconds": match_res["execution_time_seconds"],
        "total_candidate_pairs": match_res["total_candidate_pairs"],
        "high_confidence_matches": match_res["high_confidence_matches"],
        "medium_confidence_reviews": match_res["medium_confidence_reviews"],
        "low_confidence_rejected": match_res["low_confidence_rejected"],
        "total_conflicts_detected": match_res["total_conflicts_detected"],
        "unified_entities_count": match_res["unified_entities_count"]
    }

init_sample_data()

@router.get("/health")
def get_health():
    return {
        "status": "healthy",
        "service": "Multi-Source Land Record Matching & Conflict Resolution API",
        "active_sources": len(app_state["sources"]),
        "candidate_pairs_count": len(app_state["candidate_pairs"]),
        "conflicts_count": len(app_state["conflicts"])
    }

@router.post("/sources/load-sample-benchmarks")
def reset_to_sample_benchmarks():
    """Resets or loads the official benchmark datasets."""
    init_sample_data()
    return {
        "status": "success",
        "message": "Loaded 3 realistic land record sources (Revenue, Municipal, GIS Cadastre) and executed baseline matching.",
        "sources": list(app_state["sources"].keys()),
        "meta": app_state["latest_matching_run_meta"]
    }

@router.get("/sources")
def list_sources():
    sources_summary = []
    for s_id, s in app_state["sources"].items():
        q = s.get("quality_report", {})
        sources_summary.append({
            "source_id": s_id,
            "source_name": s["source_name"],
            "file_format": s.get("file_format", "UNKNOWN"),
            "total_records": len(s["records"]),
            "valid_records": q.get("valid_records_count", len(s["records"])),
            "invalid_records": q.get("invalid_records_count", 0),
            "warnings_count": q.get("warnings_count", 0)
        })
    return {"sources": sources_summary}

@router.get("/sources/{source_id}/records")
def get_source_records(source_id: str, limit: int = 100):
    source = app_state["sources"].get(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return {
        "source_id": source_id,
        "source_name": source["source_name"],
        "records": source["records"][:limit]
    }

@router.get("/sources/{source_id}/quality")
def get_source_quality_report(source_id: str):
    source = app_state["sources"].get(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return source.get("quality_report")

@router.post("/sources/upload")
async def upload_source_file(
    file: UploadFile = File(...),
    source_name: str = Form(...),
    column_mapping: Optional[str] = Form(None)
):
    """
    Uploads a file (CSV, Excel, GeoJSON, Shapefile ZIP) and applies column mapping wizard.
    """
    file_bytes = await file.read()
    source_id = f"SRC-{uuid.uuid4().hex[:8].upper()}"

    try:
        raw_records, detected_format = IngestionService.parse_file(file.filename, file_bytes)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"File parsing error: {str(e)}")

    mapping_spec = {}
    if column_mapping:
        try:
            mapping_spec = json.loads(column_mapping)
        except Exception:
            pass

    # Apply default mappings if fields not specified
    default_fields = {
        "source_record_id": "id",
        "parcel_or_survey_number": "survey_no",
        "owner_name": "owner",
        "property_address": "address",
        "land_area": "area",
        "area_unit": "area_unit",
        "latitude": "latitude",
        "longitude": "longitude",
        "parcel_geometry": "geometry",
        "land_use_category": "land_use",
        "record_date": "date",
        "village_or_locality": "village"
    }
    for k, v in default_fields.items():
        if k not in mapping_spec:
            mapping_spec[k] = v

    normalized_records, quality_report = IngestionService.map_and_normalize(
        raw_records=raw_records,
        mapping_spec=mapping_spec,
        source_id=source_id,
        source_name=source_name
    )

    app_state["sources"][source_id] = {
        "source_id": source_id,
        "source_name": source_name,
        "file_format": detected_format,
        "records": normalized_records,
        "quality_report": quality_report
    }

    return {
        "status": "success",
        "source_id": source_id,
        "source_name": source_name,
        "file_format": detected_format,
        "quality_report": quality_report
    }

@router.post("/matching/run")
def run_matching_pipeline(config: MatchingRunConfig):
    """
    Runs the multi-stage matching pipeline across configured sources.
    """
    records_by_source = {}
    if config.source_ids:
        for sid in config.source_ids:
            if sid in app_state["sources"]:
                s = app_state["sources"][sid]
                records_by_source[s["source_name"]] = s["records"]
    else:
        records_by_source = {
            s["source_name"]: s["records"] for s in app_state["sources"].values()
        }

    if len(records_by_source) < 2:
        raise HTTPException(status_code=400, detail="At least 2 sources required to run entity matching.")

    match_res = app_state["matching_service"].run_matching(
        records_by_source=records_by_source,
        high_threshold=config.high_threshold,
        medium_threshold=config.medium_threshold,
        enable_survey_blocking=config.enable_survey_blocking,
        enable_spatial_blocking=config.enable_spatial_blocking,
        enable_locality_area_blocking=config.enable_locality_area_blocking,
        area_tolerance_ratio=config.area_tolerance_ratio,
        custom_weights=config.weights
    )

    app_state["candidate_pairs"] = match_res["candidate_pairs"]
    app_state["conflicts"] = match_res["conflicts"]
    app_state["unified_entities"] = match_res["unified_entities"]
    app_state["latest_matching_run_meta"] = {
        "execution_time_seconds": match_res["execution_time_seconds"],
        "total_candidate_pairs": match_res["total_candidate_pairs"],
        "high_confidence_matches": match_res["high_confidence_matches"],
        "medium_confidence_reviews": match_res["medium_confidence_reviews"],
        "low_confidence_rejected": match_res["low_confidence_rejected"],
        "total_conflicts_detected": match_res["total_conflicts_detected"],
        "unified_entities_count": match_res["unified_entities_count"]
    }

    return {
        "status": "success",
        "metadata": app_state["latest_matching_run_meta"],
        "candidate_pairs_count": len(match_res["candidate_pairs"]),
        "conflicts_count": len(match_res["conflicts"]),
        "unified_entities_count": len(match_res["unified_entities"])
    }

@router.get("/matching/results")
def get_matching_results(
    decision: Optional[str] = Query(None),
    min_confidence: Optional[float] = Query(None),
    limit: int = 200
):
    pairs = app_state["candidate_pairs"]
    if decision:
        pairs = [p for p in pairs if p.get("match_decision") == decision.upper()]
    if min_confidence is not None:
        pairs = [p for p in pairs if p.get("final_confidence", 0) >= min_confidence]
    return {
        "total_count": len(pairs),
        "candidate_pairs": pairs[:limit],
        "metadata": app_state["latest_matching_run_meta"]
    }

@router.get("/matching/{pair_id}")
def get_candidate_pair_detail(pair_id: str):
    for p in app_state["candidate_pairs"]:
        if p.get("pair_id") == pair_id:
            # Attach any conflicts associated with this pair
            pair_conflicts = [c for c in app_state["conflicts"] if c.get("pair_id") == pair_id]
            return {"candidate_pair": p, "conflicts": pair_conflicts}
    raise HTTPException(status_code=404, detail="Candidate pair not found")

@router.post("/matching/{pair_id}/resolve")
def resolve_candidate_pair(pair_id: str, req: ConflictResolutionRequest):
    for p in app_state["candidate_pairs"]:
        if p.get("pair_id") == pair_id:
            res = app_state["resolution_service"].resolve_pair(
                pair=p,
                action=req.action,
                reviewer_id=req.reviewer_id,
                reason=req.reason,
                reviewer_notes=req.reviewer_notes
            )
            return res
    raise HTTPException(status_code=404, detail="Candidate pair not found")

@router.get("/conflicts")
def get_conflicts(
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = 200
):
    confs = app_state["conflicts"]
    if severity:
        confs = [c for c in confs if c.get("severity") == severity.upper()]
    if status:
        confs = [c for c in confs if c.get("resolution_status") == status.upper()]
    return {
        "total_conflicts": len(confs),
        "conflicts": confs[:limit]
    }

@router.get("/conflicts/{conflict_id}")
def get_conflict_detail(conflict_id: str):
    for c in app_state["conflicts"]:
        if c.get("conflict_id") == conflict_id:
            return {"conflict": c}
    raise HTTPException(status_code=404, detail="Conflict not found")

@router.post("/conflicts/{conflict_id}/resolve")
def resolve_conflict_item(conflict_id: str, req: ConflictResolutionRequest):
    for c in app_state["conflicts"]:
        if c.get("conflict_id") == conflict_id:
            res = app_state["resolution_service"].resolve_conflict(
                conflict=c,
                action=req.action,
                reviewer_id=req.reviewer_id,
                reason=req.reason,
                selected_value=req.selected_value,
                reviewer_notes=req.reviewer_notes
            )
            return res
    raise HTTPException(status_code=404, detail="Conflict not found")

@router.get("/evaluation/metrics")
def get_evaluation_metrics():
    """
    Computes Scikit-Learn validation metrics against the ground-truth benchmark pairs.
    """
    pairs = app_state["candidate_pairs"]
    gt_map = app_state["ground_truth_lookup"]

    y_true = []
    y_pred = []
    y_scores = []

    for p in pairs:
        ida = str(p.get("source_record_id_a"))
        idb = str(p.get("source_record_id_b"))
        is_gt_match = gt_map.get((ida, idb)) or gt_map.get((idb, ida))
        if is_gt_match is not None:
            y_true.append(1 if is_gt_match else 0)
            conf = p.get("final_confidence", 0.0)
            y_scores.append(conf)
            y_pred.append(1 if conf >= 0.70 else 0)

    metrics = compute_evaluation_metrics(y_true, y_pred, y_scores)
    return {
        "evaluation_metrics": metrics,
        "labeled_pairs_evaluated": len(y_true),
        "total_ground_truth_in_system": len(gt_map) // 2
    }

@router.get("/evaluation/threshold-analysis")
def get_threshold_analysis():
    """
    Produces multi-threshold sensitivity analysis (0.50, 0.60, 0.70, 0.80, 0.90)
    with measured precision, recall, false positives, review counts, and reproducibility metadata.
    """
    analyzer = ThresholdSensitivityAnalyzer()
    res = analyzer.run_sensitivity_analysis(
        evaluated_pairs=app_state["candidate_pairs"],
        ground_truth_lookup=app_state["ground_truth_lookup"],
        detected_conflicts_count=len(app_state["conflicts"])
    )
    return res

@router.get("/rules")
def get_rules():
    return {
        "rules": app_state["matching_service"].rule_engine.rules,
        "source_priority": app_state["matching_service"].conflict_detector.source_priority
    }

@router.get("/audit")
def get_audit_trail(target_id: Optional[str] = Query(None)):
    entries = app_state["resolution_service"].get_audit_trail(target_id)
    return {"audit_entries": entries, "total_records": len(entries)}

@router.get("/exports/{export_type}")
def export_data(export_type: str, format: str = Query("json")):
    """
    Exports 'matching', 'conflicts', 'audit', or 'evaluation' in CSV or JSON.
    """
    format_lower = format.lower()
    if export_type == "matching":
        if format_lower == "csv":
            content = ExportService.export_candidate_pairs_csv(app_state["candidate_pairs"])
            return Response(content=content, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=matching_results.csv"})
        return app_state["candidate_pairs"]

    elif export_type == "conflicts":
        if format_lower == "csv":
            content = ExportService.export_conflicts_csv(app_state["conflicts"])
            return Response(content=content, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=detected_conflicts.csv"})
        return app_state["conflicts"]

    elif export_type == "audit":
        audit_entries = app_state["resolution_service"].get_audit_trail()
        if format_lower == "csv":
            content = ExportService.export_audit_log_csv(audit_entries)
            return Response(content=content, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=audit_trail.csv"})
        return {"audit_trail": audit_entries}

    elif export_type == "evaluation":
        analyzer = ThresholdSensitivityAnalyzer()
        eval_res = analyzer.run_sensitivity_analysis(
            evaluated_pairs=app_state["candidate_pairs"],
            ground_truth_lookup=app_state["ground_truth_lookup"],
            detected_conflicts_count=len(app_state["conflicts"])
        )
        return eval_res

    else:
        raise HTTPException(status_code=400, detail=f"Unknown export type: {export_type}")

