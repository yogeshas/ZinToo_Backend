# services/delivery_onboarding_service.py
from models.delivery_onboarding import DeliveryOnboarding
from models.delivery_auth import DeliveryGuyAuth
from extensions import db
from datetime import datetime
from services.delivery_email_service import send_approval_email, send_rejection_email
import os
import uuid

def create_onboarding(data, email):
    """Create new onboarding record"""
    try:
        # Check if user already has onboarding
        existing_onboarding = DeliveryOnboarding.query.filter_by(
            primary_number=data.get('primary_number')
        ).first()
        
        if existing_onboarding:
            return {"success": False, "message": "Phone number already registered for onboarding"}
        
        # Check if Aadhar, PAN, DL, or vehicle number already exists
        if data.get('aadhar_card'):
            existing_aadhar = DeliveryOnboarding.query.filter_by(
                aadhar_card=data['aadhar_card']
            ).first()
            if existing_aadhar:
                return {"success": False, "message": "Aadhar card already registered"}
        
        if data.get('pan_card'):
            existing_pan = DeliveryOnboarding.query.filter_by(
                pan_card=data['pan_card']
            ).first()
            if existing_pan:
                return {"success": False, "message": "PAN card already registered"}
        
        if data.get('dl'):
            existing_dl = DeliveryOnboarding.query.filter_by(
                dl=data['dl']
            ).first()
            if existing_dl:
                return {"success": False, "message": "Driving license already registered"}
        
        if data.get('vehicle_number'):
            existing_vehicle = DeliveryOnboarding.query.filter_by(
                vehicle_number=data['vehicle_number']
            ).first()
            if existing_vehicle:
                return {"success": False, "message": "Vehicle number already registered"}
        
        # Create onboarding record
        onboarding = DeliveryOnboarding(
            first_name=data['first_name'],
            last_name=data['last_name'],
            dob=datetime.strptime(data['dob'], '%Y-%m-%d').date(),
            primary_number=data['primary_number'],
            secondary_number=data.get('secondary_number'),
            blood_group=data.get('blood_group'),
            address=data['address'],
            language=data.get('language', 'English'),
            profile_picture=data.get('profile_picture'),
            referral_code=data.get('referral_code'),
            aadhar_card=data['aadhar_card'],
            pan_card=data['pan_card'],
            dl=data['dl'],
            vehicle_number=data['vehicle_number'],
            rc_card=data.get('rc_card'),
            bank_account_number=data['bank_account_number'],
            ifsc_code=data['ifsc_code'],
            bank_passbook=data.get('bank_passbook'),
            name_as_per_bank=data['name_as_per_bank'],
            status='pending'
        )
        
        db.session.add(onboarding)
        db.session.commit()
        
        # Update auth user to mark as onboarded
        auth_user = DeliveryGuyAuth.query.filter_by(email=email).first()
        if auth_user:
            auth_user.is_onboarded = True
            db.session.commit()
        
        return {
            "success": True, 
            "message": "Onboarding submitted successfully",
            "onboarding": onboarding.as_dict()
        }
        
    except Exception as e:
        db.session.rollback()
        print(f"Error creating onboarding: {e}")
        return {"success": False, "message": "Failed to create onboarding"}

def get_onboarding_by_id(onboarding_id):
    """Get onboarding record by ID"""
    try:
        onboarding = DeliveryOnboarding.query.get(onboarding_id)
        if not onboarding:
            return {"success": False, "message": "Onboarding not found"}
        
        return {"success": True, "onboarding": onboarding.as_dict()}
        
    except Exception as e:
        print(f"Error getting onboarding: {e}")
        return {"success": False, "message": "Failed to get onboarding"}

def get_onboarding_by_email(email):
    """Get onboarding record by email"""
    try:
        print(f"Looking for onboarding for email: {email}")
        
        # Now we always save email, so search directly by email
        onboarding = DeliveryOnboarding.query.filter_by(email=email).first()
        
        if not onboarding:
            print(f"Onboarding not found for email: {email}")
            return {"success": False, "message": "Onboarding not found"}
        
        print(f"Found onboarding for user: {onboarding.first_name} {onboarding.last_name}")
        return {"success": True, "onboarding": onboarding.as_dict()}
        
    except Exception as e:
        print(f"Error getting onboarding by email: {e}")
        return {"success": False, "message": "Failed to get onboarding"}

