#!/usr/bin/env python3
"""
Test script to get a valid delivery token and test leave requests
"""

import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_delivery_login_and_leave():
    """Test delivery login and leave requests"""
    print("🧪 Testing Delivery Authentication and Leave Requests")
    print("=" * 60)
    
    # Step 1: Try to login as delivery guy
    print("\n1. Testing delivery login...")
    login_data = {
        "email": "test@delivery.com",  # You'll need to use a real delivery guy email
        "password": "password123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/delivery-mobile/auth/login", json=login_data)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('token'):
                token = data['token']
                print(f"   ✅ Got delivery token: {token[:20]}...")
                
                # Step 2: Test leave requests with valid token
                print("\n2. Testing leave requests with valid token...")
                headers = {"Authorization": f"Bearer {token}"}
                
                # Get leave requests
                response = requests.get(f"{BASE_URL}/api/leave-requests/delivery/leave-requests", headers=headers)
                print(f"   Status: {response.status_code}")
                print(f"   Response: {response.json()}")
                
                if response.status_code == 200:
                    print("   ✅ Leave requests API working!")
                else:
                    print("   ❌ Leave requests API failed")
                    
                # Create a test leave request
                print("\n3. Testing create leave request...")
                leave_data = {
                    "start_date": "2024-01-15",
                    "end_date": "2024-01-17",
                    "reason": "Test leave request from script"
                }
                
                response = requests.post(f"{BASE_URL}/api/leave-requests/delivery/leave-requests", 
                                       json=leave_data, headers=headers)
                print(f"   Status: {response.status_code}")
                print(f"   Response: {response.json()}")
                
                if response.status_code == 201:
                    print("   ✅ Create leave request working!")
                else:
                    print("   ❌ Create leave request failed")
                    
            else:
                print("   ❌ Login failed - no token received")
        else:
            print("   ❌ Login failed")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("📝 Note: You need to have a delivery guy account in the database")
    print("   with email 'test@delivery.com' and password 'password123'")
    print("   Or update the credentials in this script to match your data.")

def test_admin_login_and_leave():
    """Test admin login and leave requests"""
    print("\n🧪 Testing Admin Authentication and Leave Requests")
    print("=" * 60)
    
    # Step 1: Try to login as admin
    print("\n1. Testing admin login...")
    login_data = {
        "email": "hatchybyte@gmail.com",  # Default admin email
        "password": "zintoo@1234"  # Default admin password
    }
    
    try:
        # First, get the encrypted payload (you might need to implement this)
        response = requests.post(f"{BASE_URL}/api/admin/login", json=login_data)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('requires_otp'):
                print("   ℹ️ Admin login requires OTP verification")
                print("   This is expected behavior for security")
            elif data.get('token'):
                token = data['token']
                print(f"   ✅ Got admin token: {token[:20]}...")
                
                # Test admin leave requests
                print("\n2. Testing admin leave requests...")
                headers = {"Authorization": f"Bearer {token}"}
                
                response = requests.get(f"{BASE_URL}/api/leave-requests/admin/leave-requests", headers=headers)
                print(f"   Status: {response.status_code}")
                print(f"   Response: {response.json()}")
                
                if response.status_code == 200:
                    print("   ✅ Admin leave requests API working!")
                else:
                    print("   ❌ Admin leave requests API failed")
        else:
            print("   ❌ Admin login failed")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    test_delivery_login_and_leave()
    test_admin_login_and_leave()
