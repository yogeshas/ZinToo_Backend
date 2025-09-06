#!/usr/bin/env python3
"""
Fix for Delivery Orders API - Debug and Fix Issues

This script helps debug and fix the delivery orders API issues where
delivery personnel are not seeing their assigned orders.
"""

import sqlite3
import os
from datetime import datetime

def debug_delivery_orders():
    """Debug delivery orders assignment and API issues"""
    
    db_path = "zintoo.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database file {db_path} not found!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 Debugging Delivery Orders API Issues...")
        print("=" * 60)
        
        # 1. Check delivery onboarding records
        print("\n1. 📋 Delivery Onboarding Records:")
        cursor.execute("""
            SELECT id, first_name, last_name, email, phone_number, status, created_at 
            FROM delivery_onboarding 
            ORDER BY id DESC
        """)
        onboarding_records = cursor.fetchall()
        
        if onboarding_records:
            print(f"   Found {len(onboarding_records)} delivery onboarding records:")
            for record in onboarding_records:
                print(f"   - ID: {record[0]}, Name: {record[1]} {record[2]}, Email: {record[3]}, Status: {record[4]}")
        else:
            print("   ❌ No delivery onboarding records found!")
        
        # 2. Check orders with delivery assignments
        print("\n2. 📦 Orders with Delivery Assignments:")
        cursor.execute("""
            SELECT id, order_number, status, delivery_guy_id, assigned_at, created_at 
            FROM "order" 
            WHERE delivery_guy_id IS NOT NULL 
            ORDER BY id DESC
        """)
        assigned_orders = cursor.fetchall()
        
        if assigned_orders:
            print(f"   Found {len(assigned_orders)} orders with delivery assignments:")
            for order in assigned_orders:
                print(f"   - Order ID: {order[0]}, Number: {order[1]}, Status: {order[2]}, Delivery Guy ID: {order[3]}")
        else:
            print("   ❌ No orders with delivery assignments found!")
        
        # 3. Check order items with delivery assignments
        print("\n3. 📦 Order Items with Delivery Assignments:")
        cursor.execute("""
            SELECT id, order_id, product_name, status, delivery_guy_id, created_at 
            FROM order_item 
            WHERE delivery_guy_id IS NOT NULL 
            ORDER BY id DESC
        """)
        assigned_items = cursor.fetchall()
        
        if assigned_items:
            print(f"   Found {len(assigned_items)} order items with delivery assignments:")
            for item in assigned_items:
                print(f"   - Item ID: {item[0]}, Order ID: {item[1]}, Product: {item[2]}, Status: {item[3]}, Delivery Guy ID: {item[4]}")
        else:
            print("   ❌ No order items with delivery assignments found!")
        
        # 4. Check for mismatched assignments
        print("\n4. 🔍 Checking for Assignment Mismatches:")
        cursor.execute("""
            SELECT o.id, o.order_number, o.delivery_guy_id as order_delivery_guy,
                   oi.id as item_id, oi.delivery_guy_id as item_delivery_guy
            FROM "order" o
            LEFT JOIN order_item oi ON o.id = oi.order_id
            WHERE o.delivery_guy_id IS NOT NULL OR oi.delivery_guy_id IS NOT NULL
            ORDER BY o.id DESC
        """)
        mismatches = cursor.fetchall()
        
        if mismatches:
            print("   Checking for mismatches between order and item assignments:")
            for mismatch in mismatches:
                order_id, order_number, order_delivery_guy, item_id, item_delivery_guy = mismatch
                if order_delivery_guy != item_delivery_guy:
                    print(f"   ⚠️  MISMATCH - Order {order_number}: Order assigned to {order_delivery_guy}, Item {item_id} assigned to {item_delivery_guy}")
        
        # 5. Check recent orders without assignments
        print("\n5. 📋 Recent Orders Without Assignments:")
        cursor.execute("""
            SELECT id, order_number, status, created_at 
            FROM "order" 
            WHERE delivery_guy_id IS NULL 
            AND status IN ('pending', 'confirmed', 'processing', 'shipped')
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        unassigned_orders = cursor.fetchall()
        
        if unassigned_orders:
            print(f"   Found {len(unassigned_orders)} recent unassigned orders:")
            for order in unassigned_orders:
                print(f"   - Order ID: {order[0]}, Number: {order[1]}, Status: {order[2]}, Created: {order[3]}")
        else:
            print("   ✅ No recent unassigned orders found!")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error debugging delivery orders: {str(e)}")
        if 'conn' in locals():
            conn.close()
        return False

def fix_delivery_assignments():
    """Fix common delivery assignment issues"""
    
    db_path = "zintoo.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database file {db_path} not found!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\n🔧 Fixing Delivery Assignment Issues...")
        print("=" * 60)
        
        # 1. Sync order and order_item delivery assignments
        print("\n1. 🔄 Syncing Order and Order Item Assignments:")
        cursor.execute("""
            UPDATE order_item 
            SET delivery_guy_id = (
                SELECT delivery_guy_id 
                FROM "order" 
                WHERE "order".id = order_item.order_id 
                AND "order".delivery_guy_id IS NOT NULL
            )
            WHERE order_id IN (
                SELECT id FROM "order" WHERE delivery_guy_id IS NOT NULL
            )
            AND delivery_guy_id IS NULL
        """)
        updated_items = cursor.rowcount
        print(f"   ✅ Updated {updated_items} order items with delivery assignments")
        
        # 2. Update order status for assigned orders
        print("\n2. 📝 Updating Order Status for Assigned Orders:")
        cursor.execute("""
            UPDATE "order" 
            SET status = 'assigned' 
            WHERE delivery_guy_id IS NOT NULL 
            AND status = 'pending'
        """)
        updated_orders = cursor.rowcount
        print(f"   ✅ Updated {updated_orders} orders to 'assigned' status")
        
        # 3. Update order item status for assigned items
        print("\n3. 📝 Updating Order Item Status for Assigned Items:")
        cursor.execute("""
            UPDATE order_item 
            SET status = 'assigned' 
            WHERE delivery_guy_id IS NOT NULL 
            AND status = 'pending'
        """)
        updated_item_status = cursor.rowcount
        print(f"   ✅ Updated {updated_item_status} order items to 'assigned' status")
        
        conn.commit()
        conn.close()
        
        print("\n✅ Delivery assignment fixes completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing delivery assignments: {str(e)}")
        if 'conn' in locals():
            conn.close()
        return False

def create_test_delivery_assignment():
    """Create a test delivery assignment for debugging"""
    
    db_path = "zintoo.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database file {db_path} not found!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\n🧪 Creating Test Delivery Assignment...")
        print("=" * 60)
        
        # Get the first approved delivery guy
        cursor.execute("""
            SELECT id, first_name, last_name, email 
            FROM delivery_onboarding 
            WHERE status = 'approved' 
            LIMIT 1
        """)
        delivery_guy = cursor.fetchone()
        
        if not delivery_guy:
            print("   ❌ No approved delivery guys found!")
            return False
        
        delivery_guy_id, first_name, last_name, email = delivery_guy
        print(f"   📋 Using delivery guy: {first_name} {last_name} (ID: {delivery_guy_id})")
        
        # Get the first unassigned order
        cursor.execute("""
            SELECT id, order_number, status 
            FROM "order" 
            WHERE delivery_guy_id IS NULL 
            AND status IN ('pending', 'confirmed', 'processing')
            LIMIT 1
        """)
        order = cursor.fetchone()
        
        if not order:
            print("   ❌ No unassigned orders found!")
            return False
        
        order_id, order_number, status = order
        print(f"   📦 Using order: {order_number} (ID: {order_id}, Status: {status})")
        
        # Assign the order to the delivery guy
        cursor.execute("""
            UPDATE "order" 
            SET delivery_guy_id = ?, 
                assigned_at = CURRENT_TIMESTAMP,
                status = 'assigned'
            WHERE id = ?
        """, (delivery_guy_id, order_id))
        
        # Assign all order items to the delivery guy
        cursor.execute("""
            UPDATE order_item 
            SET delivery_guy_id = ?, 
                status = 'assigned'
            WHERE order_id = ?
        """, (delivery_guy_id, order_id))
        
        conn.commit()
        conn.close()
        
        print(f"   ✅ Successfully assigned order {order_number} to delivery guy {first_name} {last_name}")
        print(f"   🔑 Delivery Guy ID for testing: {delivery_guy_id}")
        print(f"   📦 Order ID for testing: {order_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating test assignment: {str(e)}")
        if 'conn' in locals():
            conn.close()
        return False

def main():
    """Main function to run all debugging and fixes"""
    
    print("🚀 Delivery Orders API Debug and Fix Tool")
    print("=" * 60)
    
    # Step 1: Debug current state
    if not debug_delivery_orders():
        return
    
    # Step 2: Fix common issues
    if not fix_delivery_assignments():
        return
    
    # Step 3: Create test assignment
    if not create_test_delivery_assignment():
        return
    
    print("\n🎉 All fixes completed successfully!")
    print("\n📋 Next Steps:")
    print("1. Test the delivery orders API with the delivery guy ID shown above")
    print("2. Check if orders are now visible in the mobile app")
    print("3. If issues persist, check the authentication token generation")

if __name__ == "__main__":
    main()
