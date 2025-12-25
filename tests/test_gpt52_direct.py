#!/usr/bin/env python3
"""
Direct GPT-5.2 API Test
Tests the Azure OpenAI connection and GPT-5.2 deployment directly
"""

import os
import sys
import pytest
from dotenv import load_dotenv
from openai import AzureOpenAI

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("RUN_AZURE_INTEGRATION") != "1",
        reason="Set RUN_AZURE_INTEGRATION=1 to run live Azure OpenAI integration tests",
    ),
]

load_dotenv()

def test_azure_connection():
    """Test basic Azure OpenAI connection"""
    print("=" * 60)
    print("  TESTING AZURE OPENAI GPT-5.2 CONNECTION")
    print("=" * 60)
    print()

    # Get credentials
    endpoint = os.getenv("AZURE_AI_PROJECT_ENDPOINT")
    api_key = os.getenv("AZURE_AI_API_KEY")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2025-04-01-preview")
    deployment = os.getenv("AZURE_VISION_DEPLOYMENT", "gpt-5.2")

    print("Configuration:")
    print(f"  • Endpoint: {endpoint[:50]}...")
    print(f"  • API Key: {api_key[:10]}...{api_key[-10:]}")
    print(f"  • API Version: {api_version}")
    print(f"  • Deployment: {deployment}")
    print()

    # Clean endpoint if needed
    if "/api/projects/" in endpoint:
        endpoint = endpoint.split("/api/projects/")[0]
        print(f"  • Cleaned Endpoint: {endpoint}")
        print()

    try:
        # Initialize client
        print("Initializing Azure OpenAI client...")
        client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=api_version
        )
        print("✓ Client initialized")
        print()

        # Test simple completion
        print("Testing GPT-5.2 with simple prompt...")
        response = client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello, GPT-5.2 is working!' in JSON format with a 'message' field."}
            ],
            max_completion_tokens=100,
            response_format={"type": "json_object"}
        )

        result = response.choices[0].message.content
        print("✓ GPT-5.2 Response:")
        print(result)
        print()

        print("=" * 60)
        print("  ✓ SUCCESS - GPT-5.2 is working correctly!")
        print("=" * 60)
        assert True

    except Exception as e:
        print()
        print("=" * 60)
        print("  ✗ FAILED - Error connecting to GPT-5.2")
        print("=" * 60)
        print(f"\nError Type: {type(e).__name__}")
        print(f"Error Message: {str(e)}")
        print()

        # Provide troubleshooting hints
        if "404" in str(e):
            print("Troubleshooting:")
            print("  • Check if deployment name 'gpt-5.2' exists in your Azure AI Foundry")
            print("  • Verify the endpoint URL is correct")
        elif "401" in str(e) or "403" in str(e):
            print("Troubleshooting:")
            print("  • Check if API key is correct")
            print("  • Verify API key has not expired")
        elif "DeploymentNotFound" in str(e):
            print("Troubleshooting:")
            print("  • The deployment 'gpt-5.2' was not found")
            print("  • Check Azure AI Foundry for available deployments")
            print("  • Update AZURE_VISION_DEPLOYMENT in .env file")

        assert False

if __name__ == "__main__":
    success = test_azure_connection()
    sys.exit(0 if success else 1)
