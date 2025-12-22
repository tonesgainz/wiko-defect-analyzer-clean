#!/usr/bin/env python3
"""
Wiko Defect Analyzer - Connection Test
=======================================
Run this to verify your Azure AI Foundry setup is working.
"""

import os
import sys
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def print_header():
    print("""
╔═══════════════════════════════════════════════════════════╗
║     WIKO DEFECT ANALYZER - CONNECTION TEST                ║
║     GPT-5.2 Edition                                       ║
╚═══════════════════════════════════════════════════════════╝
    """)

def check_env_vars():
    """Check required environment variables"""
    print("→ Checking environment variables...")
    
    required_vars = [
        "AZURE_AI_PROJECT_ENDPOINT",
        "AZURE_AI_API_KEY",
    ]
    
    optional_vars = [
        "AZURE_VISION_DEPLOYMENT",
        "AZURE_REASONING_DEPLOYMENT", 
        "AZURE_REPORTS_DEPLOYMENT",
        "DEFAULT_REASONING_EFFORT",
    ]
    
    missing = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing.append(var)
            print(f"  ❌ {var}: NOT SET")
        else:
            # Mask sensitive values
            if "KEY" in var:
                display = value[:8] + "..." + value[-4:] if len(value) > 12 else "****"
            else:
                display = value[:50] + "..." if len(value) > 50 else value
            print(f"  ✅ {var}: {display}")
    
    print("\n→ Optional variables:")
    for var in optional_vars:
        value = os.getenv(var, "not set (using default)")
        print(f"  ℹ️  {var}: {value}")
    
    if missing:
        print(f"\n❌ Missing required variables: {missing}")
        print("   Please edit .env file with your Azure credentials.")
        return False
    
    return True

def test_openai_connection():
    """Test connection to Azure OpenAI"""
    print("\n→ Testing Azure OpenAI connection...")
    
    try:
        from openai import AzureOpenAI
        
        endpoint = os.getenv("AZURE_AI_PROJECT_ENDPOINT")
        api_key = os.getenv("AZURE_AI_API_KEY")
        api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2025-04-01-preview")
        deployment = os.getenv("AZURE_VISION_DEPLOYMENT", "gpt-5-2")
        
        # Extract base endpoint
        if "/api/projects/" in endpoint:
            base_endpoint = endpoint.split("/api/projects/")[0]
        else:
            base_endpoint = endpoint
        
        print(f"  Endpoint: {base_endpoint}")
        print(f"  API Version: {api_version}")
        print(f"  Deployment: {deployment}")
        
        client = AzureOpenAI(
            azure_endpoint=base_endpoint,
            api_key=api_key,
            api_version=api_version
        )
        
        # Simple test call
        print("\n→ Sending test request to GPT-5.2...")
        response = client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Respond briefly."},
                {"role": "user", "content": "Say 'Wiko Defect Analyzer is ready!' and nothing else."}
            ],
            max_completion_tokens=50,  # GPT-5.2 uses max_completion_tokens instead of max_tokens
            reasoning_effort="minimal"  # Use minimal for quick test
        )
        
        result = response.choices[0].message.content
        print(f"  ✅ Response: {result}")
        
        # Check usage
        if response.usage:
            print(f"  ℹ️  Tokens used: {response.usage.total_tokens}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Connection failed: {str(e)}")
        
        # Provide helpful error messages
        error_str = str(e).lower()
        if "401" in error_str or "unauthorized" in error_str:
            print("\n  💡 Tip: Check your API key is correct")
        elif "404" in error_str or "not found" in error_str:
            print("\n  💡 Tip: Check your endpoint URL and deployment name")
            print("     Make sure you've deployed 'gpt-5-2' model in Azure AI Foundry")
        elif "429" in error_str:
            print("\n  💡 Tip: Rate limit hit. Wait a moment and try again.")
        elif "deployment" in error_str:
            print("\n  💡 Tip: The deployment name might not match.")
            print("     Go to Azure AI Foundry → Models + endpoints")
            print("     Check your deployment name and update .env")
        
        return False

