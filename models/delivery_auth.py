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
    
    # Push notification fields
    device_token = db.Column(db.String(500), nullable=True)  # FCM device token
    platform = db.Column(db.String(20), nullable=True)  # android, ios
    sns_endpoint_arn = db.Column(db.String(500), nullable=True)  # AWS SNS endpoint ARN
    is_notifications_enabled = db.Column(db.Boolean, default=True)
    
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

    def update_device_token(self, device_token, platform):
        """Update device token and platform for push notifications"""
        self.device_token = device_token
        self.platform = platform
        self.updated_at = datetime.utcnow()
        return True

    def has_valid_device_token(self):
        """Check if user has a valid device token for notifications"""
        return bool(self.device_token and self.platform and self.is_notifications_enabled)

    def disable_notifications(self):
        """Disable push notifications for this user"""
        self.is_notifications_enabled = False
        self.updated_at = datetime.utcnow()
        return True

    def enable_notifications(self):
        """Enable push notifications for this user"""
        self.is_notifications_enabled = True
        self.updated_at = datetime.utcnow()
        return True

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
