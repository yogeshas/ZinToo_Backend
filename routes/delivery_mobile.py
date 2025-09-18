# routes/delivery_mobile.py
from flask import Blueprint, request, jsonify
from services.delivery_auth_service import (
    verify_auth_token, 
    send_otp, 
    verify_otp, 
    create_delivery_auth, 
    login_delivery_guy
)
from services.delivery_onboarding_service import get_onboarding_by_id, update_onboarding
from utils.crypto import encrypt_payload, decrypt_payload
from utils.sns_service import sns_service
from models.order import Order
from models.delivery_onboarding import DeliveryOnboarding
from models.delivery_auth import DeliveryGuyAuth
from extensions import db
from functools import wraps
from datetime import datetime

delivery_mobile_bp = Blueprint("delivery_mobile", __name__)

# ============================================================================
# AUTHENTICATION ROUTES (No auth required)
# ============================================================================

@delivery_mobile_bp.route("/auth/send-otp", methods=["POST"])
def send_otp_route():
    """Send OTP to email for delivery personnel"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        email = data.get("email")
        if not email:
            return jsonify({"error": "Email is required"}), 400
        
        result = send_otp(email)
        
        if result["success"]:
            return jsonify({
                "success": True, 
                "message": "OTP sent successfully"
            }), 200
        else:
            return jsonify({"error": result["message"]}), 400
            
    except Exception as e:
        print(f"Send OTP error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@delivery_mobile_bp.route("/auth/verify-otp", methods=["POST"])
def verify_otp_route():
    """Verify OTP for delivery personnel"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        email = data.get("email")
        otp_code = data.get("otp")
        
        if not email or not otp_code:
            return jsonify({"error": "Email and OTP are required"}), 400
        
        result = verify_otp(email, otp_code)
        
        if result["success"]:
            # Return response in format expected by Flutter app
            response_data = {
                "success": True,
                "is_new_user": result.get("is_new_user", False),
                "is_onboarded": result.get("is_onboarded", False),
                "auth_token": result.get("auth_token"),
                "user": result.get("user", {}),
                "message": result.get("message", "OTP verified successfully")
            }
            
            return jsonify(response_data), 200
        else:
            return jsonify({"error": result["message"]}), 400
            
    except Exception as e:
        print(f"Verify OTP error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@delivery_mobile_bp.route("/auth/register", methods=["POST"])
def register_route():
    """Register new delivery personnel"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        email = data.get("email")
        phone_number = data.get("phone_number")
        password = data.get("password")
        
        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400
        
        result = create_delivery_auth(email, phone_number, password)
        
        if result["success"]:
            return jsonify({
                "success": True, 
                "message": "Account created successfully",
                "auth": result["auth"]
            }), 201
        else:
            return jsonify({"error": result["message"]}), 400
            
    except Exception as e:
        print(f"Register error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@delivery_mobile_bp.route("/auth/login", methods=["POST"])
def login_route():
    """Login delivery personnel"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        email = data.get("email")
        password = data.get("password")
        
        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400
        
        result = login_delivery_guy(email, password)
        
        if result["success"]:
            return jsonify({
                "success": True, 
                "message": "Login successful",
                "auth_token": result["auth_token"],
                "user": result["user"]
            }), 200
        else:
            return jsonify({"error": result["message"]}), 400
            
    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

# ============================================================================
# PROTECTED ROUTES (Require auth)
# ============================================================================

def require_delivery_auth(f):
    """Decorator to require delivery guy authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Missing or invalid authorization header"}), 401
        
        token = auth_header.split(' ')[1]
        result = verify_auth_token(token)
        
        if not result["success"]:
            return jsonify({"error": result["message"]}), 401
        
        # Add user info to request
        request.delivery_user = result["user"]
        
        # Get onboarding info
        if result["user"]["delivery_guy_id"]:
            onboarding = DeliveryOnboarding.query.get(result["user"]["delivery_guy_id"])
            if onboarding and onboarding.status == "approved":
                request.delivery_guy = {
                    "id": onboarding.id,
                    "name": f"{onboarding.first_name} {onboarding.last_name}".strip(),
                    "phone_number": onboarding.primary_number,
                    "email": onboarding.email,
                    "vehicle_number": onboarding.vehicle_number,
                    "vehicle_type": "bike",
                    "status": "active"
                }
            else:
                return jsonify({"error": "Delivery guy not approved"}), 403
        else:
            return jsonify({"error": "Delivery guy not onboarded"}), 403
        
        return f(*args, **kwargs)
    return decorated_function

@delivery_mobile_bp.route("/dashboard", methods=["GET"])
@require_delivery_auth
def get_dashboard():
    """Get delivery guy dashboard"""
    try:
        delivery_guy_id = request.delivery_guy["id"]
        result = get_delivery_guy_dashboard(delivery_guy_id)
        
        if not result["success"]:
            return jsonify({"error": result["message"]}), 400
        
        data = result["data"]
        enc = encrypt_payload(data)
        return jsonify({"success": True, "encrypted_data": enc}), 200
        
    except Exception as e:
        print(f"Get dashboard error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@delivery_mobile_bp.route("/orders", methods=["GET"])
@require_delivery_auth
def get_orders():
    """Get all orders assigned to delivery guy"""
    try:
        delivery_guy_id = request.delivery_guy["id"]
        orders = get_orders_by_delivery_guy(delivery_guy_id)
        orders_data = [order.as_dict() for order in orders]
        
        data = {"orders": orders_data}
        enc = encrypt_payload(data)
        return jsonify({"success": True, "encrypted_data": enc}), 200
        
    except Exception as e:
        print(f"Get orders error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@delivery_mobile_bp.route("/orders/active", methods=["GET"])
@require_delivery_auth
def get_active_orders():
    """Get active orders assigned to delivery guy"""
    try:
        delivery_guy_id = request.delivery_guy["id"]
        orders = get_orders_by_delivery_guy(delivery_guy_id)
        
        # Filter active orders
        active_orders = [order for order in orders if order.status in ['confirmed', 'processing', 'shipped', 'out_for_delivery']]
        orders_data = [order.as_dict() for order in active_orders]
        
        data = {"orders": orders_data}
        enc = encrypt_payload(data)
        return jsonify({"success": True, "encrypted_data": enc}), 200
        
    except Exception as e:
        print(f"Get active orders error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@delivery_mobile_bp.route("/profile", methods=["GET"])
@require_delivery_auth
def get_profile():
    """Get delivery guy profile"""
    try:
        profile_data = {
            "delivery_guy": request.delivery_guy,
            "user": request.delivery_user
        }
        
        enc = encrypt_payload(profile_data)
        return jsonify({"success": True, "encrypted_data": enc}), 200
        
    except Exception as e:
        print(f"Get profile error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@delivery_mobile_bp.route("/profile/update", methods=["PUT"])
@require_delivery_auth
def update_profile():
    """Update delivery guy profile"""
    try:
        encrypted_data = request.json.get("payload")
        if not encrypted_data:
            return jsonify({"error": "Missing encrypted payload"}), 400

        data = decrypt_payload(encrypted_data)
        
        # Update onboarding profile
        delivery_guy_id = request.delivery_guy["id"]
        
        # Get onboarding object
        onboarding = DeliveryOnboarding.query.get(delivery_guy_id)
        if not onboarding:
            return jsonify({"error": "Delivery guy not found"}), 404
        
        # Update fields
        if "first_name" in data:
            onboarding.first_name = data["first_name"]
        if "last_name" in data:
            onboarding.last_name = data["last_name"]
        if "phone_number" in data:
            onboarding.primary_number = data["phone_number"]
        if "vehicle_number" in data:
            onboarding.vehicle_number = data["vehicle_number"]
        
        onboarding.updated_at = datetime.utcnow()
        db.session.commit()
        
        updated_profile = onboarding.as_dict()
        enc = encrypt_payload({"delivery_guy": updated_profile})
        return jsonify({"success": True, "encrypted_data": enc}), 200
        
    except Exception as e:
        print(f"Update profile error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

# Helper functions
def get_delivery_guy_dashboard(onboarding_id):
    """Get dashboard data for delivery guy"""
    try:
        # Get onboarding record
        onboarding = DeliveryOnboarding.query.get(onboarding_id)
        if not onboarding:
            return {"success": False, "message": "Delivery guy not found"}
        
        # Get assigned orders
        assigned_orders = Order.query.filter_by(delivery_guy_id=onboarding_id).all()
        
        # Calculate stats
        total_orders = len(assigned_orders)
        active_orders = len([o for o in assigned_orders if o.status in ['confirmed', 'processing', 'shipped', 'out_for_delivery']])
        completed_orders = len([o for o in assigned_orders if o.status == 'delivered'])
        today_orders = len([o for o in assigned_orders if o.created_at.date() == datetime.utcnow().date()])
        
        # Get recent orders
        recent_orders = assigned_orders[-5:] if len(assigned_orders) > 5 else assigned_orders
        
        dashboard_data = {
            "delivery_guy": {
                "id": onboarding.id,
                "name": f"{onboarding.first_name} {onboarding.last_name}".strip(),
                "phone_number": onboarding.primary_number,
                "email": onboarding.email,
                "vehicle_number": onboarding.vehicle_number,
                "vehicle_type": "bike",
                "status": "active"
            },
            "stats": {
                "total_orders": total_orders,
                "active_orders": active_orders,
                "completed_orders": completed_orders,
                "today_orders": today_orders,
                "rating": 0.0,  # Placeholder
                "total_earnings": sum([o.total_amount for o in assigned_orders if o.status == 'delivered'])
            },
            "recent_orders": [order.as_dict() for order in recent_orders]
        }
        
        return {"success": True, "data": dashboard_data}
        
    except Exception as e:
        print(f"Error getting dashboard: {e}")
        return {"success": False, "message": "Failed to get dashboard data"}

def get_orders_by_delivery_guy(onboarding_id):
    """Get orders assigned to delivery guy"""
    try:
        orders = Order.query.filter_by(delivery_guy_id=onboarding_id).all()
        return orders
    except Exception as e:
        print(f"Error getting orders by delivery guy: {e}")
        return []

# ============================================================================
# NOTIFICATION ROUTES (Auth required)
# ============================================================================

@delivery_mobile_bp.route("/notifications/register-device", methods=["POST"])
@require_delivery_auth
def register_device_token():
    """Register device token for push notifications"""
    try:
        encrypted_data = request.json.get("payload")
        if not encrypted_data:
            return jsonify({"error": "Missing encrypted payload"}), 400

        data = decrypt_payload(encrypted_data)
        device_token = data.get("device_token")
        platform = data.get("platform", "android")  # android or ios
        
        if not device_token:
            return jsonify({"error": "Device token is required"}), 400
        
        if platform not in ["android", "ios"]:
            return jsonify({"error": "Platform must be 'android' or 'ios'"}), 400
        
        # Get delivery guy auth record
        delivery_guy_id = request.delivery_guy["id"]
        auth_record = DeliveryGuyAuth.query.filter_by(delivery_guy_id=delivery_guy_id).first()
        
        if not auth_record:
            return jsonify({"error": "Delivery guy auth record not found"}), 404
        
        # Update device token
        auth_record.update_device_token(device_token, platform)
        
        # Create SNS endpoint if using SNS
        if sns_service.android_app_arn or sns_service.ios_app_arn:
            endpoint_result = sns_service.create_platform_endpoint(device_token, platform)
            if endpoint_result["success"]:
                auth_record.sns_endpoint_arn = endpoint_result["endpoint_arn"]
        
        db.session.commit()
        
        response_data = {
            "success": True,
            "message": "Device token registered successfully",
            "platform": platform,
            "notifications_enabled": auth_record.is_notifications_enabled
        }
        
        enc = encrypt_payload(response_data)
        return jsonify({"success": True, "encrypted_data": enc}), 200
        
    except Exception as e:
        print(f"Register device token error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@delivery_mobile_bp.route("/notifications/toggle", methods=["POST"])
@require_delivery_auth
def toggle_notifications():
    """Enable/disable push notifications"""
    try:
        encrypted_data = request.json.get("payload")
        if not encrypted_data:
            return jsonify({"error": "Missing encrypted payload"}), 400

        data = decrypt_payload(encrypted_data)
        enable = data.get("enable", True)
        
        # Get delivery guy auth record
        delivery_guy_id = request.delivery_guy["id"]
        auth_record = DeliveryGuyAuth.query.filter_by(delivery_guy_id=delivery_guy_id).first()
        
        if not auth_record:
            return jsonify({"error": "Delivery guy auth record not found"}), 404
        
        # Toggle notifications
        if enable:
            auth_record.enable_notifications()
            message = "Notifications enabled"
        else:
            auth_record.disable_notifications()
            message = "Notifications disabled"
        
        db.session.commit()
        
        response_data = {
            "success": True,
            "message": message,
            "notifications_enabled": auth_record.is_notifications_enabled
        }
        
        enc = encrypt_payload(response_data)
        return jsonify({"success": True, "encrypted_data": enc}), 200
        
    except Exception as e:
        print(f"Toggle notifications error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@delivery_mobile_bp.route("/notifications/test", methods=["POST"])
@require_delivery_auth
def send_test_notification():
    """Send test notification to delivery guy"""
    try:
        # Get delivery guy auth record
        delivery_guy_id = request.delivery_guy["id"]
        auth_record = DeliveryGuyAuth.query.filter_by(delivery_guy_id=delivery_guy_id).first()
        
        if not auth_record:
            return jsonify({"error": "Delivery guy auth record not found"}), 404
        
        if not auth_record.has_valid_device_token():
            return jsonify({"error": "No valid device token found"}), 400
        
        # Send test notification
        title = "🧪 Test Notification"
        body = "This is a test notification from ZinToo Delivery App"
        
        if auth_record.sns_endpoint_arn:
            # Use SNS
            result = sns_service.send_push_notification(
                auth_record.sns_endpoint_arn, 
                title, 
                body,
                {"type": "test", "timestamp": datetime.utcnow().isoformat()}
            )
        else:
            # Use direct FCM
            result = sns_service.send_direct_fcm_notification(
                auth_record.device_token,
                title,
                body,
                {"type": "test", "timestamp": datetime.utcnow().isoformat()}
            )
        
        if result["success"]:
            response_data = {
                "success": True,
                "message": "Test notification sent successfully"
            }
        else:
            response_data = {
                "success": False,
                "message": f"Failed to send notification: {result['message']}"
            }
        
        enc = encrypt_payload(response_data)
        return jsonify({"success": True, "encrypted_data": enc}), 200
        
    except Exception as e:
        print(f"Send test notification error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
