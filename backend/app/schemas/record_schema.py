"""
Pydantic Schemas for Multi-Source Land Record System
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class ColumnMappingRequest(BaseModel):
    source_name: str
    source_record_id: str
    parcel_or_survey_number: str
    owner_name: Optional[str] = None
    property_address: Optional[str] = None
    land_area: Optional[str] = None
    area_unit: Optional[str] = "sq_meters"
    latitude: Optional[str] = None
    longitude: Optional[str] = None
    parcel_geometry: Optional[str] = None
    land_use_category: Optional[str] = None
    record_date: Optional[str] = None
    village_or_locality: Optional[str] = None

class DataQualityReport(BaseModel):
    source_id: str
    source_name: str
    total_records: int
    valid_records_count: int
    invalid_records_count: int
    warnings_count: int
    validation_issues: List[Dict[str, Any]]
    sample_records: List[Dict[str, Any]]

class MatchingRunConfig(BaseModel):
    source_ids: Optional[List[str]] = None
    high_threshold: float = 0.80
    medium_threshold: float = 0.55
    enable_survey_blocking: bool = True
    enable_spatial_blocking: bool = True
    enable_locality_area_blocking: bool = True
    area_tolerance_ratio: float = 0.30
    weights: Optional[Dict[str, float]] = None

class ConflictResolutionRequest(BaseModel):
    action: str # CONFIRM_MATCH, REJECT_MATCH, MARK_UNRESOLVED, SELECT_PREFERRED_VALUE
    reviewer_id: str = "Admin_Reviewer_1"
    reason: str
    selected_value: Optional[str] = None
    reviewer_notes: Optional[str] = None

class RuleDefinition(BaseModel):
    rule_id: str
    description: str
    severity: str
    evidence_fields: List[str]
    action: str
    confidence_delta: float
    conditions: Dict[str, Any]

