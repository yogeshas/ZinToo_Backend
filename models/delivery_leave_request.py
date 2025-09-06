from extensions import db
from datetime import datetime

class DeliveryLeaveRequest(db.Model):
    __tablename__ = "delivery_leave_request"
    
    id = db.Column(db.Integer, primary_key=True)
    delivery_guy_id = db.Column(db.Integer, db.ForeignKey("delivery_onboarding.id"), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default="pending", nullable=False)  # pending, approved, rejected
    admin_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    reviewed_by = db.Column(db.Integer, db.ForeignKey("admin.id"), nullable=True)
    
    # Relationships
    delivery_guy = db.relationship("DeliveryOnboarding", backref="leave_requests")
    reviewer = db.relationship("Admin", backref="reviewed_leave_requests")
    
    def __repr__(self):
        return f"<DeliveryLeaveRequest {self.id} - Delivery Guy: {self.delivery_guy_id}, Status: {self.status}>"
    
    def as_dict(self):
        return {
            "id": self.id,
            "delivery_guy_id": self.delivery_guy_id,
            "start_date": self.start_date.isoformat() if self.start_date and hasattr(self.start_date, 'isoformat') else str(self.start_date) if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date and hasattr(self.end_date, 'isoformat') else str(self.end_date) if self.end_date else None,
            "reason": self.reason,
            "status": self.status,
            "admin_notes": self.admin_notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "reviewed_by": self.reviewed_by,
            "delivery_guy_name": f"{self.delivery_guy.first_name or ''} {self.delivery_guy.last_name or ''}".strip() if self.delivery_guy else None,
            "delivery_guy_email": self.delivery_guy.email if self.delivery_guy else None,
            "reviewer_name": self.reviewer.username if self.reviewer else None,
        }
