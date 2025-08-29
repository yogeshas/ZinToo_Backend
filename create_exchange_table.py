#!/usr/bin/env python3
"""
Database migration script to create the exchange table
Run this script to add the exchange table to your database
"""

import sqlite3
import os

def create_exchange_table():
    """Create the exchange table in the database"""
    
    # Get the database path
    db_path = "zintoo.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database file {db_path} not found!")
        return False
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔧 Creating exchange table...")
        
        # Create the exchange table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exchange (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                order_item_id INTEGER NOT NULL,
                customer_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                old_size VARCHAR(20) NOT NULL,
                new_size VARCHAR(20) NOT NULL,
                reason TEXT,
                status VARCHAR(50) NOT NULL DEFAULT 'initiated',
                admin_notes TEXT,
                approved_by INTEGER,
                approved_at DATETIME,
                delivery_guy_id INTEGER,
                assigned_at DATETIME,
                delivered_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES "order" (id),
                FOREIGN KEY (order_item_id) REFERENCES order_item (id),
                FOREIGN KEY (customer_id) REFERENCES customer (id),
                FOREIGN KEY (product_id) REFERENCES product (id),
                FOREIGN KEY (approved_by) REFERENCES admin (id),
                FOREIGN KEY (delivery_guy_id) REFERENCES delivery_onboarding (id)
            )
        ''')
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_exchange_order_id ON exchange (order_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_exchange_customer_id ON exchange (customer_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_exchange_status ON exchange (status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_exchange_created_at ON exchange (created_at)')
        
        # Commit the changes
        conn.commit()
        
        print("✅ Exchange table created successfully!")
        
        # Verify the table was created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='exchange'")
        if cursor.fetchone():
            print("✅ Table verification successful!")
            
            # Show table structure
            cursor.execute("PRAGMA table_info(exchange)")
            columns = cursor.fetchall()
            print("\n📋 Exchange table structure:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
        else:
            print("❌ Table verification failed!")
            return False
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error creating exchange table: {str(e)}")
        if 'conn' in locals():
            conn.close()
        return False

def add_size_column_to_order_item():
    """Add size column to order_item table if it doesn't exist"""
    
    db_path = "zintoo.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if size column exists
        cursor.execute("PRAGMA table_info(order_item)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'size' not in columns:
            print("🔧 Adding size column to order_item table...")
            cursor.execute('ALTER TABLE order_item ADD COLUMN size VARCHAR(20)')
            conn.commit()
            print("✅ Size column added successfully!")
        else:
            print("ℹ️ Size column already exists in order_item table")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error adding size column: {str(e)}")
        if 'conn' in locals():
            conn.close()
        return False

if __name__ == "__main__":
    print("🚀 Starting exchange table migration...")
    print("=" * 50)
    
    # Create exchange table
    if create_exchange_table():
        print("\n✅ Exchange table migration completed successfully!")
    else:
        print("\n❌ Exchange table migration failed!")
        exit(1)
    
    # Add size column to order_item if needed
    if add_size_column_to_order_item():
        print("✅ Order item size column migration completed!")
    else:
        print("❌ Order item size column migration failed!")
    
    print("\n🎉 All migrations completed!")
    print("\nYou can now:")
    print("1. Restart your backend server")
    print("2. Use the exchange API endpoints")
    print("3. Manage exchanges from the admin panel")
