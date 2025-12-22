"""
Wiko Manufacturing Defect Analyzer Agent - GPT-5.2 Edition
==========================================================
Multi-agent system for defect detection, classification, and root cause analysis
using Azure AI Foundry with GPT-5.2's advanced reasoning capabilities.

Key GPT-5.2 Features Used:
- reasoning_effort: Controls depth of reasoning (none → xhigh)
- verbosity: Controls output detail level
- Preambles: Model explains intent before tool calls
- 272K input / 128K output context window
- Superior multimodal (vision) capabilities
"""

import os
import base64
import json
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
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
    SURFACE_CONTAMINATION = "surface_contamination"
    HEAT_TREATMENT_DEFECT = "heat_treatment_defect"
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


class ReasoningEffort(Enum):
    """GPT-5.2 reasoning effort levels"""
    NONE = "none"        # Fast, minimal thinking
    MINIMAL = "minimal"  # Quick responses
    LOW = "low"          # Light reasoning
    MEDIUM = "medium"    # Balanced (default)
    HIGH = "high"        # Deep reasoning
    XHIGH = "xhigh"      # Maximum reasoning (GPT-5.2 exclusive)


class Verbosity(Enum):
    """GPT-5.2 verbosity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class DefectAnalysis:
    """Result of defect analysis"""
    defect_id: str
    timestamp: datetime
    facility: str
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
    five_why_chain: List[str] = field(default_factory=list)
    contributing_factors: List[str] = field(default_factory=list)
    ishikawa_analysis: Optional[Dict[str, str]] = None
    
    # Recommendations
    corrective_actions: List[str] = field(default_factory=list)
    preventive_actions: List[str] = field(default_factory=list)
    
    # Quality metrics correlation
    catra_correlation: Optional[Dict[str, Any]] = None
    
    # GPT-5.2 reasoning metadata
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


class WikoDefectAnalyzerGPT52:
    """
    Multi-agent defect analyzer for Wiko Cutlery manufacturing.
    Optimized for GPT-5.2's advanced capabilities.
    
    Agents:
    1. Vision Agent (GPT-5.2): Multimodal defect detection with reasoning
    2. Classification Agent (GPT-5.2): Type and severity classification
    3. RCA Agent (GPT-5.2 xhigh): Deep root cause analysis with 5-Why and Ishikawa
    4. Reporting Agent (GPT-5.2-chat): Action recommendations
    """
    
    # Wiko-specific manufacturing context - optimized for GPT-5.2's long context
    WIKO_CONTEXT = """
    <wiko_manufacturing_context>
    You are analyzing defects for Wiko Cutlery Ltd, a 61-year-old premium manufacturer.
    
    COMPANY PROFILE:
    - Founded: 1963 (Wing Kwong Scissors Factory)
    - Operated by: Lo Family (2nd generation, Jonathan Lo leads)
    - Facilities: Hong Kong HQ, Shenzhen R&D, Yangjiang Production (800+ staff, 80,000m²)
    - Capacity: 1M+ units/month
    - Markets: 40+ countries, B2B focus (Williams Sonoma, John Lewis, Zwilling partnership)
    
    12-STAGE MANUFACTURING PROCESS:
    1. BLADE_STAMP: Blade stamping/forging from German 4116/4034 stainless steel
    2. BOLSTER_WELDING: Welding bolster to blade (for forged knives)
    3. BACK_EDGE_POLISHING: Polishing back edge and bolster
    4. TAPER_GRINDING: V-shape taper grinding for cutting edge geometry
    5. HEAT_TREATMENT: Heating to 1000°C for hardening
    6. VACUUM_QUENCH: **PROPRIETARY** Rapid cooling 1000°C→600°C in 2 minutes
       - Uses liquid nitrogen or quenching oil in vacuum chamber
       - Prevents chromium carbide formation
       - Maintains chromium levels for rust resistance
       - Key differentiator vs competitors who use slow cooling
    7. HANDLE_INJECTION: Injection molding of handles (various materials)
    8. RIVET_ASSEMBLY: Attaching handle to tang with rivets
    9. HANDLE_POLISHING: Final handle finish
    10. BLADE_GLAZING: Mirror/satin finish on blade
    11. CUTTING_EDGE_HONING: Final edge sharpening
    12. LOGO_PRINT: Laser/print branding + final inspection
    
    QUALITY STANDARDS:
    - CATRA sharpness: Target >50 ICP (Initial Cutting Performance)
    - CATRA angle testing: ±2° tolerance
    - Salt spray: 1000 hours corrosion resistance
    - Hardness: 54-58 HRC for blades
    - Defect rate target: 0.18%
    
    CERTIFICATIONS:
    - ISO 9001:2015 (Quality Management)
    - SMETA (Labor Standards, Health & Safety)
    - NSF Food Contact & Function
    - LFGB Food Contact (German standard)
    
    DEFECT-TO-STAGE CORRELATION PATTERNS:
    - Rust spots → Likely VACUUM_QUENCH failure (slow cooling caused chromium carbide)
    - Edge irregularity → TAPER_GRINDING or CUTTING_EDGE_HONING
    - Blade scratches → BLADE_GLAZING or cross-contamination from polishing
    - Handle cracks → HANDLE_INJECTION parameters (temp, pressure, cooling rate)
    - Weld defects → BOLSTER_WELDING (temperature, duration, alignment)
    - Polish defects → Wheel wear, pressure inconsistency
    - Heat treatment defects → Temperature profile deviation, soak time
    - Dimensional errors → BLADE_STAMP tooling wear
    
    SUSTAINABILITY CONTEXT (relevant for reporting):
    - 85% recycled steel content in cast iron products
    - Carbon neutral target: 2026
    - FSC-certified beechwood handles
    - LCA (Life Cycle Assessment) tracking
    </wiko_manufacturing_context>
    """
    
    def __init__(self):
        """Initialize Azure AI client with GPT-5.2 configuration"""
        self.project_endpoint = os.getenv("AZURE_AI_PROJECT_ENDPOINT")
        self.api_key = os.getenv("AZURE_AI_API_KEY")
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2025-04-01-preview")
        
        # Model deployments
        self.vision_deployment = os.getenv("AZURE_VISION_DEPLOYMENT", "gpt-5-2")
        self.reasoning_deployment = os.getenv("AZURE_REASONING_DEPLOYMENT", "gpt-5-2")
        self.reports_deployment = os.getenv("AZURE_REPORTS_DEPLOYMENT", "gpt-5-2-chat")
        
        # Reasoning configuration
        self.default_reasoning_effort = os.getenv("DEFAULT_REASONING_EFFORT", "high")
        self.rca_reasoning_effort = os.getenv("RCA_REASONING_EFFORT", "xhigh")
        self.default_verbosity = os.getenv("DEFAULT_VERBOSITY", "medium")
        
        # Initialize client
        self.client = AzureOpenAI(
            azure_endpoint=self._get_openai_endpoint(),
            api_key=self.api_key,
            api_version=self.api_version
        )
    
    def _get_openai_endpoint(self) -> str:
        """Convert project endpoint to OpenAI endpoint format"""
        base = self.project_endpoint
        if "/api/projects/" in base:
            base = base.split("/api/projects/")[0]
        return base
    
    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64 for API submission"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    
    def _get_image_media_type(self, image_path: str) -> str:
        """Determine image media type from extension"""
        ext = image_path.lower().split('.')[-1]
        media_types = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'webp': 'image/webp',
            'gif': 'image/gif'
        }
        return media_types.get(ext, 'image/jpeg')
    
    async def analyze_defect(
        self,
        image_path: str,
        product_sku: str,
        facility: str = "yangjiang",
        production_data: Optional[Dict[str, Any]] = None
    ) -> DefectAnalysis:
        """
        Main entry point: Orchestrates multi-agent defect analysis with GPT-5.2.
        
        Uses GPT-5.2's capabilities:
        - High reasoning effort for vision analysis
        - xhigh reasoning effort for RCA (deep causal analysis)
        - Preambles for transparent tool usage
        
        Args:
            image_path: Path to product image
            product_sku: Product SKU being inspected
            facility: Manufacturing facility
            production_data: Optional batch/process data for correlation
            
        Returns:
            DefectAnalysis with complete analysis and recommendations
        """
        import uuid
        
        defect_id = f"DEF-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
        total_reasoning_tokens = 0
        
        # Step 1: Vision + Classification Agent (combined for efficiency)
        # GPT-5.2 handles multimodal + reasoning in single pass
        vision_classification = await self._run_vision_classification_agent(
            image_path, 
            product_sku,
            reasoning_effort="high"
        )
        total_reasoning_tokens += vision_classification.get("_reasoning_tokens", 0)
        
        # Step 2: RCA Agent with xhigh reasoning (if defect detected)
        rca_result = None
        if vision_classification.get("defect_detected"):
            rca_result = await self._run_rca_agent(
                vision_classification,
                production_data,
                reasoning_effort="medium"  # Balanced reasoning (faster than xhigh)
            )
            total_reasoning_tokens += rca_result.get("_reasoning_tokens", 0)
        
        # Step 3: Reporting Agent - Generate actionable recommendations
        recommendations = await self._run_reporting_agent(
            vision_classification,
            rca_result
        )
        
        # Helper to parse production stage (handles both uppercase and lowercase)
        probable_stage = None
        if rca_result and rca_result.get("probable_stage"):
            stage_value = rca_result["probable_stage"].lower()
            try:
                probable_stage = ProductionStage(stage_value)
            except ValueError:
                # If still invalid, try to find by name
                try:
                    probable_stage = ProductionStage[rca_result["probable_stage"].upper()]
                except KeyError:
                    probable_stage = None

        # Compile final analysis
        return DefectAnalysis(
            defect_id=defect_id,
            timestamp=datetime.now(),
            facility=facility,
            product_sku=product_sku,
            image_url=image_path,
            defect_detected=vision_classification.get("defect_detected", False),
            defect_type=DefectType(vision_classification.get("defect_type", "unknown").lower()),
            severity=Severity(vision_classification.get("severity", "cosmetic").lower()),
            confidence=vision_classification.get("confidence", 0.0),
            description=vision_classification.get("description", ""),
            affected_area=vision_classification.get("affected_area", ""),
            bounding_box=vision_classification.get("bounding_box"),
            probable_stage=probable_stage,
            root_cause=rca_result.get("root_cause", "") if rca_result else "",
            five_why_chain=rca_result.get("five_why_chain", []) if rca_result else [],
            contributing_factors=rca_result.get("contributing_factors", []) if rca_result else [],
            ishikawa_analysis=rca_result.get("ishikawa_analysis") if rca_result else None,
            corrective_actions=recommendations.get("corrective_actions", []),
            preventive_actions=recommendations.get("preventive_actions", []),
            reasoning_tokens_used=total_reasoning_tokens,
            model_version="gpt-5.2"
        )
    
    async def _run_vision_classification_agent(
        self,
        image_path: str,
        product_sku: str,
        reasoning_effort: str = "high"
    ) -> Dict[str, Any]:
        """
        Combined Vision + Classification Agent using GPT-5.2's multimodal capabilities.
        
        GPT-5.2 optimizations:
        - Single pass for detection + classification (reduced latency)
        - reasoning_effort='high' for accurate defect analysis
        - Structured JSON output with bounding boxes
        """
        image_base64 = self._encode_image(image_path)
        media_type = self._get_image_media_type(image_path)
        
        system_prompt = f"""
        {self.WIKO_CONTEXT}
        
        <agent_role>
        You are a VISION + CLASSIFICATION agent for Wiko quality control.
        
        TASK: Analyze the product image and provide:
        1. Defect detection (present/absent)
        2. Defect type classification
        3. Severity assessment
        4. Location identification
        
        Before analyzing, explain your inspection approach briefly (preamble).
        </agent_role>
        
        <defect_types>
        - blade_scratch: Surface scratches on blade body
        - blade_chip: Missing material from blade edge (CRITICAL if >1mm)
        - edge_irregularity: Uneven, wavy, or serrated edge where smooth expected
        - handle_crack: Visible cracks in handle material
        - handle_discoloration: Color inconsistency, staining, or fading
        - weld_defect: Visible weld line issues, gaps, or discoloration at bolster
        - polish_defect: Uneven finish, swirl marks, orange peel texture
        - rust_spot: Orange/brown oxidation marks (CRITICAL - indicates process failure)
        - dimensional_error: Visible size/shape deviation
        - assembly_misalignment: Handle-blade alignment issues, uneven rivets
        - surface_contamination: Foreign material, oil stains, fingerprints
        - heat_treatment_defect: Discoloration bands, soft spots visible
        - unknown: Cannot classify confidently
        </defect_types>
        
        <severity_guide>
        - critical: Safety concern OR indicates major process failure (rust, chips >1mm, cracks)
        - major: Quality issue, cannot ship (visible defects, functional impact)
        - minor: Can ship with discount (small cosmetic issues <2mm)
        - cosmetic: Within acceptable tolerance (minimal visual impact)
        </severity_guide>
        
        <output_format>
        Respond ONLY with valid JSON:
        {{
            "inspection_preamble": "Brief explanation of your inspection approach",
            "defect_detected": true/false,
            "defect_type": "type_from_list",
            "severity": "critical/major/minor/cosmetic",
            "confidence": 0.0-1.0,
            "description": "Detailed description of finding",
            "affected_area": "blade/edge/handle/bolster/rivet/overall",
            "bounding_box": {{"x": int, "y": int, "width": int, "height": int}} or null,
            "visual_evidence": ["list", "of", "specific", "observations"],
            "quality_impact": "How this affects product function/appearance",
            "classification_reasoning": "Why you chose this type and severity"
        }}
        </output_format>
        """
        
        response = self.client.chat.completions.create(
            model=self.vision_deployment,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Inspect this {product_sku} product for manufacturing defects. Provide comprehensive analysis."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{media_type};base64,{image_base64}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            max_completion_tokens=2000,
            response_format={"type": "json_object"},
            # GPT-5.2 specific parameters
            reasoning_effort=reasoning_effort
            # verbosity parameter may not be supported by all deployments
        )

        # Extract content - GPT-5.2 may have different response structure
        content = response.choices[0].message.content

        # Debug logging
        if not content or content.strip() == "":
            raise ValueError(f"GPT-5.2 returned empty response. Full response: {response}")

        try:
            result = json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"GPT-5.2 returned invalid JSON. Content: {content[:500]}... Error: {str(e)}")

        # Track reasoning tokens if available
        if hasattr(response, 'usage') and hasattr(response.usage, 'completion_tokens_details'):
            result["_reasoning_tokens"] = getattr(
                response.usage.completion_tokens_details,
                'reasoning_tokens',
                0
            )

        return result
    
    async def _run_rca_agent(
        self,
        vision_classification: Dict[str, Any],
        production_data: Optional[Dict[str, Any]] = None,
        reasoning_effort: str = "xhigh"
    ) -> Dict[str, Any]:
        """
        Root Cause Analysis Agent using GPT-5.2's maximum reasoning (xhigh).
        
        GPT-5.2 optimizations:
        - xhigh reasoning_effort for deep causal chain analysis
        - 5-Why methodology
        - Ishikawa (fishbone) diagram categories
        - Production data correlation
        """
        system_prompt = f"""
        {self.WIKO_CONTEXT}
        
        <agent_role>
        You are a ROOT CAUSE ANALYSIS expert for Wiko manufacturing.
        Use MAXIMUM reasoning depth to trace defects to their source.
        
        Before your analysis, briefly explain your RCA approach (preamble).
        </agent_role>
        
        <methodology>
        1. DEFECT-TO-STAGE MAPPING:
           Map the defect type to most likely production stage(s) using Wiko's 12-stage process.
        
        2. 5-WHY ANALYSIS:
           Drill down 5 levels of "why" to find root cause.
           Example for rust spot:
           - Why rust? → Chromium depleted in surface layer
           - Why depleted? → Chromium carbide formed during cooling
           - Why carbide? → Slow cooling allowed carbon-chromium reaction
           - Why slow cooling? → Vacuum chamber pressure loss
           - Why pressure loss? → Seal degradation (ROOT CAUSE)
        
        3. ISHIKAWA (FISHBONE) ANALYSIS:
           Analyze contributing factors across 6 categories:
           - Machine: Equipment condition, calibration, wear
           - Material: Steel grade, handle material, consumables
           - Method: Process parameters, procedures, sequence
           - Man: Operator skill, training, fatigue
           - Measurement: Inspection gaps, instrument calibration
           - Environment: Temperature, humidity, contamination
        
        4. PRODUCTION DATA CORRELATION:
           If provided, correlate with batch/shift/equipment data.
        </methodology>
        
        <output_format>
        Respond ONLY with valid JSON:
        {{
            "rca_preamble": "Brief explanation of your analysis approach",
            "probable_stage": "production_stage_enum_value",
            "stage_confidence": 0.0-1.0,
            "root_cause": "Clear root cause statement",
            "five_why_chain": [
                "Why 1: [observation] → [cause]",
                "Why 2: [cause] → [deeper cause]",
                "Why 3: ...",
                "Why 4: ...",
                "Why 5: [root cause]"
            ],
            "contributing_factors": ["factor1", "factor2", "factor3"],
            "ishikawa_analysis": {{
                "machine": "Equipment-related factors",
                "material": "Material-related factors", 
                "method": "Process-related factors",
                "man": "Human-related factors",
                "measurement": "Measurement-related factors",
                "environment": "Environmental factors"
            }},
            "production_correlation": "Correlation with provided production data or 'No data provided'",
            "confidence_explanation": "Why you're confident in this analysis"
        }}
        </output_format>
        """
        
        user_content = f"""
        DEFECT ANALYSIS TO INVESTIGATE:
        {json.dumps(vision_classification, indent=2)}
        
        PRODUCTION DATA:
        {json.dumps(production_data, indent=2) if production_data else "Not provided - base analysis on defect type patterns only"}
        
        Perform comprehensive root cause analysis using 5-Why and Ishikawa methodology.
        """
        
        response = self.client.chat.completions.create(
            model=self.reasoning_deployment,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            max_completion_tokens=3000,
            response_format={"type": "json_object"},
            # GPT-5.2 xhigh reasoning for deep analysis
            reasoning_effort=reasoning_effort
            # verbosity parameter may not be supported
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Track reasoning tokens
        if hasattr(response, 'usage') and hasattr(response.usage, 'completion_tokens_details'):
            result["_reasoning_tokens"] = getattr(
                response.usage.completion_tokens_details,
                'reasoning_tokens',
                0
            )
        
        return result
    
    async def _run_reporting_agent(
        self,
        vision_classification: Dict[str, Any],
        rca_result: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Reporting Agent: Generate actionable recommendations.
        Uses GPT-5.2-chat for natural, clear communication.
        """
        system_prompt = f"""
        {self.WIKO_CONTEXT}
        
        <agent_role>
        You are a QUALITY IMPROVEMENT specialist generating actionable recommendations.
        
        Your recommendations must be:
        - Specific to Wiko's equipment and processes
        - Immediately actionable (corrective) or plannable (preventive)
        - Measurable where possible
        - Prioritized by impact
        </agent_role>
        
        <output_format>
        Respond ONLY with valid JSON:
        {{
            "corrective_actions": [
                "IMMEDIATE: [specific action with responsible party]",
                "IMMEDIATE: [second action]"
            ],
            "preventive_actions": [
                "LONG-TERM: [specific prevention measure]",
                "LONG-TERM: [second measure]"
            ],
            "quality_check_additions": [
                "New inspection step to implement"
            ],
            "training_recommendations": [
                "Operator training need"
            ],
            "equipment_actions": [
                "Maintenance or calibration need"
            ],
            "escalation_required": true/false,
            "escalation_reason": "Why escalation needed (if true)",
            "estimated_resolution_time": "Time estimate for correction",
            "recurrence_prevention_score": 0-100
        }}
        </output_format>
        """
        
        context = f"""
        DEFECT CLASSIFICATION:
        {json.dumps(vision_classification, indent=2)}
        
        ROOT CAUSE ANALYSIS:
        {json.dumps(rca_result, indent=2) if rca_result else "No defect detected - provide general quality recommendations"}
        
        Generate specific, actionable recommendations for Wiko's Yangjiang facility.
        """
        
        response = self.client.chat.completions.create(
            model=self.reports_deployment,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": context}
            ],
            max_completion_tokens=1500,
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    
    async def analyze_batch(
        self,
        image_paths: List[str],
        product_sku: str,
        facility: str = "yangjiang"
    ) -> List[DefectAnalysis]:
        """Analyze multiple images in batch"""
        import asyncio
        
        tasks = [
            self.analyze_defect(path, product_sku, facility)
            for path in image_paths
        ]
        
        return await asyncio.gather(*tasks)
    
    def generate_shift_report(
        self,
        analyses: List[DefectAnalysis]
    ) -> Dict[str, Any]:
        """Generate comprehensive shift summary report"""
        total = len(analyses)
        defects = [a for a in analyses if a.defect_detected]
        
        # Group by various dimensions
        by_type = {}
        by_severity = {}
        by_stage = {}
        
        for d in defects:
            # By type
            t = d.defect_type.value
            by_type[t] = by_type.get(t, 0) + 1
            
            # By severity
            s = d.severity.value
            by_severity[s] = by_severity.get(s, 0) + 1
            
            # By stage
            if d.probable_stage:
                stage = d.probable_stage.value
                by_stage[stage] = by_stage.get(stage, 0) + 1
        
        defect_rate = (len(defects) / total * 100) if total > 0 else 0
        
        # Aggregate root causes
        root_causes = [d.root_cause for d in defects if d.root_cause]
        
        return {
            "report_timestamp": datetime.now().isoformat(),
            "report_type": "shift_summary",
            "model_version": "gpt-5.2",
            
            # Summary metrics
            "total_inspected": total,
            "total_defects": len(defects),
            "defect_rate_percent": round(defect_rate, 3),
            "target_rate_percent": 0.18,
            "rate_status": "PASS" if defect_rate <= 0.18 else "FAIL",
            "rate_variance": round(defect_rate - 0.18, 3),
            
            # Breakdowns
            "by_defect_type": by_type,
            "by_severity": by_severity,
            "by_production_stage": by_stage,
            
            # Critical metrics
            "critical_count": by_severity.get("critical", 0),
            "major_count": by_severity.get("major", 0),
            "requires_line_stop": by_severity.get("critical", 0) > 0,
            
            # Root cause summary
            "unique_root_causes": list(set(root_causes)),
            "top_problematic_stage": max(by_stage, key=by_stage.get) if by_stage else None,
            
            # Reasoning efficiency
            "total_reasoning_tokens": sum(a.reasoning_tokens_used for a in analyses),
            "avg_reasoning_tokens_per_analysis": round(
                sum(a.reasoning_tokens_used for a in analyses) / total, 0
            ) if total > 0 else 0,
            
            # Detailed records
            "defect_details": [d.to_dict() for d in defects]
        }


