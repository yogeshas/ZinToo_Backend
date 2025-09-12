#!/usr/bin/env python3
"""
Improved Delivery Order Routes

This provides better error handling and debugging for delivery orders API.
"""

from flask import Blueprint, request, jsonify
from functools import wraps
from utils.auth import verify_auth_token
from models.delivery_onboarding import DeliveryOnboarding
from services.delivery_order_service import serialize_orders_with_customer
from improved_delivery_order_service import (
    get_orders_for_delivery_guy_improved,
    get_order_items_for_delivery_guy_improved,
    get_combined_orders_for_delivery_guy,
    debug_delivery_guy_assignments
)
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

delivery_order_bp = Blueprint("delivery_order", __name__)

def require_delivery_auth_improved(f):
    """Improved authentication decorator with better error handling"""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                logger.error("❌ Missing or invalid authorization header")
                return jsonify({"error": "Missing or invalid authorization header"}), 401

            token = auth_header.split(" ")[1]
            logger.info(f"🔑 Verifying token for delivery guy")
            
            result = verify_auth_token(token)
            if not result["success"]:
                logger.error(f"❌ Token verification failed: {result['message']}")
                return jsonify({"error": result["message"]}), 401

            # Get delivery guy ID from token
            delivery_guy_id = result["user"].get("delivery_guy_id")
            if not delivery_guy_id:
                logger.error("❌ No delivery_guy_id in token")
                return jsonify({"error": "Delivery guy not onboarded"}), 403

            logger.info(f"🔍 Looking up delivery guy ID: {delivery_guy_id}")
            
            # Verify delivery guy exists and is approved
            onboarding = DeliveryOnboarding.query.get(delivery_guy_id)
            if not onboarding:
                logger.error(f"❌ Delivery guy with ID {delivery_guy_id} not found")
                return jsonify({"error": "Delivery guy not found"}), 403
            
            if onboarding.status != "approved":
                logger.error(f"❌ Delivery guy {delivery_guy_id} not approved (status: {onboarding.status})")
                return jsonify({"error": "Delivery guy not approved"}), 403

            logger.info(f"✅ Delivery guy authenticated: {onboarding.first_name} {onboarding.last_name}")
            
            # Store in request for use in route handlers
            request.delivery_guy_id = delivery_guy_id
            request.delivery_guy = onboarding
            
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"❌ Authentication error: {str(e)}")
            return jsonify({"error": "Authentication failed"}), 500

    return decorated

