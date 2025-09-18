# routes/delivery_onboarding.py
# routes/delivery_onboarding.py
from flask import Blueprint, request, jsonify
from services.delivery_onboarding_service import (
    create_onboarding,
    get_onboarding_by_id,
    get_onboarding_by_email,
    update_onboarding,
    delete_onboarding,
    get_all_onboarding,
    approve_onboarding,
    reject_onboarding,
    upload_file
)
from services.delivery_auth_service import verify_auth_token
from utils.auth import require_admin_auth
from utils.crypto import encrypt_payload, decrypt_payload
from werkzeug.utils import secure_filename
from extensions import db  # Add this import
from models.delivery_onboarding import DeliveryOnboarding  # Add this import
from models.delivery_auth import DeliveryGuyAuth  # Add this import
import os
from datetime import datetime

delivery_onboarding_bp = Blueprint("delivery_onboarding", __name__)
UPLOAD_FOLDER = "uploads/documents"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# Mobile app routes (require delivery guy auth)
@delivery_onboarding_bp.route("/onboard", methods=["POST"])
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
        
        # Handle file uploads - all document fields
        print(f"\n🔍 [DEBUG SUBMIT ONBOARDING] Processing files for email: {email}")
        print(f"🔍 [DEBUG] Available files: {list(request.files.keys())}")
        print(f"🔍 [DEBUG] Form data received: {data}")
        
        # Document photo fields (for S3 upload) - using existing column names
        doc_photo_fields = ["aadhar_card", "pan_card", "dl", "rc_card", "bank_passbook"]
        
        print(f"🔍 [DEBUG] Checking {len(doc_photo_fields)} document fields: {doc_photo_fields}")
        
        for field in doc_photo_fields:
            if field in request.files:
                file = request.files[field]
                print(f"🔍 [DEBUG] Found {field} file: filename='{file.filename}', content_type='{file.content_type}', size={file.content_length if hasattr(file, 'content_length') else 'unknown'}")
                
                if file.filename:
                    print(f"🔍 [DEBUG] Processing {field}: {file.filename}")
                    uploaded_path = upload_file(file, "onboarding/documents")
                    if uploaded_path:
                        data[field] = uploaded_path
                        print(f"✅ [SUCCESS] Uploaded {field} to S3: {uploaded_path}")
                        print(f"🔍 [DEBUG] Updated data[{field}] = {uploaded_path}")
                    else:
                        print(f"❌ [ERROR] Failed to upload {field}")
                else:
                    print(f"⚠️ [WARNING] {field} file has no filename")
            else:
                print(f"ℹ️ [INFO] {field} not found in request files")
        
        # Handle profile picture separately (different folder)
        if 'profile_picture' in request.files:
            profile_pic = request.files['profile_picture']
            print(f"🔍 [DEBUG] Found profile_picture file: filename='{profile_pic.filename}', content_type='{profile_pic.content_type}', size={profile_pic.content_length if hasattr(profile_pic, 'content_length') else 'unknown'}")
            
            if profile_pic.filename:
                print(f"🔍 [DEBUG] Processing profile_picture: {profile_pic.filename}")
                profile_path = upload_file(profile_pic, "onboarding/profile")
                if profile_path:
                    data['profile_picture'] = profile_path
                    print(f"✅ [SUCCESS] Uploaded profile_picture to S3: {profile_path}")
                    print(f"🔍 [DEBUG] Updated data[profile_picture] = {profile_path}")
                else:
                    print(f"❌ [ERROR] Failed to upload profile_picture")
            else:
                print(f"⚠️ [WARNING] profile_picture file has no filename")
        else:
            print(f"ℹ️ [INFO] profile_picture not found in request files")
        
        print(f"🔍 [DEBUG] Final data to be saved: {data}")
        print(f"🔍 [DEBUG] Images in data: {[(k, v) for k, v in data.items() if k in ['profile_picture', 'aadhar_card', 'pan_card', 'dl', 'rc_card', 'bank_passbook']]}")
        
        # Create onboarding with mobile app data structure
        result = create_onboarding_mobile(data, email)
        
        if result["success"]:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        print(f"Submit onboarding error: {str(e)}")
        return jsonify({"success": False, "message": "Internal server error"}), 500

