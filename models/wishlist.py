from extensions import db
from datetime import datetime

class Wishlist(db.Model):
    __tablename__ = "wishlist"
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customer.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Relationships
    customer = db.relationship("Customer", backref="wishlist_items")
    product = db.relationship("Product", backref="wishlist_items")

    def to_dict(self):
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "product_id": self.product_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "product": self.product.to_dict() if self.product else None,
            "customer": self.customer.as_dict() if self.customer else None
        }

    def __repr__(self):
        return f"<Wishlist {self.id} - Customer: {self.customer_id}, Product: {self.product_id}>"
