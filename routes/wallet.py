# routes/wallet.py
from flask import Blueprint, request, jsonify
from services.wallet_service import (
    get_wallet_balance,
    add_money_to_wallet,
    deduct_money_from_wallet,
    get_wallet_transactions,
    refund_to_wallet
)
from utils.auth import require_customer_auth
from utils.crypto import decrypt_payload

wallet_bp = Blueprint("wallet", __name__)

@wallet_bp.route("/balance", methods=["GET"])
@require_customer_auth
def get_balance(current_customer):
    """Get customer wallet balance"""
    try:
        customer_id = current_customer["id"]
        res, status = get_wallet_balance(customer_id)
        return jsonify(res), status
    except Exception as e:
        print(f"Get wallet balance route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@wallet_bp.route("/add-money", methods=["POST"])
@require_customer_auth
def add_money(current_customer):
    """Add money to customer wallet"""
    try:
        customer_id = current_customer["id"]
        encrypted_data = request.json.get("payload")
        if not encrypted_data:
            return jsonify({"error": "Missing encrypted payload"}), 400
        
        decrypted_data = decrypt_payload(encrypted_data)
        amount = decrypted_data.get("amount")
        description = decrypted_data.get("description", "Wallet recharge")
        reference_id = decrypted_data.get("reference_id")
        
        if not amount or amount <= 0:
            return jsonify({"error": "Invalid amount"}), 400
        
        res, status = add_money_to_wallet(customer_id, amount, description, reference_id)
        return jsonify(res), status
    except Exception as e:
        print(f"Add money to wallet route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@wallet_bp.route("/deduct-money", methods=["POST"])
@require_customer_auth
def deduct_money(current_customer):
    """Deduct money from customer wallet"""
    try:
        customer_id = current_customer["id"]
        encrypted_data = request.json.get("payload")
        if not encrypted_data:
            return jsonify({"error": "Missing encrypted payload"}), 400
        
        decrypted_data = decrypt_payload(encrypted_data)
        amount = decrypted_data.get("amount")
        description = decrypted_data.get("description", "Purchase")
        reference_id = decrypted_data.get("reference_id")
        
        if not amount or amount <= 0:
            return jsonify({"error": "Invalid amount"}), 400
        
        res, status = deduct_money_from_wallet(customer_id, amount, description, reference_id)
        return jsonify(res), status
    except Exception as e:
        print(f"Deduct money from wallet route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@wallet_bp.route("/transactions", methods=["GET"])
@require_customer_auth
def get_transactions(current_customer):
    """Get customer wallet transaction history"""
    try:
        customer_id = current_customer["id"]
        limit = request.args.get("limit", 10, type=int)
        
        res, status = get_wallet_transactions(customer_id, limit)
        return jsonify(res), status
    except Exception as e:
        print(f"Get wallet transactions route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@wallet_bp.route("/refund", methods=["POST"])
@require_customer_auth
def refund_money(current_customer):
    """Refund money to customer wallet"""
    try:
        customer_id = current_customer["id"]
        encrypted_data = request.json.get("payload")
        if not encrypted_data:
            return jsonify({"error": "Missing encrypted payload"}), 400
        
        decrypted_data = decrypt_payload(encrypted_data)
        amount = decrypted_data.get("amount")
        description = decrypted_data.get("description", "Refund")
        reference_id = decrypted_data.get("reference_id")
        
        if not amount or amount <= 0:
            return jsonify({"error": "Invalid amount"}), 400
        
        res, status = refund_to_wallet(customer_id, amount, description, reference_id)
        return jsonify(res), status
    except Exception as e:
        print(f"Refund to wallet route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
