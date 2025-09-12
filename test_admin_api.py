#!/usr/bin/env python3
"""
Test admin API with proper authentication
"""

import requests
import json
import jwt
from config import Config

def create_test_admin_token():
    """Create a test admin token"""
    payload = {
        "id": 1,
        "username": "test_admin",
        "role": "admin"
    }
    token = jwt.encode(payload, Config.SECRET_KEY, algorithm="HS256")
    return token

def test_cancelled_products_api():
    """Test the cancelled products API with proper authentication"""
    
    base_url = "http://localhost:5000"
    
    # Create a test admin token
    admin_token = create_test_admin_token()
    
    headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }
    
    print("Testing cancelled products API with admin token...")
    print(f"Token: {admin_token}")
    
    # Test basic API call
    response = requests.get(
        f"{base_url}/api/order-items/cancelled-products/admin",
        headers=headers
    )
    
    print(f"Response status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        result = response.json()
        if "encrypted_data" in result:
            print("✅ API is working - response is encrypted")
            print("Response contains encrypted data that needs to be decrypted on frontend")
        else:
            print(f"Response data: {json.dumps(result, indent=2)}")
    else:
        print(f"❌ API failed with status {response.status_code}")

if __name__ == "__main__":
    test_cancelled_products_api()
