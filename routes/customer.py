from flask import Blueprint, request, jsonify, current_app
from services.customer_service import (
    create_customer,
    get_customer_by_id,
    get_all_customers,
    get_customer_by_username,
    get_customer_by_email_or_username,
    get_customer_by_email,
    update_customer,
)
from utils.crypto import encrypt_payload, decrypt_payload
from utils.auth import require_admin_auth
import jwt
import os
from datetime import datetime, timedelta
from extensions import db
from sqlalchemy import func, and_, desc
from models.customer import Customer
from models.order import Order, OrderItem


customer_bp = Blueprint("customer", __name__)

@customer_bp.route("/", methods=["GET"])
@require_admin_auth
def list_customers(current_admin):
    customers = get_all_customers()
    data = {"customers": [c.as_dict() for c in customers]}
    enc = encrypt_payload(data)
    return jsonify({"success": True, "encrypted_data": enc})

@customer_bp.route("/<int:cid>", methods=["GET"])
def get_customer(cid):
    c = get_customer_by_id(cid)
    if not c:
        return jsonify({"success": False, "error": "Not found"}), 404
    data = {"customer": c.as_dict()}
    enc = encrypt_payload(data)
    return jsonify({"success": True, "encrypted_data": enc})

@customer_bp.route("/", methods=["POST"])
def create():
    encrypted = request.json.get("data")
    try:
        data = decrypt_payload(encrypted)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400
    # normalize client fields
    if data.get("phone") and not data.get("phone_number"):
        data["phone_number"] = data.pop("phone")
    c = create_customer(data)
    enc = encrypt_payload({"customer": c.as_dict()})
    return jsonify({"success": True, "encrypted_data": enc})

@customer_bp.route("/register", methods=["POST"])
def register():
    encrypted = request.json.get("data")
    try:
        data = decrypt_payload(encrypted)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400
    # normalize client fields
    if data.get("phone") and not data.get("phone_number"):
        data["phone_number"] = data.pop("phone")
    
    # Handle referral code
    referral_code = data.get("referral_code")
    if referral_code:
        # Validate referral code
        from services.referral_service import validate_referral_code
        if not validate_referral_code(referral_code):
            return jsonify({"success": False, "error": "Invalid referral code"}), 400
        data["referral_code_used"] = referral_code
    
    # duplicate checks
    if not data.get("email"):
        return jsonify({"success": False, "error": "Email is required"}), 400
    if get_customer_by_email(data["email"]):
        # mirror admin duplication semantics
        return jsonify({"success": False, "error": "Email already registered"}), 409
    if data.get("username") and get_customer_by_username(data["username"]):
        return jsonify({"success": False, "error": "Username already taken"}), 409
    try:
        customer = create_customer(data)
        payload = {"customer": customer.as_dict()}
        enc = encrypt_payload(payload)
        return jsonify({"success": True, "encrypted_data": enc}), 201
    except Exception as e:
        # Ensure 500 returns JSON (not HTML) to help frontend error handling
        return jsonify({"success": False, "error": f"Register failed: {str(e)}"}), 500

@customer_bp.route("/login", methods=["POST"])
def login():
    encrypted = request.json.get("data")
    try:
        data = decrypt_payload(encrypted)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400
    # social login path
    if data.get("provider") and data.get("provider_id"):
        # trust provider email as username fallback
        username = data.get("username") or data.get("email")
        customer = get_customer_by_username(username)
        if not customer:
            # auto-register minimal account
            customer = create_customer({
                "username": username,
                "email": data.get("email") or f"{data.get('provider_id')}@social.local",
                "password": jwt.encode({"tmp": True}, os.getenv("SECRET_KEY"), algorithm="HS256"),
                "status": "social",
            })
        else:
            # Check if existing social login customer is blocked
            if customer.status == "blocked":
                return jsonify({"success": False, "error": "Your account has been blocked. Please contact support for assistance."}), 403
    else:
        identifier = data.get("username") or data.get("email")
        customer = get_customer_by_email_or_username(identifier)
        if not customer or not customer.check_password(data["password"]):
            return jsonify({"success": False, "error": "Invalid email/username or password"}), 401
        
        # Check if customer is blocked
        if customer.status == "blocked":
            return jsonify({"success": False, "error": "Your account has been blocked. Please contact support for assistance."}), 403
        
        # Auto-migrate legacy hashes to bcrypt
        try:
            if not str(customer.password_hash).startswith(("$2a$", "$2b$", "$2y$")):
                customer.set_password(data["password"])  # rehash to bcrypt
                db.session.commit()
        except Exception:
            db.session.rollback()

    payload = {
        "id": customer.id,
        "username": customer.username,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    secret_key = current_app.config.get("SECRET_KEY") or "dev-secret-key"
    try:
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        enc = encrypt_payload({"token": token, "user": customer.as_dict()})
        return jsonify({"success": True, "encrypted_data": enc}), 200
    except Exception as e:
        return jsonify({"success": False, "error": f"Login failed: {str(e)}"}), 500

@customer_bp.route("/google/register", methods=["POST"])
def google_register():
    """Register user with Google OAuth data - Frontend compatibility endpoint"""
    encrypted = request.json.get("data")
    try:
        data = decrypt_payload(encrypted)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400
    
    email = data.get("email")
    name = data.get("name", "")
    google_id = data.get("google_id")
    
    if not email:
        return jsonify({"success": False, "error": "Email is required"}), 400
    
    # Check if user already exists
    if get_customer_by_email(email):
        return jsonify({"success": False, "error": "Email already registered"}), 409
    
    try:
        # Create customer with Google OAuth data
        customer_data = {
            "username": email.split("@")[0],  # Use email prefix as username
            "email": email,
            "password": jwt.encode({"google_oauth": True, "google_id": google_id}, 
                                 current_app.config.get("SECRET_KEY"), algorithm="HS256"),
            "status": "active",
            "google_id": google_id,
            "name": name
        }
        
        customer = create_customer(customer_data)
        
        # Create JWT token
        payload = {
            "id": customer.id,
            "username": customer.username,
            "exp": datetime.utcnow() + timedelta(hours=24)
        }
        
        secret_key = current_app.config.get("SECRET_KEY") or "dev-secret-key"
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        
        # Encrypt the response
        response_data = {
            "token": token,
            "user": customer.as_dict()
        }
        enc = encrypt_payload(response_data)
        
        return jsonify({
            "success": True,
            "encrypted_data": enc
        }), 201
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Registration failed: {str(e)}"
        }), 500

