# Wiko Manufacturing Intelligence Platform

> AI-powered defect detection and root cause analysis for cutlery manufacturing

[![Azure AI Foundry](https://img.shields.io/badge/Azure%20AI-Foundry-blue)](https://ai.azure.com)
[![GPT-4.1](https://img.shields.io/badge/Model-GPT--4.1-green)](https://azure.microsoft.com/en-us/blog/announcing-the-gpt-4-1-model-series-for-azure-ai-foundry-developers/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 Overview

This platform provides real-time defect detection, classification, and root cause analysis for Wiko Cutlery Ltd's manufacturing operations across Hong Kong, Shenzhen, and Yangjiang facilities.

### Key Features

- **Multi-Agent Architecture**: Specialized AI agents for vision analysis, classification, RCA, and reporting
- **GPT-4.1 Vision**: 1M token context window for comprehensive image analysis
- **o3-mini Reasoning**: Deep causal analysis for root cause identification
- **Wiko-Specific Context**: Pre-trained on Wiko's 12-stage production process
- **Real-time API**: REST endpoints for integration with production line cameras
- **Shift Reporting**: Automated quality metrics and trend analysis

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    WIKO MANUFACTURING INTELLIGENCE              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │
│  │   Camera/   │    │   CATRA     │    │  Production │        │
│  │   Scanner   │───▶│   Test Data │───▶│   Logs      │        │
│  └─────────────┘    └─────────────┘    └─────────────┘        │
│         │                 │                   │                │
│         ▼                 ▼                   ▼                │
│  ┌─────────────────────────────────────────────────────┐      │
│  │              DATA INGESTION LAYER                    │      │
│  │   (Azure Event Hub / Blob Storage / SQL)            │      │
│  └─────────────────────────────────────────────────────┘      │
│                           │                                    │
│         ┌─────────────────┼─────────────────┐                 │
│         ▼                 ▼                 ▼                 │
│  ┌───────────┐     ┌───────────┐     ┌───────────┐           │
│  │  VISION   │     │  DEFECT   │     │   RCA     │           │
│  │  AGENT    │────▶│  ANALYZER │────▶│  AGENT    │           │
│  │ (GPT-4.1) │     │  AGENT    │     │ (o3-mini) │           │
│  └───────────┘     └───────────┘     └───────────┘           │
│                           │                                    │
│                           ▼                                    │
│  ┌─────────────────────────────────────────────────────┐      │
│  │              ORCHESTRATION LAYER                     │      │
│  │         (Azure AI Agent Service + Semantic Kernel)   │      │
│  └─────────────────────────────────────────────────────┘      │
│                           │                                    │
│         ┌─────────────────┼─────────────────┐                 │
│         ▼                 ▼                 ▼                 │
│  ┌───────────┐     ┌───────────┐     ┌───────────┐           │
│  │ REPORTING │     │ DASHBOARD │     │   ALERT   │           │
│  │   AGENT   │     │    API    │     │  SERVICE  │           │
│  └───────────┘     └───────────┘     └───────────┘           │
│                                                                │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Azure subscription with AI Foundry access
- Azure CLI installed and authenticated

### 1. Clone and Setup

```bash
git clone https://github.com/wiko-cutlery/defect-analyzer.git
cd wiko-defect-analyzer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Azure AI Foundry Setup

1. **Create Foundry Project**
   ```bash
   # Login to Azure
   az login
   
   # Create resource group
   az group create --name rg-wiko-manufacturing-ai --location eastus2
   ```

2. **Go to Azure AI Foundry Portal**: https://ai.azure.com
   - Create new project: `wiko-defect-analyzer`
   - Resource type: **Foundry resource**
   - Region: **East US 2** (GPT-4.1 + Vision support)

3. **Deploy Models**
   
   | Deployment Name | Model | Purpose |
   |-----------------|-------|---------|
   | `gpt-4-1-vision` | gpt-4.1 | Vision + Classification |
   | `o3-mini-reasoning` | o3-mini | Root Cause Analysis |
   | `gpt-4-1-mini-reports` | gpt-4.1-mini | Report Generation |

### 3. Configure Environment

```bash
# Copy template
cp .env.template .env

# Edit with your values
nano .env
```

Required configuration:
```env
AZURE_AI_PROJECT_ENDPOINT=https://your-project.api.azureml.ms
AZURE_AI_API_KEY=your-api-key-here
AZURE_VISION_DEPLOYMENT=gpt-4-1-vision
AZURE_REASONING_DEPLOYMENT=o3-mini-reasoning
AZURE_REPORTS_DEPLOYMENT=gpt-4-1-mini-reports
```

### 4. Run the API

```bash
cd api
python app.py
```

API will be available at `http://localhost:5000`

### 5. Test Analysis

```bash
# Single image analysis
curl -X POST http://localhost:5000/api/v1/analyze \
  -F "image=@test_image.jpg" \
  -F "product_sku=WK-KN-200" \
  -F "facility=yangjiang"
```

## 📡 API Reference

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/analyze` | Analyze single image |
| POST | `/api/v1/analyze/batch` | Batch analysis |
| POST | `/api/v1/shift-report` | Generate shift report |
| GET | `/api/v1/defect-types` | List defect classifications |
| GET | `/api/v1/production-stages` | List production stages |
| GET | `/api/v1/facilities` | List Wiko facilities |

### Single Image Analysis

**Request:**
```bash
POST /api/v1/analyze
Content-Type: multipart/form-data

image: <file>
product_sku: WK-KN-200
facility: yangjiang
production_data: {"batch_id": "B2024-001", "shift": "morning"}
```

**Response:**
```json
{
  "success": true,
  "analysis": {
    "defect_id": "DEF-20241220-A1B2C3D4",
    "timestamp": "2024-12-20T10:30:00Z",
    "facility": "yangjiang",
    "product_sku": "WK-KN-200",
    "defect_detected": true,
    "defect_type": "edge_irregularity",
    "severity": "minor",
    "confidence": 0.92,
    "description": "Slight waviness detected on cutting edge...",
    "probable_stage": "cutting_edge_honing",
    "root_cause": "Honing wheel wear causing inconsistent pressure",
    "contributing_factors": [
      "Wheel age exceeds 10,000 unit recommendation",
      "Humidity above normal parameters"
    ],
    "corrective_actions": [
      "Replace honing wheel immediately",
      "Re-inspect last 50 units"
    ],
    "preventive_actions": [
      "Implement wheel usage tracking",
      "Add humidity monitoring to QC"
    ]
  }
}
```

## 🔧 Defect Classification

### Defect Types

| Code | Description | Typical Stage |
|------|-------------|---------------|
| `blade_scratch` | Surface scratches | blade_glazing |
| `blade_chip` | Missing edge material | blade_stamp |
| `edge_irregularity` | Uneven cutting edge | cutting_edge_honing |
| `handle_crack` | Handle cracks | handle_injection |
| `handle_discoloration` | Color issues | handle_injection |
| `weld_defect` | Bolster weld issues | bolster_welding |
| `polish_defect` | Finish issues | handle_polishing |
| `rust_spot` | Oxidation (critical) | vacuum_quench |
| `dimensional_error` | Size out of spec | blade_stamp |
| `assembly_misalignment` | Component alignment | rivet_assembly |

### Severity Levels

| Level | Description | Action |
|-------|-------------|--------|
| `critical` | Safety concern | Cannot ship, line stop |
| `major` | Quality issue | Cannot ship |
| `minor` | Cosmetic issue | Can ship with discount |
| `cosmetic` | Within tolerance | Acceptable |

## 🏭 Production Stage Mapping

Wiko's 12-stage production flow:

1. **blade_stamp** - Blade Stamping/Forging
2. **bolster_welding** - Bolster Welding
3. **back_edge_polishing** - Back Edge & Bolster Polishing
4. **taper_grinding** - Taper Grinding (V-shape)
5. **heat_treatment** - Heat Treatment (1000°C)
6. **vacuum_quench** - Vacuum Quench Rapid Cooling (proprietary)
7. **handle_injection** - Handle Injection Molding
8. **rivet_assembly** - Rivet Assembly
9. **handle_polishing** - Handle Polishing
10. **blade_glazing** - Blade Glazing
11. **cutting_edge_honing** - Cutting Edge Honing
12. **logo_print** - Logo Print & Final Inspection

## 📊 Integration Options

### Production Line Camera Integration

```python
import requests
import cv2

# Capture from production line camera
cap = cv2.VideoCapture(0)
ret, frame = cap.read()
cv2.imwrite('capture.jpg', frame)

# Analyze
with open('capture.jpg', 'rb') as f:
    response = requests.post(
        'http://localhost:5000/api/v1/analyze',
        files={'image': f},
        data={'product_sku': 'WK-KN-200', 'facility': 'yangjiang'}
    )
    result = response.json()
    
    if result['analysis']['defect_detected']:
        # Trigger alert
        if result['analysis']['severity'] == 'critical':
            stop_production_line()
```

### Azure Event Hub Integration

```python
from azure.eventhub import EventHubProducerClient, EventData

# Send defect events for real-time dashboard
producer = EventHubProducerClient.from_connection_string(
    conn_str=EVENT_HUB_CONNECTION,
    eventhub_name="wiko-defects"
)

event_data = EventData(json.dumps(analysis_result))
producer.send_batch([event_data])
```

## 🔒 Security

- All API endpoints require authentication (configure in production)
- Images are processed in-memory, not stored
- Azure Managed Identity recommended for production
- Supports VNet integration for on-premises cameras

## 📈 Metrics & Monitoring

Built-in metrics tracking:
- Defect rate per shift
- Defect rate by stage
- Confidence score distribution
- Response time percentiles

Integration with:
- Azure Application Insights
- Power BI dashboards
- Custom alerting

## 🛠️ Development

### Running Tests

```bash
pytest tests/ -v
```

### Adding New Defect Types

1. Add to `DefectType` enum in `agents/defect_analyzer.py`
2. Update classification prompt with new type description
3. Add stage mapping in RCA agent
4. Update API documentation

## 📄 License

MIT License - see LICENSE file

## 🤝 Support

- Technical: anthony.lo@wiko.com.hk
- Project: jonathan.lo@wiko.com.hk

---

Built with ❤️ for Wiko Cutlery Ltd.
Hong Kong | Shenzhen | Yangjiang
