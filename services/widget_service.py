# services/widget_service.py
import os
import json
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from models.widget import Widget
from extensions import db
from utils.crypto import encrypt_payload, decrypt_payload
from utils.s3_service import S3Service

# Image upload configuration
UPLOAD_FOLDER = 'assets/img/widgets'  # Keep for backward compatibility
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# Initialize S3 service
s3_service = S3Service()

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_widget_images(files, widget_id):
    """Save multiple widget images to S3 and return their URLs"""
    image_urls = []
    
    for file in files:
        if file and file.filename and allowed_file(file.filename):
            try:
                # Upload to S3
                s3_url = s3_service.upload_file(
                    file=file,
                    file_id=widget_id,
                    file_type="image",
                    folder_type="widget"
                )
                
                if s3_url:
                    image_urls.append(s3_url)
                    print(f"✅ Widget image uploaded to S3: {s3_url}")
                else:
                    print(f"❌ Failed to upload widget image: {file.filename}")
                    
            except Exception as e:
                print(f"❌ Error uploading widget image {file.filename}: {str(e)}")
                # Continue with other files even if one fails
    
    return image_urls

def delete_widget_images(image_paths):
    """Delete widget images from S3 and local filesystem"""
    if not image_paths:
        return
    
    # Parse JSON if it's a string
    if isinstance(image_paths, str):
        try:
            image_paths = json.loads(image_paths)
        except:
            return
    
    for image_path in image_paths:
        if not image_path:
            continue
            
        try:
            # Check if it's an S3 URL
            if image_path.startswith('https://') and 's3' in image_path:
                # Extract S3 key from URL
                s3_key = image_path.split('.com/')[-1] if '.com/' in image_path else image_path
                
                # Delete from S3
                s3_service.s3_client.delete_object(
                    Bucket=s3_service.bucket_name,
                    Key=s3_key
                )
                print(f"✅ Deleted widget image from S3: {image_path}")
                
            else:
                # Delete from local filesystem (backward compatibility)
                os_path = image_path.replace('/', os.sep)
                if os.path.exists(os_path):
                    os.remove(os_path)
                    print(f"✅ Deleted widget image from local: {image_path}")
                    
        except Exception as e:
            print(f"❌ Error deleting widget image {image_path}: {str(e)}")

def get_all_widgets():
    """Get all widgets with encryption"""
    try:
        widgets = Widget.query.order_by(Widget.id.desc()).all()
        widgets_data = []
        
        for widget in widgets:
            # Parse images JSON
            images = []
            if widget.images:
                try:
                    images = json.loads(widget.images)
                except:
                    images = []
            
            widget_dict = {
                "id": widget.id,
                "name": widget.name,
                "title": widget.title,
                "type": widget.type,
                "page": widget.page,
                "description": widget.description,
                "images": images,
                "created_at": widget.created_at.isoformat() if widget.created_at else None,
                "updated_at": widget.updated_at.isoformat() if widget.updated_at else None,
                "is_active": widget.is_active
            }
            widgets_data.append(widget_dict)
        
        # Encrypt the response data
        encrypted_data = encrypt_payload({
            "success": True,
            "widgets": widgets_data
        })
        
        return {
            "success": True,
            "encrypted_data": encrypted_data,
            "message": "Widgets retrieved successfully"
        }, 200
        
    except Exception as e:
        print(f"❌ Get widgets error: {str(e)}")
        return {"error": "Failed to retrieve widgets"}, 500

def get_widget_by_id(widget_id):
    """Get widget by ID with encryption"""
    try:
        widget = Widget.query.get(widget_id)
        if not widget:
            return {"error": "Widget not found"}, 404
        
        # Parse images JSON
        images = []
        if widget.images:
            try:
                images = json.loads(widget.images)
            except:
                images = []
        
        widget_data = {
            "id": widget.id,
            "name": widget.name,
            "title": widget.title,
            "type": widget.type,
            "page": widget.page,
            "description": widget.description,
            "images": images,
            "created_at": widget.created_at.isoformat() if widget.created_at else None,
            "updated_at": widget.updated_at.isoformat() if widget.updated_at else None,
            "is_active": widget.is_active
        }
        
        # Encrypt the response data
        encrypted_data = encrypt_payload({
            "success": True,
            "widget": widget_data
        })
        
        return {
            "success": True,
            "encrypted_data": encrypted_data,
            "message": "Widget retrieved successfully"
        }, 200
        
    except Exception as e:
        print(f"❌ Get widget error: {str(e)}")
        return {"error": "Failed to retrieve widget"}, 500

