#!/usr/bin/env python3
"""
Test script to check if delivery routes are accessible
"""
import requests
import json

BASE_URL = "http://localhost:5000"

def test_route_access():
    """Test if delivery routes are accessible"""
    print("🔍 Testing Route Access")
    print("=" * 40)
    
    # Test 1: Check if server is running
    print("\n📡 Test 1: Server Status")
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"📥 Response Status: {response.status_code}")
        print(f"📥 Response Body: {response.text}")
    except Exception as e:
        print(f"❌ Server not accessible: {e}")
        return False
    
    # Test 2: Test delivery-mobile routes (should work)
    print("\n📱 Test 2: Delivery Mobile Routes")
    try:
        response = requests.get(f"{BASE_URL}/api/delivery-mobile/auth/send-otp")
        print(f"📥 Response Status: {response.status_code}")
        print(f"📥 Response Body: {response.text}")
    except Exception as e:
        print(f"❌ Delivery mobile route failed: {e}")
    
    # Test 3: Test delivery routes (should return 401 for missing auth)
    print("\n🚚 Test 3: Delivery Routes")
    try:
        response = requests.get(f"{BASE_URL}/api/delivery/onboard")
        print(f"📥 Response Status: {response.status_code}")
        print(f"📥 Response Body: {response.text}")
        
        if response.status_code == 401:
            print("✅ Route exists but requires authentication (expected)")
        elif response.status_code == 404:
            print("❌ Route not found (unexpected)")
        else:
            print(f"⚠️ Unexpected status code: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Delivery route failed: {e}")
    
    # Test 4: Test with invalid auth token
    print("\n🔐 Test 4: Delivery Routes with Invalid Auth")
    try:
        headers = {"Authorization": "Bearer invalid_token"}
        response = requests.get(f"{BASE_URL}/api/delivery/onboard", headers=headers)
        print(f"📥 Response Status: {response.status_code}")
        print(f"📥 Response Body: {response.text}")
        
        if response.status_code == 401:
            print("✅ Route exists and properly validates auth (expected)")
        else:
            print(f"⚠️ Unexpected status code: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Delivery route with auth failed: {e}")
    
    print("\n🏁 Route access test completed!")
    return True

if __name__ == "__main__":
    test_route_access()
