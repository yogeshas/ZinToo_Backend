# routes/product_routes.py
from flask import Blueprint, request, jsonify, current_app, send_from_directory
from werkzeug.utils import secure_filename
import os
from uuid import uuid4
from services.product_service import (
    create_product,
    get_product_by_id,
    get_all_products,
    update_product,
    delete_product,
)
from services.review_service import get_product_review_stats
from utils.crypto import encrypt_payload, decrypt_payload

product_bp = Blueprint("products", __name__)
# Serve product images
@product_bp.route("/images/<path:filename>", methods=["GET"])
def serve_product_image(filename):
    base_dir = os.path.join(current_app.root_path, "assets", "img", "products")
    return send_from_directory(base_dir, filename)


# Upload multiple product images
@product_bp.route("/upload-images", methods=["POST"])
def upload_images():
    try:
        files = request.files.getlist("images")
        if not files:
            return jsonify({"success": False, "error": "No files provided"}), 400

        base_dir = os.path.join(current_app.root_path, "assets", "img", "products")
        os.makedirs(base_dir, exist_ok=True)

        allowed_ext = {"png", "jpg", "jpeg", "gif", "webp"}
        urls = []
        for f in files:
            if not f or not getattr(f, "filename", None):
                continue
            ext = f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else ""
            if ext not in allowed_ext:
                return jsonify({"success": False, "error": f"Unsupported file type: {ext}"}), 400
            if not (f.mimetype or "").startswith("image/"):
                return jsonify({"success": False, "error": "Only image files are allowed"}), 400
            unique_name = f"{uuid4().hex}_{secure_filename(f.filename)}"
            save_path = os.path.join(base_dir, unique_name)
            f.save(save_path)
            urls.append(f"/api/products/images/{unique_name}")

        return jsonify({"success": True, "files": urls})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# GET all products
@product_bp.route("/", methods=["GET"])
def list_products():
    products = get_all_products()
    response = {"products": [p.to_dict() for p in products]}
    encrypted = encrypt_payload(response)
    return jsonify({"success": True, "encrypted_data": encrypted})


# GET product by ID
@product_bp.route("/<int:pid>", methods=["GET"])
def get_product(pid):
    p = get_product_by_id(pid)
    if not p:
        return jsonify({"success": False, "error": "Not found"}), 404
    stats = get_product_review_stats(p.id)
    response = {"product": p.to_dict(), "review_stats": stats}
    encrypted = encrypt_payload(response)
    return jsonify({"success": True, "encrypted_data": encrypted})


# CREATE product
@product_bp.route("/", methods=["POST"])
def create():
    try:
        encrypted_request = request.json.get("data")
        if not encrypted_request:
            return jsonify({"success": False, "error": "Missing encrypted data"}), 400
            
        data = decrypt_payload(encrypted_request)
        if not data:
            return jsonify({"success": False, "error": "Invalid encrypted data"}), 400

        # Debug: Print the received data
        print(f"Received product data: {data}")

        product = create_product(data)  # pass dict
        response = {"product": product.to_dict()}
        encrypted = encrypt_payload(response)
        return jsonify({"success": True, "encrypted_data": encrypted})
    except ValueError as e:
        print(f"Validation error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        print(f"Product creation error: {str(e)}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


# UPDATE product
@product_bp.route("/<int:pid>", methods=["PUT"])
def update(pid):
    try:
        encrypted_request = request.json.get("data")
        data = decrypt_payload(encrypted_request)

        product = update_product(pid, data)
        if not product:
            return jsonify({"success": False, "error": "Not found"}), 404

        response = {"product": product.to_dict()}
        encrypted = encrypt_payload(response)
        return jsonify({"success": True, "encrypted_data": encrypted})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


# DELETE product
@product_bp.route("/<int:pid>", methods=["DELETE"])
def delete(pid):
    deleted = delete_product(pid)
    if not deleted:
        return jsonify({"success": False, "error": "Not found"}), 404
    return jsonify({"success": True, "message": "Product deleted"})
