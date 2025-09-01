#!/usr/bin/env python3
"""
Migration script to add size-based inventory support to existing tables.
This script adds the new fields needed for size-based quantity management.
"""

import sqlite3
import json
from datetime import datetime

def migrate_database():
    """Migrate the database to support size-based inventory"""
    
    # Connect to the database
    conn = sqlite3.connect('zintoo.db')
    cursor = conn.cursor()
    
    print("🔧 Starting size-based inventory migration...")
    
    try:
        # 1. Add selected_size column to cart table
        print("📦 Adding selected_size to cart table...")
        try:
            cursor.execute("""
                ALTER TABLE cart 
                ADD COLUMN selected_size VARCHAR(20)
            """)
            print("✅ selected_size column added to cart table")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("ℹ️ selected_size column already exists in cart table")
            else:
                raise e
        
        # 2. Add selected_size column to order_item table
        print("📋 Adding selected_size to order_item table...")
        try:
            cursor.execute("""
                ALTER TABLE order_item 
                ADD COLUMN selected_size VARCHAR(20)
            """)
            print("✅ selected_size column added to order_item table")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("ℹ️ selected_size column already exists in order_item table")
            else:
                raise e
        
        # 3. Add new columns to exchange table
        print("🔄 Adding new columns to exchange table...")
        
        # Check if exchange table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='exchange'
        """)
        
        if cursor.fetchone():
            # Table exists, add new columns
            new_columns = [
                ("old_quantity", "INTEGER DEFAULT 1"),
                ("new_quantity", "INTEGER DEFAULT 1"),
                ("additional_payment_required", "BOOLEAN DEFAULT FALSE"),
                ("additional_amount", "REAL DEFAULT 0.0")
            ]
            
            for column_name, column_def in new_columns:
                try:
                    cursor.execute(f"""
                        ALTER TABLE exchange 
                        ADD COLUMN {column_name} {column_def}
                    """)
                    print(f"✅ {column_name} column added to exchange table")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e):
                        print(f"ℹ️ {column_name} column already exists in exchange table")
                    else:
                        raise e
        else:
            # Create exchange table with all new columns
            print("📋 Creating exchange table with new structure...")
            cursor.execute("""
                CREATE TABLE exchange (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    order_item_id INTEGER NOT NULL,
                    customer_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    old_size VARCHAR(20) NOT NULL,
                    new_size VARCHAR(20) NOT NULL,
                    old_quantity INTEGER NOT NULL DEFAULT 1,
                    new_quantity INTEGER NOT NULL DEFAULT 1,
                    reason TEXT,
                    additional_payment_required BOOLEAN DEFAULT FALSE,
                    additional_amount REAL DEFAULT 0.0,
                    status VARCHAR(50) NOT NULL DEFAULT 'initiated',
                    admin_notes TEXT,
                    approved_by INTEGER,
                    approved_at DATETIME,
                    delivery_guy_id INTEGER,
                    assigned_at DATETIME,
                    delivered_at DATETIME,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ Exchange table created with new structure")
        
        # 4. Update existing products to have proper size structure
        print("🏷️ Updating existing products with size structure...")
        cursor.execute("SELECT id, size FROM product WHERE size IS NOT NULL AND size != ''")
        products = cursor.fetchall()
        
        updated_count = 0
        for product_id, current_size in products:
            try:
                # Try to parse existing size data
                if current_size and current_size.strip():
                    # If it's already JSON, skip
                    if current_size.strip().startswith('{'):
                        continue
                    
                    # Try to convert legacy format to JSON
                    try:
                        # Handle legacy formats like "S:3,M:0,L:5" or similar
                        if ':' in current_size:
                            size_parts = current_size.split(',')
                            size_dict = {}
                            for part in size_parts:
                                if ':' in part:
                                    size_name, quantity = part.split(':', 1)
                                    size_dict[size_name.strip()] = int(quantity.strip())
                            
                            if size_dict:
                                new_size_json = json.dumps(size_dict)
                                cursor.execute("""
                                    UPDATE product 
                                    SET size = ? 
                                    WHERE id = ?
                                """, (new_size_json, product_id))
                                updated_count += 1
                                print(f"🔄 Updated product {product_id} size format")
                        else:
                            # Single size with quantity, convert to dict
                            size_dict = {current_size.strip(): 1}
                            new_size_json = json.dumps(size_dict)
                            cursor.execute("""
                                UPDATE product 
                                SET size = ? 
                                    WHERE id = ?
                                """, (new_size_json, product_id))
                            updated_count += 1
                            print(f"🔄 Updated product {product_id} size format")
                    except Exception as e:
                        print(f"⚠️ Could not parse size for product {product_id}: {e}")
                        continue
                        
            except Exception as e:
                print(f"⚠️ Error updating product {product_id}: {e}")
                continue
        
        print(f"✅ Updated {updated_count} products with new size format")
        
        # 5. Create indexes for better performance
        print("📊 Creating indexes for better performance...")
        
        indexes = [
            ("idx_cart_size", "cart", "selected_size"),
            ("idx_order_item_size", "order_item", "selected_size"),
            ("idx_exchange_status", "exchange", "status"),
            ("idx_exchange_customer", "exchange", "customer_id"),
            ("idx_exchange_order", "exchange", "order_id")
        ]
        
        for index_name, table_name, column_name in indexes:
            try:
                cursor.execute(f"""
                    CREATE INDEX IF NOT EXISTS {index_name} 
                    ON {table_name} ({column_name})
                """)
                print(f"✅ Index {index_name} created/verified")
            except Exception as e:
                print(f"⚠️ Could not create index {index_name}: {e}")
        
        # Commit all changes
        conn.commit()
        print("✅ All migrations completed successfully!")
        
        # Show summary
        print("\n📊 Migration Summary:")
        print("✅ Cart table: selected_size column added")
        print("✅ Order_item table: selected_size column added")
        print("✅ Exchange table: new columns added")
        print(f"✅ {updated_count} products updated with new size format")
        print("✅ Performance indexes created")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    try:
        migrate_database()
        print("\n🎉 Migration completed successfully!")
    except Exception as e:
        print(f"\n💥 Migration failed: {e}")
        exit(1)
