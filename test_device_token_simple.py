#!/usr/bin/env python3
"""
Test Device Token Simple - Test device token without AWS SNS
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

def test_device_token_simple(device_token, platform='ios'):
    """Test device token registration without AWS SNS"""
    print("📱 Testing Device Token Registration")
    print("=" * 50)
    
    load_dotenv()
    
    try:
        with app.app_context():
            user_email = "yogeshas91889@gmail.com"
            auth_record = DeliveryGuyAuth.query.filter_by(email=user_email).first()
            
            if not auth_record:
                print(f"❌ User not found: {user_email}")
                return False
            
            print(f"✅ User found: {auth_record.email}")
            print(f"📱 Current device token: {auth_record.device_token}")
            print(f"📱 Current platform: {auth_record.platform}")
            
            # Update user with device token
            print(f"\n📱 Updating user with device token...")
            auth_record.device_token = device_token
            auth_record.platform = platform
            auth_record.is_notifications_enabled = True
            db.session.commit()
            
            print("✅ User updated successfully!")
            print(f"📱 New device token: {device_token}")
            print(f"📱 Platform: {platform}")
            print(f"🔔 Notifications enabled: {auth_record.is_notifications_enabled}")
            
            # Test notification data structure
            print(f"\n📨 Testing notification data structure...")
            notification_data = {
                "title": "🎉 ZinToo Delivery Notification!",
                "body": f"Hello {user_email}! This is a test notification from ZinToo Delivery App!",
                "data": {
                    "type": "test_notification",
                    "platform": platform,
                    "user_email": user_email,
                    "device_token": device_token
                }
            }
            
            print(f"📨 Title: {notification_data['title']}")
            print(f"📨 Body: {notification_data['body']}")
            print(f"📊 Data: {notification_data['data']}")
            
            print(f"\n🎉 Device token registration successful!")
            print(f"📱 Your device token is now stored in the database")
            print(f"🔔 Ready for AWS SNS configuration!")
            
            return True
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def main():
    """Main function"""
    print("🚀 ZinToo Device Token Test")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        device_token = sys.argv[1]
        platform = sys.argv[2] if len(sys.argv) > 2 else 'ios'
        
        print(f"📱 Testing device token: {device_token}")
        print(f"📱 Platform: {platform}")
        
        success = test_device_token_simple(device_token, platform)
        
        if success:
            print("\n🎉 Device token test successful!")
            print("📱 Device token is now registered in database")
            print("🔧 Next step: Configure AWS SNS Platform ARNs")
        else:
            print("\n❌ Device token test failed")
    else:
        print("💡 Usage: python3 test_device_token_simple.py DEVICE_TOKEN [PLATFORM]")
        print("📱 Example: python3 test_device_token_simple.py ios_1757838401815_401815 ios")

if __name__ == "__main__":
    main()
