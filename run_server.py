#!/usr/bin/env python3
"""
Wiko Defect Analyzer - Standalone API Server (GPT-5.2)
=============================================
Single-file version that doesn't require subdirectories.
Run with: python run_server.py
"""

import os
import sys
import json
import base64
import asyncio
import uuid
import tempfile
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# ENUMS AND DATA CLASSES
# ============================================================================

class DefectType(Enum):
    BLADE_SCRATCH = "blade_scratch"
    BLADE_CHIP = "blade_chip"
    EDGE_IRREGULARITY = "edge_irregularity"
    HANDLE_CRACK = "handle_crack"
    HANDLE_DISCOLORATION = "handle_discoloration"
    WELD_DEFECT = "weld_defect"
    POLISH_DEFECT = "polish_defect"
    RUST_SPOT = "rust_spot"
    DIMENSIONAL_ERROR = "dimensional_error"
    ASSEMBLY_MISALIGNMENT = "assembly_misalignment"
    SURFACE_CONTAMINATION = "surface_contamination"
    HEAT_TREATMENT_DEFECT = "heat_treatment_defect"
    UNKNOWN = "unknown"


class ProductionStage(Enum):
    BLADE_STAMP = "blade_stamp"
    BOLSTER_WELDING = "bolster_welding"
    BACK_EDGE_POLISHING = "back_edge_polishing"
    TAPER_GRINDING = "taper_grinding"
    HEAT_TREATMENT = "heat_treatment"
    VACUUM_QUENCH = "vacuum_quench"
    HANDLE_INJECTION = "handle_injection"
    RIVET_ASSEMBLY = "rivet_assembly"
    HANDLE_POLISHING = "handle_polishing"
    BLADE_GLAZING = "blade_glazing"
    CUTTING_EDGE_HONING = "cutting_edge_honing"
    LOGO_PRINT = "logo_print"
    INSPECTION = "inspection"
    PACKAGING = "packaging"


class Severity(Enum):
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    COSMETIC = "cosmetic"


@dataclass
class DefectAnalysis:
    defect_id: str
    timestamp: datetime
    facility: str
    product_sku: str
    image_url: Optional[str] = None
    defect_detected: bool = False
    defect_type: DefectType = DefectType.UNKNOWN
    severity: Severity = Severity.COSMETIC
    confidence: float = 0.0
    bounding_box: Optional[Dict[str, int]] = None
    description: str = ""
    affected_area: str = ""
    probable_stage: Optional[ProductionStage] = None
    root_cause: str = ""
    five_why_chain: List[str] = field(default_factory=list)
    contributing_factors: List[str] = field(default_factory=list)
    ishikawa_analysis: Optional[Dict[str, str]] = None
    corrective_actions: List[str] = field(default_factory=list)
    preventive_actions: List[str] = field(default_factory=list)
    reasoning_tokens_used: int = 0
    model_version: str = "gpt-5.2"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "defect_id": self.defect_id,
            "timestamp": self.timestamp.isoformat(),
            "facility": self.facility,
            "product_sku": self.product_sku,
            "defect_detected": self.defect_detected,
            "defect_type": self.defect_type.value,
            "severity": self.severity.value,
            "confidence": self.confidence,
            "description": self.description,
            "affected_area": self.affected_area,
            "bounding_box": self.bounding_box,
            "probable_stage": self.probable_stage.value if self.probable_stage else None,
            "root_cause": self.root_cause,
            "five_why_chain": self.five_why_chain,
            "contributing_factors": self.contributing_factors,
            "ishikawa_analysis": self.ishikawa_analysis,
            "corrective_actions": self.corrective_actions,
            "preventive_actions": self.preventive_actions,
            "reasoning_tokens_used": self.reasoning_tokens_used,
            "model_version": self.model_version,
        }


# ============================================================================
# GPT-5.2 DEFECT ANALYZER
# ============================================================================

