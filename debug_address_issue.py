#!/usr/bin/env python3
"""
Debug script to identify address API 500 error
Run this to see what's causing the internal server error
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_address_issue():
    """Debug the address API issue"""
    print("🔍 Debugging Address API 500 Error...")
    print("=" * 50)
    
    try:
        from app import app, db
        
        with app.app_context():
            print("✅ Flask app context created successfully")
            
            # Test database connection
            print("📊 Testing database connection...")
            try:
                db.engine.execute("SELECT 1")
                print("✅ Database connection successful")
            except Exception as e:
                print(f"❌ Database connection failed: {str(e)}")
                return
            
            # Check if address table exists
            print("📋 Checking address table...")
            try:
                result = db.engine.execute("SHOW TABLES LIKE 'address'")
                tables = result.fetchall()
                if tables:
                    print("✅ Address table exists")
                else:
                    print("❌ Address table does not exist")
                    return
            except Exception as e:
                print(f"❌ Error checking address table: {str(e)}")
                return
            
            # Check address table structure
            print("🏗️ Checking address table structure...")
            try:
                result = db.engine.execute("DESCRIBE address")
                columns = result.fetchall()
                print("📊 Address table columns:")
                for col in columns:
                    print(f"   - {col[0]} ({col[1]})")
            except Exception as e:
                print(f"❌ Error describing address table: {str(e)}")
            
            # Check if there are any addresses
            print("🔍 Checking for existing addresses...")
            try:
                result = db.engine.execute("SELECT COUNT(*) FROM address")
                count = result.fetchone()[0]
                print(f"✅ Found {count} addresses in database")
                
                if count > 0:
                    result = db.engine.execute("SELECT * FROM address LIMIT 3")
                    addresses = result.fetchall()
                    print("📝 Sample addresses:")
                    for addr in addresses:
                        print(f"   - ID: {addr[0]}, UID: {addr[1]}, Name: {addr[2]}, Type: {addr[3]}")
            except Exception as e:
                print(f"❌ Error querying addresses: {str(e)}")
            
            # Test the address service functions
            print("🧪 Testing address service functions...")
            try:
                from services.address_service import get_addresses_by_customer
                print("✅ Address service imported successfully")
                
                # Test with customer ID 1
                addresses = get_addresses_by_customer(1)
                print(f"✅ get_addresses_by_customer(1) returned {len(addresses)} addresses")
                
            except Exception as e:
                print(f"❌ Error testing address service: {str(e)}")
                import traceback
                traceback.print_exc()
            
            print("✅ Debugging completed!")
            
    except Exception as e:
        print(f"❌ Failed to debug: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_address_issue()
