# routes/widget.py
from flask import Blueprint, request, jsonify, current_app
from services.widget_service import (
    get_all_widgets,
    get_widget_by_id,
    create_widget,
    update_widget,
    delete_widget,
    delete_widget_image
)
import os

widget_bp = Blueprint("widget", __name__)

@widget_bp.route("/", methods=["GET"])
def get_widgets():
    """Get all widgets"""
    try:
        res, status = get_all_widgets()
        return jsonify(res), status
    except Exception as e:
        print(f"Get widgets route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@widget_bp.route("/<int:widget_id>", methods=["GET"])
def get_widget(widget_id):
    """Get widget by ID"""
    try:
        res, status = get_widget_by_id(widget_id)
        return jsonify(res), status
    except Exception as e:
        print(f"Get widget route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@widget_bp.route("/", methods=["POST"])
def add_widget():
    """Create new widget with images"""
    try:
        # Get form data
        encrypted_data = request.form.get("payload")
        if not encrypted_data:
            return jsonify({"error": "Missing encrypted payload"}), 400
        
        # Get uploaded files
        files = request.files.getlist("images")
        
        res, status = create_widget(encrypted_data, files)
        return jsonify(res), status
    except Exception as e:
        print(f"Create widget route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@widget_bp.route("/<int:widget_id>", methods=["PUT"])
def edit_widget(widget_id):
    """Update widget with images"""
    try:
        # Get form data
        encrypted_data = request.form.get("payload")
        if not encrypted_data:
            return jsonify({"error": "Missing encrypted payload"}), 400
        
        # Get uploaded files
        files = request.files.getlist("images")
        
        res, status = update_widget(widget_id, encrypted_data, files)
        return jsonify(res), status
    except Exception as e:
        print(f"Update widget route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@widget_bp.route("/<int:widget_id>", methods=["DELETE"])
def remove_widget(widget_id):
    """Delete widget"""
    try:
        res, status = delete_widget(widget_id)
        return jsonify(res), status
    except Exception as e:
        print(f"Delete widget route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@widget_bp.route("/<int:widget_id>/images/<path:image_path>", methods=["DELETE"])
def remove_widget_image_route(widget_id, image_path):
    """Delete specific image from widget"""
    try:
        # Decode the image path
        import urllib.parse
        decoded_image_path = urllib.parse.unquote(image_path)
        
        res, status = delete_widget_image(widget_id, decoded_image_path)
        return jsonify(res), status
    except Exception as e:
        print(f"Delete widget image route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@widget_bp.route("/images/<path:image_path>")
def serve_widget_image(image_path):
    """Serve widget images"""
    try:
        # Decode the image path
        import urllib.parse
        decoded_image_path = urllib.parse.unquote(image_path)
        
        # Ensure the path is within the assets directory
        if not decoded_image_path.startswith('assets/img/widgets/'):
            return jsonify({"error": "Invalid image path"}), 400
        
        # Check if file exists
        if not os.path.exists(decoded_image_path):
            return jsonify({"error": "Image not found"}), 404
        
        # Serve the image
        from flask import send_file
        return send_file(decoded_image_path)
        
    except Exception as e:
        print(f"Serve widget image route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500 
