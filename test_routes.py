#!/usr/bin/env python3
"""
Test script to check if all backend routes are working
"""
import requests
import json

BASE_URL = "http://localhost:5000"

def test_route(url, method="GET", data=None):
    """Test a single route"""
    try:
        if method == "GET":
            response = requests.get(f"{BASE_URL}{url}")
        elif method == "POST":
            response = requests.post(f"{BASE_URL}{url}", json=data)
        
        print(f"{method} {url}: {response.status_code}")
        if response.status_code != 200:
            print(f"  Error: {response.text[:100]}...")
        return response.status_code == 200
    except Exception as e:
        print(f"{method} {url}: ERROR - {str(e)}")
        return False

def main():
    """Test all routes"""
    print("Testing Backend Routes...")
    print("=" * 50)
    
    # Test health endpoint
    test_route("/api/health")
    
    # Test main routes
    routes_to_test = [
        "/api/categories/",
        "/api/subcategories/",
        "/api/products/",
        "/api/widgets/",
        "/api/cart/",
        "/api/wishlist/",
        "/api/coupons/",
        "/api/addresses/",
    ]
    
    success_count = 0
    total_count = len(routes_to_test)
    
    for route in routes_to_test:
        if test_route(route):
            success_count += 1
    
    print("=" * 50)
    print(f"Results: {success_count}/{total_count} routes working")
    
    if success_count == total_count:
        print("✅ All routes are working!")
    else:
        print("❌ Some routes are not working. Check the errors above.")

if __name__ == "__main__":
    main()
