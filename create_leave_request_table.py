#!/usr/bin/env python3
"""
Script to create the delivery_leave_request table in the database.
Run this script after setting up your database connection.
"""

from app import app, db
from models.delivery_leave_request import DeliveryLeaveRequest

def create_leave_request_table():
    """Create the delivery_leave_request table"""
    with app.app_context():
        try:
            # Create the table
            db.create_all()
            print("✅ delivery_leave_request table created successfully!")
            
            # Verify the table was created
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'delivery_leave_request' in tables:
                print("✅ Table 'delivery_leave_request' exists in database")
                
                # Show table structure
                columns = inspector.get_columns('delivery_leave_request')
                print("\n📋 Table structure:")
                for column in columns:
                    print(f"  - {column['name']}: {column['type']}")
            else:
                print("❌ Table 'delivery_leave_request' not found in database")
                
        except Exception as e:
            print(f"❌ Error creating table: {str(e)}")

if __name__ == "__main__":
    create_leave_request_table()