@customer_bp.route("/<int:cid>", methods=["PUT", "PATCH"])
@require_admin_auth
def update_customer_route(current_admin, cid):
    encrypted = request.json.get("data")
    if not encrypted:
        return jsonify({"success": False, "error": "Missing data"}), 400
    try:
        data = decrypt_payload(encrypted)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400
    c = get_customer_by_id(cid)
    if not c:
        return jsonify({"success": False, "error": "Not found"}), 404
    try:
        updated = update_customer(cid, data)
        enc = encrypt_payload({"customer": updated.as_dict()})
        return jsonify({"success": True, "encrypted_data": enc}), 200
    except Exception as e:
        return jsonify({"success": False, "error": f"Update failed: {str(e)}"}), 500

@customer_bp.route("/<int:cid>", methods=["DELETE"])
@require_admin_auth
def delete_customer_route(current_admin, cid):
    c = get_customer_by_id(cid)
    if not c:
        return jsonify({"success": False, "error": "Customer not found"}), 404
    try:
        from services.customer_service import delete_customer
        delete_customer(cid)
        return jsonify({"success": True, "message": "Customer deleted successfully"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": f"Delete failed: {str(e)}"}), 500

@customer_bp.route("/<int:cid>/block", methods=["POST"])
@require_admin_auth
def block_customer_route(current_admin, cid):
    c = get_customer_by_id(cid)
    if not c:
        return jsonify({"success": False, "error": "Customer not found"}), 404
    
    try:
        data = request.json
        blocked = data.get("blocked", True)
        
        from services.customer_service import set_customer_blocked
        updated = set_customer_blocked(cid, blocked)
        
        if updated:
            enc = encrypt_payload({"customer": updated.as_dict()})
            return jsonify({"success": True, "encrypted_data": enc}), 200
        else:
            return jsonify({"success": False, "error": "Failed to update customer status"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": f"Block/Unblock failed: {str(e)}"}), 500

@customer_bp.route("/analytics", methods=["GET"])
# @require_admin_auth  # Temporarily disabled for testing
def get_customer_analytics():
    """
    Get customer analytics for dashboard
    Returns: new customers (last 6 days), active customers (not blocked), 
    top repeat customers (top 2 by order count), total customers
    """
    try:
        now = datetime.utcnow()
        six_days_ago = now - timedelta(days=6)
        
        # 1. New Customers - Last 6 days including today
        new_customers = Customer.query.filter(
            Customer.id.in_(
                db.session.query(Order.customer_id)
                .filter(Order.created_at >= six_days_ago)
                .distinct()
            )
        ).count()
        
        # 2. Active Customers - Not blocked customers (status != 'blocked')
        active_customers = Customer.query.filter(
            and_(
                Customer.status != 'blocked',
                Customer.status != 'suspended'
            )
        ).count()
        
        # 3. Top Repeat Customers - Top 2 customers by order count
        top_customers = db.session.query(
            Order.customer_id,
            func.count(Order.id).label('order_count')
        ).group_by(Order.customer_id).order_by(desc('order_count')).limit(2).all()
        
        repeat_customers = len(top_customers)
        
        # 4. Total Customers - Total count from customer table
        total_customers = Customer.query.count()
        
        # Additional breakdown data for doughnut charts
        blocked_customers = Customer.query.filter(Customer.status == 'blocked').count()
        suspended_customers = Customer.query.filter(Customer.status == 'suspended').count()
        
        # Previous 6 days for comparison
        twelve_days_ago = now - timedelta(days=12)
        previous_new_customers = Customer.query.filter(
            Customer.id.in_(
                db.session.query(Order.customer_id)
                .filter(
                    and_(
                        Order.created_at >= twelve_days_ago,
                        Order.created_at < six_days_ago
                    )
                )
                .distinct()
            )
        ).count()
        
        return jsonify({
            "success": True,
            "data": {
                "new_customers": new_customers,
                "active_customers": active_customers,
                "repeat_customers": repeat_customers,
                "total_customers": total_customers,
                "breakdown": {
                    "blocked_customers": blocked_customers,
                    "suspended_customers": suspended_customers,
                    "previous_new_customers": previous_new_customers
                },
                "top_customers": [
                    {
                        "customer_id": customer_id,
                        "order_count": order_count
                    }
                    for customer_id, order_count in top_customers
                ]
            }
        })
        
    except Exception as e:
        print(f"Error getting customer analytics: {e}")
        return jsonify({"success": False, "error": "Internal server error", "details": str(e)}), 500
