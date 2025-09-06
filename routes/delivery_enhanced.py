from flask import Blueprint, request, jsonify
from functools import wraps
from services.delivery_auth_service import verify_auth_token
from services.delivery_order_service import (
    get_orders_for_delivery_guy,
    get_order_detail_for_delivery_guy,
    approve_order_by_delivery_guy,
    reject_order_by_delivery_guy,
    serialize_orders_with_customer,
    out_for_delivery_order_by_delivery_guy,
    delivered_order_by_delivery_guy,
    get_order_delivery_purpose
)
from services.exchange_service import get_exchanges_for_delivery_guy
from services.order_items_service import get_cancelled_order_items_for_delivery_guy
from utils.crypto import encrypt_payload, decrypt_payload
from models.delivery_onboarding import DeliveryOnboarding
from models.order import Order
from models.exchange import Exchange
from models.order import OrderItem
from models.delivery_track import DeliveryTrack
from extensions import db
import random
import string
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

delivery_enhanced_bp = Blueprint("delivery_enhanced", __name__)

def require_delivery_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid authorization header"}), 401

        token = auth_header.split(" ")[1]
        result = verify_auth_token(token)
        if not result["success"]:
            return jsonify({"error": result["message"]}), 401

        # Fetch onboarding and ensure approved
        delivery_guy_id = result["user"].get("delivery_guy_id")
        if not delivery_guy_id:
            return jsonify({"error": "Delivery guy not onboarded"}), 403

        onboarding = DeliveryOnboarding.query.get(delivery_guy_id)
        if not onboarding or onboarding.status != "approved":
            return jsonify({"error": "Delivery guy not approved"}), 403

        request.delivery_guy_id = delivery_guy_id
        return f(*args, **kwargs)

    return decorated

def generate_otp():
    """Generate a 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))

def send_otp_email(customer_email, otp):
    """Send OTP to customer email"""
    try:
        # Email configuration (you should move this to environment variables)
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        smtp_username = os.getenv('SMTP_USERNAME', '')
        smtp_password = os.getenv('SMTP_PASSWORD', '')
        
        if not smtp_username or not smtp_password:
            print("SMTP credentials not configured")
            return False
            
        # Create message
        msg = MIMEMultipart()
        msg['From'] = smtp_username
        msg['To'] = customer_email
        msg['Subject'] = "ZinToo Delivery Verification Code"
        
        body = f"""
        <html>
        <body>
            <h2>ZinToo Delivery Verification</h2>
            <p>Your delivery verification code is:</p>
            <h1 style="color: #007bff; font-size: 32px; text-align: center;">{otp}</h1>
            <p>This code will expire in 10 minutes.</p>
            <p>Please provide this code to the delivery personnel to complete your order delivery.</p>
            <br>
            <p>Thank you for choosing ZinToo!</p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        text = msg.as_string()
        server.sendmail(smtp_username, customer_email, text)
        server.quit()
        
        return True
    except Exception as e:
        print(f"Error sending OTP email: {str(e)}")
        return False

# Store OTPs temporarily (in production, use Redis or database)
otp_storage = {}

