import random
import string
import uuid
import threading
from models.otp import OTP
from extensions import db, mail
from flask_mail import Message
import datetime
from flask import current_app

def send_email_async(app, msg):
    """Send email in a separate thread to avoid blocking the main request"""
    try:
        # Use the actual app object passed from the request thread
        with app.app_context():
            mail.send(msg)
            print(f"✅ Email sent successfully to {msg.recipients[0]}")
    except Exception as e:
        print(f"❌ Email sending error: {str(e)}")

def generate_otp(email):
    otp = "".join(random.choices(string.digits, k=6))
    token_uuid = str(uuid.uuid4())

    # Create OTP entry
    otp_entry = OTP(email=email, otp_code=otp, token_uuid=token_uuid)
    db.session.add(otp_entry)
    db.session.commit()

    # Send email in background thread
    msg = Message("ZINTOO Admin OTP Verification", recipients=[email])
    msg.body = f"Your admin login OTP code is {otp}. It will expire in 5 minutes. Do not share this code with anyone."
    msg.html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #7c3aed;">ZINTOO Admin Login</h2>
        <p>Your verification code is:</p>
        <div style="background-color: #f3f4f6; padding: 20px; text-align: center; border-radius: 8px; margin: 20px 0;">
            <h1 style="color: #7c3aed; font-size: 32px; margin: 0; letter-spacing: 4px;">{otp}</h1>
        </div>
        <p>This code will expire in 5 minutes.</p>
        <p style="color: #6b7280; font-size: 14px;">If you didn't request this code, please ignore this email.</p>
    </div>
    """
    
    # Start email sending in background thread
    app = current_app._get_current_object()
    email_thread = threading.Thread(target=send_email_async, args=(app, msg,))
    email_thread.daemon = True
    email_thread.start()

    return {"token_uuid": token_uuid, "email": email, "message": "OTP sent successfully"}, 200

def verify_otp(token_uuid, otp_code):
    otp_entry = OTP.query.filter_by(token_uuid=token_uuid).first()

    if not otp_entry:
        return {"error": "Invalid OTP request"}, 400
    
    if otp_entry.verified:
        return {"error": "OTP already used"}, 400
    
    if datetime.datetime.utcnow() > otp_entry.expires_at:
        return {"error": "OTP expired"}, 400
    
    if otp_entry.otp_code != otp_code:
        return {"error": "Invalid OTP"}, 400

    # Mark as verified
    otp_entry.verified = True
    db.session.commit()

    return {"message": "OTP verified successfully", "email": otp_entry.email}, 200

def get_active_otp_by_email(email):
    """Get the most recent active OTP for an email"""
    otp_entry = OTP.query.filter_by(
        email=email, 
        verified=False
    ).filter(
        OTP.expires_at > datetime.datetime.utcnow()
    ).order_by(OTP.id.desc()).first()
    
    return otp_entry

def cleanup_expired_otps():
    """Clean up expired OTPs in background"""
    try:
        with current_app.app_context():
            expired_otps = OTP.query.filter(
                OTP.expires_at < datetime.datetime.utcnow()
            ).all()
            
            for otp in expired_otps:
                db.session.delete(otp)
            
            db.session.commit()
            print(f"Cleaned up {len(expired_otps)} expired OTPs")
    except Exception as e:
        print(f"OTP cleanup error: {str(e)}")
