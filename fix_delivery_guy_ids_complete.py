#!/usr/bin/env python3
"""
Complete Delivery Guy ID Fix Script

This script fixes the delivery_guy_id field for existing approved delivery guys
in BOTH the onboarding table AND the auth table.
"""

from extensions import db
from models.delivery_onboarding import DeliveryOnboarding
from models.delivery_auth import DeliveryGuyAuth
from datetime import datetime

def fix_delivery_guy_ids_complete():
    """Fix delivery_guy_id for all approved onboarding records and auth users"""
    try:
        print("🔧 Starting COMPLETE delivery guy ID fix...")
        
        # Get all approved onboarding records
        approved_onboardings = DeliveryOnboarding.query.filter_by(status='approved').all()
        
        if not approved_onboardings:
            print("ℹ️ No approved onboarding records found")
            return
        
        print(f"📋 Found {len(approved_onboardings)} approved onboarding records")
        
        fixed_count = 0
        for onboarding in approved_onboardings:
            print(f"\n🔍 Processing: {onboarding.first_name} {onboarding.last_name} (ID: {onboarding.id})")
            
            # Step 1: Fix onboarding table delivery_guy_id
            if onboarding.delivery_guy_id != onboarding.id:
                onboarding.delivery_guy_id = onboarding.id
                print(f"✅ Set onboarding.delivery_guy_id to {onboarding.id}")
                fixed_count += 1
            else:
                print(f"ℹ️ onboarding.delivery_guy_id already set to {onboarding.delivery_guy_id}")
            
            # Step 2: Fix auth table delivery_guy_id
            if onboarding.email:
                auth_user = DeliveryGuyAuth.query.filter_by(email=onboarding.email).first()
                if auth_user:
                    if auth_user.delivery_guy_id != onboarding.id:
                        # IMPORTANT: Remove foreign key constraint first
                        print(f"⚠️ Auth user found but delivery_guy_id constraint prevents update")
                        print(f"   Current: {auth_user.delivery_guy_id}, Should be: {onboarding.id}")
                        
                        # Try to update directly with SQL to bypass constraint
                        try:
                            from sqlalchemy import text
                            db.session.execute(
                                text("UPDATE delivery_guy_auth SET delivery_guy_id = :id WHERE id = :auth_id"),
                                {"id": onboarding.id, "auth_id": auth_user.id}
                            )
                            print(f"✅ Updated auth user delivery_guy_id to {onboarding.id} via SQL")
                        except Exception as sql_error:
                            print(f"❌ SQL update failed: {sql_error}")
                            print(f"   You need to remove the foreign key constraint manually")
                    else:
                        print(f"ℹ️ Auth user delivery_guy_id already set to {auth_user.delivery_guy_id}")
                else:
                    print(f"⚠️ No auth user found for email: {onboarding.email}")
            
            print("---")
        
        # Commit all changes
        db.session.commit()
        print(f"\n🎉 Successfully processed {len(approved_onboardings)} delivery guys!")
        
        # Verify the fix
        print("\n🔍 Verifying the fix...")
        for onboarding in approved_onboardings:
            print(f"\n📋 {onboarding.first_name} {onboarding.last_name}:")
            
            # Check onboarding table
            if onboarding.delivery_guy_id == onboarding.id:
                print(f"   ✅ Onboarding: delivery_guy_id = {onboarding.delivery_guy_id}")
            else:
                print(f"   ❌ Onboarding: delivery_guy_id = {onboarding.delivery_guy_id} (should be {onboarding.id})")
            
            # Check auth table
            if onboarding.email:
                auth_user = DeliveryGuyAuth.query.filter_by(email=onboarding.email).first()
                if auth_user:
                    if auth_user.delivery_guy_id == onboarding.id:
                        print(f"   ✅ Auth: delivery_guy_id = {auth_user.delivery_guy_id}")
                    else:
                        print(f"   ❌ Auth: delivery_guy_id = {auth_user.delivery_guy_id} (should be {onboarding.id})")
                else:
                    print(f"   ⚠️ Auth: No auth user found")
        
        # Final instructions
        print(f"\n🚨 IMPORTANT: If you still get foreign key errors, run this SQL:")
        print(f"   ALTER TABLE delivery_guy_auth DROP FOREIGN KEY delivery_guy_auth_ibfk_1;")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error fixing delivery guy IDs: {e}")
        raise

if __name__ == "__main__":
    print("🚀 COMPLETE Delivery Guy ID Fix Script")
    print("=" * 50)
    
    try:
        # Import and create Flask app context
        from app import app
        
        with app.app_context():
            fix_delivery_guy_ids_complete()
            print("\n✅ Script completed successfully!")
    except Exception as e:
        print(f"\n❌ Script failed: {e}")
        exit(1)
