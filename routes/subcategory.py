# routes/subcategory.py
from flask import Blueprint, request, jsonify
from services.subcategory_service import (
    get_all_subcategories,
    get_subcategory_by_id,
    get_subcategories_by_category,
    create_subcategory,
    update_subcategory,
    delete_subcategory
)

subcategory_bp = Blueprint("subcategory", __name__)

@subcategory_bp.route("/", methods=["GET"])
def get_subcategories():
    """Get all subcategories"""
    try:
        res, status = get_all_subcategories()
        return jsonify(res), status
    except Exception as e:
        print(f"Get subcategories route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@subcategory_bp.route("/<int:subcategory_id>", methods=["GET"])
def get_subcategory(subcategory_id):
    """Get subcategory by ID"""
    try:
        res, status = get_subcategory_by_id(subcategory_id)
        return jsonify(res), status
    except Exception as e:
        print(f"Get subcategory route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@subcategory_bp.route("/category/<int:category_id>", methods=["GET"])
def get_subcategories_by_category_route(category_id):
    """Get subcategories by parent category ID"""
    try:
        res, status = get_subcategories_by_category(category_id)
        return jsonify(res), status
    except Exception as e:
        print(f"Get subcategories by category route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@subcategory_bp.route("/", methods=["POST"])
def add_subcategory():
    """Create new subcategory"""
    try:
        encrypted_data = request.json.get("payload")
        if not encrypted_data:
            return jsonify({"error": "Missing encrypted payload"}), 400
        
        res, status = create_subcategory(encrypted_data)
        return jsonify(res), status
    except Exception as e:
        print(f"Create subcategory route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@subcategory_bp.route("/<int:subcategory_id>", methods=["PUT"])
def edit_subcategory(subcategory_id):
    """Update subcategory"""
    try:
        encrypted_data = request.json.get("payload")
        if not encrypted_data:
            return jsonify({"error": "Missing encrypted payload"}), 400
        
        res, status = update_subcategory(subcategory_id, encrypted_data)
        return jsonify(res), status
    except Exception as e:
        print(f"Update subcategory route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@subcategory_bp.route("/<int:subcategory_id>", methods=["DELETE"])
def remove_subcategory(subcategory_id):
    """Delete subcategory"""
    try:
        res, status = delete_subcategory(subcategory_id)
        return jsonify(res), status
    except Exception as e:
        print(f"Delete subcategory route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500 
