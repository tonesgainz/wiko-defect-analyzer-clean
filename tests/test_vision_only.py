#!/usr/bin/env python3
"""
Test just the vision API call without full analysis
"""

import os
import json
import base64
import pytest
from dotenv import load_dotenv
from openai import AzureOpenAI

pytestmark = [
    pytest.mark.manual,
    pytest.mark.skipif(
        os.getenv("RUN_VISION_MANUAL") != "1",
        reason="Requires local test_knife.jpg and live Azure creds",
    ),
]

load_dotenv()

def encode_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def test_vision_api():
    print("=" * 60)
    print("  TESTING GPT-5.2 VISION API (Simplified)")
    print("=" * 60)
    print()

    endpoint = os.getenv("AZURE_AI_PROJECT_ENDPOINT")
    api_key = os.getenv("AZURE_AI_API_KEY")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2025-04-01-preview")
    deployment = os.getenv("AZURE_VISION_DEPLOYMENT", "gpt-5.2")

    if "/api/projects/" in endpoint:
        endpoint = endpoint.split("/api/projects/")[0]

    print(f"Deployment: {deployment}")
    print(f"API Version: {api_version}")
    print()

    client = AzureOpenAI(
        azure_endpoint=endpoint,
        api_key=api_key,
        api_version=api_version
    )

    print("Encoding image...")
    image_base64 = encode_image("test_knife.jpg")
    print(f"Image encoded: {len(image_base64)} bytes")
    print()

    print("Calling GPT-5.2 vision API (NO reasoning_effort)...")
    try:
        response = client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "system", "content": "You are a quality control inspector. Analyze the image and respond in JSON."},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe what you see in this image. Respond in JSON with 'description' field."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}", "detail": "high"}}
                    ]
                }
            ],
            max_completion_tokens=500,
            response_format={"type": "json_object"}
            # NO reasoning_effort or verbosity
        )

        content = response.choices[0].message.content
        print("✓ SUCCESS - Got response:")
        print(content)
        print()

        result = json.loads(content)
        print("Parsed JSON:")
        print(json.dumps(result, indent=2))
        assert True

    except Exception as e:
        print(f"✗ FAILED: {type(e).__name__}")
        print(f"Error: {str(e)}")
        pytest.fail(str(e))

if __name__ == "__main__":
    import sys
    success = test_vision_api()
    sys.exit(0 if success else 1)
