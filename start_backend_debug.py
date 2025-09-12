#!/usr/bin/env python3
"""
Debug startup script for ZinToo Backend
This script will help identify and fix admin login issues
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    print("🚀 Starting ZinToo Backend in debug mode...")
    print("=" * 50)
    
    # Check environment variables
    print("🔍 Checking environment variables...")
    crypto_secret = os.getenv("CRYPTO_SECRET", "my_super_secret_key_32chars!!")
    secret_key = os.getenv("SECRET_KEY", "4e8f3d1c90b2a6d73a7f8b19c4d2f50a")
    
    print(f"🔑 CRYPTO_SECRET: {crypto_secret[:20]}... (length: {len(crypto_secret)})")
    print(f"🔑 SECRET_KEY: {secret_key[:20]}... (length: {len(secret_key)})")
    
    # Check if crypto secret is 32 characters
    if len(crypto_secret) != 32:
        print(f"⚠️  Warning: CRYPTO_SECRET should be 32 characters, got {len(crypto_secret)}")
        print("   This might cause encryption/decryption issues")
    
    print()
    
    # Import and test app
    try:
        print("📦 Importing Flask app...")
        from app import app, db
        
        print("✅ Flask app imported successfully")
        
        # Test database connection
        with app.app_context():
            print("🔌 Testing database connection...")
            try:
                db.engine.execute("SELECT 1")
                print("✅ Database connection successful")
            except Exception as e:
                print(f"❌ Database connection failed: {str(e)}")
                print("   Please check your database configuration")
                return
            
            # Test admin creation
            print("👤 Testing admin creation...")
            from models.admin import Admin, create_default_admin
            
            try:
                create_default_admin()
                print("✅ Admin creation completed")
                
                # Check admin count
                admin_count = Admin.query.count()
                print(f"📊 Total admins in database: {admin_count}")
                
                if admin_count > 0:
                    admin = Admin.query.first()
                    print(f"👤 Admin details: {admin.username} ({admin.email})")
                    
                    # Test password
                    if admin.check_password("zintoo@1234"):
                        print("✅ Admin password verification successful")
                    else:
                        print("❌ Admin password verification failed")
                        print("   Resetting password...")
                        admin.set_password("zintoo@1234")
                        db.session.commit()
                        print("✅ Password reset successful")
                
            except Exception as e:
                print(f"❌ Admin creation failed: {str(e)}")
                import traceback
                traceback.print_exc()
        
        print()
        print("🎯 Backend is ready! You can now:")
        print("   1. Start the Flask app: python app.py")
        print("   2. Test admin login with:")
        print("      Email: hatchybyte@gmail.com")
        print("      Password: zintoo@1234")
        print()
        print("🔧 If you still have issues, check:")
        print("   - Database connection")
        print("   - Email configuration for OTP")
        print("   - Frontend crypto secret matches backend")
        
    except Exception as e:
        print(f"❌ Failed to import app: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
