#!/usr/bin/env python3
"""
Debug script - call the API endpoint directly and see the full error
"""

import requests
import json

print("=" * 60)
print("  DEBUG: Direct API Call")
print("=" * 60)
print()

# Upload test image
print("Uploading test_knife.jpg to API...")
with open('test_knife.jpg', 'rb') as f:
    files = {'image': f}
    data = {
        'product_sku': 'WK-KN-200',
        'facility': 'yangjiang'
    }

    try:
        response = requests.post(
            'http://localhost:5001/api/v1/analyze',
            files=files,
            data=data,
            timeout=120  # 2 minute timeout
        )

        print(f"Status Code: {response.status_code}")
        print()
        print("Response Headers:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
        print()
        print("Response Body:")
        print(response.text[:1000])
        print()

        if response.status_code == 200:
            try:
                result = response.json()
                print("✓ Success! Parsed JSON:")
                print(json.dumps(result, indent=2)[:500])
            except json.JSONDecodeError as e:
                print(f"✗ Failed to parse JSON: {e}")
        else:
            print(f"✗ HTTP Error: {response.status_code}")

    except requests.exceptions.Timeout:
        print("✗ Request timed out after 120 seconds")
    except Exception as e:
        print(f"✗ Error: {type(e).__name__}: {str(e)}")
