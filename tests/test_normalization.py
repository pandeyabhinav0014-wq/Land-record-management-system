"""
Unit and Acceptance Tests for Data Quality, Normalization, and Validation (Section 5)
"""

import pytest
from matching.normalization import (
    normalize_text,
    normalize_survey_number,
    normalize_area,
    normalize_coordinates,
    validate_record
)

def test_text_normalization():
    # Abbreviation expansion, case folding, unicode NFKC
    raw = "  12, mg rd, vill rampur, dist shamli. "
    norm = normalize_text(raw)
    assert "ROAD" in norm
    assert "VILLAGE" in norm
    assert "DISTRICT" in norm
    assert not norm.endswith(".")

def test_survey_number_normalization():
    # Leading zeros preserved, spaces stripped around slashes
    assert normalize_survey_number(" 0014 / 2 - A ") == "0014/2-A"
    assert normalize_survey_number("S.No. 45/1") == "45/1"
    assert normalize_survey_number("Khasra No. 108/3") == "108/3"

def test_area_normalization():
    # Acres to square meters: 1 acre = 4046.8564 sqm
    sqm, unit, warn = normalize_area(1.0, "acres")
    assert unit == "sq_meters"
    assert abs(sqm - 4046.8564) < 0.1
    assert len(warn) == 0

    # Hectares to square meters: 2 ha = 20000 sqm
    sqm_ha, _, _ = normalize_area(2.0, "hectares")
    assert sqm_ha == 20000.0

    # Negative area detection (deliberately injected error)
    _, _, neg_warn = normalize_area(-150.0, "sq_meters")
    assert any("Impossible negative area" in w for w in neg_warn)

def test_coordinates_normalization_and_swap():
    # Normal coordinates
    lat, lon, warn = normalize_coordinates(28.6139, 77.2090)
    assert lat == 28.6139
    assert lon == 77.2090
    assert len(warn) == 0

    # Swapped coordinates (Lon > 90 placed in Lat)
    lat_s, lon_s, warn_s = normalize_coordinates(77.2090, 28.6139)
    assert lat_s == 28.6139
    assert lon_s == 77.2090
    assert any("Swapped" in w for w in warn_s)

def test_validation_detects_deliberate_errors():
    seen_ids = set()
    # Missing ID
    is_v1, w1 = validate_record({"source_record_id": None}, seen_ids)
    assert not is_v1
    assert any("Missing mandatory source record ID" in w for w in w1)

    # Valid record
    valid_rec = {"source_record_id": "REC-01", "parcel_or_survey_number": "14/1", "land_area": 500.0}
    is_v2, _ = validate_record(valid_rec, seen_ids)
    assert is_v2

    # Duplicate ID
    is_v3, w3 = validate_record({"source_record_id": "REC-01", "parcel_or_survey_number": "14/2"}, seen_ids)
    assert not is_v3
    assert any("Duplicate" in w for w in w3)

