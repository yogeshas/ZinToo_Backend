#!/usr/bin/env python3
"""
Test script for the exchange endpoint
"""

import requests
import json

def test_exchange_endpoint():
    """Test the exchange endpoint"""
    
    # Test data
    test_data = {
        "payload": "test_payload_not_encrypted"  # This should fail with decryption error
    }
    
    # Test the endpoint
    url = "http://localhost:5000/api/orders/1/exchange"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer test_token"
    }
    
    try:
        print("🧪 Testing exchange endpoint...")
        print(f"URL: {url}")
        print(f"Data: {test_data}")
        
        response = requests.post(url, json=test_data, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 401:
            print("✅ Expected 401 - Authentication required")
        elif response.status_code == 500:
            print("✅ Expected 500 - Decryption error (payload not encrypted)")
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing endpoint: {e}")

if __name__ == "__main__":
    test_exchange_endpoint()
