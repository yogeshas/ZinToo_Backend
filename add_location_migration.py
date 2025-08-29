#!/usr/bin/env python3
"""
Script to add location field to customer table if it doesn't exist
"""
import sqlite3
import os

def add_location_field():
    """Add location field to customer table if it doesn't exist"""
    
    # Database path - adjust as needed
    db_path = "app.db"  # or your actual database path
    
    if not os.path.exists(db_path):
        print(f"❌ Database file {db_path} not found")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if location column exists
        cursor.execute("PRAGMA table_info(customer)")
        columns = [column[1] for column in cursor.fetchall()]
        
        print(f"📋 Current customer table columns: {columns}")
        
        if 'location' not in columns:
            print("➕ Adding location column to customer table...")
            cursor.execute("ALTER TABLE customer ADD COLUMN location BLOB")
            conn.commit()
            print("✅ Location column added successfully")
        else:
            print("ℹ️ Location column already exists")
        
        # Check if phone_number column exists
        if 'phone_number' not in columns:
            print("➕ Adding phone_number column to customer table...")
            cursor.execute("ALTER TABLE customer ADD COLUMN phone_number BLOB")
            conn.commit()
            print("✅ Phone number column added successfully")
        else:
            print("ℹ️ Phone number column already exists")
        
        # Verify the changes
        cursor.execute("PRAGMA table_info(customer)")
        updated_columns = [column[1] for column in cursor.fetchall()]
        print(f"📋 Updated customer table columns: {updated_columns}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error adding location field: {str(e)}")
        if conn:
            conn.close()

if __name__ == "__main__":
    add_location_field()
