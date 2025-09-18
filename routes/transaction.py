#!/usr/bin/env python3
"""
API routes for transaction management.
Handles all transaction-related operations including viewing, filtering, and creating transactions.
"""

from flask import Blueprint, request, jsonify
from models.transaction import Transaction
from models.customer import Customer
from extensions import db
from sqlalchemy import desc, and_, or_
from sqlalchemy.orm import joinedload
import math

transaction_bp = Blueprint('transaction', __name__)

@transaction_bp.route('/transactions', methods=['GET'])
def get_all_transactions():
    """
    Get all transactions with pagination, search, and filtering
    Query parameters:
    - page: Page number (default: 1)
    - limit: Items per page (default: 10)
    - search: Search term for customer name, email, or description
    - type: Filter by transaction type
    - status: Filter by transaction status
    - customer_id: Filter by specific customer
    - start_date: Filter transactions from this date (YYYY-MM-DD)
    - end_date: Filter transactions to this date (YYYY-MM-DD)
    """
    try:
        # Get query parameters
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        search = request.args.get('search', '').strip()
        transaction_type = request.args.get('type', '').strip()
        status = request.args.get('status', '').strip()
        customer_id = request.args.get('customer_id', '').strip()
        start_date = request.args.get('start_date', '').strip()
        end_date = request.args.get('end_date', '').strip()
        
        # Build base query
        query = Transaction.query.options(joinedload(Transaction.customer))
        
        # Apply filters
        if search:
            query = query.join(Customer).filter(
                or_(
                    Customer.name.ilike(f'%{search}%'),
                    Customer.email.ilike(f'%{search}%'),
                    Transaction.description.ilike(f'%{search}%')
                )
            )
        
        if transaction_type:
            query = query.filter(Transaction.type == transaction_type)
        
        if status:
            query = query.filter(Transaction.status == status)
        
        if customer_id:
            query = query.filter(Transaction.customer_id == customer_id)
        
        if start_date:
            try:
                from datetime import datetime
                start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(Transaction.created_at >= start_datetime)
            except ValueError:
                return jsonify({"error": "Invalid start_date format. Use YYYY-MM-DD"}), 400
        
        if end_date:
            try:
                from datetime import datetime
                end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
                # Add 23:59:59 to include the entire day
                end_datetime = end_datetime.replace(hour=23, minute=59, second=59)
                query = query.filter(Transaction.created_at <= end_datetime)
            except ValueError:
                return jsonify({"error": "Invalid end_date format. Use YYYY-MM-DD"}), 400
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * limit
        transactions = query.order_by(desc(Transaction.created_at)).offset(offset).limit(limit).all()
        
        # Calculate pagination info
        total_pages = math.ceil(total_count / limit) if total_count > 0 else 1
        
        # Convert to dict
        transactions_data = [transaction.to_dict() for transaction in transactions]
        
        return jsonify({
            "success": True,
            "data": transactions_data,
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "total_count": total_count,
                "limit": limit,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }), 200

    except Exception as e:
        print(f"Error in get_all_transactions: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@transaction_bp.route('/transactions/<int:transaction_id>', methods=['GET'])
def get_transaction_by_id(transaction_id):
    """
    Get a specific transaction by ID
    """
    try:
        transaction = Transaction.query.options(joinedload(Transaction.customer)).get(transaction_id)
        
        if not transaction:
            return jsonify({
                "success": False,
                "error": "Transaction not found"
            }), 404
        
        return jsonify({
            "success": True,
            "data": transaction.to_dict()
        }), 200

    except Exception as e:
        print(f"Error in get_transaction_by_id: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@transaction_bp.route('/transactions/stats', methods=['GET'])
def get_transaction_stats():
    """
    Get transaction statistics
    """
    try:
        from sqlalchemy import func
        from datetime import datetime, timedelta
        
        # Get date range parameters
        days = int(request.args.get('days', 30))
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Total transactions count
        total_transactions = Transaction.query.filter(
            Transaction.created_at >= start_date
        ).count()
        
        # Total amount (sum of all amounts)
        total_amount = Transaction.query.filter(
            Transaction.created_at >= start_date
        ).with_entities(func.sum(Transaction.amount)).scalar() or 0
        
        # Transactions by type
        type_stats = db.session.query(
            Transaction.type,
            func.count(Transaction.id).label('count'),
            func.sum(Transaction.amount).label('total_amount')
        ).filter(
            Transaction.created_at >= start_date
        ).group_by(Transaction.type).all()
        
        # Transactions by status
        status_stats = db.session.query(
            Transaction.status,
            func.count(Transaction.id).label('count')
        ).filter(
            Transaction.created_at >= start_date
        ).group_by(Transaction.status).all()
        
        # Daily transaction count for the last 30 days
        daily_stats = db.session.query(
            func.date(Transaction.created_at).label('date'),
            func.count(Transaction.id).label('count'),
            func.sum(Transaction.amount).label('total_amount')
        ).filter(
            Transaction.created_at >= start_date
        ).group_by(func.date(Transaction.created_at)).order_by('date').all()
        
        stats = {
            "total_transactions": total_transactions,
            "total_amount": float(total_amount),
            "transactions_by_type": [
                {
                    "type": stat.type,
                    "count": stat.count,
                    "total_amount": float(stat.total_amount)
                }
                for stat in type_stats
            ],
            "transactions_by_status": [
                {
                    "status": stat.status,
                    "count": stat.count
                }
                for stat in status_stats
            ],
            "daily_transactions": [
                {
                    "date": stat.date.isoformat(),
                    "count": stat.count,
                    "total_amount": float(stat.total_amount)
                }
                for stat in daily_stats
            ],
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            }
        }
        
        return jsonify({
            "success": True,
            "data": stats
        }), 200

    except Exception as e:
        print(f"Error in get_transaction_stats: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@transaction_bp.route('/transactions', methods=['POST'])
def create_transaction():
    """
    Create a new transaction
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['customer_id', 'type', 'amount', 'description']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "error": f"Missing required field: {field}"
                }), 400
        
        # Create transaction
        transaction = Transaction.create_transaction(
            customer_id=data['customer_id'],
            transaction_type=data['type'],
            amount=float(data['amount']),
            description=data['description'],
            reference_id=data.get('reference_id'),
            reference_type=data.get('reference_type'),
            payment_method=data.get('payment_method'),
            metadata=data.get('metadata'),
            status=data.get('status', 'completed')
        )
        
        return jsonify({
            "success": True,
            "data": transaction.to_dict(),
            "message": "Transaction created successfully"
        }), 201

    except Exception as e:
        print(f"Error in create_transaction: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
