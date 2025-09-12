from flask import Blueprint, request, jsonify
from services.cart_service import get_customer_cart, get_cart_count
from services.wishlist_service import get_customer_wishlist, get_wishlist_count
from models.customer import Customer
from models.product import Product
from utils.crypto import encrypt_payload, decrypt_payload
from functools import wraps
import jwt
from extensions import db

admin_cart_bp = Blueprint("admin_cart", __name__)

def require_admin_auth(f):
    """Decorator to require admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Admin authentication required"}), 401
        
        token = auth_header.split(" ", 1)[1].strip()
        try:
            # Decode token to get admin info
            from config import Config
            payload = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
            admin_id = payload.get("id")
            if not admin_id:
                return jsonify({"error": "Invalid admin token"}), 401
            
            # Add admin_id to request context
            request.admin_id = admin_id
            return f(*args, **kwargs)
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Admin token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid admin token"}), 401
        except Exception as e:
            return jsonify({"error": "Admin authentication failed"}), 401
    
    return decorated_function

@admin_cart_bp.route("/cart-summary", methods=["GET"])
@require_admin_auth
def get_cart_summary():
    """Get summary of all customer carts for admin panel"""
    try:
        # Get all customers with their cart counts
        customers = Customer.query.all()
        cart_summary = []
        
        for customer in customers:
            cart_count = get_cart_count(customer.id)
            wishlist_count = get_wishlist_count(customer.id)
            
            if cart_count > 0 or wishlist_count > 0:
                cart_summary.append({
                    "customer_id": customer.id,
                    "customer_name": customer.username,
                    "customer_email": customer.email,
                    "cart_count": cart_count,
                    "wishlist_count": wishlist_count
                })
        
        data = {"cart_summary": cart_summary}
        enc = encrypt_payload(data)
        return jsonify({"success": True, "encrypted_data": enc})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@admin_cart_bp.route("/customer-cart/<int:customer_id>", methods=["GET"])
@require_admin_auth
def get_customer_cart_admin(customer_id):
    """Get detailed cart information for a specific customer"""
    try:
        customer = Customer.query.get(customer_id)
        if not customer:
            return jsonify({"success": False, "error": "Customer not found"}), 404
        
        cart_items = get_customer_cart(customer_id)
        wishlist_items = get_customer_wishlist(customer_id)
        
        data = {
            "customer": customer.as_dict(),
            "cart_items": [item.to_dict() for item in cart_items],
            "wishlist_items": [item.to_dict() for item in wishlist_items],
            "cart_total": sum(item.quantity for item in cart_items),
            "wishlist_total": len(wishlist_items)
        }
        
        enc = encrypt_payload(data)
        return jsonify({"success": True, "encrypted_data": enc})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@admin_cart_bp.route("/cart-items", methods=["GET"])
@require_admin_auth
def get_all_cart_items():
    """Get all cart items across all customers for admin panel"""
    try:
        from models.cart import Cart
        
        # Get all cart items with customer and product details
        cart_items = Cart.query.join(Customer).join(Product).all()
        
        cart_data = []
        for item in cart_items:
            cart_data.append({
                "id": item.id,
                "customer_id": item.customer_id,
                "customer_name": item.customer.username if item.customer else "Unknown",
                "customer_email": item.customer.email if item.customer else "Unknown",
                "product_id": item.product_id,
                "product_name": item.product.pname if item.product else "Unknown",
                "product_price": item.product.price if item.product else 0,
                "quantity": item.quantity,
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "updated_at": item.updated_at.isoformat() if item.updated_at else None
            })
        
        data = {"cart_items": cart_data}
        enc = encrypt_payload(data)
        return jsonify({"success": True, "encrypted_data": enc})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@admin_cart_bp.route("/wishlist-items", methods=["GET"])
@require_admin_auth
def get_all_wishlist_items():
    """Get all wishlist items across all customers for admin panel"""
    try:
        from models.wishlist import Wishlist
        
        # Get all wishlist items with customer and product details
        wishlist_items = Wishlist.query.join(Customer).join(Product).all()
        
        wishlist_data = []
        for item in wishlist_items:
            wishlist_data.append({
                "id": item.id,
                "customer_id": item.customer_id,
                "customer_name": item.customer.username if item.customer else "Unknown",
                "customer_email": item.customer.email if item.customer else "Unknown",
                "product_id": item.product_id,
                "product_name": item.product.pname if item.product else "Unknown",
                "product_price": item.product.price if item.product else 0,
                "created_at": item.created_at.isoformat() if item.created_at else None
            })
        
        data = {"wishlist_items": wishlist_data}
        enc = encrypt_payload(data)
        return jsonify({"success": True, "encrypted_data": enc})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@admin_cart_bp.route("/stats", methods=["GET"])
@require_admin_auth
def get_cart_wishlist_stats():
    """Get overall statistics for cart and wishlist"""
    try:
        from models.cart import Cart
        from models.wishlist import Wishlist
        
        total_cart_items = Cart.query.count()
        total_wishlist_items = Wishlist.query.count()
        customers_with_cart = db.session.query(Cart.customer_id).distinct().count()
        customers_with_wishlist = db.session.query(Wishlist.customer_id).distinct().count()
        
        # Get top products in cart
        from sqlalchemy import func
        top_cart_products = db.session.query(
            Cart.product_id,
            Product.pname,
            func.sum(Cart.quantity).label('total_quantity')
        ).join(Product).group_by(Cart.product_id, Product.pname).order_by(
            func.sum(Cart.quantity).desc()
        ).limit(10).all()
        
        # Get top products in wishlist
        top_wishlist_products = db.session.query(
            Wishlist.product_id,
            Product.pname,
            func.count(Wishlist.id).label('wishlist_count')
        ).join(Product).group_by(Wishlist.product_id, Product.pname).order_by(
            func.count(Wishlist.id).desc()
        ).limit(10).all()
        
        data = {
            "total_cart_items": total_cart_items,
            "total_wishlist_items": total_wishlist_items,
            "customers_with_cart": customers_with_cart,
            "customers_with_wishlist": customers_with_wishlist,
            "top_cart_products": [
                {
                    "product_id": item.product_id,
                    "product_name": item.pname,
                    "total_quantity": int(item.total_quantity)
                } for item in top_cart_products
            ],
            "top_wishlist_products": [
                {
                    "product_id": item.product_id,
                    "product_name": item.pname,
                    "wishlist_count": item.wishlist_count
                } for item in top_wishlist_products
            ]
        }
        
        enc = encrypt_payload(data)
        return jsonify({"success": True, "encrypted_data": enc})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400
