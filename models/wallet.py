from extensions import db
from datetime import datetime

def get_current_time():
    return datetime.utcnow()

class Wallet(db.Model):
    __tablename__ = "wallet"
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customer.id"), nullable=False)
    balance = db.Column(db.Float, default=0.0, nullable=False)
    created_at = db.Column(db.DateTime, default=get_current_time)
    updated_at = db.Column(db.DateTime, default=get_current_time, onupdate=get_current_time)

    # Relationships
    customer = db.relationship("Customer", backref="wallet")
    transactions = db.relationship("WalletTransaction", backref="wallet", lazy="dynamic")

    def __repr__(self):
        return f"<Wallet {self.id} - Customer: {self.customer_id}, Balance: {self.balance}>"

    def as_dict(self):
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "balance": self.balance,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class WalletTransaction(db.Model):
    __tablename__ = "wallet_transaction"
    id = db.Column(db.Integer, primary_key=True)
    wallet_id = db.Column(db.Integer, db.ForeignKey("wallet.id"), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # 'credit', 'debit', 'refund'
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200))
    reference_id = db.Column(db.String(100))  # Order ID, Payment ID, etc.
    created_at = db.Column(db.DateTime, default=get_current_time)

    def __repr__(self):
        return f"<WalletTransaction {self.id} - Type: {self.transaction_type}, Amount: {self.amount}>"

    def as_dict(self):
        return {
            "id": self.id,
            "wallet_id": self.wallet_id,
            "transaction_type": self.transaction_type,
            "amount": self.amount,
            "description": self.description,
            "reference_id": self.reference_id,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
