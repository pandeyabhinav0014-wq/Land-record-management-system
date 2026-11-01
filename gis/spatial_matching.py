"""
Spatial Matching and GIS Distance/Overlap Computations
Calculates Haversine distance, polygon intersection over union (IoU),
containment ratio, and spatial proximity scores.
"""

import math
from typing import Dict, Any, Optional, Tuple
from shapely.geometry import shape, Polygon, MultiPolygon

def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Computes great-circle distance between two points in meters using Haversine formula.
    """
    R = 6371008.8  # Earth mean radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1.0 - a)))
    return R * c

def calculate_spatial_similarity(
    geom1: Optional[Dict[str, Any]],
    geom2: Optional[Dict[str, Any]],
    lat1: Optional[float] = None,
    lon1: Optional[float] = None,
    lat2: Optional[float] = None,
    lon2: Optional[float] = None,
    decay_distance_meters: float = 150.0
) -> Dict[str, Any]:
    """
    Computes spatial similarity metrics:
    - geographic_distance_meters: distance between centroids / coords
    - polygon_iou: intersection over union if both geometries are polygons
    - containment_ratio: intersection / min(area1, area2)
    - spatial_proximity_score: continuous score in [0.0, 1.0]
    - geometries_available: whether full polygons or point coordinates were used
    """
    res = {
        "geographic_distance_meters": None,
        "polygon_iou": None,
        "containment_ratio": None,
        "spatial_proximity_score": 0.0,
        "geometries_available": False,
        "points_available": False,
        "intersects": False
    }

    s_geom1 = None
    s_geom2 = None

    if geom1 and isinstance(geom1, dict):
        try:
            s_geom1 = shape(geom1)
            if s_geom1.is_empty or not s_geom1.is_valid:
                s_geom1 = None
        except Exception:
            s_geom1 = None

    if geom2 and isinstance(geom2, dict):
        try:
            s_geom2 = shape(geom2)
            if s_geom2.is_empty or not s_geom2.is_valid:
                s_geom2 = None
        except Exception:
            s_geom2 = None

    # Polygon overlap calculation
    if s_geom1 and s_geom2 and isinstance(s_geom1, (Polygon, MultiPolygon)) and isinstance(s_geom2, (Polygon, MultiPolygon)):
        res["geometries_available"] = True
        try:
            # Check intersection
            if s_geom1.intersects(s_geom2):
                res["intersects"] = True
                intersection = s_geom1.intersection(s_geom2)
                union = s_geom1.union(s_geom2)
                inter_area = intersection.area
                union_area = union.area
                
                if union_area > 0:
                    res["polygon_iou"] = round(inter_area / union_area, 4)
                min_area = min(s_geom1.area, s_geom2.area)
                if min_area > 0:
                    res["containment_ratio"] = round(inter_area / min_area, 4)
            else:
                res["polygon_iou"] = 0.0
                res["containment_ratio"] = 0.0
        except Exception:
            res["polygon_iou"] = 0.0

    # Centroid coordinate extraction for distance
    c_lat1, c_lon1 = None, None
    c_lat2, c_lon2 = None, None

    if s_geom1:
        c_lat1, c_lon1 = s_geom1.centroid.y, s_geom1.centroid.x
    elif lat1 is not None and lon1 is not None:
        c_lat1, c_lon1 = lat1, lon1

    if s_geom2:
        c_lat2, c_lon2 = s_geom2.centroid.y, s_geom2.centroid.x
    elif lat2 is not None and lon2 is not None:
        c_lat2, c_lon2 = lat2, lon2

    if c_lat1 is not None and c_lon1 is not None and c_lat2 is not None and c_lon2 is not None:
        res["points_available"] = True
        dist = haversine_distance_meters(c_lat1, c_lon1, c_lat2, c_lon2)
        res["geographic_distance_meters"] = round(dist, 2)
        
        # Continuous proximity score (1.0 at 0m, decaying to ~0.37 at decay_distance_meters)
        prox_score = math.exp(-dist / max(10.0, decay_distance_meters))
        res["spatial_proximity_score"] = round(prox_score, 4)
    elif res["polygon_iou"] is not None:
        # If geometries overlap, infer high proximity
        res["spatial_proximity_score"] = round(res["polygon_iou"], 4)

    return res

