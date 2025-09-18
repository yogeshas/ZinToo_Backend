#!/usr/bin/env python3
"""
Script to create the transaction table in the database.
Run this script to add the transaction table to your existing database.
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models.transaction import Transaction

def create_transaction_table():
    """Create the transaction table"""
    try:
        with app.app_context():
            # Create the transaction table
            db.create_all()
            print("✅ Transaction table created successfully!")
            
            # Verify the table was created
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'transaction' in tables:
                print("✅ Transaction table verified in database")
                
                # Show table structure
                columns = inspector.get_columns('transaction')
                print("\n📋 Transaction table structure:")
                for column in columns:
                    print(f"  - {column['name']}: {column['type']}")
            else:
                print("❌ Transaction table not found in database")
                
    except Exception as e:
        print(f"❌ Error creating transaction table: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Creating transaction table...")
    success = create_transaction_table()
    
    if success:
        print("\n🎉 Transaction table setup completed successfully!")
        print("\n📝 Next steps:")
        print("1. Update wallet operations to log transactions")
        print("2. Update order operations to log transactions") 
        print("3. Update exchange operations to log transactions")
        print("4. Test the transaction management interface")
    else:
        print("\n❌ Transaction table setup failed!")
        sys.exit(1)
