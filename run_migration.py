#!/usr/bin/env python3
"""
Database Migration Script for Push Notifications
This script will add the required columns to the delivery_guy_auth table
"""

import mysql.connector
from config import Config
import sys

def run_migration():
    """Run the database migration to add notification fields"""
    
    print("🔄 Starting database migration for push notifications...")
    
    try:
        # Connect to MySQL database
        connection = mysql.connector.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            port=int(Config.DB_PORT)
        )
        
        cursor = connection.cursor()
        
        print("✅ Connected to database successfully")
        
        # Check if columns already exist
        cursor.execute("DESCRIBE delivery_guy_auth")
        columns = [row[0] for row in cursor.fetchall()]
        
        print(f"📋 Current columns: {columns}")
        
        # Add columns if they don't exist
        new_columns = [
            ("device_token", "VARCHAR(500) NULL"),
            ("platform", "VARCHAR(20) NULL"),
            ("sns_endpoint_arn", "VARCHAR(500) NULL"),
            ("is_notifications_enabled", "BOOLEAN DEFAULT TRUE")
        ]
        
        for column_name, column_definition in new_columns:
            if column_name not in columns:
                try:
                    sql = f"ALTER TABLE delivery_guy_auth ADD COLUMN {column_name} {column_definition}"
                    print(f"🔧 Adding column: {column_name}")
                    cursor.execute(sql)
                    print(f"✅ Added column: {column_name}")
                except Exception as e:
                    print(f"⚠️ Error adding column {column_name}: {e}")
            else:
                print(f"ℹ️ Column {column_name} already exists")
        
        # Commit changes
        connection.commit()
        print("✅ Migration completed successfully!")
        
        # Verify the changes
        print("\n📋 Verifying table structure:")
        cursor.execute("DESCRIBE delivery_guy_auth")
        for row in cursor.fetchall():
            print(f"  - {row[0]}: {row[1]}")
        
        print("\n🎉 Database migration completed! You can now use push notifications.")
        
    except mysql.connector.Error as e:
        print(f"❌ Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
            print("🔌 Database connection closed")

if __name__ == "__main__":
    print("🚀 Push Notifications Database Migration")
    print("=" * 50)
    run_migration()
