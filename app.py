"""
Wiko Defect Analyzer REST API
==============================
Flask-based API for manufacturing defect analysis.
"""

import os
from datetime import datetime
from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
from views.analysis import analysis_bp
from views.metadata import metadata_bp

app = Flask(__name__)
CORS(app)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH

# Register Blueprints
app.register_blueprint(analysis_bp, url_prefix='/api/v1')
app.register_blueprint(metadata_bp, url_prefix='/api/v1')


@app.route('/', methods=['GET'])
def index():
    """API documentation endpoint"""
    return jsonify({
        "service": "Wiko Defect Analyzer API",
        "version": "1.0.0",
        "description": "AI-powered defect detection and root cause analysis for cutlery manufacturing",
        "endpoints": {
            "GET /health": "Health check",
            "GET /api/v1/defect-types": "List defect classifications",
            "GET /api/v1/production-stages": "List production stages",
            "GET /api/v1/facilities": "List Wiko facilities",
            "POST /api/v1/analyze": "Analyze single image (requires: image, product_sku)",
            "POST /api/v1/analyze/batch": "Batch image analysis",
            "POST /api/v1/shift-report": "Generate shift report"
        },
        "example": {
            "curl": "curl -X POST http://localhost:5001/api/v1/analyze -F 'image=@test.jpg' -F 'product_sku=WK-KN-200' -F 'facility=yangjiang'"
        },
        "documentation": "https://github.com/wiko-cutlery/defect-analyzer"
    })


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "wiko-defect-analyzer",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    })


@app.errorhandler(413)
def too_large(e):
    return jsonify({"error": "File too large. Maximum size is 16MB."}), 413


@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500


if __name__ == '__main__':
    port = int(os.getenv("PORT", "8080"))
    debug = os.getenv('FLASK_DEBUG', '0') == '1'
    
    print(f"""
    ╔═══════════════════════════════════════════════════════════╗
    ║     WIKO DEFECT ANALYZER API                              ║
    ║     Manufacturing Intelligence Platform                    ║
    ╠═══════════════════════════════════════════════════════════╣
    ║  Endpoints:                                                ║
    ║    POST /api/v1/analyze        - Single image analysis    ║
    ║    POST /api/v1/analyze/batch  - Batch analysis           ║
    ║    POST /api/v1/shift-report   - Generate shift report    ║
    ║    GET  /api/v1/defect-types   - List defect types        ║
    ║    GET  /api/v1/production-stages - Production flow       ║
    ║    GET  /api/v1/facilities     - Wiko facilities          ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    app.run(host='0.0.0.0', port=port, debug=debug)
