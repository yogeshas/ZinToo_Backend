from extensions import db
from datetime import datetime

def get_current_time():
    return datetime.utcnow()

class Exchange(db.Model):
    __tablename__ = "exchange"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)
    order_item_id = db.Column(db.Integer, db.ForeignKey("order_item.id"), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("customer.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    
    # Exchange details
    old_size = db.Column(db.String(20), nullable=False)
    new_size = db.Column(db.String(20), nullable=False)
    old_color = db.Column(db.String(50), nullable=True)  # Original color
    new_color = db.Column(db.String(50), nullable=True)  # New color
    old_quantity = db.Column(db.Integer, default=1, nullable=False)  # Quantity being exchanged
    new_quantity = db.Column(db.Integer, default=1, nullable=False)  # New quantity requested
    reason = db.Column(db.String(500), nullable=True)
    
    # Additional payment info for quantity changes
    additional_payment_required = db.Column(db.Boolean, default=False)
    additional_amount = db.Column(db.Float, default=0.0)
    
    # Status tracking
    status = db.Column(db.String(50), default="initiated", nullable=False)  # initiated, approved, out_for_delivery, delivered, rejected
    
    # Admin notes
    admin_notes = db.Column(db.Text, nullable=True)
    approved_by = db.Column(db.Integer, db.ForeignKey("admin.id"), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    
    # Delivery tracking
    delivery_guy_id = db.Column(db.Integer, db.ForeignKey("delivery_onboarding.id"), nullable=True)
    assigned_at = db.Column(db.DateTime, nullable=True)
    delivered_at = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=get_current_time)
    updated_at = db.Column(db.DateTime, default=get_current_time, onupdate=get_current_time)
    
    # Relationships
    order = db.relationship("Order", backref="exchanges")
    order_item = db.relationship("OrderItem", backref="exchanges", foreign_keys=[order_item_id])
    customer = db.relationship("Customer", backref="exchanges")
    product = db.relationship("Product", backref="exchanges")
    admin = db.relationship("Admin", backref="approved_exchanges")
    delivery_guy = db.relationship("DeliveryOnboarding", backref="exchange_assignments")

    def __repr__(self):
        return f"<Exchange {self.id} - Order: {self.order_id}, Status: {self.status}>"

    def as_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "order_item_id": self.order_item_id,
            "customer_id": self.customer_id,
            "product_id": self.product_id,
            "old_size": self.old_size,
            "new_size": self.new_size,
            "old_color": self.old_color,
            "new_color": self.new_color,
            "old_quantity": self.old_quantity,
            "new_quantity": self.new_quantity,
            "reason": self.reason,
            "additional_payment_required": self.additional_payment_required,
            "additional_amount": self.additional_amount,
            "status": self.status,
            "admin_notes": self.admin_notes,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "delivery_guy_id": self.delivery_guy_id,
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def to_dict(self):
        """Alias for as_dict for consistency with other models"""
        return self.as_dict()

    def can_approve(self):
        """Check if exchange can be approved"""
        return self.status == "initiated"
    
    def can_assign_delivery(self):
        """Check if exchange can be assigned for delivery"""
        return self.status == "approved"
    
    def can_start_delivery(self):
        """Check if delivery can be started (by delivery team)"""
        return self.status == "assigned"
    
    def can_mark_delivered(self):
        """Check if exchange can be marked as delivered"""
        return self.status == "out_for_delivery"
    
    def approve(self, admin_id):
        """Approve the exchange"""
        if not self.can_approve():
            return False, "Exchange cannot be approved in current status"
        
        self.status = "approved"
        self.approved_by = admin_id
        self.approved_at = get_current_time()
        return True, "Exchange approved successfully"
    
    def assign_delivery(self, delivery_guy_id):
        """Assign delivery guy for exchange (admin action)"""
        if not self.can_assign_delivery():
            return False, "Exchange cannot be assigned for delivery in current status"
        
        self.status = "assigned"  # Changed from "out_for_delivery" to "assigned"
        self.delivery_guy_id = delivery_guy_id
        self.assigned_at = get_current_time()
        return True, "Delivery assigned successfully"
    
    def start_delivery(self):
        """Start delivery (delivery team action)"""
        if not self.can_start_delivery():
            return False, "Delivery cannot be started in current status"
        
        self.status = "out_for_delivery"
        return True, "Delivery started successfully"
    
    def mark_delivered(self):
        """Mark exchange as delivered"""
        if not self.can_mark_delivered():
            return False, "Exchange cannot be marked as delivered in current status"
        
        self.status = "delivered"
        self.delivered_at = get_current_time()
        return True, "Exchange marked as delivered"
    
    def reject(self, admin_id, reason):
        """Reject the exchange"""
        if self.status != "initiated":
            return False, "Exchange cannot be rejected in current status"
        
        self.status = "rejected"
        self.approved_by = admin_id
        self.approved_at = get_current_time()
        self.admin_notes = reason
        return True, "Exchange rejected successfully"
