"""
Human-in-the-Loop Conflict Resolution & Audit Service (Section 9)
Provides reviewer actions (confirm, reject, select preferred values, notes)
and an auditable decision ledger. Source records are preserved intact.
"""

from typing import List, Dict, Any, Optional
import datetime
import uuid

class ConflictResolutionService:
    def __init__(self):
        # In-memory storage with optional persistence
        self.audit_log: List[Dict[str, Any]] = []

    def resolve_conflict(
        self,
        conflict: Dict[str, Any],
        action: str, # CONFIRM_MATCH, REJECT_MATCH, MARK_UNRESOLVED, SELECT_PREFERRED_VALUE
        reviewer_id: str,
        reason: str,
        selected_value: Optional[str] = None,
        reviewer_notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Applies a resolution action to a conflict and writes to the audit trail.
        """
        prev_state = conflict.get("resolution_status", "PENDING")
        new_state = action.upper()

        conflict["resolution_status"] = new_state
        if selected_value is not None:
            conflict["resolved_value"] = selected_value
        if reviewer_notes:
            conflict["reviewer_notes"] = reviewer_notes

        audit_entry = {
            "audit_id": f"AUD-{uuid.uuid4().hex[:10].upper()}",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "target_type": "CONFLICT",
            "target_id": conflict.get("conflict_id"),
            "pair_id": conflict.get("pair_id"),
            "reviewer_id": reviewer_id,
            "action": action,
            "previous_state": prev_state,
            "new_state": new_state,
            "reason": reason,
            "selected_value": selected_value,
            "reviewer_notes": reviewer_notes
        }
        self.audit_log.append(audit_entry)
        return {
            "status": "success",
            "conflict": conflict,
            "audit_entry": audit_entry
        }

    def resolve_pair(
        self,
        pair: Dict[str, Any],
        action: str, # CONFIRM_MATCH, REJECT_MATCH, MARK_UNRESOLVED
        reviewer_id: str,
        reason: str,
        reviewer_notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Applies a reviewer decision directly to a candidate match pair.
        """
        prev_decision = pair.get("reviewer_decision", pair.get("match_decision"))
        new_decision = action.upper()

        pair["reviewer_decision"] = new_decision
        pair["reviewer_id"] = reviewer_id
        pair["resolution_timestamp"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        if reviewer_notes:
            pair["reviewer_notes"] = reviewer_notes

        audit_entry = {
            "audit_id": f"AUD-{uuid.uuid4().hex[:10].upper()}",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "target_type": "PAIR",
            "target_id": pair.get("pair_id"),
            "reviewer_id": reviewer_id,
            "action": action,
            "previous_state": prev_decision,
            "new_state": new_decision,
            "reason": reason,
            "reviewer_notes": reviewer_notes
        }
        self.audit_log.append(audit_entry)
        return {
            "status": "success",
            "pair": pair,
            "audit_entry": audit_entry
        }

    def get_audit_trail(self, target_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns filtered or full audit history."""
        if target_id:
            return [e for e in self.audit_log if e.get("target_id") == target_id or e.get("pair_id") == target_id]
        return list(self.audit_log)

