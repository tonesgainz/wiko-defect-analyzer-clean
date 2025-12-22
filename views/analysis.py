"""
Analysis-related API endpoints for Wiko Defect Analyzer
"""

import asyncio
import json
from datetime import datetime
from flask import Blueprint, request, jsonify
from agents.defect_analyzer import WikoDefectAnalyzer, DefectAnalysis, DefectType, Severity, ProductionStage
from config import Config

analysis_bp = Blueprint('analysis_bp', __name__)
analyzer = WikoDefectAnalyzer()
ALLOWED_EXTENSIONS = Config.ALLOWED_EXTENSIONS

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@analysis_bp.route('/analyze', methods=['POST'])
async def analyze_defect():
    """
    Analyze a single product image for defects.
    """
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400
    
    file = request.files['image']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({"error": "Invalid file"}), 400
    
    product_sku = request.form.get('product_sku', 'WK-KN-200')
    facility = request.form.get('facility', 'yangjiang')
    
    production_data = None
    if 'production_data' in request.form:
        try:
            production_data = json.loads(request.form['production_data'])
        except:
            pass
            
    image_bytes = file.read()

    try:
        result = await analyzer.analyze_defect(
            image_bytes=image_bytes,
            product_sku=product_sku,
            facility=facility,
            production_data=production_data
        )
        return jsonify({"success": True, "analysis": result.to_dict()})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@analysis_bp.route('/analyze/batch', methods=['POST'])
async def analyze_batch():
    """
    Analyze multiple product images in batch.
    """
    if 'images' not in request.files:
        return jsonify({"error": "No image files provided"}), 400
    
    files = request.files.getlist('images')
    if not files or len(files) == 0:
        return jsonify({"error": "No files selected"}), 400
    
    product_sku = request.form.get('product_sku')
    if not product_sku:
        return jsonify({"error": "product_sku is required"}), 400
    
    facility = request.form.get('facility', 'yangjiang')
    
    image_bytes_list = []
    for file in files:
        if file and allowed_file(file.filename):
            image_bytes_list.append(file.read())

    if not image_bytes_list:
        return jsonify({"error": "No valid image files provided"}), 400

    try:
        results = await analyzer.analyze_batch(
            image_bytes_list=image_bytes_list,
            product_sku=product_sku,
            facility=facility
        )
        
        summary = analyzer.generate_shift_report(results)
        
        return jsonify({
            "success": True,
            "count": len(results),
            "analyses": [r.to_dict() for r in results],
            "summary": summary
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@analysis_bp.route('/shift-report', methods=['POST'])
def generate_shift_report():
    """
    Generate a shift summary report from analysis IDs.
    """
    data = request.get_json()
    if not data or 'analyses' not in data:
        return jsonify({"error": "analyses array is required"}), 400
    
    try:
        analyses = []
        for a in data['analyses']:
            analysis = DefectAnalysis(
                defect_id=a['defect_id'],
                timestamp=datetime.fromisoformat(a['timestamp']),
                facility=a['facility'],
                product_sku=a['product_sku'],
                defect_detected=a['defect_detected'],
                defect_type=DefectType(a['defect_type']),
                severity=Severity(a['severity']),
                confidence=a['confidence'],
                description=a.get('description', ''),
                probable_stage=ProductionStage(a['probable_stage']) if a.get('probable_stage') else None,
                root_cause=a.get('root_cause', ''),
                contributing_factors=a.get('contributing_factors', []),
                corrective_actions=a.get('corrective_actions', []),
                preventive_actions=a.get('preventive_actions', []),
            )
            analyses.append(analysis)
        
        report = analyzer.generate_shift_report(analyses)
        
        return jsonify({
            "success": True,
            "report": report
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
