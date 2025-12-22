"""
Wiko Defect Analyzer Configuration
==================================
Centralized configuration and data for the application.
"""

from agents.defect_analyzer import DefectType, ProductionStage

class Config:
    """Application configuration"""
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
    
    # Using the enums from the agent
    DEFECT_TYPES_DATA = {
        "blade_scratch": "Surface scratches on the blade",
        "blade_chip": "Missing material from blade edge",
        "edge_irregularity": "Uneven or wavy cutting edge",
        "handle_crack": "Cracks in handle material",
        "handle_discoloration": "Color inconsistency in handle",
        "weld_defect": "Issues with bolster welding",
        "polish_defect": "Uneven or missing polish",
        "rust_spot": "Oxidation marks (indicates cooling issue)",
        "dimensional_error": "Size/shape out of specification",
        "assembly_misalignment": "Components not properly aligned",
        "unknown": "Cannot classify"
    }

    PRODUCTION_STAGES_DATA = [
        {"code": "blade_stamp", "name": "Blade Stamping/Forging", "order": 1},
        {"code": "bolster_welding", "name": "Bolster Welding", "order": 2},
        {"code": "back_edge_polishing", "name": "Back Edge & Bolster Polishing", "order": 3},
        {"code": "taper_grinding", "name": "Taper Grinding (V-shape)", "order": 4},
        {"code": "heat_treatment", "name": "Heat Treatment (1000°C)", "order": 5},
        {"code": "vacuum_quench", "name": "Vacuum Quench Rapid Cooling", "order": 6},
        {"code": "handle_injection", "name": "Handle Injection Molding", "order": 7},
        {"code": "rivet_assembly", "name": "Rivet Assembly", "order": 8},
        {"code": "handle_polishing", "name": "Handle Polishing", "order": 9},
        {"code": "blade_glazing", "name": "Blade Glazing", "order": 10},
        {"code": "cutting_edge_honing", "name": "Cutting Edge Honing", "order": 11},
        {"code": "logo_print", "name": "Logo Print", "order": 12},
        {"code": "inspection", "name": "Final Inspection", "order": 13},
        {"code": "packaging", "name": "Packaging", "order": 14},
    ]

    FACILITIES_DATA = [
        {
            "code": "hongkong",
            "name": "Hong Kong HQ",
            "location": "Kwai Chung District",
            "role": "Headquarters",
            "functions": ["Sales", "Management Office", "Showroom"]
        },
        {
            "code": "shenzhen",
            "name": "Shenzhen Support Office",
            "location": "Futian District",
            "role": "Support Office",
            "functions": ["R&D", "Logistics", "Finance", "Showroom"]
        },
        {
            "code": "yangjiang",
            "name": "Yangjiang Production",
            "location": "Yangxi County",
            "role": "Production Site",
            "functions": ["R&D", "Production", "Packaging"],
            "capacity": "1M+ units/month",
            "floor_area": "80,000m²"
        }
    ]

def get_defect_types():
    """List all defect types and their descriptions"""
    return [
        {"code": dt.value, "description": Config.DEFECT_TYPES_DATA.get(dt.value, "")}
        for dt in DefectType
    ]

def get_production_stages():
    """List all production stages in order"""
    return Config.PRODUCTION_STAGES_DATA

def get_facilities():
    """List Wiko manufacturing facilities"""
    return Config.FACILITIES_DATA
