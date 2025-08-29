# services/category_service.py
import os
import uuid
from werkzeug.utils import secure_filename
from models.category import Category
from extensions import db
from utils.crypto import encrypt_payload, decrypt_payload
import json

# Image upload configuration
UPLOAD_FOLDER = 'assets/category'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_category_image(file, category_id):
    """Save category image and return the path"""
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    if file and file.filename and allowed_file(file.filename):
        # Generate unique filename
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"category_{category_id}_{uuid.uuid4().hex[:8]}.{file_extension}"
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        
        # Save file
        file.save(file_path)
        
        # Normalize to forward slashes for URL use
        normalized_path = file_path.replace('\\', '/')
        return normalized_path
    
    return None

def delete_category_image(image_path):
    """Delete category image from filesystem"""
    if not image_path:
        return
    
    # Convert to OS path
    os_path = image_path.replace('/', os.sep)
    if os.path.exists(os_path):
        try:
            os.remove(os_path)
        except Exception as e:
            print(f"Error deleting image {os_path}: {str(e)}")

def get_all_categories():
    """Get all categories with encryption"""
    try:
        categories = Category.query.order_by(Category.id.desc()).all()
        categories_data = []
        
        for category in categories:
            category_dict = {
                "id": category.id,
                "name": category.category_name,
                "description": category.description,
                "category_count": category.category_count,
                "image": category.image
            }
            categories_data.append(category_dict)
        
        # Encrypt the response data
        encrypted_data = encrypt_payload({
            "success": True,
            "categories": categories_data
        })
        
        return {
            "success": True,
            "encrypted_data": encrypted_data,
            "message": "Categories retrieved successfully"
        }, 200
        
    except Exception as e:
        print(f"❌ Get categories error: {str(e)}")
        return {"error": "Failed to retrieve categories"}, 500

def get_category_by_id(category_id):
    """Get category by ID with encryption"""
    try:
        category = Category.query.get(category_id)
        if not category:
            return {"error": "Category not found"}, 404
        
        category_data = {
            "id": category.id,
            "name": category.category_name,
            "description": category.description,
            "category_count": category.category_count,
            "image": category.image
        }
        
        # Encrypt the response data
        encrypted_data = encrypt_payload({
            "success": True,
            "category": category_data
        })
        
        return {
            "success": True,
            "encrypted_data": encrypted_data,
            "message": "Category retrieved successfully"
        }, 200
        
    except Exception as e:
        print(f"❌ Get category error: {str(e)}")
        return {"error": "Failed to retrieve category"}, 500

def create_category(encrypted_data, file=None):
    """Create new category with encrypted data and optional image"""
    try:
        # Decrypt the incoming data
        decrypted_data = decrypt_payload(encrypted_data)
        name = decrypted_data.get("name")
        description = decrypted_data.get("description")
        
        if not name or not description:
            return {"error": "Name and description are required"}, 400
        
        # Check if category already exists
        existing_category = Category.query.filter_by(category_name=name).first()
        if existing_category:
            return {"error": "Category with this name already exists"}, 400
        
        # Create new category first to get ID
        new_category = Category(
            category_name=name,
            description=description,
            category_count=0,
            image=None
        )
        
        db.session.add(new_category)
        db.session.flush()  # Get the ID without committing
        
        # Handle image upload if file provided
        if file:
            image_path = save_category_image(file, new_category.id)
            if image_path:
                new_category.image = image_path
        
        db.session.commit()
        
        # Return encrypted response
        category_data = {
            "id": new_category.id,
            "name": new_category.category_name,
            "description": new_category.description,
            "category_count": new_category.category_count,
            "image": new_category.image
        }
        
        encrypted_response = encrypt_payload({
            "success": True,
            "category": category_data,
            "message": "Category created successfully"
        })
        
        return {
            "success": True,
            "encrypted_data": encrypted_response,
            "message": "Category created successfully"
        }, 201
        
    except Exception as e:
        print(f"❌ Create category error: {str(e)}")
        db.session.rollback()
        return {"error": "Failed to create category"}, 500

def update_category(category_id, encrypted_data, file=None):
    """Update category with encrypted data and optional image"""
    try:
        # Decrypt the incoming data
        decrypted_data = decrypt_payload(encrypted_data)
        name = decrypted_data.get("name")
        description = decrypted_data.get("description")
        
        if not name or not description:
            return {"error": "Name and description are required"}, 400
        
        # Find category
        category = Category.query.get(category_id)
        if not category:
            return {"error": "Category not found"}, 404
        
        # Check if name already exists (excluding current category)
        existing_category = Category.query.filter(
            Category.category_name == name,
            Category.id != category_id
        ).first()
        if existing_category:
            return {"error": "Category with this name already exists"}, 400
        
        # Handle image upload if file provided
        if file:
            # Delete old image if exists
            if category.image:
                delete_category_image(category.image)
            
            # Save new image
            image_path = save_category_image(file, category.id)
            if image_path:
                category.image = image_path
        
        # Update category
        category.category_name = name
        category.description = description
        
        db.session.commit()
        
        # Return encrypted response
        category_data = {
            "id": category.id,
            "name": category.category_name,
            "description": category.description,
            "category_count": category.category_count,
            "image": category.image
        }
        
        encrypted_response = encrypt_payload({
            "success": True,
            "category": category_data,
            "message": "Category updated successfully"
        })
        
        return {
            "success": True,
            "encrypted_data": encrypted_response,
            "message": "Category updated successfully"
        }, 200
        
    except Exception as e:
        print(f"❌ Update category error: {str(e)}")
        db.session.rollback()
        return {"error": "Failed to update category"}, 500

def delete_category(category_id):
    """Delete category by ID"""
    try:
        category = Category.query.get(category_id)
        if not category:
            return {"error": "Category not found"}, 404
        
        # Check if category has subcategories
        if category.subcategories:
            return {"error": "Cannot delete category with existing subcategories"}, 400
        
        # Delete associated image if exists
        if category.image:
            delete_category_image(category.image)
        
        db.session.delete(category)
        db.session.commit()
        
        return {
            "success": True,
            "message": "Category deleted successfully"
        }, 200
        
    except Exception as e:
        print(f"❌ Delete category error: {str(e)}")
        db.session.rollback()
        return {"error": "Failed to delete category"}, 500 