@delivery_enhanced_bp.route("/orders/scan-barcode", methods=["POST"])
@require_delivery_auth
def scan_barcode():
    """Scan barcode and get order details"""
    try:
        delivery_guy_id = request.delivery_guy_id
        data = request.get_json()
        barcode = data.get("barcode")
        
        if not barcode:
            return jsonify({"error": "Barcode is required"}), 400
        
        # Find order by barcode (assuming barcode is stored in order or product)
        # You may need to adjust this based on your barcode implementation
        order = Order.query.filter_by(delivery_guy_id=delivery_guy_id).join(
            OrderItem, Order.id == OrderItem.order_id
        ).filter(
            OrderItem.product_barcode == barcode
        ).first()
        
        if not order:
            return jsonify({"error": "Order not found or not assigned to you"}), 404
        
        # Get order details
        order_detail = get_order_detail_for_delivery_guy(delivery_guy_id, order.id)
        
        return jsonify({
            "success": True,
            "order": order_detail,
            "message": "Order found successfully"
        }), 200
        
    except Exception as e:
        print(f"Barcode scan error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@delivery_enhanced_bp.route("/orders/<int:order_id>/send-otp", methods=["POST"])
@require_delivery_auth
def send_delivery_otp(order_id):
    """Send OTP to customer for order verification"""
    try:
        delivery_guy_id = request.delivery_guy_id
        
        # Verify order is assigned to this delivery guy
        order = Order.query.filter_by(id=order_id, delivery_guy_id=delivery_guy_id).first()
        if not order:
            return jsonify({"error": "Order not found or not assigned to you"}), 404
        
        # Get customer email
        customer_email = order.customer.email if order.customer else None
        if not customer_email:
            return jsonify({"error": "Customer email not found"}), 400
        
        # Generate and store OTP
        otp = generate_otp()
        otp_storage[f"{order_id}_{delivery_guy_id}"] = {
            "otp": otp,
            "expires_at": datetime.now() + timedelta(minutes=10),
            "customer_email": customer_email
        }
        
        # Send OTP email
        if send_otp_email(customer_email, otp):
            return jsonify({
                "success": True,
                "message": f"OTP sent to {customer_email}",
                "expires_in": 600  # 10 minutes in seconds
            }), 200
        else:
            return jsonify({"error": "Failed to send OTP email"}), 500
            
    except Exception as e:
        print(f"Send OTP error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@delivery_enhanced_bp.route("/orders/<int:order_id>/verify-otp", methods=["POST"])
@require_delivery_auth
def verify_delivery_otp(order_id):
    """Verify OTP and mark order as delivered"""
    try:
        delivery_guy_id = request.delivery_guy_id
        data = request.get_json()
        otp = data.get("otp")
        
        if not otp:
            return jsonify({"error": "OTP is required"}), 400
        
        # Verify order is assigned to this delivery guy
        order = Order.query.filter_by(id=order_id, delivery_guy_id=delivery_guy_id).first()
        if not order:
            return jsonify({"error": "Order not found or not assigned to you"}), 404
        
        # Check OTP
        otp_key = f"{order_id}_{delivery_guy_id}"
        stored_otp_data = otp_storage.get(otp_key)
        
        if not stored_otp_data:
            return jsonify({"error": "OTP not found or expired"}), 400
        
        if datetime.now() > stored_otp_data["expires_at"]:
            del otp_storage[otp_key]
            return jsonify({"error": "OTP expired"}), 400
        
        if stored_otp_data["otp"] != otp:
            return jsonify({"error": "Invalid OTP"}), 400
        
        # OTP verified, mark order as delivered
        delivered_reason = f"Order delivered and verified with OTP at {datetime.now()}"
        result = delivered_order_by_delivery_guy(delivery_guy_id, order_id, delivered_reason)
        
        # Clean up OTP
        del otp_storage[otp_key]
        
        if result["success"]:
            return jsonify({
                "success": True,
                "message": "Order delivered successfully",
                "order": result["order"]
            }), 200
        else:
            return jsonify({"error": result["message"]}), 400
            
    except Exception as e:
        print(f"Verify OTP error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@delivery_enhanced_bp.route("/orders/combined", methods=["GET"])
@require_delivery_auth
def get_combined_orders():
    """Get all orders, exchanges, and cancelled items combined"""
    try:
        delivery_guy_id = request.delivery_guy_id
        status = request.args.get("status", "all")  # all, approved, rejected
        
        combined_data = {
            "orders": [],
            "exchanges": [],
            "cancelled_items": [],
            "delivery_tracks": []
        }
        
        if status == "all":
            # Get all orders
            orders = get_orders_for_delivery_guy(delivery_guy_id, "all")
            combined_data["orders"] = serialize_orders_with_customer(orders)
            
            # Get all exchanges
            exchanges = get_exchanges_for_delivery_guy(delivery_guy_id)
            combined_data["exchanges"] = exchanges
            
            # Get all cancelled order items
            cancelled_items = get_cancelled_order_items_for_delivery_guy(delivery_guy_id)
            combined_data["cancelled_items"] = cancelled_items
            
        elif status == "approved":
            # Get approved orders from delivery_track
            delivery_tracks = DeliveryTrack.query.filter_by(
                delivery_guy_id=delivery_guy_id,
                status="approved"
            ).all()
            
            for track in delivery_tracks:
                if track.order_id:
                    order_detail = get_order_detail_for_delivery_guy(delivery_guy_id, track.order_id)
                    if order_detail:
                        combined_data["orders"].append(order_detail)
                elif track.exchange_id:
                    exchange = Exchange.query.get(track.exchange_id)
                    if exchange:
                        combined_data["exchanges"].append(exchange.to_dict())
                        
        elif status == "rejected":
            # Get rejected orders from delivery_track
            delivery_tracks = DeliveryTrack.query.filter_by(
                delivery_guy_id=delivery_guy_id,
                status="rejected"
            ).all()
            
            for track in delivery_tracks:
                if track.order_id:
                    order_detail = get_order_detail_for_delivery_guy(delivery_guy_id, track.order_id)
                    if order_detail:
                        combined_data["orders"].append(order_detail)
                elif track.exchange_id:
                    exchange = Exchange.query.get(track.exchange_id)
                    if exchange:
                        combined_data["exchanges"].append(exchange.to_dict())
        
        return jsonify({
            "success": True,
            "data": combined_data,
            "status": status
        }), 200
        
    except Exception as e:
        print(f"Get combined orders error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@delivery_enhanced_bp.route("/orders/<int:order_id>/approve", methods=["POST"])
@require_delivery_auth
def approve_order_enhanced(order_id):
    """Approve an order and create delivery track"""
    try:
        delivery_guy_id = request.delivery_guy_id
        data = request.get_json() or {}
        approval_reason = data.get("reason", "Order approved by delivery personnel")
        
        # Approve the order
        result = approve_order_by_delivery_guy(delivery_guy_id, order_id)
        
        if result["success"]:
            # Create delivery track entry
            delivery_track = DeliveryTrack(
                delivery_guy_id=delivery_guy_id,
                order_id=order_id,
                status="approved",
                notes=approval_reason,
                created_at=datetime.now()
            )
            db.session.add(delivery_track)
            db.session.commit()
            
            return jsonify({
                "success": True,
                "message": "Order approved successfully",
                "order": result["order"],
                "delivery_track_id": delivery_track.id
            }), 200
        else:
            return jsonify({"error": result["message"]}), 400
            
    except Exception as e:
        print(f"Approve order enhanced error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@delivery_enhanced_bp.route("/orders/<int:order_id>/reject", methods=["POST"])
@require_delivery_auth
def reject_order_enhanced(order_id):
    """Reject an order and create delivery track"""
    try:
        delivery_guy_id = request.delivery_guy_id
        data = request.get_json() or {}
        rejection_reason = data.get("reason", "Order rejected by delivery personnel")
        
        # Reject the order
        result = reject_order_by_delivery_guy(delivery_guy_id, order_id, rejection_reason)
        
        if result["success"]:
            # Create delivery track entry
            delivery_track = DeliveryTrack(
                delivery_guy_id=delivery_guy_id,
                order_id=order_id,
                status="rejected",
                notes=rejection_reason,
                created_at=datetime.now()
            )
            db.session.add(delivery_track)
            db.session.commit()
            
            return jsonify({
                "success": True,
                "message": "Order rejected successfully",
                "order": result["order"],
                "delivery_track_id": delivery_track.id
            }), 200
        else:
            return jsonify({"error": result["message"]}), 400
            
    except Exception as e:
        print(f"Reject order enhanced error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@delivery_enhanced_bp.route("/exchanges/<int:exchange_id>/approve", methods=["POST"])
@require_delivery_auth
def approve_exchange_enhanced(exchange_id):
    """Approve an exchange and create delivery track"""
    try:
        delivery_guy_id = request.delivery_guy_id
        data = request.get_json() or {}
        approval_reason = data.get("reason", "Exchange approved by delivery personnel")
        
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
            notes=approval_reason,
            created_at=datetime.now()
        )
        db.session.add(delivery_track)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Exchange approved successfully",
            "exchange": exchange.to_dict(),
            "delivery_track_id": delivery_track.id
        }), 200
        
    except Exception as e:
        print(f"Approve exchange enhanced error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@delivery_enhanced_bp.route("/exchanges/<int:exchange_id>/reject", methods=["POST"])
@require_delivery_auth
def reject_exchange_enhanced(exchange_id):
    """Reject an exchange and create delivery track"""
    try:
        delivery_guy_id = request.delivery_guy_id
        data = request.get_json() or {}
        rejection_reason = data.get("reason", "Exchange rejected by delivery personnel")
        
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
            notes=rejection_reason,
            created_at=datetime.now()
        )
        db.session.add(delivery_track)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Exchange rejected successfully",
            "exchange": exchange.to_dict(),
            "delivery_track_id": delivery_track.id
        }), 200
        
    except Exception as e:
        print(f"Reject exchange enhanced error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@delivery_enhanced_bp.route("/exchanges", methods=["GET"])
@require_delivery_auth
def get_exchanges():
    """Get all exchanges assigned to delivery guy"""
    try:
        delivery_guy_id = request.delivery_guy_id
        exchanges = get_exchanges_for_delivery_guy(delivery_guy_id)
        
        return jsonify({
            "success": True,
            "exchanges": exchanges
        }), 200
        
    except Exception as e:
        print(f"Get exchanges error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@delivery_enhanced_bp.route("/order-items/cancelled", methods=["GET"])
@require_delivery_auth
def get_cancelled_order_items():
    """Get all cancelled order items assigned to delivery guy"""
    try:
        delivery_guy_id = request.delivery_guy_id
        cancelled_items = get_cancelled_order_items_for_delivery_guy(delivery_guy_id)
        
        return jsonify({
            "success": True,
            "cancelled_items": cancelled_items
        }), 200
        
    except Exception as e:
        print(f"Get cancelled order items error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