def update_onboarding(onboarding_id, data):
    """Update onboarding record"""
    try:
        onboarding = DeliveryOnboarding.query.get(onboarding_id)
        if not onboarding:
            return {"success": False, "message": "Onboarding not found"}
        
        # Update fields
        for field, value in data.items():
            if hasattr(onboarding, field) and field not in ['id', 'created_at', 'updated_at']:
                if field == 'dob' and value:
                    setattr(onboarding, field, datetime.strptime(value, '%Y-%m-%d').date())
                else:
                    setattr(onboarding, field, value)
        
        onboarding.updated_at = datetime.utcnow()
        db.session.commit()
        
        return {
            "success": True, 
            "message": "Onboarding updated successfully",
            "onboarding": onboarding.as_dict()
        }
        
    except Exception as e:
        db.session.rollback()
        print(f"Error updating onboarding: {e}")
        return {"success": False, "message": "Failed to update onboarding"}

def delete_onboarding(onboarding_id):
    """Delete onboarding record"""
    try:
        onboarding = DeliveryOnboarding.query.get(onboarding_id)
        if not onboarding:
            return {"success": False, "message": "Onboarding not found"}
        
        # Delete associated files
        if onboarding.profile_picture:
            try:
                os.remove(onboarding.profile_picture)
            except:
                pass
        
        if onboarding.rc_card:
            try:
                os.remove(onboarding.rc_card)
            except:
                pass
        
        if onboarding.bank_passbook:
            try:
                os.remove(onboarding.bank_passbook)
            except:
                pass
        
        db.session.delete(onboarding)
        db.session.commit()
        
        return {"success": True, "message": "Onboarding deleted successfully"}
        
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting onboarding: {e}")
        return {"success": False, "message": "Failed to delete onboarding"}

def get_all_onboarding(status=None):
    """Get all onboarding records with optional status filter"""
    try:
        query = DeliveryOnboarding.query
        
        if status:
            query = query.filter_by(status=status)
        
        onboarding_records = query.order_by(DeliveryOnboarding.created_at.desc()).all()
        
        return {
            "success": True, 
            "onboarding_records": [record.as_dict() for record in onboarding_records]
        }
        
    except Exception as e:
        print(f"Error getting all onboarding: {e}")
        return {"success": False, "message": "Failed to get onboarding records"}

def approve_onboarding(onboarding_id, admin_id, notes=None):
    """Approve onboarding"""
    try:
        print(f"🔍 Attempting to approve onboarding ID: {onboarding_id}")
        onboarding = DeliveryOnboarding.query.get(onboarding_id)
        if not onboarding:
            print(f"❌ Onboarding not found for ID: {onboarding_id}")
            return {"success": False, "message": "Onboarding not found"}
        
        print(f"📋 Onboarding found - Status: {onboarding.status}, Email: {onboarding.email}")
        
        # Allow approval from pending, documents_submitted, or profile_incomplete status
        valid_statuses = ['pending', 'documents_submitted', 'profile_incomplete']
        if onboarding.status not in valid_statuses:
            print(f"❌ Invalid status for approval: {onboarding.status}. Valid statuses: {valid_statuses}")
            return {"success": False, "message": f"Onboarding is not in a valid status for approval. Current status: {onboarding.status}"}
        
        print(f"✅ Status check passed. Proceeding with approval...")
        
        # Update onboarding status
        onboarding.update_status('approved', admin_id, notes)
        
        # CRITICAL FIX: Set delivery_guy_id to the onboarding ID itself
        # This links the onboarding record to the delivery guy system
        onboarding.delivery_guy_id = onboarding.id
        print(f"🔗 Set delivery_guy_id to onboarding ID: {onboarding.id}")
        
        # Update auth user if exists (check by email first, then phone number)
        auth_user = None
        if onboarding.email:
            auth_user = DeliveryGuyAuth.query.filter_by(email=onboarding.email).first()
            print(f"🔍 Looking for auth user by email: {onboarding.email}")
        
        if not auth_user and onboarding.primary_number:
            auth_user = DeliveryGuyAuth.query.filter_by(phone_number=onboarding.primary_number).first()
            print(f"🔍 Looking for auth user by phone: {onboarding.primary_number}")
        
        if auth_user:
            auth_user.is_onboarded = True  # Mark as onboarded
            # CRITICAL FIX: Link the auth user to the delivery guy
            auth_user.delivery_guy_id = onboarding.id
            print(f"✅ Updated auth user - is_onboarded: True, delivery_guy_id: {onboarding.id}")
        else:
            print(f"⚠️ No auth user found for email: {onboarding.email} or phone: {onboarding.primary_number}")
        
        db.session.commit()
        
        # Send approval email
        if onboarding.email:
            delivery_guy_name = f"{onboarding.first_name} {onboarding.last_name}".strip()
            if not delivery_guy_name:
                delivery_guy_name = "Delivery Personnel"
            
            email_sent = send_approval_email(onboarding.email, delivery_guy_name)
            if email_sent:
                print(f"✅ Approval email sent to {onboarding.email}")
            else:
                print(f"❌ Failed to send approval email to {onboarding.email}")
        
        return {
            "success": True, 
            "message": "Onboarding approved successfully. Approval email sent.",
            "onboarding": onboarding.as_dict()
        }
        
    except Exception as e:
        db.session.rollback()
        print(f"Error approving onboarding: {e}")
        return {"success": False, "message": "Failed to approve onboarding"}

