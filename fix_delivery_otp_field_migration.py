#!/usr/bin/env python3
"""
Fix Delivery OTP Field Migration

This script fixes the field name mismatch in the delivery_guy_otp table.
The database table has 'otp_code' but the model was trying to use 'otp'.
"""

import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from extensions import db
from sqlalchemy import text

def fix_delivery_otp_field():
    """Fix the field name mismatch in delivery_guy_otp table"""
    with app.app_context():
        try:
            # Check if we're using SQLite or MySQL
            engine = db.engine
            if 'sqlite' in str(engine.url):
                fix_delivery_otp_field_sqlite()
            elif 'mysql' in str(engine.url):
                fix_delivery_otp_field_mysql()
            else:
                print("⚠️ Unknown database type, trying SQLite approach")
                fix_delivery_otp_field_sqlite()
                
        except Exception as e:
            print(f"❌ Error fixing delivery OTP field: {e}")
            db.session.rollback()
            raise

def fix_delivery_otp_field_sqlite():
    """Fix delivery_guy_otp table in SQLite"""
    try:
        # Check if delivery_guy_otp table exists
        result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='delivery_guy_otp'"))
        if not result.fetchone():
            print("ℹ️ delivery_guy_otp table doesn't exist, creating it...")
            create_delivery_otp_table_sqlite()
            return
        
        # Check current table structure
        result = db.session.execute(text("PRAGMA table_info(delivery_guy_otp)"))
        columns = {row[1]: row[2] for row in result.fetchall()}
        
        print(f"📋 Current delivery_guy_otp table columns: {list(columns.keys())}")
        
        # If table has 'otp' field instead of 'otp_code', rename it
        if 'otp' in columns and 'otp_code' not in columns:
            print("🔄 Renaming 'otp' field to 'otp_code'...")
            
            # SQLite doesn't support ALTER COLUMN RENAME, so we need to recreate the table
            # First, get all data
            data = db.session.execute(text("SELECT id, email, otp, is_used, expires_at, created_at FROM delivery_guy_otp")).fetchall()
            
            # Drop the old table
            db.session.execute(text("DROP TABLE delivery_guy_otp"))
            
            # Create new table with correct structure
            db.session.execute(text("""
                CREATE TABLE delivery_guy_otp (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email VARCHAR(120) NOT NULL,
                    otp_code VARCHAR(6) NOT NULL,
                    is_used BOOLEAN DEFAULT 0,
                    expires_at DATETIME NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Reinsert data with new field name
            for row in data:
                db.session.execute(text("""
                    INSERT INTO delivery_guy_otp (id, email, otp_code, is_used, expires_at, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """), (row[0], row[1], row[2], row[3], row[4], row[5]))
            
            print("✅ Field renamed successfully")
        elif 'otp_code' in columns:
            print("✅ Table already has correct 'otp_code' field")
        else:
            print("⚠️ Table structure is unexpected, recreating...")
            recreate_delivery_otp_table_sqlite()
        
        db.session.commit()
        print("✅ delivery_guy_otp table fixed successfully in SQLite")
        
    except Exception as e:
        print(f"❌ Error fixing delivery_guy_otp table in SQLite: {e}")
        db.session.rollback()
        raise

def fix_delivery_otp_field_mysql():
    """Fix delivery_guy_otp table in MySQL"""
    try:
        # Check if delivery_guy_otp table exists
        result = db.session.execute(text("SHOW TABLES LIKE 'delivery_guy_otp'"))
        if not result.fetchone():
            print("ℹ️ delivery_guy_otp table doesn't exist, creating it...")
            create_delivery_otp_table_mysql()
            return
        
        # Check current table structure
        result = db.session.execute(text("DESCRIBE delivery_guy_otp"))
        columns = {row[0]: row[1] for row in result.fetchall()}
        
        print(f"📋 Current delivery_guy_otp table columns: {list(columns.keys())}")
        
        # If table has 'otp' field instead of 'otp_code', rename it
        if 'otp' in columns and 'otp_code' not in columns:
            print("🔄 Renaming 'otp' field to 'otp_code'...")
            db.session.execute(text("ALTER TABLE delivery_guy_otp CHANGE COLUMN otp otp_code VARCHAR(6) NOT NULL"))
            print("✅ Field renamed successfully")
        elif 'otp_code' in columns:
            print("✅ Table already has correct 'otp_code' field")
        else:
            print("⚠️ Table structure is unexpected, recreating...")
            recreate_delivery_otp_table_mysql()
        
        db.session.commit()
        print("✅ delivery_guy_otp table fixed successfully in MySQL")
        
    except Exception as e:
        print(f"❌ Error fixing delivery_guy_otp table in MySQL: {e}")
        db.session.rollback()
        raise

def create_delivery_otp_table_sqlite():
    """Create delivery_guy_otp table in SQLite with correct structure"""
    db.session.execute(text("""
        CREATE TABLE delivery_guy_otp (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email VARCHAR(120) NOT NULL,
            otp_code VARCHAR(6) NOT NULL,
            is_used BOOLEAN DEFAULT 0,
            expires_at DATETIME NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """))
    print("✅ delivery_guy_otp table created with correct structure")

def create_delivery_otp_table_mysql():
    """Create delivery_guy_otp table in MySQL with correct structure"""
    db.session.execute(text("""
        CREATE TABLE delivery_guy_otp (
            id INT AUTO_INCREMENT PRIMARY KEY,
            email VARCHAR(120) NOT NULL,
            otp_code VARCHAR(6) NOT NULL,
            is_used BOOLEAN DEFAULT FALSE,
            expires_at DATETIME NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """))
    print("✅ delivery_guy_otp table created with correct structure")

def recreate_delivery_otp_table_sqlite():
    """Recreate delivery_guy_otp table in SQLite"""
    db.session.execute(text("DROP TABLE IF EXISTS delivery_guy_otp"))
    create_delivery_otp_table_sqlite()

def recreate_delivery_otp_table_mysql():
    """Recreate delivery_guy_otp table in MySQL"""
    db.session.execute(text("DROP TABLE IF EXISTS delivery_guy_otp"))
    create_delivery_otp_table_mysql()

if __name__ == "__main__":
    print("🚀 Fixing Delivery OTP Field Mismatch")
    print("=" * 50)
    
    try:
        fix_delivery_otp_field()
        print("\n✅ Migration completed successfully!")
        print("\nThe delivery_guy_otp table now has the correct 'otp_code' field.")
        print("You can now restart your application and the OTP functionality should work.")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)
