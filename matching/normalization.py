"""
Data Quality and Normalization Pipeline for Land Record Matching
Handles Unicode, whitespace, abbreviations, survey numbers, area conversions,
CRS/coordinate normalization, and validation checks.
"""

import re
import unicodedata
from typing import Dict, Any, List, Optional, Tuple

# Conversion factors to canonical square meters (m²)
AREA_CONVERSIONS_TO_SQ_METERS = {
    "sq_meters": 1.0,
    "sq_meter": 1.0,
    "sqm": 1.0,
    "m2": 1.0,
    "square_meters": 1.0,
    "sq_yards": 0.83612736,
    "sq_yard": 0.83612736,
    "sqyd": 0.83612736,
    "sq_feet": 0.09290304,
    "sq_foot": 0.09290304,
    "sqft": 0.09290304,
    "acres": 4046.8564224,
    "acre": 4046.8564224,
    "ac": 4046.8564224,
    "hectares": 10000.0,
    "hectare": 10000.0,
    "ha": 10000.0,
    "bigha": 2529.285, # Standard Indian bigha (varies by state, standardized baseline)
    "guntha": 101.1714, # Standard 1/40 acre
    "cents": 40.4686,
    "cent": 40.4686
}

ABBREVIATIONS_MAP = {
    r"\bRD\b": "ROAD",
    r"\bST\b": "STREET",
    r"\bAVE\b": "AVENUE",
    r"\bVILL\b": "VILLAGE",
    r"\bVIL\b": "VILLAGE",
    r"\bDIST\b": "DISTRICT",
    r"\bTEH\b": "TEHSIL",
    r"\bTAL\b": "TALUK",
    r"\bSEC\b": "SECTOR",
    r"\bNO\b": "NUMBER",
    r"\bSY\b": "SURVEY",
    r"\bSRV\b": "SURVEY",
    r"\bPLT\b": "PLOT",
    r"\bKHA\b": "KHASRA",
    r"\bKH\b": "KHASRA",
    r"\bAPPT\b": "APARTMENT",
    r"\bBLDG\b": "BUILDING",
    r"\bFLR\b": "FLOOR",
    r"\bHWY\b": "HIGHWAY",
    r"\bN\b": "NORTH",
    r"\bS\b": "SOUTH",
    r"\bE\b": "EAST",
    r"\bW\b": "WEST",
}

def normalize_text(text: Optional[str]) -> Optional[str]:
    """
    Remove unnecessary whitespace, normalize Unicode (NFKC),
    expand standard abbreviations, and uppercase.
    Preserves original string if None.
    """
    if text is None:
        return None
    s = str(text).strip()
    if not s or s.lower() in ("nan", "none", "null", "n/a", "na", "-"):
        return None
    
    # Unicode NFKC normalization
    s = unicodedata.normalize("NFKC", s)
    
    # Remove excessive whitespace
    s = re.sub(r"\s+", " ", s).strip()
    
    # Normalize common abbreviations
    s_upper = s.upper()
    for pattern, replacement in ABBREVIATIONS_MAP.items():
        s_upper = re.sub(pattern, replacement, s_upper)
    
    # Remove repeated punctuation
    s_upper = re.sub(r"[\.,\-]+$", "", s_upper).strip()
    return s_upper

def normalize_survey_number(survey_no: Optional[str]) -> Optional[str]:
    """
    Normalizes parcel and survey numbers without losing meaningful leading zeros.
    E.g. '0014 / 2 - A ' -> '0014/2-A', 'S.No. 45/1' -> '45/1'.
    """
    if survey_no is None:
        return None
    s = str(survey_no).strip()
    if not s or s.lower() in ("nan", "none", "null", "n/a", "na", "-"):
        return None
    
    s = unicodedata.normalize("NFKC", s).upper()
    # Remove prefixes like 'S.NO.', 'SY.NO.', 'KHASRA NO.', 'PARCEL NO.', 'PLOT NO.'
    s = re.sub(r"^(S(?:URVEY)?\.?\s*NO\.?|SY\.?\s*NO\.?|KHASRA\s*(?:NO\.?)?|PLOT\s*(?:NO\.?)?|PARCEL\s*(?:NO\.?)?)\s*", "", s, flags=re.IGNORECASE)
    # Remove spaces around delimiters /, -, _, .
    s = re.sub(r"\s*([/\-_:])\s*", r"\1", s)
    # Clean redundant whitespace
    s = re.sub(r"\s+", " ", s).strip()
    return s

