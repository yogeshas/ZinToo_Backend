# services/subcategory_service.py
from models.subcategory import SubCategory
from models.category import Category
from extensions import db
from utils.crypto import encrypt_payload, decrypt_payload
import json

def get_all_subcategories():
    """Get all subcategories with encryption"""
    try:
        subcategories = SubCategory.query.order_by(SubCategory.id.desc()).all()
        subcategories_data = []
        
        for subcategory in subcategories:
            # Get parent category name
            parent_category = Category.query.get(subcategory.cid)
            parent_name = parent_category.category_name if parent_category else "Unknown"
            
            subcategory_dict = {
                "id": subcategory.id,
                "name": subcategory.sub_category_name,
                "category_id": subcategory.cid,
                "category_name": parent_name,
                "sub_category_count": subcategory.sub_category_count
            }
            subcategories_data.append(subcategory_dict)
        
        # Encrypt the response data
        encrypted_data = encrypt_payload({
            "success": True,
            "subcategories": subcategories_data
        })
        
        return {
            "success": True,
            "encrypted_data": encrypted_data,
            "message": "Subcategories retrieved successfully"
        }, 200
        
    except Exception as e:
        print(f"❌ Get subcategories error: {str(e)}")
        return {"error": "Failed to retrieve subcategories"}, 500

def get_subcategory_by_id(subcategory_id):
    """Get subcategory by ID with encryption"""
    try:
        subcategory = SubCategory.query.get(subcategory_id)
        if not subcategory:
            return {"error": "Subcategory not found"}, 404
        
        # Get parent category name
        parent_category = Category.query.get(subcategory.cid)
        parent_name = parent_category.category_name if parent_category else "Unknown"
        
        subcategory_data = {
            "id": subcategory.id,
            "name": subcategory.sub_category_name,
            "category_id": subcategory.cid,
            "category_name": parent_name,
            "sub_category_count": subcategory.sub_category_count
        }
        
        # Encrypt the response data
        encrypted_data = encrypt_payload({
            "success": True,
            "subcategory": subcategory_data
        })
        
        return {
            "success": True,
            "encrypted_data": encrypted_data,
            "message": "Subcategory retrieved successfully"
        }, 200
        
    except Exception as e:
        print(f"❌ Get subcategory error: {str(e)}")
        return {"error": "Failed to retrieve subcategory"}, 500

def get_subcategories_by_category(category_id):
    """Get subcategories by parent category ID with encryption"""
    try:
        subcategories = SubCategory.query.filter_by(cid=category_id).order_by(SubCategory.id.desc()).all()
        subcategories_data = []
        
        for subcategory in subcategories:
            subcategory_dict = {
                "id": subcategory.id,
                "name": subcategory.sub_category_name,
                "category_id": subcategory.cid,
                "sub_category_count": subcategory.sub_category_count
            }
            subcategories_data.append(subcategory_dict)
        
        # Encrypt the response data
        encrypted_data = encrypt_payload({
            "success": True,
            "subcategories": subcategories_data
        })
        
        return {
            "success": True,
            "encrypted_data": encrypted_data,
            "message": "Subcategories retrieved successfully"
        }, 200
        
    except Exception as e:
        print(f"❌ Get subcategories by category error: {str(e)}")
        return {"error": "Failed to retrieve subcategories"}, 500

def create_subcategory(encrypted_data):
    """Create new subcategory with encrypted data"""
    try:
        # Decrypt the incoming data
        decrypted_data = decrypt_payload(encrypted_data)
        name = decrypted_data.get("name")
        category_id = decrypted_data.get("category_id")
        
        if not name or not category_id:
            return {"error": "Name and category are required"}, 400
        
        # Check if parent category exists
        parent_category = Category.query.get(category_id)
        if not parent_category:
            return {"error": "Parent category not found"}, 404
        
        # Check if subcategory already exists in this category
        existing_subcategory = SubCategory.query.filter_by(
            sub_category_name=name,
            cid=category_id
        ).first()
        if existing_subcategory:
            return {"error": "Subcategory with this name already exists in the selected category"}, 400
        
        # Create new subcategory
        new_subcategory = SubCategory(
            sub_category_name=name,
            cid=category_id,
            sub_category_count=0
        )
        
        db.session.add(new_subcategory)
        db.session.commit()
        
        # Return encrypted response
        subcategory_data = {
            "id": new_subcategory.id,
            "name": new_subcategory.sub_category_name,
            "category_id": new_subcategory.cid,
            "category_name": parent_category.category_name,
            "sub_category_count": new_subcategory.sub_category_count
        }
        
        encrypted_response = encrypt_payload({
            "success": True,
            "subcategory": subcategory_data,
            "message": "Subcategory created successfully"
        })
        
        return {
            "success": True,
            "encrypted_data": encrypted_response,
            "message": "Subcategory created successfully"
        }, 201
        
    except Exception as e:
        print(f"❌ Create subcategory error: {str(e)}")
        db.session.rollback()
        return {"error": "Failed to create subcategory"}, 500

def update_subcategory(subcategory_id, encrypted_data):
    """Update subcategory with encrypted data"""
    try:
        # Decrypt the incoming data
        decrypted_data = decrypt_payload(encrypted_data)
        name = decrypted_data.get("name")
        category_id = decrypted_data.get("category_id")
        
        if not name or not category_id:
            return {"error": "Name and category are required"}, 400
        
        # Find subcategory
        subcategory = SubCategory.query.get(subcategory_id)
        if not subcategory:
            return {"error": "Subcategory not found"}, 404
        
        # Check if parent category exists
        parent_category = Category.query.get(category_id)
        if not parent_category:
            return {"error": "Parent category not found"}, 404
        
        # Check if name already exists in the selected category (excluding current subcategory)
        existing_subcategory = SubCategory.query.filter(
            SubCategory.sub_category_name == name,
            SubCategory.cid == category_id,
            SubCategory.id != subcategory_id
        ).first()
        if existing_subcategory:
            return {"error": "Subcategory with this name already exists in the selected category"}, 400
        
        # Update subcategory
        subcategory.sub_category_name = name
        subcategory.cid = category_id
        
        db.session.commit()
        
        # Return encrypted response
        subcategory_data = {
            "id": subcategory.id,
            "name": subcategory.sub_category_name,
            "category_id": subcategory.cid,
            "category_name": parent_category.category_name,
            "sub_category_count": subcategory.sub_category_count
        }
        
        encrypted_response = encrypt_payload({
            "success": True,
            "subcategory": subcategory_data,
            "message": "Subcategory updated successfully"
        })
        
        return {
            "success": True,
            "encrypted_data": encrypted_response,
            "message": "Subcategory updated successfully"
        }, 200
        
    except Exception as e:
        print(f"❌ Update subcategory error: {str(e)}")
        db.session.rollback()
        return {"error": "Failed to update subcategory"}, 500

def delete_subcategory(subcategory_id):
    """Delete subcategory by ID"""
    try:
        subcategory = SubCategory.query.get(subcategory_id)
        if not subcategory:
            return {"error": "Subcategory not found"}, 404
        
        # Check if subcategory has products
        if subcategory.products:
            return {"error": "Cannot delete subcategory with existing products"}, 400
        
        db.session.delete(subcategory)
        db.session.commit()
        
        return {
            "success": True,
            "message": "Subcategory deleted successfully"
        }, 200
        
    except Exception as e:
        print(f"❌ Delete subcategory error: {str(e)}")
        db.session.rollback()
        return {"error": "Failed to delete subcategory"}, 500 
