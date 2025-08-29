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

@category_bp.route("/images/<path:image_path>")
def serve_category_image(image_path):
    """Serve category images"""
    try:
        # Decode the image path
        import urllib.parse
        decoded_image_path = urllib.parse.unquote(image_path)
        
        # Ensure the path is within the assets directory
        if not decoded_image_path.startswith('assets/category/'):
            return jsonify({"error": "Invalid image path"}), 400
        
        # Check if file exists
        import os
        if not os.path.exists(decoded_image_path):
            return jsonify({"error": "Image not found"}), 404
        
        # Serve the image
        from flask import send_file
        return send_file(decoded_image_path)
        
    except Exception as e:
        print(f"Serve category image route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500 
