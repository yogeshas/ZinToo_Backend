#!/usr/bin/env python3
"""
Fix Delivery Guy IDs Script

This script fixes the delivery_guy_id field for existing approved delivery guys.
It sets the delivery_guy_id to the onboarding ID for all approved onboarding records.
"""

from extensions import db
from models.delivery_onboarding import DeliveryOnboarding
from models.delivery_auth import DeliveryGuyAuth
from datetime import datetime

def fix_delivery_guy_ids():
    """Fix delivery_guy_id for all approved onboarding records"""
    try:
        print("🔧 Starting delivery guy ID fix...")
        
        # Get all approved onboarding records
        approved_onboardings = DeliveryOnboarding.query.filter_by(status='approved').all()
        
        if not approved_onboardings:
            print("ℹ️ No approved onboarding records found")
            return
        
        print(f"📋 Found {len(approved_onboardings)} approved onboarding records")
        
        fixed_count = 0
        for onboarding in approved_onboardings:
            print(f"🔍 Processing: {onboarding.first_name} {onboarding.last_name} (ID: {onboarding.id})")
            
            # Set delivery_guy_id to onboarding ID
            if onboarding.delivery_guy_id != onboarding.id:
                onboarding.delivery_guy_id = onboarding.id
                print(f"✅ Set delivery_guy_id to {onboarding.id}")
                fixed_count += 1
            else:
                print(f"ℹ️ delivery_guy_id already set to {onboarding.delivery_guy_id}")
            
            # Also update the auth user if exists
            if onboarding.email:
                auth_user = DeliveryGuyAuth.query.filter_by(email=onboarding.email).first()
                if auth_user:
                    if auth_user.delivery_guy_id != onboarding.id:
                        # For now, just print that we would update it
                        # The foreign key constraint needs to be fixed first
                        print(f"⚠️ Would update auth user delivery_guy_id to {onboarding.id} (foreign key constraint prevents this)")
                    else:
                        print(f"ℹ️ Auth user delivery_guy_id already set to {auth_user.delivery_guy_id}")
                else:
                    print(f"⚠️ No auth user found for email: {onboarding.email}")
            
            print("---")
        
        # Commit all changes
        db.session.commit()
        print(f"🎉 Successfully fixed {fixed_count} delivery guy IDs!")
        
        # Verify the fix
        print("\n🔍 Verifying the fix...")
        for onboarding in approved_onboardings:
            if onboarding.delivery_guy_id == onboarding.id:
                print(f"✅ {onboarding.first_name} {onboarding.last_name}: delivery_guy_id = {onboarding.delivery_guy_id}")
            else:
                print(f"❌ {onboarding.first_name} {onboarding.last_name}: delivery_guy_id = {onboarding.delivery_guy_id} (should be {onboarding.id})")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error fixing delivery guy IDs: {e}")
        raise

if __name__ == "__main__":
    print("🚀 Delivery Guy ID Fix Script")
    print("=" * 40)
    
    try:
        # Import and create Flask app context
        from app import app
        
        with app.app_context():
            fix_delivery_guy_ids()
            print("\n✅ Script completed successfully!")
    except Exception as e:
        print(f"\n❌ Script failed: {e}")
        exit(1)
