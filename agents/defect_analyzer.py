"""
Wiko Manufacturing Defect Analyzer Agent
=========================================
Multi-agent system for defect detection, classification, and root cause analysis
using Azure AI Foundry with GPT-4.1 and o3-mini models.
"""

import os
import base64
import json
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

load_dotenv()


class DefectType(Enum):
    """Classification of defect types in cutlery manufacturing"""
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
    UNKNOWN = "unknown"


class ProductionStage(Enum):
    """Production stages in Wiko's manufacturing process"""
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
    """Defect severity classification"""
    CRITICAL = "critical"  # Product cannot ship, safety concern
    MAJOR = "major"        # Product cannot ship, quality issue
    MINOR = "minor"        # Product can ship with discount
    COSMETIC = "cosmetic"  # Acceptable variance


@dataclass
class DefectAnalysis:
    """Result of defect analysis"""
    defect_id: str
    timestamp: datetime
    facility: str  # hongkong, shenzhen, yangjiang
    product_sku: str
    image_url: Optional[str] = None
    
    # Detection results
    defect_detected: bool = False
    defect_type: DefectType = DefectType.UNKNOWN
    severity: Severity = Severity.COSMETIC
    confidence: float = 0.0
    
    # Location in image
    bounding_box: Optional[Dict[str, int]] = None
    
    # Analysis details
    description: str = ""
    affected_area: str = ""
    
    # Root cause analysis
    probable_stage: Optional[ProductionStage] = None
    root_cause: str = ""
    contributing_factors: List[str] = field(default_factory=list)
    
    # Recommendations
    corrective_actions: List[str] = field(default_factory=list)
    preventive_actions: List[str] = field(default_factory=list)
    
    # Quality metrics correlation
    catra_correlation: Optional[Dict[str, Any]] = None
    
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
            "probable_stage": self.probable_stage.value if self.probable_stage else None,
            "root_cause": self.root_cause,
            "contributing_factors": self.contributing_factors,
            "corrective_actions": self.corrective_actions,
            "preventive_actions": self.preventive_actions,
        }


