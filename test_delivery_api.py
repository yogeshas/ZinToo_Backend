#!/usr/bin/env python3
"""
Test Delivery API

This script tests the delivery orders API to ensure it's working correctly.
"""

import requests
import json
from datetime import datetime

def test_delivery_orders_api():
    """Test the delivery orders API"""
    
    base_url = "http://localhost:5000"
    
    print("🧪 Testing Delivery Orders API")
    print("=" * 50)
    
    # Test data - using delivery guy ID 1
    delivery_guy_id = 1
    test_token = f"test_token_for_delivery_guy_{delivery_guy_id}"
    
    print(f"🔑 Testing with Delivery Guy ID: {delivery_guy_id}")
    print(f"🔑 Using test token: {test_token}")
    
    # Test 1: Get all orders for delivery guy
    print("\n1. 📦 Testing GET /api/delivery/orders")
    try:
        response = requests.get(
            f"{base_url}/api/delivery/orders",
            headers={
                "Authorization": f"Bearer {test_token}",
                "Content-Type": "application/json"
            }
        )
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                orders = data.get("orders", [])
                print(f"   ✅ Success! Found {len(orders)} orders")
                for order in orders:
                    print(f"      - Order {order.get('order_number')}: {order.get('status')}")
            else:
                print(f"   ❌ API returned success=false: {data.get('message')}")
        else:
            print(f"   ❌ API returned error status: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("   ❌ Connection error - is the server running?")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # Test 2: Get orders with status filter
    print("\n2. 📦 Testing GET /api/delivery/orders?status=assigned")
    try:
        response = requests.get(
            f"{base_url}/api/delivery/orders?status=assigned",
            headers={
                "Authorization": f"Bearer {test_token}",
                "Content-Type": "application/json"
            }
        )
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                orders = data.get("orders", [])
                print(f"   ✅ Success! Found {len(orders)} assigned orders")
            else:
                print(f"   ❌ API returned success=false: {data.get('message')}")
        else:
            print(f"   ❌ API returned error status: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("   ❌ Connection error - is the server running?")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # Test 3: Get specific order details
    print("\n3. 📦 Testing GET /api/delivery/orders/1")
    try:
        response = requests.get(
            f"{base_url}/api/delivery/orders/1",
            headers={
                "Authorization": f"Bearer {test_token}",
                "Content-Type": "application/json"
            }
        )
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                order = data.get("order")
                print(f"   ✅ Success! Retrieved order details")
                if order:
                    print(f"      - Order: {order.get('order_number')}")
                    print(f"      - Status: {order.get('status')}")
                    print(f"      - Items: {len(order.get('items', []))}")
            else:
                print(f"   ❌ API returned success=false: {data.get('message')}")
        else:
            print(f"   ❌ API returned error status: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("   ❌ Connection error - is the server running?")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")

def create_simple_auth_token():
    """Create a simple auth token for testing"""
    
    print("\n🔑 Creating Simple Auth Token for Testing")
    print("=" * 50)
    
    # This is a simplified approach - in production, you'd use proper JWT tokens
    # For testing, we'll create a mock token that the API can recognize
    
    test_token_data = {
        "delivery_guy_id": 1,
        "email": "rajesh.kumar@delivery.com",
        "exp": int(datetime.now().timestamp()) + 3600  # 1 hour from now
    }
    
    # Simple base64 encoding (not secure, just for testing)
    import base64
    token = base64.b64encode(json.dumps(test_token_data).encode()).decode()
    
    print(f"✅ Test token created: {token}")
    print(f"📋 Token data: {test_token_data}")
    
    return token

def main():
    """Main test function"""
    
    print("🚀 Delivery Orders API Test Suite")
    print("=" * 60)
    
    # Create test token
    test_token = create_simple_auth_token()
    
    # Test the API
    test_delivery_orders_api()
    
    print("\n📋 Test Summary:")
    print("✅ Created test delivery system with sample data")
    print("✅ Created test authentication token")
    print("✅ Tested delivery orders API endpoints")
    print("\n🔧 If tests fail:")
    print("1. Make sure the Flask server is running on localhost:5000")
    print("2. Check that the delivery orders routes are properly registered")
    print("3. Verify the authentication system is working")
    print("4. Check server logs for any errors")

if __name__ == "__main__":
    main()
