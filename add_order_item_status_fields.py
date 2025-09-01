#!/usr/bin/env python3
"""
Database migration script to add individual product status tracking to order_item table.
This enables individual product cancellation, refund, and exchange tracking.
"""

import sqlite3
import os
from datetime import datetime

def add_order_item_status_fields():
    """Add new status tracking fields to order_item table"""
    
    # Database path
    db_path = "zintoo.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database file {db_path} not found!")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 Checking current order_item table structure...")
        
        # Check current table structure
        cursor.execute("PRAGMA table_info(order_item)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print(f"📋 Current columns: {column_names}")
        
        # Fields to add
        new_fields = [
            ("status", "TEXT DEFAULT 'pending' NOT NULL"),
            ("cancel_reason", "TEXT"),
            ("cancel_requested_at", "DATETIME"),
            ("cancelled_at", "DATETIME"),
            ("cancelled_by", "TEXT"),
            ("refund_status", "TEXT DEFAULT 'not_applicable' NOT NULL"),
            ("refund_amount", "REAL DEFAULT 0.0 NOT NULL"),
            ("refund_reason", "TEXT"),
            ("refund_requested_at", "DATETIME"),
            ("refunded_at", "DATETIME"),
            ("exchange_status", "TEXT DEFAULT 'not_applicable' NOT NULL"),
            ("exchange_id", "INTEGER"),
            ("updated_at", "DATETIME DEFAULT CURRENT_TIMESTAMP")
        ]
        
        # Add new fields
        for field_name, field_type in new_fields:
            if field_name not in column_names:
                print(f"➕ Adding field: {field_name}")
                try:
                    cursor.execute(f"ALTER TABLE order_item ADD COLUMN {field_name} {field_type}")
                    print(f"✅ Added {field_name}")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e).lower():
                        print(f"⚠️ Field {field_name} already exists, skipping...")
                    else:
                        print(f"❌ Error adding {field_name}: {e}")
            else:
                print(f"✅ Field {field_name} already exists")
        
        # Update existing records to set default status
        print("🔄 Updating existing order items with default status...")
        cursor.execute("""
            UPDATE order_item 
            SET status = 'pending', 
                refund_status = 'not_applicable',
                exchange_status = 'not_applicable',
                updated_at = CURRENT_TIMESTAMP
            WHERE status IS NULL
        """)
        
        updated_count = cursor.rowcount
        print(f"✅ Updated {updated_count} existing order items")
        
        # Commit changes
        conn.commit()
        print("✅ All changes committed successfully!")
        
        # Verify final structure
        cursor.execute("PRAGMA table_info(order_item)")
        final_columns = cursor.fetchall()
        final_column_names = [col[1] for col in final_columns]
        
        print(f"📋 Final table structure: {final_column_names}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("🚀 Starting OrderItem status fields migration...")
    print("=" * 50)
    
    success = add_order_item_status_fields()
    
    print("=" * 50)
    if success:
        print("🎉 Migration completed successfully!")
    else:
        print("💥 Migration failed!")
