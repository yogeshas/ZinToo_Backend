# services/delivery_auth_service.py
from models.delivery_auth import DeliveryGuyAuth, DeliveryGuyOTP, generate_otp, generate_auth_token
from extensions import db
from datetime import datetime, timedelta
import hashlib
import secrets

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed):
    """Verify password against hash"""
    return hash_password(password) == hashed

def create_delivery_auth(email, phone_number, password):
    """Create new delivery guy auth account"""
    try:
        # Check if email already exists
        existing_email = DeliveryGuyAuth.query.filter_by(email=email).first()
        if existing_email:
            return {"success": False, "message": "Email already registered"}
        
        # Check if phone number already exists
        if phone_number:
            existing_phone = DeliveryGuyAuth.query.filter_by(phone_number=phone_number).first()
            if existing_phone:
                return {"success": False, "message": "Phone number already registered"}
        
        # Create auth account
        auth = DeliveryGuyAuth(
            email=email,
            phone_number=phone_number,
            password_hash=hash_password(password),
            is_onboarded=False
        )
        
        db.session.add(auth)
        db.session.commit()
        
        return {
            "success": True,
            "message": "Account created successfully",
            "auth": {
                "id": auth.id,
                "email": auth.email,
                "phone_number": auth.phone_number,
                "is_onboarded": auth.is_onboarded
            }
        }
        
    except Exception as e:
        db.session.rollback()
        print(f"Error creating delivery auth: {e}")
        return {"success": False, "message": "Failed to create account"}

def login_delivery_guy(email, password):
    """Login delivery guy with email and password"""
    try:
        # Find auth account
        auth = DeliveryGuyAuth.query.filter_by(email=email).first()
        if not auth:
            return {"success": False, "message": "Invalid credentials"}
        
        # Verify password
        if not verify_password(password, auth.password_hash):
            return {"success": False, "message": "Invalid credentials"}
        
        # Generate auth token
        token = auth.generate_auth_token()
        db.session.commit()
        
        return {
            "success": True,
            "message": "Login successful",
            "auth_token": token,
            "user": {
                "id": auth.id,
                "email": auth.email,
                "phone_number": auth.phone_number,
                "is_onboarded": auth.is_onboarded,
                "delivery_guy_id": auth.delivery_guy_id
            }
        }
        
    except Exception as e:
        print(f"Error logging in delivery guy: {e}")
        return {"success": False, "message": "Login failed"}

def send_otp(email):
    """Send OTP to email for verification"""
    try:
        # Generate OTP
        otp_code = generate_otp()
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        
        # Save OTP
        otp = DeliveryGuyOTP(
            email=email,
            otp_code=otp_code,
            expires_at=expires_at
        )
        
        db.session.add(otp)
        db.session.commit()
        
        # In production, send email here
        print(f"OTP for {email}: {otp_code}")
        
        return {
            "success": True,
            "message": "OTP sent successfully",
            "otp": otp_code  # Remove this in production
        }
        
    except Exception as e:
        db.session.rollback()
        print(f"Error sending OTP: {e}")
        return {"success": False, "message": "Failed to send OTP"}

def verify_otp(email, otp_code):
    """Verify OTP and mark as used"""
    try:
        # Find valid OTP
        otp = DeliveryGuyOTP.query.filter_by(
            email=email,
            otp_code=otp_code,
            is_used=False
        ).first()
        
        if not otp:
            return {"success": False, "message": "Invalid OTP"}
        
        if otp.is_expired():
            return {"success": False, "message": "OTP expired"}
        
        # Mark OTP as used
        otp.is_used = True
        db.session.commit()
        
        # Check if user exists
        auth = DeliveryGuyAuth.query.filter_by(email=email).first()
        
        if auth:
            # Existing user - generate auth token
            auth_token = auth.generate_auth_token()
            db.session.commit()
            
            return {
                "success": True, 
                "message": "Login successful",
                "is_new_user": False,
                "is_onboarded": auth.is_onboarded,
                "auth_token": auth_token,
                "user": {
                    "id": auth.id,
                    "email": auth.email,
                    "phone_number": auth.phone_number,
                    "is_verified": True,
                    "is_onboarded": auth.is_onboarded,
                    "delivery_guy_id": auth.delivery_guy_id
                }
            }
        else:
            # New user - create account
            auth = DeliveryGuyAuth(
                email=email,
                phone_number="",  # Will be filled during onboarding
                password_hash="",  # No password for OTP-based auth
                is_onboarded=False
            )
            
            db.session.add(auth)
            db.session.commit()
            
            # Generate auth token
            auth_token = auth.generate_auth_token()
            db.session.commit()
            
            return {
                "success": True, 
                "message": "New user created",
                "is_new_user": True,
                "is_onboarded": False,
                "auth_token": auth_token,
                "user": {
                    "id": auth.id,
                    "email": auth.email,
                    "phone_number": "",
                    "is_verified": True,
                    "is_onboarded": False,
                    "delivery_guy_id": None
                }
            }
        
    except Exception as e:
        print(f"Error verifying OTP: {e}")
        return {"success": False, "message": "OTP verification failed"}

