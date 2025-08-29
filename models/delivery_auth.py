# models/delivery_auth.py
from extensions import db
from datetime import datetime, timedelta
import secrets

class DeliveryGuyAuth(db.Model):
    __tablename__ = "delivery_guy_auth"
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone_number = db.Column(db.String(20), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_onboarded = db.Column(db.Boolean, default=False)
    delivery_guy_id = db.Column(db.Integer, nullable=True)  # This will now reference onboarding_id
    auth_token = db.Column(db.String(255), unique=True, nullable=True)
    token_expires_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<DeliveryGuyAuth {self.email}>"

    def generate_auth_token(self):
        """Generate a new auth token"""
        self.auth_token = secrets.token_urlsafe(32)
        self.token_expires_at = datetime.utcnow() + timedelta(days=30)
        return self.auth_token

    def is_token_valid(self):
        """Check if auth token is still valid"""
        if not self.auth_token or not self.token_expires_at:
            return False
        return datetime.utcnow() < self.token_expires_at

class DeliveryGuyOTP(db.Model):
    __tablename__ = "delivery_guy_otp"
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    otp_code = db.Column(db.String(6), nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<DeliveryGuyOTP {self.email}>"

    def is_expired(self):
        """Check if OTP is expired"""
        return datetime.utcnow() > self.expires_at

def generate_otp():
    """Generate a 6-digit OTP"""
    import random
    return str(random.randint(100000, 999999))

def generate_auth_token():
    """Generate a secure auth token"""
    return secrets.token_urlsafe(32)