def normalize_area(value: Any, unit: Optional[str] = "sq_meters") -> Tuple[Optional[float], Optional[str], List[str]]:
    """
    Standardize area to square meters.
    Returns (normalized_area_sqm, normalized_unit_name, warnings)
    """
    warnings = []
    if value is None or str(value).strip().lower() in ("nan", "none", "null", "n/a", "na", "", "-"):
        return None, None, warnings
    
    try:
        # Strip potential commas or text in numeric strings like '1,200.50 sqft'
        val_str = str(value).strip().replace(",", "")
        
        # Check if unit is embedded in the value string
        match = re.search(r"(-?[0-9]+(?:\.[0-9]+)?)\s*([a-zA-Z_]+)?", val_str)
        if match:
            num = float(match.group(1))
            embedded_unit = match.group(2)
            if embedded_unit:
                unit = embedded_unit.lower()
        else:
            num = float(val_str)
            
        if num < 0:
            warnings.append(f"Impossible negative area: {num}")
            return None, unit, warnings
        if num == 0:
            warnings.append("Area reported as 0")
            
        unit_key = (unit or "sq_meters").strip().lower().replace(" ", "_").replace(".", "")
        factor = AREA_CONVERSIONS_TO_SQ_METERS.get(unit_key)
        
        if factor is None:
            warnings.append(f"Unrecognized area unit '{unit}', assumed square meters")
            factor = 1.0
            canonical_unit = "sq_meters"
        else:
            canonical_unit = "sq_meters"
            
        normalized_sqm = round(num * factor, 4)
        return normalized_sqm, canonical_unit, warnings
        
    except (ValueError, TypeError) as e:
        warnings.append(f"Invalid area value '{value}': {str(e)}")
        return None, unit, warnings

def normalize_coordinates(lat: Any, lon: Any) -> Tuple[Optional[float], Optional[float], List[str]]:
    """
    Validates and normalizes latitude and longitude (EPSG:4326).
    Detects coordinate flips (e.g., lon in lat position).
    """
    warnings = []
    if lat is None or lon is None:
        return None, None, warnings
    
    try:
        lat_f = float(str(lat).strip().replace(",", ""))
        lon_f = float(str(lon).strip().replace(",", ""))
    except (ValueError, TypeError):
        warnings.append(f"Malformed coordinate values: lat={lat}, lon={lon}")
        return None, None, warnings
    
    # Coordinate flip detection: If lat is outside [-90, 90], or if lat > 60 while lon < 40 (regional swap)
    is_flipped = ((lat_f < -90 or lat_f > 90) and (-90 <= lon_f <= 90) and (-180 <= lat_f <= 180)) or \
                 (abs(lat_f) > 65.0 and abs(lon_f) <= 40.0)
    if is_flipped:
        warnings.append(f"Swapped latitude/longitude coordinates detected and auto-corrected (original lat={lat_f}, lon={lon_f})")
        lat_f, lon_f = lon_f, lat_f
        
    if not (-90.0 <= lat_f <= 90.0):
        warnings.append(f"Invalid latitude {lat_f} (must be between -90 and 90)")
        return None, None, warnings
        
    if not (-180.0 <= lon_f <= 180.0):
        warnings.append(f"Invalid longitude {lon_f} (must be between -180 and 180)")
        return None, None, warnings
        
    return round(lat_f, 7), round(lon_f, 7), warnings

def validate_record(record: Dict[str, Any], seen_ids: set) -> Tuple[bool, List[str]]:
    """
    Performs comprehensive data quality checks on an incoming record.
    Returns (is_valid, list_of_quality_warnings)
    """
    warnings = []
    is_valid = True
    
    # 1. Mandatory identifier
    rec_id = record.get("source_record_id")
    if not rec_id or str(rec_id).strip() in ("", "None", "nan"):
        warnings.append("Missing mandatory source record ID")
        is_valid = False
    elif str(rec_id).strip() in seen_ids:
        warnings.append(f"Duplicate source record ID within source: '{rec_id}'")
        is_valid = False
    else:
        seen_ids.add(str(rec_id).strip())
        
    # 2. Parcel / Survey number check
    survey_no = record.get("parcel_or_survey_number")
    if not survey_no:
        warnings.append("Missing parcel or survey number")
    elif len(str(survey_no).strip()) < 1:
        warnings.append("Empty or malformed survey number")
        
    # 3. Area check
    area = record.get("land_area")
    if area is not None:
        if area <= 0:
            warnings.append(f"Non-positive area value: {area}")
        elif area > 100_000_000: # 100 sq km for a single parcel is suspiciously large
            warnings.append(f"Unusually large parcel area: {area} m²")
            
    # 4. Coordinates / Geometry check
    lat = record.get("latitude")
    lon = record.get("longitude")
    geom = record.get("parcel_geometry")
    
    if lat is not None and lon is not None:
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            warnings.append(f"Coordinates out of bounds: ({lat}, {lon})")
            
    if geom is not None and not isinstance(geom, dict):
        warnings.append("Geometry is not a valid GeoJSON object")
        
    return is_valid, warnings
