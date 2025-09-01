#!/usr/bin/env python3
"""
Script to create order tables in the SQLite database
"""

import sqlite3
import os

def create_order_tables():
    """Create order and order_item tables"""
    
    # Database path
    db_path = "zintoo.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database file {db_path} not found!")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 Creating order tables...")
        
        # Create order table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `order` (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                order_number VARCHAR(50) UNIQUE NOT NULL,
                status VARCHAR(20) DEFAULT 'pending' NOT NULL,
                delivery_address TEXT NOT NULL,
                delivery_type VARCHAR(20) NOT NULL,
                scheduled_time DATETIME,
                delivery_fee REAL DEFAULT 0.0,
                payment_method VARCHAR(20) NOT NULL,
                payment_id VARCHAR(100),
                payment_status VARCHAR(20) DEFAULT 'pending',
                subtotal REAL NOT NULL,
                delivery_fee_amount REAL DEFAULT 0.0,
                platform_fee REAL DEFAULT 0.0,
                discount_amount REAL DEFAULT 0.0,
                total_amount REAL NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                estimated_delivery DATETIME,
                delivery_guy_id INTEGER,
                assigned_at DATETIME,
                delivery_notes TEXT,
                is_exchange_delivery BOOLEAN DEFAULT 0
            )
        """)
        print("✅ Order table created")
        
        # Create order_item table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_item (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                total_price REAL NOT NULL,
                product_name VARCHAR(200) NOT NULL,
                product_image VARCHAR(500),
                selected_size VARCHAR(20),
                status VARCHAR(20) DEFAULT 'pending' NOT NULL,
                cancel_reason TEXT,
                cancel_requested_at DATETIME,
                cancelled_at DATETIME,
                cancelled_by VARCHAR(20),
                refund_status VARCHAR(20) DEFAULT 'not_applicable' NOT NULL,
                refund_amount REAL DEFAULT 0.0 NOT NULL,
                refund_reason TEXT,
                refund_requested_at DATETIME,
                refunded_at DATETIME,
                exchange_status VARCHAR(20) DEFAULT 'not_applicable' NOT NULL,
                exchange_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES `order` (id)
            )
        """)
        print("✅ Order_item table created")
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_order_customer ON `order` (customer_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_order_status ON `order` (status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_order_delivery_guy ON `order` (delivery_guy_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_order_item_order ON order_item (order_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_order_item_product ON order_item (product_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_order_item_status ON order_item (status)")
        print("✅ Indexes created")
        
        # Commit changes
        conn.commit()
        print("✅ All changes committed successfully!")
        
        # Verify tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        
        print(f"📋 Available tables: {table_names}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("🚀 Starting order tables creation...")
    print("=" * 50)
    
    success = create_order_tables()
    
    print("=" * 50)
    if success:
        print("🎉 Order tables created successfully!")
    else:
        print("💥 Failed to create order tables!")
