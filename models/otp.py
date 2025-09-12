from extensions import db
import datetime
import uuid

class OTP(db.Model):
    __tablename__ = "otp"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False, index=True)
    otp_code = db.Column(db.String(6), nullable=False)
    token_uuid = db.Column(db.String(64), nullable=False, unique=True)  # link with JWT uuid
    expires_at = db.Column(db.DateTime, nullable=False)
    verified = db.Column(db.Boolean, default=False)

    def __init__(self, email, otp_code, token_uuid):
        self.email = email
        self.otp_code = otp_code
        self.token_uuid = token_uuid
        self.expires_at = datetime.datetime.utcnow() + datetime.timedelta(minutes=5)  # 5 min expiry

    def as_dict(self):
        return {
            "email": self.email,
            "otp_code": self.otp_code,
            "token_uuid": self.token_uuid,
            "expires_at": self.expires_at.isoformat(),
            "verified": self.verified
        }
