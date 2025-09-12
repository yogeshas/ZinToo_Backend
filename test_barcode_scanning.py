#!/usr/bin/env python3
"""
Test script for barcode scanning API endpoint
"""

import requests
import base64
import json

def test_barcode_scanning():
    """Test the barcode scanning endpoint"""
    
    # Test data
    base_url = "http://127.0.0.1:5000"
    endpoint = f"{base_url}/api/delivery-orders/scan-barcode"
    
    # Create a simple test image (1x1 pixel) - this is just for testing the endpoint
    # In real usage, you would send an actual barcode image
    test_image_data = b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    test_image_base64 = base64.b64encode(test_image_data).decode('utf-8')
    
    # Test payload
    payload = {
        "image_base64": test_image_base64,
        "expected_barcodes": ["1234567890123", "9876543210987"]
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        print("Testing barcode scanning endpoint...")
        print(f"Endpoint: {endpoint}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(endpoint, json=payload, headers=headers)
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            print("\n✅ Barcode scanning endpoint is working!")
        else:
            print(f"\n❌ Barcode scanning endpoint returned error: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the server. Make sure the Flask app is running.")
    except Exception as e:
        print(f"❌ Error testing barcode scanning: {e}")

if __name__ == "__main__":
    test_barcode_scanning()
