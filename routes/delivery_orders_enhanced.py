# routes/delivery_orders_enhanced.py
from flask import Blueprint, request, jsonify
from models.order import Order, OrderItem
from models.exchange import Exchange
from models.delivery_track import DeliveryTrack
from models.delivery_onboarding import DeliveryOnboarding
from extensions import db
from datetime import datetime, timedelta
import json
import random
import string

delivery_orders_enhanced_bp = Blueprint("delivery_orders_enhanced", __name__)

# Store OTPs temporarily (in production, use Redis or database)
otp_storage = {}

def generate_otp():
    """Generate a 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))

def send_otp_email(customer_email, otp):
    """Send OTP email to customer (simplified implementation)"""
    try:
        # TODO: Implement actual email sending
        print(f"OTP for {customer_email}: {otp}")
        return True
    except Exception as e:
        print(f"Error sending OTP email: {e}")
        return False

def require_delivery_auth(f):
    """Decorator to require delivery guy authentication"""
    from functools import wraps
    from services.delivery_auth_service import verify_auth_token
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Missing or invalid authorization header"}), 401
        
        token = auth_header.split(' ')[1]
        token_validation = verify_auth_token(token)
        if not token_validation["success"]:
            return jsonify({"error": token_validation["message"]}), 401
        
        user = token_validation["user"]
        email = user.get("email")
        
        # Get delivery guy ID from onboarding
        delivery_guy = DeliveryOnboarding.query.filter_by(email=email).first()
        if not delivery_guy:
            return jsonify({"error": "Delivery guy not found"}), 404
        
        if delivery_guy.status != "approved":
            return jsonify({"error": "Delivery guy not approved"}), 403
        
        # Add delivery guy ID to request
        request.delivery_guy_id = delivery_guy.id
        return f(*args, **kwargs)
    
    return decorated_function

@delivery_orders_enhanced_bp.route("/orders", methods=["GET"])
@require_delivery_auth
def get_delivery_orders():
    """Get all orders assigned to delivery guy"""
    try:
        delivery_guy_id = request.delivery_guy_id
        status = request.args.get('status', 'all')
        
        # Base query for orders assigned to this delivery guy
        query = Order.query.filter_by(delivery_guy_id=delivery_guy_id)
        
        # Filter by status if specified
        if status != 'all':
            query = query.filter_by(status=status)
        
        orders = query.order_by(Order.created_at.desc()).all()
        
        result = []
        for order in orders:
            order_data = order.as_dict()
            # Add customer information
            if order.customer:
                order_data['customer'] = {
                    'id': order.customer.id,
                    'name': order.customer.username,
                    'email': order.customer.email,
                    'phone': order.customer.phone_number_enc.decode('utf-8') if order.customer.phone_number_enc else None
                }
            
            # Add order items with product information including barcode
            order_items = []
            for item in order.order_items:
                item_data = item.as_dict()
                # Add product information including barcode
                if item.product:
                    item_data['product'] = {
                        'id': item.product.id,
                        'name': item.product.pname,
                        'barcode': item.product.barcode,
                        'price': item.product.price,
                        'image': item.product.image
                    }
                order_items.append(item_data)
            order_data['order_items'] = order_items
            
            result.append(order_data)
        
        return jsonify({
            "success": True,
            "orders": result,
            "total": len(result),
            "delivery_guy_id": delivery_guy_id
        }), 200
        
    except Exception as e:
        print(f"Get delivery orders error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@delivery_orders_enhanced_bp.route("/exchanges", methods=["GET"])
@require_delivery_auth
def get_delivery_exchanges():
    """Get all exchanges assigned to delivery guy"""
    try:
        delivery_guy_id = request.delivery_guy_id
        
        exchanges = Exchange.query.filter_by(delivery_guy_id=delivery_guy_id)\
            .order_by(Exchange.created_at.desc()).all()
        
        result = []
        for exchange in exchanges:
            exchange_data = exchange.as_dict()
            # Add customer information
            if exchange.order and exchange.order.customer:
                exchange_data['customer'] = {
                    'id': exchange.order.customer.id,
                    'name': exchange.order.customer.username,
                    'email': exchange.order.customer.email,
                    'phone': exchange.order.customer.phone_number_enc.decode('utf-8') if exchange.order.customer.phone_number_enc else None
                }
            # Add product information
            if exchange.product:
                exchange_data['product'] = {
                    'id': exchange.product.id,
                    'name': exchange.product.pname,
                    'barcode': exchange.product.barcode,
                    'price': exchange.product.price
                }
            result.append(exchange_data)
        
        return jsonify({
            "success": True,
            "exchanges": result,
            "total": len(result),
            "delivery_guy_id": delivery_guy_id
        }), 200
        
    except Exception as e:
        print(f"Get delivery exchanges error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@delivery_orders_enhanced_bp.route("/cancelled-items", methods=["GET"])
@require_delivery_auth
def get_cancelled_order_items():
    """Get all cancelled order items assigned to delivery guy"""
    try:
        delivery_guy_id = request.delivery_guy_id
        
        # Get cancelled order items that are assigned to this delivery guy
        cancelled_items = OrderItem.query.filter_by(
            delivery_guy_id=delivery_guy_id,
            status='cancelled'
        ).order_by(OrderItem.updated_at.desc()).all()
        
        result = []
        for item in cancelled_items:
            item_data = item.to_dict()
            # Add order information
            if item.order:
                item_data['order'] = {
                    'id': item.order.id,
                    'order_number': item.order.order_number,
                    'status': item.order.status,
                    'total_amount': item.order.total_amount
                }
                # Add customer information
                if item.order.customer:
                    item_data['customer'] = {
                        'id': item.order.customer.id,
                        'name': item.order.customer.username,
                        'email': item.order.customer.email,
                        'phone': item.order.customer.phone_number_enc.decode('utf-8') if item.order.customer.phone_number_enc else None
                    }
            # Add product information
            if item.product:
                item_data['product'] = {
                    'id': item.product.id,
                    'name': item.product.pname,
                    'barcode': item.product.barcode,
                    'price': item.product.price
                }
            result.append(item_data)
        
        return jsonify({
            "success": True,
            "cancelled_items": result,
            "total": len(result),
            "delivery_guy_id": delivery_guy_id
        }), 200
        
    except Exception as e:
        print(f"Get cancelled order items error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@delivery_orders_enhanced_bp.route("/approved", methods=["GET"])
@require_delivery_auth
def get_approved_items():
    """Get all approved items (orders, exchanges, cancelled items)"""
    try:
        delivery_guy_id = request.delivery_guy_id
        
        # Get approved delivery tracks
        approved_tracks = DeliveryTrack.query.filter_by(
            delivery_guy_id=delivery_guy_id,
            status='approved'
        ).order_by(DeliveryTrack.created_at.desc()).all()
        
        result = []
        for track in approved_tracks:
            item_data = {
                'id': track.id,
                'type': 'delivery_track',
                'status': track.status,
                'notes': track.notes,
                'created_at': track.created_at.isoformat() if track.created_at else None,
                'delivery_guy_id': track.delivery_guy_id
            }
            
            # Add order information if available
            if track.order:
                item_data['order'] = track.order.as_dict()
                if track.order.customer:
                    item_data['customer'] = {
                        'id': track.order.customer.id,
                        'name': track.order.customer.username,
                        'email': track.order.customer.email,
                        'phone': track.order.customer.phone_number_enc.decode('utf-8') if track.order.customer.phone_number_enc else None
                    }
            
            # Add exchange information if available
            if track.exchange:
                item_data['exchange'] = track.exchange.as_dict()
                if track.exchange.order and track.exchange.order.customer:
                    item_data['customer'] = {
                        'id': track.exchange.order.customer.id,
                        'name': track.exchange.order.customer.username,
                        'email': track.exchange.order.customer.email,
                        'phone': track.exchange.order.customer.phone_number_enc.decode('utf-8') if track.exchange.order.customer.phone_number_enc else None
                    }
            
            result.append(item_data)
        
        return jsonify({
            "success": True,
            "approved_items": result,
            "total": len(result),
            "delivery_guy_id": delivery_guy_id
        }), 200
        
    except Exception as e:
        print(f"Get approved items error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@delivery_orders_enhanced_bp.route("/rejected", methods=["GET"])
@require_delivery_auth
def get_rejected_items():
    """Get all rejected items (orders, exchanges, cancelled items)"""
    try:
        delivery_guy_id = request.delivery_guy_id
        
        # Get rejected delivery tracks
        rejected_tracks = DeliveryTrack.query.filter_by(
            delivery_guy_id=delivery_guy_id,
            status='rejected'
        ).order_by(DeliveryTrack.created_at.desc()).all()
        
        result = []
        for track in rejected_tracks:
            item_data = {
                'id': track.id,
                'type': 'delivery_track',
                'status': track.status,
                'notes': track.notes,
                'created_at': track.created_at.isoformat() if track.created_at else None,
                'delivery_guy_id': track.delivery_guy_id
            }
            
            # Add order information if available
            if track.order:
                item_data['order'] = track.order.as_dict()
                if track.order.customer:
                    item_data['customer'] = {
                        'id': track.order.customer.id,
                        'name': track.order.customer.username,
                        'email': track.order.customer.email,
                        'phone': track.order.customer.phone_number_enc.decode('utf-8') if track.order.customer.phone_number_enc else None
                    }
            
            # Add exchange information if available
            if track.exchange:
                item_data['exchange'] = track.exchange.as_dict()
                if track.exchange.order and track.exchange.order.customer:
                    item_data['customer'] = {
                        'id': track.exchange.order.customer.id,
                        'name': track.exchange.order.customer.username,
                        'email': track.exchange.order.customer.email,
                        'phone': track.exchange.order.customer.phone_number_enc.decode('utf-8') if track.exchange.order.customer.phone_number_enc else None
                    }
            
            result.append(item_data)
        
        return jsonify({
            "success": True,
            "rejected_items": result,
            "total": len(result),
            "delivery_guy_id": delivery_guy_id
        }), 200
        
    except Exception as e:
        print(f"Get rejected items error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@delivery_orders_enhanced_bp.route("/orders/<int:order_id>/approve", methods=["POST"])
@require_delivery_auth
def approve_order(order_id):
    """Approve an order and create delivery track"""
    try:
        delivery_guy_id = request.delivery_guy_id
        data = request.get_json() or {}
        reason = data.get("reason", "Order approved by delivery personnel")
        
        # Verify order is assigned to this delivery guy
        order = Order.query.filter_by(id=order_id, delivery_guy_id=delivery_guy_id).first()
        if not order:
            return jsonify({"error": "Order not found or not assigned to you"}), 404
        
        # Update order status
        order.status = "approved"
        order.updated_at = datetime.now()
        db.session.commit()
        
        # Create delivery track entry
        delivery_track = DeliveryTrack(
            delivery_guy_id=delivery_guy_id,
            order_id=order_id,
            status="approved",
            notes=reason,
            created_at=datetime.now()
        )
        db.session.add(delivery_track)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Order approved successfully",
            "order": order.as_dict(),
            "delivery_track_id": delivery_track.id
        }), 200
        
    except Exception as e:
        print(f"Approve order error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@delivery_orders_enhanced_bp.route("/orders/<int:order_id>/reject", methods=["POST"])
@require_delivery_auth
def reject_order(order_id):
    """Reject an order and create delivery track"""
    try:
        delivery_guy_id = request.delivery_guy_id
        data = request.get_json() or {}
        reason = data.get("reason", "Order rejected by delivery personnel")
        
        # Verify order is assigned to this delivery guy
        order = Order.query.filter_by(id=order_id, delivery_guy_id=delivery_guy_id).first()
        if not order:
            return jsonify({"error": "Order not found or not assigned to you"}), 404
        
        # Update order status
        order.status = "rejected"
        order.updated_at = datetime.now()
        db.session.commit()
        
        # Create delivery track entry
        delivery_track = DeliveryTrack(
            delivery_guy_id=delivery_guy_id,
            order_id=order_id,
            status="rejected",
            notes=reason,
            created_at=datetime.now()
        )
        db.session.add(delivery_track)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Order rejected successfully",
            "order": order.as_dict(),
            "delivery_track_id": delivery_track.id
        }), 200
        
    except Exception as e:
        print(f"Reject order error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@delivery_orders_enhanced_bp.route("/exchanges/<int:exchange_id>/approve", methods=["POST"])
@require_delivery_auth
def approve_exchange(exchange_id):
    """Approve an exchange and create delivery track"""
    try:
        delivery_guy_id = request.delivery_guy_id
        data = request.get_json() or {}
        reason = data.get("reason", "Exchange approved by delivery personnel")
        
        # Verify exchange is assigned to this delivery guy
        exchange = Exchange.query.filter_by(id=exchange_id, delivery_guy_id=delivery_guy_id).first()
        if not exchange:
            return jsonify({"error": "Exchange not found or not assigned to you"}), 404
        
        # Update exchange status
        exchange.status = "approved"
        exchange.updated_at = datetime.now()
        db.session.commit()
        
        # Create delivery track entry
        delivery_track = DeliveryTrack(
            delivery_guy_id=delivery_guy_id,
            exchange_id=exchange_id,
            status="approved",
            notes=reason,
            created_at=datetime.now()
        )
        db.session.add(delivery_track)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Exchange approved successfully",
            "exchange": exchange.as_dict(),
            "delivery_track_id": delivery_track.id
        }), 200
        
    except Exception as e:
        print(f"Approve exchange error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@delivery_orders_enhanced_bp.route("/exchanges/<int:exchange_id>/reject", methods=["POST"])
@require_delivery_auth
def reject_exchange(exchange_id):
    """Reject an exchange and create delivery track"""
    try:
        delivery_guy_id = request.delivery_guy_id
        data = request.get_json() or {}
        reason = data.get("reason", "Exchange rejected by delivery personnel")
        
        # Verify exchange is assigned to this delivery guy
        exchange = Exchange.query.filter_by(id=exchange_id, delivery_guy_id=delivery_guy_id).first()
        if not exchange:
            return jsonify({"error": "Exchange not found or not assigned to you"}), 404
        
        # Update exchange status
        exchange.status = "rejected"
        exchange.updated_at = datetime.now()
        db.session.commit()
        
        # Create delivery track entry
        delivery_track = DeliveryTrack(
            delivery_guy_id=delivery_guy_id,
            exchange_id=exchange_id,
            status="rejected",
            notes=reason,
            created_at=datetime.now()
        )
        db.session.add(delivery_track)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Exchange rejected successfully",
            "exchange": exchange.as_dict(),
            "delivery_track_id": delivery_track.id
        }), 200
        
    except Exception as e:
        print(f"Reject exchange error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

# ============================================================================
# DELIVERY STATUS UPDATE ENDPOINTS
# ============================================================================

@delivery_orders_enhanced_bp.route("/orders/<int:order_id>/out-for-delivery", methods=["POST"])
@require_delivery_auth
def mark_order_out_for_delivery(order_id):
    """Mark order as out for delivery"""
    try:
        delivery_guy_id = request.delivery_guy_id
        
        # Verify order is assigned to this delivery guy
        order = Order.query.filter_by(id=order_id, delivery_guy_id=delivery_guy_id).first()
        if not order:
            return jsonify({"error": "Order not found or not assigned to you"}), 404
        
        # Update order status
        order.status = "out_for_delivery"
        order.updated_at = datetime.now()
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Order marked as out for delivery",
            "order": order.as_dict()
        }), 200
        
    except Exception as e:
        print(f"Mark order out for delivery error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@delivery_orders_enhanced_bp.route("/orders/<int:order_id>/delivered", methods=["POST"])
@require_delivery_auth
def mark_order_delivered(order_id):
    """Mark order as delivered"""
    try:
        delivery_guy_id = request.delivery_guy_id
        
        # Verify order is assigned to this delivery guy
        order = Order.query.filter_by(id=order_id, delivery_guy_id=delivery_guy_id).first()
        if not order:
            return jsonify({"error": "Order not found or not assigned to you"}), 404
        
        # Update order status
        order.status = "delivered"
        order.updated_at = datetime.now()
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Order marked as delivered",
            "order": order.as_dict()
        }), 200
        
    except Exception as e:
        print(f"Mark order delivered error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@delivery_orders_enhanced_bp.route("/exchanges/<int:exchange_id>/out-for-delivery", methods=["POST"])
@require_delivery_auth
def mark_exchange_out_for_delivery(exchange_id):
    """Mark exchange as out for delivery"""
    try:
        delivery_guy_id = request.delivery_guy_id
        
        # Verify exchange is assigned to this delivery guy
        exchange = Exchange.query.filter_by(id=exchange_id, delivery_guy_id=delivery_guy_id).first()
        if not exchange:
            return jsonify({"error": "Exchange not found or not assigned to you"}), 404
        
        # Update exchange status
        exchange.status = "out_for_delivery"
        exchange.updated_at = datetime.now()
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Exchange marked as out for delivery",
            "exchange": exchange.as_dict()
        }), 200
        
    except Exception as e:
        print(f"Mark exchange out for delivery error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@delivery_orders_enhanced_bp.route("/exchanges/<int:exchange_id>/delivered", methods=["POST"])
@require_delivery_auth
def mark_exchange_delivered(exchange_id):
    """Mark exchange as delivered"""
    try:
        delivery_guy_id = request.delivery_guy_id
        
        # Verify exchange is assigned to this delivery guy
        exchange = Exchange.query.filter_by(id=exchange_id, delivery_guy_id=delivery_guy_id).first()
        if not exchange:
            return jsonify({"error": "Exchange not found or not assigned to you"}), 404
        
        # Update exchange status
        exchange.status = "delivered"
        exchange.updated_at = datetime.now()
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Exchange marked as delivered",
            "exchange": exchange.as_dict()
        }), 200
        
    except Exception as e:
        print(f"Mark exchange delivered error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

# ============================================================================
# OTP ENDPOINTS
# ============================================================================

@delivery_orders_enhanced_bp.route("/send-otp", methods=["POST"])
@require_delivery_auth
def send_delivery_otp():
    """Send OTP to customer for delivery verification"""
    try:
        delivery_guy_id = request.delivery_guy_id
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        item_id = data.get("item_id")
        item_type = data.get("item_type")  # 'orders', 'exchanges', 'cancelled_items'
        
        if not item_id or not item_type:
            return jsonify({"error": "item_id and item_type are required"}), 400
        
        # Get customer information based on item type
        customer_email = None
        customer_phone = None
        
        if item_type == 'orders':
            order = Order.query.filter_by(id=item_id, delivery_guy_id=delivery_guy_id).first()
            if not order:
                return jsonify({"error": "Order not found or not assigned to you"}), 404
            if order.customer:
                customer_email = order.customer.email
                customer_phone = order.customer.phone_number_enc.decode('utf-8') if order.customer.phone_number_enc else None
                
        elif item_type == 'exchanges':
            exchange = Exchange.query.filter_by(id=item_id, delivery_guy_id=delivery_guy_id).first()
            if not exchange:
                return jsonify({"error": "Exchange not found or not assigned to you"}), 404
            if exchange.order and exchange.order.customer:
                customer_email = exchange.order.customer.email
                customer_phone = exchange.order.customer.phone_number_enc.decode('utf-8') if exchange.order.customer.phone_number_enc else None
                
        elif item_type == 'cancelled_items':
            order_item = OrderItem.query.filter_by(id=item_id, delivery_guy_id=delivery_guy_id).first()
            if not order_item:
                return jsonify({"error": "Order item not found or not assigned to you"}), 404
            if order_item.order and order_item.order.customer:
                customer_email = order_item.order.customer.email
                customer_phone = order_item.order.customer.phone_number_enc.decode('utf-8') if order_item.order.customer.phone_number_enc else None
        
        if not customer_email:
            return jsonify({"error": "Customer email not found"}), 400
        
        # Generate and store OTP
        otp = generate_otp()
        otp_key = f"{item_type}_{item_id}_{delivery_guy_id}"
        otp_storage[otp_key] = {
            "otp": otp,
            "expires_at": datetime.now() + timedelta(minutes=10),
            "customer_email": customer_email,
            "customer_phone": customer_phone
        }
        
        # Send OTP email
        if send_otp_email(customer_email, otp):
            return jsonify({
                "success": True,
                "message": f"OTP sent to {customer_email}",
                "expires_in": 600,  # 10 minutes in seconds
                "otp": otp  # For testing purposes - remove in production
            }), 200
        else:
            return jsonify({"error": "Failed to send OTP email"}), 500
            
    except Exception as e:
        print(f"Send OTP error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@delivery_orders_enhanced_bp.route("/verify-otp", methods=["POST"])
@require_delivery_auth
def verify_delivery_otp():
    """Verify OTP for delivery confirmation"""
    try:
        delivery_guy_id = request.delivery_guy_id
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        item_id = data.get("item_id")
        item_type = data.get("item_type")
        otp = data.get("otp")
        
        if not all([item_id, item_type, otp]):
            return jsonify({"error": "item_id, item_type, and otp are required"}), 400
        
        # Check OTP
        otp_key = f"{item_type}_{item_id}_{delivery_guy_id}"
        stored_otp_data = otp_storage.get(otp_key)
        
        if not stored_otp_data:
            return jsonify({"error": "OTP not found or expired"}), 400
        
        if datetime.now() > stored_otp_data["expires_at"]:
            del otp_storage[otp_key]
            return jsonify({"error": "OTP expired"}), 400
        
        if stored_otp_data["otp"] != otp:
            return jsonify({"error": "Invalid OTP"}), 400
        
        # OTP is valid, remove it from storage
        del otp_storage[otp_key]
        
        return jsonify({
            "success": True,
            "message": "OTP verified successfully"
        }), 200
        
    except Exception as e:
        print(f"Verify OTP error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
