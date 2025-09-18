#!/usr/bin/env python3
"""
Direct SNS Test - Test AWS SNS without user registration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from utils.sns_service import sns_service

def test_sns_direct():
    """Test SNS service directly"""
    
    print("🧪 Testing AWS SNS Service Directly")
    print("=" * 50)
    
    try:
        # Test SNS service initialization
        print("1️⃣ Testing SNS Service Initialization...")
        print(f"✅ SNS Service initialized: {sns_service is not None}")
        print(f"📱 Android App ARN: {sns_service.android_app_arn}")
        print(f"📱 iOS App ARN: {sns_service.ios_app_arn}")
        print(f"🔑 FCM Server Key: {'Set' if sns_service.fcm_server_key else 'Not Set'}")
        
        # Test creating a platform endpoint (mock)
        print("\n2️⃣ Testing Platform Endpoint Creation...")
        mock_device_token = "test_device_token_12345"
        platform = "android"
        
        result = sns_service.create_platform_endpoint(mock_device_token, platform)
        print(f"📱 Endpoint Creation Result: {result}")
        
        if result["success"]:
            endpoint_arn = result["endpoint_arn"]
            print(f"✅ Endpoint ARN: {endpoint_arn}")
            
            # Test sending notification
            print("\n3️⃣ Testing Push Notification...")
            title = "🧪 Test Notification from ZinToo"
            body = "This is a test notification to verify SNS is working!"
            data = {"type": "test", "message": "SNS test successful"}
            
            notification_result = sns_service.send_push_notification(
                endpoint_arn, title, body, data
            )
            
            print(f"📨 Notification Result: {notification_result}")
            
            if notification_result["success"]:
                print("✅ SNS notification sent successfully!")
                print(f"📨 Message ID: {notification_result.get('message_id', 'N/A')}")
            else:
                print(f"❌ SNS notification failed: {notification_result['message']}")
        else:
            print(f"❌ Endpoint creation failed: {result['message']}")
            
    except Exception as e:
        print(f"❌ Error testing SNS: {str(e)}")

if __name__ == "__main__":
    with app.app_context():
        test_sns_direct()
