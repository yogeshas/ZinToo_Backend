#!/usr/bin/env python3
"""
Migration script to create delivery_track table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from extensions import db

def create_delivery_track_table():
    """Create the delivery_track table"""
    
    print("Creating delivery_track table...")
    
    with app.app_context():
        try:
            # Create the table using raw SQL
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS delivery_track (
                id INT AUTO_INCREMENT PRIMARY KEY,
                delivery_guy_id INT NOT NULL,
                order_id INT NULL,
                exchange_id INT NULL,
                status VARCHAR(20) NOT NULL,
                notes TEXT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (delivery_guy_id) REFERENCES delivery_onboarding(id) ON DELETE CASCADE,
                FOREIGN KEY (order_id) REFERENCES `order`(id) ON DELETE CASCADE,
                FOREIGN KEY (exchange_id) REFERENCES exchange(id) ON DELETE CASCADE,
                INDEX idx_delivery_guy_id (delivery_guy_id),
                INDEX idx_order_id (order_id),
                INDEX idx_exchange_id (exchange_id),
                INDEX idx_status (status)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """
            
            db.session.execute(db.text(create_table_sql))
            db.session.commit()
            
            print("✅ delivery_track table created successfully!")
            
            # Verify the table was created
            result = db.session.execute(db.text("SHOW TABLES LIKE 'delivery_track'"))
            if result.fetchone():
                print("✅ Table verification successful!")
                
                # Show table structure
                result = db.session.execute(db.text("DESCRIBE delivery_track"))
                print("\n📋 Table structure:")
                for row in result:
                    print(f"   {row[0]} - {row[1]} - {row[2]} - {row[3]} - {row[4]} - {row[5]}")
                
                return True
            else:
                print("❌ Table creation failed - table not found")
                return False
                
        except Exception as e:
            print(f"❌ Error creating delivery_track table: {str(e)}")
            db.session.rollback()
            return False

def add_delivery_guy_id_to_exchange():
    """Add delivery_guy_id column to exchange table if it doesn't exist"""
    
    print("\nChecking exchange table for delivery_guy_id column...")
    
    with app.app_context():
        try:
            # Check if column exists
            result = db.session.execute(db.text("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'exchange' 
                AND COLUMN_NAME = 'delivery_guy_id'
            """))
            
            if not result.fetchone():
                print("Adding delivery_guy_id column to exchange table...")
                
                # Add the column
                alter_sql = """
                ALTER TABLE exchange 
                ADD COLUMN delivery_guy_id INT NULL,
                ADD FOREIGN KEY (delivery_guy_id) REFERENCES delivery_onboarding(id) ON DELETE SET NULL,
                ADD INDEX idx_delivery_guy_id (delivery_guy_id)
                """
                
                db.session.execute(db.text(alter_sql))
                db.session.commit()
                
                print("✅ delivery_guy_id column added to exchange table!")
            else:
                print("✅ delivery_guy_id column already exists in exchange table")
            
            return True
            
        except Exception as e:
            print(f"❌ Error adding delivery_guy_id to exchange table: {str(e)}")
            db.session.rollback()
            return False

def main():
    """Run the migration"""
    
    print("🚀 Starting Enhanced Order Management System Migration")
    print("=" * 60)
    
    success = True
    
    # Create delivery_track table
    if not create_delivery_track_table():
        success = False
    
    # Add delivery_guy_id to exchange table
    if not add_delivery_guy_id_to_exchange():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Migration completed successfully!")
        print("✅ Enhanced Order Management System is ready!")
    else:
        print("⚠️ Migration completed with errors. Please check the issues above.")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
