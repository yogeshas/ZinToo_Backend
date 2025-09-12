from flask import Blueprint, request, jsonify
from functools import wraps
import base64
import io
from PIL import Image
try:
    import cv2
except ImportError:
    cv2 = None
try:
    import numpy as np
except ImportError:
    np = None
try:
    from pyzbar import pyzbar
except ImportError:
    pyzbar = None
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
    delivered_order_by_delivery_guy,
    get_order_delivery_purpose
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
    print(f"Statusssssss: {status}")
    
    # NEW LOGIC: Show orders based on order-item status and delivery_track
    print(f"Delivery guy ID: {delivery_guy_id}")
    print(f"Status filter: {status}")
    
    # Get orders with new logic that groups by status and delivery_track
    orders = get_orders_for_delivery_guy(delivery_guy_id, status)
    
    print(f"Found {len(orders)} orders for delivery guy {delivery_guy_id}")
    serialized = serialize_orders_with_customer(orders)
    print(f"Serialized: {serialized}")
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
        print(f"🚀 [REJECT ROUTE] Delivery guy {delivery_guy_id} rejecting order {order_id}")
        
        # Get rejection reason from request
        data = request.get_json()
        rejection_reason = data.get("rejection_reason", "Order rejected by delivery personnel") if data else "Order rejected by delivery personnel"
        
        print(f"📝 [REJECT ROUTE] Rejection reason: {rejection_reason}")
        
        result = reject_order_by_delivery_guy(delivery_guy_id, order_id, rejection_reason)
        
        print(f"📊 [REJECT ROUTE] Result: {result}")
        
        if result["success"]:
            # Return normal JSON instead of encrypted data
            return jsonify({"success": True, "message": result["message"], "order": result["order"]}), 200
        else:
            print(f"❌ [REJECT ROUTE] Rejection failed: {result['message']}")
            return jsonify({"error": result["message"]}), 400
            
    except Exception as e:
        print(f"💥 [REJECT ROUTE] Exception: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@delivery_order_bp.route("/orders/<int:order_id>/out_for_delivery", methods=["POST"])
@require_delivery_auth
def out_for_delivery(order_id: int):
    """Out for delivery an order by delivery guy"""
    try:
        delivery_guy_id = request.delivery_guy_id
        
        # Get out for delivery reason and exchange flag from request
        data = request.get_json() or {}
        out_for_delivery_reason = data.get("out_for_delivery_reason", "Order out for delivery by delivery personnel")
        is_exchange = data.get("is_exchange", False)  # Simple boolean flag
        
        result = out_for_delivery_order_by_delivery_guy(delivery_guy_id, order_id, out_for_delivery_reason, is_exchange)
        
        if result["success"]:
            return jsonify({
                "success": True, 
                "message": result["message"], 
                "order": result["order"],
                "is_exchange": is_exchange
            }), 200
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


@delivery_order_bp.route("/orders/<int:order_id>/delivery-purpose", methods=["GET"])
@require_delivery_auth
def get_delivery_purpose(order_id: int):
    """Get delivery purpose information for an order"""
    try:
        delivery_guy_id = request.delivery_guy_id
        
        # Verify order is assigned to this delivery guy
        from models.order import Order
        order = Order.query.filter_by(id=order_id, delivery_guy_id=delivery_guy_id).first()
        if not order:
            return jsonify({"error": "Order not found or not assigned to you"}), 404
        
        purpose_info = get_order_delivery_purpose(order_id)
        
        return jsonify({
            "success": True,
            "delivery_purpose": purpose_info
        }), 200
        
    except Exception as e:
        print(f"Get delivery purpose error: {str(e)}")
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


@delivery_order_bp.route("/scan-barcode", methods=["POST"])
@require_delivery_auth
def scan_barcode():
    """
    Scan barcodes from captured image
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        image_base64 = data.get('image_base64')
        expected_barcodes = data.get('expected_barcodes', [])

        if not image_base64:
            return jsonify({"success": False, "error": "No image provided"}), 400

        if not expected_barcodes:
            return jsonify({"success": False, "error": "No expected barcodes provided"}), 400

        # Clean base64 string (remove data:image prefix if present)
        if image_base64.startswith('data:image'):
            image_base64 = image_base64.split(',')[1]

        # Decode base64 image
        try:
            image_bytes = base64.b64decode(image_base64)
            image = Image.open(io.BytesIO(image_bytes))
        except Exception as e:
            return jsonify({"success": False, "error": f"Invalid image format: {str(e)}"}), 400

        # Convert PIL image to OpenCV format
        if cv2 is None or np is None or pyzbar is None:
            return jsonify({"success": False, "error": "OpenCV, NumPy, or pyzbar not available. Please install opencv-python, numpy, and pyzbar."}), 400
        
        opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        # Detect barcodes using pyzbar
        barcodes = pyzbar.decode(opencv_image)
        detected_barcodes = []

        for barcode in barcodes:
            try:
                barcode_data = barcode.data.decode('utf-8')
                # Check if this barcode is in the expected list
                if barcode_data in expected_barcodes:
                    detected_barcodes.append(barcode_data)
            except UnicodeDecodeError:
                # Skip barcodes that can't be decoded as UTF-8
                continue

        # Remove duplicates while preserving order
        detected_barcodes = list(dict.fromkeys(detected_barcodes))

        return jsonify({
            "success": True,
            "detected_barcodes": detected_barcodes,
            "message": f"Found {len(detected_barcodes)} matching barcode(s) out of {len(expected_barcodes)} expected"
        }), 200

    except Exception as e:
        print(f"Error scanning barcode: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Error processing image: {str(e)}"
        }), 500


