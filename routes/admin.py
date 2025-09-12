# routes/admin.py
from flask import Blueprint, request, jsonify, current_app
from services.admin_service import login_user, verify_admin_otp, change_admin_password, logout_admin
from services.forgot_password_service import (
    send_password_reset_otp, 
    verify_password_reset_otp, 
    reset_admin_password, 
    resend_password_reset_otp
)
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import base64, json

admin_bp = Blueprint("admin", __name__)

def decrypt_payload(encrypted_payload: str):
    """Decrypt payload - DEPRECATED: Use utils.crypto instead"""
    # Import the proper decryption function
    from utils.crypto import decrypt_payload as proper_decrypt
    return proper_decrypt(encrypted_payload)

@admin_bp.route("/login", methods=["POST"])
def login():
    try:
        encrypted = request.json.get("payload")
        if not encrypted:
            return jsonify({"error": "Missing payload"}), 400

        data = decrypt_payload(encrypted)
        print(f"[ADMIN LOGIN] Decrypted data: {data}")

        res, status = login_user(data)
        return jsonify(res), status
    except Exception as e:
        print("Login error:", str(e))
        return jsonify({"error": "Decryption or login failed"}), 400

@admin_bp.route("/verify-otp", methods=["POST"])
def verify_otp():
    try:
        encrypted = request.json.get("payload")
        if not encrypted:
            return jsonify({"error": "Missing payload"}), 400

        data = decrypt_payload(encrypted)
        token_uuid = data.get("token_uuid")
        otp_code = data.get("otp_code")

        if not token_uuid or not otp_code:
            return jsonify({"error": "Missing token_uuid or otp_code"}), 400

        res, status = verify_admin_otp(token_uuid, otp_code)
        return jsonify(res), status
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        print("OTP verification error:", str(e))
        return jsonify({"error": "OTP verification failed"}), 400

@admin_bp.route("/resend-otp", methods=["POST"])
def resend_otp():
    try:
        data = request.json
        email = data.get("email")
        
        if not email:
            return jsonify({"error": "Email is required"}), 400
        
        from services.otp_service import generate_otp
        res, status = generate_otp(email)
        return jsonify(res), status
    except Exception as e:
        print("Resend OTP error:", str(e))
        return jsonify({"error": "Failed to resend OTP"}), 400


@admin_bp.route("/change-password", methods=["POST"])
def change_password():
    try:
        # Authorization: Bearer <token>
        auth_header = request.headers.get("Authorization", "")
        token = None
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1].strip()

        if not token:
            return jsonify({"error": "Missing or invalid Authorization header"}), 401

        encrypted = request.json.get("payload")
        if not encrypted:
            return jsonify({"error": "Missing payload"}), 400

        data = decrypt_payload(encrypted)
        old_password = data.get("old_password")
        new_password = data.get("new_password")

        if not old_password or not new_password:
            return jsonify({"error": "Missing old_password or new_password"}), 400

        res, status = change_admin_password(token, old_password, new_password)
        return jsonify(res), status
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        print("Change password error:", str(e))
        return jsonify({"error": "Failed to change password"}), 400


@admin_bp.route("/logout", methods=["POST"])
def logout():
    try:
        auth_header = request.headers.get("Authorization", "")
        token = None
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1].strip()

        # Stateless: just return success; frontend should clear tokens
        res, status = logout_admin(token)
        return jsonify(res), status
    except Exception as e:
        print("Logout error:", str(e))
        return jsonify({"error": "Logout failed"}), 400

# ==================== FORGOT PASSWORD ENDPOINTS ====================

@admin_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    """Send password reset OTP"""
    try:
        encrypted = request.json.get("payload")
        if not encrypted:
            return jsonify({"error": "Missing payload"}), 400

        data = decrypt_payload(encrypted)
        email = data.get("email")
        
        if not email:
            return jsonify({"error": "Email is required"}), 400
        
        print(f"[FORGOT PASSWORD] Request for email: {email}")
        
        res, status = send_password_reset_otp(email)
        return jsonify(res), status
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        print(f"Forgot password error: {str(e)}")
        return jsonify({"error": "Failed to process forgot password request"}), 400

