# routes/coupon.py
from flask import Blueprint, request, jsonify
from services.coupon_service import (
    get_all_coupons,
    get_coupon_by_id,
    create_coupon,
    update_coupon,
    delete_coupon,
    get_categories_for_coupon,
    get_subcategories_for_coupon,
    get_products_for_coupon,
    validate_coupon_for_cart
)

coupon_bp = Blueprint("coupon", __name__)

@coupon_bp.route("/", methods=["GET"])
def get_coupons():
    """Get all coupons"""
    try:
        res, status = get_all_coupons()
        return jsonify(res), status
    except Exception as e:
        print(f"Get coupons route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@coupon_bp.route("/<int:coupon_id>", methods=["GET"])
def get_coupon(coupon_id):
    """Get coupon by ID"""
    try:
        res, status = get_coupon_by_id(coupon_id)
        return jsonify(res), status
    except Exception as e:
        print(f"Get coupon route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@coupon_bp.route("/", methods=["POST"])
def add_coupon():
    """Create new coupon"""
    try:
        encrypted_data = request.json.get("payload")
        if not encrypted_data:
            return jsonify({"error": "Missing encrypted payload"}), 400
        
        res, status = create_coupon(encrypted_data)
        return jsonify(res), status
    except Exception as e:
        print(f"Create coupon route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@coupon_bp.route("/<int:coupon_id>", methods=["PUT"])
def edit_coupon(coupon_id):
    """Update coupon"""
    try:
        encrypted_data = request.json.get("payload")
        if not encrypted_data:
            return jsonify({"error": "Missing encrypted payload"}), 400
        
        res, status = update_coupon(coupon_id, encrypted_data)
        return jsonify(res), status
    except Exception as e:
        print(f"Update coupon route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@coupon_bp.route("/<int:coupon_id>", methods=["DELETE"])
def remove_coupon(coupon_id):
    """Delete coupon"""
    try:
        res, status = delete_coupon(coupon_id)
        return jsonify(res), status
    except Exception as e:
        print(f"Delete coupon route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@coupon_bp.route("/targets/categories", methods=["GET"])
def get_coupon_categories():
    """Get categories for coupon target selection"""
    try:
        res, status = get_categories_for_coupon()
        return jsonify(res), status
    except Exception as e:
        print(f"Get coupon categories route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@coupon_bp.route("/targets/subcategories", methods=["GET"])
def get_coupon_subcategories():
    """Get subcategories for coupon target selection"""
    try:
        category_id = request.args.get("category_id", type=int)
        res, status = get_subcategories_for_coupon(category_id)
        return jsonify(res), status
    except Exception as e:
        print(f"Get coupon subcategories route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@coupon_bp.route("/targets/products", methods=["GET"])
def get_coupon_products():
    """Get products for coupon target selection"""
    try:
        subcategory_id = request.args.get("subcategory_id", type=int)
        category_id = request.args.get("category_id", type=int)
        res, status = get_products_for_coupon(subcategory_id, category_id)
        return jsonify(res), status
    except Exception as e:
        print(f"Get coupon products route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@coupon_bp.route("/validate", methods=["POST"])
def validate_coupon():
    """Validate coupon for cart items"""
    try:
        data = request.json
        coupon_code = data.get("coupon_code")
        cart_items = data.get("cart_items", [])
        subtotal = data.get("subtotal", 0)
        
        if not coupon_code:
            return jsonify({"error": "Coupon code is required"}), 400
        
        res, status = validate_coupon_for_cart(coupon_code, cart_items, subtotal)
        return jsonify(res), status
        
    except Exception as e:
        print(f"Validate coupon route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500 
