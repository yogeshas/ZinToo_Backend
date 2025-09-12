#!/usr/bin/env python3
"""
Check database status directly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import mysql.connector
from config import Config

def check_order_items():
    """Check order items in database"""
    try:
        # Connect to database
        connection = mysql.connector.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )
        
        cursor = connection.cursor()
        
        # First, check if there are any order items at all
        check_query = "SELECT COUNT(*) FROM order_item"
        cursor.execute(check_query)
        total_count = cursor.fetchone()[0]
        print(f"Total order items in database: {total_count}")
        
        if total_count == 0:
            print("No order items found in database")
            return
        
        # Get some sample order items
        sample_query = """
        SELECT id, order_id, product_name, quantity, quantity_cancel, status
        FROM order_item 
        ORDER BY id DESC
        LIMIT 5
        """
        
        cursor.execute(sample_query)
        sample_results = cursor.fetchall()
        
        print("\nSample Order Items:")
        print("=" * 60)
        for row in sample_results:
            id, order_id, product_name, quantity, quantity_cancel, status = row
            print(f"ID: {id}, Order: {order_id}, Product: {product_name[:20]}, Qty: {quantity}, Cancel: {quantity_cancel}, Status: {status}")
        
        # Get order items with cancellation info
        query = """
        SELECT id, order_id, product_name, quantity, quantity_cancel, status, 
               cancel_reason, cancelled_at
        FROM order_item 
        WHERE quantity_cancel > 0
        ORDER BY updated_at DESC
        LIMIT 10
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        print("Order Items with Cancellations:")
        print("=" * 80)
        print(f"{'ID':<5} {'Order':<8} {'Product':<20} {'Qty':<5} {'Cancel':<8} {'Status':<12} {'Reason':<15}")
        print("-" * 80)
        
        for row in results:
            id, order_id, product_name, quantity, quantity_cancel, status, cancel_reason, cancelled_at = row
            print(f"{id:<5} {order_id:<8} {product_name[:20]:<20} {quantity:<5} {quantity_cancel:<8} {status:<12} {cancel_reason or 'N/A':<15}")
        
        # Check for fully cancelled items
        print("\nFully Cancelled Items (quantity_cancel >= quantity):")
        print("=" * 60)
        
        query2 = """
        SELECT id, order_id, product_name, quantity, quantity_cancel, status
        FROM order_item 
        WHERE quantity_cancel >= quantity
        ORDER BY updated_at DESC
        LIMIT 5
        """
        
        cursor.execute(query2)
        results2 = cursor.fetchall()
        
        for row in results2:
            id, order_id, product_name, quantity, quantity_cancel, status = row
            should_be_cancelled = quantity_cancel >= quantity
            print(f"ID: {id}, Product: {product_name[:30]}, Qty: {quantity}, Cancelled: {quantity_cancel}, Status: {status}, Should be cancelled: {should_be_cancelled}")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_order_items()