# Add this new function to handle mobile app data structure
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
            existing_onboarding.updated_at = datetime.utcnow()
            existing_onboarding.vehicle_number = data.get('vehicle_number', '')
            existing_onboarding.bank_account_number = data.get('bank_account_number', '')
            existing_onboarding.ifsc_code = data.get('ifsc_code', '')
            
            existing_onboarding.name_as_per_bank = data.get('name_as_per_bank')
            
            db.session.commit()
            
            return {
                "success": True, 
                "message": "Profile updated successfully! Please upload required documents.",
                "onboarding_id": existing_onboarding.id,
                "user_status": "profile_incomplete",
                "next_step": "documents"
            }
        
        # Create new onboarding record if none exists
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
            status='profile_incomplete'  # Mark as profile incomplete until documents are uploaded
        )
        
        db.session.add(onboarding)
        db.session.commit()
        
        # Update auth user to mark as profile created and sync phone number
        auth_user = DeliveryGuyAuth.query.filter_by(email=email).first()
        if auth_user:
            # Sync the phone number from onboarding to auth user
            if auth_user.phone_number != data.get('primary_number'):
                print(f"Syncing phone number: {auth_user.phone_number} -> {data.get('primary_number')}")
                auth_user.phone_number = data.get('primary_number')
            
            auth_user.is_onboarded = False  # Keep false until documents are uploaded
            db.session.commit()
        
        return {
            "success": True, 
            "message": "Profile created successfully! Please upload required documents.",
            "onboarding_id": onboarding.id,
            "user_status": "profile_incomplete",
            "next_step": "documents"
        }
        
    except Exception as e:
        db.session.rollback()
        print(f"Error creating onboarding: {e}")
        return {"success": False, "message": "Failed to create profile"}

# ... rest of your existing code ...
@delivery_onboarding_bp.route("/onboard", methods=["GET"])
def get_user_onboarding():
    """Get user's onboarding status from mobile app"""
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
        
        # Get onboarding
        result = get_onboarding_by_email(email)
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 404
            
    except Exception as e:
        print(f"Get user onboarding error: {str(e)}")
        return jsonify({"success": False, "message": "Internal server error"}), 500

