from extensions import db
from datetime import datetime

class Payout(db.Model):
    __tablename__ = "payout"
    id = db.Column(db.Integer, primary_key=True)
    delivery_user_id = db.Column(db.Integer, db.ForeignKey("delivery_onboarding.id"), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(50), default="pending")
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    processed_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    delivery_user = db.relationship("DeliveryOnboarding", backref="payouts")

    def to_dict(self):
        return {
            "id": self.id,
            "delivery_user_id": self.delivery_user_id,
            "amount": float(self.amount) if self.amount else None,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None
        }

    def __repr__(self):
        return f"<Payout {self.id} - User: {self.delivery_user_id}, Amount: {self.amount}>"
