"""
Data Export Service (Section 12 & 14)
Exports matching results, conflicts, audit logs, and evaluation reports to CSV or JSON formats.
"""

import io
import json
import csv
from typing import List, Dict, Any

class ExportService:
    @staticmethod
    def export_to_json(data: Any) -> str:
        """Serializes data structure to formatted JSON."""
        return json.dumps(data, indent=2, default=str)

    @staticmethod
    def export_candidate_pairs_csv(pairs: List[Dict[str, Any]]) -> str:
        """Exports matching candidate pairs to CSV format."""
        output = io.StringIO()
        fieldnames = [
            "pair_id",
            "source_record_id_a",
            "source_a_name",
            "source_record_id_b",
            "source_b_name",
            "final_confidence",
            "match_decision",
            "score_type",
            "reviewer_decision",
            "reviewer_id",
            "survey_a",
            "survey_b",
            "area_a_sqm",
            "area_b_sqm",
            "explanation_summary"
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for p in pairs:
            raw = p.get("raw_metrics", {})
            expl = p.get("explanation", {})
            writer.writerow({
                "pair_id": p.get("pair_id"),
                "source_record_id_a": p.get("source_record_id_a"),
                "source_a_name": p.get("source_a_name"),
                "source_record_id_b": p.get("source_record_id_b"),
                "source_b_name": p.get("source_b_name"),
                "final_confidence": p.get("final_confidence"),
                "match_decision": p.get("match_decision"),
                "score_type": p.get("score_type"),
                "reviewer_decision": p.get("reviewer_decision"),
                "reviewer_id": p.get("reviewer_id"),
                "survey_a": raw.get("survey_a"),
                "survey_b": raw.get("survey_b"),
                "area_a_sqm": raw.get("area_a_sqm"),
                "area_b_sqm": raw.get("area_b_sqm"),
                "explanation_summary": expl.get("summary")
            })

        return output.getvalue()

    @staticmethod
    def export_conflicts_csv(conflicts: List[Dict[str, Any]]) -> str:
        """Exports detected conflicts to CSV format."""
        output = io.StringIO()
        fieldnames = [
            "conflict_id",
            "pair_id",
            "category",
            "field",
            "source_a",
            "value_a",
            "source_b",
            "value_b",
            "severity",
            "discrepancy_measure",
            "suggested_value",
            "resolution_status",
            "resolved_value",
            "reviewer_notes"
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for c in conflicts:
            writer.writerow({
                "conflict_id": c.get("conflict_id"),
                "pair_id": c.get("pair_id"),
                "category": c.get("category"),
                "field": c.get("field"),
                "source_a": c.get("source_a"),
                "value_a": c.get("value_a"),
                "source_b": c.get("source_b"),
                "value_b": c.get("value_b"),
                "severity": c.get("severity"),
                "discrepancy_measure": c.get("discrepancy_measure"),
                "suggested_value": c.get("suggested_value"),
                "resolution_status": c.get("resolution_status"),
                "resolved_value": c.get("resolved_value"),
                "reviewer_notes": c.get("reviewer_notes")
            })

        return output.getvalue()

    @staticmethod
    def export_audit_log_csv(audit_entries: List[Dict[str, Any]]) -> str:
        """Exports audit entries to CSV format."""
        output = io.StringIO()
        fieldnames = [
            "audit_id",
            "timestamp",
            "target_type",
            "target_id",
            "pair_id",
            "reviewer_id",
            "action",
            "previous_state",
            "new_state",
            "reason",
            "selected_value",
            "reviewer_notes"
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for a in audit_entries:
            writer.writerow({
                "audit_id": a.get("audit_id"),
                "timestamp": a.get("timestamp"),
                "target_type": a.get("target_type"),
                "target_id": a.get("target_id"),
                "pair_id": a.get("pair_id"),
                "reviewer_id": a.get("reviewer_id"),
                "action": a.get("action"),
                "previous_state": a.get("previous_state"),
                "new_state": a.get("new_state"),
                "reason": a.get("reason"),
                "selected_value": a.get("selected_value"),
                "reviewer_notes": a.get("reviewer_notes")
            })

        return output.getvalue()

