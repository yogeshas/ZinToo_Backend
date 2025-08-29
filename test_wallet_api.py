#!/usr/bin/env python3
"""
Test script for wallet API endpoints
"""

import requests
import json
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_wallet_apis():
    """Test wallet API endpoints"""
    base_url = "http://localhost:5001"
    
    print("🧪 Testing Wallet API Endpoints...")
    
    # Test 1: Get wallet balance (requires authentication)
    print("\n1. Testing GET /api/wallet/balance")
    try:
        response = requests.get(f"{base_url}/api/wallet/balance")
        print(f"   Status: {response.status_code}")
        if response.status_code == 401:
            print("   ✅ Expected: Authentication required")
        else:
            print(f"   Response: {response.text[:200]}...")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # Test 2: Get wallet transactions (requires authentication)
    print("\n2. Testing GET /api/wallet/transactions")
    try:
        response = requests.get(f"{base_url}/api/wallet/transactions")
        print(f"   Status: {response.status_code}")
        if response.status_code == 401:
            print("   ✅ Expected: Authentication required")
        else:
            print(f"   Response: {response.text[:200]}...")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # Test 3: Create Razorpay order (requires authentication)
    print("\n3. Testing POST /api/razorpay/create-order")
    try:
        response = requests.post(f"{base_url}/api/razorpay/create-order", 
                               json={"payload": "test_data"})
        print(f"   Status: {response.status_code}")
        if response.status_code == 401:
            print("   ✅ Expected: Authentication required")
        else:
            print(f"   Response: {response.text[:200]}...")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # Test 4: Health check (should work without auth)
    print("\n4. Testing GET /api/health")
    try:
        response = requests.get(f"{base_url}/api/health")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Backend is running")
        else:
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    print("\n🎉 Wallet API tests completed!")

if __name__ == "__main__":
    test_wallet_apis()
