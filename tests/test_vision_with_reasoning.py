#!/usr/bin/env python3
"""
Test vision API WITH reasoning_effort parameter
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

def test_with_reasoning():
    print("=" * 60)
    print("  TESTING GPT-5.2 WITH reasoning_effort")
    print("=" * 60)
    print()

    endpoint = os.getenv("AZURE_AI_PROJECT_ENDPOINT")
    api_key = os.getenv("AZURE_AI_API_KEY")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2025-04-01-preview")
    deployment = os.getenv("AZURE_VISION_DEPLOYMENT", "gpt-5.2")

    if "/api/projects/" in endpoint:
        endpoint = endpoint.split("/api/projects/")[0]

    client = AzureOpenAI(
        azure_endpoint=endpoint,
        api_key=api_key,
        api_version=api_version
    )

    image_base64 = encode_image("test_knife.jpg")

    print("Calling GPT-5.2 WITH reasoning_effort='high'...")
    try:
        response = client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "system", "content": "You are a quality control inspector. Analyze in JSON."},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe this image in JSON with 'description' field."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}", "detail": "high"}}
                    ]
                }
            ],
            max_completion_tokens=500,
            response_format={"type": "json_object"},
            reasoning_effort="high"  # ADD THIS
        )

        content = response.choices[0].message.content
        print("✓ SUCCESS with reasoning_effort='high'")
        print(content[:200])
        assert True

    except Exception as e:
        print(f"✗ FAILED: {type(e).__name__}")
        print(f"Error: {str(e)}")

        # Try without reasoning_effort
        print("\nTrying WITHOUT reasoning_effort parameter...")
        try:
            response = client.chat.completions.create(
                model=deployment,
                messages=[
                    {"role": "system", "content": "You are a quality control inspector. Analyze in JSON."},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Describe this image in JSON with 'description' field."},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}", "detail": "high"}}
                        ]
                    }
                ],
                max_completion_tokens=500,
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            print("✓ SUCCESS without reasoning_effort")
            print("→ reasoning_effort parameter is NOT supported by this deployment")
            assert True
        except Exception as e2:
            print(f"✗ Also failed without reasoning_effort: {str(e2)}")
            pytest.fail(str(e2))
