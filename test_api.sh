#!/bin/bash
# Comprehensive API Testing Script for Wiko Defect Analyzer

echo "═══════════════════════════════════════════════════════════"
echo "  WIKO DEFECT ANALYZER - API TEST SUITE"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Health Check
echo "Test 1: Health Check"
echo "------------------------------------------------------------"
HEALTH=$(curl -s http://localhost:5001/health)
if echo "$HEALTH" | grep -q "healthy"; then
    echo -e "${GREEN}✓ PASSED${NC} - API is healthy"
    echo "$HEALTH" | python3 -m json.tool
else
    echo -e "${RED}✗ FAILED${NC} - API is not responding"
    exit 1
fi
echo ""

# Test 2: Defect Types Endpoint
echo "Test 2: Get Defect Types"
echo "------------------------------------------------------------"
TYPES=$(curl -s http://localhost:5001/api/v1/defect-types)
if echo "$TYPES" | grep -q "blade_scratch"; then
    echo -e "${GREEN}✓ PASSED${NC} - Defect types retrieved"
    echo "Sample types:" $(echo "$TYPES" | python3 -m json.tool | head -20)
else
    echo -e "${RED}✗ FAILED${NC} - Could not get defect types"
fi
echo ""

# Test 3: Production Stages Endpoint
echo "Test 3: Get Production Stages"
echo "------------------------------------------------------------"
STAGES=$(curl -s http://localhost:5001/api/v1/production-stages)
if echo "$STAGES" | grep -q "blade_stamp"; then
    echo -e "${GREEN}✓ PASSED${NC} - Production stages retrieved"
else
    echo -e "${RED}✗ FAILED${NC} - Could not get production stages"
fi
echo ""

# Test 4: Analyze Image (Main Test)
echo "Test 4: Analyze Image with GPT-5.2"
echo "------------------------------------------------------------"
echo -e "${YELLOW}Uploading test_knife.jpg...${NC}"
echo ""

RESULT=$(curl -s -X POST http://localhost:5001/api/v1/analyze \
  -F "image=@test_knife.jpg" \
  -F "product_sku=WK-KN-200" \
  -F "facility=yangjiang" \
  2>&1)

if echo "$RESULT" | grep -q '"success":true'; then
    echo -e "${GREEN}✓ PASSED${NC} - Image analysis completed successfully!"
    echo ""
    echo "Analysis Result:"
    echo "$RESULT" | python3 -m json.tool
    echo ""

    # Extract key information
    DEFECT_DETECTED=$(echo "$RESULT" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['analysis']['defect_detected'])" 2>/dev/null)
    DEFECT_TYPE=$(echo "$RESULT" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['analysis'].get('defect_type', 'N/A'))" 2>/dev/null)
    CONFIDENCE=$(echo "$RESULT" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['analysis'].get('confidence', 'N/A'))" 2>/dev/null)

    echo "Summary:"
    echo "  • Defect Detected: $DEFECT_DETECTED"
    echo "  • Defect Type: $DEFECT_TYPE"
    echo "  • Confidence: $CONFIDENCE"

elif echo "$RESULT" | grep -q '"success":false'; then
    echo -e "${RED}✗ FAILED${NC} - Analysis returned error"
    echo "Error:"
    echo "$RESULT" | python3 -m json.tool
    ERROR_MSG=$(echo "$RESULT" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('error', 'Unknown error'))" 2>/dev/null)
    echo ""
    echo -e "${YELLOW}Error Message:${NC} $ERROR_MSG"
else
    echo -e "${RED}✗ FAILED${NC} - Unexpected response"
    echo "$RESULT"
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  Test Suite Complete"
echo "═══════════════════════════════════════════════════════════"
