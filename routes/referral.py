# routes/referral.py
from flask import Blueprint, request, jsonify
from services.referral_service import (
    validate_referral_code,
    get_referral_stats,
    get_customer_by_referral_code
)
from utils.auth import require_customer_auth
from utils.crypto import decrypt_payload

referral_bp = Blueprint("referral", __name__)

@referral_bp.route("/validate", methods=["POST"])
def validate_code():
    """Validate a referral code"""
    try:
        data = request.json
        referral_code = data.get("referral_code")
        
        if not referral_code:
            return jsonify({"error": "Referral code is required"}), 400
        
        is_valid = validate_referral_code(referral_code)
        
        if is_valid:
            # Get referrer info
            referrer = get_customer_by_referral_code(referral_code)
            return jsonify({
                "success": True,
                "valid": True,
                "referrer_name": referrer.username if referrer else None,
                "message": "Valid referral code"
            }), 200
        else:
            return jsonify({
                "success": True,
                "valid": False,
                "message": "Invalid referral code"
            }), 200
            
    except Exception as e:
        print(f"Validate referral code route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@referral_bp.route("/stats", methods=["GET"])
@require_customer_auth
def get_stats(current_customer):
    """Get referral statistics for current customer"""
    try:
        customer_id = current_customer["id"]
        res, status = get_referral_stats(customer_id)
        return jsonify(res), status
    except Exception as e:
        print(f"Get referral stats route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
