from flask import Blueprint, request, jsonify
from extensions import db
from models.earnings_management import EarningsManagement
from models.delivery_onboarding import DeliveryOnboarding
from datetime import datetime, date, timedelta
from functools import wraps
import jwt
import os

earnings_management_bp = Blueprint('earnings_management', __name__, url_prefix='/api/earnings-management')

# Test endpoint
@earnings_management_bp.route("/test", methods=["GET"])
def test_earnings_management():
    """Test endpoint to verify earnings management routes are working"""
    return jsonify({
        "success": True,
        "message": "Earnings management API is working!",
        "timestamp": datetime.utcnow().isoformat()
    }), 200

# ============================================================================
# AUTHENTICATION DECORATORS
# ============================================================================

def require_delivery_auth(f):
    """Decorator to require delivery guy authentication"""
    from functools import wraps
    from services.delivery_auth_service import verify_auth_token
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"error": "Authorization header required"}), 401
        
        try:
            # Extract token from Bearer header
            if not auth_header.startswith('Bearer '):
                return jsonify({"error": "Invalid authorization header format"}), 401
            
            token = auth_header.split(' ', 1)[1]
            
            # Verify the auth token
            result = verify_auth_token(token)
            if not result["success"]:
                return jsonify({"error": "Invalid or expired token"}), 401
            
            # Add delivery guy ID to request
            request.delivery_guy_id = result["user"]["delivery_guy_id"]
            return f(*args, **kwargs)
        except Exception as e:
            print(f"Auth error: {str(e)}")
            return jsonify({"error": "Authentication failed"}), 401
    
    return decorated_function

def require_admin_auth(f):
    """Decorator to require admin authentication"""
    from functools import wraps
    from services.admin_service import get_admin_by_token
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"error": "Authorization header required"}), 401
        
        try:
            # Extract token from Bearer header
            if not auth_header.startswith('Bearer '):
                return jsonify({"error": "Invalid authorization header format"}), 401
            
            token = auth_header.split(' ', 1)[1]
            
            # Verify the admin token
            admin = get_admin_by_token(token)
            if not admin:
                return jsonify({"error": "Invalid or expired admin token"}), 401
            
            # Add admin ID to request
            request.admin_id = admin.id
            return f(*args, **kwargs)
        except Exception as e:
            print(f"Admin auth error: {str(e)}")
            return jsonify({"error": "Authentication failed"}), 401
    
    return decorated_function

# ============================================================================
# DELIVERY GUY ENDPOINTS
# ============================================================================

