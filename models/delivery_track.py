from extensions import db
from datetime import datetime

class DeliveryTrack(db.Model):
    __tablename__ = "delivery_track"
    
    id = db.Column(db.Integer, primary_key=True)
    delivery_guy_id = db.Column(db.Integer, db.ForeignKey("delivery_onboarding.id"), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=True)
    exchange_id = db.Column(db.Integer, db.ForeignKey("exchange.id"), nullable=True)
    status = db.Column(db.String(20), nullable=False)  # approved, rejected, delivered
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    delivery_guy = db.relationship("DeliveryOnboarding", backref="delivery_tracks")
    order = db.relationship("Order", backref="delivery_tracks")
    exchange = db.relationship("Exchange", backref="delivery_tracks")
    
    def to_dict(self):
        return {
            "id": self.id,
            "delivery_guy_id": self.delivery_guy_id,
            "order_id": self.order_id,
            "exchange_id": self.exchange_id,
            "status": self.status,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f"<DeliveryTrack {self.id} - Delivery Guy: {self.delivery_guy_id}, Status: {self.status}>"
