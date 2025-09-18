from extensions import db
from datetime import datetime

class Transaction(db.Model):
    __tablename__ = "transaction"
    
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customer.id"), nullable=True)
    type = db.Column(db.String(50), nullable=False)  # wallet_credit, wallet_debit, order_payment, refund, exchange_payment, delivery_payment
    amount = db.Column(db.Float, nullable=False)  # Positive for credit, negative for debit
    description = db.Column(db.Text, nullable=False)
    reference_id = db.Column(db.String(100), nullable=True)  # Order ID, Exchange ID, etc.
    reference_type = db.Column(db.String(50), nullable=True)  # order, exchange, refund, etc.
    status = db.Column(db.String(20), default="completed")  # pending, completed, failed, cancelled
    payment_method = db.Column(db.String(50), nullable=True)  # wallet, card, upi, cash, etc.
    transaction_metadata = db.Column(db.JSON, nullable=True)  # Additional data like order details, exchange details, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    customer = db.relationship("Customer", backref="transactions")
    
    def __repr__(self):
        return f"<Transaction {self.id} - {self.type} - {self.amount}>"
    
    def to_dict(self):
        # Get customer phone number (it's encrypted, so we'll show a placeholder)
        customer_phone = None
        if self.customer and hasattr(self.customer, 'phone_number_enc') and self.customer.phone_number_enc:
            customer_phone = "***-***-****"  # Placeholder for encrypted phone
        
        # Get customer name - try multiple fields
        customer_name = None
        if self.customer:
            customer_name = self.customer.name or self.customer.username or "Unknown Customer"
        
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "customer_name": customer_name,
            "customer_email": self.customer.email if self.customer else None,
            "customer_phone": customer_phone,
            "type": self.type,
            "amount": self.amount,
            "description": self.description,
            "reference_id": self.reference_id,
            "reference_type": self.reference_type,
            "status": self.status,
            "payment_method": self.payment_method,
            "metadata": self.transaction_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def create_transaction(customer_id, transaction_type, amount, description, reference_id=None, reference_type=None, payment_method=None, metadata=None, status="completed"):
        """Helper method to create a transaction"""
        transaction = Transaction(
            customer_id=customer_id,
            type=transaction_type,
            amount=amount,
            description=description,
            reference_id=reference_id,
            reference_type=reference_type,
            payment_method=payment_method,
            transaction_metadata=metadata,
            status=status
        )
        db.session.add(transaction)
        db.session.commit()
        return transaction
