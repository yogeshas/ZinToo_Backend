#!/usr/bin/env python3
"""
MySQL migration script to add delivery_guy_id column to order_item table.
This enables individual product delivery assignment tracking.
"""

import mysql.connector
import os
from datetime import datetime

def get_mysql_connection():
    """Get MySQL database connection"""
    try:
        # Get database credentials from environment or use defaults
        host = os.getenv('DB_HOST', 'localhost')
        user = os.getenv('DB_USER', 'root')
        password = os.getenv('DB_PASSWORD', '')
        database = os.getenv('DB_NAME', 'zintoo')
        port = int(os.getenv('DB_PORT', 3306))
        
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port
        )
        return connection
    except Exception as e:
        print(f"❌ Error connecting to MySQL: {e}")
        return None

def add_delivery_guy_to_order_items_mysql():
    """Add delivery_guy_id column to order_item table in MySQL"""
    
    connection = get_mysql_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        
        print("🔍 Checking current order_item table structure...")
        
        # Check current table structure
        cursor.execute("DESCRIBE order_item")
        columns = cursor.fetchall()
        column_names = [col[0] for col in columns]
        
        print(f"📋 Current columns: {column_names}")
        
        # Check if delivery_guy_id already exists
        if 'delivery_guy_id' in column_names:
            print("✅ delivery_guy_id column already exists in order_item table")
            return True
        
        print("➕ Adding delivery_guy_id column to order_item table...")
        
        # Add delivery_guy_id column
        cursor.execute("""
            ALTER TABLE order_item 
            ADD COLUMN delivery_guy_id INT NULL
        """)
        
        print("✅ delivery_guy_id column added to order_item table")
        
        # Create index for better performance
        cursor.execute("""
            CREATE INDEX idx_order_item_delivery_guy 
            ON order_item (delivery_guy_id)
        """)
        
        print("✅ Index created for delivery_guy_id")
        
        # Commit changes
        connection.commit()
        print("✅ Migration completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during migration: {str(e)}")
        connection.rollback()
        return False
        
    finally:
        connection.close()

def create_order_history_table_mysql():
    """Create order_history table for tracking delivery assignments in MySQL"""
    
    connection = get_mysql_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        
        print("🔍 Checking if order_history table exists...")
        
        # Check if table exists
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = DATABASE() 
            AND table_name = 'order_history'
        """)
        
        if cursor.fetchone()[0] > 0:
            print("✅ order_history table already exists")
            return True
        
        print("➕ Creating order_history table...")
        
        # Create order_history table
        cursor.execute("""
            CREATE TABLE order_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                order_id INT NOT NULL,
                delivery_guy_id INT NOT NULL,
                status VARCHAR(50) NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES `order` (id),
                FOREIGN KEY (delivery_guy_id) REFERENCES delivery_onboarding (id)
            )
        """)
        
        print("✅ order_history table created")
        
        # Create indexes
        cursor.execute("""
            CREATE INDEX idx_order_history_order 
            ON order_history (order_id)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_order_history_delivery_guy 
            ON order_history (delivery_guy_id)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_order_history_status 
            ON order_history (status)
        """)
        
        print("✅ Indexes created for order_history table")
        
        # Commit changes
        connection.commit()
        print("✅ order_history table creation completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating order_history table: {str(e)}")
        connection.rollback()
        return False
        
    finally:
        connection.close()

if __name__ == "__main__":
    print("🚀 Starting MySQL database migration for delivery assignment system...")
    print("=" * 60)
    
    # Add delivery_guy_id to order_items
    success1 = add_delivery_guy_to_order_items_mysql()
    
    print("\n" + "=" * 60)
    
    # Create order_history table
    success2 = create_order_history_table_mysql()
    
    print("\n" + "=" * 60)
    
    if success1 and success2:
        print("🎉 All MySQL migrations completed successfully!")
        print("✅ delivery_guy_id column added to order_item table")
        print("✅ order_history table created")
    else:
        print("❌ Some migrations failed. Please check the errors above.")
