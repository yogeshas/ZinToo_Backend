from extensions import db
from datetime import datetime

class Cart(db.Model):
    __tablename__ = "cart"
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customer.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    selected_size = db.Column(db.String(20), nullable=True)  # Store the selected size
    selected_color = db.Column(db.String(50), nullable=True)  # Store the selected color
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    # Relationships
    customer = db.relationship("Customer", backref="cart_items")
    product = db.relationship("Product", backref="cart_items")

    def to_dict(self):
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "selected_size": self.selected_size,
            "selected_color": self.selected_color,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "product": self.product.to_dict() if self.product else None,
            "customer": self.customer.as_dict() if self.customer else None,
            "sizes": getattr(self, 'sizes', {})  # Include sizes data if available
        }

    def __repr__(self):
        return f"<Cart {self.id} - Customer: {self.customer_id}, Product: {self.product_id}, Size: {self.selected_size}, Color: {self.selected_color}, Qty: {self.quantity}>"
