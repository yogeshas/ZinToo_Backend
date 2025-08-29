#!/usr/bin/env python3
"""
Test script to verify address API functionality
Run this to test address CRUD operations
"""

import os
import sys
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_address_api():
    """Test address API endpoints"""
    print("🔍 Testing Address API functionality...")
    print("=" * 50)
    
    base_url = "http://localhost:5000/api/addresses"
    
    # Test data
    test_address = {
        "uid": 1,  # Assuming customer ID 1 exists
        "name": "John Doe",
        "type": "home",
        "city": "New York",
        "state": "NY",
        "country": "USA",
        "zip_code": "10001"
    }
    
    try:
        # Test 1: Get customer addresses
        print("📋 Test 1: Get customer addresses")
        response = requests.get(f"{base_url}/customer/1")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=2)}")
        else:
            print(f"   Error: {response.text}")
        print()
        
        # Test 2: Create new address
        print("➕ Test 2: Create new address")
        response = requests.post(f"{base_url}/", json=test_address)
        print(f"   Status: {response.status_code}")
        if response.status_code == 201:
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=2)}")
            address_id = data.get("address", {}).get("id")
        else:
            print(f"   Error: {response.text}")
            address_id = None
        print()
        
        if address_id:
            # Test 3: Get specific address
            print(f"🔍 Test 3: Get address {address_id}")
            response = requests.get(f"{base_url}/{address_id}")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Response: {json.dumps(data, indent=2)}")
            else:
                print(f"   Error: {response.text}")
            print()
            
            # Test 4: Update address
            print(f"✏️  Test 4: Update address {address_id}")
            update_data = {"city": "Los Angeles", "state": "CA", "zip_code": "90210"}
            response = requests.put(f"{base_url}/{address_id}", json=update_data)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Response: {json.dumps(data, indent=2)}")
            else:
                print(f"   Error: {response.text}")
            print()
            
            # Test 5: Delete address
            print(f"🗑️  Test 5: Delete address {address_id}")
            response = requests.delete(f"{base_url}/{address_id}")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Response: {json.dumps(data, indent=2)}")
            else:
                print(f"   Error: {response.text}")
            print()
        
        # Test 6: Test error handling
        print("❌ Test 6: Test error handling")
        response = requests.get(f"{base_url}/999999")  # Non-existent address
        print(f"   Status: {response.status_code}")
        if response.status_code == 404:
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=2)}")
        else:
            print(f"   Unexpected response: {response.text}")
        print()
        
        print("✅ Address API testing completed!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed. Make sure the backend is running on http://localhost:5000")
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")

def test_database_connection():
    """Test database connection and models"""
    print("🔍 Testing database connection and models...")
    print("=" * 50)
    
    try:
        from app import app, db
        from models.address import Address
        from models.customer import Customer
        
        with app.app_context():
            # Test database connection
            print("📊 Testing database connection...")
            db.engine.execute("SELECT 1")
            print("✅ Database connection successful")
            
            # Check tables
            print("📋 Checking database tables...")
            customer_count = Customer.query.count()
            address_count = Address.query.count()
            print(f"   Customers: {customer_count}")
            print(f"   Addresses: {address_count}")
            
            # List some customers
            if customer_count > 0:
                print("👥 Sample customers:")
                customers = Customer.query.limit(3).all()
                for customer in customers:
                    print(f"   - ID: {customer.id}, Username: {customer.username}, Email: {customer.email}")
            
            # List some addresses
            if address_count > 0:
                print("🏠 Sample addresses:")
                addresses = Address.query.limit(3).all()
                for address in addresses:
                    print(f"   - ID: {address.id}, Name: {address.name}, City: {address.city}")
            
            print("✅ Database testing completed!")
            
    except Exception as e:
        print(f"❌ Database testing failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting Address API and Database Tests...")
    print()
    
    # Test database first
    test_database_connection()
    print()
    
    # Test API endpoints
    test_address_api()
    
    print()
    print("🎯 Testing completed! Check the results above.")
