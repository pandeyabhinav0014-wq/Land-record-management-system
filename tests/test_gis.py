"""
Tests for GIS, Geometry Validation, and Spatial Matching
"""

from gis.geometry_validation import validate_and_repair_geometry, extract_centroid
from gis.spatial_matching import haversine_distance_meters, calculate_spatial_similarity

def test_haversine_distance():
    # Distance between New Delhi (28.6139, 77.2090) and nearby point
    d = haversine_distance_meters(28.6139, 77.2090, 28.6140, 77.2091)
    assert 5.0 < d < 25.0 # Approximately 15 meters

def test_polygon_iou_overlap():
    # Two identical polygons should have IoU = 1.0
    poly1 = {
        "type": "Polygon",
        "coordinates": [[[0, 0], [2, 0], [2, 2], [0, 2], [0, 0]]]
    }
    poly2 = {
        "type": "Polygon",
        "coordinates": [[[0, 0], [2, 0], [2, 2], [0, 2], [0, 0]]]
    }
    res = calculate_spatial_similarity(poly1, poly2)
    assert res["polygon_iou"] == 1.0
    assert res["intersects"] is True

def test_partial_polygon_overlap():
    # Offset by 1 unit: intersection area 2, union area 6 -> IoU 0.3333
    poly1 = {
        "type": "Polygon",
        "coordinates": [[[0, 0], [2, 0], [2, 2], [0, 2], [0, 0]]]
    }
    poly2 = {
        "type": "Polygon",
        "coordinates": [[[1, 0], [3, 0], [3, 2], [1, 2], [1, 0]]]
    }
    res = calculate_spatial_similarity(poly1, poly2)
    assert 0.30 <= res["polygon_iou"] <= 0.35
    assert res["containment_ratio"] == 0.5

def test_invalid_geometry_repair():
    # Self-intersecting bowtie polygon
    bowtie = {
        "type": "Polygon",
        "coordinates": [[[0, 0], [2, 2], [2, 0], [0, 2], [0, 0]]]
    }
    repaired, is_valid, warnings = validate_and_repair_geometry(bowtie)
    assert is_valid is True
    assert len(warnings) > 0

