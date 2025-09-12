#!/usr/bin/env python3
"""
Test script for Coupon API endpoints
Run this script to test the coupon CRUD operations
"""

import requests
import json
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:5000/api"
HEADERS = {"Content-Type": "application/json"}

def test_coupon_endpoints():
    """Test all coupon API endpoints"""
    
    print("🧪 Testing Coupon API Endpoints")
    print("=" * 50)
    
    # Test 1: Get all coupons
    print("\n1. Testing GET /api/coupons/")
    try:
        response = requests.get(f"{BASE_URL}/coupons/", headers=HEADERS)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success')}")
            print(f"Message: {data.get('message')}")
            if data.get('encrypted_data'):
                print("✅ Encrypted data received")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
    
    # Test 2: Get categories for target selection
    print("\n2. Testing GET /api/coupons/targets/categories")
    try:
        response = requests.get(f"{BASE_URL}/coupons/targets/categories", headers=HEADERS)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success')}")
            print(f"Message: {data.get('message')}")
            if data.get('encrypted_data'):
                print("✅ Categories encrypted data received")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
    
    # Test 3: Get subcategories
    print("\n3. Testing GET /api/coupons/targets/subcategories")
    try:
        response = requests.get(f"{BASE_URL}/coupons/targets/subcategories", headers=HEADERS)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success')}")
            print(f"Message: {data.get('message')}")
            if data.get('encrypted_data'):
                print("✅ Subcategories encrypted data received")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
    
    # Test 4: Get products
    print("\n4. Testing GET /api/coupons/targets/products")
    try:
        response = requests.get(f"{BASE_URL}/coupons/targets/products", headers=HEADERS)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success')}")
            print(f"Message: {data.get('message')}")
            if data.get('encrypted_data'):
                print("✅ Products encrypted data received")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🎯 Test completed! Check the results above.")
    print("\nNote: These tests verify the API endpoints are accessible.")
    print("For full functionality testing, use the admin frontend.")

if __name__ == "__main__":
    test_coupon_endpoints() 