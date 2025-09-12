#!/usr/bin/env python3
"""
Migration script to create delivery auth tables
"""
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from extensions import db
from sqlalchemy import text

def create_delivery_auth_tables():
    """Create delivery auth tables"""
    
    with app.app_context():
        try:
            print("🔧 Creating delivery auth tables...")
            print("=" * 60)
            
            # Check if we're using SQLite or MySQL
            engine = db.engine
            if 'sqlite' in str(engine.url):
                create_delivery_auth_tables_sqlite()
            elif 'mysql' in str(engine.url):
                create_delivery_auth_tables_mysql()
            else:
                print("⚠️ Unknown database type, trying SQLite approach")
                create_delivery_auth_tables_sqlite()
                
        except Exception as e:
            print(f"❌ Error creating delivery auth tables: {e}")
            import traceback
            traceback.print_exc()

def create_delivery_auth_tables_sqlite():
    """Create delivery auth tables in SQLite"""
    try:
        # Check if delivery_guy_auth table exists
        result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='delivery_guy_auth'"))
        if not result.fetchone():
            print("➕ Creating delivery_guy_auth table in SQLite...")
            
            db.session.execute(text("""
                CREATE TABLE delivery_guy_auth (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email VARCHAR(120) NOT NULL UNIQUE,
                    phone_number VARCHAR(20) NOT NULL UNIQUE,
                    password_hash VARCHAR(255),
                    is_verified BOOLEAN DEFAULT 0,
                    is_onboarded BOOLEAN DEFAULT 0,
                    auth_token VARCHAR(500),
                    token_expires_at DATETIME,
                    delivery_guy_id INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (delivery_guy_id) REFERENCES delivery_guy (id)
                )
            """))
            
            print("✅ delivery_guy_auth table created successfully in SQLite")
        else:
            print("ℹ️ delivery_guy_auth table already exists in SQLite")
        
        # Check if delivery_guy_otp table exists
        result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='delivery_guy_otp'"))
        if not result.fetchone():
            print("➕ Creating delivery_guy_otp table in SQLite...")
            
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
            
            print("✅ delivery_guy_otp table created successfully in SQLite")
        else:
            print("ℹ️ delivery_guy_otp table already exists in SQLite")
        
        db.session.commit()
        print("✅ All delivery auth tables created successfully in SQLite")
        
    except Exception as e:
        print(f"❌ Error creating delivery auth tables in SQLite: {e}")
        db.session.rollback()
        raise

def create_delivery_auth_tables_mysql():
    """Create delivery auth tables in MySQL"""
    try:
        # Check if delivery_guy_auth table exists
        result = db.session.execute(text("SHOW TABLES LIKE 'delivery_guy_auth'"))
        if not result.fetchone():
            print("➕ Creating delivery_guy_auth table in MySQL...")
            
            db.session.execute(text("""
                CREATE TABLE delivery_guy_auth (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    email VARCHAR(120) NOT NULL UNIQUE,
                    phone_number VARCHAR(20) NOT NULL UNIQUE,
                    password_hash VARCHAR(255),
                    is_verified BOOLEAN DEFAULT FALSE,
                    is_onboarded BOOLEAN DEFAULT FALSE,
                    auth_token VARCHAR(500),
                    token_expires_at DATETIME,
                    delivery_guy_id INT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (delivery_guy_id) REFERENCES delivery_guy (id)
                )
            """))
            
            print("✅ delivery_guy_auth table created successfully in MySQL")
        else:
            print("ℹ️ delivery_guy_auth table already exists in MySQL")
        
        # Check if delivery_guy_otp table exists
        result = db.session.execute(text("SHOW TABLES LIKE 'delivery_guy_otp'"))
        if not result.fetchone():
            print("➕ Creating delivery_guy_otp table in MySQL...")
            
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
            
            print("✅ delivery_guy_otp table created successfully in MySQL")
        else:
            print("ℹ️ delivery_guy_otp table already exists in MySQL")
        
        db.session.commit()
        print("✅ All delivery auth tables created successfully in MySQL")
        
    except Exception as e:
        print(f"❌ Error creating delivery auth tables in MySQL: {e}")
        db.session.rollback()
        raise

if __name__ == "__main__":
    print("🚀 Creating Delivery Auth Tables")
    print("=" * 60)
    
    create_delivery_auth_tables()
    
    print("\n🎉 Delivery auth tables creation completed!")
