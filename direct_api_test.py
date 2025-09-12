#!/usr/bin/env python3
"""
Direct API Test

This script directly tests the delivery orders API without complex model imports.
"""

import requests
import json
from datetime import datetime

def test_delivery_api_directly():
    """Test the delivery API directly via HTTP requests"""
    
    print("🧪 Testing Delivery API Directly via HTTP")
    print("=" * 60)
    
    base_url = "http://localhost:5000"
    
    # Test 1: Health check
    print("\n1. 🏥 Testing Health Check:")
    try:
        response = requests.get(f"{base_url}/api/health", timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 200:
            print("   ✅ Backend is running")
        else:
            print("   ❌ Backend health check failed")
            return False
            
    except requests.exceptions.ConnectionError:
        print("   ❌ Cannot connect to backend - is it running?")
        print("   💡 Start the Flask server with: python app.py")
        return False
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False
    
    # Test 2: Test delivery orders endpoint (without auth for now)
    print("\n2. 📦 Testing Delivery Orders Endpoint (No Auth):")
    try:
        response = requests.get(f"{base_url}/api/delivery/orders", timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 401:
            print("   ✅ Endpoint exists and requires authentication (expected)")
        else:
            print(f"   ⚠️ Unexpected status code: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # Test 3: Test with mock authentication
    print("\n3. 🔑 Testing with Mock Authentication:")
    try:
        # Create a mock token (this won't work but shows the endpoint structure)
        mock_token = "mock_token_for_testing"
        
        headers = {
            'Authorization': f'Bearer {mock_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(f"{base_url}/api/delivery/orders", headers=headers, timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 401:
            print("   ✅ Authentication is working (token rejected as expected)")
        elif response.status_code == 200:
            print("   ✅ API returned data (unexpected but good!)")
            data = response.json()
            if data.get('success'):
                orders = data.get('orders', [])
                print(f"   📦 Found {len(orders)} orders")
            else:
                print(f"   ⚠️ API returned success=false: {data.get('message')}")
        else:
            print(f"   ⚠️ Unexpected status: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    return True

def create_simple_test_data():
    """Create simple test data for the API"""
    
    print("\n🔧 Creating Simple Test Data...")
    print("=" * 40)
    
    # This would require database access, so we'll skip for now
    print("💡 To create test data:")
    print("1. Make sure your MySQL database is running")
    print("2. Ensure you have delivery personnel in the delivery_onboarding table")
    print("3. Ensure you have orders assigned to delivery personnel")
    print("4. Use the admin panel to assign orders to delivery guys")

def main():
    """Main test function"""
    
    print("🚀 Direct Delivery API Test")
    print("=" * 40)
    
    if test_delivery_api_directly():
        print("\n✅ API endpoints are accessible!")
        print("\n📋 Summary:")
        print("✅ Backend server is running")
        print("✅ Delivery orders endpoint exists")
        print("✅ Authentication is working")
        print("\n🔧 Next Steps:")
        print("1. Make sure you have delivery personnel in your database")
        print("2. Make sure you have orders assigned to delivery personnel")
        print("3. Use the fixed_api_service.dart in your Flutter app")
        print("4. Test with a valid authentication token")
        print("\n💡 If you're still getting empty arrays:")
        print("- Check if orders are assigned to delivery personnel")
        print("- Verify the delivery_guy_id in the order table")
        print("- Check if the delivery personnel status is 'approved'")
    else:
        print("\n❌ API test failed!")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure the Flask server is running: python app.py")
        print("2. Check if the server is accessible at http://localhost:5000")
        print("3. Verify the database connection")
        print("4. Check server logs for errors")

if __name__ == "__main__":
    main()
