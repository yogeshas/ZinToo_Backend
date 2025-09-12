# routes/delivery_leave_requests.py
from flask import Blueprint, request, jsonify
from models.delivery_leave_request import DeliveryLeaveRequest
from models.delivery_onboarding import DeliveryOnboarding
from extensions import db
from datetime import datetime, date
from functools import wraps

delivery_leave_requests_bp = Blueprint("delivery_leave_requests", __name__)

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
            return jsonify({"error": "Admin authentication failed"}), 401
    
    return decorated_function

# ============================================================================
# DELIVERY GUY ENDPOINTS
# ============================================================================

@delivery_leave_requests_bp.route("/delivery/leave-requests", methods=["GET"])
@require_delivery_auth
def get_delivery_leave_requests():
    """Get all leave requests for a delivery guy"""
    try:
        delivery_guy_id = request.delivery_guy_id
        
        # Get all leave requests for this delivery guy
        leave_requests = DeliveryLeaveRequest.query.filter_by(
            delivery_guy_id=delivery_guy_id
        ).order_by(DeliveryLeaveRequest.created_at.desc()).all()
        
        result = [request.as_dict() for request in leave_requests]
        
        return jsonify({
            "success": True,
            "leave_requests": result,
            "total": len(result)
        }), 200
        
    except Exception as e:
        print(f"Get leave requests error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@delivery_leave_requests_bp.route("/delivery/leave-requests", methods=["POST"])
@require_delivery_auth
def create_leave_request():
    """Create a new leave request"""
    try:
        delivery_guy_id = request.delivery_guy_id
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate required fields
        start_date_str = data.get("start_date")
        end_date_str = data.get("end_date")
        reason = data.get("reason")
        
        if not all([start_date_str, end_date_str, reason]):
            return jsonify({"error": "start_date, end_date, and reason are required"}), 400
        
        # Parse dates
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
        
        # Validate dates
        if start_date < date.today():
            return jsonify({"error": "Start date cannot be in the past"}), 400
        
        if end_date < start_date:
            return jsonify({"error": "End date cannot be before start date"}), 400
        
        # Check for overlapping leave requests
        overlapping = DeliveryLeaveRequest.query.filter(
            DeliveryLeaveRequest.delivery_guy_id == delivery_guy_id,
            DeliveryLeaveRequest.status.in_(["pending", "approved"]),
            DeliveryLeaveRequest.start_date <= end_date,
            DeliveryLeaveRequest.end_date >= start_date
        ).first()
        
        if overlapping:
            return jsonify({"error": "You already have a leave request for this period"}), 400
        
        # Create new leave request
        leave_request = DeliveryLeaveRequest(
            delivery_guy_id=delivery_guy_id,
            start_date=start_date,
            end_date=end_date,
            reason=reason,
            status="pending"
        )
        
        db.session.add(leave_request)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Leave request submitted successfully",
            "leave_request": leave_request.as_dict()
        }), 201
        
    except Exception as e:
        print(f"Create leave request error: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "Internal server error"}), 500

# ============================================================================
# ADMIN ENDPOINTS
# ============================================================================

@delivery_leave_requests_bp.route("/admin/leave-requests", methods=["GET"])
@require_admin_auth
def get_all_leave_requests():
    """Get all leave requests for admin review"""
    try:
        status = request.args.get('status', 'all')
        
        # Base query
        query = DeliveryLeaveRequest.query
        
        # Filter by status if specified
        if status != 'all':
            query = query.filter_by(status=status)
        
        # Order by creation date (newest first)
        leave_requests = query.order_by(DeliveryLeaveRequest.created_at.desc()).all()
        
        result = [request.as_dict() for request in leave_requests]
        
        return jsonify({
            "success": True,
            "leave_requests": result,
            "total": len(result)
        }), 200
        
    except Exception as e:
        print(f"Get all leave requests error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@delivery_leave_requests_bp.route("/admin/leave-requests/<int:request_id>/approve", methods=["POST"])
@require_admin_auth
def approve_leave_request(request_id):
    """Approve a leave request"""
    try:
        admin_id = request.admin_id
        data = request.get_json() or {}
        admin_notes = data.get("admin_notes", "")
        
        # Find the leave request
        leave_request = DeliveryLeaveRequest.query.get(request_id)
        if not leave_request:
            return jsonify({"error": "Leave request not found"}), 404
        
        if leave_request.status != "pending":
            return jsonify({"error": "Leave request has already been reviewed"}), 400
        
        # Update leave request
        leave_request.status = "approved"
        leave_request.admin_notes = admin_notes
        leave_request.reviewed_at = datetime.utcnow()
        leave_request.reviewed_by = admin_id
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Leave request approved successfully",
            "leave_request": leave_request.as_dict()
        }), 200
        
    except Exception as e:
        print(f"Approve leave request error: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "Internal server error"}), 500

@delivery_leave_requests_bp.route("/admin/leave-requests/<int:request_id>/reject", methods=["POST"])
@require_admin_auth
def reject_leave_request(request_id):
    """Reject a leave request"""
    try:
        admin_id = request.admin_id
        data = request.get_json() or {}
        admin_notes = data.get("admin_notes", "")
        
        if not admin_notes:
            return jsonify({"error": "Admin notes are required for rejection"}), 400
        
        # Find the leave request
        leave_request = DeliveryLeaveRequest.query.get(request_id)
        if not leave_request:
            return jsonify({"error": "Leave request not found"}), 404
        
        if leave_request.status != "pending":
            return jsonify({"error": "Leave request has already been reviewed"}), 400
        
        # Update leave request
        leave_request.status = "rejected"
        leave_request.admin_notes = admin_notes
        leave_request.reviewed_at = datetime.utcnow()
        leave_request.reviewed_by = admin_id
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Leave request rejected successfully",
            "leave_request": leave_request.as_dict()
        }), 200
        
    except Exception as e:
        print(f"Reject leave request error: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "Internal server error"}), 500