def reject_onboarding(onboarding_id, admin_id, notes):
    """Reject onboarding"""
    try:
        onboarding = DeliveryOnboarding.query.get(onboarding_id)
        if not onboarding:
            return {"success": False, "message": "Onboarding not found"}
        
        onboarding.update_status('rejected', admin_id, notes)
        
        # Update auth user if exists (check by email first, then phone number)
        auth_user = None
        if onboarding.email:
            auth_user = DeliveryGuyAuth.query.filter_by(email=onboarding.email).first()
            print(f"🔍 Looking for auth user by email: {onboarding.email}")
        
        if not auth_user and onboarding.primary_number:
            auth_user = DeliveryGuyAuth.query.filter_by(phone_number=onboarding.primary_number).first()
            print(f"🔍 Looking for auth user by phone: {onboarding.primary_number}")
        
        if auth_user:
            auth_user.is_onboarded = False  # Mark as not onboarded when rejected
            print(f"✅ Updated auth user - is_onboarded: False (rejected)")
        else:
            print(f"⚠️ No auth user found for email: {onboarding.email} or phone: {onboarding.primary_number}")
        
        db.session.commit()
        
        # Send rejection email with reason
        if onboarding.email:
            delivery_guy_name = f"{onboarding.first_name} {onboarding.last_name}".strip()
            if not delivery_guy_name:
                delivery_guy_name = "Delivery Personnel"
            
            email_sent = send_rejection_email(onboarding.email, delivery_guy_name, notes)
            if email_sent:
                print(f"✅ Rejection email sent to {onboarding.email}")
            else:
                print(f"❌ Failed to send rejection email to {onboarding.email}")
        
        return {"success": True, "message": "Onboarding rejected successfully. Rejection email sent with reason."}
        
    except Exception as e:
        print(f"Error rejecting onboarding: {e}")
        return {"success": False, "message": "Failed to reject onboarding"}

def out_for_delivery_order_by_delivery_guy(delivery_guy_id, order_id, out_for_delivery_reason):
    """Out for delivery an order by delivery guy"""
    try:
        order = Order.query.get(order_id)
        if not order:
            return {"success": False, "message": "Order not found"}
        
        order.update_status('out_for_delivery', delivery_guy_id, out_for_delivery_reason)
        
        return {"success": True, "message": "Order out for delivery successfully"}
        
    except Exception as e:
        print(f"Error out for delivery order: {e}")
        return {"success": False, "message": "Failed to out for delivery order"}

def reject_order_by_delivery_guy(delivery_guy_id, order_id, rejection_reason):
    """Reject an order by delivery guy"""
    try:
        order = Order.query.get(order_id)
        if not order:
            return {"success": False, "message": "Order not found"}
        
        order.update_status('rejected', delivery_guy_id, rejection_reason)
        
        return {"success": True, "message": "Order rejected successfully"}
        
    except Exception as e:
        print(f"Error rejecting order: {e}")
        return {"success": False, "message": "Failed to reject order"}

def delivered_order_by_delivery_guy(delivery_guy_id, order_id, delivered_reason):
    """Delivered an order by delivery guy"""
    try:
        order = Order.query.get(order_id)
        if not order:
            return {"success": False, "message": "Order not found"}
        
        order.update_status('delivered', delivery_guy_id, delivered_reason)
        
        return {"success": True, "message": "Order delivered successfully"}
        
    except Exception as e:
        print(f"Error delivering order: {e}")
        return {"success": False, "message": "Failed to deliver order"}


def upload_file(file, folder="onboarding"):
    """Upload file and return path"""
    try:
        if not file:
            return None
        
        # Create upload directory if it doesn't exist
        upload_dir = os.path.join('assets', folder)
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        filename = f"{uuid.uuid4()}_{file.filename}"
        file_path = os.path.join(upload_dir, filename)
        
        # Save file
        file.save(file_path)
        
        return file_path
        
    except Exception as e:
        print(f"Error uploading file: {e}")
        return None
