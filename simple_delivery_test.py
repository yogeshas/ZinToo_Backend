#!/usr/bin/env python3
"""
Simple Delivery Test

This script tests the delivery API with proper model imports.
"""

import os
import sys
from flask import Flask
from config import Config
from extensions import db

def test_delivery_with_proper_imports():
    """Test delivery API with proper model imports"""
    
    print("🧪 Testing Delivery API with Proper Model Imports")
    print("=" * 60)
    
    # Create Flask app
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize database
    db.init_app(app)
    
    with app.app_context():
        try:
            # Import models in correct order
            print("📦 Importing models...")
            
            # Import base models first
            from models.category import Category
            from models.subcategory import SubCategory
            from models.customer import Customer
            from models.product import Product
            from models.delivery_onboarding import DeliveryOnboarding
            from models.order import Order, OrderItem
            
            print("✅ Models imported successfully")
            
            # Test 1: Check delivery onboarding
            print("\n1. 📋 Checking Delivery Onboarding:")
            delivery_guys = DeliveryOnboarding.query.all()
            print(f"   Found {len(delivery_guys)} delivery personnel")
            
            for guy in delivery_guys:
                print(f"   - ID: {guy.id}, Name: {guy.first_name} {guy.last_name}, Status: {guy.status}")
            
            # Test 2: Check orders
            print("\n2. 📦 Checking Orders:")
            orders = Order.query.all()
            print(f"   Found {len(orders)} total orders")
            
            for order in orders:
                print(f"   - ID: {order.id}, Number: {order.order_number}, Status: {order.status}, Delivery Guy: {order.delivery_guy_id}")
            
            # Test 3: Check assigned orders
            print("\n3. 🚚 Checking Assigned Orders:")
            assigned_orders = Order.query.filter(Order.delivery_guy_id.isnot(None)).all()
            print(f"   Found {len(assigned_orders)} assigned orders")
            
            for order in assigned_orders:
                print(f"   - Order {order.order_number}: Assigned to Delivery Guy {order.delivery_guy_id}")
            
            # Test 4: Test delivery API function
            if assigned_orders:
                print("\n4. 🔍 Testing Delivery API Function:")
                from services.delivery_order_service import get_orders_for_delivery_guy, serialize_orders_with_customer
                
                # Test with first assigned order's delivery guy
                delivery_guy_id = assigned_orders[0].delivery_guy_id
                print(f"   Testing for Delivery Guy ID: {delivery_guy_id}")
                
                orders_for_guy = get_orders_for_delivery_guy(delivery_guy_id)
                print(f"   - Found {len(orders_for_guy)} orders for this delivery guy")
                
                for order in orders_for_guy:
                    print(f"     * Order {order.order_number}: {order.status}")
                
                # Test serialization
                serialized_orders = serialize_orders_with_customer(orders_for_guy)
                print(f"   - Serialized {len(serialized_orders)} orders successfully")
                
                if serialized_orders:
                    print(f"   - First order data: {serialized_orders[0].keys()}")
                
                print("\n✅ Delivery API is working correctly!")
                return True
            else:
                print("\n⚠️ No assigned orders found. You need to assign orders to delivery personnel.")
                return False
                
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """Main test function"""
    
    print("🚀 Simple Delivery API Test")
    print("=" * 40)
    
    if test_delivery_with_proper_imports():
        print("\n🎉 SUCCESS! The delivery API is working correctly.")
        print("\n📋 Summary:")
        print("✅ All models imported successfully")
        print("✅ Database connection working")
        print("✅ Delivery API functions working")
        print("✅ Order serialization working")
        print("\n🔧 Next Steps:")
        print("1. Use the fixed_api_service.dart in your Flutter app")
        print("2. Make sure your Flutter app uses the correct API endpoints")
        print("3. Test with a valid delivery guy authentication token")
        print("4. Check if orders are now visible in the mobile app")
    else:
        print("\n❌ FAILED! There are issues with the delivery API.")
        print("\n🔧 Troubleshooting:")
        print("1. Check if orders are assigned to delivery personnel")
        print("2. Verify the database connection")
        print("3. Check if all required models are imported")

if __name__ == "__main__":
    main()
