#!/usr/bin/env python3
"""
Test script to verify admin creation and database connectivity
Run this to debug admin login issues
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models.admin import Admin, create_default_admin

def test_admin_creation():
    """Test admin creation and database connectivity"""
    print("🔍 Testing admin creation and database connectivity...")
    
    with app.app_context():
        try:
            # Test database connection
            print("📊 Testing database connection...")
            db.engine.execute("SELECT 1")
            print("✅ Database connection successful")
            
            # Check if admin table exists
            print("📋 Checking admin table...")
            admin_count = Admin.query.count()
            print(f"📊 Found {admin_count} admin users in database")
            
            # List all admins
            admins = Admin.query.all()
            for admin in admins:
                print(f"👤 Admin: {admin.username} ({admin.email}) - Status: {admin.status}")
            
            # Try to create default admin
            print("🔧 Attempting to create default admin...")
            create_default_admin()
            
            # Check again
            admin_count_after = Admin.query.count()
            print(f"📊 Admin count after creation: {admin_count_after}")
            
            # Test password verification
            if admin_count_after > 0:
                admin = Admin.query.first()
                print(f"🔐 Testing password verification for {admin.email}...")
                
                # Test with correct password
                if admin.check_password("zintoo@1234"):
                    print("✅ Password verification successful")
                else:
                    print("❌ Password verification failed")
                    
                    # Try to reset password
                    print("🔄 Resetting admin password...")
                    admin.set_password("zintoo@1234")
                    db.session.commit()
                    print("✅ Password reset successful")
                    
                    # Test again
                    if admin.check_password("zintoo@1234"):
                        print("✅ Password verification successful after reset")
                    else:
                        print("❌ Password verification still failed")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_admin_creation()
