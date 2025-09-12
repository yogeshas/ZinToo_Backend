# routes/product_routes.py
from flask import Blueprint, request, jsonify, current_app, send_from_directory
from werkzeug.utils import secure_filename
import os
from uuid import uuid4
from services.product_service import (
    create_product,
    get_product_by_id,
    get_all_products,
    get_customer_products,
    update_product,
    delete_product,
    regenerate_product_barcode,
)
from utils.barcode_image_generator import generate_barcode_image, generate_barcode_sticker_html
from utils.delivery_barcode_generator import generate_delivery_barcode_image, generate_delivery_barcode_sticker_html
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
        product_id = request.form.get("product_id")
        color_name = request.form.get("color_name")  # Optional for color-specific images
        
        if not files or all(not f or not getattr(f, "filename", None) for f in files):
            return jsonify({"success": False, "error": "No files provided"}), 400

        # Try S3 upload first, fallback to local storage
        try:
            from utils.s3_service import S3Service
            s3_service = S3Service()
            
            allowed_ext = {"png", "jpg", "jpeg", "gif", "webp"}
            urls = []
            
            for f in files:
                if not f or not getattr(f, "filename", None):
                    continue
                    
                ext = f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else ""
                
                if ext not in allowed_ext:
                    return jsonify({"success": False, "error": f"Unsupported file type: {ext}"}), 400
                    
                mimetype = f.mimetype or ""
                if not mimetype.startswith("image/"):
                    return jsonify({"success": False, "error": "Only image files are allowed"}), 400
                
                # Upload to S3 with organized folder structure
                if product_id:
                    url = s3_service.upload_product_file(f, product_id, color_name)
                else:
                    url = s3_service.upload_file(f, "temp", "image", "products")
                
                if url:
                    urls.append(url)
                else:
                    return jsonify({"success": False, "error": f"Failed to upload file: {f.filename}"}), 500

            return jsonify({"success": True, "files": urls})
            
        except Exception as s3_error:
            print(f"S3 upload failed, falling back to local storage: {str(s3_error)}")
            
            # Fallback to local storage
            base_dir = os.path.join(current_app.root_path, "assets", "img", "products")
            os.makedirs(base_dir, exist_ok=True)
            
            if not os.path.exists(base_dir):
                return jsonify({"success": False, "error": "Failed to create upload directory"}), 500

            allowed_ext = {"png", "jpg", "jpeg", "gif", "webp"}
            urls = []
            
            for f in files:
                if not f or not getattr(f, "filename", None):
                    continue
                    
                ext = f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else ""
                
                if ext not in allowed_ext:
                    return jsonify({"success": False, "error": f"Unsupported file type: {ext}"}), 400
                    
                mimetype = f.mimetype or ""
                if not mimetype.startswith("image/"):
                    return jsonify({"success": False, "error": "Only image files are allowed"}), 400
                    
                unique_name = f"{uuid4().hex}_{secure_filename(f.filename)}"
                save_path = os.path.join(base_dir, unique_name)
                
                try:
                    f.save(save_path)
                    
                    if os.path.exists(save_path):
                        urls.append(f"/api/products/images/{unique_name}")
                    else:
                        return jsonify({"success": False, "error": f"Failed to save file: {f.filename}"}), 500
                        
                except Exception as save_error:
                    return jsonify({"success": False, "error": f"Failed to save file: {str(save_error)}"}), 500

            return jsonify({"success": True, "files": urls})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# GET all products (admin)
@product_bp.route("/", methods=["GET"])
def list_products():
    products = get_all_products()
    response = {"products": [p.to_dict() for p in products]}
    encrypted = encrypt_payload(response)
    return jsonify({"success": True, "encrypted_data": encrypted})

# GET customer products (filtered for customer view)
@product_bp.route("/customer", methods=["GET"])
def list_customer_products():
    products = get_customer_products()
    response = {"products": [p.to_dict() for p in products]}
    encrypted = encrypt_payload(response)
    return jsonify({"success": True, "encrypted_data": encrypted})


# GET product by ID (admin)
@product_bp.route("/<int:pid>", methods=["GET"])
def get_product(pid):
    p = get_product_by_id(pid)
    if not p:
        return jsonify({"success": False, "error": "Not found"}), 404
    stats = get_product_review_stats(p.id)
    response = {"product": p.to_dict(), "review_stats": stats}
    encrypted = encrypt_payload(response)
    return jsonify({"success": True, "encrypted_data": encrypted})

# GET customer product by ID (filtered for customer view)
@product_bp.route("/customer/<int:pid>", methods=["GET"])
def get_customer_product(pid):
    p = get_product_by_id(pid)
    if not p or not p.is_active or not p.visibility:
        return jsonify({"success": False, "error": "Product not found or not available"}), 404
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

        product = create_product(data)  # pass dict
        response = {"product": product.to_dict()}
        encrypted = encrypt_payload(response)
        return jsonify({"success": True, "encrypted_data": encrypted})
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
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


# REGENERATE BARCODE
@product_bp.route("/<int:pid>/regenerate-barcode", methods=["POST"])
def regenerate_barcode(pid):
    try:
        result = regenerate_product_barcode(pid)
        if result["success"]:
            response = {"barcode": result["barcode"]}
            encrypted = encrypt_payload(response)
            return jsonify({"success": True, "encrypted_data": encrypted})
        else:
            return jsonify({"success": False, "error": result["error"]}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# GENERATE BARCODE IMAGE
@product_bp.route("/<int:pid>/barcode-image", methods=["GET"])
def get_barcode_image(pid):
    try:
        product = get_product_by_id(pid)
        if not product:
            return jsonify({"success": False, "error": "Product not found"}), 404
        
        if not product.barcode:
            return jsonify({"success": False, "error": "Product has no barcode"}), 400
        
        # Generate delivery-optimized barcode image
        image_data = generate_delivery_barcode_image(
            product.barcode, 
            product.pname, 
            product.id
        )
        
        if not image_data:
            return jsonify({"success": False, "error": "Failed to generate barcode image"}), 500
        
        response = {"barcode_image": image_data}
        encrypted = encrypt_payload(response)
        return jsonify({"success": True, "encrypted_data": encrypted})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# GENERATE BARCODE STICKER HTML FOR PRINTING
@product_bp.route("/<int:pid>/barcode-sticker", methods=["GET"])
def get_barcode_sticker(pid):
    try:
        product = get_product_by_id(pid)
        if not product:
            return jsonify({"success": False, "error": "Product not found"}), 404
        
        if not product.barcode:
            return jsonify({"success": False, "error": "Product has no barcode"}), 400
        
        # Generate delivery-optimized sticker HTML
        html_content = generate_delivery_barcode_sticker_html(
            product.barcode,
            product.pname,
            product.id
        )
        
        return html_content, 200, {'Content-Type': 'text/html'}
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
