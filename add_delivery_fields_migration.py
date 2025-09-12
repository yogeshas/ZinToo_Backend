#!/usr/bin/env python3
"""
Migration script to add delivery fields to the order table
"""
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from extensions import db
from sqlalchemy import text

def add_delivery_fields_to_order():
    """Add delivery fields to the order table"""
    
    with app.app_context():
        try:
            # Check if we're using SQLite or MySQL
            engine = db.engine
            if 'sqlite' in str(engine.url):
                print("🔍 Detected SQLite database")
                add_delivery_fields_sqlite()
            elif 'mysql' in str(engine.url):
                print("🔍 Detected MySQL database")
                add_delivery_fields_mysql()
            else:
                print("⚠️ Unknown database type, trying SQLite approach")
                add_delivery_fields_sqlite()
                
        except Exception as e:
            print(f"❌ Error adding delivery fields: {e}")
            import traceback
            traceback.print_exc()

def add_delivery_fields_sqlite():
    """Add delivery fields to SQLite order table"""
    try:
        # Check if columns already exist
        result = db.session.execute(text("PRAGMA table_info(`order`)"))
        columns = [row[1] for row in result.fetchall()]
        
        print(f"📋 Current order table columns: {columns}")
        
        # Add delivery_guy_id column if it doesn't exist
        if 'delivery_guy_id' not in columns:
            print("➕ Adding delivery_guy_id column...")
            db.session.execute(text("ALTER TABLE `order` ADD COLUMN delivery_guy_id INTEGER"))
            print("✅ delivery_guy_id column added")
        else:
            print("ℹ️ delivery_guy_id column already exists")
        
        # Add assigned_at column if it doesn't exist
        if 'assigned_at' not in columns:
            print("➕ Adding assigned_at column...")
            db.session.execute(text("ALTER TABLE `order` ADD COLUMN assigned_at DATETIME"))
            print("✅ assigned_at column added")
        else:
            print("ℹ️ assigned_at column already exists")
        
        # Add delivery_notes column if it doesn't exist
        if 'delivery_notes' not in columns:
            print("➕ Adding delivery_notes column...")
            db.session.execute(text("ALTER TABLE `order` ADD COLUMN delivery_notes TEXT"))
            print("✅ delivery_notes column added")
        else:
            print("ℹ️ delivery_notes column already exists")
        
        db.session.commit()
        print("✅ All delivery fields added successfully to SQLite")
        
    except Exception as e:
        print(f"❌ Error adding delivery fields to SQLite: {e}")
        db.session.rollback()
        raise

def add_delivery_fields_mysql():
    """Add delivery fields to MySQL order table"""
    try:
        # Check if columns already exist
        result = db.session.execute(text("DESCRIBE `order`"))
        columns = [row[0] for row in result.fetchall()]
        
        print(f"📋 Current order table columns: {columns}")
        
        # Add delivery_guy_id column if it doesn't exist
        if 'delivery_guy_id' not in columns:
            print("➕ Adding delivery_guy_id column...")
            db.session.execute(text("ALTER TABLE `order` ADD COLUMN delivery_guy_id INT"))
            print("✅ delivery_guy_id column added")
        else:
            print("ℹ️ delivery_guy_id column already exists")
        
        # Add assigned_at column if it doesn't exist
        if 'assigned_at' not in columns:
            print("➕ Adding assigned_at column...")
            db.session.execute(text("ALTER TABLE `order` ADD COLUMN assigned_at DATETIME"))
            print("✅ assigned_at column added")
        else:
            print("ℹ️ assigned_at column already exists")
        
        # Add delivery_notes column if it doesn't exist
        if 'delivery_notes' not in columns:
            print("➕ Adding delivery_notes column...")
            db.session.execute(text("ALTER TABLE `order` ADD COLUMN delivery_notes TEXT"))
            print("✅ delivery_notes column added")
        else:
            print("ℹ️ delivery_notes column already exists")
        
        db.session.commit()
        print("✅ All delivery fields added successfully to MySQL")
        
    except Exception as e:
        print(f"❌ Error adding delivery fields to MySQL: {e}")
        db.session.rollback()
        raise

def create_delivery_guy_table():
    """Create delivery_guy table if it doesn't exist"""
    with app.app_context():
        try:
            # Check if we're using SQLite or MySQL
            engine = db.engine
            if 'sqlite' in str(engine.url):
                create_delivery_guy_table_sqlite()
            elif 'mysql' in str(engine.url):
                create_delivery_guy_table_mysql()
            else:
                print("⚠️ Unknown database type, trying SQLite approach")
                create_delivery_guy_table_sqlite()
                
        except Exception as e:
            print(f"❌ Error creating delivery_guy table: {e}")
            db.session.rollback()
            raise

def create_delivery_guy_table_sqlite():
    """Create delivery_guy table in SQLite"""
    try:
        # Check if delivery_guy table exists
        result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='delivery_guy'"))
        if not result.fetchone():
            print("➕ Creating delivery_guy table in SQLite...")
            
            # Create the delivery_guy table
            db.session.execute(text("""
                CREATE TABLE delivery_guy (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(100) NOT NULL,
                    phone_number VARCHAR(20) NOT NULL UNIQUE,
                    email VARCHAR(120),
                    vehicle_number VARCHAR(20),
                    vehicle_type VARCHAR(50),
                    status VARCHAR(20) DEFAULT 'active',
                    current_location VARCHAR(200),
                    rating FLOAT DEFAULT 0.0,
                    total_deliveries INTEGER DEFAULT 0,
                    completed_deliveries INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            db.session.commit()
            print("✅ delivery_guy table created successfully in SQLite")
        else:
            print("ℹ️ delivery_guy table already exists in SQLite")
            
    except Exception as e:
        print(f"❌ Error creating delivery_guy table in SQLite: {e}")
        db.session.rollback()
        raise

def create_delivery_guy_table_mysql():
    """Create delivery_guy table in MySQL"""
    try:
        # Check if delivery_guy table exists
        result = db.session.execute(text("SHOW TABLES LIKE 'delivery_guy'"))
        if not result.fetchone():
            print("➕ Creating delivery_guy table in MySQL...")
            
            # Create the delivery_guy table
            db.session.execute(text("""
                CREATE TABLE delivery_guy (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    phone_number VARCHAR(20) NOT NULL UNIQUE,
                    email VARCHAR(120),
                    vehicle_number VARCHAR(20),
                    vehicle_type VARCHAR(50),
                    status VARCHAR(20) DEFAULT 'active',
                    current_location VARCHAR(200),
                    rating FLOAT DEFAULT 0.0,
                    total_deliveries INT DEFAULT 0,
                    completed_deliveries INT DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """))
            
            db.session.commit()
            print("✅ delivery_guy table created successfully in MySQL")
        else:
            print("ℹ️ delivery_guy table already exists in MySQL")
            
    except Exception as e:
        print(f"❌ Error creating delivery_guy table in MySQL: {e}")
        db.session.rollback()
        raise

if __name__ == "__main__":
    print("🚀 Starting delivery fields migration...")
    
    # First create the delivery_guy table
    create_delivery_guy_table()
    
    # Then add delivery fields to order table
    add_delivery_fields_to_order()
    
    print("🎉 Migration completed successfully!")
