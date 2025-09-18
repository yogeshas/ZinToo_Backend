# services/wallet_service.py
from models.wallet import Wallet, WalletTransaction
from models.customer import Customer
from models.transaction import Transaction
from extensions import db
from utils.crypto import encrypt_payload, decrypt_payload
from datetime import datetime
import json

def get_wallet_balance(customer_id: int):
    """Get customer wallet balance"""
    try:
        wallet = Wallet.query.filter_by(customer_id=customer_id).first()
        
        if not wallet:
            # Create wallet if it doesn't exist
            wallet = Wallet(customer_id=customer_id, balance=0.0)
            db.session.add(wallet)
            db.session.flush()  # Flush to get the wallet.id
            db.session.commit()
        
        # Encrypt the response data
        encrypted_data = encrypt_payload({
            "success": True,
            "balance": wallet.balance,
            "wallet_id": wallet.id
        })
        
        return {
            "success": True,
            "encrypted_data": encrypted_data,
            "message": "Wallet balance retrieved successfully"
        }, 200
        
    except Exception as e:
        print(f"❌ Get wallet balance error: {str(e)}")
        return {"error": "Failed to retrieve wallet balance"}, 500

def add_money_to_wallet(customer_id: int, amount: float, description: str = "Wallet recharge", reference_id: str = None):
    """Add money to customer wallet"""
    try:
        wallet = Wallet.query.filter_by(customer_id=customer_id).first()
        
        if not wallet:
            # Create wallet if it doesn't exist
            wallet = Wallet(customer_id=customer_id, balance=amount)
            db.session.add(wallet)
            db.session.flush()  # Flush to get the wallet.id
        else:
            wallet.balance += amount
            wallet.updated_at = datetime.utcnow()
        
        # Create wallet transaction record
        wallet_transaction = WalletTransaction(
            wallet_id=wallet.id,
            transaction_type="credit",
            amount=amount,
            description=description,
            reference_id=reference_id
        )
        
        # Create main transaction record
        main_transaction = Transaction.create_transaction(
            customer_id=customer_id,
            transaction_type="wallet_credit",
            amount=amount,
            description=description,
            reference_id=reference_id,
            reference_type="wallet",
            payment_method="wallet",
            metadata={
                "wallet_id": wallet.id,
                "previous_balance": wallet.balance - amount,
                "new_balance": wallet.balance
            }
        )
        
        db.session.add(wallet_transaction)
        db.session.commit()
        
        # Encrypt the response data
        encrypted_data = encrypt_payload({
            "success": True,
            "new_balance": wallet.balance,
            "transaction_id": main_transaction.id,
            "message": f"₹{amount} added to wallet successfully"
        })
        
        return {
            "success": True,
            "encrypted_data": encrypted_data,
            "message": "Money added to wallet successfully"
        }, 200
        
    except Exception as e:
        print(f"❌ Add money to wallet error: {str(e)}")
        db.session.rollback()
        return {"error": "Failed to add money to wallet"}, 500

def deduct_money_from_wallet(customer_id: int, amount: float, description: str = "Purchase", reference_id: str = None):
    """Deduct money from customer wallet"""
    try:
        wallet = Wallet.query.filter_by(customer_id=customer_id).first()
        
        if not wallet:
            return {"error": "Wallet not found"}, 404
        
        if wallet.balance < amount:
            return {"error": "Insufficient wallet balance"}, 400
        
        wallet.balance -= amount
        wallet.updated_at = datetime.utcnow()
        
        # Create wallet transaction record
        wallet_transaction = WalletTransaction(
            wallet_id=wallet.id,
            transaction_type="debit",
            amount=amount,
            description=description,
            reference_id=reference_id
        )
        
        # Create main transaction record
        main_transaction = Transaction.create_transaction(
            customer_id=customer_id,
            transaction_type="wallet_debit",
            amount=-amount,  # Negative amount for debit
            description=description,
            reference_id=reference_id,
            reference_type="wallet",
            payment_method="wallet",
            metadata={
                "wallet_id": wallet.id,
                "previous_balance": wallet.balance + amount,
                "new_balance": wallet.balance
            }
        )
        
        db.session.add(wallet_transaction)
        db.session.commit()
        
        # Encrypt the response data
        encrypted_data = encrypt_payload({
            "success": True,
            "new_balance": wallet.balance,
            "transaction_id": main_transaction.id,
            "message": f"₹{amount} deducted from wallet successfully"
        })
        
        return {
            "success": True,
            "encrypted_data": encrypted_data,
            "message": "Money deducted from wallet successfully"
        }, 200
        
    except Exception as e:
        print(f"❌ Deduct money from wallet error: {str(e)}")
        db.session.rollback()
        return {"error": "Failed to deduct money from wallet"}, 500

def get_wallet_transactions(customer_id: int, limit: int = 10):
    """Get customer wallet transaction history"""
    try:
        wallet = Wallet.query.filter_by(customer_id=customer_id).first()
        
        if not wallet:
            return {"error": "Wallet not found"}, 404
        
        transactions = WalletTransaction.query.filter_by(wallet_id=wallet.id)\
            .order_by(WalletTransaction.created_at.desc())\
            .limit(limit)\
            .all()
        
        transactions_data = [wallet_tx.as_dict() for wallet_tx in transactions]
        
        # Encrypt the response data
        encrypted_data = encrypt_payload({
            "success": True,
            "transactions": transactions_data,
            "total_count": len(transactions_data)
        })
        
        return {
            "success": True,
            "encrypted_data": encrypted_data,
            "message": "Wallet transactions retrieved successfully"
        }, 200
        
    except Exception as e:
        print(f"❌ Get wallet transactions error: {str(e)}")
        return {"error": "Failed to retrieve wallet transactions"}, 500

def refund_to_wallet(customer_id: int, amount: float, description: str = "Refund", reference_id: str = None):
    """Refund money to customer wallet"""
    try:
        wallet = Wallet.query.filter_by(customer_id=customer_id).first()
        
        if not wallet:
            # Create wallet if it doesn't exist
            wallet = Wallet(customer_id=customer_id, balance=amount)
            db.session.add(wallet)
            db.session.flush()  # Flush to get the wallet.id
        
        wallet.balance += amount
        wallet.updated_at = datetime.utcnow()
        
        # Create wallet transaction record
        wallet_transaction = WalletTransaction(
            wallet_id=wallet.id,
            transaction_type="refund",
            amount=amount,
            description=description,
            reference_id=reference_id
        )
        
        # Create main transaction record
        main_transaction = Transaction.create_transaction(
            customer_id=customer_id,
            transaction_type="refund",
            amount=amount,
            description=description,
            reference_id=reference_id,
            reference_type="refund",
            payment_method="wallet",
            metadata={
                "wallet_id": wallet.id,
                "previous_balance": wallet.balance - amount,
                "new_balance": wallet.balance
            }
        )
        
        db.session.add(wallet_transaction)
        db.session.commit()
        
        # Encrypt the response data
        encrypted_data = encrypt_payload({
            "success": True,
            "new_balance": wallet.balance,
            "transaction_id": main_transaction.id,
            "message": f"₹{amount} refunded to wallet successfully"
        })
        
        return {
            "success": True,
            "encrypted_data": encrypted_data,
            "message": "Money refunded to wallet successfully"
        }, 200
        
    except Exception as e:
        print(f"❌ Refund to wallet error: {str(e)}")
        db.session.rollback()
        return {"error": "Failed to refund money to wallet"}, 500
