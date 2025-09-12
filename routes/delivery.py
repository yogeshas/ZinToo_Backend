# routes/delivery.py
from flask import Blueprint, request, jsonify, send_file
from services.delivery_onboarding_service import (
    get_all_onboarding,
    get_onboarding_by_id,
    approve_onboarding,
    reject_onboarding,
    update_onboarding,
    delete_onboarding,
    create_onboarding,
    get_onboarding_by_email,
    upload_file
)
from services.delivery_auth_service import verify_auth_token
from utils.auth import require_admin_auth
from utils.crypto import encrypt_payload, decrypt_payload
from models.order import Order
from models.delivery_onboarding import DeliveryOnboarding
from extensions import db
from datetime import datetime
import os
import mimetypes

delivery_bp = Blueprint("delivery", __name__)

# ============================================================================
# DOCUMENT UPLOAD AND VIEWING ROUTES
# ============================================================================

@delivery_bp.route("/documents/upload", methods=["POST"])
def upload_delivery_documents():
    """Upload documents for delivery onboarding"""
    try:
        # Get auth token from header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"success": False, "message": "Authorization header required"}), 401
        
        # Validate token format
        if not auth_header.startswith('Bearer '):
            return jsonify({"success": False, "message": "Invalid authorization format. Use 'Bearer <token>'"}), 401
        
        # Extract token
        token = auth_header.split(' ')[1]
        
        # Validate token
        token_validation = verify_auth_token(token)
        if not token_validation["success"]:
            return jsonify({"success": False, "message": token_validation["message"]}), 401
        
        user = token_validation["user"]
        email = user["email"]
        
        print(f"Processing document upload for user: {email}")
        print(f"Files received: {request.files}")
        
        # Get existing onboarding record
        onboarding = DeliveryOnboarding.query.filter_by(email=email).first()
        if not onboarding:
            return jsonify({"success": False, "message": "Onboarding record not found. Please complete profile first."}), 404
        
        # Handle file uploads
        uploaded_files = {}
        document_fields = [
            'aadhar_card', 'pan_card', 'dl', 'rc_card', 'bank_passbook'
        ]
        
        for field in document_fields:
            if field in request.files:
                file = request.files[field]
                if file and file.filename:
                    # Upload to assets/onboarding/documents folder
                    file_path = upload_file(file, "onboarding/documents")
                    if file_path:
                        uploaded_files[field] = file_path
                        print(f"Uploaded {field}: {file_path}")
        
        # Update onboarding record with uploaded documents
        if uploaded_files:
            for field, file_path in uploaded_files.items():
                setattr(onboarding, field, file_path)
            
            # Update submission status based on what was uploaded
            if 'aadhar_card' in uploaded_files or 'pan_card' in uploaded_files or 'dl' in uploaded_files:
                onboarding.documents_submitted = True
            
            if 'rc_card' in uploaded_files:
                onboarding.vehicle_docs_submitted = True
            
            if 'bank_passbook' in uploaded_files:
                onboarding.bank_docs_submitted = True
            
            # Update status to pending if documents are submitted
            if onboarding.documents_submitted and onboarding.vehicle_docs_submitted and onboarding.bank_docs_submitted:
                onboarding.status = 'pending'
            
            onboarding.updated_at = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                "success": True,
                "message": f"Successfully uploaded {len(uploaded_files)} document(s)",
                "uploaded_files": uploaded_files,
                "onboarding_id": onboarding.id
            }), 200
        else:
            return jsonify({"success": False, "message": "No valid files were uploaded"}), 400
            
    except Exception as e:
        print(f"Document upload error: {str(e)}")
        return jsonify({"success": False, "message": "Internal server error"}), 500

@delivery_bp.route("/documents/<path:file_path>", methods=["GET"])
def view_document(file_path):
    """View uploaded documents"""
    try:
        # Security check - ensure file path is within allowed directory
        allowed_path = os.path.join('assets', 'onboarding')
        
        # Handle both relative and absolute paths
        if file_path.startswith('assets/onboarding/'):
            # Path already includes assets/onboarding prefix
            full_path = file_path
        else:
            # Add assets/onboarding prefix
            full_path = os.path.join('assets', 'onboarding', file_path)
        
        if not os.path.commonpath([os.path.abspath(full_path), os.path.abspath(allowed_path)]) == os.path.abspath(allowed_path):
            return jsonify({"success": False, "message": "Access denied"}), 403
        
        if not os.path.exists(full_path):
            print(f"File not found: {full_path}")
            return jsonify({"success": False, "message": "File not found"}), 404
        
        # Determine content type
        content_type, _ = mimetypes.guess_type(full_path)
        if not content_type:
            content_type = 'application/octet-stream'
        
        return send_file(full_path, mimetype=content_type)
        
    except Exception as e:
        print(f"View document error: {str(e)}")
        return jsonify({"success": False, "message": "Internal server error"}), 500

@delivery_bp.route("/documents/list/<int:onboarding_id>", methods=["GET"])
@require_admin_auth
def list_delivery_documents(current_admin, onboarding_id):
    """List all documents for a delivery onboarding record"""
    try:
        onboarding = DeliveryOnboarding.query.get(onboarding_id)
        if not onboarding:
            return jsonify({"success": False, "message": "Onboarding record not found"}), 404
        
        documents = {}
        document_fields = {
            'profile_picture': 'Profile Picture',
            'aadhar_card': 'Aadhar Card',
            'pan_card': 'PAN Card', 
            'dl': 'Driving License',
            'rc_card': 'RC Card',
            'bank_passbook': 'Bank Passbook'
        }
        
        for field, display_name in document_fields.items():
            file_path = getattr(onboarding, field, None)
            if file_path:
                # Check if file exists - handle both relative and absolute paths
                if file_path.startswith('assets/onboarding/'):
                    full_path = file_path
                elif file_path.startswith('assets/'):
                    full_path = file_path
                else:
                    full_path = os.path.join('assets', 'onboarding', file_path)
                
                if os.path.exists(full_path):
                    # Get file info
                    file_stat = os.stat(full_path)
                    file_size = file_stat.st_size
                    file_ext = os.path.splitext(file_path)[1].lower()
                    
                    # Determine file type
                    if file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                        file_type = 'image'
                    elif file_ext in ['.pdf']:
                        file_type = 'pdf'
                    else:
                        file_type = 'document'
                    
                    documents[field] = {
                        'display_name': display_name,
                        'file_path': file_path,
                        'file_size': file_size,
                        'file_type': file_type,
                        'file_extension': file_ext,
                        'uploaded_at': file_stat.st_mtime
                    }
        
        data = {"documents": documents}
        enc = encrypt_payload(data)
        return jsonify({"success": True, "encrypted_data": enc}), 200
        
    except Exception as e:
        print(f"List documents error: {str(e)}")
        return jsonify({"success": False, "message": "Internal server error"}), 500

