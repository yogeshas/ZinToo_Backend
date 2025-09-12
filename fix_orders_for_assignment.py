#!/usr/bin/env python3
"""
Script to fix orders for assignment by updating their status
"""
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from models.order import Order
from extensions import db

def fix_orders_for_assignment():
    """Update order statuses to make them assignable"""
    
    with app.app_context():
        try:
            print("🔧 Fixing orders for assignment...")
            print("=" * 60)
            
            # Get all pending orders
            pending_orders = Order.query.filter_by(status='pending').all()
            
            if not pending_orders:
                print("❌ No pending orders found!")
                return
            
            print(f"📊 Found {len(pending_orders)} pending orders")
            
            # Update first 5 orders to 'confirmed' status
            orders_to_update = pending_orders[:5]
            
            for i, order in enumerate(orders_to_update, 1):
                order.status = 'confirmed'
                print(f"✅ Updated Order #{order.id} ({order.order_number}) to 'confirmed' status")
            
            # Update next 3 orders to 'processing' status
            if len(pending_orders) > 5:
                orders_to_process = pending_orders[5:8]
                for i, order in enumerate(orders_to_process, 1):
                    order.status = 'processing'
                    print(f"✅ Updated Order #{order.id} ({order.order_number}) to 'processing' status")
            
            db.session.commit()
            print(f"\n🎉 Successfully updated {len(orders_to_update) + (len(orders_to_process) if len(pending_orders) > 5 else 0)} orders!")
            
            # Check the results
            print("\n📊 Updated Order Status Distribution:")
            all_orders = Order.query.all()
            status_counts = {}
            for order in all_orders:
                status = order.status
                status_counts[status] = status_counts.get(status, 0) + 1
            
            for status, count in status_counts.items():
                print(f"  - {status}: {count} orders")
            
            # Check unassigned orders
            unassigned_orders = Order.query.filter_by(delivery_guy_id=None).filter(
                Order.status.in_(['confirmed', 'processing'])
            ).all()
            
            print(f"\n📦 Unassigned orders (confirmed/processing): {len(unassigned_orders)}")
            
            if unassigned_orders:
                print("\n📋 Unassigned Orders Ready for Assignment:")
                for order in unassigned_orders:
                    print(f"  - Order #{order.id}: {order.order_number} | Status: {order.status} | Amount: ₹{order.total_amount}")
            
            print("=" * 60)
            
        except Exception as e:
            print(f"❌ Error fixing orders: {e}")
            db.session.rollback()
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    fix_orders_for_assignment()
