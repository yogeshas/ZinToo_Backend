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
        identifier = data.get("username") or data.get("email")
        customer = get_customer_by_email_or_username(identifier)
        if not customer or not customer.check_password(data["password"]):
            return jsonify({"success": False, "error": "Invalid email/username or password"}), 401
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
