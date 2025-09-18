#!/usr/bin/env python3
"""
AWS SNS Notification - Send notifications using AWS SNS
"""

import sys
import os
import boto3
import json
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import Flask app and create context
from app import app
from models.delivery_auth import DeliveryGuyAuth
from extensions import db

def create_sns_client():
    """Create AWS SNS client"""
    try:
        sns_client = boto3.client(
            'sns',
            region_name=os.getenv('AWS_REGION', 'ap-south-1'),
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        print("✅ AWS SNS client created successfully")
        return sns_client
    except Exception as e:
        print(f"❌ Error creating SNS client: {str(e)}")
        return None

def create_platform_endpoint(sns_client, device_token, platform):
    """Create SNS platform endpoint for device token"""
    try:
        # Determine platform application ARN based on platform
        if platform.lower() == 'ios':
            platform_arn = os.getenv('SNS_APPLICATION_ARN_IOS')
        elif platform.lower() == 'android':
            platform_arn = os.getenv('SNS_APPLICATION_ARN_ANDROID')
        else:
            print(f"❌ Unsupported platform: {platform}")
            return None
        
        if not platform_arn:
            print(f"❌ Platform ARN not configured for {platform}")
            return None
        
        # Create platform endpoint
        response = sns_client.create_platform_endpoint(
            PlatformApplicationArn=platform_arn,
            Token=device_token,
            CustomUserData=f"ZinToo Delivery App - {platform}"
        )
        
        endpoint_arn = response['EndpointArn']
        print(f"✅ Platform endpoint created: {endpoint_arn}")
        return endpoint_arn
        
    except Exception as e:
        print(f"❌ Error creating platform endpoint: {str(e)}")
        return None

def send_sns_notification(sns_client, endpoint_arn, title, body, data=None):
    """Send notification via SNS"""
    try:
        # Create message payload
        message = {
            "default": f"{title}: {body}",
            "APNS": json.dumps({
                "aps": {
                    "alert": {
                        "title": title,
                        "body": body
                    },
                    "sound": "default",
                    "badge": 1
                },
                "data": data or {}
            }),
            "GCM": json.dumps({
                "notification": {
                    "title": title,
                    "body": body,
                    "sound": "default"
                },
                "data": data or {}
            })
        }
        
        # Send notification
        response = sns_client.publish(
            TargetArn=endpoint_arn,
            Message=json.dumps(message),
            MessageStructure='json'
        )
        
        print(f"✅ SNS notification sent successfully!")
        print(f"📨 Message ID: {response['MessageId']}")
        return True
        
    except Exception as e:
        print(f"❌ Error sending SNS notification: {str(e)}")
        return False

def send_real_sns_notification(device_token, platform='ios'):
    """Send real notification using AWS SNS"""
    print("📱 Sending Real SNS Notification")
    print("=" * 50)
    
    load_dotenv()
    
    # Create SNS client
    sns_client = create_sns_client()
    if not sns_client:
        return False
    
    # Create platform endpoint
    endpoint_arn = create_platform_endpoint(sns_client, device_token, platform)
    if not endpoint_arn:
        return False
    
    # Update user in database
    with app.app_context():
        user_email = "yogeshas91889@gmail.com"
        auth_record = DeliveryGuyAuth.query.filter_by(email=user_email).first()
        
        if not auth_record:
            print(f"❌ User not found: {user_email}")
            return False
        
        # Update user with device token and endpoint ARN
        auth_record.device_token = device_token
        auth_record.platform = platform
        auth_record.sns_endpoint_arn = endpoint_arn
        auth_record.is_notifications_enabled = True
        db.session.commit()
        
        print(f"✅ User updated with device token and SNS endpoint")
        print(f"📱 Device token: {device_token[:20]}...")
        print(f"📱 Platform: {platform}")
        print(f"🔗 SNS Endpoint: {endpoint_arn[:50]}...")
    
    # Send test notification
    print("\n📨 Sending Test Notification...")
    
    success = send_sns_notification(
        sns_client,
        endpoint_arn,
        "🎉 ZinToo Delivery Notification!",
        f"Hello! This is a real notification from ZinToo Delivery App!",
        {
            "type": "test_notification",
            "platform": platform,
            "user_email": user_email
        }
    )
    
    if success:
        print("\n🎉 Real SNS notification sent successfully!")
        print("📱 Check your device for the notification!")
    
    return success

def main():
    """Main function"""
    print("🚀 ZinToo AWS SNS Notification Sender")
    print("=" * 60)
    
    if len(sys.argv) > 2:
        device_token = sys.argv[1]
        platform = sys.argv[2]
        print(f"📱 Using device token: {device_token[:20]}...")
        print(f"📱 Platform: {platform}")
        
        success = send_real_sns_notification(device_token, platform)
        
        if success:
            print("\n🎉 Real SNS notification sent successfully!")
            print("📱 Check your device for the notification!")
        else:
            print("\n❌ Real SNS notification failed")
    else:
        print("💡 Usage: python3 aws_sns_notification.py DEVICE_TOKEN PLATFORM")
        print("📱 Example: python3 aws_sns_notification.py YOUR_DEVICE_TOKEN ios")
        print("📱 Get device token from your Flutter app first")

if __name__ == "__main__":
    main()
