from flask import Blueprint, request, jsonify
from services.wishlist_service import (
    add_to_wishlist,
    remove_from_wishlist,
    remove_wishlist_item_by_id,
    get_customer_wishlist,
    get_wishlist_item,
    clear_customer_wishlist,
    get_wishlist_count,
    is_product_in_wishlist
)
from utils.crypto import encrypt_payload, decrypt_payload
from functools import wraps
import jwt

wishlist_bp = Blueprint("wishlist", __name__)

def require_auth(f):
    """Decorator to require customer authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"success": False, "error": "Login required"}), 401
        
        token = auth_header.split(" ", 1)[1].strip()
        try:
            # Decode token to get customer ID
            from config import Config
            payload = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
            customer_id = payload.get("id")
            if not customer_id:
                return jsonify({"success": False, "error": "Invalid token"}), 401
            
            # Add customer_id to request context
            request.customer_id = customer_id
            return f(*args, **kwargs)
        except jwt.ExpiredSignatureError:
            return jsonify({"success": False, "error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"success": False, "error": "Invalid token"}), 401
        except Exception as e:
            return jsonify({"success": False, "error": "Authentication failed"}), 401
    
    return decorated_function

@wishlist_bp.route("/", methods=["GET"])
@require_auth
def get_wishlist():
    """Get customer's wishlist items"""
    try:
        customer_id = request.customer_id
        
        wishlist_items = get_customer_wishlist(customer_id)
        total_count = get_wishlist_count(customer_id)
        
        data = {
            "wishlist_items": [item.to_dict() for item in wishlist_items],
            "total_count": total_count
        }
        enc = encrypt_payload(data)
        return jsonify({"success": True, "encrypted_data": enc})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@wishlist_bp.route("/count", methods=["GET"])
@require_auth
def get_wishlist_count_route():
    """Get total number of items in customer's wishlist"""
    try:
        customer_id = request.customer_id
        count = get_wishlist_count(customer_id)
        data = {"count": count}
        enc = encrypt_payload(data)
        return jsonify({"success": True, "encrypted_data": enc})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@wishlist_bp.route("/check/<int:product_id>", methods=["GET"])
@require_auth
def check_wishlist_status(product_id):
    """Check if a product is in customer's wishlist"""
    try:
        customer_id = request.customer_id
        is_in_wishlist = is_product_in_wishlist(customer_id, product_id)
        data = {"is_in_wishlist": is_in_wishlist}
        enc = encrypt_payload(data)
        return jsonify({"success": True, "encrypted_data": enc})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@wishlist_bp.route("/add", methods=["POST"])
@require_auth
def add_to_wishlist_route():
    """Add product to wishlist"""
    try:
        encrypted = request.json.get("data")
        if not encrypted:
            return jsonify({"success": False, "error": "Missing data"}), 400
        
        data = decrypt_payload(encrypted)
        customer_id = request.customer_id
        product_id = data.get("product_id")
        
        if not product_id:
            return jsonify({"success": False, "error": "Product ID is required"}), 400
        
        wishlist_item = add_to_wishlist(customer_id, product_id)
        data = {"wishlist_item": wishlist_item.to_dict()}
        enc = encrypt_payload(data)
        return jsonify({"success": True, "encrypted_data": enc}), 201
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@wishlist_bp.route("/remove/<int:product_id>", methods=["DELETE"])
@require_auth
def remove_from_wishlist_route(product_id):
    """Remove item from wishlist by product ID"""
    try:
        customer_id = request.customer_id
        remove_from_wishlist(customer_id, product_id)
        data = {"message": "Item removed from wishlist"}
        enc = encrypt_payload(data)
        return jsonify({"success": True, "encrypted_data": enc})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@wishlist_bp.route("/remove-item/<int:wishlist_id>", methods=["DELETE"])
@require_auth
def remove_wishlist_item_route(wishlist_id):
    """Remove wishlist item by wishlist ID"""
    try:
        # Verify wishlist item belongs to customer
        wishlist_item = get_wishlist_item(wishlist_id)
        if not wishlist_item or wishlist_item.customer_id != request.customer_id:
            return jsonify({"success": False, "error": "Wishlist item not found"}), 404
        
        remove_wishlist_item_by_id(wishlist_id)
        data = {"message": "Item removed from wishlist"}
        enc = encrypt_payload(data)
        return jsonify({"success": True, "encrypted_data": enc})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@wishlist_bp.route("/clear", methods=["DELETE"])
@require_auth
def clear_wishlist_route():
    """Clear all items from customer's wishlist"""
    try:
        customer_id = request.customer_id
        clear_customer_wishlist(customer_id)
        data = {"message": "Wishlist cleared successfully"}
        enc = encrypt_payload(data)
        return jsonify({"success": True, "encrypted_data": enc})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400
