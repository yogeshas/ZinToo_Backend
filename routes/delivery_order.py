from flask import Blueprint, request, jsonify
from functools import wraps
from services.delivery_auth_service import verify_auth_token
from services.delivery_order_service import (
    get_orders_for_delivery_guy,
    get_order_detail_for_delivery_guy,
    approve_order_by_delivery_guy,
    reject_order_by_delivery_guy,
    get_delivery_loyalty_with_order_tracking,
    serialize_orders_with_customer,
    out_for_delivery_order_by_delivery_guy,
    reject_order_by_delivery_guy,
    delivered_order_by_delivery_guy
)
from utils.crypto import encrypt_payload
from models.delivery_onboarding import DeliveryOnboarding


delivery_order_bp = Blueprint("delivery_order", __name__)


def require_delivery_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid authorization header"}), 401

        token = auth_header.split(" ")[1]
        result = verify_auth_token(token)
        if not result["success"]:
            return jsonify({"error": result["message"]}), 401

        # Fetch onboarding and ensure approved
        delivery_guy_id = result["user"].get("delivery_guy_id")
        if not delivery_guy_id:
            return jsonify({"error": "Delivery guy not onboarded"}), 403

        onboarding = DeliveryOnboarding.query.get(delivery_guy_id)
        if not onboarding or onboarding.status != "approved":
            return jsonify({"error": "Delivery guy not approved"}), 403

        request.delivery_guy_id = delivery_guy_id
        return f(*args, **kwargs)

    return decorated


@delivery_order_bp.route("/orders", methods=["GET"])  # All assigned orders
@require_delivery_auth
def list_orders():
    delivery_guy_id = request.delivery_guy_id
    status = request.args.get("status")  # approved|assigned|cancelled|delivered
    orders = get_orders_for_delivery_guy(delivery_guy_id, status)
    serialized = serialize_orders_with_customer(orders)
    # Return normal JSON instead of encrypted data
    return jsonify({"success": True, "orders": serialized}), 200


@delivery_order_bp.route("/orders/approved", methods=["GET"])  # Active buckets
@require_delivery_auth
def list_orders_approved():
    delivery_guy_id = request.delivery_guy_id
    orders = get_orders_for_delivery_guy(delivery_guy_id, "approved")
    serialized = serialize_orders_with_customer(orders)
    # Return normal JSON instead of encrypted data
    return jsonify({"success": True, "orders": serialized}), 200


@delivery_order_bp.route("/orders/cancelled", methods=["GET"])  # Cancelled
@require_delivery_auth
def list_orders_cancelled():
    delivery_guy_id = request.delivery_guy_id
    orders = get_orders_for_delivery_guy(delivery_guy_id, "cancelled")
    serialized = serialize_orders_with_customer(orders)
    # Return normal JSON instead of encrypted data
    return jsonify({"success": True, "orders": serialized}), 200


@delivery_order_bp.route("/orders/delivered", methods=["GET"])  # Completed
@require_delivery_auth
def list_orders_delivered():
    delivery_guy_id = request.delivery_guy_id
    orders = get_orders_for_delivery_guy(delivery_guy_id, "delivered")
    serialized = serialize_orders_with_customer(orders)
    # Return normal JSON instead of encrypted data
    return jsonify({"success": True, "orders": serialized}), 200


@delivery_order_bp.route("/orders/rejected", methods=["GET"])  # Rejected orders
@require_delivery_auth
def list_orders_rejected():
    delivery_guy_id = request.delivery_guy_id
    orders = get_orders_for_delivery_guy(delivery_guy_id, "rejected")
    serialized = serialize_orders_with_customer(orders)
    # Return normal JSON instead of encrypted data
    return jsonify({"success": True, "orders": serialized}), 200


