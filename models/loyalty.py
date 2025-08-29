from extensions import db

class Loyalty(db.Model):
    __tablename__ = "user_loyalty"
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customer.id"), nullable=False)
    order_count = db.Column(db.Integer, default=0)
    total_spent = db.Column(db.Float, default=0.0)
    last_order_date = db.Column(db.DateTime, nullable=True)
    points = db.Column(db.Integer, default=0)
    tier = db.Column(db.String(50), nullable=False, default="Bronze")
    last_updated = db.Column(db.DateTime, nullable=False)
    customer = db.relationship("Customer", backref="loyalty", lazy=True)
    

    def __repr__(self):
        return f"<Address {self.name} for Customer {self.uid}>"
