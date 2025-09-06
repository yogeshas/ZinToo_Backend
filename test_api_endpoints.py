#!/usr/bin/env python3
"""
Test script for API endpoints
"""

import requests
import json

def test_api_endpoints():
    """Test the enhanced API endpoints"""
    
    base_url = "http://localhost:5000"
    
    # Test endpoints (without authentication for now)
    endpoints = [
        "/api/delivery-enhanced/orders/combined?status=all",
        "/api/delivery-enhanced/exchanges",
        "/api/delivery-enhanced/order-items/cancelled",
    ]
    
    print("🧪 Testing Enhanced API Endpoints...")
    print("=" * 50)
    
    for endpoint in endpoints:
        try:
            url = f"{base_url}{endpoint}"
            print(f"\n📡 Testing: {endpoint}")
            
            response = requests.get(url, timeout=5)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 401:
                print("   ✅ Endpoint exists (requires authentication)")
            elif response.status_code == 200:
                print("   ✅ Endpoint working")
            else:
                print(f"   ⚠️ Unexpected status: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print("   ❌ Server not running")
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    print("\n" + "=" * 50)
    print("✅ API endpoint testing completed!")

if __name__ == "__main__":
    test_api_endpoints()
