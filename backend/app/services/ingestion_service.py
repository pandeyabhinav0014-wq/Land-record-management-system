"""
Data Ingestion and Quality Validation Service (Section 4 & 5)
Parses CSV, Excel (.xlsx/.xls), GeoJSON, and Shapefile ZIP archives.
Applies column mapping wizard, data normalization, coordinate checks, and generates
detailed quality reports.
"""

import io
import json
import zipfile
import uuid
from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
from matching.normalization import (
    normalize_text,
    normalize_survey_number,
    normalize_area,
    normalize_coordinates,
    validate_record
)
from gis.geometry_validation import validate_and_repair_geometry, extract_centroid

class IngestionService:
    @staticmethod
    def parse_file(filename: str, file_bytes: bytes) -> Tuple[List[Dict[str, Any]], str]:
        """
        Extracts raw record dictionaries from uploaded file.
        Returns (raw_records, detected_format)
        """
        fname_lower = filename.lower()
        if fname_lower.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(file_bytes), dtype=str)
            records = df.where(pd.notnull(df), None).to_dict(orient="records")
            return records, "CSV"
            
        elif fname_lower.endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(file_bytes), dtype=str)
            records = df.where(pd.notnull(df), None).to_dict(orient="records")
            return records, "EXCEL"
            
        elif fname_lower.endswith(".geojson") or fname_lower.endswith(".json"):
            content = json.loads(file_bytes.decode("utf-8"))
            records = []
            if isinstance(content, dict) and content.get("type") == "FeatureCollection":
                for feat in content.get("features", []):
                    props = feat.get("properties", {}) or {}
                    props["_geometry"] = feat.get("geometry")
                    records.append(props)
            elif isinstance(content, list):
                records = content
            return records, "GEOJSON"
            
        elif fname_lower.endswith(".zip"):
            # Shapefile ZIP archive extraction
            records = []
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
                # Look for .geojson or .dbf or shapefile components
                file_names = z.namelist()
                geojson_files = [f for f in file_names if f.lower().endswith(".geojson") or f.lower().endswith(".json")]
                csv_files = [f for f in file_names if f.lower().endswith(".csv")]
                
                if geojson_files:
                    data = json.loads(z.read(geojson_files[0]).decode("utf-8"))
                    for feat in data.get("features", []):
                        props = feat.get("properties", {}) or {}
                        props["_geometry"] = feat.get("geometry")
                        records.append(props)
                elif csv_files:
                    df = pd.read_csv(io.BytesIO(z.read(csv_files[0])), dtype=str)
                    records = df.where(pd.notnull(df), None).to_dict(orient="records")
                else:
                    # Provide informative message if pure binary ESRI shapefile without simple reader
                    raise ValueError("ZIP archive must contain a .geojson, .json, or .csv layer representation.")
            return records, "SHAPEFILE_ZIP"
            
        else:
            raise ValueError(f"Unsupported file format for '{filename}'. Supported: CSV, Excel, GeoJSON, Shapefile ZIP.")

    @staticmethod
    def map_and_normalize(
        raw_records: List[Dict[str, Any]],
        mapping_spec: Dict[str, str],
        source_id: str,
        source_name: str
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Maps raw input dictionary keys to Common Internal Schema and applies normalization.
        Returns: (normalized_records, data_quality_report)
        """
        normalized_records: List[Dict[str, Any]] = []
        validation_issues: List[Dict[str, Any]] = []
        seen_ids = set()

        for idx, raw in enumerate(raw_records):
            row_warnings = []
            
            # Map fields according to mapping_spec
            # Field keys: source_record_id, parcel_or_survey_number, owner_name, property_address,
            # land_area, area_unit, latitude, longitude, parcel_geometry, land_use_category, record_date, village_or_locality
            raw_id = raw.get(mapping_spec.get("source_record_id", "id"))
            raw_survey = raw.get(mapping_spec.get("parcel_or_survey_number", "survey_no"))
            raw_owner = raw.get(mapping_spec.get("owner_name", "owner"))
            raw_addr = raw.get(mapping_spec.get("property_address", "address"))
            raw_area = raw.get(mapping_spec.get("land_area", "area"))
            unit_col = mapping_spec.get("area_unit")
            raw_unit = raw.get(unit_col) if unit_col else "sq_meters"
            raw_lat = raw.get(mapping_spec.get("latitude", "latitude"))
            raw_lon = raw.get(mapping_spec.get("longitude", "longitude"))
            
            # Geometry can be mapped directly or passed in from GeoJSON _geometry
            geom_col = mapping_spec.get("parcel_geometry", "geometry")
            raw_geom = raw.get(geom_col) or raw.get("_geometry")
            if isinstance(raw_geom, str):
                try:
                    raw_geom = json.loads(raw_geom)
                except Exception:
                    pass

            raw_land_use = raw.get(mapping_spec.get("land_use_category", "land_use"))
            raw_date = raw.get(mapping_spec.get("record_date", "date"))
            raw_locality = raw.get(mapping_spec.get("village_or_locality", "village"))

            # Normalize values
            norm_id = str(raw_id).strip() if raw_id is not None else None
            norm_survey = normalize_survey_number(raw_survey)
            norm_owner = normalize_text(raw_owner)
            norm_addr = normalize_text(raw_addr)
            norm_locality = normalize_text(raw_locality)
            norm_land_use = normalize_text(raw_land_use)
            
            # Normalize Area
            norm_area_sqm, norm_unit, area_warn = normalize_area(raw_area, raw_unit)
            row_warnings.extend(area_warn)
            
            # Normalize Coordinates
            norm_lat, norm_lon, coord_warn = normalize_coordinates(raw_lat, raw_lon)
            row_warnings.extend(coord_warn)
            
            # Validate and Repair Geometry
            repaired_geom, geom_valid, geom_warn = validate_and_repair_geometry(raw_geom)
            row_warnings.extend(geom_warn)
            
            # If coordinates were missing but geometry exists, extract centroid
            if (norm_lat is None or norm_lon is None) and repaired_geom:
                centroid = extract_centroid(repaired_geom)
                if centroid:
                    norm_lat, norm_lon = centroid
            
            # Validate Record
            record_dict = {
                "source_id": source_id,
                "source_name": source_name,
                "source_record_id": norm_id,
                "parcel_or_survey_number": norm_survey,
                "owner_name": norm_owner,
                "property_address": norm_addr,
                "land_area": norm_area_sqm,
                "area_unit": norm_unit or "sq_meters",
                "original_area": float(raw_area) if raw_area and str(raw_area).replace('.', '', 1).isdigit() else None,
                "latitude": norm_lat,
                "longitude": norm_lon,
                "parcel_geometry": repaired_geom,
                "land_use_category": norm_land_use,
                "record_date": str(raw_date).strip() if raw_date else None,
                "village_or_locality": norm_locality,
                "raw_attributes": raw
            }

            is_valid, val_warnings = validate_record(record_dict, seen_ids)
            row_warnings.extend(val_warnings)

            record_dict["is_valid"] = is_valid
            record_dict["quality_warnings"] = row_warnings

            if not is_valid or row_warnings:
                validation_issues.append({
                    "row_index": idx + 1,
                    "source_record_id": norm_id,
                    "is_valid": is_valid,
                    "warnings": row_warnings,
                    "raw_record": raw
                })

            normalized_records.append(record_dict)

        total_records = len(normalized_records)
        invalid_count = sum(1 for r in normalized_records if not r["is_valid"])
        valid_count = total_records - invalid_count
        warnings_count = sum(len(r["quality_warnings"]) for r in normalized_records)

        quality_report = {
            "source_id": source_id,
            "source_name": source_name,
            "total_records": total_records,
            "valid_records_count": valid_count,
            "invalid_records_count": invalid_count,
            "warnings_count": warnings_count,
            "validation_issues": validation_issues,
            "sample_records": normalized_records[:5]
        }

        return normalized_records, quality_report

