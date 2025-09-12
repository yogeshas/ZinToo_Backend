from flask import Blueprint, request, jsonify, current_app
from services.address_service import (
    create_address,
    get_addresses_by_customer,
    get_address_by_id,
    update_address,
    delete_address,
)
from utils.crypto import decrypt_payload
from utils.auth import require_customer_auth

address_bp = Blueprint("address", __name__)
@address_bp.route("/", methods=["GET"])
@require_customer_auth
def list_my_addresses(current_customer):
    """Return addresses for the logged-in customer (plain JSON for simple use)."""
    try:
        uid = int(current_customer["id"])
        addresses = get_addresses_by_customer(uid)
        result = {
            "success": True,
            "addresses": [
                {
                    "id": a.id,
                    "customer_id": a.uid,
                    "name": a.name,
                    "city": a.city,
                    "state": a.state,
                    "country": a.country,
                    "postal_code": a.zip_code,
                    "type": a.type,
                }
                for a in addresses
            ]
        }
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@address_bp.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for debugging"""
    try:
        from models.address import Address
        from extensions import db
        
        # Test database connection
        db.engine.execute("SELECT 1")
        
        # Test address model
        address_count = Address.query.count()
        
        return jsonify({
            "success": True,
            "message": "Address API is healthy",
            "database": "connected",
            "address_count": address_count,
            "timestamp": "2024-01-01T00:00:00Z"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": "2024-01-01T00:00:00Z"
        }), 500


@address_bp.route("/customer/<int:uid>", methods=["GET"])
def get_customer_addresses(uid):
    """Get all addresses for a specific customer"""
    try:
        print(f"[ADDRESS API] Getting addresses for customer {uid}")
        addresses = get_addresses_by_customer(uid)
        print(f"[ADDRESS API] Found {len(addresses)} addresses")
        
        # Encrypt the response data
        from utils.crypto import encrypt_payload
        
        result = {
            "success": True,
            "addresses": [
                {
                    "id": a.id,
                    "customer_id": a.uid,
                    "address_line1": a.name,
                    "address_line2": "",
                    "city": a.city,
                    "state": a.state,
                    "country": a.country,
                    "postal_code": a.zip_code,
                    "type": a.type,
                    "is_default": False,  # You can add this field to your address model
                    "created_at": a.created_at.isoformat() if hasattr(a, 'created_at') else None,
                    "updated_at": a.updated_at.isoformat() if hasattr(a, 'updated_at') else None,
                }
                for a in addresses
            ]
        }
        
        encrypted_data = encrypt_payload(result)
        
        print(f"[ADDRESS API] Returning encrypted result with {len(result['addresses'])} addresses")
        return jsonify({
            "success": True,
            "encrypted_data": encrypted_data,
            "message": "Addresses retrieved successfully"
        })
        
    except Exception as e:
        print(f"[ADDRESS API] Error getting addresses for customer {uid}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@address_bp.route("/<int:aid>", methods=["GET"])
def get_address(aid):
    """Get a specific address by ID"""
    try:
        address = get_address_by_id(aid)
        if not address:
            return jsonify({"success": False, "error": "Address not found"}), 404
        
        # Encrypt the response data
        from utils.crypto import encrypt_payload
        
        address_data = {
            "id": address.id,
            "customer_id": address.uid,
            "address_line1": address.name,
            "address_line2": "",
            "city": address.city,
            "state": address.state,
            "country": address.country,
            "postal_code": address.zip_code,
            "type": address.type,
            "is_default": False,
            "created_at": address.created_at.isoformat() if hasattr(address, 'created_at') else None,
            "updated_at": address.updated_at.isoformat() if hasattr(address, 'updated_at') else None,
        }
        
        encrypted_data = encrypt_payload({
            "success": True,
            "address": address_data
        })
        
        return jsonify({
            "success": True,
            "encrypted_data": encrypted_data,
            "message": "Address retrieved successfully"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@address_bp.route("/", methods=["POST"])
def create():
    """Create a new address"""
    try:
        print(f"[ADDRESS ROUTE] Creating new address")
        data = request.json or {}
        print(f"[ADDRESS ROUTE] Raw request data: {data}")
        
        # Handle encrypted payload if present
        if "payload" in data:
            try:
                data = decrypt_payload(data["payload"])
                print(f"[ADDRESS ROUTE] Decrypted from payload: {data}")
            except Exception as e:
                return jsonify({"success": False, "error": f"Decryption failed: {str(e)}"}), 400
        elif "data" in data:
            try:
                data = decrypt_payload(data["data"])
                print(f"[ADDRESS ROUTE] Decrypted from data: {data}")
            except Exception as e:
                return jsonify({"success": False, "error": f"Decryption failed: {str(e)}"}), 400
        
        # Extract user ID and address data
        uid = data.get("uid") or data.get("user_id") or data.get("customer_id")
        payload = data.get("address") or data
        print(f"[ADDRESS ROUTE] Extracted uid: {uid}, payload: {payload}")
        
        if not uid:
            return jsonify({"success": False, "error": "User ID is required"}), 400
        
        # Validate required fields
        required_fields = ["name", "city", "state", "country", "zip_code"]
        missing_fields = [field for field in required_fields if not payload.get(field)]
        if missing_fields:
            return jsonify({"success": False, "error": f"Missing required fields: {', '.join(missing_fields)}"}), 400
        
        address = create_address(uid, payload)
        
        # Encrypt the response data
        from utils.crypto import encrypt_payload
        
        address_data = {
            "id": address.id,
            "customer_id": address.uid,
            "address_line1": address.name,
            "address_line2": "",
            "city": address.city,
            "state": address.state,
            "country": address.country,
            "postal_code": address.zip_code,
            "type": address.type,
            "is_default": False,
            "created_at": address.created_at.isoformat() if hasattr(address, 'created_at') else None,
            "updated_at": address.updated_at.isoformat() if hasattr(address, 'updated_at') else None,
        }
        
        encrypted_data = encrypt_payload({
            "success": True,
            "address": address_data
        })
        
        return jsonify({
            "success": True,
            "encrypted_data": encrypted_data,
            "message": "Address created successfully"
        }), 201
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@address_bp.route("/<int:aid>", methods=["PUT", "PATCH"])
def update(aid):
    """Update an existing address"""
    try:
        print(f"[ADDRESS ROUTE] Updating address ID: {aid}")
        data = request.json or {}
        print(f"[ADDRESS ROUTE] Raw request data: {data}")
        
        # Handle encrypted payload if present
        if "payload" in data:
            try:
                data = decrypt_payload(data["payload"])
                print(f"[ADDRESS ROUTE] Decrypted from payload: {data}")
            except Exception as e:
                return jsonify({"success": False, "error": f"Decryption failed: {str(e)}"}), 400
        elif "data" in data:
            try:
                data = decrypt_payload(data["data"])
                print(f"[ADDRESS ROUTE] Decrypted from data: {data}")
            except Exception as e:
                return jsonify({"success": False, "error": f"Decryption failed: {str(e)}"}), 400
        
        print(f"[ADDRESS ROUTE] Final data for update: {data}")
        address = update_address(aid, data)
        if not address:
            return jsonify({"success": False, "error": "Address not found"}), 404
        
        # Encrypt the response data
        from utils.crypto import encrypt_payload
        
        address_data = {
            "id": address.id,
            "customer_id": address.uid,
            "address_line1": address.name,
            "address_line2": "",
            "city": address.city,
            "state": address.state,
            "country": address.country,
            "postal_code": address.zip_code,
            "type": address.type,
            "is_default": False,
            "created_at": address.created_at.isoformat() if hasattr(address, 'created_at') else None,
            "updated_at": address.updated_at.isoformat() if hasattr(address, 'updated_at') else None,
        }
        
        encrypted_data = encrypt_payload({
            "success": True,
            "address": address_data
        })
        
        return jsonify({
            "success": True,
            "encrypted_data": encrypted_data,
            "message": "Address updated successfully"
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@address_bp.route("/<int:aid>", methods=["DELETE"])
def remove(aid):
    """Delete an address"""
    try:
        print(f"[ADDRESS ROUTE] Deleting address ID: {aid}")
        ok = delete_address(aid)
        if not ok:
            return jsonify({"success": False, "error": "Address not found"}), 404
        
        # Encrypt the response data
        from utils.crypto import encrypt_payload
        
        encrypted_data = encrypt_payload({
            "success": True,
            "message": "Address deleted successfully"
        })
        
        return jsonify({
            "success": True,
            "encrypted_data": encrypted_data,
            "message": "Address deleted successfully"
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
