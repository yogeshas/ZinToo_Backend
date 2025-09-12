from extensions import db

class Leave(db.Model):
    __tablename__ = "leave"
    id = db.Column(db.Integer, primary_key=True)
    delivery_user_id = db.Column(db.Integer, db.ForeignKey('delivery_onboarding.id'))  # Updated to reference delivery_onboarding table
    
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default="pending")
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    def __repr__(self):
        return f"<DeliveryUser {self.name} with ID {self.id}>"
