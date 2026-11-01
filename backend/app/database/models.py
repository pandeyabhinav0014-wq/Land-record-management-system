"""
SQLAlchemy ORM Models for Land Record Matching System
"""

import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime
from backend.app.database.db import Base

class SourceDatasetModel(Base):
    __tablename__ = "source_datasets"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(String(64), unique=True, index=True)
    source_name = Column(String(128), index=True)
    file_format = Column(String(32))
    record_count = Column(Integer, default=0)
    valid_count = Column(Integer, default=0)
    invalid_count = Column(Integer, default=0)
    quality_report_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class LandRecordModel(Base):
    __tablename__ = "land_records"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(String(64), index=True)
    source_name = Column(String(128), index=True)
    source_record_id = Column(String(128), index=True)
    parcel_or_survey_number = Column(String(128), index=True)
    owner_name = Column(String(256), nullable=True, index=True)
    property_address = Column(String(512), nullable=True)
    land_area = Column(Float, nullable=True)
    area_unit = Column(String(32), default="sq_meters")
    original_area = Column(Float, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    parcel_geometry_json = Column(Text, nullable=True)
    land_use_category = Column(String(64), nullable=True)
    record_date = Column(String(64), nullable=True)
    village_or_locality = Column(String(128), nullable=True, index=True)
    is_valid = Column(Boolean, default=True)
    quality_warnings_json = Column(Text, nullable=True)
    raw_attributes_json = Column(Text, nullable=True)

class CandidateMatchPairModel(Base):
    __tablename__ = "candidate_match_pairs"

    id = Column(Integer, primary_key=True, index=True)
    pair_id = Column(String(64), unique=True, index=True)
    source_record_id_a = Column(String(128), index=True)
    source_record_id_b = Column(String(128), index=True)
    source_a_name = Column(String(128))
    source_b_name = Column(String(128))
    final_confidence = Column(Float, index=True)
    preliminary_score = Column(Float)
    rule_adjustment = Column(Float)
    match_decision = Column(String(64), index=True) # HIGH_CONFIDENCE, MEDIUM_CONFIDENCE, LOW_CONFIDENCE
    score_type = Column(String(64), default="heuristic")
    feature_scores_json = Column(Text)
    raw_metrics_json = Column(Text)
    missing_features_json = Column(Text)
    triggered_rules_json = Column(Text)
    explanation_json = Column(Text)
    reviewer_decision = Column(String(64), nullable=True, index=True)
    reviewer_id = Column(String(128), nullable=True)
    reviewer_notes = Column(Text, nullable=True)
    resolution_timestamp = Column(String(64), nullable=True)

class DetectedConflictModel(Base):
    __tablename__ = "detected_conflicts"

    id = Column(Integer, primary_key=True, index=True)
    conflict_id = Column(String(64), unique=True, index=True)
    pair_id = Column(String(64), index=True)
    category = Column(String(64), index=True)
    field = Column(String(64))
    source_a = Column(String(128))
    value_a = Column(String(256), nullable=True)
    source_b = Column(String(128))
    value_b = Column(String(256), nullable=True)
    discrepancy_measure = Column(String(256))
    severity = Column(String(32), index=True)
    supporting_evidence = Column(Text)
    suggested_value = Column(String(256), nullable=True)
    suggested_value_rationale = Column(Text, nullable=True)
    resolution_status = Column(String(64), default="PENDING", index=True)
    resolved_value = Column(String(256), nullable=True)
    reviewer_notes = Column(Text, nullable=True)

class UnifiedParcelEntityModel(Base):
    __tablename__ = "unified_parcel_entities"

    id = Column(Integer, primary_key=True, index=True)
    entity_id = Column(String(64), unique=True, index=True)
    member_record_ids_json = Column(Text)
    sources_json = Column(Text)
    member_count = Column(Integer, default=0)
    primary_survey_number = Column(String(128), nullable=True)
    primary_locality = Column(String(128), nullable=True)
    has_transitive_conflict = Column(Boolean, default=False)
    transitive_conflict_notes_json = Column(Text, nullable=True)

class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    audit_id = Column(String(64), unique=True, index=True)
    timestamp = Column(String(64), index=True)
    target_type = Column(String(32)) # PAIR or CONFLICT
    target_id = Column(String(64), index=True)
    pair_id = Column(String(64), nullable=True, index=True)
    reviewer_id = Column(String(128))
    action = Column(String(64))
    previous_state = Column(String(64), nullable=True)
    new_state = Column(String(64))
    reason = Column(Text)
    selected_value = Column(String(256), nullable=True)
    reviewer_notes = Column(Text, nullable=True)

