#!/usr/bin/env python3
"""
Migration script to add payment tracking columns for return delivery
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from extensions import db

def add_payment_tracking_columns():
    """Add payment tracking columns to order_item table"""
    with app.app_context():
        try:
            with db.engine.connect() as connection:
                # Check if payment_return_delivery_id column exists
                result = connection.execute(db.text("""
                    SELECT COLUMN_NAME 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME = 'order_item' 
                    AND COLUMN_NAME = 'payment_return_delivery_id'
                """))
                
                if not result.fetchone():
                    print("Adding payment_return_delivery_id column...")
                    connection.execute(db.text("""
                        ALTER TABLE order_item 
                        ADD COLUMN payment_return_delivery_id VARCHAR(100) NULL
                    """))
                    print("✅ payment_return_delivery_id column added")
                else:
                    print("✅ payment_return_delivery_id column already exists")
                
                # Check if payment_return_delivery_method column exists
                result = connection.execute(db.text("""
                    SELECT COLUMN_NAME 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME = 'order_item' 
                    AND COLUMN_NAME = 'payment_return_delivery_method'
                """))
                
                if not result.fetchone():
                    print("Adding payment_return_delivery_method column...")
                    connection.execute(db.text("""
                        ALTER TABLE order_item 
                        ADD COLUMN payment_return_delivery_method VARCHAR(50) NULL
                    """))
                    print("✅ payment_return_delivery_method column added")
                else:
                    print("✅ payment_return_delivery_method column already exists")
                
                connection.commit()
                print("🎉 Payment tracking columns migration completed successfully!")
                
        except Exception as e:
            print(f"❌ Error adding payment tracking columns: {e}")
            raise

if __name__ == "__main__":
    add_payment_tracking_columns()
