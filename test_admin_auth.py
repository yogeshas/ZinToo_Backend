#!/usr/bin/env python3
"""
Test script for admin authentication
"""

import requests
import json
import sys
import os

def test_admin_auth():
    """Test admin authentication functionality"""
    base_url = "http://localhost:5000"
    
    print("🔐 Testing Admin Authentication...")
    
    # Test 1: Check if backend is running
    print("\n1. Testing backend health")
    try:
        response = requests.get(f"{base_url}/api/health")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Backend is running")
        else:
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return
    
    # Test 2: Test customer endpoint without auth
    print("\n2. Testing customer endpoint without authentication")
    try:
        response = requests.get(f"{base_url}/api/customers/")
        print(f"   Status: {response.status_code}")
        if response.status_code == 401:
            print("   ✅ Expected: Authentication required")
        else:
            print(f"   Response: {response.text[:200]}...")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # Test 3: Test with invalid token
    print("\n3. Testing with invalid token")
    try:
        response = requests.get(f"{base_url}/api/customers/", 
                              headers={"Authorization": "Bearer invalid_token"})
        print(f"   Status: {response.status_code}")
        if response.status_code == 401:
            print("   ✅ Expected: Invalid token rejected")
        else:
            print(f"   Response: {response.text[:200]}...")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # Test 4: Test with empty token
    print("\n4. Testing with empty token")
    try:
        response = requests.get(f"{base_url}/api/customers/", 
                              headers={"Authorization": "Bearer "})
        print(f"   Status: {response.status_code}")
        if response.status_code == 401:
            print("   ✅ Expected: Empty token rejected")
        else:
            print(f"   Response: {response.text[:200]}...")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # Test 5: Check if admin routes are registered
    print("\n5. Testing admin route registration")
    try:
        response = requests.get(f"{base_url}/api/customers/1")
        print(f"   Status: {response.status_code}")
        if response.status_code == 401:
            print("   ✅ Admin routes are registered and protected")
        else:
            print(f"   Response: {response.text[:200]}...")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    print("\n🎉 Admin authentication tests completed!")
    print("\n📋 Summary:")
    print("   - Backend should be running (200 response)")
    print("   - Customer endpoints should require auth (401 responses)")
    print("   - Invalid tokens should be rejected (401 responses)")
    print("   - Admin routes should be registered and protected")

if __name__ == "__main__":
    test_admin_auth()