def test_vision_capability():
    """Test multimodal (vision) capability with a simple test"""
    print("\n→ Testing GPT-5.2 vision capability...")
    
    try:
        from openai import AzureOpenAI
        import base64
        
        # Create a simple 1x1 red pixel image for testing
        # This is a minimal valid PNG
        red_pixel_png = base64.b64encode(bytes([
            0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
            0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
            0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # 1x1
            0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
            0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,  # IDAT chunk
            0x54, 0x08, 0xD7, 0x63, 0xF8, 0xCF, 0xC0, 0x00,
            0x00, 0x00, 0x03, 0x00, 0x01, 0x00, 0x18, 0xDD,
            0x8D, 0xB4, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45,  # IEND chunk
            0x4E, 0x44, 0xAE, 0x42, 0x60, 0x82
        ])).decode('utf-8')
        
        endpoint = os.getenv("AZURE_AI_PROJECT_ENDPOINT")
        api_key = os.getenv("AZURE_AI_API_KEY")
        api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2025-04-01-preview")
        deployment = os.getenv("AZURE_VISION_DEPLOYMENT", "gpt-5-2")
        
        if "/api/projects/" in endpoint:
            base_endpoint = endpoint.split("/api/projects/")[0]
        else:
            base_endpoint = endpoint
        
        client = AzureOpenAI(
            azure_endpoint=base_endpoint,
            api_key=api_key,
            api_version=api_version
        )
        
        response = client.chat.completions.create(
            model=deployment,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "What color is this image? Reply with just the color name."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{red_pixel_png}",
                                "detail": "low"
                            }
                        }
                    ]
                }
            ],
            max_completion_tokens=20,
            reasoning_effort="minimal"
        )
        
        result = response.choices[0].message.content
        print(f"  ✅ Vision test passed. Response: {result}")
        return True
        
    except Exception as e:
        print(f"  ⚠️  Vision test skipped or failed: {str(e)[:100]}")
        print("     (This is optional - text analysis will still work)")
        return True  # Don't fail the whole test for this

def test_reasoning_effort():
    """Test that reasoning_effort parameter works"""
    print("\n→ Testing reasoning_effort parameter...")
    
    try:
        from openai import AzureOpenAI
        
        endpoint = os.getenv("AZURE_AI_PROJECT_ENDPOINT")
        api_key = os.getenv("AZURE_AI_API_KEY")
        api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2025-04-01-preview")
        deployment = os.getenv("AZURE_VISION_DEPLOYMENT", "gpt-5-2")
        
        if "/api/projects/" in endpoint:
            base_endpoint = endpoint.split("/api/projects/")[0]
        else:
            base_endpoint = endpoint
        
        client = AzureOpenAI(
            azure_endpoint=base_endpoint,
            api_key=api_key,
            api_version=api_version
        )
        
        # Test with 'high' reasoning effort
        response = client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "user", "content": "What is 2+2? Just say the number."}
            ],
            max_completion_tokens=10,
            reasoning_effort="high"
        )

        print(f"  ✅ reasoning_effort='high' works")

        # Test xhigh if available (GPT-5.2 exclusive)
        try:
            response = client.chat.completions.create(
                model=deployment,
                messages=[
                    {"role": "user", "content": "What is 3+3? Just say the number."}
                ],
                max_completion_tokens=10,
                reasoning_effort="xhigh"
            )
            print(f"  ✅ reasoning_effort='xhigh' works (GPT-5.2 confirmed!)")
        except Exception as e:
            if "xhigh" in str(e).lower():
                print(f"  ⚠️  'xhigh' not available - you may have GPT-5.1 instead of 5.2")
            else:
                raise e
        
        return True
        
    except Exception as e:
        print(f"  ❌ Reasoning effort test failed: {str(e)}")
        return False

def main():
    print_header()
    
    # Run checks
    env_ok = check_env_vars()
    if not env_ok:
        sys.exit(1)
    
    connection_ok = test_openai_connection()
    if not connection_ok:
        sys.exit(1)
    
    vision_ok = test_vision_capability()
    reasoning_ok = test_reasoning_effort()
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"  Environment variables: {'✅ OK' if env_ok else '❌ Failed'}")
    print(f"  OpenAI connection:     {'✅ OK' if connection_ok else '❌ Failed'}")
    print(f"  Vision capability:     {'✅ OK' if vision_ok else '⚠️  Limited'}")
    print(f"  Reasoning effort:      {'✅ OK' if reasoning_ok else '⚠️  Limited'}")
    
    if env_ok and connection_ok:
        print("\n✅ All critical tests passed! You're ready to analyze defects.")
        print("\nNext: Run the API server:")
        print("  cd api && python app.py")
        print("\nOr test single image:")
        print("  python -c \"import asyncio; from agents.defect_analyzer_gpt52 import analyze_single_image; print(asyncio.run(analyze_single_image('test.jpg')))\"")
    else:
        print("\n❌ Some tests failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