def reset_password(email, new_password):
    """Reset password using email"""
    try:
        # Find auth account
        auth = DeliveryGuyAuth.query.filter_by(email=email).first()
        if not auth:
            return {"success": False, "message": "Email not found"}
        
        # Update password
        auth.password_hash = hash_password(new_password)
        auth.updated_at = datetime.utcnow()
        db.session.commit()
        
        return {"success": True, "message": "Password reset successfully"}
        
    except Exception as e:
        print(f"Error resetting password: {e}")
        return {"success": False, "message": "Password reset failed"}

def create_delivery_auth_with_phone(phone_number, email=None):
    """Create delivery auth account with phone number (for mobile app)"""
    try:
        # Check if phone number already exists
        existing_phone = DeliveryGuyAuth.query.filter_by(phone_number=phone_number).first()
        if existing_phone:
            return {"success": False, "message": "Phone number already registered"}
        
        # Create auth account
        auth = DeliveryGuyAuth(
            phone_number=phone_number,
            email=email,
            password_hash="",  # No password for phone-based auth
            is_onboarded=False
        )
        
        db.session.add(auth)
        db.session.commit()
        
        return {
            "success": True,
            "message": "Account created successfully",
            "auth": {
                "id": auth.id,
                "phone_number": auth.phone_number,
                "email": auth.email,
                "is_onboarded": auth.is_onboarded
            }
        }
        
    except Exception as e:
        db.session.rollback()
        print(f"Error creating delivery auth with phone: {e}")
        return {"success": False, "message": "Failed to create account"}

def verify_auth_token(token):
    """Verify auth token and return user info"""
    try:
        auth = DeliveryGuyAuth.query.filter_by(auth_token=token).first()
        if not auth:
            return {"success": False, "message": "Invalid token"}
        
        if not auth.is_token_valid():
            return {"success": False, "message": "Token expired"}
        
        return {
            "success": True,
            "user": {
                "id": auth.id,
                "email": auth.email,
                "phone_number": auth.phone_number,
                "is_onboarded": auth.is_onboarded,
                "delivery_guy_id": auth.delivery_guy_id
            }
        }
        
    except Exception as e:
        print(f"Error verifying auth token: {e}")
        return {"success": False, "message": "Token verification failed"}

def logout_delivery_guy(token):
    """Logout delivery guy by invalidating token"""
    try:
        auth = DeliveryGuyAuth.query.filter_by(auth_token=token).first()
        if not auth:
            return {"success": False, "message": "Invalid token"}
        
        # Clear token
        auth.auth_token = None
        auth.token_expires_at = None
        db.session.commit()
        
        return {"success": True, "message": "Logged out successfully"}
        
    except Exception as e:
        print(f"Error logging out delivery guy: {e}")
        return {"success": False, "message": "Logout failed"}

def update_delivery_guy_id(auth_id, onboarding_id):
    """Update delivery_guy_id to reference onboarding record"""
    try:
        auth = DeliveryGuyAuth.query.get(auth_id)
        if not auth:
            return {"success": False, "message": "Auth account not found"}
        
        auth.delivery_guy_id = onboarding_id
        auth.updated_at = datetime.utcnow()
        db.session.commit()
        
        return {"success": True, "message": "Delivery guy ID updated successfully"}
        
    except Exception as e:
        print(f"Error updating delivery guy ID: {e}")
        return {"success": False, "message": "Failed to update delivery guy ID"}