@delivery_order_bp.route("/orders/<int:order_id>", methods=["GET"])  # Detail view
@require_delivery_auth
def get_order_detail(order_id: int):
    delivery_guy_id = request.delivery_guy_id
    detail = get_order_detail_for_delivery_guy(delivery_guy_id, order_id)
    if not detail:
        return jsonify({"error": "Order not found"}), 404
    # Return normal JSON instead of encrypted data
    return jsonify({"success": True, "order": detail}), 200


@delivery_order_bp.route("/orders/<int:order_id>/approve", methods=["POST"])
@require_delivery_auth
def approve_order(order_id: int):
    """Approve an order by delivery guy"""
    try:
        delivery_guy_id = request.delivery_guy_id
        result = approve_order_by_delivery_guy(delivery_guy_id, order_id)
        
        if result["success"]:
            # Return normal JSON instead of encrypted data
            return jsonify({"success": True, "message": result["message"], "order": result["order"]}), 200
        else:
            return jsonify({"error": result["message"]}), 400
            
    except Exception as e:
        print(f"Approve order error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@delivery_order_bp.route("/orders/<int:order_id>/reject", methods=["POST"])
@require_delivery_auth
def reject_order(order_id: int):
    """Reject an order by delivery guy"""
    try:
        delivery_guy_id = request.delivery_guy_id
        
        # Get rejection reason from request
        data = request.get_json()
        rejection_reason = data.get("rejection_reason", "Order rejected by delivery personnel") if data else "Order rejected by delivery personnel"
        
        result = reject_order_by_delivery_guy(delivery_guy_id, order_id, rejection_reason)
        
        if result["success"]:
            # Return normal JSON instead of encrypted data
            return jsonify({"success": True, "message": result["message"], "order": result["order"]}), 200
        else:
            return jsonify({"error": result["message"]}), 400
            
    except Exception as e:
        print(f"Reject order error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@delivery_order_bp.route("/orders/<int:order_id>/out_for_delivery", methods=["POST"])
@require_delivery_auth
def out_for_delivery(order_id: int):
    """Out for delivery an order by delivery guy"""
    try:
        delivery_guy_id = request.delivery_guy_id
        
        # Get out for delivery reason from request
        data = request.get_json()
        out_for_delivery_reason = data.get("out_for_delivery_reason", "Order out for delivery by delivery personnel") if data else "Order out for delivery by delivery personnel"
        
        result = out_for_delivery_order_by_delivery_guy(delivery_guy_id, order_id, out_for_delivery_reason)
        
        if result["success"]:
            # Return normal JSON instead of encrypted data
            return jsonify({"success": True, "message": result["message"], "order": result["order"]}), 200
        else:
            return jsonify({"error": result["message"]}), 400
            
    except Exception as e:
        print(f"Out for delivery order error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500



@delivery_order_bp.route("/orders/<int:order_id>/delivered", methods=["POST"])
@require_delivery_auth
def delivered(order_id: int):
    """Delivered an order by delivery guy"""
    try:
        delivery_guy_id = request.delivery_guy_id
        data = request.get_json()
        delivered_reason = data.get("delivered_reason", "Order delivered by delivery personnel") if data else "Order delivered by delivery personnel"
        result = delivered_order_by_delivery_guy(delivery_guy_id, order_id, delivered_reason)

        if result["success"]:
            return jsonify({"success": True, "message": result["message"], "order": result["order"]}), 200
        else:
            return jsonify({"error": result["message"]}), 400
            
    except Exception as e:
        print(f"Delivered order error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@delivery_order_bp.route("/loyalty", methods=["GET"])
@require_delivery_auth
def get_loyalty_info():
    """Get delivery loyalty information with order tracking"""
    try:
        delivery_guy_id = request.delivery_guy_id
        loyalty_info = get_delivery_loyalty_with_order_tracking(delivery_guy_id)
        
        if not loyalty_info:
            return jsonify({"error": "Loyalty information not found"}), 404
            
        return jsonify({"success": True, "loyalty": loyalty_info}), 200
        
    except Exception as e:
        print(f"Error getting loyalty info: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


