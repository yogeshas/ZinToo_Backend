# routes/exchange.py
from flask import Blueprint, request, jsonify
from services.exchange_service import (
    create_exchange,
    get_customer_exchanges,
    get_all_exchanges,
    get_exchange_by_id,
    approve_exchange,
    reject_exchange,
    assign_delivery,
    start_delivery,
    mark_exchange_delivered,
    get_exchanges_by_status
)
from utils.auth import require_customer_auth, require_admin_auth
from utils.crypto import decrypt_payload, encrypt_payload

exchange_bp = Blueprint("exchange", __name__)

# Customer routes
@exchange_bp.route("/customer", methods=["GET"])
@require_customer_auth
def get_my_exchanges(current_customer):
    """Get all exchanges for current customer"""
    try:
        customer_id = current_customer["id"]
        limit = request.args.get("limit", 20, type=int)
        
        res, status = get_customer_exchanges(customer_id, limit)
        if status != 200:
            return jsonify(res), status
        
        # Encrypt the response
        encrypted_data = encrypt_payload(res)
        return jsonify({
            "success": True,
            "encrypted_data": encrypted_data,
            "message": "Exchanges retrieved successfully"
        }), 200
        
    except Exception as e:
        print(f"Get customer exchanges route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@exchange_bp.route("/<int:exchange_id>", methods=["GET"])
@require_customer_auth
def get_exchange(current_customer, exchange_id):
    """Get exchange by ID for customer"""
    try:
        customer_id = current_customer["id"]
        res, status = get_exchange_by_id(exchange_id)
        
        if status != 200:
            return jsonify(res), status
        
        # Check if exchange belongs to customer
        exchange_data = res["exchange"]
        if exchange_data["customer_id"] != customer_id:
            return jsonify({"error": "Access denied"}), 403
        
        # Encrypt the response
        encrypted_data = encrypt_payload(res)
        return jsonify({
            "success": True,
            "encrypted_data": encrypted_data,
            "message": "Exchange retrieved successfully"
        }), 200
        
    except Exception as e:
        print(f"Get exchange route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

# Admin routes
@exchange_bp.route("/admin", methods=["GET"])
@require_admin_auth
def get_exchanges_admin(current_admin):
    """Get all exchanges for admin panel"""
    try:
        limit = request.args.get("limit", 50, type=int)
        status_filter = request.args.get("status")
        
        if status_filter:
            res, status = get_exchanges_by_status(status_filter, limit)
        else:
            res, status = get_all_exchanges(limit)
        
        if status != 200:
            return jsonify(res), status
        
        # Encrypt the response
        encrypted_data = encrypt_payload(res)
        return jsonify({
            "success": True,
            "encrypted_data": encrypted_data,
            "message": "Exchanges retrieved successfully"
        }), 200
        
    except Exception as e:
        print(f"Get exchanges admin route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@exchange_bp.route("/admin/<int:exchange_id>", methods=["GET"])
@require_admin_auth
def get_exchange_admin(current_admin, exchange_id):
    """Get exchange by ID for admin"""
    try:
        res, status = get_exchange_by_id(exchange_id)
        
        if status != 200:
            return jsonify(res), status
        
        # Encrypt the response
        encrypted_data = encrypt_payload(res)
        return jsonify({
            "success": True,
            "encrypted_data": encrypted_data,
            "message": "Exchange retrieved successfully"
        }), 200
        
    except Exception as e:
        print(f"Get exchange admin route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@exchange_bp.route("/admin/<int:exchange_id>/approve", methods=["POST"])
@require_admin_auth
def approve_exchange_admin(current_admin, exchange_id):
    """Approve an exchange request"""
    try:
        admin_id = current_admin["id"]
        print(f"🔍 DEBUG: Admin approval request for exchange {exchange_id}")
        print(f"🔍 DEBUG: Request JSON: {request.json}")
        
        encrypted_data = request.json.get("payload")
        print(f"🔍 DEBUG: Encrypted data: {encrypted_data}")
        
        if not encrypted_data:
            print("🔍 DEBUG: Missing encrypted payload")
            return jsonify({"error": "Missing encrypted payload"}), 400
        
        data = decrypt_payload(encrypted_data)
        print(f"🔍 DEBUG: Decrypted data: {data}")
        admin_notes = data.get("admin_notes")
        
        res, status = approve_exchange(exchange_id, admin_id, admin_notes)
        print(f"🔍 DEBUG: Approval result: {res}, status: {status}")
        return jsonify(res), status
        
    except Exception as e:
        print(f"Approve exchange admin route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@exchange_bp.route("/admin/<int:exchange_id>/reject", methods=["POST"])
@require_admin_auth
def reject_exchange_admin(current_admin, exchange_id):
    """Reject an exchange request"""
    try:
        admin_id = current_admin["id"]
        encrypted_data = request.json.get("payload")
        
        if not encrypted_data:
            return jsonify({"error": "Missing encrypted payload"}), 400
        
        data = decrypt_payload(encrypted_data)
        reason = data.get("reason")
        
        if not reason:
            return jsonify({"error": "Rejection reason is required"}), 400
        
        res, status = reject_exchange(exchange_id, admin_id, reason)
        return jsonify(res), status
        
    except Exception as e:
        print(f"Reject exchange admin route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@exchange_bp.route("/admin/<int:exchange_id>/assign-delivery", methods=["POST"])
@require_admin_auth
def assign_delivery_admin(current_admin, exchange_id):
    """Assign delivery guy for exchange"""
    try:
        encrypted_data = request.json.get("payload")
        
        if not encrypted_data:
            return jsonify({"error": "Missing encrypted payload"}), 400
        
        data = decrypt_payload(encrypted_data)
        delivery_guy_id = data.get("delivery_guy_id")
        
        if not delivery_guy_id:
            return jsonify({"error": "Delivery guy ID is required"}), 400
        
        res, status = assign_delivery(exchange_id, delivery_guy_id)
        return jsonify(res), status
        
    except Exception as e:
        print(f"Assign delivery admin route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@exchange_bp.route("/admin/<int:exchange_id>/mark-delivered", methods=["POST"])
@require_admin_auth
def mark_delivered_admin(current_admin, exchange_id):
    """Mark exchange as delivered"""
    try:
        res, status = mark_exchange_delivered(exchange_id)
        return jsonify(res), status
        
    except Exception as e:
        print(f"Mark delivered admin route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

# Delivery guy routes (for mobile app)
@exchange_bp.route("/delivery/<int:exchange_id>/start-delivery", methods=["POST"])
def start_delivery_delivery(exchange_id):
    """Start delivery by delivery guy"""
    try:
        # This would typically require delivery guy authentication
        # For now, we'll allow it without auth for testing
        res, status = start_delivery(exchange_id)
        return jsonify(res), status
        
    except Exception as e:
        print(f"Start delivery delivery route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@exchange_bp.route("/delivery/<int:exchange_id>/mark-delivered", methods=["POST"])
def mark_delivered_delivery(exchange_id):
    """Mark exchange as delivered by delivery guy"""
    try:
        # This would typically require delivery guy authentication
        # For now, we'll allow it without auth for testing
        res, status = mark_exchange_delivered(exchange_id)
        return jsonify(res), status
        
    except Exception as e:
        print(f"Mark delivered delivery route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
