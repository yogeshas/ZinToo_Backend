#!/usr/bin/env python3
"""
Script to create a test delivery guy account for testing leave requests
"""

from app import app, db
from models.delivery_auth import DeliveryGuyAuth
from models.delivery_onboarding import DeliveryOnboarding

def create_test_delivery_account():
    """Create a test delivery guy account"""
    with app.app_context():
        try:
            # Check if test account already exists
            existing_auth = DeliveryGuyAuth.query.filter_by(email="test@delivery.com").first()
            if existing_auth:
                print("✅ Test delivery account already exists")
                print(f"   Email: {existing_auth.email}")
                print(f"   Token: {existing_auth.auth_token}")
                return existing_auth.auth_token
            
            # Create delivery onboarding record first
            onboarding = DeliveryOnboarding(
                first_name="Test",
                last_name="Delivery",
                email="test@delivery.com",
                primary_number="1234567890",
                name_as_per_bank="Test Delivery",  # Required field
                status="approved"
            )
            db.session.add(onboarding)
            db.session.flush()  # Get the ID
            
            # Create delivery auth record
            auth = DeliveryGuyAuth(
                email="test@delivery.com",
                phone_number="1234567890",
                password_hash="hashed_password",  # You'll need to hash this properly
                is_onboarded=True,
                delivery_guy_id=onboarding.id
            )
            
            # Generate auth token
            token = auth.generate_auth_token()
            
            db.session.add(auth)
            db.session.commit()
            
            print("✅ Test delivery account created successfully!")
            print(f"   Email: {auth.email}")
            print(f"   Phone: {auth.phone_number}")
            print(f"   Token: {token}")
            print(f"   Delivery Guy ID: {auth.delivery_guy_id}")
            
            return token
            
        except Exception as e:
            print(f"❌ Error creating test account: {e}")
            db.session.rollback()
            return None

if __name__ == "__main__":
    token = create_test_delivery_account()
    if token:
        print(f"\n🔑 Use this token for testing: {token}")
        print("\n📱 Test in Flutter app:")
        print("   1. Save this token in SharedPreferences as 'authToken'")
        print("   2. Navigate to Leave Requests")
        print("   3. Try to create a leave request")
        
        print("\n🌐 Test with curl:")
        print(f"   curl -X GET 'http://127.0.0.1:5000/api/leave-requests/delivery/leave-requests' \\")
        print(f"     -H 'Authorization: Bearer {token}'")
