"""
Metadata-related API endpoints for Wiko Defect Analyzer
"""

from flask import Blueprint, jsonify
from config import get_defect_types as get_defect_types_data, get_production_stages as get_production_stages_data, get_facilities as get_facilities_data

metadata_bp = Blueprint('metadata_bp', __name__)

@metadata_bp.route('/defect-types', methods=['GET'])
def get_defect_types():
    """List all defect types and their descriptions"""
    return jsonify({"defect_types": get_defect_types_data()})


@metadata_bp.route('/production-stages', methods=['GET'])
def get_production_stages():
    """List all production stages in order"""
    return jsonify({"production_stages": get_production_stages_data()})


@metadata_bp.route('/facilities', methods=['GET'])
def get_facilities():
    """List Wiko manufacturing facilities"""
    return jsonify({"facilities": get_facilities_data()})
