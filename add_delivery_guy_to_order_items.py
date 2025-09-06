#!/usr/bin/env python3
"""
Database migration script to add delivery_guy_id column to order_item table.
This enables individual product delivery assignment tracking.
"""

import sqlite3
import os
from datetime import datetime

def add_delivery_guy_to_order_items():
    """Add delivery_guy_id column to order_item table"""
    
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
        
        # Check if delivery_guy_id already exists
        if 'delivery_guy_id' in column_names:
            print("✅ delivery_guy_id column already exists in order_item table")
            return True
        
        print("➕ Adding delivery_guy_id column to order_item table...")
        
        # Add delivery_guy_id column
        cursor.execute("""
            ALTER TABLE order_item 
            ADD COLUMN delivery_guy_id INTEGER
        """)
        
        print("✅ delivery_guy_id column added to order_item table")
        
        # Create index for better performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_order_item_delivery_guy 
            ON order_item (delivery_guy_id)
        """)
        
        print("✅ Index created for delivery_guy_id")
        
        # Commit changes
        conn.commit()
        print("✅ Migration completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during migration: {str(e)}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

def create_order_history_table():
    """Create order_history table for tracking delivery assignments"""
    
    # Database path
    db_path = "zintoo.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database file {db_path} not found!")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 Checking if order_history table exists...")
        
        # Check if table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='order_history'
        """)
        
        if cursor.fetchone():
            print("✅ order_history table already exists")
            return True
        
        print("➕ Creating order_history table...")
        
        # Create order_history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                delivery_guy_id INTEGER NOT NULL,
                status VARCHAR(50) NOT NULL,
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES `order` (id),
                FOREIGN KEY (delivery_guy_id) REFERENCES delivery_onboarding (id)
            )
        """)
        
        print("✅ order_history table created")
        
        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_order_history_order 
            ON order_history (order_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_order_history_delivery_guy 
            ON order_history (delivery_guy_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_order_history_status 
            ON order_history (status)
        """)
        
        print("✅ Indexes created for order_history table")
        
        # Commit changes
        conn.commit()
        print("✅ order_history table creation completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating order_history table: {str(e)}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 Starting database migration for delivery assignment system...")
    print("=" * 60)
    
    # Add delivery_guy_id to order_items
    success1 = add_delivery_guy_to_order_items()
    
    print("\n" + "=" * 60)
    
    # Create order_history table
    success2 = create_order_history_table()
    
    print("\n" + "=" * 60)
    
    if success1 and success2:
        print("🎉 All migrations completed successfully!")
        print("✅ delivery_guy_id column added to order_item table")
        print("✅ order_history table created")
    else:
        print("❌ Some migrations failed. Please check the errors above.")
