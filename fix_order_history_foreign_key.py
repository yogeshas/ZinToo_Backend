#!/usr/bin/env python3
"""
Fix the order_history table foreign key constraint to reference delivery_onboarding instead of delivery_guy
"""

import sqlite3
import os

def fix_order_history_foreign_key():
    """Fix the foreign key constraint in order_history table"""
    
    # Database path
    db_path = "zintoo.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database file {db_path} not found!")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 Checking current order_history table structure...")
        
        # Check if table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='order_history'
        """)
        
        if not cursor.fetchone():
            print("❌ order_history table does not exist")
            return False
        
        print("🗑️ Dropping existing order_history table...")
        cursor.execute("DROP TABLE order_history")
        
        print("➕ Creating order_history table with correct foreign key...")
        
        # Create order_history table with correct foreign key
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
        
        print("✅ order_history table recreated with correct foreign key")
        
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
        print("✅ Foreign key fix completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing foreign key: {str(e)}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 Fixing order_history table foreign key constraint...")
    print("=" * 60)
    
    success = fix_order_history_foreign_key()
    
    if success:
        print("🎉 Foreign key fix completed successfully!")
        print("✅ order_history table now references delivery_onboarding table")
    else:
        print("❌ Foreign key fix failed. Please check the errors above.")