@earnings_management_bp.route("/delivery/earnings", methods=["GET"])
@require_delivery_auth
def get_delivery_earnings():
    """Get all earnings for a delivery guy"""
    try:
        delivery_guy_id = request.delivery_guy_id
        payment_type = request.args.get('type', 'all')  # all, salary, bonus, payout
        period = request.args.get('period', 'all')  # all, daily, weekly, monthly
        
        # Base query
        query = EarningsManagement.query.filter_by(delivery_guy_id=delivery_guy_id)
        
        # Filter by payment type
        if payment_type != 'all':
            query = query.filter_by(payment_type=payment_type)
        
        # Filter by period
        if period != 'all':
            query = query.filter_by(payment_period=period)
        
        # Order by creation date (newest first)
        earnings = query.order_by(EarningsManagement.created_at.desc()).all()
        
        result = [earning.as_dict() for earning in earnings]
        
        return jsonify({
            "success": True,
            "earnings": result,
            "total": len(result)
        }), 200
        
    except Exception as e:
        print(f"Get delivery earnings error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@earnings_management_bp.route("/delivery/earnings/summary", methods=["GET"])
@require_delivery_auth
def get_delivery_earnings_summary():
    """Get earnings summary for delivery guy dashboard"""
    try:
        delivery_guy_id = request.delivery_guy_id
        period = request.args.get('period', 'monthly')  # daily, weekly, monthly
        
        # Calculate date range based on period
        end_date = date.today()
        if period == 'daily':
            start_date = end_date
        elif period == 'weekly':
            start_date = end_date - timedelta(days=7)
        else:  # monthly
            start_date = end_date - timedelta(days=30)
        
        # Get summary
        summary = EarningsManagement.get_earnings_summary(
            delivery_guy_id=delivery_guy_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Get weekly breakdown
        weekly_breakdown = EarningsManagement.get_weekly_breakdown(
            delivery_guy_id=delivery_guy_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Get daily breakdown
        daily_breakdown = EarningsManagement.get_daily_breakdown(
            delivery_guy_id=delivery_guy_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Format results
        summary_data = {}
        for item in summary:
            summary_data[item.payment_type] = {
                'total_amount': float(item.total_amount),
                'count': item.count
            }
        
        weekly_data = []
        for item in weekly_breakdown:
            weekly_data.append({
                'week_start': item.week_start.isoformat() if item.week_start else None,
                'payment_type': item.payment_type,
                'total_amount': float(item.total_amount),
                'count': item.count
            })
        
        daily_data = []
        for item in daily_breakdown:
            daily_data.append({
                'date': item.start_date.isoformat() if item.start_date else None,
                'payment_type': item.payment_type,
                'total_amount': float(item.total_amount),
                'count': item.count
            })
        
        return jsonify({
            "success": True,
            "summary": summary_data,
            "weekly_breakdown": weekly_data,
            "daily_breakdown": daily_data,
            "period": period
        }), 200
        
    except Exception as e:
        print(f"Get delivery earnings summary error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

# ============================================================================
# ADMIN ENDPOINTS
# ============================================================================

@earnings_management_bp.route("/admin/earnings", methods=["GET"])
@require_admin_auth
def get_all_earnings():
    """Get all earnings for admin review"""
    try:
        payment_type = request.args.get('type', 'all')  # all, salary, bonus, payout
        status = request.args.get('status', 'all')  # all, pending, approved, paid, rejected
        delivery_guy_id = request.args.get('delivery_guy_id')
        
        # Base query
        query = EarningsManagement.query
        
        # Filter by payment type
        if payment_type != 'all':
            query = query.filter_by(payment_type=payment_type)
        
        # Filter by status
        if status != 'all':
            query = query.filter_by(status=status)
        
        # Filter by delivery guy
        if delivery_guy_id:
            query = query.filter_by(delivery_guy_id=delivery_guy_id)
        
        # Order by creation date (newest first)
        earnings = query.order_by(EarningsManagement.created_at.desc()).all()
        
        result = [earning.as_dict() for earning in earnings]
        
        return jsonify({
            "success": True,
            "earnings": result,
            "total": len(result)
        }), 200
        
    except Exception as e:
        print(f"Get all earnings error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@earnings_management_bp.route("/admin/earnings", methods=["POST"])
@require_admin_auth
def create_earning():
    """Create new earning entry"""
    try:
        admin_id = request.admin_id
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate required fields
        delivery_guy_id = data.get("delivery_guy_id")
        payment_type = data.get("payment_type")
        amount = data.get("amount")
        payment_period = data.get("payment_period")
        start_date_str = data.get("start_date")
        
        if not all([delivery_guy_id, payment_type, amount, payment_period, start_date_str]):
            return jsonify({"error": "delivery_guy_id, payment_type, amount, payment_period, and start_date are required"}), 400
        
        # Validate payment type
        if payment_type not in ['salary', 'bonus', 'payout']:
            return jsonify({"error": "payment_type must be salary, bonus, or payout"}), 400
        
        # Validate payment period
        if payment_period not in ['daily', 'weekly', 'monthly']:
            return jsonify({"error": "payment_period must be daily, weekly, or monthly"}), 400
        
        # Parse start date
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "Invalid start_date format. Use YYYY-MM-DD"}), 400
        
        # Calculate end date based on period
        end_date = None
        if payment_period == 'weekly':
            end_date = start_date + timedelta(days=6)
        elif payment_period == 'monthly':
            # Calculate end of month
            if start_date.month == 12:
                end_date = date(start_date.year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(start_date.year, start_date.month + 1, 1) - timedelta(days=1)
        
        # Check if delivery guy exists
        delivery_guy = DeliveryOnboarding.query.get(delivery_guy_id)
        if not delivery_guy:
            return jsonify({"error": "Delivery guy not found"}), 404
        
        # Create new earning entry
        earning = EarningsManagement(
            delivery_guy_id=delivery_guy_id,
            payment_type=payment_type,
            amount=float(amount),
            payment_period=payment_period,
            start_date=start_date,
            end_date=end_date,
            description=data.get("description", ""),
            status="approved",  # Admin created entries are auto-approved
            admin_notes=data.get("admin_notes", ""),
            approved_at=datetime.utcnow(),
            approved_by=admin_id
        )
        
        db.session.add(earning)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Earning entry created successfully",
            "earning": earning.as_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Create earning error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@earnings_management_bp.route("/admin/earnings/<int:earning_id>/approve", methods=["POST"])
@require_admin_auth
def approve_earning(earning_id):
    """Approve an earning entry"""
    try:
        admin_id = request.admin_id
        data = request.get_json() or {}
        admin_notes = data.get("admin_notes", "")
        
        earning = EarningsManagement.query.get(earning_id)
        if not earning:
            return jsonify({"error": "Earning entry not found"}), 404
        
        if earning.status != "pending":
            return jsonify({"error": "Earning entry is not pending"}), 400
        
        earning.status = "approved"
        earning.admin_notes = admin_notes
        earning.approved_at = datetime.utcnow()
        earning.approved_by = admin_id
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Earning entry approved successfully",
            "earning": earning.as_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Approve earning error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@earnings_management_bp.route("/admin/earnings/<int:earning_id>/reject", methods=["POST"])
@require_admin_auth
def reject_earning(earning_id):
    """Reject an earning entry"""
    try:
        admin_id = request.admin_id
        data = request.get_json()
        
        if not data or not data.get("admin_notes"):
            return jsonify({"error": "admin_notes is required for rejection"}), 400
        
        earning = EarningsManagement.query.get(earning_id)
        if not earning:
            return jsonify({"error": "Earning entry not found"}), 404
        
        if earning.status != "pending":
            return jsonify({"error": "Earning entry is not pending"}), 400
        
        earning.status = "rejected"
        earning.admin_notes = data.get("admin_notes")
        earning.approved_at = datetime.utcnow()
        earning.approved_by = admin_id
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Earning entry rejected successfully",
            "earning": earning.as_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Reject earning error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@earnings_management_bp.route("/admin/earnings/<int:earning_id>/mark-paid", methods=["POST"])
@require_admin_auth
def mark_earning_paid(earning_id):
    """Mark an earning entry as paid"""
    try:
        earning = EarningsManagement.query.get(earning_id)
        if not earning:
            return jsonify({"error": "Earning entry not found"}), 404
        
        if earning.status != "approved":
            return jsonify({"error": "Earning entry must be approved before marking as paid"}), 400
        
        earning.status = "paid"
        earning.paid_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Earning entry marked as paid successfully",
            "earning": earning.as_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Mark earning paid error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@earnings_management_bp.route("/admin/earnings/summary", methods=["GET"])
@require_admin_auth
def get_admin_earnings_summary():
    """Get earnings summary for admin dashboard"""
    try:
        period = request.args.get('period', 'monthly')  # daily, weekly, monthly
        delivery_guy_id = request.args.get('delivery_guy_id')
        
        # Calculate date range based on period
        end_date = date.today()
        if period == 'daily':
            start_date = end_date
        elif period == 'weekly':
            start_date = end_date - timedelta(days=7)
        else:  # monthly
            start_date = end_date - timedelta(days=30)
        
        # Get summary
        summary = EarningsManagement.get_earnings_summary(
            delivery_guy_id=delivery_guy_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Get breakdown based on period
        weekly_breakdown = []
        daily_breakdown = []
        
        if period == 'weekly':
            # For weekly period, show weekly breakdown
            weekly_breakdown = EarningsManagement.get_weekly_breakdown(
                delivery_guy_id=delivery_guy_id,
                start_date=start_date,
                end_date=end_date
            )
        elif period == 'monthly':
            # For monthly period, show daily breakdown
            daily_breakdown = EarningsManagement.get_daily_breakdown(
                delivery_guy_id=delivery_guy_id,
                start_date=start_date,
                end_date=end_date
            )
        else:  # daily
            # For daily period, show daily breakdown
            daily_breakdown = EarningsManagement.get_daily_breakdown(
                delivery_guy_id=delivery_guy_id,
                start_date=start_date,
                end_date=end_date
            )
        
        # Format results
        summary_data = {}
        for item in summary:
            summary_data[item.payment_type] = {
                'total_amount': float(item.total_amount),
                'count': item.count
            }
        
        weekly_data = []
        for item in weekly_breakdown:
            weekly_data.append({
                'week_start': item.week_start.isoformat() if item.week_start else None,
                'payment_type': item.payment_type,
                'total_amount': float(item.total_amount),
                'count': item.count
            })
        
        daily_data = []
        for item in daily_breakdown:
            daily_data.append({
                'date': item.start_date.isoformat() if item.start_date else None,
                'payment_type': item.payment_type,
                'total_amount': float(item.total_amount),
                'count': item.count
            })
        
        return jsonify({
            "success": True,
            "summary": summary_data,
            "weekly_breakdown": weekly_data,
            "daily_breakdown": daily_data,
            "period": period
        }), 200
        
    except Exception as e:
        print(f"Get admin earnings summary error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@earnings_management_bp.route("/admin/delivery-guys", methods=["GET"])
@require_admin_auth
def get_delivery_guys():
    """Get list of delivery guys for dropdown"""
    try:
        # Get all delivery guys, not just active ones
        delivery_guys = DeliveryOnboarding.query.all()
        
        result = []
        for dg in delivery_guys:
            # Create full name from first_name and last_name
            full_name = f"{dg.first_name or ''} {dg.last_name or ''}".strip()
            if not full_name:
                full_name = 'Unknown'
            
            result.append({
                'id': dg.id,
                'name': full_name,
                'email': dg.email or 'No email',
                'phone': dg.primary_number or 'No phone',
                'status': dg.status or 'unknown'
            })
        
        return jsonify({
            "success": True,
            "delivery_guys": result
        }), 200
        
    except Exception as e:
        print(f"Get delivery guys error: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500
