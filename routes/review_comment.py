from flask import Blueprint, request, jsonify
from utils.crypto import encrypt_payload, decrypt_payload
from utils.auth import require_customer_auth, require_admin_auth
from services.review_comment_service import list_comments, create_comment, moderate_comment


review_comment_bp = Blueprint("review_comments", __name__)


@review_comment_bp.route("/review/<int:review_id>", methods=["GET"])
def get_comments(review_id):
    comments = list_comments(review_id)
    enc = encrypt_payload({"comments": [c.to_dict() for c in comments]})
    return jsonify({"success": True, "encrypted_data": enc})


@review_comment_bp.route("/", methods=["POST"])
@require_customer_auth
def add_comment_customer(current_customer):
    payload = request.json.get("payload")
    data = decrypt_payload(payload)
    comment = create_comment({"customer_id": current_customer["id"]}, {**data, "author_type": "customer"})
    enc = encrypt_payload({"comment": comment.to_dict()})
    return jsonify({"success": True, "encrypted_data": enc})


@review_comment_bp.route("/admin", methods=["POST"])
@require_admin_auth
def add_comment_admin(current_admin):
    payload = request.json.get("payload")
    data = decrypt_payload(payload)
    comment = create_comment({"admin_id": current_admin["id"]}, {**data, "author_type": "admin"})
    enc = encrypt_payload({"comment": comment.to_dict()})
    return jsonify({"success": True, "encrypted_data": enc})


@review_comment_bp.route("/<int:comment_id>/status", methods=["PUT"])
@require_admin_auth
def moderate(current_admin, comment_id):
    payload = request.json.get("payload")
    data = decrypt_payload(payload)
    c = moderate_comment(comment_id, data.get("status"))
    if not c:
        return jsonify({"success": False, "error": "Not found"}), 404
    enc = encrypt_payload({"comment": c.to_dict()})
    return jsonify({"success": True, "encrypted_data": enc})