@admin_bp.route("/verify-reset-otp", methods=["POST"])
def verify_reset_otp():
    """Verify password reset OTP"""
    try:
        encrypted = request.json.get("payload")
        if not encrypted:
            return jsonify({"error": "Missing payload"}), 400

        data = decrypt_payload(encrypted)
        email = data.get("email")
        otp = data.get("otp")
        
        if not email or not otp:
            return jsonify({"error": "Email and OTP are required"}), 400
        
        print(f"[VERIFY RESET OTP] Email: {email}, OTP: {otp}")
        
        res, status = verify_password_reset_otp(email, otp)
        return jsonify(res), status
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        print(f"Verify reset OTP error: {str(e)}")
        return jsonify({"error": "Failed to verify OTP"}), 400

@admin_bp.route("/reset-password", methods=["POST"])
def reset_password():
    """Reset admin password after OTP verification"""
    try:
        encrypted = request.json.get("payload")
        if not encrypted:
            return jsonify({"error": "Missing payload"}), 400

        data = decrypt_payload(encrypted)
        email = data.get("email")
        otp = data.get("otp")
        new_password = data.get("newPassword")
        
        if not email or not otp or not new_password:
            return jsonify({"error": "Email, OTP, and new password are required"}), 400
        
        print(f"[RESET PASSWORD] Email: {email}, OTP: {otp}")
        
        res, status = reset_admin_password(email, otp, new_password)
        return jsonify(res), status
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        print(f"Reset password error: {str(e)}")
        return jsonify({"error": "Failed to reset password"}), 400

@admin_bp.route("/resend-reset-otp", methods=["POST"])
def resend_reset_otp():
    """Resend password reset OTP"""
    try:
        encrypted = request.json.get("payload")
        if not encrypted:
            return jsonify({"error": "Missing payload"}), 400

        data = decrypt_payload(encrypted)
        email = data.get("email")
        
        if not email:
            return jsonify({"error": "Email is required"}), 400
        
        print(f"[RESEND RESET OTP] Request for email: {email}")
        
        res, status = resend_password_reset_otp(email)
        return jsonify(res), status
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        print(f"Resend reset OTP error: {str(e)}")
        return jsonify({"error": "Failed to resend OTP"}), 400


# -------------------- ADMIN CUSTOMER MANAGEMENT --------------------
# NOTE: These routes are now handled by admin_customer.py with better functionality
# Keeping them commented out to avoid conflicts

# from services.customer_service import (
#     get_all_customers,
#     get_customer_by_id,
# )
# from services.address_service import get_addresses_by_customer


# @admin_bp.route("/customers", methods=["GET"])
# def admin_list_customers():
#     customers = get_all_customers()
#     out = []
#     for c in customers:
#         cust = c.as_dict()
#         # attach addresses
#         addrs = get_addresses_by_customer(c.id)
#         cust["addresses"] = [
#             {
#                 "id": a.id,
#                 "name": a.name,
#                 "type": a.type,
#                 "city": a.city,
#                 "state": a.state,
#                 "country": a.country,
#                 "zip_code": a.zip_code,
#             }
#             for a in addrs
#         ]
#         out.append(cust)
#     return jsonify({"customers": out})


# @admin_bp.route("/customers/<int:cid>", methods=["GET"])
# def admin_get_customer(cid):
#     c = get_customer_by_id(cid)
#     if not c:
#         return jsonify({"error": "Not found"}), 404
#     cust = c.as_dict()
#     addrs = get_addresses_by_customer(c.id)
#     cust["addresses"] = [
#         {
#             "id": a.id,
#             "name": a.name,
#             "type": a.type,
#             "city": a.city,
#             "state": a.state,
#             "country": a.country,
#             "zip_code": a.zip_code,
#         }
#         for a in addrs
#     ]
#     return jsonify({"customer": cust})


# @admin_bp.route("/customers/<int:cid>", methods=["PUT", "PATCH"])
# def admin_update_customer(cid):
#     data = request.json or {}
#     from services.customer_service import update_customer

#     c = update_customer(cid, data)
#     if not c:
#         return jsonify({"error": "Not found"}), 404
#     return jsonify({"customer": c.as_dict()})


# @admin_bp.route("/customers/<int:cid>", methods=["DELETE"])
# def admin_delete_customer(cid):
#     from services.customer_service import delete_customer

#     ok = delete_customer(cid)
#     if not ok:
#         return jsonify({"error": "Not found"}), 404
#     return jsonify({"success": True})


# @admin_bp.route("/customers/<int:cid>/block", methods=["POST"])
# def admin_block_customer(cid):
#     from services.customer_service import set_customer_blocked
#     data = request.json or {}
#     blocked = data.get("blocked", True)
#     c = set_customer_blocked(cid, blocked=blocked)
#     if not c:
#         return jsonify({"error": "Not found"}), 404
#     return jsonify({"customer": c.as_dict()})