@delivery_order_bp.route("/orders", methods=["GET"])
@require_delivery_auth_improved
def list_orders_improved():
    """Improved endpoint to list orders for delivery guy"""
    try:
        delivery_guy_id = request.delivery_guy_id
        status = request.args.get("status")
        debug = request.args.get("debug", "false").lower() == "true"
        
        logger.info(f"📦 Getting orders for delivery guy {delivery_guy_id}, status: {status}")
        
        # Get orders using improved service
        orders = get_orders_for_delivery_guy_improved(delivery_guy_id, status, debug)
        
        # Serialize orders
        serialized_orders = serialize_orders_with_customer(orders)
        
        logger.info(f"✅ Returning {len(serialized_orders)} orders for delivery guy {delivery_guy_id}")
        
        return jsonify({
            "success": True, 
            "orders": serialized_orders,
            "total": len(serialized_orders),
            "delivery_guy_id": delivery_guy_id,
            "status_filter": status
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error in list_orders_improved: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@delivery_order_bp.route("/orders/items", methods=["GET"])
@require_delivery_auth_improved
def list_order_items_improved():
    """Endpoint to list order items for delivery guy"""
    try:
        delivery_guy_id = request.delivery_guy_id
        status = request.args.get("status")
        debug = request.args.get("debug", "false").lower() == "true"
        
        logger.info(f"📦 Getting order items for delivery guy {delivery_guy_id}, status: {status}")
        
        # Get order items using improved service
        order_items = get_order_items_for_delivery_guy_improved(delivery_guy_id, status, debug)
        
        # Serialize order items
        serialized_items = []
        for item in order_items:
            item_dict = {
                "id": item.id,
                "order_id": item.order_id,
                "product_id": item.product_id,
                "product_name": item.product_name,
                "product_image": item.product_image,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "total_price": item.total_price,
                "selected_size": item.selected_size,
                "status": item.status,
                "delivery_guy_id": item.delivery_guy_id,
                "created_at": item.created_at.isoformat() if item.created_at else None
            }
            serialized_items.append(item_dict)
        
        logger.info(f"✅ Returning {len(serialized_items)} order items for delivery guy {delivery_guy_id}")
        
        return jsonify({
            "success": True,
            "order_items": serialized_items,
            "total": len(serialized_items),
            "delivery_guy_id": delivery_guy_id,
            "status_filter": status
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error in list_order_items_improved: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@delivery_order_bp.route("/orders/combined", methods=["GET"])
@require_delivery_auth_improved
def list_combined_orders_improved():
    """Endpoint to get both orders and order items for delivery guy"""
    try:
        delivery_guy_id = request.delivery_guy_id
        status = request.args.get("status")
        debug = request.args.get("debug", "false").lower() == "true"
        
        logger.info(f"📦 Getting combined data for delivery guy {delivery_guy_id}, status: {status}")
        
        # Get combined data using improved service
        result = get_combined_orders_for_delivery_guy(delivery_guy_id, status, debug)
        
        # Serialize orders
        serialized_orders = serialize_orders_with_customer(result["orders"])
        
        # Serialize order items
        serialized_items = []
        for item in result["order_items"]:
            item_dict = {
                "id": item.id,
                "order_id": item.order_id,
                "product_id": item.product_id,
                "product_name": item.product_name,
                "product_image": item.product_image,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "total_price": item.total_price,
                "selected_size": item.selected_size,
                "status": item.status,
                "delivery_guy_id": item.delivery_guy_id,
                "created_at": item.created_at.isoformat() if item.created_at else None
            }
            serialized_items.append(item_dict)
        
        logger.info(f"✅ Returning {len(serialized_orders)} orders and {len(serialized_items)} items for delivery guy {delivery_guy_id}")
        
        return jsonify({
            "success": True,
            "orders": serialized_orders,
            "order_items": serialized_items,
            "total_orders": len(serialized_orders),
            "total_items": len(serialized_items),
            "delivery_guy_id": delivery_guy_id,
            "status_filter": status
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error in list_combined_orders_improved: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@delivery_order_bp.route("/debug", methods=["GET"])
@require_delivery_auth_improved
def debug_assignments():
    """Debug endpoint to check delivery guy assignments"""
    try:
        delivery_guy_id = request.delivery_guy_id
        
        logger.info(f"🔍 Debugging assignments for delivery guy {delivery_guy_id}")
        
        # Get debug information
        debug_info = debug_delivery_guy_assignments(delivery_guy_id)
        
        return jsonify({
            "success": True,
            "debug_info": debug_info
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error in debug_assignments: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@delivery_order_bp.route("/orders/<int:order_id>", methods=["GET"])
@require_delivery_auth_improved
def get_order_details_improved(order_id):
    """Improved endpoint to get order details"""
    try:
        delivery_guy_id = request.delivery_guy_id
        
        logger.info(f"📦 Getting order details for order {order_id}, delivery guy {delivery_guy_id}")
        
        # Get order details using existing service
        from services.delivery_order_service import get_order_detail_for_delivery_guy
        order_detail = get_order_detail_for_delivery_guy(delivery_guy_id, order_id)
        
        if not order_detail:
            logger.warning(f"⚠️ Order {order_id} not found or not assigned to delivery guy {delivery_guy_id}")
            return jsonify({"error": "Order not found or not assigned to you"}), 404
        
        logger.info(f"✅ Returning order details for order {order_id}")
        
        return jsonify({
            "success": True,
            "order": order_detail
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error in get_order_details_improved: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