@delivery_onboarding_bp.route("/profile", methods=["GET"])
def get_delivery_profile():
    """Return basic profile for logged-in delivery user (via Bearer token)."""
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Missing or invalid authorization header"}), 401

        token = auth_header.split(' ')[1]
        token_validation = verify_auth_token(token)
        if not token_validation["success"]:
            return jsonify({"error": token_validation["message"]}), 401

        user = token_validation["user"]
        email = user.get("email")
        if not email:
            return jsonify({"error": "Email not present in token"}), 400

        onboarding = DeliveryOnboarding.query.filter_by(email=email).first()
        if not onboarding:
            return jsonify({"error": "Delivery user not found"}), 404

        data = {
            "delivery_guy": {
                "id": onboarding.id,
                "first_name": onboarding.first_name,
                "last_name": onboarding.last_name,
                "email": onboarding.email,
                "phone_number": onboarding.primary_number,
                "status": onboarding.status,
            }
        }
        enc = encrypt_payload(data)
        return jsonify({"success": True, "encrypted_data": enc}), 200
    except Exception as e:
        print(f"Get delivery profile error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@delivery_onboarding_bp.route("/profile/by-email", methods=["GET"])
def get_delivery_profile_by_email():
    """Return basic profile for a delivery user by email (protected)."""
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Missing or invalid authorization header"}), 401

        token = auth_header.split(' ')[1]
        token_validation = verify_auth_token(token)
        if not token_validation["success"]:
            return jsonify({"error": token_validation["message"]}), 401

        email = request.args.get("email")
        if not email:
            return jsonify({"error": "email is required"}), 400

        onboarding = DeliveryOnboarding.query.filter_by(email=email).first()
        if not onboarding:
            return jsonify({"error": "Delivery user not found"}), 404

        data = {
            "delivery_guy": {
                "id": onboarding.id,
                "first_name": onboarding.first_name,
                "last_name": onboarding.last_name,
                "email": onboarding.email,
                "phone_number": onboarding.primary_number,
                "status": onboarding.status,
            }
        }
        enc = encrypt_payload(data)
        return jsonify({"success": True, "encrypted_data": enc}), 200
    except Exception as e:
        print(f"Get delivery profile by email error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@delivery_onboarding_bp.route("/onboard", methods=["PUT"])
def update_user_onboarding():
    """Update user's onboarding from mobile app"""
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
        
        # Get current onboarding to get ID
        current_onboarding = get_onboarding_by_email(email)
        if not current_onboarding["success"]:
            return jsonify({"success": False, "message": "Onboarding not found"}), 404
        
        onboarding_id = current_onboarding["onboarding"]["id"]
        
        # Get form data
        data = request.form.to_dict()
        
        # Handle file uploads - all document fields
        print(f"\n🔍 [DEBUG UPDATE ONBOARDING] Processing files for email: {email}")
        print(f"🔍 [DEBUG] Available files: {list(request.files.keys())}")
        print(f"🔍 [DEBUG] Form data received: {data}")
        
        # Document photo fields (for S3 upload) - using existing column names
        doc_photo_fields = ["aadhar_card", "pan_card", "dl", "rc_card", "bank_passbook"]
        
        print(f"🔍 [DEBUG] Checking {len(doc_photo_fields)} document fields: {doc_photo_fields}")
        
        for field in doc_photo_fields:
            if field in request.files:
                file = request.files[field]
                print(f"🔍 [DEBUG] Found {field} file: filename='{file.filename}', content_type='{file.content_type}', size={file.content_length if hasattr(file, 'content_length') else 'unknown'}")
                
                if file.filename:
                    print(f"🔍 [DEBUG] Processing {field}: {file.filename}")
                    uploaded_path = upload_file(file, "onboarding/documents")
                    if uploaded_path:
                        data[field] = uploaded_path
                        print(f"✅ [SUCCESS] Uploaded {field} to S3: {uploaded_path}")
                        print(f"🔍 [DEBUG] Updated data[{field}] = {uploaded_path}")
                    else:
                        print(f"❌ [ERROR] Failed to upload {field}")
                else:
                    print(f"⚠️ [WARNING] {field} file has no filename")
            else:
                print(f"ℹ️ [INFO] {field} not found in request files")
        
        # Handle profile picture separately (different folder)
        if 'profile_picture' in request.files:
            profile_pic = request.files['profile_picture']
            print(f"🔍 [DEBUG] Found profile_picture file: filename='{profile_pic.filename}', content_type='{profile_pic.content_type}', size={profile_pic.content_length if hasattr(profile_pic, 'content_length') else 'unknown'}")
            
            if profile_pic.filename:
                print(f"🔍 [DEBUG] Processing profile_picture: {profile_pic.filename}")
                profile_path = upload_file(profile_pic, "onboarding/profile")
                if profile_path:
                    data['profile_picture'] = profile_path
                    print(f"✅ [SUCCESS] Uploaded profile_picture to S3: {profile_path}")
                    print(f"🔍 [DEBUG] Updated data[profile_picture] = {profile_path}")
                else:
                    print(f"❌ [ERROR] Failed to upload profile_picture")
            else:
                print(f"⚠️ [WARNING] profile_picture file has no filename")
        else:
            print(f"ℹ️ [INFO] profile_picture not found in request files")
        
        print(f"🔍 [DEBUG] Final data to be updated: {data}")
        print(f"🔍 [DEBUG] Images in data: {[(k, v) for k, v in data.items() if k in ['profile_picture', 'aadhar_card', 'pan_card', 'dl', 'rc_card', 'bank_passbook']]}")
        
        # Update onboarding
        result = update_onboarding(onboarding_id, data)
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        print(f"Update user onboarding error: {str(e)}")
        return jsonify({"success": False, "message": "Internal server error"}), 500

# Admin routes (require admin auth)
@delivery_onboarding_bp.route("/admin/onboarding", methods=["GET"])
@require_admin_auth
def get_all_onboarding_admin(current_admin):
    """Get all onboarding records for admin panel"""
    try:
        status = request.args.get('status')
        result = get_all_onboarding(status)
        
        if result["success"]:
            data = {"onboarding_records": result["onboarding_records"]}
            enc = encrypt_payload(data)
            return jsonify({"success": True, "encrypted_data": enc}), 200
        else:
            return jsonify({"success": False, "message": result["message"]}), 400
            
    except Exception as e:
        print(f"Get all onboarding admin error: {str(e)}")
        return jsonify({"success": False, "message": "Internal server error"}), 500

@delivery_onboarding_bp.route("/admin/onboarding/<int:onboarding_id>", methods=["GET"])
@require_admin_auth
def get_onboarding_by_id_admin(current_admin, onboarding_id):
    """Get specific onboarding record for admin panel"""
    try:
        result = get_onboarding_by_id(onboarding_id)
        
        if result["success"]:
            data = {"onboarding": result["onboarding"]}
            enc = encrypt_payload(data)
            return jsonify({"success": True, "encrypted_data": enc}), 200
        else:
            return jsonify({"success": False, "message": result["message"]}), 404
            
    except Exception as e:
        print(f"Get onboarding by ID admin error: {str(e)}")
        return jsonify({"success": False, "message": "Internal server error"}), 500

@delivery_onboarding_bp.route("/admin/onboarding/<int:onboarding_id>/approve", methods=["POST"])
@require_admin_auth
def approve_onboarding_admin(current_admin, onboarding_id):
    """Approve onboarding from admin panel"""
    try:
        encrypted_data = request.json.get("payload")
        if not encrypted_data:
            return jsonify({"success": False, "message": "Missing encrypted payload"}), 400

        data = decrypt_payload(encrypted_data)
        notes = data.get('notes')
        
        result = approve_onboarding(onboarding_id, current_admin.id, notes)
        
        if result["success"]:
            data = {"message": result["message"], "delivery_guy": result["delivery_guy"]}
            enc = encrypt_payload(data)
            return jsonify({"success": True, "encrypted_data": enc}), 200
        else:
            return jsonify({"success": False, "message": result["message"]}), 400
            
    except Exception as e:
        print(f"Approve onboarding admin error: {str(e)}")
        return jsonify({"success": False, "message": "Internal server error"}), 500

@delivery_onboarding_bp.route("/admin/onboarding/<int:onboarding_id>/reject", methods=["POST"])
@require_admin_auth
def reject_onboarding_admin(current_admin, onboarding_id):
    """Reject onboarding from admin panel"""
    try:
        encrypted_data = request.json.get("payload")
        if not encrypted_data:
            return jsonify({"success": False, "message": "Missing encrypted payload"}), 400

        data = decrypt_payload(encrypted_data)
        notes = data.get('notes')
        
        if not notes:
            return jsonify({"success": False, "message": "Rejection notes are required"}), 400
        
        result = reject_onboarding(onboarding_id, current_admin.id, notes)
        
        if result["success"]:
            data = {"message": result["message"]}
            enc = encrypt_payload(data)
            return jsonify({"success": True, "encrypted_data": enc}), 200
        else:
            return jsonify({"success": False, "message": result["message"]}), 400
            
    except Exception as e:
        print(f"Reject onboarding admin error: {str(e)}")
        return jsonify({"success": False, "message": "Internal server error"}), 500

@delivery_onboarding_bp.route("/admin/onboarding/<int:onboarding_id>", methods=["DELETE"])
@require_admin_auth
def delete_onboarding_admin(current_admin, onboarding_id):
    """Delete onboarding from admin panel"""
    try:
        result = delete_onboarding(onboarding_id)
        
        if result["success"]:
            data = {"message": result["message"]}
            enc = encrypt_payload(data)
            return jsonify({"success": True, "encrypted_data": enc}), 200
        else:
            return jsonify({"success": False, "message": result["message"]}), 400
            
    except Exception as e:
        print(f"Delete onboarding admin error: {str(e)}")
        return jsonify({"success": False, "message": "Internal server error"}), 500

@delivery_onboarding_bp.route("/admin/onboarding/<int:onboarding_id>", methods=["PUT"])
@require_admin_auth
def update_onboarding_admin(current_admin, onboarding_id):
    """Update onboarding from admin panel"""
    try:
        encrypted_data = request.json.get("payload")
        if not encrypted_data:
            return jsonify({"success": False, "message": "Missing encrypted payload"}), 400

        data = decrypt_payload(encrypted_data)
        
        result = update_onboarding(onboarding_id, data)
        
        if result["success"]:
            data = {"message": result["message"], "onboarding": result["onboarding"]}
            enc = encrypt_payload(data)
            return jsonify({"success": True, "encrypted_data": enc}), 200
        else:
            return jsonify({"success": False, "message": result["message"]}), 400
            
    except Exception as e:
        print(f"Update onboarding admin error: {str(e)}")
        return jsonify({"success": False, "message": "Internal server error"}), 500
@delivery_onboarding_bp.route("/documents", methods=["POST","GET"])
def upload_documents():
    """
    Upload or update onboarding documents for a delivery user.
    """
    try:
        # --- Validate token ---
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"success": False, "message": "Invalid or missing Authorization header"}), 401

        token = auth_header.split(' ')[1]
        token_validation = verify_auth_token(token)
        if not token_validation["success"]:
            return jsonify({"success": False, "message": token_validation["message"]}), 401

        user = token_validation["user"]
        email = user["email"]

        # --- Upload files ---
        # Document photo fields (for S3 upload) - using existing column names
        doc_photo_fields = ["aadhar_card", "pan_card", "dl", "rc_card", "bank_passbook"]
        uploaded_docs = {}

        print(f"\n🔍 [DEBUG DOCUMENT UPLOAD] Processing files for email: {email}")
        print(f"🔍 [DEBUG] Available files: {list(request.files.keys())}")

        # Handle document fields
        for field in doc_photo_fields:
            if field in request.files:
                file = request.files[field]
                print(f"🔍 [DEBUG] Found {field} file: filename='{file.filename}', content_type='{file.content_type}', size={file.content_length if hasattr(file, 'content_length') else 'unknown'}")
                
                if file.filename:
                    print(f"🔍 [DEBUG] Processing {field}: {file.filename}")
                    uploaded_docs[field] = upload_file(file, "onboarding/documents")
                    if uploaded_docs[field]:
                        print(f"✅ [SUCCESS] Uploaded {field} to S3: {uploaded_docs[field]}")
                    else:
                        print(f"❌ [ERROR] Failed to upload {field}")
                else:
                    print(f"⚠️ [WARNING] {field} file has no filename")
            else:
                print(f"ℹ️ [INFO] {field} not found in request files")

        # Handle profile picture separately (different folder)
        if 'profile_picture' in request.files:
            profile_pic = request.files['profile_picture']
            print(f"🔍 [DEBUG] Found profile_picture file: filename='{profile_pic.filename}', content_type='{profile_pic.content_type}', size={profile_pic.content_length if hasattr(profile_pic, 'content_length') else 'unknown'}")
            
            if profile_pic.filename:
                print(f"🔍 [DEBUG] Processing profile_picture: {profile_pic.filename}")
                profile_path = upload_file(profile_pic, "onboarding/profile")
                if profile_path:
                    uploaded_docs['profile_picture'] = profile_path
                    print(f"✅ [SUCCESS] Uploaded profile_picture to S3: {profile_path}")
                else:
                    print(f"❌ [ERROR] Failed to upload profile_picture")
            else:
                print(f"⚠️ [WARNING] profile_picture file has no filename")
        else:
            print(f"ℹ️ [INFO] profile_picture not found in request files")

        print(f"🔍 [DEBUG] Total uploaded docs: {len(uploaded_docs)}")
        print(f"🔍 [DEBUG] Uploaded files: {uploaded_docs}")

        # --- Create or update onboarding record ---
        onboarding = DeliveryOnboarding.query.filter_by(email=email).first()
        if onboarding:
            print(f"🔍 [DEBUG] Found existing onboarding record: {onboarding.id}")
            print(f"🔍 [DEBUG] Current image fields before update:")
            image_fields = ['profile_picture', 'aadhar_card', 'pan_card', 'dl', 'rc_card', 'bank_passbook']
            for field in image_fields:
                current_value = getattr(onboarding, field, None)
                print(f"  - {field}: {current_value}")
            
            # Update existing record
            for field, path in uploaded_docs.items():
                print(f"🔍 [DEBUG] Updating {field} with: {path}")
                setattr(onboarding, field, path)
            onboarding.status = "documents_submitted"
            onboarding.updated_at = datetime.utcnow()
            
            print(f"🔍 [DEBUG] Committing to database...")
            db.session.commit()
            print(f"✅ [SUCCESS] Database updated successfully")
            
            # Print final image fields after update
            print(f"🔍 [DEBUG] Final image fields after update:")
            for field in image_fields:
                final_value = getattr(onboarding, field, None)
                print(f"  - {field}: {final_value}")

            return jsonify({
                "success": True,
                "message": "Documents updated successfully! Pending verification.",
                "onboarding_id": onboarding.id,
                "user_status": onboarding.status,
                "next_step": "wait_verification"
            }), 200

        else:
            print(f"[DOCUMENT UPLOAD] No existing onboarding record found for email: {email}")
            # Create new onboarding with documents only
            onboarding = DeliveryOnboarding(
                email=email,
                status="documents_submitted",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                **uploaded_docs
            )
            print(f"[DOCUMENT UPLOAD] Creating new onboarding record with documents: {uploaded_docs}")
            db.session.add(onboarding)
            db.session.commit()
            print(f"[DOCUMENT UPLOAD] New onboarding record created: {onboarding.id}")

            return jsonify({
                "success": True,
                "message": "Documents uploaded successfully! Pending verification.",
                "onboarding_id": onboarding.id,
                "user_status": onboarding.status,
                "next_step": "wait_verification"
            }), 201

    except Exception as e:
        db.session.rollback()
        print(f"[DOCUMENT UPLOAD] Error: {e}")
        import traceback
        print(f"[DOCUMENT UPLOAD] Traceback: {traceback.format_exc()}")
        return jsonify({"success": False, "message": f"Internal server error: {str(e)}"}), 500
