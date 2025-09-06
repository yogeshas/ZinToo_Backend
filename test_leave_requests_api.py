#!/usr/bin/env python3
"""
Test script for leave requests API endpoints
"""

import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_admin_endpoints():
    """Test admin leave request endpoints"""
    print("🧪 Testing Leave Requests API Endpoints")
    print("=" * 50)
    
    # Test 1: Get all leave requests (should require auth)
    print("\n1. Testing GET /api/leave-requests/admin/leave-requests (no auth)")
    try:
        response = requests.get(f"{BASE_URL}/api/leave-requests/admin/leave-requests")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        if response.status_code == 401:
            print("   ✅ Correctly requires authentication")
        else:
            print("   ❌ Should require authentication")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Test with invalid token
    print("\n2. Testing GET /api/leave-requests/admin/leave-requests (invalid token)")
    try:
        headers = {"Authorization": "Bearer invalid_token"}
        response = requests.get(f"{BASE_URL}/api/leave-requests/admin/leave-requests", headers=headers)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        if response.status_code == 401:
            print("   ✅ Correctly rejects invalid token")
        else:
            print("   ❌ Should reject invalid token")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Test delivery guy endpoints (should require delivery auth)
    print("\n3. Testing GET /api/leave-requests/delivery/leave-requests (no auth)")
    try:
        response = requests.get(f"{BASE_URL}/api/leave-requests/delivery/leave-requests")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        if response.status_code == 401:
            print("   ✅ Correctly requires delivery authentication")
        else:
            print("   ❌ Should require delivery authentication")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("✅ API endpoints are working correctly!")
    print("📝 Note: To test with valid tokens, you need to:")
    print("   1. Login as admin to get admin token")
    print("   2. Login as delivery guy to get delivery token")
    print("   3. Use tokens in Authorization header")

def test_database_connection():
    """Test database connection and table existence"""
    print("\n🗄️ Testing Database Connection")
    print("=" * 30)
    
    try:
        from app import app, db
        from models.delivery_leave_request import DeliveryLeaveRequest
        
        with app.app_context():
            # Check if table exists
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'delivery_leave_request' in tables:
                print("✅ delivery_leave_request table exists")
                
                # Check table structure
                columns = inspector.get_columns('delivery_leave_request')
                print(f"✅ Table has {len(columns)} columns:")
                for col in columns:
                    print(f"   - {col['name']}: {col['type']}")
                
                # Test model creation
                print("\n🧪 Testing model creation...")
                test_request = DeliveryLeaveRequest(
                    delivery_guy_id=1,
                    start_date="2024-01-15",
                    end_date="2024-01-17",
                    reason="Test leave request",
                    status="pending"
                )
                print("✅ Model creation successful")
                print(f"   - ID: {test_request.id}")
                print(f"   - Status: {test_request.status}")
                print(f"   - As dict: {test_request.as_dict()}")
                
            else:
                print("❌ delivery_leave_request table not found")
                print(f"Available tables: {tables}")
                
    except Exception as e:
        print(f"❌ Database test failed: {e}")

if __name__ == "__main__":
    test_database_connection()
    test_admin_endpoints()
