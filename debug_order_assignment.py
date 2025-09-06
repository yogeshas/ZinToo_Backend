#!/usr/bin/env python3
"""
Debug Order Assignment Script

This script helps debug order assignment issues by checking:
1. If order exists
2. If order has items
3. If items are assigned to delivery guys
4. If the specific delivery guy has items assigned
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from extensions import db
from models.order import Order, OrderItem
from models.delivery_onboarding import DeliveryOnboarding

def debug_order_assignment(order_id, delivery_guy_id=None):
    """Debug order assignment for a specific order and delivery guy"""
    
    print(f"🔍 Debugging Order Assignment")
    print(f"Order ID: {order_id}")
    if delivery_guy_id:
        print(f"Delivery Guy ID: {delivery_guy_id}")
    print("=" * 50)
    
    # Check if order exists
    order = Order.query.get(order_id)
    if not order:
        print(f"❌ Order {order_id} not found")
        return
    
    print(f"✅ Order {order_id} found")
    print(f"   Status: {order.status}")
    print(f"   Delivery Guy ID: {order.delivery_guy_id}")
    print(f"   Created: {order.created_at}")
    
    # Check order items
    items = OrderItem.query.filter_by(order_id=order_id).all()
    print(f"\n📦 Order Items ({len(items)} total):")
    
    if not items:
        print("   ❌ No items found in order")
        return
    
    assigned_items = []
    unassigned_items = []
    
    for item in items:
        item_delivery_guy_id = getattr(item, 'delivery_guy_id', None)
        item_status = getattr(item, 'status', 'unknown')
        
        print(f"   - Item {item.id}: {item.product_name}")
        print(f"     Delivery Guy ID: {item_delivery_guy_id}")
        print(f"     Status: {item_status}")
        
        if item_delivery_guy_id:
            assigned_items.append(item)
        else:
            unassigned_items.append(item)
    
    print(f"\n📊 Assignment Summary:")
    print(f"   Assigned items: {len(assigned_items)}")
    print(f"   Unassigned items: {len(unassigned_items)}")
    
    # If delivery guy ID provided, check specific assignments
    if delivery_guy_id:
        print(f"\n👤 Checking assignments for Delivery Guy {delivery_guy_id}:")
        
        # Check if delivery guy exists
        delivery_guy = DeliveryOnboarding.query.get(delivery_guy_id)
        if not delivery_guy:
            print(f"   ❌ Delivery guy {delivery_guy_id} not found")
            return
        
        print(f"   ✅ Delivery guy found: {delivery_guy.first_name} {delivery_guy.last_name}")
        print(f"   Status: {delivery_guy.status}")
        
        # Check items assigned to this delivery guy
        assigned_to_guy = OrderItem.query.filter_by(
            order_id=order_id,
            delivery_guy_id=delivery_guy_id
        ).all()
        
        print(f"   Items assigned to this delivery guy: {len(assigned_to_guy)}")
        
        if assigned_to_guy:
            for item in assigned_to_guy:
                print(f"     - Item {item.id}: {item.product_name} (Status: {getattr(item, 'status', 'unknown')})")
        else:
            print("     ❌ No items assigned to this delivery guy")
            
            # Suggest assignment
            if unassigned_items:
                print(f"\n💡 Suggestion: Assign {len(unassigned_items)} unassigned items to delivery guy {delivery_guy_id}")
                print("   You can use the admin panel to assign items to delivery personnel.")

def main():
    """Main function to run the debug script"""
    if len(sys.argv) < 2:
        print("Usage: python debug_order_assignment.py <order_id> [delivery_guy_id]")
        print("Example: python debug_order_assignment.py 31 5")
        return
    
    order_id = int(sys.argv[1])
    delivery_guy_id = int(sys.argv[2]) if len(sys.argv) > 2 else None
    
    debug_order_assignment(order_id, delivery_guy_id)

if __name__ == "__main__":
    main()
