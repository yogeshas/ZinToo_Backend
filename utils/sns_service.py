# utils/sns_service.py
import boto3
import json
import requests
from botocore.exceptions import ClientError, NoCredentialsError
from config import Config
import logging

logger = logging.getLogger(__name__)

class SNSService:
    def __init__(self):
        """Initialize SNS client with configuration from environment variables"""
        try:
            # Validate required environment variables are set
            if not Config.AWS_ACCESS_KEY_ID:
                raise ValueError("❌ AWS_ACCESS_KEY_ID environment variable is required")
            if not Config.AWS_SECRET_ACCESS_KEY:
                raise ValueError("❌ AWS_SECRET_ACCESS_KEY environment variable is required")
            if not Config.AWS_REGION:
                raise ValueError("❌ AWS_REGION environment variable is required")
            
            # Initialize SNS client with environment variables
            self.sns_client = boto3.client(
                'sns',
                aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
                region_name=Config.AWS_REGION
            )
            
            # Set application ARNs from environment
            self.android_app_arn = Config.SNS_APPLICATION_ARN_ANDROID
            self.ios_app_arn = Config.SNS_APPLICATION_ARN_IOS
            self.fcm_server_key = Config.FCM_SERVER_KEY
            
            logger.info("✅ SNS Service initialized successfully")
            
        except NoCredentialsError:
            logger.error("❌ AWS credentials not found")
            raise
        except Exception as e:
            logger.error(f"❌ Error initializing SNS service: {str(e)}")
            raise

    def create_platform_endpoint(self, device_token, platform="android"):
        """Create a platform endpoint for a device token"""
        try:
            app_arn = self.android_app_arn if platform.lower() == "android" else self.ios_app_arn
            
            if not app_arn:
                raise ValueError(f"❌ {platform.upper()} application ARN not configured")
            
            response = self.sns_client.create_platform_endpoint(
                PlatformApplicationArn=app_arn,
                Token=device_token,
                CustomUserData=f"delivery_app_{platform}"
            )
            
            return {
                "success": True,
                "endpoint_arn": response['EndpointArn'],
                "message": f"Platform endpoint created for {platform}"
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'InvalidParameter':
                logger.warning(f"⚠️ Invalid device token for {platform}: {device_token}")
                return {"success": False, "message": "Invalid device token"}
            else:
                logger.error(f"❌ AWS SNS error: {str(e)}")
                return {"success": False, "message": f"AWS SNS error: {str(e)}"}
        except Exception as e:
            logger.error(f"❌ Error creating platform endpoint: {str(e)}")
            return {"success": False, "message": f"Error creating platform endpoint: {str(e)}"}

    def send_push_notification(self, endpoint_arn, title, body, data=None):
        """Send push notification to a specific endpoint"""
        try:
            # Prepare message payload
            message = {
                "default": f"{title}: {body}",
                "GCM": json.dumps({
                    "notification": {
                        "title": title,
                        "body": body,
                        "sound": "default",
                        "click_action": "FLUTTER_NOTIFICATION_CLICK"
                    },
                    "data": data or {}
                }),
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
                })
            }
            
            # Send notification
            response = self.sns_client.publish(
                TargetArn=endpoint_arn,
                Message=json.dumps(message),
                MessageStructure='json'
            )
            
            return {
                "success": True,
                "message_id": response['MessageId'],
                "message": "Push notification sent successfully"
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'EndpointDisabled':
                logger.warning(f"⚠️ Endpoint disabled: {endpoint_arn}")
                return {"success": False, "message": "Device endpoint is disabled"}
            else:
                logger.error(f"❌ AWS SNS error: {str(e)}")
                return {"success": False, "message": f"AWS SNS error: {str(e)}"}
        except Exception as e:
            logger.error(f"❌ Error sending push notification: {str(e)}")
            return {"success": False, "message": f"Error sending push notification: {str(e)}"}

    def send_delivery_assignment_notification(self, device_token, platform, order_details):
        """Send delivery assignment notification"""
        try:
            # Create platform endpoint
            endpoint_result = self.create_platform_endpoint(device_token, platform)
            if not endpoint_result["success"]:
                return endpoint_result
            
            endpoint_arn = endpoint_result["endpoint_arn"]
            
            # Prepare notification content
            title = "🚚 New Delivery Assignment"
            body = f"Order #{order_details.get('order_number', 'N/A')} assigned to you"
            
            data = {
                "type": "delivery_assignment",
                "order_id": str(order_details.get('id', '')),
                "order_number": order_details.get('order_number', ''),
                "customer_name": order_details.get('customer_name', ''),
                "delivery_address": order_details.get('delivery_address', ''),
                "total_amount": str(order_details.get('total_amount', 0)),
                "scheduled_time": order_details.get('scheduled_time', ''),
                "priority": "high"
            }
            
            # Send notification
            return self.send_push_notification(endpoint_arn, title, body, data)
            
        except Exception as e:
            logger.error(f"❌ Error sending delivery assignment notification: {str(e)}")
            return {"success": False, "message": f"Error sending notification: {str(e)}"}

    def send_direct_fcm_notification(self, device_token, title, body, data=None):
        """Send notification directly via FCM (alternative to SNS)"""
        try:
            if not self.fcm_server_key:
                return {"success": False, "message": "FCM server key not configured"}
            
            url = "https://fcm.googleapis.com/fcm/send"
            headers = {
                "Authorization": f"key={self.fcm_server_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "to": device_token,
                "notification": {
                    "title": title,
                    "body": body,
                    "sound": "default"
                },
                "data": data or {}
            }
            
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success") == 1:
                    return {"success": True, "message": "FCM notification sent successfully"}
                else:
                    return {"success": False, "message": f"FCM error: {result.get('results', [{}])[0].get('error', 'Unknown error')}"}
            else:
                return {"success": False, "message": f"FCM request failed: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"❌ Error sending FCM notification: {str(e)}")
            return {"success": False, "message": f"Error sending FCM notification: {str(e)}"}

    def delete_endpoint(self, endpoint_arn):
        """Delete a platform endpoint"""
        try:
            self.sns_client.delete_endpoint(EndpointArn=endpoint_arn)
            return {"success": True, "message": "Endpoint deleted successfully"}
        except ClientError as e:
            logger.error(f"❌ Error deleting endpoint: {str(e)}")
            return {"success": False, "message": f"Error deleting endpoint: {str(e)}"}
        except Exception as e:
            logger.error(f"❌ Error deleting endpoint: {str(e)}")
            return {"success": False, "message": f"Error deleting endpoint: {str(e)}"}

# Global instance
sns_service = SNSService()
