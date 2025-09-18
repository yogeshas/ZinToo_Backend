from flask import Blueprint, request, jsonify, current_app
import os
from uuid import uuid4
from werkzeug.utils import secure_filename

from utils.crypto import encrypt_payload, decrypt_payload
from utils.auth import require_customer_auth, require_admin_auth
from utils.s3_service import s3_service
from services.review_service import (
    create_review,
    list_reviews_for_product,
    list_reviews_for_admin,
    update_review_status,
    add_media_to_review,
    get_product_review_stats,
)


review_bp = Blueprint("reviews", __name__)


@review_bp.route("/", methods=["POST"])
@require_customer_auth
def create(current_customer):
    encrypted_request = request.json.get("payload")
    if not encrypted_request:
        return jsonify({"success": False, "error": "Missing encrypted payload"}), 400
    data = decrypt_payload(encrypted_request)
    review = create_review(current_customer["id"], data)
    enc = encrypt_payload({"review": review.to_dict()})
    return jsonify({"success": True, "encrypted_data": enc})


@review_bp.route("/product/<int:product_id>", methods=["GET"])
def list_for_product(product_id):
    status = request.args.get("status", "approved")
    reviews = list_reviews_for_product(product_id, status)
    stats = get_product_review_stats(product_id)
    enc = encrypt_payload({
        "reviews": [r.to_dict() for r in reviews],
        "stats": stats,
    })
    return jsonify({"success": True, "encrypted_data": enc})


@review_bp.route("/admin", methods=["GET"])
@require_admin_auth
def admin_list(current_admin):
    product_id = request.args.get("product_id")
    status = request.args.get("status")
    pid = int(product_id) if product_id else None
    reviews = list_reviews_for_admin(pid, status)
    enc = encrypt_payload({"reviews": [r.to_dict() for r in reviews]})
    return jsonify({"success": True, "encrypted_data": enc})


@review_bp.route("/admin/<int:review_id>/status", methods=["PUT"])
@require_admin_auth
def admin_update_status(current_admin, review_id):
    encrypted_request = request.json.get("payload")
    if not encrypted_request:
        return jsonify({"success": False, "error": "Missing encrypted payload"}), 400
    data = decrypt_payload(encrypted_request)
    review = update_review_status(review_id, data.get("status"), data.get("admin_note"))
    if not review:
        return jsonify({"success": False, "error": "Review not found"}), 404
    enc = encrypt_payload({"review": review.to_dict()})
    return jsonify({"success": True, "encrypted_data": enc})


@review_bp.route("/upload-media", methods=["OPTIONS"])
def upload_media_options():
    # Allow CORS preflight
    return ("", 200)


@review_bp.route("/upload-media", methods=["POST"])
@require_customer_auth
def upload_media(current_customer):
    files = request.files.getlist("files")
    if not files:
        return jsonify({"success": False, "error": "No files provided"}), 400

    # Validate file types
    image_ext = {"png", "jpg", "jpeg", "gif", "webp"}
    video_ext = {"mp4", "webm", "mov", "avi"}
    
    for f in files:
        if not f or not getattr(f, "filename", None):
            continue
        ext = f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else ""
        
        if ext in image_ext:
            if not (f.mimetype or "").startswith("image/"):
                return jsonify({"success": False, "error": "Invalid image file"}), 400
        elif ext in video_ext:
            if not (f.mimetype or "").startswith("video/"):
                return jsonify({"success": False, "error": "Invalid video file"}), 400
        else:
            return jsonify({"success": False, "error": f"Unsupported file type: {ext}"}), 400

    try:
        # Upload files to S3 using environment configuration
        # Use customer ID as file_id for unique naming
        result = s3_service.upload_multiple_files(
            files, 
            current_customer["id"], 
            "review"  # Use review folder from environment
        )
        
        if not result['images'] and not result['videos']:
            return jsonify({"success": False, "error": "Failed to upload files"}), 500

        enc = encrypt_payload({
            "images": result['images'], 
            "videos": result['videos']
        })
        return jsonify({"success": True, "encrypted_data": enc})
        
    except Exception as e:
        print(f"❌ S3 upload error: {str(e)}")
        return jsonify({"success": False, "error": "Failed to upload files to S3"}), 500


# Note: Media serving is now handled by S3 directly via public URLs
# The image_urls and video_urls fields in the database now contain full S3 URLs
# Frontend can access media directly using the URLs from the API response