class WikoDefectAnalyzer:
    """
    Multi-agent defect analyzer for Wiko Cutlery manufacturing.
    
    Agents:
    1. Vision Agent (GPT-4.1): Analyzes images for visual defects
    2. Classification Agent (GPT-4.1): Classifies defect type and severity
    3. RCA Agent (o3-mini): Performs root cause analysis with deep reasoning
    4. Reporting Agent (GPT-4.1-mini): Generates corrective action reports
    """
    
    # Wiko-specific manufacturing context
    WIKO_CONTEXT = """
    You are analyzing defects for Wiko Cutlery Ltd, a premium manufacturer with:
    
    MANUFACTURING PROCESS (12-Stage Flow):
    1. Blade Stamping/Forging
    2. Bolster Welding (for forged knives)
    3. Back Edge & Bolster Polishing
    4. Taper Grinding (V-shape edge)
    5. Heat Treatment (1000°C)
    6. Vacuum Quench Rapid Cooling (proprietary - cools 1000°C to 600°C in 2 minutes)
       - Uses liquid nitrogen or quenching oil
       - Prevents chromium carbide formation
       - Reduces rust susceptibility
    7. Handle Injection Molding
    8. Rivet Assembly
    9. Handle Polishing
    10. Blade Glazing
    11. Cutting Edge Honing
    12. Logo Print & Final Inspection
    
    KEY QUALITY DIFFERENTIATORS:
    - Vacuum chamber rapid cooling maintains chromium levels (rust prevention)
    - German 4116/4034 stainless steel grades
    - CATRA sharpness testing: target >50 ICP
    - Salt spray testing: 1000 hours corrosion resistance
    - 0.18% historical defect rate target
    
    FACILITIES:
    - Hong Kong: HQ, Sales, R&D Showroom
    - Shenzhen: R&D, Logistics, Support (20 staff)
    - Yangjiang: Production (800+ staff, 80,000m² floor)
    
    COMMON DEFECT PATTERNS:
    - Rust spots often correlate with slow cooling (non-vacuum heat treatment)
    - Edge irregularities typically from grinding/honing stages
    - Handle defects from injection molding parameters
    - Weld defects from bolster attachment process
    """
    
    def __init__(self):
        """Initialize Azure AI clients for each agent"""
        self.project_endpoint = os.getenv("AZURE_AI_PROJECT_ENDPOINT")
        self.api_key = os.getenv("AZURE_AI_API_KEY")
        
        # Vision/Classification Agent - GPT-4.1 (multimodal)
        self.vision_client = AzureOpenAI(
            azure_endpoint=self._get_openai_endpoint(),
            api_key=self.api_key,
            api_version="2024-10-21"
        )
        self.vision_deployment = os.getenv("AZURE_VISION_DEPLOYMENT", "gpt-4-1-vision")
        
        # RCA Agent - o3-mini for deep reasoning
        self.reasoning_deployment = os.getenv("AZURE_REASONING_DEPLOYMENT", "o3-mini-reasoning")
        
        # Reporting Agent - GPT-4.1-mini for cost-effective reports
        self.reports_deployment = os.getenv("AZURE_REPORTS_DEPLOYMENT", "gpt-4-1-mini-reports")
    
    def _get_openai_endpoint(self) -> str:
        """Convert project endpoint to OpenAI endpoint format"""
        # Azure AI Foundry endpoint format varies; adjust as needed
        if "api.azureml.ms" in self.project_endpoint:
            return self.project_endpoint.replace("/api/projects/", "/openai/deployments/")
        return self.project_endpoint
    
    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64 for API submission"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    def _encode_image_bytes(self, image_bytes: bytes) -> str:
        """Encode image bytes to base64 for API submission"""
        return base64.b64encode(image_bytes).decode("utf-8")
    
    async def analyze_defect(
        self,
        product_sku: str,
        image_path: Optional[str] = None,
        image_bytes: Optional[bytes] = None,
        facility: str = "yangjiang",
        production_data: Optional[Dict[str, Any]] = None
    ) -> DefectAnalysis:
        """
        Main entry point: Orchestrates multi-agent defect analysis.
        
        Args:
            product_sku: Product SKU being inspected
            image_path: Path to product image (if image_bytes is not provided)
            image_bytes: Image content as bytes (preferred)
            facility: Manufacturing facility
            production_data: Optional batch/process data for correlation
            
        Returns:
            DefectAnalysis with complete analysis and recommendations
        """
        import uuid
        
        if not image_path and not image_bytes:
            raise ValueError("Either image_path or image_bytes must be provided.")

        defect_id = f"DEF-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
        
        # Step 1: Vision Agent - Detect and describe defects
        vision_result = await self._run_vision_agent(product_sku, image_path, image_bytes)
        
        # Step 2: Classification Agent - Classify type and severity
        classification = await self._run_classification_agent(vision_result, product_sku)
        
        # Step 3: RCA Agent - Deep reasoning for root cause (if defect detected)
        rca_result = None
        if classification.get("defect_detected"):
            rca_result = await self._run_rca_agent(
                vision_result,
                classification,
                production_data
            )
        
        # Step 4: Reporting Agent - Generate action recommendations
        recommendations = await self._run_reporting_agent(
            classification,
            rca_result
        )
        
        # Compile final analysis
        return DefectAnalysis(
            defect_id=defect_id,
            timestamp=datetime.now(),
            facility=facility,
            product_sku=product_sku,
            image_url=image_path, # Could be None if bytes are passed
            defect_detected=classification.get("defect_detected", False),
            defect_type=DefectType(classification.get("defect_type", "unknown")),
            severity=Severity(classification.get("severity", "cosmetic")),
            confidence=classification.get("confidence", 0.0),
            description=vision_result.get("description", ""),
            affected_area=vision_result.get("affected_area", ""),
            bounding_box=vision_result.get("bounding_box"),
            probable_stage=ProductionStage(rca_result["probable_stage"]) if rca_result else None,
            root_cause=rca_result.get("root_cause", "") if rca_result else "",
            contributing_factors=rca_result.get("contributing_factors", []) if rca_result else [],
            corrective_actions=recommendations.get("corrective_actions", []),
            preventive_actions=recommendations.get("preventive_actions", []),
        )
    
    async def _run_vision_agent(
        self,
        product_sku: str,
        image_path: Optional[str] = None,
        image_bytes: Optional[bytes] = None
    ) -> Dict[str, Any]:
        """
        Vision Agent: Analyze image for defects using GPT-4.1 multimodal.
        """
        if image_bytes:
            image_base64 = self._encode_image_bytes(image_bytes)
        elif image_path:
            image_base64 = self._encode_image(image_path)
        else:
            raise ValueError("Either image_path or image_bytes must be provided to vision agent.")

        system_prompt = f"""
        {self.WIKO_CONTEXT}
        
        VISION AGENT ROLE:
        You are a quality control vision specialist. Analyze the product image and:
        1. Identify any visual defects or anomalies
        2. Describe the defect location and characteristics
        3. Note the affected area (blade, edge, handle, bolster, etc.)
        4. Estimate defect dimensions if visible
        
        Product being inspected: {product_sku}
        
        Respond in JSON format:
        {{
            "defect_found": true/false,
            "description": "detailed description of what you see",
            "affected_area": "blade/edge/handle/bolster/assembly",
            "visual_characteristics": ["list", "of", "observations"],
            "bounding_box": {{"x": int, "y": int, "width": int, "height": int}} or null,
            "confidence_notes": "any uncertainty in observation"
        }}
        """
        
        response = self.vision_client.chat.completions.create(
            model=self.vision_deployment,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Analyze this {product_sku} for manufacturing defects."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000,
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    
    async def _run_classification_agent(
        self,
        vision_result: Dict[str, Any],
        product_sku: str
    ) -> Dict[str, Any]:
        """
        Classification Agent: Classify defect type and severity.
        """
        system_prompt = f"""
        {self.WIKO_CONTEXT}
        
        CLASSIFICATION AGENT ROLE:
        Based on the vision analysis, classify the defect:
        
        DEFECT TYPES:
        - blade_scratch: Surface scratches on blade
        - blade_chip: Missing material from blade edge
        - edge_irregularity: Uneven or wavy cutting edge
        - handle_crack: Cracks in handle material
        - handle_discoloration: Color inconsistency in handle
        - weld_defect: Issues with bolster welding
        - polish_defect: Uneven or missing polish
        - rust_spot: Oxidation marks (critical - indicates cooling issue)
        - dimensional_error: Size/shape out of specification
        - assembly_misalignment: Components not properly aligned
        - unknown: Cannot classify
        
        SEVERITY LEVELS:
        - critical: Safety concern, cannot ship (chips, cracks affecting function)
        - major: Quality issue, cannot ship (visible defects, rust)
        - minor: Can ship with discount (small cosmetic issues)
        - cosmetic: Acceptable variance (within tolerance)
        
        Respond in JSON:
        {{
            "defect_detected": true/false,
            "defect_type": "type_from_list",
            "severity": "severity_level",
            "confidence": 0.0-1.0,
            "classification_reasoning": "explanation"
        }}
        """
        
        response = self.vision_client.chat.completions.create(
            model=self.vision_deployment,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"Classify this defect observation:\n{json.dumps(vision_result, indent=2)}"
                }
            ],
            max_tokens=500,
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    
    async def _run_rca_agent(
        self,
        vision_result: Dict[str, Any],
        classification: Dict[str, Any],
        production_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        RCA Agent: Deep reasoning for root cause analysis using o3-mini.
        
        Uses reasoning model for complex causal analysis.
        """
        system_prompt = f"""
        {self.WIKO_CONTEXT}
        
        ROOT CAUSE ANALYSIS AGENT ROLE:
        Perform systematic root cause analysis using:
        
        1. DEFECT-TO-STAGE MAPPING:
        - Rust spots → Usually heat_treatment or vacuum_quench failure
        - Edge irregularity → taper_grinding or cutting_edge_honing
        - Blade scratches → blade_glazing or handle_polishing (contact)
        - Handle defects → handle_injection parameters
        - Weld defects → bolster_welding temperature/duration
        - Polish defects → polishing wheel wear or pressure
        
        2. 5-WHY ANALYSIS:
        Trace the defect back through likely causes.
        
        3. ISHIKAWA CATEGORIES:
        Consider: Machine, Material, Method, Man, Measurement, Environment
        
        Respond in JSON:
        {{
            "probable_stage": "production_stage_enum_value",
            "stage_confidence": 0.0-1.0,
            "root_cause": "primary root cause statement",
            "five_why_chain": ["why1", "why2", "why3", "why4", "why5"],
            "contributing_factors": ["factor1", "factor2"],
            "ishikawa_analysis": {{
                "machine": "relevant machine factors",
                "material": "relevant material factors",
                "method": "relevant method factors",
                "man": "relevant human factors",
                "measurement": "relevant measurement factors",
                "environment": "relevant environmental factors"
            }},
            "data_correlation": "any patterns with production data"
        }}
        """
        
        context = f"""
        VISION ANALYSIS:
        {json.dumps(vision_result, indent=2)}
        
        CLASSIFICATION:
        {json.dumps(classification, indent=2)}
        
        PRODUCTION DATA:
        {json.dumps(production_data, indent=2) if production_data else "Not available"}
        """
        
        response = self.vision_client.chat.completions.create(
            model=self.reasoning_deployment,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Perform root cause analysis:\n{context}"}
            ],
            max_tokens=1500,
            # Note: o3-mini may have different parameters for reasoning_effort
        )
        
        return json.loads(response.choices[0].message.content)
    
    async def _run_reporting_agent(
        self,
        classification: Dict[str, Any],
        rca_result: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Reporting Agent: Generate actionable recommendations.
        """
        system_prompt = f"""
        {self.WIKO_CONTEXT}
        
        REPORTING AGENT ROLE:
        Generate practical corrective and preventive actions.
        
        For Wiko's facilities:
        - Corrective actions should be immediately actionable
        - Preventive actions should reference specific equipment/processes
        - Consider Wiko's vacuum quench technology as a key quality factor
        - Reference CATRA testing for verification steps
        
        Respond in JSON:
        {{
            "corrective_actions": [
                "Immediate action 1",
                "Immediate action 2"
            ],
            "preventive_actions": [
                "Long-term prevention 1",
                "Long-term prevention 2"
            ],
            "quality_check_additions": [
                "New inspection step to add"
            ],
            "training_recommendations": [
                "Operator training need"
            ],
            "escalation_required": true/false,
            "escalation_reason": "why if true"
        }}
        """
        
        context = f"""
        CLASSIFICATION:
        {json.dumps(classification, indent=2)}
        
        ROOT CAUSE ANALYSIS:
        {json.dumps(rca_result, indent=2) if rca_result else "Defect not detected or RCA not performed"}
        """
        
        response = self.vision_client.chat.completions.create(
            model=self.reports_deployment,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Generate recommendations:\n{context}"}
            ],
            max_tokens=800,
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    
    async def analyze_batch(
        self,
        product_sku: str,
        image_paths: Optional[List[str]] = None,
        image_bytes_list: Optional[List[bytes]] = None,
        facility: str = "yangjiang"
    ) -> List[DefectAnalysis]:
        """Analyze multiple images in batch"""
        import asyncio

        if image_bytes_list:
            tasks = [
                self.analyze_defect(product_sku=product_sku, image_bytes=image_bytes, facility=facility)
                for image_bytes in image_bytes_list
            ]
        elif image_paths:
            tasks = [
                self.analyze_defect(product_sku=product_sku, image_path=path, facility=facility)
                for path in image_paths
            ]
        else:
            raise ValueError("Either image_paths or image_bytes_list must be provided.")
        
        return await asyncio.gather(*tasks)
    
    def generate_shift_report(
        self,
        analyses: List[DefectAnalysis]
    ) -> Dict[str, Any]:
        """Generate summary report for a production shift"""
        total = len(analyses)
        defects = [a for a in analyses if a.defect_detected]
        
        # Group by defect type
        by_type = {}
        for d in defects:
            t = d.defect_type.value
            by_type[t] = by_type.get(t, 0) + 1
        
        # Group by severity
        by_severity = {}
        for d in defects:
            s = d.severity.value
            by_severity[s] = by_severity.get(s, 0) + 1
        
        # Group by probable stage
        by_stage = {}
        for d in defects:
            if d.probable_stage:
                s = d.probable_stage.value
                by_stage[s] = by_stage.get(s, 0) + 1
        
        defect_rate = (len(defects) / total * 100) if total > 0 else 0
        
        return {
            "report_timestamp": datetime.now().isoformat(),
            "total_inspected": total,
            "total_defects": len(defects),
            "defect_rate_percent": round(defect_rate, 2),
            "target_rate_percent": 0.18,  # Wiko's target
            "rate_status": "PASS" if defect_rate <= 0.18 else "FAIL",
            "by_defect_type": by_type,
            "by_severity": by_severity,
            "by_production_stage": by_stage,
            "critical_count": by_severity.get("critical", 0),
            "requires_line_stop": by_severity.get("critical", 0) > 0,
            "defect_details": [d.to_dict() for d in defects]
        }


# Convenience function for CLI/testing
async def analyze_single_image(image_path: str, sku: str = "WK-KN-200"):
    """Quick analysis of a single image"""
    analyzer = WikoDefectAnalyzer()
    result = await analyzer.analyze_defect(image_path=image_path, product_sku=sku)
    return result


if __name__ == "__main__":
    import asyncio
    import sys
    
    if len(sys.argv) > 1:
        image = sys.argv[1]
        sku = sys.argv[2] if len(sys.argv) > 2 else "WK-KN-200"
        result = asyncio.run(analyze_single_image(image, sku))
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print("Usage: python defect_analyzer.py <image_path> [product_sku]")
