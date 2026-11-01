"""
GIS Geometry Validation and CRS Handling
Validates GeoJSON geometries, checks ring orientation, detects self-intersections,
and handles spatial integrity using Shapely.
"""

from typing import Dict, Any, Optional, Tuple, List
import math
from shapely.geometry import shape, mapping, Polygon, MultiPolygon, Point
from shapely.validation import make_valid, explain_validity

def validate_and_repair_geometry(geom_dict: Optional[Dict[str, Any]]) -> Tuple[Optional[Dict[str, Any]], bool, List[str]]:
    """
    Validates a GeoJSON geometry dictionary.
    Attempts to repair minor topological defects (self-intersections, unclosed rings).
    Returns (repaired_geom_dict, is_valid, list_of_warnings)
    """
    warnings = []
    if not geom_dict:
        return None, True, warnings
        
    try:
        geom_type = geom_dict.get("type")
        if not geom_type:
            warnings.append("Geometry missing 'type' attribute")
            return None, False, warnings
            
        coords = geom_dict.get("coordinates")
        if coords is None or len(coords) == 0:
            warnings.append(f"Geometry type '{geom_type}' has empty coordinates")
            return None, False, warnings
            
        s_geom = shape(geom_dict)
        if s_geom.is_empty:
            warnings.append("Geometry is topologically empty")
            return None, False, warnings
            
        if not s_geom.is_valid:
            reason = explain_validity(s_geom)
            warnings.append(f"Invalid geometry: {reason}. Attempting automated repair.")
            repaired = make_valid(s_geom)
            if repaired.is_valid and not repaired.is_empty:
                return mapping(repaired), True, warnings
            else:
                warnings.append("Automated geometry repair failed")
                return None, False, warnings
                
        # Check area if polygon
        if isinstance(s_geom, (Polygon, MultiPolygon)):
            if s_geom.area <= 0:
                warnings.append("Polygon has zero area")
                return None, False, warnings
                
        return mapping(s_geom), True, warnings
        
    except Exception as e:
        warnings.append(f"Geometry validation exception: {str(e)}")
        return None, False, warnings

def extract_centroid(geom_dict: Optional[Dict[str, Any]], lat: Optional[float] = None, lon: Optional[float] = None) -> Optional[Tuple[float, float]]:
    """
    Returns (latitude, longitude) of centroid.
    If geometry is present, extracts its centroid.
    Otherwise falls back to lat/lon if available.
    """
    if geom_dict:
        try:
            s_geom = shape(geom_dict)
            if not s_geom.is_empty:
                centroid = s_geom.centroid
                # GeoJSON coordinates are [longitude, latitude]
                return (round(centroid.y, 7), round(centroid.x, 7))
        except Exception:
            pass
            
    if lat is not None and lon is not None:
        return (lat, lon)
    return None

