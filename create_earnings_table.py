#!/usr/bin/env python3
"""
Quick script to create the earnings_management table
Run this from the ZinToo_Backend-main directory
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from extensions import db

def create_earnings_table():
    """Create the earnings_management table"""
    with app.app_context():
        try:
            # Import the model to register it
            from models.earnings_management import EarningsManagement
            
            # Create all tables
            db.create_all()
            
            print("✅ Successfully created earnings_management table")
            print("✅ All database tables are up to date")
            
            # Verify the table was created
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'earnings_management' in tables:
                print("✅ Verified: earnings_management table exists")
            else:
                print("❌ Error: earnings_management table not found")
                
        except Exception as e:
            print(f"❌ Error creating table: {str(e)}")
            return False
    
    return True

if __name__ == "__main__":
    print("🚀 Creating earnings_management table...")
    success = create_earnings_table()
    
    if success:
        print("\n🎉 Migration completed successfully!")
        print("You can now use the earnings management system.")
    else:
        print("\n💥 Migration failed. Please check the error messages above.")
