#!/usr/bin/env python3
"""
Test script to verify customer API functionality
Run this to test customer profile operations
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

def test_customer_api():
    """Test customer API endpoints"""
    print("🔍 Testing Customer API functionality...")
    print("=" * 50)
    
    base_url = "http://localhost:5000/api/customers"
    
    try:
        # Test 1: Get customer by ID
        print("👤 Test 1: Get customer by ID")
        response = requests.get(f"{base_url}/1")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=2)}")
        else:
            print(f"   Error: {response.text}")
        print()
        
        # Test 2: Get customer by ID 2
        print("👤 Test 2: Get customer by ID 2")
        response = requests.get(f"{base_url}/2")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=2)}")
        else:
            print(f"   Error: {response.text}")
        print()
        
        # Test 3: Test error handling
        print("❌ Test 3: Test error handling")
        response = requests.get(f"{base_url}/999999")  # Non-existent customer
        print(f"   Status: {response.status_code}")
        if response.status_code == 404:
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=2)}")
        else:
            print(f"   Unexpected response: {response.text}")
        print()
        
        print("✅ Customer API testing completed!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed. Make sure the backend is running on http://localhost:5000")
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")

def test_database_connection():
    """Test database connection and customer models"""
    print("🔍 Testing database connection and customer models...")
    print("=" * 50)
    
    try:
        from app import app, db
        from models.customer import Customer
        
        with app.app_context():
            # Test database connection
            print("📊 Testing database connection...")
            db.engine.execute("SELECT 1")
            print("✅ Database connection successful")
            
            # Check customer table
            print("📋 Checking customer table...")
            customer_count = Customer.query.count()
            print(f"   Customers: {customer_count}")
            
            # List some customers
            if customer_count > 0:
                print("👥 Sample customers:")
                customers = Customer.query.limit(3).all()
                for customer in customers:
                    print(f"   - ID: {customer.id}, Username: {customer.username}, Email: {customer.email}")
                    print(f"     Status: {customer.status}, Phone: {customer.get_phone_number()}")
            else:
                print("   No customers found in database")
            
            print("✅ Database testing completed!")
            
    except Exception as e:
        print(f"❌ Database testing failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting Customer API and Database Tests...")
    print()
    
    # Test database first
    test_database_connection()
    print()
    
    # Test API endpoints
    test_customer_api()
    
    print()
    print("🎯 Testing completed! Check the results above.")
