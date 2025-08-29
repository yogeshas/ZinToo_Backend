# routes/razorpay.py
from flask import Blueprint, request, jsonify
from services.razorpay_service import (
    create_wallet_payment_order,
    verify_payment_signature,
    get_payment_details
)
from services.wallet_service import add_money_to_wallet
from utils.auth import require_customer_auth
from utils.crypto import decrypt_payload

razorpay_bp = Blueprint("razorpay", __name__)

@razorpay_bp.route("/create-order", methods=["POST"])
@require_customer_auth
def create_order(current_customer):
    """Create a Razorpay order for wallet top-up"""
    try:
        print(f"🔍 Razorpay create order - Customer ID: {current_customer['id']}")
        customer_id = current_customer["id"]
        encrypted_data = request.json.get("payload")
        if not encrypted_data:
            return jsonify({"error": "Missing encrypted payload"}), 400
        
        decrypted_data = decrypt_payload(encrypted_data)
        amount = decrypted_data.get("amount")
        customer_email = decrypted_data.get("email")
        
        print(f"🔍 Decrypted data: amount={amount}, email={customer_email}")
        
        if not amount or amount <= 0:
            return jsonify({"error": "Invalid amount"}), 400
        
        res, status = create_wallet_payment_order(amount, customer_id, customer_email)
        return jsonify(res), status
    except Exception as e:
        print(f"❌ Create Razorpay order route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@razorpay_bp.route("/verify-payment", methods=["POST"])
@require_customer_auth
def verify_payment(current_customer):
    """Verify Razorpay payment and add money to wallet"""
    try:
        customer_id = current_customer["id"]
        encrypted_data = request.json.get("payload")
        if not encrypted_data:
            return jsonify({"error": "Missing encrypted payload"}), 400
        
        decrypted_data = decrypt_payload(encrypted_data)
        payment_id = decrypted_data.get("payment_id")
        order_id = decrypted_data.get("order_id")
        signature = decrypted_data.get("signature")
        amount = decrypted_data.get("amount")
        
        if not all([payment_id, order_id, signature, amount]):
            return jsonify({"error": "Missing required payment details"}), 400
        
        # Verify payment signature
        if not verify_payment_signature(payment_id, order_id, signature):
            return jsonify({"error": "Payment verification failed"}), 400
        
        # Get payment details to confirm
        payment_res, payment_status = get_payment_details(payment_id)
        if payment_status != 200:
            return jsonify({"error": "Failed to verify payment status"}), 400
        
        # Add money to wallet
        description = f"Wallet top-up via Razorpay (Order: {order_id})"
        wallet_res, wallet_status = add_money_to_wallet(
            customer_id, 
            amount, 
            description, 
            payment_id
        )
        
        if wallet_status != 200:
            return jsonify({"error": "Failed to add money to wallet"}), 500
        
        return jsonify(wallet_res), wallet_status
    except Exception as e:
        print(f"Verify Razorpay payment route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@razorpay_bp.route("/payment-details/<payment_id>", methods=["GET"])
@require_customer_auth
def get_payment_details_route(current_customer, payment_id):
    """Get payment details from Razorpay"""
    try:
        res, status = get_payment_details(payment_id)
        return jsonify(res), status
    except Exception as e:
        print(f"Get payment details route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
