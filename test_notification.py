#!/usr/bin/env python3
"""
Test Notification Script
Send a test notification to a specific user
"""

import requests
import json
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import Flask app and create context
from app import app
from utils.sns_service import sns_service
from models.delivery_auth import DeliveryGuyAuth
from extensions import db

def test_notification_to_user(email):
    """Send test notification to specific user by email"""
    
    print(f"🧪 Testing notification for user: {email}")
    
    try:
        # Create Flask application context
        with app.app_context():
            # Find user by email
            auth_record = DeliveryGuyAuth.query.filter_by(email=email).first()
            
            if not auth_record:
                print(f"❌ User not found: {email}")
                return False
            
            print(f"✅ User found: {auth_record.email}")
            print(f"📱 Device token: {auth_record.device_token}")
            print(f"📱 Platform: {auth_record.platform}")
            print(f"🔔 Notifications enabled: {auth_record.is_notifications_enabled}")
            
            if not auth_record.has_valid_device_token():
                print("❌ No valid device token found for this user")
                return False
        
        # Send test notification
        title = "🧪 Test Notification from ZinToo"
        body = f"Hello {email}! This is a test notification from ZinToo Delivery App."
        
        data = {
            "type": "test",
            "user_email": email,
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        if auth_record.sns_endpoint_arn:
            # Use SNS
            print("📤 Sending via AWS SNS...")
            result = sns_service.send_push_notification(
                auth_record.sns_endpoint_arn, 
                title, 
                body,
                data
            )
        else:
            # Use direct FCM
            print("📤 Sending via FCM...")
            result = sns_service.send_direct_fcm_notification(
                auth_record.device_token,
                title,
                body,
                data
            )
        
        if result["success"]:
            print("✅ Test notification sent successfully!")
            print(f"📨 Message ID: {result.get('message_id', 'N/A')}")
            return True
        else:
            print(f"❌ Failed to send notification: {result['message']}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending test notification: {str(e)}")
        return False

def test_via_api(email, auth_token):
    """Test notification via API endpoint"""
    
    print(f"🧪 Testing notification via API for user: {email}")
    
    try:
        url = "http://localhost:5000/api/delivery-mobile/notifications/test"
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, headers=headers, json={})
        
        print(f"📱 API Response: {response.status_code}")
        print(f"📱 Response Body: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print("✅ Test notification sent via API!")
                return True
            else:
                print(f"❌ API Error: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing via API: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 ZinToo Notification Test")
    print("=" * 50)
    
    # Test user email
    test_email = "yogeshas91889@gmail.com"
    
    # Test 1: Direct notification sending
    print("\n1️⃣ Testing direct notification...")
    success1 = test_notification_to_user(test_email)
    
    # Test 2: Via API (you'll need to provide a valid auth token)
    print("\n2️⃣ Testing via API...")
    print("⚠️ Note: You need to provide a valid auth token for API testing")
    # success2 = test_via_api(test_email, "YOUR_AUTH_TOKEN_HERE")
    
    print("\n" + "=" * 50)
    if success1:
        print("🎉 Notification test completed successfully!")
    else:
        print("❌ Notification test failed. Check the logs above.")
