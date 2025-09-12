#!/usr/bin/env python3
"""
Test script for referral system
"""

import requests
import json
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_referral_system():
    """Test referral system functionality"""
    base_url = "http://localhost:5000"
    
    print("🧪 Testing Referral System...")
    
    # Test 1: Validate referral code endpoint
    print("\n1. Testing POST /api/referral/validate")
    try:
        response = requests.post(f"{base_url}/api/referral/validate", 
                               json={"referral_code": "JOH001"})
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {data}")
        else:
            print(f"   Response: {response.text[:200]}...")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # Test 2: Get referral stats (requires authentication)
    print("\n2. Testing GET /api/referral/stats")
    try:
        response = requests.get(f"{base_url}/api/referral/stats")
        print(f"   Status: {response.status_code}")
        if response.status_code == 401:
            print("   ✅ Expected: Authentication required")
        else:
            print(f"   Response: {response.text[:200]}...")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # Test 3: Health check
    print("\n3. Testing GET /api/health")
    try:
        response = requests.get(f"{base_url}/api/health")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Backend is running")
        else:
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    print("\n🎉 Referral system tests completed!")

if __name__ == "__main__":
    test_referral_system()