# Factory function for easy instantiation
def create_analyzer() -> WikoDefectAnalyzerGPT52:
    """Create a configured GPT-5.2 defect analyzer instance"""
    return WikoDefectAnalyzerGPT52()


# CLI entry point
async def analyze_single_image(image_path: str, sku: str = "WK-KN-200"):
    """Quick analysis of a single image"""
    analyzer = create_analyzer()
    result = await analyzer.analyze_defect(image_path, sku)
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
        print("""
╔═══════════════════════════════════════════════════════════╗
║     WIKO DEFECT ANALYZER - GPT-5.2 EDITION                ║
╠═══════════════════════════════════════════════════════════╣
║  Usage: python defect_analyzer_gpt52.py <image> [sku]     ║
║                                                           ║
║  Features:                                                ║
║  • GPT-5.2 multimodal vision analysis                     ║
║  • xhigh reasoning for root cause analysis                ║
║  • 5-Why + Ishikawa methodology                           ║
║  • 272K context window                                    ║
║                                                           ║
║  Environment Variables:                                   ║
║  • AZURE_AI_PROJECT_ENDPOINT                              ║
║  • AZURE_AI_API_KEY                                       ║
║  • AZURE_VISION_DEPLOYMENT (default: gpt-5-2)            ║
╚═══════════════════════════════════════════════════════════╝
        """)