# ============================================================================
# MOBILE ONBOARDING ROUTES
# ============================================================================

@delivery_bp.route("/onboard", methods=["POST"])
def submit_onboarding():
    """Submit onboarding form from mobile app"""
    try:
        # Get auth token from header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"success": False, "message": "Authorization header required"}), 401
        
        # Validate token format
        if not auth_header.startswith('Bearer '):
            return jsonify({"success": False, "message": "Invalid authorization format. Use 'Bearer <token>'"}), 401
        
        # Extract token
        token = auth_header.split(' ')[1]
        
        # Validate token
        token_validation = verify_auth_token(token)
        if not token_validation["success"]:
            return jsonify({"success": False, "message": token_validation["message"]}), 401
        
        user = token_validation["user"]
        email = user["email"]
        
        print(f"Processing onboarding for user: {email}")
        print(f"Form data: {request.form}")
        print(f"Files: {request.files}")
        
        # Get form data
        data = request.form.to_dict()
        
        # Handle file uploads
        if 'profile_picture' in request.files:
            profile_pic = request.files['profile_picture']
            if profile_pic.filename:
                profile_path = upload_file(profile_pic, "onboarding/profile")
                data['profile_picture'] = profile_path
                print(f"Profile picture uploaded: {profile_path}")
        
        # Create onboarding with mobile app data structure
        result = create_onboarding_mobile(data, email)
        
        if result["success"]:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        print(f"Submit onboarding error: {str(e)}")
        return jsonify({"success": False, "message": "Internal server error"}), 500

@delivery_bp.route("/onboard", methods=["GET"])
def get_onboarding():
    """Get onboarding status for mobile app"""
    try:
        # Get auth token from header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"success": False, "message": "Authorization header required"}), 401
        
        # Validate token format
        if not auth_header.startswith('Bearer '):
            return jsonify({"success": False, "message": "Invalid authorization format. Use 'Bearer <token>'"}), 401
        
        # Extract token
        token = auth_header.split(' ')[1]
        
        # Validate token
        token_validation = verify_auth_token(token)
        if not token_validation["success"]:
            return jsonify({"success": False, "message": token_validation["message"]}), 401
        
        user = token_validation["user"]
        email = user["email"]
        
        # Get onboarding record
        result = get_onboarding_by_email(email)
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 404
            
    except Exception as e:
        print(f"Get onboarding error: {str(e)}")
        return jsonify({"success": False, "message": "Internal server error"}), 500

@delivery_bp.route("/onboard", methods=["PUT"])
def update_onboarding_mobile():
    """Update onboarding from mobile app"""
    try:
        # Get auth token from header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"success": False, "message": "Authorization header required"}), 401
        
        # Validate token format
        if not auth_header.startswith('Bearer '):
            return jsonify({"success": False, "message": "Invalid authorization format. Use 'Bearer <token>'"}), 401
        
        # Extract token
        token = auth_header.split(' ')[1]
        
        # Validate token
        token_validation = verify_auth_token(token)
        if not token_validation["success"]:
            return jsonify({"success": False, "message": token_validation["message"]}), 401
        
        user = token_validation["user"]
        email = user["email"]
        
        # Get form data
        data = request.form.to_dict()
        
        # Handle file uploads
        if 'profile_picture' in request.files:
            profile_pic = request.files['profile_picture']
            if profile_pic.filename:
                profile_path = upload_file(profile_pic, "onboarding/profile")
                data['profile_picture'] = profile_path
        
        # Get existing onboarding record
        result = get_onboarding_by_email(email)
        if not result["success"]:
            return jsonify({"success": False, "message": "Onboarding record not found"}), 404
        
        onboarding_id = result["onboarding"]["id"]
        
        # Update onboarding
        update_result = update_onboarding(onboarding_id, data)
        
        if update_result["success"]:
            return jsonify(update_result), 200
        else:
            return jsonify(update_result), 400
            
    except Exception as e:
        print(f"Update onboarding error: {str(e)}")
        return jsonify({"success": False, "message": "Internal server error"}), 500

# Helper function for mobile onboarding
def create_onboarding_mobile(data, email):
    """Create onboarding record from mobile app data"""
    try:
        # Check if user already has onboarding - update existing one instead of removing
        existing_onboarding = DeliveryOnboarding.query.filter_by(email=email).first()
        
        if existing_onboarding:
            print(f"Updating existing onboarding for email: {email}")
            # Update existing record with new data
            existing_onboarding.first_name = data.get('first_name', '')
            existing_onboarding.last_name = data.get('last_name', '')
            existing_onboarding.dob = datetime.strptime(data['dob'], '%Y-%m-%d').date() if data.get('dob') else None
            existing_onboarding.primary_number = data.get('primary_number', '')
            existing_onboarding.secondary_number = data.get('secondary_number')
            existing_onboarding.blood_group = data.get('blood_group')
            existing_onboarding.address = data.get('address', '')
            existing_onboarding.language = data.get('language', 'English')
            existing_onboarding.profile_picture = data.get('profile_picture')
            existing_onboarding.referral_code = data.get('referral_code')
            existing_onboarding.status = 'profile_incomplete'
            existing_onboarding.profile_submitted = True  # Mark profile as submitted
            
            # Update timestamp
            existing_onboarding.updated_at = datetime.utcnow()
            db.session.commit()
            
            return {
                "success": True,
                "message": "Onboarding updated successfully",
                "onboarding": existing_onboarding.as_dict()
            }
        else:
            # Create new onboarding record
            print(f"Creating new onboarding for email: {email}")
            print(f"Form data received: {data}")
            
            onboarding = DeliveryOnboarding(
                first_name=data.get('first_name', ''),
                last_name=data.get('last_name', ''),
                dob=datetime.strptime(data['dob'], '%Y-%m-%d').date() if data.get('dob') else None,
                email=email,  # Always save email for easy searching
                primary_number=data.get('primary_number', ''),
                secondary_number=data.get('secondary_number'),
                blood_group=data.get('blood_group'),
                address=data.get('address', ''),
                language=data.get('language', 'English'),
                profile_picture=data.get('profile_picture'),
                referral_code=data.get('referral_code'),
                # Set default values for required fields that mobile app doesn't send yet
                aadhar_card='',
                pan_card='',
                dl='',
                vehicle_number=data.get('vehicle_number', ''),
                rc_card='',
                bank_account_number=data.get('bank_account_number', ''),
                ifsc_code=data.get('ifsc_code', ''),
                bank_passbook=data.get('bank_passbook', ''),
                name_as_per_bank=data.get('name_as_per_bank'),
                status='profile_incomplete',  # Mark as profile incomplete until documents are uploaded
                profile_submitted=True  # Mark profile as submitted
            )
            
            db.session.add(onboarding)
            db.session.commit()
            
            return {
                "success": True, 
                "message": "Profile created successfully! Please upload required documents.",
                "onboarding_id": onboarding.id,
                "user_status": "profile_incomplete",
                "next_step": "documents"
            }
            
    except Exception as e:
        print(f"Error in create_onboarding_mobile: {e}")
        return {"success": False, "message": "Failed to create/update onboarding"}

