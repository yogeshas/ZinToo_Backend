# services/forgot_password_service.py
import random
import string
import uuid
import threading
from datetime import datetime, timedelta
from models.otp import OTP
from models.admin import Admin
from extensions import db, mail
from flask_mail import Message
from flask import current_app
from passlib.context import CryptContext

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def send_email_async(app, msg):
    """Send email in a separate thread to avoid blocking the main request"""
    try:
        # Use the actual app object passed from the request thread
        with app.app_context():
            mail.send(msg)
            print(f"✅ Password reset email sent successfully to {msg.recipients[0]}")
    except Exception as e:
        print(f"❌ Password reset email sending error: {str(e)}")

def send_password_reset_otp(email):
    """Send password reset OTP to admin email"""
    try:
        # Check if admin exists
        admin = Admin.query.filter_by(email=email, status="active").first()
        if not admin:
            return {"error": "Admin account not found or inactive"}, 404

        # Generate 6-digit OTP
        otp = "".join(random.choices(string.digits, k=6))
        token_uuid = str(uuid.uuid4())
        
        # Set expiration (10 minutes for password reset)
        expires_at = datetime.utcnow() + timedelta(minutes=10)

        # Create OTP entry and override expiry to 10 minutes
        otp_entry = OTP(email=email, otp_code=otp, token_uuid=token_uuid)
        otp_entry.expires_at = expires_at
        
        db.session.add(otp_entry)
        db.session.commit()

        # Send email in background thread
        msg = Message("ZINTOO Admin Password Reset", recipients=[email])
        msg.body = f"Your password reset OTP code is {otp}. It will expire in 10 minutes. Do not share this code with anyone."
        msg.html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #7c3aed;">ZINTOO Admin Password Reset</h2>
            <p>You requested a password reset. Your verification code is:</p>
            <div style="background-color: #f3f4f6; padding: 20px; text-align: center; border-radius: 8px; margin: 20px 0;">
                <h1 style="color: #7c3aed; font-size: 32px; margin: 0; letter-spacing: 4px;">{otp}</h1>
            </div>
            <p>This code will expire in 10 minutes.</p>
            <p style="color: #6b7280; font-size: 14px;">
                If you didn't request this password reset, please ignore this email and ensure your account is secure.
            </p>
            <hr style="margin: 20px 0; border: none; border-top: 1px solid #e5e7eb;">
            <p style="color: #6b7280; font-size: 12px;">
                This is an automated message from ZINTOO Admin System.
            </p>
        </div>
        """
        
        # Start email sending in background thread
        app = current_app._get_current_object()
        email_thread = threading.Thread(target=send_email_async, args=(app, msg,))
        email_thread.daemon = True
        email_thread.start()

        return {
            "success": True,
            "message": "Password reset OTP sent successfully",
            "token_uuid": token_uuid,
            "email": email
        }, 200

    except Exception as e:
        print(f"❌ Send password reset OTP error: {str(e)}")
        db.session.rollback()
        return {"error": "Failed to send password reset OTP"}, 500

def verify_password_reset_otp(email, otp):
    """Verify password reset OTP"""
    try:
        # Find the most recent active OTP for this email (no purpose column)
        otp_entry = OTP.query.filter_by(
            email=email,
            verified=False
        ).filter(
            OTP.expires_at > datetime.utcnow()
        ).order_by(OTP.id.desc()).first()

        if not otp_entry:
            return {"error": "Invalid or expired OTP"}, 400
        
        if otp_entry.otp_code != otp:
            return {"error": "Invalid OTP code"}, 400

        # Mark as verified
        otp_entry.verified = True
        db.session.commit()

        return {
            "success": True,
            "message": "OTP verified successfully",
            "email": email
        }, 200

    except Exception as e:
        print(f"❌ Verify password reset OTP error: {str(e)}")
        db.session.rollback()
        return {"error": "Failed to verify OTP"}, 500

def reset_admin_password(email, otp, new_password):
    """Reset admin password after OTP verification"""
    try:
        # Verify most recent verified OTP (no purpose column)
        otp_entry = OTP.query.filter_by(
            email=email,
            verified=True
        ).filter(
            OTP.expires_at > datetime.utcnow()
        ).order_by(OTP.id.desc()).first()

        if not otp_entry:
            return {"error": "Invalid or expired OTP"}, 400

        # Find admin
        admin = Admin.query.filter_by(email=email, status="active").first()
        if not admin:
            return {"error": "Admin account not found"}, 404

        # Validate new password
        if len(new_password) < 8:
            return {"error": "Password must be at least 8 characters long"}, 400

        # Hash and set new password
        admin.set_password(new_password)
        
        # Mark all OTPs for this email as used (security measure)
        OTP.query.filter_by(email=email).update({
            "verified": True
        })
        
        db.session.commit()

        # Send confirmation email
        msg = Message("ZINTOO Admin Password Changed", recipients=[email])
        msg.body = "Your ZINTOO admin password has been successfully changed. If you didn't make this change, please contact support immediately."
        msg.html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #7c3aed;">ZINTOO Admin Password Changed</h2>
            <div style="background-color: #f0f9ff; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #3b82f6;">
                <p style="margin: 0; color: #1e40af;">✅ Your password has been successfully changed.</p>
            </div>
            <p>Your ZINTOO admin account password was updated at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC.</p>
            <p style="color: #6b7280; font-size: 14px;">
                If you didn't make this change, please contact support immediately to secure your account.
            </p>
            <hr style="margin: 20px 0; border: none; border-top: 1px solid #e5e7eb;">
            <p style="color: #6b7280; font-size: 12px;">
                This is an automated message from ZINTOO Admin System.
            </p>
        </div>
        """
        
        # Send confirmation email in background
        app = current_app._get_current_object()
        email_thread = threading.Thread(target=send_email_async, args=(app, msg,))
        email_thread.daemon = True
        email_thread.start()

        return {
            "success": True,
            "message": "Password reset successfully",
            "email": email
        }, 200

    except Exception as e:
        print(f"❌ Reset admin password error: {str(e)}")
        db.session.rollback()
        return {"error": "Failed to reset password"}, 500

def resend_password_reset_otp(email):
    """Resend password reset OTP"""
    try:
        # Check if admin exists
        admin = Admin.query.filter_by(email=email, status="active").first()
        if not admin:
            return {"error": "Admin account not found or inactive"}, 404

        # Invalidate any existing unverified OTPs for this email (no purpose column)
        OTP.query.filter_by(
            email=email,
            verified=False
        ).update({
            "verified": True  # Mark as used to prevent conflicts
        })
        
        db.session.commit()

        # Send new OTP
        return send_password_reset_otp(email)

    except Exception as e:
        print(f"❌ Resend password reset OTP error: {str(e)}")
        db.session.rollback()
        return {"error": "Failed to resend OTP"}, 500

def cleanup_expired_password_reset_otps():
    """Clean up expired OTPs (no purpose column)"""
    try:
        expired_otps = OTP.query.filter(
            OTP.expires_at < datetime.utcnow()
        ).all()
        
        for otp in expired_otps:
            db.session.delete(otp)
        
        db.session.commit()
        if expired_otps:
            print(f"🧹 Cleaned up {len(expired_otps)} expired OTPs")
            
    except Exception as e:
        print(f"❌ Password reset OTP cleanup error: {str(e)}")
        db.session.rollback() 
