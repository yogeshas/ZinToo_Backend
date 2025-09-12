#!/usr/bin/env python3
"""
Migration script to add color columns to exchange table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from extensions import db

def add_color_columns_to_exchange():
    """Add old_color and new_color columns to exchange table"""
    try:
        with app.app_context():
            # Check if columns already exist
            with db.engine.connect() as connection:
                # Check if old_color column exists
                result = connection.execute(db.text("""
                    SELECT COUNT(*) as count 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME = 'exchange' 
                    AND COLUMN_NAME = 'old_color'
                """))
                old_color_exists = result.fetchone()[0] > 0
                
                # Check if new_color column exists
                result = connection.execute(db.text("""
                    SELECT COUNT(*) as count 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME = 'exchange' 
                    AND COLUMN_NAME = 'new_color'
                """))
                new_color_exists = result.fetchone()[0] > 0
                
                print(f"old_color column exists: {old_color_exists}")
                print(f"new_color column exists: {new_color_exists}")
                
                # Add old_color column if it doesn't exist
                if not old_color_exists:
                    print("Adding old_color column to exchange table...")
                    connection.execute(db.text("ALTER TABLE exchange ADD COLUMN old_color VARCHAR(50)"))
                    connection.commit()
                    print("✅ old_color column added successfully!")
                else:
                    print("ℹ️ old_color column already exists")
                
                # Add new_color column if it doesn't exist
                if not new_color_exists:
                    print("Adding new_color column to exchange table...")
                    connection.execute(db.text("ALTER TABLE exchange ADD COLUMN new_color VARCHAR(50)"))
                    connection.commit()
                    print("✅ new_color column added successfully!")
                else:
                    print("ℹ️ new_color column already exists")
                
                print("🎉 Migration completed successfully!")
                return True
                
    except Exception as e:
        print(f"❌ Error adding color columns to exchange table: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting exchange color columns migration...")
    success = add_color_columns_to_exchange()
    if success:
        print("✅ Migration completed successfully!")
    else:
        print("❌ Migration failed!")
        sys.exit(1)
