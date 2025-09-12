#!/usr/bin/env python3
"""
Test the cancelled products admin API
"""

import requests
import json

def test_cancelled_products_api():
    """Test the cancelled products API"""
    
    base_url = "http://localhost:5000"
    
    # You'll need a valid admin token - replace this
    admin_token = "your_admin_token_here"
    
    headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }
    
    print("Testing cancelled products API...")
    
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
            print("Response is encrypted - would need to decrypt to see details")
        else:
            print(f"Response data: {json.dumps(result, indent=2)}")
    
    # Test with filters
    print("\nTesting with filters...")
    response2 = requests.get(
        f"{base_url}/api/order-items/cancelled-products/admin?status=assigned&limit=10",
        headers=headers
    )
    
    print(f"Filtered response status: {response2.status_code}")
    print(f"Filtered response: {response2.text}")

if __name__ == "__main__":
    test_cancelled_products_api()
