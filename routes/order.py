# routes/order.py
from flask import Blueprint, request, jsonify
from services.order_service import (
    create_order,
    get_order_by_id,
    get_customer_orders,
    update_order_status,
    cancel_order
)
from utils.auth import require_customer_auth
from utils.crypto import decrypt_payload

order_bp = Blueprint("order", __name__)

@order_bp.route("/", methods=["POST"])
@require_customer_auth
def place_order(current_customer):
    """Create a new order"""
    try:
        print(f"[ORDER ROUTE] Creating new order for customer: {current_customer['id']}")
        customer_id = current_customer["id"]
        encrypted_data = request.json.get("payload") or request.json.get("data")
        if not encrypted_data:
            print(f"[ORDER ROUTE] Missing encrypted data")
            return jsonify({"error": "Missing encrypted payload or data"}), 400
        
        print(f"[ORDER ROUTE] Encrypted data received: {encrypted_data[:50]}...")
        decrypted_data = decrypt_payload(encrypted_data)
        print(f"[ORDER ROUTE] Decrypted data: {decrypted_data}")
        
        # Add customer_id to order data
        order_data = decrypted_data
        order_data["customer_id"] = customer_id
        
        print(f"[ORDER ROUTE] Final order data: {order_data}")
        res, status = create_order(customer_id, order_data)
        return jsonify(res), status
    except Exception as e:
        print(f"Place order route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@order_bp.route("/<int:order_id>", methods=["GET"])
@require_customer_auth
def get_order(current_customer, order_id):
    """Get order by ID"""
    try:
        customer_id = current_customer["id"]
        res, status = get_order_by_id(order_id, customer_id)
        return jsonify(res), status
    except Exception as e:
        print(f"Get order route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@order_bp.route("/customer", methods=["GET"])
@require_customer_auth
def get_my_orders(current_customer):
    """Get all orders for current customer"""
    try:
        customer_id = current_customer["id"]
        limit = request.args.get("limit", 20, type=int)
        
        res, status = get_customer_orders(customer_id, limit)
        return jsonify(res), status
    except Exception as e:
        print(f"Get customer orders route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@order_bp.route("/<int:order_id>/status", methods=["PUT"])
@require_customer_auth
def update_status(current_customer, order_id):
    """Update order status"""
    try:
        customer_id = current_customer["id"]
        encrypted_data = request.json.get("payload") or request.json.get("data")
        if not encrypted_data:
            return jsonify({"error": "Missing encrypted payload or data"}), 400
        
        decrypted_data = decrypt_payload(encrypted_data)
        status = decrypted_data.get("status")
        
        if not status:
            return jsonify({"error": "Status is required"}), 400
        
        res, status_code = update_order_status(order_id, status, customer_id)
        return jsonify(res), status_code
    except Exception as e:
        print(f"Update order status route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@order_bp.route("/<int:order_id>/cancel", methods=["POST"])
@require_customer_auth
def cancel_my_order(current_customer, order_id):
    """Cancel an order"""
    try:
        customer_id = current_customer["id"]
        res, status = cancel_order(order_id, customer_id)
        return jsonify(res), status
    except Exception as e:
        print(f"Cancel order route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@order_bp.route("/<int:order_id>/exchange", methods=["POST"])
@require_customer_auth
def create_exchange_request(current_customer, order_id):
    """Create an exchange request for an order"""
    try:
        customer_id = current_customer["id"]
        encrypted_data = request.json.get("payload") or request.json.get("data")
        
        print(f"[EXCHANGE ROUTE] Received request for order {order_id}")
        print(f"[EXCHANGE ROUTE] Encrypted data: {encrypted_data[:100] if encrypted_data else 'None'}...")
        
        if not encrypted_data:
            return jsonify({"error": "Missing encrypted payload or data"}), 400
        
        decrypted_data = decrypt_payload(encrypted_data)
        print(f"[EXCHANGE ROUTE] Decrypted data: {decrypted_data}")
        
        order_item_id = decrypted_data.get("order_item_id")
        product_id = decrypted_data.get("product_id")
        new_size = decrypted_data.get("new_size")
        reason = decrypted_data.get("reason")
        
        print(f"[EXCHANGE ROUTE] Parsed fields: order_item_id={order_item_id}, product_id={product_id}, new_size={new_size}, reason={reason}")
        
        if not all([order_item_id, product_id, new_size]):
            return jsonify({"error": "Missing required fields: order_item_id, product_id, new_size"}), 400
        
        # Import exchange service
        from services.exchange_service import create_exchange
        res, status = create_exchange(customer_id, order_id, order_item_id, product_id, new_size, reason)
        return jsonify(res), status
        
    except Exception as e:
        print(f"Create exchange request route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@order_bp.route("/<int:order_id>/track", methods=["GET"])
@require_customer_auth
def track_order(current_customer, order_id):
    """Track order status and delivery"""
    try:
        customer_id = current_customer["id"]
        res, status = get_order_by_id(order_id, customer_id)
        
        if status != 200:
            return jsonify(res), status
        
        # Decrypt the response to get order data
        from utils.crypto import decrypt_payload
        order_data = decrypt_payload(res["encrypted_data"])
        order = order_data["order"]
        
        # Calculate delivery progress
        delivery_progress = {
            "order_placed": True,
            "confirmed": order["status"] in ["confirmed", "processing", "shipped", "delivered"],
            "processing": order["status"] in ["processing", "shipped", "delivered"],
            "shipped": order["status"] in ["shipped", "delivered"],
            "delivered": order["status"] == "delivered"
        }
        
        # Calculate estimated time remaining
        estimated_delivery = None
        if order["estimated_delivery"]:
            from datetime import datetime
            estimated = datetime.fromisoformat(order["estimated_delivery"])
            now = datetime.utcnow()
            if estimated > now:
                time_diff = estimated - now
                if time_diff.days > 0:
                    estimated_delivery = f"{time_diff.days} days"
                elif time_diff.seconds > 3600:
                    hours = time_diff.seconds // 3600
                    estimated_delivery = f"{hours} hours"
                else:
                    minutes = time_diff.seconds // 60
                    estimated_delivery = f"{minutes} minutes"
            else:
                estimated_delivery = "Overdue"
        
        tracking_data = {
            "order_id": order["id"],
            "order_number": order["order_number"],
            "status": order["status"],
            "delivery_type": order["delivery_type"],
            "estimated_delivery": order["estimated_delivery"],
            "estimated_time_remaining": estimated_delivery,
            "delivery_progress": delivery_progress,
            "delivery_address": order["delivery_address"],
            "payment_status": order["payment_status"]
        }
        
        # Encrypt tracking data
        from utils.crypto import encrypt_payload
        encrypted_tracking = encrypt_payload({
            "success": True,
            "tracking": tracking_data,
            "message": "Order tracking information retrieved successfully"
        })
        
        return jsonify({
            "success": True,
            "encrypted_data": encrypted_tracking,
            "message": "Order tracking information retrieved successfully"
        }), 200
        
    except Exception as e:
        print(f"Track order route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
