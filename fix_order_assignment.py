#!/usr/bin/env python3
"""
Fix Order Assignment Script

This script helps fix order assignment issues by:
1. Assigning unassigned items to delivery guys
2. Updating order status based on item assignments
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from extensions import db
from models.order import Order, OrderItem
from models.delivery_onboarding import DeliveryOnboarding
from datetime import datetime

def assign_items_to_delivery_guy(order_id, delivery_guy_id, item_ids=None):
    """Assign specific items or all unassigned items to a delivery guy"""
    
    print(f"🔧 Fixing Order Assignment")
    print(f"Order ID: {order_id}")
    print(f"Delivery Guy ID: {delivery_guy_id}")
    print("=" * 50)
    
    # Check if order exists
    order = Order.query.get(order_id)
    if not order:
        print(f"❌ Order {order_id} not found")
        return False
    
    # Check if delivery guy exists
    delivery_guy = DeliveryOnboarding.query.get(delivery_guy_id)
    if not delivery_guy:
        print(f"❌ Delivery guy {delivery_guy_id} not found")
        return False
    
    print(f"✅ Order: {order.order_number}")
    print(f"✅ Delivery Guy: {delivery_guy.first_name} {delivery_guy.last_name}")
    
    # Get items to assign
    if item_ids:
        items = OrderItem.query.filter(
            OrderItem.order_id == order_id,
            OrderItem.id.in_(item_ids)
        ).all()
    else:
        # Get all unassigned items
        items = OrderItem.query.filter(
            OrderItem.order_id == order_id,
            OrderItem.delivery_guy_id.is_(None)
        ).all()
    
    if not items:
        print("❌ No items to assign")
        return False
    
    print(f"📦 Assigning {len(items)} items:")
    
    # Assign items
    for item in items:
        old_delivery_guy_id = getattr(item, 'delivery_guy_id', None)
        item.delivery_guy_id = delivery_guy_id
        item.status = 'assigned'
        item.updated_at = datetime.utcnow()
        
        print(f"   - Item {item.id}: {item.product_name}")
        print(f"     From: {old_delivery_guy_id} → To: {delivery_guy_id}")
    
    # Update order status
    all_items = OrderItem.query.filter_by(order_id=order_id).all()
    assigned_count = len([item for item in all_items if item.delivery_guy_id])
    
    if assigned_count == len(all_items):
        order.status = 'assigned'
        print(f"✅ Updated order status to 'assigned'")
    elif assigned_count > 0:
        order.status = 'processing'
        print(f"✅ Updated order status to 'processing' (partial assignment)")
    
    order.updated_at = datetime.utcnow()
    
    # Add assignment note
    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    assignment_note = f"\n[ASSIGNED] {timestamp} - Items assigned to {delivery_guy.first_name} {delivery_guy.last_name} (ID: {delivery_guy_id})"
    order.delivery_notes = (order.delivery_notes or "") + assignment_note
    
    try:
        db.session.commit()
        print(f"✅ Successfully assigned {len(items)} items to delivery guy {delivery_guy_id}")
        return True
    except Exception as e:
        db.session.rollback()
        print(f"❌ Failed to assign items: {e}")
        return False

def main():
    """Main function to run the fix script"""
    if len(sys.argv) < 3:
        print("Usage: python fix_order_assignment.py <order_id> <delivery_guy_id> [item_id1,item_id2,...]")
        print("Example: python fix_order_assignment.py 31 5")
        print("Example: python fix_order_assignment.py 31 5 1,2,3")
        return
    
    order_id = int(sys.argv[1])
    delivery_guy_id = int(sys.argv[2])
    item_ids = None
    
    if len(sys.argv) > 3:
        item_ids = [int(x.strip()) for x in sys.argv[3].split(',')]
    
    assign_items_to_delivery_guy(order_id, delivery_guy_id, item_ids)

if __name__ == "__main__":
    main()
