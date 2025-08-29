#!/usr/bin/env python3
"""
Test script for authentication and token validation
"""

import requests
import json
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_authentication():
    """Test authentication endpoints"""
    base_url = "http://localhost:5000"
    
    print("🧪 Testing Authentication...")
    
    # Test 1: Health check (should work without auth)
    print("\n1. Testing GET /api/health")
    try:
        response = requests.get(f"{base_url}/api/health")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Backend is running")
        else:
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # Test 2: Wallet balance without auth (should fail)
    print("\n2. Testing GET /api/wallet/balance (no auth)")
    try:
        response = requests.get(f"{base_url}/api/wallet/balance")
        print(f"   Status: {response.status_code}")
        if response.status_code == 401:
            print("   ✅ Expected: Authentication required")
        else:
            print(f"   Response: {response.text[:200]}...")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # Test 3: Wallet balance with invalid token
    print("\n3. Testing GET /api/wallet/balance (invalid token)")
    try:
        response = requests.get(
            f"{base_url}/api/wallet/balance",
            headers={"Authorization": "Bearer invalid_token"}
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 401:
            print("   ✅ Expected: Invalid token rejected")
        else:
            print(f"   Response: {response.text[:200]}...")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # Test 4: Razorpay create order without auth
    print("\n4. Testing POST /api/razorpay/create-order (no auth)")
    try:
        response = requests.post(f"{base_url}/api/razorpay/create-order")
        print(f"   Status: {response.status_code}")
        if response.status_code == 401:
            print("   ✅ Expected: Authentication required")
        else:
            print(f"   Response: {response.text[:200]}...")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    print("\n🎉 Authentication tests completed!")

if __name__ == "__main__":
    test_authentication()
