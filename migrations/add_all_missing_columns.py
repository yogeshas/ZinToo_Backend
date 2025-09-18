#!/usr/bin/env python3
"""
Migration script to add all missing columns to order_item table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from extensions import db

def add_missing_columns():
    """Add all missing columns to order_item table"""
    try:
        with app.app_context():
            with db.engine.connect() as connection:
                # List of columns to add
                columns_to_add = [
                    ("return_pickup_time_from", "DATETIME"),
                    ("return_pickup_time_to", "DATETIME"),
                    ("return_delivery_status", "VARCHAR(50)"),
                    ("payment_return_delivery", "DECIMAL(10,2)"),
                    ("payment_return_delivery_id", "VARCHAR(255)"),
                    ("payment_return_delivery_method", "VARCHAR(50)"),
                    ("refund_status", "VARCHAR(50)"),
                    ("refund_amount", "DECIMAL(10,2)"),
                    ("refund_reason", "TEXT"),
                    ("refund_requested_at", "DATETIME"),
                    ("refunded_at", "DATETIME"),
                    ("exchange_status", "VARCHAR(50)"),
                    ("exchange_id", "INT"),
                    ("delivery_guy_id", "INT")
                ]
                
                for column_name, column_type in columns_to_add:
                    # Check if column exists
                    result = connection.execute(db.text(f"""
                        SELECT COUNT(*) as count 
                        FROM INFORMATION_SCHEMA.COLUMNS 
                        WHERE TABLE_NAME = 'order_item' 
                        AND COLUMN_NAME = '{column_name}'
                    """))
                    column_exists = result.fetchone()[0] > 0
                    
                    if not column_exists:
                        print(f"Adding {column_name} column to order_item table...")
                        connection.execute(db.text(f"ALTER TABLE order_item ADD COLUMN {column_name} {column_type}"))
                        connection.commit()
                        print(f"✅ {column_name} column added successfully!")
                    else:
                        print(f"ℹ️ {column_name} column already exists")
                
                print("🎉 All missing columns migration completed successfully!")
                return True
                
    except Exception as e:
        print(f"❌ Error adding missing columns to order_item table: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting missing columns migration...")
    success = add_missing_columns()
    if success:
        print("✅ Migration completed successfully!")
    else:
        print("❌ Migration failed!")
        sys.exit(1)
