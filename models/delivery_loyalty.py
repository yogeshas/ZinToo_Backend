from extensions import db

class Delivery_Loyalty(db.Model):
    __tablename__ = "delivery_loyalty"
    id = db.Column(db.Integer, primary_key=True)
    delivery_user_id = db.Column(db.Integer, db.ForeignKey('delivery_onboarding.id'))
    order_count = db.Column(db.Integer, default=0)
    total_earnings = db.Column(db.Float, default=0.0)
    last_order_date = db.Column(db.DateTime, nullable=True)
    points = db.Column(db.Integer, default=0)
    tier = db.Column(db.String(50), nullable=False, default="Bronze")
    last_updated = db.Column(db.DateTime, nullable=False)
    # New columns for tracking order IDs
    rejected_order_ids = db.Column(db.Text, nullable=True)  # Store as comma-separated IDs
    approved_order_ids = db.Column(db.Text, nullable=True)  # Store as comma-separated IDs
    delivery_user = db.relationship("DeliveryOnboarding", back_populates="delivery_loyalties")

    def __repr__(self):
        return f"<DeliveryLoyalty {self.id} for user {self.delivery_user_id}>"
    
    def add_rejected_order(self, order_id: int):
        """Add a rejected order ID to the list"""
        if not self.rejected_order_ids:
            self.rejected_order_ids = str(order_id)
        else:
            current_ids = self.rejected_order_ids.split(',')
            if str(order_id) not in current_ids:
                current_ids.append(str(order_id))
                self.rejected_order_ids = ','.join(current_ids)
    
    def add_approved_order(self, order_id: int):
        """Add an approved order ID to the list"""
        if not self.approved_order_ids:
            self.approved_order_ids = str(order_id)
        else:
            current_ids = self.approved_order_ids.split(',')
            if str(order_id) not in current_ids:
                current_ids.append(str(order_id))
                self.approved_order_ids = ','.join(current_ids)
    
    def get_rejected_order_ids(self) -> list:
        """Get list of rejected order IDs"""
        if not self.rejected_order_ids:
            return []
        return [int(id.strip()) for id in self.rejected_order_ids.split(',') if id.strip()]
    
    def get_approved_order_ids(self) -> list:
        """Get list of approved order IDs"""
        if not self.approved_order_ids:
            return []
        return [int(id.strip()) for id in self.approved_order_ids.split(',') if id.strip()]
