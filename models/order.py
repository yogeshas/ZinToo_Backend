from extensions import db
from datetime import datetime

def get_current_time():
    return datetime.utcnow()

class Order(db.Model):
    __tablename__ = "order"
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customer.id"), nullable=False)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    status = db.Column(db.String(20), default="pending", nullable=False)  # pending, confirmed, processing, shipped, delivered, cancelled
    
    # Delivery Information
    delivery_address = db.Column(db.Text, nullable=False)
    delivery_type = db.Column(db.String(20), nullable=False)  # express, standard, scheduled
    scheduled_time = db.Column(db.DateTime, nullable=True)
    delivery_fee = db.Column(db.Float, default=0.0)
    
    # Payment Information
    payment_method = db.Column(db.String(20), nullable=False)  # wallet, razorpay, cod
    payment_id = db.Column(db.String(100), nullable=True)
    payment_status = db.Column(db.String(20), default="pending")  # pending, completed, failed, refunded
    
    # Pricing
    subtotal = db.Column(db.Float, nullable=False)
    delivery_fee_amount = db.Column(db.Float, default=0.0)
    platform_fee = db.Column(db.Float, default=0.0)
    discount_amount = db.Column(db.Float, default=0.0)
    total_amount = db.Column(db.Float, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=get_current_time)
    updated_at = db.Column(db.DateTime, default=get_current_time, onupdate=get_current_time)
    estimated_delivery = db.Column(db.DateTime, nullable=True)

    # Delivery Assignment - Now using onboarding_id
    delivery_guy_id = db.Column(db.Integer, db.ForeignKey("delivery_onboarding.id"), nullable=True)
    assigned_at = db.Column(db.DateTime, nullable=True)
    delivery_notes = db.Column(db.Text, nullable=True)

    # Relationships
    customer = db.relationship("Customer", backref="orders")
    order_items = db.relationship("OrderItem", backref="order", lazy="dynamic", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Order {self.order_number} - Customer: {self.customer_id}, Status: {self.status}>"

    def as_dict(self):
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "order_number": self.order_number,
            "status": self.status,
            "delivery_address": self.delivery_address,
            "delivery_type": self.delivery_type,
            "scheduled_time": self.scheduled_time.isoformat() if self.scheduled_time else None,
            "delivery_fee": self.delivery_fee,
            "payment_method": self.payment_method,
            "payment_id": self.payment_id,
            "payment_status": self.payment_status,
            "subtotal": self.subtotal,
            "delivery_fee_amount": self.delivery_fee_amount,
            "platform_fee": self.platform_fee,
            "discount_amount": self.discount_amount,
            "total_amount": self.total_amount,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "estimated_delivery": self.estimated_delivery.isoformat() if self.estimated_delivery else None,
            "delivery_guy_id": self.delivery_guy_id,
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "delivery_notes": self.delivery_notes
        }

    def generate_order_number(self):
        """Generate unique order number"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"ORD{timestamp}{self.id}"

class OrderItem(db.Model):
    __tablename__ = "order_item"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    
    # Product snapshot (in case product details change)
    product_name = db.Column(db.String(200), nullable=False)
    product_image = db.Column(db.String(500), nullable=True)
    
    created_at = db.Column(db.DateTime, default=get_current_time)

    # Relationships
    product = db.relationship("Product", backref="order_items")

    def __repr__(self):
        return f"<OrderItem {self.id} - Order: {self.order_id}, Product: {self.product_id}, Qty: {self.quantity}>"

    def as_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "total_price": self.total_price,
            "product_name": self.product_name,
            "product_image": self.product_image,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
