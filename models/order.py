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
    
    # Coupon Information
    coupon_id = db.Column(db.Integer, db.ForeignKey("coupon.id"), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=get_current_time)
    updated_at = db.Column(db.DateTime, default=get_current_time, onupdate=get_current_time)
    estimated_delivery = db.Column(db.DateTime, nullable=True)

    # Delivery Assignment - Now using onboarding_id
    delivery_guy_id = db.Column(db.Integer, db.ForeignKey("delivery_onboarding.id"), nullable=True)
    assigned_at = db.Column(db.DateTime, nullable=True)
    delivery_notes = db.Column(db.Text, nullable=True)
    
    # Simple delivery type tracking (optional for now)
    is_exchange_delivery = db.Column(db.Boolean, default=False, nullable=True)
    


    # Relationships
    customer = db.relationship("Customer", backref="orders")
    order_items = db.relationship("OrderItem", backref="order", lazy="dynamic", cascade="all, delete-orphan")
    coupon = db.relationship("Coupon", backref="orders")


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
            "delivery_notes": self.delivery_notes,
            "is_exchange_delivery": self.is_exchange_delivery,
            "coupon_id": self.coupon_id,
            "coupon_code": self.coupon.code if self.coupon else None
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
    selected_size = db.Column(db.String(20), nullable=True)  # Store the selected size
    selected_color = db.Column(db.String(50), nullable=True)  # Store the selected color
    
    # Individual product status tracking
    status = db.Column(db.String(20), default="pending", nullable=False)  # pending, confirmed, processing, shipped, delivered, cancelled, returned, refunded
    quantity_cancel = db.Column(db.Integer, default=0, nullable=False)  # Track how many items have been cancelled
    cancel_reason = db.Column(db.String(500), nullable=True)
    cancel_requested_at = db.Column(db.DateTime, nullable=True)
    cancelled_at = db.Column(db.DateTime, nullable=True)
    cancelled_by = db.Column(db.String(20), nullable=True)  # customer, admin, system
    return_pickup_time = db.Column(db.DateTime, nullable=True)  # Scheduled pickup time for cancelled items
    return_pickup_time_from = db.Column(db.DateTime, nullable=True)  # From datetime for pickup time range
    return_pickup_time_to = db.Column(db.DateTime, nullable=True)  # To datetime for pickup time range
    return_delivery_status = db.Column(db.String(20), default="not_applicable", nullable=False)  # not_applicable, pending_payment, paid, scheduled, picked_up, delivered
    payment_return_delivery = db.Column(db.Float, default=0.0, nullable=False)  # Payment for return delivery
    payment_return_delivery_id = db.Column(db.String(100), nullable=True)  # Payment ID for return delivery
    payment_return_delivery_method = db.Column(db.String(50), nullable=True)  # Payment method for return delivery
    
    # Refund tracking
    refund_status = db.Column(db.String(20), default="not_applicable", nullable=False)  # not_applicable, requested, initiated, completed, failed
    refund_amount = db.Column(db.Float, default=0.0, nullable=False)
    refund_reason = db.Column(db.String(500), nullable=True)
    refund_requested_at = db.Column(db.DateTime, nullable=True)
    refunded_at = db.Column(db.DateTime, nullable=True)
    
    # Exchange tracking
    exchange_status = db.Column(db.String(20), default="not_applicable", nullable=False)  # not_applicable, requested, approved, out_for_delivery, delivered, rejected
    exchange_id = db.Column(db.Integer, db.ForeignKey("exchange.id"), nullable=True)
    
    # Delivery assignment
    delivery_guy_id = db.Column(db.Integer, db.ForeignKey("delivery_onboarding.id"), nullable=True)
    
    created_at = db.Column(db.DateTime, default=get_current_time)
    updated_at = db.Column(db.DateTime, default=get_current_time, onupdate=get_current_time)

    # Relationships
    product = db.relationship("Product", backref="order_items")
    # Note: Exchange relationship is handled by Exchange model's backref to "exchanges"

    def __repr__(self):
        pickup_info = f", Pickup: {self.return_pickup_time}" if self.return_pickup_time else ""
        return f"<OrderItem {self.id} - Order: {self.order_id}, Product: {self.product_id}, Size: {self.selected_size}, Color: {self.selected_color}, Qty: {self.quantity}, Cancelled: {self.quantity_cancel}{pickup_info}>"

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
            "selected_size": self.selected_size,
            "selected_color": self.selected_color,
            "status": self.status,
            "quantity_cancel": self.quantity_cancel,
            "cancel_reason": self.cancel_reason,
            "cancel_requested_at": self.cancel_requested_at.isoformat() if self.cancel_requested_at else None,
            "cancelled_at": self.cancelled_at.isoformat() if self.cancelled_at else None,
            "cancelled_by": self.cancelled_by,
            "return_pickup_time": self.return_pickup_time.isoformat() if self.return_pickup_time else None,
            "return_pickup_time_from": self.return_pickup_time_from.isoformat() if self.return_pickup_time_from else None,
            "return_pickup_time_to": self.return_pickup_time_to.isoformat() if self.return_pickup_time_to else None,
            "return_delivery_status": self.return_delivery_status,
            "payment_return_delivery": self.payment_return_delivery,
            "payment_return_delivery_id": self.payment_return_delivery_id,
            "payment_return_delivery_method": self.payment_return_delivery_method,
            "refund_status": self.refund_status,
            "refund_amount": self.refund_amount,
            "refund_reason": self.refund_reason,
            "refund_requested_at": self.refund_requested_at.isoformat() if self.refund_requested_at else None,
            "refunded_at": self.refunded_at.isoformat() if self.refunded_at else None,
            "exchange_status": self.exchange_status,
            "exchange_id": self.exchange_id,
            "delivery_guy_id": self.delivery_guy_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class OrderHistory(db.Model):
    __tablename__ = "order_history"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)
    delivery_guy_id = db.Column(db.Integer, db.ForeignKey("delivery_onboarding.id"), nullable=False)
    status = db.Column(db.String(50), nullable=False)  # assigned, picked_up, delivered, cancelled, etc.
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=get_current_time)
    updated_at = db.Column(db.DateTime, default=get_current_time, onupdate=get_current_time)
    
    # Relationships
    order = db.relationship("Order", backref="history")
    delivery_guy = db.relationship("DeliveryOnboarding", backref="order_history")
    
    def __repr__(self):
        return f"<OrderHistory {self.id} - Order: {self.order_id}, Delivery Guy: {self.delivery_guy_id}, Status: {self.status}>"
    
    def as_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "delivery_guy_id": self.delivery_guy_id,
            "status": self.status,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
