#!/usr/bin/env python3
"""
Migration script to add return_pickup_time column to order_item table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from extensions import db

def add_return_pickup_time_column():
    """Add return_pickup_time column to order_item table"""
    try:
        with app.app_context():
            # Check if column already exists
            with db.engine.connect() as connection:
                # Check if return_pickup_time column exists
                result = connection.execute(db.text("""
                    SELECT COUNT(*) as count 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME = 'order_item' 
                    AND COLUMN_NAME = 'return_pickup_time'
                """))
                column_exists = result.fetchone()[0] > 0
                
                print(f"return_pickup_time column exists: {column_exists}")
                
                # Add return_pickup_time column if it doesn't exist
                if not column_exists:
                    print("Adding return_pickup_time column to order_item table...")
                    connection.execute(db.text("ALTER TABLE order_item ADD COLUMN return_pickup_time DATETIME"))
                    connection.commit()
                    print("✅ return_pickup_time column added successfully!")
                else:
                    print("ℹ️ return_pickup_time column already exists")
                
                print("🎉 Migration completed successfully!")
                return True
                
    except Exception as e:
        print(f"❌ Error adding return_pickup_time column to order_item table: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting return_pickup_time column migration...")
    success = add_return_pickup_time_column()
    if success:
        print("✅ Migration completed successfully!")
    else:
        print("❌ Migration failed!")
        sys.exit(1)