def create_widget(encrypted_data, files=None):
    """Create new widget with encrypted data and images"""
    try:
        # Decrypt the incoming data
        decrypted_data = decrypt_payload(encrypted_data)
        name = decrypted_data.get("name")
        title = decrypted_data.get("title", "")
        widget_type = decrypted_data.get("type", "default")
        description = decrypted_data.get("description", "")
        page = decrypted_data.get("page", "home")
        
        if not name:
            return {"error": "Widget name is required"}, 400
        
        # Allow multiple widgets with same name - removed restriction
        # existing_widget = Widget.query.filter_by(name=name).first()
        # if existing_widget:
        #     return {"error": "Widget with this name already exists"}, 400
        
        # Create new widget first to get ID
        new_widget = Widget(
            name=name,
            title=title,
            type=widget_type,
            description=description,
            page=page,
            images="[]",  # Start with empty images
            is_active=True
        )
        
        db.session.add(new_widget)
        db.session.flush()  # Get the ID without committing
        
        # Handle image uploads if files provided
        image_paths = []
        if files:
            image_paths = save_widget_images(files, new_widget.id)
        
        # Update widget with image paths
        if image_paths:
            new_widget.images = json.dumps(image_paths)
        
        db.session.commit()
        
        # Return encrypted response
        widget_data = {
            "id": new_widget.id,
            "name": new_widget.name,
            "title": new_widget.title,
            "type": new_widget.type,
            "page": new_widget.page,
            "description": new_widget.description,
            "images": image_paths,
            "created_at": new_widget.created_at.isoformat() if new_widget.created_at else None,
            "updated_at": new_widget.updated_at.isoformat() if new_widget.updated_at else None,
            "is_active": new_widget.is_active
        }
        
        encrypted_response = encrypt_payload({
            "success": True,
            "widget": widget_data,
            "message": "Widget created successfully"
        })
        
        return {
            "success": True,
            "encrypted_data": encrypted_response,
            "message": "Widget created successfully"
        }, 201
        
    except Exception as e:
        print(f"❌ Create widget error: {str(e)}")
        db.session.rollback()
        return {"error": "Failed to create widget"}, 500

def update_widget(widget_id, encrypted_data, files=None):
    """Update widget with encrypted data and images"""
    try:
        # Decrypt the incoming data
        decrypted_data = decrypt_payload(encrypted_data)
        name = decrypted_data.get("name")
        title = decrypted_data.get("title", "")
        widget_type = decrypted_data.get("type", "default")
        description = decrypted_data.get("description", "")
        page = decrypted_data.get("page", "home")
        
        if not name:
            return {"error": "Widget name is required"}, 400
        
        # Find widget
        widget = Widget.query.get(widget_id)
        if not widget:
            return {"error": "Widget not found"}, 404
        
        # Allow multiple widgets with same name - removed restriction
        # existing_widget = Widget.query.filter(
        #     Widget.name == name,
        #     Widget.id != widget_id
        # ).first()
        # if existing_widget:
        #     return {"error": "Widget with this name already exists"}, 400
        
        # Handle new image uploads if files provided
        new_image_paths = []
        if files:
            new_image_paths = save_widget_images(files, widget.id)
        
        # Get existing images
        existing_images = []
        if widget.images:
            try:
                existing_images = json.loads(widget.images)
            except:
                existing_images = []
        
        # Combine existing and new images
        all_images = existing_images + new_image_paths
        
        # Update widget
        widget.name = name
        widget.title = title
        widget.type = widget_type
        widget.description = description
        widget.page = page
        widget.images = json.dumps(all_images)
        widget.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Return encrypted response
        widget_data = {
            "id": widget.id,
            "name": widget.name,
            "title": widget.title,
            "type": widget.type,
            "page": widget.page,
            "description": widget.description,
            "images": all_images,
            "created_at": widget.created_at.isoformat() if widget.created_at else None,
            "updated_at": widget.updated_at.isoformat() if widget.updated_at else None,
            "is_active": widget.is_active
        }
        
        encrypted_response = encrypt_payload({
            "success": True,
            "widget": widget_data,
            "message": "Widget updated successfully"
        })
        
        return {
            "success": True,
            "encrypted_data": encrypted_response,
            "message": "Widget updated successfully"
        }, 200
        
    except Exception as e:
        print(f"❌ Update widget error: {str(e)}")
        db.session.rollback()
        return {"error": "Failed to update widget"}, 500

def delete_widget(widget_id):
    """Delete widget by ID and remove associated images"""
    try:
        widget = Widget.query.get(widget_id)
        if not widget:
            return {"error": "Widget not found"}, 404
        
        # Delete associated images from filesystem
        if widget.images:
            delete_widget_images(widget.images)
        
        db.session.delete(widget)
        db.session.commit()
        
        return {
            "success": True,
            "message": "Widget deleted successfully"
        }, 200
        
    except Exception as e:
        print(f"❌ Delete widget error: {str(e)}")
        db.session.rollback()
        return {"error": "Failed to delete widget"}, 500

def delete_widget_image(widget_id, image_path):
    """Delete specific image from widget"""
    try:
        widget = Widget.query.get(widget_id)
        if not widget:
            return {"error": "Widget not found"}, 404
        
        # Parse existing images
        images = []
        if widget.images:
            try:
                images = json.loads(widget.images)
            except:
                images = []
        
        # Remove the specified image
        if image_path in images:
            images.remove(image_path)
            
            # Delete file from filesystem
            os_path = image_path.replace('/', os.sep)
            if os.path.exists(os_path):
                try:
                    os.remove(os_path)
                except Exception as e:
                    print(f"Error deleting image {os_path}: {str(e)}")
            
            # Update widget
            widget.images = json.dumps(images)
            widget.updated_at = datetime.utcnow()
            db.session.commit()
            
            return {
                "success": True,
                "message": "Image deleted successfully"
            }, 200
        else:
            return {"error": "Image not found in widget"}, 404
        
    except Exception as e:
        print(f"❌ Delete widget image error: {str(e)}")
        db.session.rollback()
        return {"error": "Failed to delete image"}, 500 
