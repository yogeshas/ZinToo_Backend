# models/customer.py
from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from passlib.context import CryptContext
import os

# Fernet removed for customer fields. We store UTF-8 bytes for simple fields and hash passwords with bcrypt.

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)

class Customer(db.Model):
    __tablename__ = "customer"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    customerid = db.Column(db.String(64), unique=True)
    status = db.Column(db.String(32))
    phone_number_enc = db.Column("phone_number", db.LargeBinary)
    location_enc = db.Column("location", db.LargeBinary)
    referral_code_enc = db.Column("referral_code", db.LargeBinary)
    referral_count = db.Column(db.Integer, default=0)
    referred_by_id = db.Column(db.Integer, db.ForeignKey("customer.id"), nullable=True)
    total_referral_earnings = db.Column(db.Float, default=0.0)

    # new fields for social login
    provider = db.Column(db.String(50), nullable=True)    # google, apple, facebook
    provider_id = db.Column(db.String(200), nullable=True)  # unique provider id
    google_id = db.Column(db.String(200), nullable=True)  # Google OAuth ID
    name = db.Column(db.String(200), nullable=True)  # Full name from Google

    # Relationships
    referred_by = db.relationship("Customer", remote_side=[id], backref="referrals")

    def set_password(self, password: str):
        # Use same hashing strategy as Admin (bcrypt via passlib)
        self.password_hash = pwd_context.hash(password)
    def check_password(self, password: str) -> bool:
        # Prefer bcrypt (passlib) like Admin
        try:
            if pwd_context.verify(password, self.password_hash):
                return True
        except Exception:
            pass
        # Backward compatibility: accept older werkzeug hashes
        try:
            return check_password_hash(self.password_hash, password)
        except Exception:
            return False

    def set_phone_number(self, phone: str):
        if phone is None or phone == "":
            self.phone_number_enc = None
        else:
            self.phone_number_enc = str(phone).encode('utf-8')
        print(f"[CUSTOMER MODEL] Set phone_number: '{phone}' -> stored: {self.phone_number_enc}")
        
    def get_phone_number(self):
        try:
            if self.phone_number_enc is None:
                return None
            return self.phone_number_enc.decode('utf-8')
        except Exception as e:
            print(f"[CUSTOMER MODEL] Error getting phone_number: {e}")
            return None

    def set_location(self, location: str):
        if location is None or location == "":
            self.location_enc = None
        else:
            self.location_enc = str(location).encode('utf-8')
        print(f"[CUSTOMER MODEL] Set location: '{location}' -> stored: {self.location_enc}")
        
    def get_location(self):
        try:
            if self.location_enc is None:
                return None
            return self.location_enc.decode('utf-8')
        except Exception as e:
            print(f"[CUSTOMER MODEL] Error getting location: {e}")
            return None

    def set_referral_code(self, code: str):
        self.referral_code_enc = code.encode() if code is not None else None
    def get_referral_code(self):
        try:
            return self.referral_code_enc.decode() if self.referral_code_enc else None
        except Exception:
            return None

    def as_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "customerid": self.customerid,
            "status": self.status,
            "phone_number": self.get_phone_number(),
            "location": self.get_location(),
            "referral_code": self.get_referral_code(),
            "referral_count": self.referral_count,
            "referred_by_id": self.referred_by_id,
            "total_referral_earnings": self.total_referral_earnings,
            "provider": self.provider,
            "provider_id": self.provider_id,
            "google_id": self.google_id,
            "name": self.name,
        }
