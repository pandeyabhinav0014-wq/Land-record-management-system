"""
Ground Truth Benchmark Dataset Generator & Loader (Section 11)
Creates realistic multi-source land record benchmarks with known entity clusters
and ground-truth labels (SAME_PARCEL vs DIFFERENT_PARCEL).
"""

from typing import List, Dict, Any, Tuple
import hashlib
import json

def generate_benchmark_datasets() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Generates three realistic synthetic datasets reflecting real-world land record anomalies:
    - Source A: Revenue Department Land Records (cadastral survey & tax ledger)
    - Source B: Municipal Property Authority (ward, door numbers, property tax)
    - Source C: GIS Boundary Cadastre (digital polygons, centroid coordinates)
    
    Also generates ground_truth_pairs list with true 'is_match' booleans.
    """
    
    # Base canonical parcels
    # Parcel 1: Agri / Residential conversion in Village Rampur
    # Parcel 2: Commercial plot in Ward 12
    # Parcel 3: Boundary disputed agricultural land in Rampur
    # Parcel 4: Urban industrial warehouse
    # Parcel 5: Forest fringe conservation parcel

    # Source A: Revenue Records
    source_a_records = [
        {
            "source_name": "Revenue Department",
            "source_record_id": "REV-2024-101",
            "parcel_or_survey_number": "14/1",
            "owner_name": "RAMESHWAR PRASAD SHARMA",
            "property_address": "RAMPUR VILLAGE NEAR CANAL DIST SHAMLI",
            "land_area": 4046.86, # 1.0 Acre in sqm
            "area_unit": "acres",
            "original_area": 1.0,
            "latitude": 28.6139,
            "longitude": 77.2090,
            "land_use_category": "AGRICULTURAL",
            "record_date": "2020-05-12",
            "village_or_locality": "RAMPUR"
        },
        {
            "source_name": "Revenue Department",
            "source_record_id": "REV-2024-102",
            "parcel_or_survey_number": "14/2-A",
            "owner_name": "SUNITA DEVI & RAJESH KUMAR",
            "property_address": "PLOT 14/2 RAMPUR VILLAGE ROAD",
            "land_area": 2529.29, # 1.0 Bigha
            "area_unit": "bigha",
            "original_area": 1.0,
            "latitude": 28.6145,
            "longitude": 77.2105,
            "land_use_category": "AGRICULTURAL",
            "record_date": "2019-11-20",
            "village_or_locality": "RAMPUR"
        },
        {
            "source_name": "Revenue Department",
            "source_record_id": "REV-2024-103",
            "parcel_or_survey_number": "52/B",
            "owner_name": "METRO LOGISTICS LTD",
            "property_address": "SECTOR 6 INDUSTRIAL CORRIDOR",
            "land_area": 8093.71, # 2.0 Acres
            "area_unit": "acres",
            "original_area": 2.0,
            "latitude": 28.6250,
            "longitude": 77.2210,
            "land_use_category": "INDUSTRIAL",
            "record_date": "2022-01-15",
            "village_or_locality": "SECTOR 6"
        },
        {
            "source_name": "Revenue Department",
            "source_record_id": "REV-2024-104",
            "parcel_or_survey_number": "108/3",
            "owner_name": "ANAND SWAROOP VERMA",
            "property_address": "OLD CIVIL LINES WARD 4",
            "land_area": 836.13, # 1000 sq yards
            "area_unit": "sq_yards",
            "original_area": 1000.0,
            "latitude": 28.6310,
            "longitude": 77.2150,
            "land_use_category": "RESIDENTIAL",
            "record_date": "2018-04-10",
            "village_or_locality": "CIVIL LINES"
        },
        {
            "source_name": "Revenue Department",
            "source_record_id": "REV-2024-105",
            "parcel_or_survey_number": "210",
            "owner_name": "STATE FOREST RESERVE",
            "property_address": "NORTH GREEN BELT RIDGE",
            "land_area": 50000.0, # 5 Hectares
            "area_unit": "hectares",
            "original_area": 5.0,
            "latitude": 28.6400,
            "longitude": 77.2000,
            "land_use_category": "FOREST",
            "record_date": "2015-08-01",
            "village_or_locality": "NORTH RIDGE"
        }
    ]

    # Source B: Municipal Authority (with inconsistent spelling, variations, and missing fields)
    source_b_records = [
        {
            "source_name": "Municipal Property Records",
            "source_record_id": "MUN-PROP-881",
            "parcel_or_survey_number": "14/1", # Matches REV-101
            "owner_name": "RAMESHWAR P SHARMA", # Abbreviated
            "property_address": "CANAL RD RAMPUR VIL",
            "land_area": 4050.0, # Minor area variance
            "area_unit": "sq_meters",
            "original_area": 4050.0,
            "latitude": 28.6140, # 10m away
            "longitude": 77.2091,
            "land_use_category": "AGRICULTURE",
            "record_date": "2023-08-10",
            "village_or_locality": "RAMPUR"
        },
        {
            "source_name": "Municipal Property Records",
            "source_record_id": "MUN-PROP-882",
            "parcel_or_survey_number": "14/2A", # Delimiter variation of 14/2-A
            "owner_name": "RAJESH KUMAR SHARMA", # One co-owner listed
            "property_address": "14/2-A VILLAGE RAMPUR",
            "land_area": 2530.0,
            "area_unit": "sq_meters",
            "original_area": 2530.0,
            "latitude": 28.6144,
            "longitude": 77.2106,
            "land_use_category": "RESIDENTIAL", # Land use contradiction (Agri vs Residential)
            "record_date": "2023-01-05",
            "village_or_locality": "RAMPUR"
        },
        {
            "source_name": "Municipal Property Records",
            "source_record_id": "MUN-PROP-883",
            "parcel_or_survey_number": "52-B", # Matches REV-103
            "owner_name": "METRO LOGISTICS PRIVATE LIMITED",
            "property_address": "PLOT 52B SEC 6 IND AREA",
            "land_area": 8094.0,
            "area_unit": "sq_meters",
            "original_area": 8094.0,
            "latitude": 28.6251,
            "longitude": 77.2211,
            "land_use_category": "INDUSTRIAL",
            "record_date": "2022-09-30",
            "village_or_locality": "SECTOR 6"
        },
        {
            "source_name": "Municipal Property Records",
            "source_record_id": "MUN-PROP-884",
            "parcel_or_survey_number": "108/3-X", # Divergent survey suffix
            "owner_name": "ANAND S VERMA",
            "property_address": "CIVIL LINES WARD 4 PLOT 108",
            "land_area": 836.0,
            "area_unit": "sq_meters",
            "original_area": 836.0,
            "latitude": 28.6311,
            "longitude": 77.2151,
            "land_use_category": "RESIDENTIAL",
            "record_date": "2021-03-12",
            "village_or_locality": "CIVIL LINES"
        },
        {
            "source_name": "Municipal Property Records",
            "source_record_id": "MUN-PROP-999", # Non-matching distinct record
            "parcel_or_survey_number": "301/9",
            "owner_name": "BHARAT PETROLEUM CORP",
            "property_address": "NATIONAL HIGHWAY 24 JUNCTION",
            "land_area": 12000.0,
            "area_unit": "sq_meters",
            "original_area": 12000.0,
            "latitude": 28.6500,
            "longitude": 77.2300,
            "land_use_category": "COMMERCIAL",
            "record_date": "2024-02-01",
            "village_or_locality": "HIGHWAY BYPASS"
        }
    ]

    # Source C: GIS Cadastre (GeoJSON Polygons)
    source_c_records = [
        {
            "source_name": "GIS Survey Records",
            "source_record_id": "GIS-CAD-501",
            "parcel_or_survey_number": "14/1",
            "owner_name": None, # Missing owner in GIS
            "property_address": "RAMPUR REVENUE SECTOR CADASTRE",
            "land_area": 4048.0,
            "area_unit": "sq_meters",
            "original_area": 4048.0,
            "latitude": 28.6139,
            "longitude": 77.2090,
            "parcel_geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [77.2085, 28.6135],
                    [77.2095, 28.6135],
                    [77.2095, 28.6143],
                    [77.2085, 28.6143],
                    [77.2085, 28.6135]
                ]]
            },
            "land_use_category": "AGRICULTURAL",
            "record_date": "2023-11-01",
            "village_or_locality": "RAMPUR"
        },
        {
            "source_name": "GIS Survey Records",
            "source_record_id": "GIS-CAD-502",
            "parcel_or_survey_number": "14/2-A",
            "owner_name": "SUNITA DEVI",
            "property_address": "RAMPUR VILLAGE SECTOR B",
            "land_area": 2529.0,
            "area_unit": "sq_meters",
            "original_area": 2529.0,
            "latitude": 28.6145,
            "longitude": 77.2105,
            "parcel_geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [77.2100, 28.6140],
                    [77.2110, 28.6140],
                    [77.2110, 28.6150],
                    [77.2100, 28.6150],
                    [77.2100, 28.6140]
                ]]
            },
            "land_use_category": "AGRICULTURAL",
            "record_date": "2023-11-01",
            "village_or_locality": "RAMPUR"
        },
        {
            "source_name": "GIS Survey Records",
            "source_record_id": "GIS-CAD-503",
            "parcel_or_survey_number": "52/B",
            "owner_name": "METRO LOGISTICS",
            "property_address": "SECTOR 6 INDUSTRIAL CADASTRE",
            "land_area": 8092.0,
            "area_unit": "sq_meters",
            "original_area": 8092.0,
            "latitude": 28.6250,
            "longitude": 77.2210,
            "parcel_geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [77.2205, 28.6245],
                    [77.2215, 28.6245],
                    [77.2215, 28.6255],
                    [77.2205, 28.6255],
                    [77.2205, 28.6245]
                ]]
            },
            "land_use_category": "INDUSTRIAL",
            "record_date": "2023-11-01",
            "village_or_locality": "SECTOR 6"
        }
    ]

    # Ground truth pairwise labels (Source A vs Source B)
    ground_truth_pairs = [
        # True Positive Matches
        {"source_record_id_a": "REV-2024-101", "source_record_id_b": "MUN-PROP-881", "is_match": True, "notes": "Same parcel in Rampur"},
        {"source_record_id_a": "REV-2024-102", "source_record_id_b": "MUN-PROP-882", "is_match": True, "notes": "Same parcel with land-use discrepancy"},
        {"source_record_id_a": "REV-2024-103", "source_record_id_b": "MUN-PROP-883", "is_match": True, "notes": "Metro Logistics commercial parcel"},
        {"source_record_id_a": "REV-2024-104", "source_record_id_b": "MUN-PROP-884", "is_match": True, "notes": "Civil Lines residential property"},
        
        # True Negative Non-Matches (Cross-pairs in same village/sector)
        {"source_record_id_a": "REV-2024-101", "source_record_id_b": "MUN-PROP-882", "is_match": False, "notes": "Adjacent but distinct parcels (14/1 vs 14/2)"},
        {"source_record_id_a": "REV-2024-102", "source_record_id_b": "MUN-PROP-881", "is_match": False, "notes": "Distinct survey numbers"},
        {"source_record_id_a": "REV-2024-103", "source_record_id_b": "MUN-PROP-881", "is_match": False, "notes": "Different localities entirely"},
        {"source_record_id_a": "REV-2024-105", "source_record_id_b": "MUN-PROP-999", "is_match": False, "notes": "Forest vs Highway parcel"},
        {"source_record_id_a": "REV-2024-104", "source_record_id_b": "MUN-PROP-883", "is_match": False, "notes": "Civil Lines vs Sector 6"}
    ]

    return source_a_records, source_b_records, source_c_records, ground_truth_pairs

