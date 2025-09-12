#!/usr/bin/env python3
"""
Test script to check database connectivity and model registration
"""
import sys
import os

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_database_connection():
    """Test database connection and model registration"""
    try:
        from app import app
        from extensions import db
        from models.delivery_auth import DeliveryGuyAuth, DeliveryGuyOTP
        
        with app.app_context():
            print("🔍 Testing database connection...")
            
            # Test basic database connection
            try:
                result = db.session.execute(db.text("SELECT 1"))
                print("✅ Database connection successful")
            except Exception as e:
                print(f"❌ Database connection failed: {e}")
                return False
            
            # Test if tables exist
            try:
                # Check delivery_guy_auth table
                result = db.session.execute(db.text("SHOW TABLES LIKE 'delivery_guy_auth'"))
                if result.fetchone():
                    print("✅ delivery_guy_auth table exists")
                else:
                    print("❌ delivery_guy_auth table does not exist")
                    return False
                
                # Check delivery_guy_otp table
                result = db.session.execute(db.text("SHOW TABLES LIKE 'delivery_guy_otp'"))
                if result.fetchone():
                    print("✅ delivery_guy_otp table exists")
                else:
                    print("❌ delivery_guy_otp table does not exist")
                    return False
                    
            except Exception as e:
                print(f"❌ Table check failed: {e}")
                return False
            
            # Test model queries
            try:
                # Test DeliveryGuyAuth model
                auth_count = DeliveryGuyAuth.query.count()
                print(f"✅ DeliveryGuyAuth model working - {auth_count} records found")
                
                # Test DeliveryGuyOTP model
                otp_count = DeliveryGuyOTP.query.count()
                print(f"✅ DeliveryGuyOTP model working - {otp_count} records found")
                
            except Exception as e:
                print(f"❌ Model query failed: {e}")
                return False
            
            print("✅ All database tests passed!")
            return True
            
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

if __name__ == "__main__":
    print("🗄️ Database Connection Test")
    print("=" * 40)
    
    test_database_connection()
    
    print("\n🏁 Database test completed!")
