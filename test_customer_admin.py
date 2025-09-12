#!/usr/bin/env python3
"""
Test script for customer admin API endpoints
"""

import requests
import json
import sys
import os

def test_customer_admin_api():
    """Test customer admin API functionality"""
    base_url = "http://localhost:5000"
    
    print("🧪 Testing Customer Admin API...")
    
    # Test 1: Get customers list (requires admin auth)
    print("\n1. Testing GET /api/customers/")
    try:
        response = requests.get(f"{base_url}/api/customers/")
        print(f"   Status: {response.status_code}")
        if response.status_code == 401:
            print("   ✅ Expected: Admin authentication required")
        else:
            print(f"   Response: {response.text[:200]}...")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # Test 2: Update customer (requires admin auth)
    print("\n2. Testing PUT /api/customers/1")
    try:
        response = requests.put(f"{base_url}/api/customers/1", 
                              json={"data": "encrypted_data_here"})
        print(f"   Status: {response.status_code}")
        if response.status_code == 401:
            print("   ✅ Expected: Admin authentication required")
        else:
            print(f"   Response: {response.text[:200]}...")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # Test 3: Delete customer (requires admin auth)
    print("\n3. Testing DELETE /api/customers/1")
    try:
        response = requests.delete(f"{base_url}/api/customers/1")
        print(f"   Status: {response.status_code}")
        if response.status_code == 401:
            print("   ✅ Expected: Admin authentication required")
        else:
            print(f"   Response: {response.text[:200]}...")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # Test 4: Block customer (requires admin auth)
    print("\n4. Testing POST /api/customers/1/block")
    try:
        response = requests.post(f"{base_url}/api/customers/1/block", 
                               json={"blocked": True})
        print(f"   Status: {response.status_code}")
        if response.status_code == 401:
            print("   ✅ Expected: Admin authentication required")
        else:
            print(f"   Response: {response.text[:200]}...")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # Test 5: Health check
    print("\n5. Testing GET /api/health")
    try:
        response = requests.get(f"{base_url}/api/health")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Backend is running")
        else:
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    print("\n🎉 Customer admin API tests completed!")

if __name__ == "__main__":
    test_customer_admin_api()
