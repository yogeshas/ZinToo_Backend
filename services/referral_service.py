# services/referral_service.py
from models.customer import Customer
from services.wallet_service import add_money_to_wallet
from extensions import db
from utils.crypto import encrypt_payload, decrypt_payload
from datetime import datetime
import re

def generate_referral_code(username: str) -> str:
    """Generate unique referral code based on username"""
    try:
        # Get first 3 letters of username (uppercase)
        name_part = username[:3].upper()
        
        # Find the highest existing number for this name part
        existing_codes = Customer.query.filter(
            Customer.referral_code_enc.isnot(None)
        ).all()
        
        max_number = 0
        for customer in existing_codes:
            code = customer.get_referral_code()
            if code and code.startswith(name_part):
                # Extract number from code (e.g., "JOH001" -> 1)
                number_part = code[3:]
                if number_part.isdigit():
                    max_number = max(max_number, int(number_part))
        
        # Generate next number
        next_number = max_number + 1
        
        # Format as 3-digit number with leading zeros
        number_part = f"{next_number:03d}"
        
        # Combine name part and number part
        referral_code = f"{name_part}{number_part}"
        
        print(f"🔍 Generated referral code: {referral_code} for user: {username}")
        return referral_code
        
    except Exception as e:
        print(f"❌ Error generating referral code: {str(e)}")
        # Fallback: use timestamp-based code
        timestamp = datetime.now().strftime("%H%M%S")
        return f"REF{timestamp}"

def validate_referral_code(referral_code: str) -> bool:
    """Validate referral code format"""
    if not referral_code:
        return False
    
    # Check if code exists in database
    existing_customer = Customer.query.filter(
        Customer.referral_code_enc.isnot(None)
    ).all()
    
    for customer in existing_customer:
        if customer.get_referral_code() == referral_code:
            return True
    
    return False

def get_customer_by_referral_code(referral_code: str) -> Customer:
    """Get customer by referral code"""
    try:
        existing_customers = Customer.query.filter(
            Customer.referral_code_enc.isnot(None)
        ).all()
        
        for customer in existing_customers:
            if customer.get_referral_code() == referral_code:
                return customer
        
        return None
    except Exception as e:
        print(f"❌ Error getting customer by referral code: {str(e)}")
        return None

def process_referral_signup(new_customer_id: int, referral_code: str = None):
    """Process referral when new customer signs up"""
    try:
        if not referral_code:
            print(f"🔍 No referral code provided for customer {new_customer_id}")
            return
        
        # Get the referrer (person who provided the code)
        referrer = get_customer_by_referral_code(referral_code)
        if not referrer:
            print(f"❌ Invalid referral code: {referral_code}")
            return
        
        # Get the new customer
        new_customer = Customer.query.get(new_customer_id)
        if not new_customer:
            print(f"❌ New customer not found: {new_customer_id}")
            return
        
        # Check if customer is referring themselves
        if referrer.id == new_customer.id:
            print(f"❌ Customer cannot refer themselves")
            return
        
        # Check if customer was already referred
        if new_customer.referred_by_id:
            print(f"❌ Customer already referred by someone else")
            return
        
        print(f"🔍 Processing referral: {referrer.username} -> {new_customer.username}")
        
        # Update referral relationship
        new_customer.referred_by_id = referrer.id
        referrer.referral_count += 1
        
        # Give rewards to both parties
        reward_amount = 150.0
        
        # Reward the referrer
        referrer_reward_result, referrer_status = add_money_to_wallet(
            referrer.id,
            reward_amount,
            f"Referral reward for {new_customer.username}",
            f"REF-{new_customer.id}"
        )
        
        if referrer_status == 200:
            referrer.total_referral_earnings += reward_amount
            print(f"✅ Referrer {referrer.username} received ₹{reward_amount}")
        else:
            print(f"❌ Failed to reward referrer: {referrer_reward_result}")
        
        # Reward the new customer
        new_customer_reward_result, new_customer_status = add_money_to_wallet(
            new_customer.id,
            reward_amount,
            f"Referral bonus from {referrer.username}",
            f"REF-{referrer.id}"
        )
        
        if new_customer_status == 200:
            print(f"✅ New customer {new_customer.username} received ₹{reward_amount}")
        else:
            print(f"❌ Failed to reward new customer: {new_customer_reward_result}")
        
        # Commit all changes
        db.session.commit()
        print(f"✅ Referral processed successfully")
        
    except Exception as e:
        print(f"❌ Error processing referral: {str(e)}")
        db.session.rollback()

def get_referral_stats(customer_id: int):
    """Get referral statistics for a customer"""
    try:
        customer = Customer.query.get(customer_id)
        if not customer:
            return {"error": "Customer not found"}, 404
        
        # Get referrals made by this customer
        referrals = Customer.query.filter_by(referred_by_id=customer_id).all()
        
        # Get referrer info
        referrer = None
        if customer.referred_by_id:
            referrer = Customer.query.get(customer.referred_by_id)
        
        stats = {
            "referral_code": customer.get_referral_code(),
            "referral_count": customer.referral_count,
            "total_earnings": customer.total_referral_earnings,
            "referrals": [
                {
                    "id": ref.id,
                    "username": ref.username,
                    "email": ref.email,
                    "joined_date": ref.created_at.isoformat() if hasattr(ref, 'created_at') else None
                } for ref in referrals
            ],
            "referred_by": {
                "id": referrer.id,
                "username": referrer.username,
                "email": referrer.email
            } if referrer else None
        }
        
        # Encrypt the response
        encrypted_data = encrypt_payload({
            "success": True,
            "stats": stats
        })
        
        return {
            "success": True,
            "encrypted_data": encrypted_data,
            "message": "Referral stats retrieved successfully"
        }, 200
        
    except Exception as e:
        print(f"❌ Error getting referral stats: {str(e)}")
        return {"error": "Failed to get referral stats"}, 500
