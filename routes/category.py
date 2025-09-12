# routes/category.py
from flask import Blueprint, request, jsonify
from services.category_service import (
    get_all_categories,
    get_category_by_id,
    create_category,
    update_category,
    delete_category
)

category_bp = Blueprint("category", __name__)

@category_bp.route("/", methods=["GET"])
def get_categories():
    """Get all categories"""
    try:
        res, status = get_all_categories()
        return jsonify(res), status
    except Exception as e:
        print(f"Get categories route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@category_bp.route("/<int:category_id>", methods=["GET"])
def get_category(category_id):
    """Get category by ID"""
    try:
        res, status = get_category_by_id(category_id)
        return jsonify(res), status
    except Exception as e:
        print(f"Get category route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@category_bp.route("/", methods=["POST"])
def add_category():
    """Create new category with optional image"""
    try:
        # Get form data
        encrypted_data = request.form.get("payload")
        if not encrypted_data:
            return jsonify({"error": "Missing encrypted payload"}), 400
        
        # Get uploaded file
        file = request.files.get("image")
        
        res, status = create_category(encrypted_data, file)
        return jsonify(res), status
    except Exception as e:
        print(f"Create category route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@category_bp.route("/<int:category_id>", methods=["PUT"])
def edit_category(category_id):
    """Update category with optional image"""
    try:
        # Get form data
        encrypted_data = request.form.get("payload")
        if not encrypted_data:
            return jsonify({"error": "Missing encrypted payload"}), 400
        
        # Get uploaded file
        file = request.files.get("image")
        
        res, status = update_category(category_id, encrypted_data, file)
        return jsonify(res), status
    except Exception as e:
        print(f"Update category route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@category_bp.route("/<int:category_id>", methods=["DELETE"])
def remove_category(category_id):
    """Delete category"""
    try:
        res, status = delete_category(category_id)
        return jsonify(res), status
    except Exception as e:
        print(f"Delete category route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

# Note: Image serving is now handled by S3 directly via public URLs
# The image field in the database now contains the full S3 URL
# Frontend can access images directly using the URL from the API response 
