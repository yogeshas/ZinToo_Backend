from flask import Blueprint, request, jsonify
from services.cart_service import (
    add_to_cart,
    update_cart_quantity,
    remove_from_cart,
    get_customer_cart,
    get_cart_item,
    clear_customer_cart,
    get_cart_count
)
from utils.crypto import encrypt_payload, decrypt_payload
from functools import wraps
import jwt
from extensions import db


cart_bp = Blueprint("cart", __name__)

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

@cart_bp.route("/", methods=["GET"])
@require_auth
def get_cart():
    """Get customer's cart items"""
    try:
        customer_id = request.customer_id
        cart_items = get_customer_cart(customer_id)
        # cart_items are now dictionaries with sizes data already included
        data = {"cart_items": cart_items}
        enc = encrypt_payload(data)
        return jsonify({"success": True, "encrypted_data": enc})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@cart_bp.route("/count", methods=["GET"])
@require_auth
def get_cart_count_route():
    """Get total number of items in customer's cart"""
    try:
        customer_id = request.customer_id
        count = get_cart_count(customer_id)
        data = {"count": count}
        enc = encrypt_payload(data)
        return jsonify({"success": True, "encrypted_data": enc})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@cart_bp.route("/add", methods=["POST"])
@require_auth
def add_to_cart_route():
    """Add product to cart"""
    try:
        encrypted = request.json.get("data")
        if not encrypted:
            return jsonify({"success": False, "error": "Missing data"}), 400
        
        # Try to handle both encrypted and base64 data
        try:
            data = decrypt_payload(encrypted)
        except:
            # If decryption fails, try base64 decode
            try:
                import base64
                import json
                decoded = base64.b64decode(encrypted).decode('utf-8')
                data = json.loads(decoded)
                print(f"[CART ROUTE] Using base64 data: {data}")
            except Exception as e:
                return jsonify({"success": False, "error": f"Failed to decode data: {str(e)}"}), 400
        
        customer_id = request.customer_id
        product_id = data.get("product_id")
        quantity = data.get("quantity", 1)
        selected_size = data.get("selected_size")  # Get selected size
        selected_color = data.get("selected_color")  # Get selected color
        
        # Debug: Log received data
        print(f"[CART ROUTE] Received data: product_id={product_id}, quantity={quantity}, selected_size={selected_size}, selected_color={selected_color}")
        
        if not product_id:
            return jsonify({"success": False, "error": "Product ID is required"}), 400
        
        cart_item = add_to_cart(customer_id, product_id, quantity, selected_size, selected_color)
        data = {"cart_item": cart_item.to_dict()}
        enc = encrypt_payload(data)
        return jsonify({"success": True, "encrypted_data": enc}), 201
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@cart_bp.route("/update/<int:cart_id>", methods=["PUT", "PATCH"])
@require_auth
def update_cart_quantity_route(cart_id):
    """Update cart item quantity"""
    try:
        encrypted = request.json.get("data")
        if not encrypted:
            return jsonify({"success": False, "error": "Missing data"}), 400
        
        # Try to handle both encrypted and base64 data
        try:
            data = decrypt_payload(encrypted)
        except:
            # If decryption fails, try base64 decode
            try:
                import base64
                import json
                decoded = base64.b64decode(encrypted).decode('utf-8')
                data = json.loads(decoded)
                print(f"[CART UPDATE] Using base64 data: {data}")
            except Exception as e:
                return jsonify({"success": False, "error": f"Failed to decode data: {str(e)}"}), 400
        
        quantity = data.get("quantity")
        
        if quantity is None:
            return jsonify({"success": False, "error": "Quantity is required"}), 400
        
        # Verify cart item belongs to customer
        cart_item = get_cart_item(cart_id)
        if not cart_item or cart_item.customer_id != request.customer_id:
            return jsonify({"success": False, "error": "Cart item not found"}), 404
        
        updated_item = update_cart_quantity(cart_id, quantity)
        if updated_item:
            data = {"cart_item": updated_item.to_dict()}
        else:
            data = {"message": "Item removed from cart"}
        
        enc = encrypt_payload(data)
        return jsonify({"success": True, "encrypted_data": enc})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@cart_bp.route("/remove/<int:cart_id>", methods=["DELETE"])
@require_auth
def remove_from_cart_route(cart_id):
    """Remove item from cart"""
    try:
        # Verify cart item belongs to customer
        cart_item = get_cart_item(cart_id)
        if not cart_item or cart_item.customer_id != request.customer_id:
            return jsonify({"success": False, "error": "Cart item not found"}), 404
        
        remove_from_cart(cart_id)
        data = {"message": "Item removed from cart"}
        enc = encrypt_payload(data)
        return jsonify({"success": True, "encrypted_data": enc})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@cart_bp.route("/clear", methods=["DELETE"])
@require_auth
def clear_cart_route():
    """Clear all items from customer's cart"""
    try:
        customer_id = request.customer_id
        clear_customer_cart(customer_id)
        data = {"message": "Cart cleared successfully"}
        enc = encrypt_payload(data)
        return jsonify({"success": True, "encrypted_data": enc})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400
