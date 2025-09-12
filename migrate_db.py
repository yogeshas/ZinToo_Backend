#!/usr/bin/env python3
"""
Database migration script to add new fields to existing tables.
Run this script to update the database schema.
"""

from app import app, db
from models.category import Category
from models.widget import Widget
import sqlite3
import os

def migrate_database():
    """Migrate the database to add new fields"""
    
    with app.app_context():
        # Get the database file path
        db_path = app.config.get('SQLALCHEMY_DATABASE_URI', '').replace('sqlite:///', '')
        if not db_path:
            print("❌ Could not determine database path")
            return
        
        print(f"📁 Database path: {db_path}")
        
        if not os.path.exists(db_path):
            print("❌ Database file not found")
            return
        
        try:
            # Connect to SQLite database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if image column exists in category table
            cursor.execute("PRAGMA table_info(category)")
            category_columns = [column[1] for column in cursor.fetchall()]
            
            if 'image' not in category_columns:
                print("➕ Adding 'image' column to category table...")
                cursor.execute("ALTER TABLE category ADD COLUMN image VARCHAR(255)")
                print("✅ Added 'image' column to category table")
            else:
                print("ℹ️  'image' column already exists in category table")
            
            # Check if title column exists in widget table
            cursor.execute("PRAGMA table_info(widget)")
            widget_columns = [column[1] for column in cursor.fetchall()]
            
            if 'title' not in widget_columns:
                print("➕ Adding 'title' column to widget table...")
                cursor.execute("ALTER TABLE widget ADD COLUMN title VARCHAR(100)")
                print("✅ Added 'title' column to widget table")
            else:
                print("ℹ️  'title' column already exists in widget table")
            
            # Commit changes
            conn.commit()
            conn.close()
            
            print("🎉 Database migration completed successfully!")
            
        except Exception as e:
            print(f"❌ Migration failed: {str(e)}")
            if 'conn' in locals():
                conn.rollback()
                conn.close()

if __name__ == "__main__":
    print("🚀 Starting database migration...")
    migrate_database()
