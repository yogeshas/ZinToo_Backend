#!/usr/bin/env python3
"""
Script to check orders and their assignment status
"""
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from models.order import Order
from models.delivery_onboarding import DeliveryOnboarding
from extensions import db
from datetime import datetime, timedelta

def check_orders_status():
    """Check and update orders status based on delivery time"""
    try:
        print("🔍 Checking orders status...")
        
        # Get current time
        now = datetime.utcnow()
        
        # Get unassigned orders older than 24 hours
        unassigned_orders = Order.query.filter_by(delivery_guy_id=None).filter(
            Order.created_at < (now - timedelta(hours=24))
        ).all()
        
        print(f"📦 Found {len(unassigned_orders)} unassigned orders older than 24 hours")
        
        # Update status for old unassigned orders
        for order in unassigned_orders:
            if order.status == 'pending':
                order.status = 'processing'
                print(f"✅ Updated order {order.id} status to 'processing'")
        
        # Get assigned orders
        assigned_orders = Order.query.filter(Order.delivery_guy_id.isnot(None)).all()
        print(f"🚚 Found {len(assigned_orders)} assigned orders")
        
        # Check for orders that might be stuck
        for order in assigned_orders:
            if order.status in ['confirmed', 'processing']:
                # Check if order has been assigned for more than 48 hours
                if order.assigned_at and (now - order.assigned_at) > timedelta(hours=48):
                    print(f"⚠️ Order {order.id} has been assigned for more than 48 hours")
                    # Could add logic here to escalate or reassign
        
        # Get delivery personnel info
        delivery_personnel = DeliveryOnboarding.query.filter_by(status="approved").all()
        print(f"👥 Found {len(delivery_personnel)} approved delivery personnel")
        
        # Check for delivery personnel with many active orders
        for personnel in delivery_personnel:
            active_orders = Order.query.filter_by(
                delivery_guy_id=personnel.id
            ).filter(
                Order.status.in_(['confirmed', 'processing', 'shipped', 'out_for_delivery'])
            ).count()
            
            if active_orders > 5:
                print(f"⚠️ Delivery personnel {personnel.first_name} {personnel.last_name} has {active_orders} active orders")
        
        db.session.commit()
        print("✅ Orders status check completed successfully")
        
    except Exception as e:
        print(f"❌ Error checking orders status: {e}")
        db.session.rollback()

def create_test_orders():
    """Create some test orders for assignment"""
    
    with app.app_context():
        try:
            print("🔧 Creating test orders...")
            
            # Check if we have any orders
            existing_orders = Order.query.count()
            print(f"📊 Existing orders: {existing_orders}")
            
            if existing_orders > 0:
                print("ℹ️ Orders already exist. Creating a few more test orders...")
            
            # Create some test orders
            test_orders = [
                {
                    "customer_id": 1,
                    "order_number": f"TEST-{1001 + existing_orders}",
                    "status": "confirmed",
                    "delivery_address": "123 Test Street, New Delhi",
                    "delivery_type": "standard",
                    "payment_method": "cod",
                    "subtotal": 1500.0,
                    "total_amount": 1600.0
                },
                {
                    "customer_id": 1,
                    "order_number": f"TEST-{1002 + existing_orders}",
                    "status": "processing",
                    "delivery_address": "456 Sample Road, Mumbai",
                    "delivery_type": "express",
                    "payment_method": "razorpay",
                    "subtotal": 2500.0,
                    "total_amount": 2600.0
                },
                {
                    "customer_id": 1,
                    "order_number": f"TEST-{1003 + existing_orders}",
                    "status": "confirmed",
                    "delivery_address": "789 Demo Lane, Bangalore",
                    "delivery_type": "standard",
                    "payment_method": "cod",
                    "subtotal": 800.0,
                    "total_amount": 900.0
                }
            ]
            
            created_count = 0
            for order_data in test_orders:
                try:
                    order = Order(**order_data)
                    db.session.add(order)
                    created_count += 1
                    print(f"✅ Created order: {order_data['order_number']}")
                except Exception as e:
                    print(f"❌ Failed to create order {order_data['order_number']}: {e}")
            
            db.session.commit()
            print(f"\n🎉 Successfully created {created_count} test orders!")
            
        except Exception as e:
            print(f"❌ Error creating test orders: {e}")
            db.session.rollback()
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Order Status Checker")
    print("=" * 60)
    
    # First check current status
    check_orders_status()
    
    print("\n" + "=" * 60)
    
    # Ask if user wants to create test orders
    response = input("\n❓ Do you want to create test orders for assignment? (y/n): ")
    
    if response.lower() in ['y', 'yes']:
        create_test_orders()
        print("\n" + "=" * 60)
        print("🔍 Checking status after creating test orders...")
        check_orders_status()
    else:
        print("ℹ️ No test orders created.")
    
    print("\n✅ Check complete!")
