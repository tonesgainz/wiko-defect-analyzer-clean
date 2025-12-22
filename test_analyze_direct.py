#!/usr/bin/env python3
"""
Direct test of analyze_defect function
"""

import asyncio
import sys
from agents.defect_analyzer_gpt52 import WikoDefectAnalyzerGPT52

async def test_analyze():
    print("=" * 60)
    print("  TESTING DIRECT ANALYZE_DEFECT CALL")
    print("=" * 60)
    print()

    analyzer = WikoDefectAnalyzerGPT52()

    print("Analyzing test_knife.jpg...")
    print()

    try:
        result = await analyzer.analyze_defect(
            image_path="test_knife.jpg",
            product_sku="WK-KN-200",
            facility="yangjiang"
        )

        print("✓ SUCCESS!")
        print()
        print("Result:")
        print(f"  • Defect ID: {result.defect_id}")
        print(f"  • Defect Detected: {result.defect_detected}")
        print(f"  • Defect Type: {result.defect_type.value}")
        print(f"  • Severity: {result.severity.value}")
        print(f"  • Confidence: {result.confidence}")
        print(f"  • Description: {result.description[:100]}...")
        print()
        print("Full JSON:")
        import json
        print(json.dumps(result.to_dict(), indent=2))

    except Exception as e:
        print(f"✗ FAILED: {type(e).__name__}")
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    success = asyncio.run(test_analyze())
    sys.exit(0 if success else 1)
