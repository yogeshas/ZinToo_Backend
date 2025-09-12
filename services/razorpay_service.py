# services/razorpay_service.py
import razorpay
import os
from datetime import datetime
from utils.crypto import encrypt_payload, decrypt_payload

# Initialize Razorpay client
# For testing, we'll use a mock client if no proper keys are provided
razorpay_key_id = os.getenv("RAZORPAY_KEY_ID", "rzp_test_WjZgY0Pdzmhm88")
razorpay_key_secret = os.getenv("RAZORPAY_KEY_SECRET", "test_secret_key")

if razorpay_key_secret == "test_secret_key" or razorpay_key_secret == "your_razorpay_secret_key":
    print("⚠️ Using test mode - Razorpay integration will be simulated")
    client = None
else:
    client = razorpay.Client(auth=(razorpay_key_id, razorpay_key_secret))

def create_wallet_payment_order(amount: float, customer_id: int, customer_email: str = None):
    """Create a Razorpay order for wallet top-up"""
    try:
        # Convert amount to paise (Razorpay expects amount in smallest currency unit)
        amount_paise = int(amount * 100)
        
        # Create order data
        order_data = {
            "amount": amount_paise,
            "currency": "INR",
            "receipt": f"wallet_topup_{customer_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "notes": {
                "customer_id": str(customer_id),
                "purpose": "wallet_topup"
            }
        }
        
        # Check if we're in test mode
        if client is None:
            # Test mode - create a mock order
            mock_order_id = f"order_test_{customer_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            print(f"🧪 Test mode: Created mock order {mock_order_id}")
            
            # Encrypt the response
            encrypted_data = encrypt_payload({
                "success": True,
                "order_id": mock_order_id,
                "amount": amount,
                "amount_paise": amount_paise,
                "currency": "INR",
                "receipt": order_data["receipt"],
                "key_id": razorpay_key_id
            })
            
            return {
                "success": True,
                "encrypted_data": encrypted_data,
                "message": "Test payment order created successfully"
            }, 200
        else:
            # Real mode - create order with Razorpay
            order = client.order.create(data=order_data)
            
            # Encrypt the response
            encrypted_data = encrypt_payload({
                "success": True,
                "order_id": order["id"],
                "amount": amount,
                "amount_paise": amount_paise,
                "currency": "INR",
                "receipt": order["receipt"],
                "key_id": razorpay_key_id
            })
            
            return {
                "success": True,
                "encrypted_data": encrypted_data,
                "message": "Payment order created successfully"
            }, 200
        
    except Exception as e:
        print(f"❌ Create wallet payment order error: {str(e)}")
        return {"error": "Failed to create payment order"}, 500

def verify_payment_signature(payment_id: str, order_id: str, signature: str):
    """Verify Razorpay payment signature"""
    try:
        # Check if we're in test mode
        if client is None:
            # Test mode - always return True for test orders
            if order_id.startswith("order_test_"):
                print(f"🧪 Test mode: Verified mock payment {payment_id}")
                return True
            else:
                print(f"❌ Test mode: Invalid test order ID {order_id}")
                return False
        else:
            # Real mode - verify with Razorpay
            client.utility.verify_payment_signature({
                "razorpay_payment_id": payment_id,
                "razorpay_order_id": order_id,
                "razorpay_signature": signature
            })
            return True
    except Exception as e:
        print(f"❌ Payment signature verification failed: {str(e)}")
        return False

def get_payment_details(payment_id: str):
    """Get payment details from Razorpay"""
    try:
        # Check if we're in test mode
        if client is None:
            # Test mode - return mock payment details
            if payment_id.startswith("pay_test_"):
                print(f"🧪 Test mode: Retrieved mock payment details {payment_id}")
                
                encrypted_data = encrypt_payload({
                    "success": True,
                    "payment_id": payment_id,
                    "order_id": f"order_test_{payment_id.split('_')[-1]}",
                    "amount": 1000.0,  # Mock amount
                    "currency": "INR",
                    "status": "captured",
                    "method": "test",
                    "created_at": datetime.now().isoformat(),
                    "captured_at": datetime.now().isoformat()
                })
                
                return {
                    "success": True,
                    "encrypted_data": encrypted_data,
                    "message": "Test payment details retrieved successfully"
                }, 200
            else:
                return {"error": "Invalid test payment ID"}, 400
        else:
            # Real mode - get details from Razorpay
            payment = client.payment.fetch(payment_id)
            
            # Encrypt the response
            encrypted_data = encrypt_payload({
                "success": True,
                "payment_id": payment["id"],
                "order_id": payment["order_id"],
                "amount": payment["amount"] / 100,  # Convert from paise to rupees
                "currency": payment["currency"],
                "status": payment["status"],
                "method": payment["method"],
                "created_at": payment["created_at"],
                "captured_at": payment.get("captured_at")
            })
            
            return {
                "success": True,
                "encrypted_data": encrypted_data,
                "message": "Payment details retrieved successfully"
            }, 200
        
    except Exception as e:
        print(f"❌ Get payment details error: {str(e)}")
        return {"error": "Failed to get payment details"}, 500