@delivery_bp.route("/guys/available", methods=["GET"])
@require_admin_auth
def get_available_delivery_guys(current_admin):
    """Get all available delivery guys (approved status only)"""
    try:
        # Get only approved delivery guys
        available_guys = DeliveryOnboarding.query.filter_by(status="approved").all()
        
        available_guys_data = []
        for guy in available_guys:
            # Get active orders count
            active_orders = Order.query.filter_by(
                delivery_guy_id=guy.id
            ).filter(
                Order.status.in_(['assigned', 'picked_up', 'out_for_delivery'])
            ).count()
            
            guy_data = {
                "id": guy.id,
                "name": f"{guy.first_name} {guy.last_name}".strip() if guy.first_name and guy.last_name else "N/A",
                "first_name": guy.first_name,
                "last_name": guy.last_name,
                "phone_number": guy.primary_number,
                "email": guy.email,
                "status": guy.status,
                "active_orders_count": active_orders,
                "available": active_orders < 5,  # Consider available if less than 5 active orders
                "created_at": guy.created_at.isoformat() if guy.created_at else None
            }
            available_guys_data.append(guy_data)
        
        data = {"available_delivery_guys": available_guys_data}
        enc = encrypt_payload(data)
        return jsonify({"success": True, "encrypted_data": enc}), 200
    except Exception as e:
        print(f"Get available delivery guys error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@delivery_bp.route("/orders/unassigned", methods=["GET"])
@require_admin_auth
def get_unassigned_orders(current_admin):
    """Get all unassigned orders for delivery assignment"""
    try:
        # Get orders that are not assigned to any delivery guy
        unassigned_orders = Order.query.filter(
            Order.delivery_guy_id.is_(None)
        ).filter(
            Order.status.in_(['confirmed', 'processing', 'ready_for_delivery'])
        ).order_by(Order.created_at.desc()).all()
        
        orders_data = []
        for order in unassigned_orders:
            # Get customer info
            customer = order.customer
            customer_data = {
                "id": customer.id,
                "name": customer.name,
                "email": customer.email,
                "phone": customer.phone
            } if customer else None
            
            # Get order items
            order_items = []
            for item in order.order_items:
                item_data = {
                    "id": item.id,
                    "product_name": item.product_name,
                    "quantity": item.quantity,
                    "price": float(item.price),
                    "total": float(item.total)
                }
                order_items.append(item_data)
            
            order_data = {
                "id": order.id,
                "order_number": order.order_number,
                "status": order.status,
                "total_amount": float(order.total_amount),
                "created_at": order.created_at.isoformat() if order.created_at else None,
                "customer": customer_data,
                "order_items": order_items,
                "delivery_address": order.delivery_address,
                "delivery_notes": order.delivery_notes
            }
            orders_data.append(order_data)
        
        data = {"unassigned_orders": orders_data}
        enc = encrypt_payload(data)
        return jsonify({"success": True, "encrypted_data": enc}), 200
    except Exception as e:
        print(f"Get unassigned orders error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

# ============================================================================
# DELIVERY ORDERS MANAGEMENT (ADMIN)
# ============================================================================

@delivery_bp.route("/admin/orders", methods=["GET"])
@require_admin_auth
def get_all_delivery_orders_admin(current_admin):
    """Get all delivery orders for admin panel"""
    try:
        status = request.args.get('status')  # approved, assigned, cancelled, delivered, rejected
        
        # Get all orders with delivery assignment
        query = Order.query
        
        if status and status != 'all':
            query = query.filter(Order.status == status)
        
        orders = query.order_by(Order.created_at.desc()).all()
        
        orders_data = []
        for order in orders:
            # Get delivery guy info
            delivery_guy = None
            if order.delivery_guy_id:
                onboarding = DeliveryOnboarding.query.get(order.delivery_guy_id)
                if onboarding:
                    delivery_guy = {
                        "id": onboarding.id,
                        "name": f"{onboarding.first_name} {onboarding.last_name}".strip(),
                        "phone": onboarding.primary_number,
                        "email": onboarding.email,
                        "vehicle_number": onboarding.vehicle_number
                    }
            
            # Get customer info
            customer = None
            if order.customer:
                customer = {
                    "id": order.customer.id,
                    "name": order.customer.username,
                    "email": order.customer.email,
                    "phone": order.customer.get_phone_number()
                }
            
            order_data = {
                "id": order.id,
                "order_number": order.order_number,
                "status": order.status,
                "total_amount": order.total_amount,
                "delivery_address": order.delivery_address,
                "delivery_type": order.delivery_type,
                "created_at": order.created_at.isoformat() if order.created_at else None,
                "assigned_at": order.assigned_at.isoformat() if order.assigned_at else None,
                "delivery_guy": delivery_guy,
                "customer": customer
            }
            orders_data.append(order_data)
        
        data = {"orders": orders_data}
        enc = encrypt_payload(data)
        return jsonify({"success": True, "encrypted_data": enc}), 200
        
    except Exception as e:
        print(f"Get delivery orders admin error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@delivery_bp.route("/admin/orders/<int:order_id>", methods=["GET"])
@require_admin_auth
def get_delivery_order_detail_admin(current_admin, order_id):
    """Get delivery order detail for admin panel"""
    try:
        order = Order.query.get(order_id)
        if not order:
            return jsonify({"error": "Order not found"}), 404
        
        if not order.delivery_guy_id:
            return jsonify({"error": "Order not assigned to delivery"}), 400
        
        # Get delivery guy info
        delivery_guy = None
        if order.delivery_guy_id:
            onboarding = DeliveryOnboarding.query.get(order.delivery_guy_id)
            if onboarding:
                delivery_guy = {
                    "id": onboarding.id,
                    "name": f"{onboarding.first_name} {onboarding.last_name}".strip(),
                    "phone": onboarding.primary_number,
                    "email": onboarding.email,
                    "vehicle_number": onboarding.vehicle_number,
                    "status": onboarding.status
                }
        
        # Get customer info
        customer = None
        if order.customer:
            customer = {
                "id": order.customer.id,
                "name": order.customer.username,
                "email": order.customer.email,
                "phone": order.customer.get_phone_number()
            }
        
        # Get order items
        order_items = []
        if order.order_items:
            for item in order.order_items:
                order_items.append({
                    "id": item.id,
                    "product_name": item.product_name,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "total_price": item.total_price,
                    "selected_size": item.selected_size
                })
        
        order_data = {
            "id": order.id,
            "order_number": order.order_number,
            "status": order.status,
            "total_amount": order.total_amount,
            "delivery_address": order.delivery_address,
            "delivery_type": order.delivery_type,
            "delivery_fee": order.delivery_fee_amount,
            "payment_method": order.payment_method,
            "payment_status": order.payment_status,
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "assigned_at": order.assigned_at.isoformat() if order.assigned_at else None,
            "delivery_notes": order.delivery_notes,
            "delivery_guy": delivery_guy,
            "customer": customer,
            "order_items": order_items
        }
        
        data = {"order": order_data}
        enc = encrypt_payload(data)
        return jsonify({"success": True, "encrypted_data": enc}), 200
        
    except Exception as e:
        print(f"Get delivery order detail admin error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@delivery_bp.route("/admin/orders/<int:order_id>/pickup", methods=["POST"])
@require_admin_auth
def pickup_order_admin(current_admin, order_id):
    """Mark order as picked up (admin action)"""
    try:
        order = Order.query.get(order_id)
        if not order:
            return jsonify({"error": "Order not found"}), 404
        
        if not order.delivery_guy_id:
            return jsonify({"error": "Order not assigned to delivery"}), 400
        
        # Update order status to picked up
        order.status = "picked_up"
        order.delivery_notes = "Order picked up by delivery guy"
        order.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        data = {"message": "Order marked as picked up successfully"}
        enc = encrypt_payload(data)
        return jsonify({"success": True, "encrypted_data": enc}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Pickup order admin error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@delivery_bp.route("/admin/orders/<int:order_id>/deliver", methods=["POST"])
@require_admin_auth
def deliver_order_admin(current_admin, order_id):
    """Mark order as delivered (admin action)"""
    try:
        order = Order.query.get(order_id)
        if not order:
            return jsonify({"error": "Order not found"}), 404
        
        if not order.delivery_guy_id:
            return jsonify({"error": "Order not assigned to delivery"}), 400
        
        # Update order status to delivered
        order.status = "delivered"
        order.delivery_notes = "Order delivered successfully"
        order.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        data = {"message": "Order marked as delivered successfully"}
        enc = encrypt_payload(data)
        return jsonify({"success": True, "encrypted_data": enc}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Deliver order admin error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@delivery_bp.route("/admin/orders/<int:order_id>/status", methods=["PUT"])
@require_admin_auth
def update_order_status_admin(current_admin, order_id):
    """Update order status (admin action)"""
    try:
        encrypted_data = request.json.get("payload")
        if not encrypted_data:
            return jsonify({"error": "Missing encrypted payload"}), 400
        
        data = decrypt_payload(encrypted_data)
        new_status = data.get("status")
        delivery_notes = data.get("delivery_notes", "")
        
        if not new_status:
            return jsonify({"error": "Status is required"}), 400
        
        order = Order.query.get(order_id)
        if not order:
            return jsonify({"error": "Order not found"}), 404
        
        # Import the order service function
        from services.order_service import update_order_items_status
        
        # Update order items status first
        items_result, items_status_code = update_order_items_status(order_id, new_status)
        if items_status_code != 200:
            return jsonify({"error": items_result.get("error", "Failed to update order items")}), items_status_code
        
        # Update order status and notes
        order.status = new_status
        order.delivery_notes = delivery_notes
        order.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Include order items update info in response
        response_data = {
            "message": "Order status and order items updated successfully",
            "order_items_updated": items_result.get("total_updated", 0),
            "order_items_skipped": items_result.get("total_skipped", 0)
        }
        enc = encrypt_payload(response_data)
        return jsonify({"success": True, "encrypted_data": enc}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Update order status admin error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

# ============================================================================
# DELIVERY ONBOARDING MANAGEMENT (ADMIN)
# ============================================================================

@delivery_bp.route("/onboarding", methods=["GET"])
@require_admin_auth
def get_all_delivery_onboarding(current_admin):
    """Get all delivery onboarding records with optional status filter"""
    try:
        status = request.args.get('status')  # pending, approved, rejected
        result = get_all_onboarding(status)
        
        if not result["success"]:
            return jsonify({"error": result["message"]}), 400
        
        data = {"onboarding_records": result["onboarding_records"]}
        enc = encrypt_payload(data)
        return jsonify({"success": True, "encrypted_data": enc}), 200
    except Exception as e:
        print(f"Get delivery onboarding error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@delivery_bp.route("/onboarding/<int:onboarding_id>", methods=["GET"])
@require_admin_auth
def get_delivery_onboarding_by_id(current_admin, onboarding_id):
    """Get specific delivery onboarding record by ID"""
    try:
        result = get_onboarding_by_id(onboarding_id)
        
        if not result["success"]:
            return jsonify({"error": result["message"]}), 404
        
        data = {"onboarding": result["onboarding"]}
        enc = encrypt_payload(data)
        return jsonify({"success": True, "encrypted_data": enc}), 200
    except Exception as e:
        print(f"Get delivery onboarding by ID error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@delivery_bp.route("/onboarding/<int:onboarding_id>/approve", methods=["POST"])
@require_admin_auth
def approve_delivery_onboarding(current_admin, onboarding_id):
    """Approve delivery onboarding"""
    try:
        encrypted_data = request.json.get("payload")
        if not encrypted_data:
            return jsonify({"error": "Missing encrypted payload"}), 400

        data = decrypt_payload(encrypted_data)
        notes = data.get("notes")
        
        result = approve_onboarding(onboarding_id, current_admin["id"], notes)
        
        if not result["success"]:
            return jsonify({"error": result["message"]}), 400
        
        data = {
            "message": result["message"],
            "onboarding": result["onboarding"]
        }
        enc = encrypt_payload(data)
        return jsonify({"success": True, "encrypted_data": enc}), 200
    except Exception as e:
        print(f"Approve delivery onboarding error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@delivery_bp.route("/onboarding/<int:onboarding_id>/reject", methods=["POST"])
@require_admin_auth
def reject_delivery_onboarding(current_admin, onboarding_id):
    """Reject delivery onboarding"""
    try:
        encrypted_data = request.json.get("payload")
        if not encrypted_data:
            return jsonify({"error": "Missing encrypted payload"}), 400

        data = decrypt_payload(encrypted_data)
        notes = data.get("notes")
        
        if not notes:
            return jsonify({"error": "Rejection notes are required"}), 400
        
        result = reject_onboarding(onboarding_id, current_admin["id"], notes)
        
        if not result["success"]:
            return jsonify({"error": result["message"]}), 400
        
        data = {"message": result["message"]}
        enc = encrypt_payload(data)
        return jsonify({"success": True, "encrypted_data": enc}), 200
    except Exception as e:
        print(f"Reject delivery onboarding error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@delivery_bp.route("/onboarding/<int:onboarding_id>", methods=["PUT"])
@require_admin_auth
def update_delivery_onboarding(current_admin, onboarding_id):
    """Update delivery onboarding record"""
    try:
        encrypted_data = request.json.get("payload")
        if not encrypted_data:
            return jsonify({"error": "Missing encrypted payload"}), 400

        data = decrypt_payload(encrypted_data)
        
        result = update_onboarding(onboarding_id, data)
        
        if not result["success"]:
            return jsonify({"error": result["message"]}), 400
        
        data = {
            "message": result["message"],
            "onboarding": result["onboarding"]
        }
        enc = encrypt_payload(data)
        return jsonify({"success": True, "encrypted_data": enc}), 200
    except Exception as e:
        print(f"Update delivery onboarding error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@delivery_bp.route("/onboarding/<int:onboarding_id>", methods=["DELETE"])
@require_admin_auth
def delete_delivery_onboarding(current_admin, onboarding_id):
    """Delete delivery onboarding record"""
    try:
        result = delete_onboarding(onboarding_id)
        
        if not result["success"]:
            return jsonify({"error": result["message"]}), 400
        
        data = {"message": result["message"]}
        enc = encrypt_payload(data)
        return jsonify({"success": True, "encrypted_data": enc}), 200
    except Exception as e:
        print(f"Delete delivery onboarding error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

# ============================================================================
# DELIVERY MANAGEMENT (ADMIN) - Using onboarding table
# ============================================================================

@delivery_bp.route("/guys", methods=["GET"])
@require_admin_auth
def get_all_delivery_guys_route(current_admin):
    """Get all delivery onboarding records for admin management"""
    try:
        # Get all onboarding records (not just approved ones)
        all_onboarding = DeliveryOnboarding.query.all()
        
        delivery_guys_data = []
        for onboarding in all_onboarding:
            # Get active orders count for approved delivery guys only
            active_orders = 0
            if onboarding.status == "approved":
                active_orders = Order.query.filter_by(
                    delivery_guy_id=onboarding.id
                ).filter(
                    Order.status.in_(['assigned', 'picked_up', 'out_for_delivery'])
                ).count()
            
            guy_data = {
                "id": onboarding.id,
                "name": f"{onboarding.first_name} {onboarding.last_name}".strip() if onboarding.first_name and onboarding.last_name else "N/A",
                "first_name": onboarding.first_name,
                "last_name": onboarding.last_name,
                "phone_number": onboarding.primary_number,
                "secondary_number": onboarding.secondary_number,
                "email": onboarding.email,
                "dob": onboarding.dob.isoformat() if onboarding.dob else None,
                "blood_group": onboarding.blood_group,
                "address": onboarding.address,
                "language": onboarding.language,
                "profile_picture": onboarding.profile_picture,
                "referral_code": onboarding.referral_code,
                
                # Identity Documents
                "aadhar_card": onboarding.aadhar_card,
                "pan_card": onboarding.pan_card,
                "dl": onboarding.dl,
                
                # Vehicle Information
                "vehicle_number": onboarding.vehicle_number,
                "rc_card": onboarding.rc_card,
                "vehicle_type": "Bike",
                
                # Bank Information
                "bank_account_number": onboarding.bank_account_number,
                "ifsc_code": onboarding.ifsc_code,
                "bank_passbook": onboarding.bank_passbook,
                "name_as_per_bank": onboarding.name_as_per_bank,
                
                # Status and Performance
                "status": onboarding.status,
                "status_display": onboarding.get_status_display(),
                "completion_percentage": onboarding.get_completion_percentage(),
                "ready_for_approval": onboarding.is_ready_for_approval(),
                "current_location": None,
                "rating": 0.0,
                "total_deliveries": 0,
                "completed_deliveries": 0,
                "active_orders_count": active_orders,
                
                # Document Submission Status
                "profile_submitted": onboarding.profile_submitted,
                "documents_submitted": onboarding.documents_submitted,
                "vehicle_docs_submitted": onboarding.vehicle_docs_submitted,
                "bank_docs_submitted": onboarding.bank_docs_submitted,
                
                # Verification Status
                "profile_verified": onboarding.profile_verified,
                "documents_verified": onboarding.documents_verified,
                "vehicle_verified": onboarding.vehicle_verified,
                "bank_verified": onboarding.bank_verified,
                
                # Onboarding Details
                "onboarding_details": onboarding.as_dict(),
                "created_at": onboarding.created_at.isoformat() if onboarding.created_at else None,
                "approved_at": onboarding.approved_at.isoformat() if onboarding.approved_at else None,
                "admin_notes": onboarding.admin_notes
            }
            delivery_guys_data.append(guy_data)
        
        data = {"delivery_guys": delivery_guys_data}
        enc = encrypt_payload(data)
        return jsonify({"success": True, "encrypted_data": enc}), 200
    except Exception as e:
        print(f"Get all delivery guys error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@delivery_bp.route("/guys/active", methods=["GET"])
@require_admin_auth
def get_active_delivery_guys_route(current_admin):
    """Get active delivery guys from onboarding"""
    try:
        # Get all approved onboarding records (all are considered active)
        active_onboarding = DeliveryOnboarding.query.filter_by(
            status="approved"
        ).all()
        
        delivery_guys_data = []
        for onboarding in active_onboarding:
            # Get active orders count for this delivery guy
            active_orders = Order.query.filter_by(
                delivery_guy_id=onboarding.id
            ).filter(
                Order.status.in_(['assigned', 'picked_up', 'out_for_delivery'])
            ).count()
            
            guy_data = {
                "id": onboarding.id,
                "name": f"{onboarding.first_name} {onboarding.last_name}".strip(),
                "first_name": onboarding.first_name,
                "last_name": onboarding.last_name,
                "phone_number": onboarding.primary_number,
                "secondary_number": onboarding.secondary_number,
                "email": onboarding.email,
                "dob": onboarding.dob.isoformat() if onboarding.dob else None,
                "blood_group": onboarding.blood_group,
                "address": onboarding.address,
                "language": onboarding.language,
                "profile_picture": onboarding.profile_picture,
                "referral_code": onboarding.referral_code,
                
                # Identity Documents
                "aadhar_card": onboarding.aadhar_card,
                "pan_card": onboarding.pan_card,
                "dl": onboarding.dl,
                
                # Vehicle Information
                "vehicle_number": onboarding.vehicle_number,
                "rc_card": onboarding.rc_card,
                "vehicle_type": "Bike",
                
                # Bank Information
                "bank_account_number": onboarding.bank_account_number,
                "ifsc_code": onboarding.ifsc_code,
                "bank_passbook": onboarding.bank_passbook,
                "name_as_per_bank": onboarding.name_as_per_bank,
                
                # Status and Performance
                "status": "active",
                "current_location": None,
                "rating": 0.0,
                "total_deliveries": 0,
                "completed_deliveries": 0,
                "active_orders_count": active_orders,
                
                # Onboarding Details
                "onboarding_details": onboarding.as_dict(),
                "created_at": onboarding.created_at.isoformat() if onboarding.created_at else None,
                "approved_at": onboarding.approved_at.isoformat() if onboarding.approved_at else None,
                "admin_notes": onboarding.admin_notes
            }
            delivery_guys_data.append(guy_data)
        
        data = {"delivery_guys": delivery_guys_data}
        enc = encrypt_payload(data)
        return jsonify({"success": True, "encrypted_data": enc}), 200
    except Exception as e:
        print(f"Get active delivery guys error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@delivery_bp.route("/guys/available", methods=["GET"])
@require_admin_auth
def get_available_delivery_guys_route(current_admin):
    """Get available delivery guys from onboarding"""
    try:
        # Get all approved onboarding records (all are considered available)
        available_onboarding = DeliveryOnboarding.query.filter_by(
            status="approved"
        ).all()
        
        delivery_guys_data = []
        for onboarding in available_onboarding:
            # Get active orders count for this delivery guy
            active_orders = Order.query.filter_by(
                delivery_guy_id=onboarding.id
            ).filter(
                Order.status.in_(['assigned', 'picked_up', 'out_for_delivery'])
            ).count()
            
            guy_data = {
                "id": onboarding.id,
                "name": f"{onboarding.first_name} {onboarding.last_name}".strip(),
                "first_name": onboarding.first_name,
                "last_name": onboarding.last_name,
                "phone_number": onboarding.primary_number,
                "secondary_number": onboarding.secondary_number,
                "email": onboarding.email,
                "dob": onboarding.dob.isoformat() if onboarding.dob else None,
                "blood_group": onboarding.blood_group,
                "address": onboarding.address,
                "language": onboarding.language,
                "profile_picture": onboarding.profile_picture,
                "referral_code": onboarding.referral_code,
                
                # Identity Documents
                "aadhar_card": onboarding.aadhar_card,
                "pan_card": onboarding.pan_card,
                "dl": onboarding.dl,
                
                # Vehicle Information
                "vehicle_number": onboarding.vehicle_number,
                "rc_card": onboarding.rc_card,
                "vehicle_type": "Bike",
                
                # Bank Information
                "bank_account_number": onboarding.bank_account_number,
                "ifsc_code": onboarding.ifsc_code,
                "bank_passbook": onboarding.bank_passbook,
                "name_as_per_bank": onboarding.name_as_per_bank,
                
                # Status and Performance
                "status": "available",
                "current_location": None,
                "rating": 0.0,
                "total_deliveries": 0,
                "completed_deliveries": 0,
                "active_orders_count": active_orders,
                
                # Onboarding Details
                "onboarding_details": onboarding.as_dict(),
                "created_at": onboarding.created_at.isoformat() if onboarding.created_at else None,
                "approved_at": onboarding.approved_at.isoformat() if onboarding.approved_at else None,
                "admin_notes": onboarding.admin_notes
            }
            delivery_guys_data.append(guy_data)
        
        data = {"delivery_guys": delivery_guys_data}
        enc = encrypt_payload(data)
        return jsonify({"success": True, "encrypted_data": enc}), 200
    except Exception as e:
        print(f"Get available delivery guys error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@delivery_bp.route("/guys/<int:onboarding_id>", methods=["GET"])
@require_admin_auth
def get_delivery_guy_route(current_admin, onboarding_id):
    """Get delivery guy by onboarding ID"""
    try:
        # Get onboarding record
        onboarding = DeliveryOnboarding.query.filter_by(
            id=onboarding_id,
            status="approved"
        ).first()
        
        if not onboarding:
            return jsonify({"error": "Delivery guy not found"}), 404
        
        # Get active orders count for this delivery guy
        active_orders = Order.query.filter_by(
            delivery_guy_id=onboarding.id
        ).filter(
            Order.status.in_(['assigned', 'picked_up', 'out_for_delivery'])
        ).count()
        
        guy_data = {
            "id": onboarding.id,
            "name": f"{onboarding.first_name} {onboarding.last_name}".strip(),
            "first_name": onboarding.first_name,
            "last_name": onboarding.last_name,
            "phone_number": onboarding.primary_number,
            "secondary_number": onboarding.secondary_number,
            "email": onboarding.email,
            "dob": onboarding.dob.isoformat() if onboarding.dob else None,
            "blood_group": onboarding.blood_group,
            "address": onboarding.address,
            "language": onboarding.language,
            "profile_picture": onboarding.profile_picture,
            "referral_code": onboarding.referral_code,
            
            # Identity Documents
            "aadhar_card": onboarding.aadhar_card,
            "pan_card": onboarding.pan_card,
            "dl": onboarding.dl,
            
            # Vehicle Information
            "vehicle_number": onboarding.vehicle_number,
            "rc_card": onboarding.rc_card,
            "vehicle_type": "Bike",
            
            # Bank Information
            "bank_account_number": onboarding.bank_account_number,
            "ifsc_code": onboarding.ifsc_code,
            "bank_passbook": onboarding.bank_passbook,
            "name_as_per_bank": onboarding.name_as_per_bank,
            
            # Status and Performance
            "status": "active",
            "current_location": None,
            "rating": 0.0,
            "total_deliveries": 0,
            "completed_deliveries": 0,
            "active_orders_count": active_orders,
            
            # Onboarding Details
            "onboarding_details": onboarding.as_dict(),
            "created_at": onboarding.created_at.isoformat() if onboarding.created_at else None,
            "approved_at": onboarding.approved_at.isoformat() if onboarding.approved_at else None,
            "admin_notes": onboarding.admin_notes
        }
        
        # Get stats (placeholder for now)
        stats = {
            "total_orders": 0,
            "completed_orders": 0,
            "active_orders": active_orders,
            "rating": 0.0
        }
        
        data = {
            "delivery_guy": guy_data,
            "stats": stats
        }
        enc = encrypt_payload(data)
        return jsonify({"success": True, "encrypted_data": enc}), 200
    except Exception as e:
        print(f"Get delivery guy error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@delivery_bp.route("/guys/<int:onboarding_id>/status", methods=["PUT"])
@require_admin_auth
def update_delivery_guy_status(current_admin, onboarding_id):
    """Update delivery guy status (placeholder - status managed in onboarding)"""
    try:
        encrypted_data = request.json.get("payload")
        if not encrypted_data:
            return jsonify({"error": "Missing encrypted payload"}), 400

        data = decrypt_payload(encrypted_data)
        new_status = data.get("status")
        
        if not new_status:
            return jsonify({"error": "Status is required"}), 400
        
        # For now, just return success since status is managed in onboarding
        data = {"message": f"Delivery guy status updated to {new_status}"}
        enc = encrypt_payload(data)
        return jsonify({"success": True, "encrypted_data": enc}), 200
    except Exception as e:
        print(f"Update delivery guy status error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

# ============================================================================
# ORDER ASSIGNMENT MANAGEMENT - Using onboarding IDs
# ============================================================================

@delivery_bp.route("/orders/unassigned", methods=["GET"])
@require_admin_auth
def get_unassigned_orders_route(current_admin):
    """Get unassigned orders"""
    try:
        orders = Order.query.filter_by(delivery_guy_id=None).all()
        orders_data = [order.as_dict() for order in orders]
        
        data = {"orders": orders_data}
        enc = encrypt_payload(data)
        return jsonify({"success": True, "encrypted_data": enc}), 200
    except Exception as e:
        print(f"Get unassigned orders error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@delivery_bp.route("/orders/<int:order_id>/assign", methods=["POST"])
@require_admin_auth
def assign_order_route(current_admin, order_id):
    """Assign order to delivery guy (using onboarding ID)"""
    try:
        encrypted_data = request.json.get("payload")
        if not encrypted_data:
            return jsonify({"error": "Missing encrypted payload"}), 400

        data = decrypt_payload(encrypted_data)
        onboarding_id = data.get("delivery_guy_id")  # This is actually onboarding_id now
        notes = data.get("notes")
        
        if not onboarding_id:
            return jsonify({"error": "Delivery guy ID is required"}), 400
        
        # Verify onboarding exists and is approved
        onboarding = DeliveryOnboarding.query.filter_by(
            id=onboarding_id,
            status="approved"
        ).first()
        
        if not onboarding:
            return jsonify({"error": "Delivery guy not found or not approved"}), 404
        
        # Get order
        order = Order.query.get(order_id)
        if not order:
            return jsonify({"error": "Order not found"}), 404
        
        if order.delivery_guy_id:
            return jsonify({"error": "Order is already assigned to a delivery guy"}), 400
        
        # Assign order using onboarding_id as delivery_guy_id
        order.delivery_guy_id = onboarding_id
        order.assigned_at = datetime.utcnow()
        if notes:
            order.delivery_notes = notes
        
        db.session.commit()
        
        order_dict = order.as_dict()
        enc = encrypt_payload({"order": order_dict})
        return jsonify({"success": True, "encrypted_data": enc}), 200
    except Exception as e:
        print(f"Assign order error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@delivery_bp.route("/orders/<int:order_id>/unassign", methods=["POST"])
@require_admin_auth
def unassign_order_route(current_admin, order_id):
    """Unassign order from delivery guy"""
    try:
        order = Order.query.get(order_id)
        if not order:
            return jsonify({"error": "Order not found"}), 404
        
        if not order.delivery_guy_id:
            return jsonify({"error": "Order is not assigned to any delivery guy"}), 400
        
        # Unassign order
        order.delivery_guy_id = None
        order.assigned_at = None
        
        db.session.commit()
        
        order_dict = order.as_dict()
        enc = encrypt_payload({"order": order_dict})
        return jsonify({"success": True, "encrypted_data": enc}), 200
    except Exception as e:
        print(f"Unassign order error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

# ============================================================================
# ASSIGNED ORDERS MANAGEMENT
# ============================================================================

@delivery_bp.route("/orders/assigned", methods=["GET"])
@require_admin_auth
def get_assigned_orders_route(current_admin):
    """Get all assigned orders with delivery guy and onboarding info"""
    try:
        orders = Order.query.filter(Order.delivery_guy_id.isnot(None)).order_by(Order.id.desc()).all()
        orders_data = []
        
        for order in orders:
            order_dict = order.as_dict()
            
            # Get onboarding details for the delivery guy
            if order.delivery_guy_id:
                onboarding = DeliveryOnboarding.query.get(order.delivery_guy_id)
                
                if onboarding:
                    order_dict['delivery_onboarding'] = onboarding.as_dict()
                    # Add delivery_guy info for compatibility
                    order_dict['delivery_guy'] = {
                        "id": onboarding.id,
                        "name": f"{onboarding.first_name} {onboarding.last_name}".strip(),
                        "phone_number": onboarding.primary_number,
                        "email": onboarding.email,
                        "vehicle_number": onboarding.vehicle_number,
                        "status": "active"
                    }
            
            orders_data.append(order_dict)
        
        data = {"orders": orders_data}
        enc = encrypt_payload(data)
        return jsonify({"success": True, "encrypted_data": enc}), 200
    except Exception as e:
        print(f"Get assigned orders error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@delivery_bp.route("/guys/<int:onboarding_id>/orders", methods=["GET"])
@require_admin_auth
def get_delivery_guy_orders(current_admin, onboarding_id):
    """Get orders assigned to a specific delivery guy (using onboarding ID)"""
    try:
        # Verify onboarding exists and is approved
        onboarding = DeliveryOnboarding.query.filter_by(
            id=onboarding_id,
            status="approved"
        ).first()
        
        if not onboarding:
            return jsonify({"error": "Delivery guy not found or not approved"}), 404
        
        orders = Order.query.filter_by(delivery_guy_id=onboarding_id).order_by(Order.id.desc()).all()
        orders_data = [order.as_dict() for order in orders]
        
        guy_data = {
            "id": onboarding.id,
            "name": f"{onboarding.first_name} {onboarding.last_name}".strip(),
            "phone_number": onboarding.primary_number,
            "email": onboarding.email,
            "vehicle_number": onboarding.vehicle_number,
            "status": "active"
        }
        
        data = {
            "orders": orders_data,
            "delivery_guy": guy_data,
            "onboarding_details": onboarding.as_dict()
        }
        enc = encrypt_payload(data)
        return jsonify({"success": True, "encrypted_data": enc}), 200
    except Exception as e:
        print(f"Get delivery guy orders error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

# ============================================================================
# ORDER STATUS MANAGEMENT
# ============================================================================

@delivery_bp.route("/orders/<int:order_id>/status", methods=["PUT"])
@require_admin_auth
def update_order_status_route(current_admin, order_id):
    """Update order status (for delivery tracking)"""
    try:
        encrypted_data = request.json.get("payload")
        if not encrypted_data:
            return jsonify({"error": "Missing encrypted payload"}), 400

        data = decrypt_payload(encrypted_data)
        new_status = data.get("status")
        delivery_notes = data.get("delivery_notes")
        
        if not new_status:
            return jsonify({"error": "Status is required"}), 400
        
        # Validate status
        valid_statuses = ['confirmed', 'processing', 'shipped', 'out_for_delivery', 'delivered', 'cancelled']
        if new_status not in valid_statuses:
            return jsonify({"error": f"Invalid status. Must be one of: {valid_statuses}"}), 400
        
        order = Order.query.get(order_id)
        if not order:
            return jsonify({"error": "Order not found"}), 404
        
        # Import the order service function
        from services.order_service import update_order_items_status
        
        # Update order items status first
        items_result, items_status_code = update_order_items_status(order_id, new_status)
        if items_status_code != 200:
            return jsonify({"error": items_result.get("error", "Failed to update order items")}), items_status_code
        
        # Update order status
        order.status = new_status
        if delivery_notes:
            order.delivery_notes = (order.delivery_notes or "") + f"\n{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}: {delivery_notes}"
        
        db.session.commit()
        
        # Include order items update info in response
        response_data = {
            "order": order.as_dict(),
            "order_items_updated": items_result.get("total_updated", 0),
            "order_items_skipped": items_result.get("total_skipped", 0)
        }
        enc = encrypt_payload(response_data)
        return jsonify({"success": True, "encrypted_data": enc}), 200
    except Exception as e:
        print(f"Update order status error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@delivery_bp.route("/orders/<int:order_id>/pickup", methods=["POST"])
@require_admin_auth
def pickup_order_route(current_admin, order_id):
    """Mark order as picked up by delivery guy"""
    try:
        encrypted_data = request.json.get("payload")
        if not encrypted_data:
            return jsonify({"error": "Missing encrypted payload"}), 400

        data = decrypt_payload(encrypted_data)
        pickup_notes = data.get("pickup_notes")
        
        order = Order.query.get(order_id)
        if not order:
            return jsonify({"error": "Order not found"}), 404
        
        if not order.delivery_guy_id:
            return jsonify({"error": "Order is not assigned to any delivery guy"}), 400
        
        # Import the order service function
        from services.order_service import update_order_items_status
        
        # Update order items status first
        items_result, items_status_code = update_order_items_status(order_id, "out_for_delivery")
        if items_status_code != 200:
            return jsonify({"error": items_result.get("error", "Failed to update order items")}), items_status_code
        
        # Update order status to out for delivery
        order.status = "out_for_delivery"
        if pickup_notes:
            order.delivery_notes = (order.delivery_notes or "") + f"\nPickup: {pickup_notes}"
        
        db.session.commit()
        
        # Include order items update info in response
        response_data = {
            "order": order.as_dict(),
            "order_items_updated": items_result.get("total_updated", 0),
            "order_items_skipped": items_result.get("total_skipped", 0)
        }
        enc = encrypt_payload(response_data)
        return jsonify({"success": True, "encrypted_data": enc}), 200
    except Exception as e:
        print(f"Pickup order error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@delivery_bp.route("/orders/<int:order_id>/deliver", methods=["POST"])
@require_admin_auth
def deliver_order_route(current_admin, order_id):
    """Mark order as delivered"""
    try:
        encrypted_data = request.json.get("payload")
        if not encrypted_data:
            return jsonify({"error": "Missing encrypted payload"}), 400

        data = decrypt_payload(encrypted_data)
        delivery_notes = data.get("delivery_notes")
        
        order = Order.query.get(order_id)
        if not order:
            return jsonify({"error": "Order not found"}), 404
        
        if not order.delivery_guy_id:
            return jsonify({"error": "Order is not assigned to any delivery guy"}), 400
        
        # Import the order service function
        from services.order_service import update_order_items_status
        
        # Update order items status first
        items_result, items_status_code = update_order_items_status(order_id, "delivered")
        if items_status_code != 200:
            return jsonify({"error": items_result.get("error", "Failed to update order items")}), items_status_code
        
        # Update order status to delivered
        order.status = "delivered"
        if delivery_notes:
            order.delivery_notes = (order.delivery_notes or "") + f"\nDelivered: {delivery_notes}"
        
        db.session.commit()
        
        # Include order items update info in response
        response_data = {
            "order": order.as_dict(),
            "order_items_updated": items_result.get("total_updated", 0),
            "order_items_skipped": items_result.get("total_skipped", 0)
        }
        enc = encrypt_payload(response_data)
        return jsonify({"success": True, "encrypted_data": enc}), 200
    except Exception as e:
        print(f"Deliver order error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
