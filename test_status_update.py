#!/usr/bin/env python3
"""
Simple test to check if status is updating in database
"""

import requests
import json

def test_cancellation_api():
    """Test the cancellation API directly"""
    
    # Replace with actual values
    order_item_id = 1  # Change this to an actual order item ID
    base_url = "http://localhost:5000"
    
    # You'll need a valid token - replace this
    token = "your_token_here"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test cancellation
    cancel_data = {
        "quantity": 1,
        "reason": "Test cancellation"
    }
    
    print(f"Testing cancellation of item {order_item_id}")
    
    response = requests.post(
        f"{base_url}/api/order-items/items/{order_item_id}/cancel",
        headers=headers,
        json=cancel_data
    )
    
    print(f"Response status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        result = response.json()
        if "encrypted_data" in result:
            print("Response is encrypted - would need to decrypt to see details")
        else:
            print(f"Response data: {json.dumps(result, indent=2)}")

if __name__ == "__main__":
    test_cancellation_api()
