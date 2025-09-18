#!/usr/bin/env python3
"""
Test SNS Notification - Simple test for AWS SNS notifications
"""

import sys
import os
from dotenv import load_dotenv

def test_sns_notification():
    """Test SNS notification with device token"""
    print("📱 Testing AWS SNS Notification")
    print("=" * 50)
    
    load_dotenv()
    
    # Check if device token provided
    if len(sys.argv) > 1:
        device_token = sys.argv[1]
        platform = sys.argv[2] if len(sys.argv) > 2 else 'ios'
        
        print(f"📱 Device Token: {device_token[:20]}...")
        print(f"📱 Platform: {platform}")
        
        # Import and run the SNS notification
        from aws_sns_notification import send_real_sns_notification
        
        success = send_real_sns_notification(device_token, platform)
        
        if success:
            print("\n🎉 SNS notification test successful!")
            print("📱 Check your device for the notification!")
        else:
            print("\n❌ SNS notification test failed")
    else:
        print("💡 Usage: python3 test_sns_notification.py DEVICE_TOKEN [PLATFORM]")
        print("📱 Example: python3 test_sns_notification.py ios_1234567890_123456 ios")
        print("📱 Get device token from your Flutter app first")

if __name__ == "__main__":
    test_sns_notification()
