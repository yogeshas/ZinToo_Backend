#!/usr/bin/env python3
"""
Test MySQL Delivery API

This script tests the delivery orders API with the existing MySQL database.
"""

import os
import sys
from flask import Flask
from config import Config
from extensions import db
from models.delivery_onboarding import DeliveryOnboarding
from models.order import Order, OrderItem
from services.delivery_order_service import get_orders_for_delivery_guy, serialize_orders_with_customer

def test_delivery_api_with_mysql():
    """Test the delivery API with existing MySQL database"""
    
    print("🧪 Testing Delivery API with MySQL Database")
    print("=" * 60)
    
    # Create Flask app
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize database
    db.init_app(app)
    
    with app.app_context():
        try:
            # Test 1: Check if delivery onboarding table exists and has data
            print("\n1. 📋 Checking Delivery Onboarding Table:")
            delivery_guys = DeliveryOnboarding.query.all()
            print(f"   Found {len(delivery_guys)} delivery personnel:")
            
            for guy in delivery_guys:
                print(f"   - ID: {guy.id}, Name: {guy.first_name} {guy.last_name}, Email: {guy.email}, Status: {guy.status}")
            
            if not delivery_guys:
                print("   ❌ No delivery personnel found!")
                return False
            
            # Test 2: Check if orders exist
            print("\n2. 📦 Checking Orders Table:")
            orders = Order.query.all()
            print(f"   Found {len(orders)} total orders:")
            
            for order in orders:
                print(f"   - ID: {order.id}, Number: {order.order_number}, Status: {order.status}, Delivery Guy ID: {order.delivery_guy_id}")
            
            if not orders:
                print("   ❌ No orders found!")
                return False
            
            # Test 3: Check orders assigned to delivery personnel
            print("\n3. 🚚 Checking Assigned Orders:")
            assigned_orders = Order.query.filter(Order.delivery_guy_id.isnot(None)).all()
            print(f"   Found {len(assigned_orders)} assigned orders:")
            
            for order in assigned_orders:
                print(f"   - Order {order.order_number}: Assigned to Delivery Guy {order.delivery_guy_id}")
            
            if not assigned_orders:
                print("   ❌ No assigned orders found!")
                print("   💡 You need to assign orders to delivery personnel first.")
                return False
            
            # Test 4: Test the delivery API function
            print("\n4. 🔍 Testing Delivery API Function:")
            for delivery_guy in delivery_guys[:2]:  # Test first 2 delivery guys
                print(f"\n   Testing for Delivery Guy {delivery_guy.id} ({delivery_guy.first_name} {delivery_guy.last_name}):")
                
                # Test getting orders for this delivery guy
                orders_for_guy = get_orders_for_delivery_guy(delivery_guy.id)
                print(f"   - Found {len(orders_for_guy)} orders assigned to this delivery guy")
                
                for order in orders_for_guy:
                    print(f"     * Order {order.order_number}: {order.status}")
                
                # Test serialization
                serialized_orders = serialize_orders_with_customer(orders_for_guy)
                print(f"   - Serialized {len(serialized_orders)} orders successfully")
                
                # Test with status filter
                approved_orders = get_orders_for_delivery_guy(delivery_guy.id, "approved")
                print(f"   - Found {len(approved_orders)} approved orders")
            
            print("\n✅ All tests passed! The delivery API should work correctly.")
            return True
            
        except Exception as e:
            print(f"\n❌ Error testing delivery API: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

def create_test_assignment():
    """Create a test assignment if none exist"""
    
    print("\n🔧 Creating Test Assignment...")
    print("=" * 40)
    
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    
    with app.app_context():
        try:
            # Get first approved delivery guy
            delivery_guy = DeliveryOnboarding.query.filter_by(status='approved').first()
            if not delivery_guy:
                print("❌ No approved delivery personnel found!")
                return False
            
            print(f"📋 Using delivery guy: {delivery_guy.first_name} {delivery_guy.last_name} (ID: {delivery_guy.id})")
            
            # Get first unassigned order
            unassigned_order = Order.query.filter_by(delivery_guy_id=None).first()
            if not unassigned_order:
                print("❌ No unassigned orders found!")
                return False
            
            print(f"📦 Using order: {unassigned_order.order_number} (ID: {unassigned_order.id})")
            
            # Assign the order
            unassigned_order.delivery_guy_id = delivery_guy.id
            unassigned_order.status = 'assigned'
            
            # Assign order items
            order_items = OrderItem.query.filter_by(order_id=unassigned_order.id).all()
            for item in order_items:
                item.delivery_guy_id = delivery_guy.id
                item.status = 'assigned'
            
            db.session.commit()
            
            print(f"✅ Successfully assigned order {unassigned_order.order_number} to delivery guy {delivery_guy.first_name}")
            print(f"🔑 Delivery Guy ID for testing: {delivery_guy.id}")
            print(f"📦 Order ID for testing: {unassigned_order.id}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating test assignment: {str(e)}")
            db.session.rollback()
            return False

def main():
    """Main test function"""
    
    print("🚀 MySQL Delivery API Test Suite")
    print("=" * 60)
    
    # Test the API
    if test_delivery_api_with_mysql():
        print("\n🎉 Delivery API is working correctly!")
    else:
        print("\n🔧 Creating test assignment...")
        if create_test_assignment():
            print("\n🔄 Re-testing after creating assignment...")
            test_delivery_api_with_mysql()
    
    print("\n📋 Next Steps:")
    print("1. Use the fixed_api_service.dart in your Flutter app")
    print("2. Test with a valid delivery guy authentication token")
    print("3. Check if orders are now visible in the mobile app")
    print("4. Verify the API endpoints are working correctly")

if __name__ == "__main__":
    main()
