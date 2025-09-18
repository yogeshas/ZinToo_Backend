#!/usr/bin/env python3
"""
Test Direct SNS - Test SNS notification directly with endpoint ARN
"""

import sys
import os
import boto3
import json
from dotenv import load_dotenv

def test_direct_sns_notification():
    """Test SNS notification directly with endpoint ARN"""
    print("📱 Testing Direct SNS Notification")
    print("=" * 50)
    
    load_dotenv()
    
    # Your endpoint ARN
    endpoint_arn = "arn:aws:sns:ap-south-1:038237617294:endpoint/GCM/zintoo/a6ee1537-c934-3c81-a002-1c44c37d6b1f"
    device_token = "ios_1757838401815_401815"
    
    print(f"📱 Endpoint ARN: {endpoint_arn}")
    print(f"📱 Device Token: {device_token}")
    
    try:
        # Create SNS client
        sns_client = boto3.client(
            'sns',
            region_name='ap-south-1',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        print("✅ AWS SNS client created successfully")
        
        # Create message payload
        message = {
            "default": "ZinToo Delivery Notification: Hello! This is a test notification from ZinToo Delivery App!",
            "APNS": json.dumps({
                "aps": {
                    "alert": {
                        "title": "🎉 ZinToo Delivery Notification!",
                        "body": "Hello! This is a test notification from ZinToo Delivery App!"
                    },
                    "sound": "default",
                    "badge": 1
                },
                "data": {
                    "type": "test_notification",
                    "platform": "ios",
                    "device_token": device_token
                }
            }),
            "GCM": json.dumps({
                "notification": {
                    "title": "🎉 ZinToo Delivery Notification!",
                    "body": "Hello! This is a test notification from ZinToo Delivery App!",
                    "sound": "default"
                },
                "data": {
                    "type": "test_notification",
                    "platform": "ios",
                    "device_token": device_token
                }
            })
        }
        
        print("\n📨 Sending SNS notification...")
        print(f"📨 Title: 🎉 ZinToo Delivery Notification!")
        print(f"📨 Body: Hello! This is a test notification from ZinToo Delivery App!")
        
        # Send notification
        response = sns_client.publish(
            TargetArn=endpoint_arn,
            Message=json.dumps(message),
            MessageStructure='json'
        )
        
        print("✅ SNS notification sent successfully!")
        print(f"📨 Message ID: {response['MessageId']}")
        print("🎉 Check your device for the notification!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error sending SNS notification: {str(e)}")
        return False

def main():
    """Main function"""
    print("🚀 ZinToo Direct SNS Test")
    print("=" * 50)
    
    success = test_direct_sns_notification()
    
    if success:
        print("\n🎉 Direct SNS notification sent successfully!")
        print("📱 Check your device for the notification!")
    else:
        print("\n❌ Direct SNS notification failed")

if __name__ == "__main__":
    main()
