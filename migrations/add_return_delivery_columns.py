#!/usr/bin/env python3
"""
Migration script to add return delivery columns to order_item table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from extensions import db

def add_return_delivery_columns():
    """Add return delivery columns to order_item table"""
    try:
        with app.app_context():
            with db.engine.connect() as connection:
                # Check if columns already exist
                result = connection.execute(db.text("""
                    SELECT COUNT(*) as count 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME = 'order_item' 
                    AND COLUMN_NAME IN ('return_pickup_time_from', 'return_pickup_time_to', 'return_delivery_status', 'payment_return_delivery')
                """))
                existing_columns = result.fetchone()[0]
                
                print(f"Existing return delivery columns: {existing_columns}")
                
                # Add return_pickup_time_from column if it doesn't exist
                if existing_columns < 4:
                    print("Adding return delivery columns to order_item table...")
                    
                    # Add return_pickup_time_from column
                    connection.execute(db.text("ALTER TABLE order_item ADD COLUMN return_pickup_time_from DATETIME"))
                    print("✅ return_pickup_time_from column added")
                    
                    # Add return_pickup_time_to column
                    connection.execute(db.text("ALTER TABLE order_item ADD COLUMN return_pickup_time_to DATETIME"))
                    print("✅ return_pickup_time_to column added")
                    
                    # Add return_delivery_status column
                    connection.execute(db.text("ALTER TABLE order_item ADD COLUMN return_delivery_status VARCHAR(20) DEFAULT 'not_applicable' NOT NULL"))
                    print("✅ return_delivery_status column added")
                    
                    # Add payment_return_delivery column
                    connection.execute(db.text("ALTER TABLE order_item ADD COLUMN payment_return_delivery FLOAT DEFAULT 0.0 NOT NULL"))
                    print("✅ payment_return_delivery column added")
                    
                    connection.commit()
                    print("✅ All return delivery columns added successfully!")
                else:
                    print("ℹ️ Return delivery columns already exist")
                
                print("🎉 Migration completed successfully!")
                return True
                
    except Exception as e:
        print(f"❌ Error adding return delivery columns to order_item table: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting return delivery columns migration...")
    success = add_return_delivery_columns()
    if success:
        print("✅ Migration completed successfully!")
    else:
        print("❌ Migration failed!")
        sys.exit(1)
