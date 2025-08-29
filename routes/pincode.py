from flask import Blueprint, request, jsonify
from models.pincode import Pincode
from models.address import Address
from utils.crypto import encrypt_payload, decrypt_payload


pincode_bp = Blueprint("pincode", __name__)


@pincode_bp.route("/check", methods=["POST"])
def check_pincode():
    payload = request.json.get("payload")
    if not payload:
        return jsonify({"success": False, "error": "Missing encrypted payload"}), 400
    data = decrypt_payload(payload)
    code = (data.get("pincode") or data.get("zip") or data.get("postal") or "").strip()
    if not code:
        return jsonify({"success": False, "error": "Pincode required"}), 400
    pin = Pincode.query.filter_by(code=code).first()
    serviceable = bool(pin and pin.is_serviceable)
    enc = encrypt_payload({"serviceable": serviceable, "pincode": code, "city": pin.city if pin else None, "state": pin.state if pin else None})
    return jsonify({"success": True, "encrypted_data": enc})


@pincode_bp.route("/check-address", methods=["POST"])
def check_address():
    payload = request.json.get("payload")
    if not payload:
        return jsonify({"success": False, "error": "Missing encrypted payload"}), 400
    data = decrypt_payload(payload)
    address_id = data.get("address_id")
    if not address_id:
        return jsonify({"success": False, "error": "address_id required"}), 400
    address = Address.query.get(int(address_id))
    if not address:
        return jsonify({"success": False, "error": "Address not found"}), 404
    pin = Pincode.query.filter_by(code=str(address.zip_code)).first()
    serviceable = bool(pin and pin.is_serviceable)
    enc = encrypt_payload({"serviceable": serviceable, "pincode": address.zip_code})
    return jsonify({"success": True, "encrypted_data": enc})


