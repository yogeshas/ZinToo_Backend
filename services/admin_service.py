import jwt
import datetime
from flask import current_app
from models.admin import Admin
from services.otp_service import generate_otp, verify_otp, get_active_otp_by_email
from extensions import db

def login_user(data):
    email = data.get("email")
    password = data.get("password")
    
    print(f"[DEBUG] Login attempt for email: {email}")
    
    admin = Admin.query.filter_by(email=email).first()
    if not admin:
        print(f"[DEBUG] Admin not found for email: {email}")
        return {"error": "Invalid credentials"}, 401
    
    print(f"[DEBUG] Admin found: {admin.username} ({admin.email})")
    print(f"[DEBUG] Checking password...")
    
    if not admin.check_password(password):
        print(f"[DEBUG] Password verification failed for: {email}")
        return {"error": "Invalid credentials"}, 401
    
    print(f"[DEBUG] Password verified successfully!")
    
    # Generate OTP for additional verification
    otp_result, otp_status = generate_otp(email)
    if otp_status != 200:
        return {"error": "Failed to send OTP"}, 500
    
    return {
        "message": "Password verified. OTP sent to your email.",
        "requires_otp": True,
        "token_uuid": otp_result["token_uuid"],
        "email": email
    }, 200

def verify_admin_otp(token_uuid, otp_code):
    """Verify OTP and return admin token if successful"""
    result, status = verify_otp(token_uuid, otp_code)
    
    if status != 200:
        return result, status
    
    # Get admin details from the email in OTP
    admin = Admin.query.filter_by(email=result["email"]).first()
    if not admin:
        return {"error": "Admin not found"}, 404
    
    # Generate JWT token for admin
    secret = current_app.config.get("SECRET_KEY")
    if not secret:
        raise RuntimeError("SECRET_KEY not configured")
    
    payload = {
        "id": admin.id,
        "email": admin.email,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=12)
    }
    
    token = jwt.encode(payload, secret, algorithm="HS256")
    
    return {
        "token": token,
        "admin": admin.as_dict(),
        "message": "Login successful"
    }, 200

def get_admin_by_token(token):
    """Get admin details from JWT token"""
    try:
        secret = current_app.config.get("SECRET_KEY")
        if not secret:
            raise RuntimeError("SECRET_KEY not configured")
        
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        admin = Admin.query.get(payload["id"])
        
        if not admin:
            return None
        
        return admin
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def change_admin_password(token: str, old_password: str, new_password: str):
    """Change admin password after verifying JWT and current password."""
    admin = get_admin_by_token(token)
    if not admin:
        return {"error": "Invalid or expired token"}, 401

    if not admin.check_password(old_password):
        return {"error": "Current password is incorrect"}, 400

    if not new_password or len(new_password) < 6:
        return {"error": "New password must be at least 6 characters"}, 400

    admin.set_password(new_password)
    db.session.commit()
    return {"message": "Password updated successfully"}, 200


def logout_admin(token: str):
    """Stateless logout. Optionally validate token; frontend should clear it."""
    # Optionally validate token to ensure it's a well-formed/known user
    admin = get_admin_by_token(token)
    if not admin:
        # Even if invalid, respond success to avoid leaking token validity
        return {"message": "Logged out"}, 200
    return {"message": "Logged out"}, 200
