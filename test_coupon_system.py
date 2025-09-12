#!/usr/bin/env python3
"""
Test script for the coupon system
This script will:
1. Test database connection
2. Check if coupons table exists
3. Create sample coupons
4. Test coupon API endpoints
"""

import requests
import json
from datetime import datetime, timedelta
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_database_connection():
    """Test if we can connect to the database and access coupon model"""
    try:
        from app import app, db
        from models.coupons import Coupon
        
        with app.app_context():
            # Check if table exists
            result = db.engine.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='coupon'")
            tables = [row[0] for row in result]
            
            if 'coupon' not in tables:
                print("❌ Coupon table does not exist!")
                return False
            
            print("✅ Coupon table exists")
            
            # Check if there are any coupons
            coupon_count = Coupon.query.count()
            print(f"📊 Found {coupon_count} coupons in database")
            
            return True
            
    except Exception as e:
        print(f"❌ Database connection error: {str(e)}")
        return False

def create_sample_coupons():
    """Create sample coupons for testing"""
    try:
        from app import app, db
        from models.coupons import Coupon
        from datetime import datetime, timedelta
        
        with app.app_context():
            # Check if coupons already exist
            existing_coupons = Coupon.query.all()
            if existing_coupons:
                print(f"📝 Found {len(existing_coupons)} existing coupons:")
                for coupon in existing_coupons:
                    print(f"   - {coupon.code}: {coupon.discount_value}{'%' if coupon.discount_type == 'percentage' else '₹'} off")
                return True
            
            # Create sample coupons
            now = datetime.utcnow()
            future_date = now + timedelta(days=30)
            
            sample_coupons = [
                {
                    "code": "WELCOME10",
                    "discount_type": "percentage",
                    "discount_value": 10,
                    "start_date": now,
                    "end_date": future_date,
                    "is_active": True,
                    "description": "Welcome discount for new customers",
                    "min_order_amount": 100,
                    "max_discount_amount": 500,
                    "usage_limit": 100,
                    "target_type": "all"
                },
                {
                    "code": "SAVE20",
                    "discount_type": "percentage",
                    "discount_value": 20,
                    "start_date": now,
                    "end_date": future_date,
                    "is_active": True,
                    "description": "Save 20% on your order",
                    "min_order_amount": 200,
                    "max_discount_amount": 1000,
                    "usage_limit": 50,
                    "target_type": "all"
                },
                {
                    "code": "FLAT50",
                    "discount_type": "fixed",
                    "discount_value": 50,
                    "start_date": now,
                    "end_date": future_date,
                    "is_active": True,
                    "description": "Flat ₹50 off on orders above ₹300",
                    "min_order_amount": 300,
                    "max_discount_amount": 50,
                    "usage_limit": 200,
                    "target_type": "all"
                },
                {
                    "code": "FREESHIP",
                    "discount_type": "fixed",
                    "discount_value": 50,  # Assuming delivery fee is ₹50
                    "start_date": now,
                    "end_date": future_date,
                    "is_active": True,
                    "description": "Free shipping on orders above ₹500",
                    "min_order_amount": 500,
                    "max_discount_amount": 50,
                    "usage_limit": 100,
                    "target_type": "all"
                }
            ]
            
            for coupon_data in sample_coupons:
                coupon = Coupon(**coupon_data)
                db.session.add(coupon)
            
            db.session.commit()
            print(f"✅ Created {len(sample_coupons)} sample coupons")
            
            # Verify coupons were created
            coupon_count = Coupon.query.count()
            print(f"📊 Total coupons in database: {coupon_count}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error creating sample coupons: {str(e)}")
        return False

def test_coupon_api():
    """Test the coupon API endpoints"""
    base_url = "http://localhost:5000"
    
    print("\n🧪 Testing Coupon API Endpoints...")
    
    # Test 1: Get all coupons
    try:
        print("📡 Testing GET /api/coupons/")
        response = requests.get(f"{base_url}/api/coupons/")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=2)}")
            
            if data.get("success") and data.get("encrypted_data"):
                print("   ✅ Coupons endpoint working with encrypted data")
            else:
                print("   ❌ Unexpected response format")
        else:
            print(f"   ❌ Failed to get coupons: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("   ❌ Cannot connect to backend. Is it running?")
    except Exception as e:
        print(f"   ❌ Error testing coupons endpoint: {str(e)}")
    
    # Test 2: Test coupon validation
    try:
        print("\n📡 Testing POST /api/coupons/validate")
        test_data = {
            "coupon_code": "WELCOME10",
            "cart_items": [
                {"product_id": 1, "cid": 1, "sid": 1, "price": 150}
            ],
            "subtotal": 150
        }
        
        response = requests.post(
            f"{base_url}/api/coupons/validate",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=2)}")
            print("   ✅ Coupon validation endpoint working")
        else:
            print(f"   ❌ Validation failed: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("   ❌ Cannot connect to backend. Is it running?")
    except Exception as e:
        print(f"   ❌ Error testing validation endpoint: {str(e)}")

def main():
    """Main test function"""
    print("🎫 Testing Coupon System")
    print("=" * 50)
    
    # Test 1: Database connection
    print("\n1️⃣ Testing Database Connection...")
    if not test_database_connection():
        print("❌ Database test failed. Exiting.")
        return
    
    # Test 2: Create sample coupons
    print("\n2️⃣ Creating Sample Coupons...")
    if not create_sample_coupons():
        print("❌ Failed to create sample coupons. Exiting.")
        return
    
    # Test 3: Test API endpoints
    print("\n3️⃣ Testing API Endpoints...")
    test_coupon_api()
    
    print("\n" + "=" * 50)
    print("🎉 Coupon system test completed!")
    print("\n📋 Next Steps:")
    print("1. Make sure your backend is running: python3 app.py")
    print("2. Check the frontend cart page for coupons")
    print("3. If still no coupons, check browser console for errors")

if __name__ == "__main__":
    main()