class WikoDefectAnalyzer:
    """GPT-5.2 powered defect analyzer for Wiko manufacturing"""
    
    WIKO_CONTEXT = """
    <wiko_manufacturing_context>
    You are analyzing defects for Wiko Cutlery Ltd, a 61-year-old premium manufacturer.
    
    COMPANY: Hong Kong HQ, Shenzhen R&D, Yangjiang Production (800+ staff, 80,000m²)
    
    12-STAGE MANUFACTURING PROCESS:
    1. BLADE_STAMP: Stamping/forging from German 4116/4034 stainless steel
    2. BOLSTER_WELDING: Welding bolster to blade
    3. BACK_EDGE_POLISHING: Polishing back edge and bolster
    4. TAPER_GRINDING: V-shape taper grinding
    5. HEAT_TREATMENT: Heating to 1000°C
    6. VACUUM_QUENCH: **PROPRIETARY** Rapid cooling 1000°C→600°C in 2 minutes
       - Prevents chromium carbide formation, maintains rust resistance
    7. HANDLE_INJECTION: Injection molding of handles
    8. RIVET_ASSEMBLY: Attaching handle to tang
    9. HANDLE_POLISHING: Final handle finish
    10. BLADE_GLAZING: Mirror/satin finish
    11. CUTTING_EDGE_HONING: Final edge sharpening
    12. LOGO_PRINT: Branding + final inspection
    
    QUALITY STANDARDS:
    - CATRA sharpness: >50 ICP
    - Salt spray: 1000 hours corrosion resistance
    - Hardness: 54-58 HRC
    - Defect rate target: 0.18%
    
    DEFECT-TO-STAGE PATTERNS:
    - Rust spots → VACUUM_QUENCH failure
    - Edge irregularity → TAPER_GRINDING or CUTTING_EDGE_HONING
    - Handle cracks → HANDLE_INJECTION parameters
    - Weld defects → BOLSTER_WELDING
    </wiko_manufacturing_context>
    """
    
    def __init__(self):
        self.endpoint = os.getenv("AZURE_AI_PROJECT_ENDPOINT", "")
        self.api_key = os.getenv("AZURE_AI_API_KEY", "")
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2025-04-01-preview")
        self.deployment = os.getenv("AZURE_VISION_DEPLOYMENT", "gpt-5.2")
        self.reports_deployment = os.getenv("AZURE_REPORTS_DEPLOYMENT", "gpt-5.2")
        
        # Clean endpoint
        if "/api/projects/" in self.endpoint:
            self.endpoint = self.endpoint.split("/api/projects/")[0]
        
        self.client = AzureOpenAI(
            azure_endpoint=self.endpoint,
            api_key=self.api_key,
            api_version=self.api_version
        )
    
    def _encode_image(self, image_path: str) -> str:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    
    def _get_media_type(self, path: str) -> str:
        ext = path.lower().split('.')[-1]
        return {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}.get(ext, "image/jpeg")
    
    async def analyze_defect(
        self,
        image_path: str,
        product_sku: str,
        facility: str = "yangjiang",
        production_data: Optional[Dict] = None
    ) -> DefectAnalysis:
        """Main analysis pipeline"""
        
        defect_id = f"DEF-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
        
        # Step 1: Vision + Classification
        vision_result = await self._analyze_image(image_path, product_sku)
        
        # Step 2: RCA (if defect found)
        rca_result = None
        if vision_result.get("defect_detected"):
            rca_result = await self._root_cause_analysis(vision_result, production_data)
        
        # Step 3: Recommendations
        recommendations = await self._generate_recommendations(vision_result, rca_result)
        
        return DefectAnalysis(
            defect_id=defect_id,
            timestamp=datetime.now(),
            facility=facility,
            product_sku=product_sku,
            image_url=image_path,
            defect_detected=vision_result.get("defect_detected", False),
            defect_type=DefectType(vision_result.get("defect_type", "unknown")),
            severity=Severity(vision_result.get("severity", "cosmetic")),
            confidence=vision_result.get("confidence", 0.0),
            description=vision_result.get("description", ""),
            affected_area=vision_result.get("affected_area", ""),
            bounding_box=vision_result.get("bounding_box"),
            probable_stage=ProductionStage(rca_result["probable_stage"]) if rca_result and rca_result.get("probable_stage") else None,
            root_cause=rca_result.get("root_cause", "") if rca_result else "",
            five_why_chain=rca_result.get("five_why_chain", []) if rca_result else [],
            contributing_factors=rca_result.get("contributing_factors", []) if rca_result else [],
            ishikawa_analysis=rca_result.get("ishikawa_analysis") if rca_result else None,
            corrective_actions=recommendations.get("corrective_actions", []),
            preventive_actions=recommendations.get("preventive_actions", []),
        )
    
    async def _analyze_image(self, image_path: str, product_sku: str) -> Dict:
        """Vision + Classification with GPT-5.2"""
        
        image_base64 = self._encode_image(image_path)
        media_type = self._get_media_type(image_path)
        
        system_prompt = f"""
        {self.WIKO_CONTEXT}
        
        TASK: Analyze this product image for manufacturing defects.
        
        DEFECT TYPES: blade_scratch, blade_chip, edge_irregularity, handle_crack, 
        handle_discoloration, weld_defect, polish_defect, rust_spot, dimensional_error,
        assembly_misalignment, surface_contamination, heat_treatment_defect, unknown
        
        SEVERITY: critical (safety/process failure), major (cannot ship), 
        minor (ship with discount), cosmetic (acceptable)
        
        Respond ONLY with JSON:
        {{
            "defect_detected": true/false,
            "defect_type": "type",
            "severity": "level",
            "confidence": 0.0-1.0,
            "description": "detailed description",
            "affected_area": "blade/edge/handle/bolster/rivet",
            "bounding_box": {{"x": int, "y": int, "width": int, "height": int}} or null,
            "visual_evidence": ["observations"],
            "classification_reasoning": "why this classification"
        }}
        """
        
        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"Inspect this {product_sku} for defects."},
                        {"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{image_base64}", "detail": "high"}}
                    ]
                }
            ],
            max_completion_tokens=2000,
            response_format={"type": "json_object"},
            reasoning_effort="high"
        )
        
        return json.loads(response.choices[0].message.content)
    
    async def _root_cause_analysis(self, vision_result: Dict, production_data: Optional[Dict]) -> Dict:
        """Deep RCA with xhigh reasoning"""
        
        system_prompt = f"""
        {self.WIKO_CONTEXT}
        
        TASK: Perform root cause analysis using 5-Why and Ishikawa methodology.
        
        Respond ONLY with JSON:
        {{
            "probable_stage": "production_stage",
            "root_cause": "root cause statement",
            "five_why_chain": ["why1", "why2", "why3", "why4", "why5"],
            "contributing_factors": ["factor1", "factor2"],
            "ishikawa_analysis": {{
                "machine": "equipment factors",
                "material": "material factors",
                "method": "process factors",
                "man": "human factors",
                "measurement": "measurement factors",
                "environment": "environmental factors"
            }}
        }}
        """
        
        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyze root cause:\n{json.dumps(vision_result, indent=2)}\n\nProduction data: {json.dumps(production_data) if production_data else 'None'}"}
            ],
            max_completion_tokens=2000,
            response_format={"type": "json_object"},
            reasoning_effort="xhigh"  # Maximum reasoning for RCA
        )
        
        return json.loads(response.choices[0].message.content)
    
    async def _generate_recommendations(self, vision_result: Dict, rca_result: Optional[Dict]) -> Dict:
        """Generate actionable recommendations"""
        
        system_prompt = f"""
        {self.WIKO_CONTEXT}
        
        Generate specific, actionable recommendations for Wiko's Yangjiang facility.
        
        Respond ONLY with JSON:
        {{
            "corrective_actions": ["immediate action 1", "immediate action 2"],
            "preventive_actions": ["long-term action 1", "long-term action 2"],
            "escalation_required": true/false,
            "estimated_resolution_time": "time estimate"
        }}
        """
        
        response = self.client.chat.completions.create(
            model=self.reports_deployment,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Vision: {json.dumps(vision_result)}\nRCA: {json.dumps(rca_result) if rca_result else 'No defect'}"}
            ],
            max_completion_tokens=1000,
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)


