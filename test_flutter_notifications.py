#!/usr/bin/env python3
"""
Test Flutter Notifications - Send notifications to Flutter app
"""

import sys
import os
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import Flask app and create context
from app import app
from models.delivery_auth import DeliveryGuyAuth
from extensions import db

def test_flutter_notifications():
    """Test sending notifications to Flutter app"""
    print("📱 Testing Flutter Notifications")
    print("=" * 50)
    
    load_dotenv()
    
    try:
        # Import Firebase Admin SDK
        import firebase_admin
        from firebase_admin import credentials, messaging
        
        # Initialize Firebase Admin SDK
        if not firebase_admin._apps:
            service_account_path = os.getenv('FCM_SERVICE_ACCOUNT_PATH', 'firebase-service-account-fixed.json')
            cred = credentials.Certificate(service_account_path)
            firebase_app = firebase_admin.initialize_app(cred)
            print("✅ Firebase Admin SDK initialized")
        
        # Get user from database
        with app.app_context():
            user_email = "yogeshas91889@gmail.com"
            auth_record = DeliveryGuyAuth.query.filter_by(email=user_email).first()
            
            if not auth_record:
                print(f"❌ User not found: {user_email}")
                return False
            
            print(f"✅ User found: {auth_record.email}")
            print(f"📱 Current device token: {auth_record.device_token}")
            print(f"📱 Platform: {auth_record.platform}")
            print(f"🔔 Notifications enabled: {auth_record.is_notifications_enabled}")
            
            # Check if we have a real FCM token
            if not auth_record.device_token or auth_record.device_token.startswith('fA'):
                print("\n⚠️ No real FCM token found!")
                print("💡 Please get the real FCM token from your Flutter app first")
                print("📱 Run your Flutter app and check the console for FCM token")
                print("🔍 Then run: python3 validate_fcm_token.py YOUR_REAL_FCM_TOKEN")
                return False
            
            # Send Flutter-specific notifications
            print("\n📱 Sending Flutter Notifications...")
            
            flutter_notifications = [
                {
                    "title": "🚀 Flutter App Test",
                    "body": "Testing notifications in your Flutter app!",
                    "data": {"type": "flutter_test", "platform": "flutter"}
                },
                {
                    "title": "📱 Flutter Notification",
                    "body": "This notification is sent to your Flutter app!",
                    "data": {"type": "flutter_notification", "platform": "flutter"}
                },
                {
                    "title": "🎉 Flutter Working!",
                    "body": "Your Flutter notification system is working perfectly!",
                    "data": {"type": "flutter_success", "platform": "flutter"}
                },
                {
                    "title": "🚚 New Delivery Assignment",
                    "body": "You have a new delivery order! Tap to view details.",
                    "data": {
                        "type": "delivery_assignment",
                        "order_id": "12345",
                        "platform": "flutter",
                        "action": "view_order"
                    }
                },
                {
                    "title": "💰 Earnings Update",
                    "body": "Your earnings have been updated! Check your wallet.",
                    "data": {
                        "type": "earnings_update",
                        "amount": "₹500",
                        "platform": "flutter",
                        "action": "view_earnings"
                    }
                }
            ]
            
            success_count = 0
            
            for i, notif in enumerate(flutter_notifications, 1):
                print(f"\n📨 Sending Flutter notification {i}...")
                print(f"   Title: {notif['title']}")
                print(f"   Body: {notif['body']}")
                
                message = messaging.Message(
                    notification=messaging.Notification(
                        title=notif["title"],
                        body=notif["body"]
                    ),
                    data=notif["data"],
                    token=auth_record.device_token,
                    apns=messaging.APNSConfig(
                        payload=messaging.APNSPayload(
                            aps=messaging.Aps(
                                alert=messaging.ApsAlert(
                                    title=notif["title"],
                                    body=notif["body"]
                                ),
                                sound="default",
                                badge=1
                            )
                        )
                    )
                )
                
                try:
                    response = messaging.send(message)
                    print(f"   ✅ Sent successfully! Message ID: {response}")
                    success_count += 1
                except Exception as e:
                    print(f"   ❌ Failed: {str(e)}")
            
            print(f"\n📊 Flutter Notification Results:")
            print(f"   ✅ Successful: {success_count}/{len(flutter_notifications)}")
            print(f"   ❌ Failed: {len(flutter_notifications) - success_count}/{len(flutter_notifications)}")
            
            if success_count > 0:
                print("\n🎉 Flutter notifications are working!")
                print("📱 Check your Flutter app for notifications!")
                return True
            else:
                print("\n❌ All Flutter notifications failed")
                return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def update_user_with_real_token(real_fcm_token):
    """Update user with real FCM token"""
    print(f"\n📱 Updating user with real FCM token...")
    
    try:
        with app.app_context():
            user_email = "yogeshas91889@gmail.com"
            auth_record = DeliveryGuyAuth.query.filter_by(email=user_email).first()
            
            if not auth_record:
                print(f"❌ User not found: {user_email}")
                return False
            
            # Update with real FCM token
            auth_record.device_token = real_fcm_token
            auth_record.platform = "ios"
            auth_record.is_notifications_enabled = True
            db.session.commit()
            
            print("✅ User updated with real FCM token")
            print(f"📱 New device token: {real_fcm_token[:20]}...")
            print(f"📱 Platform: {auth_record.platform}")
            print(f"🔔 Notifications: {auth_record.is_notifications_enabled}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error updating user: {str(e)}")
        return False

def main():
    """Main function"""
    print("🚀 ZinToo Flutter Notification Test")
    print("=" * 60)
    
    # Check if FCM token provided as argument
    if len(sys.argv) > 1:
        real_fcm_token = sys.argv[1]
        print(f"📱 Using provided FCM token: {real_fcm_token[:20]}...")
        
        # Update user with real token
        if update_user_with_real_token(real_fcm_token):
            # Test Flutter notifications
            test_flutter_notifications()
        else:
            print("❌ Failed to update user with real token")
    else:
        # Test with current token in database
        test_flutter_notifications()
        
        print("\n💡 To test with real FCM token from Flutter:")
        print("python3 test_flutter_notifications.py YOUR_REAL_FCM_TOKEN")

if __name__ == "__main__":
    main()