# ============================================================================
# FLASK API
# ============================================================================

app = Flask(__name__)
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
analyzer = WikoDefectAnalyzer()


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "service": "wiko-defect-analyzer",
        "model": "gpt-5.2",
        "timestamp": datetime.now().isoformat()
    })


@app.route('/api/v1/analyze', methods=['POST'])
def analyze():
    """Analyze single image for defects"""
    
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400
    
    file = request.files['image']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({"error": "Invalid file"}), 400
    
    product_sku = request.form.get('product_sku', 'WK-KN-200')
    facility = request.form.get('facility', 'yangjiang')
    
    # Parse optional production data
    production_data = None
    if 'production_data' in request.form:
        try:
            production_data = json.loads(request.form['production_data'])
        except:
            pass
    
    # Save temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name
    
    try:
        result = run_async(analyzer.analyze_defect(tmp_path, product_sku, facility, production_data))
        return jsonify({"success": True, "analysis": result.to_dict()})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.route('/api/v1/defect-types', methods=['GET'])
def defect_types():
    return jsonify({"defect_types": [{"code": dt.value} for dt in DefectType]})


@app.route('/api/v1/production-stages', methods=['GET'])
def production_stages():
    return jsonify({"stages": [{"code": ps.value} for ps in ProductionStage]})


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("""
╔═══════════════════════════════════════════════════════════╗
║     WIKO DEFECT ANALYZER API - GPT-5.2                    ║
╠═══════════════════════════════════════════════════════════╣
║  Endpoints:                                                ║
║    GET  /health              - Health check               ║
║    POST /api/v1/analyze      - Analyze image              ║
║    GET  /api/v1/defect-types - List defect types          ║
╠═══════════════════════════════════════════════════════════╣
║  Test with:                                                ║
║    curl -X POST http://localhost:5000/api/v1/analyze \\    ║
║      -F "image=@knife.jpg" -F "product_sku=WK-KN-200"     ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    port = int(os.getenv('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)
