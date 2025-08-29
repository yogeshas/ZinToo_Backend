# services/coupon_service.py
from models.coupons import Coupon
from models.category import Category
from models.subcategory import SubCategory
from models.product import Product
from extensions import db
from utils.crypto import encrypt_payload, decrypt_payload
from datetime import datetime
import json

def validate_coupon_for_cart(coupon_code: str, cart_items: list, subtotal: float):
    """Validate if a coupon can be applied to the given cart items"""
    try:
        # Find the coupon
        coupon = Coupon.query.filter_by(code=coupon_code).first()
        if not coupon:
            return {
                "success": False,
                "error": "Coupon not found"
            }, 404
        
        if not coupon.is_active:
            return {
                "success": False,
                "error": "Coupon is not active"
            }, 400
        
        # Check date validity
        now = datetime.utcnow()
        if now < coupon.start_date or now > coupon.end_date:
            return {
                "success": False,
                "error": "Coupon is expired or not yet active"
            }, 400
        
        # Check usage limit
        if coupon.usage_limit and coupon.used_count >= coupon.usage_limit:
            return {
                "success": False,
                "error": "Coupon usage limit exceeded"
            }, 400
        
        # Check minimum order amount
        if subtotal < coupon.min_order_amount:
            return {
                "success": False,
                "error": f"Minimum order amount of ₹{coupon.min_order_amount} required"
            }, 400
        
        # Check target type validation
        if coupon.target_type != 'all':
            cart_product_ids = [item.get('product_id') for item in cart_items]
            cart_category_ids = [item.get('cid') for item in cart_items if item.get('cid')]
            cart_subcategory_ids = [item.get('sid') for item in cart_items if item.get('sid')]
            
            is_valid = False
            
            if coupon.target_type == 'product':
                if coupon.target_product_id in cart_product_ids:
                    is_valid = True
            elif coupon.target_type == 'category':
                if coupon.target_category_id in cart_category_ids:
                    is_valid = True
            elif coupon.target_type == 'subcategory':
                if coupon.target_subcategory_id in cart_subcategory_ids:
                    is_valid = True
            
            if not is_valid:
                return {
                    "success": False,
                    "error": f"Coupon is not applicable to items in your cart"
                }, 400
        
        # Calculate discount
        discount_amount = 0
        if coupon.discount_type == 'percentage':
            discount_amount = subtotal * (coupon.discount_value / 100)
            if coupon.max_discount_amount:
                discount_amount = min(discount_amount, coupon.max_discount_amount)
        else:
            discount_amount = coupon.discount_value
        
        # Ensure discount doesn't exceed subtotal
        discount_amount = min(discount_amount, subtotal)
        
        # Return success with discount details
        coupon_data = {
            "id": coupon.id,
            "code": coupon.code,
            "discount_type": coupon.discount_type,
            "discount_value": coupon.discount_value,
            "min_order_amount": coupon.min_order_amount,
            "max_discount_amount": coupon.max_discount_amount,
            "target_type": coupon.target_type,
            "target_category_id": coupon.target_category_id,
            "target_subcategory_id": coupon.target_subcategory_id,
            "target_product_id": coupon.target_product_id,
            "description": coupon.description,
            "start_date": coupon.start_date.isoformat() if coupon.start_date else None,
            "end_date": coupon.end_date.isoformat() if coupon.end_date else None,
            "is_active": coupon.is_active,
            "usage_limit": coupon.usage_limit,
            "used_count": coupon.used_count,
        }
        
        return {
            "success": True,
            "coupon": coupon_data,
            "discount_amount": round(discount_amount, 2),
            "message": "Coupon is valid and can be applied"
        }, 200
        
    except Exception as e:
        print(f"❌ Coupon validation error: {str(e)}")
        return {
            "success": False,
            "error": "Failed to validate coupon"
        }, 500

def get_all_coupons():
    """Get all coupons with encryption"""
    try:
        coupons = Coupon.query.order_by(Coupon.id.desc()).all()
        coupons_data = []
        
        for coupon in coupons:
            coupon_dict = {
                "id": coupon.id,
                "code": coupon.code,
                "discount_type": coupon.discount_type,
                "discount_value": coupon.discount_value,
                "start_date": coupon.start_date.isoformat() if coupon.start_date else None,
                "end_date": coupon.end_date.isoformat() if coupon.end_date else None,
                "is_active": coupon.is_active,
                "description": coupon.description,
                "min_order_amount": coupon.min_order_amount,
                "max_discount_amount": coupon.max_discount_amount,
                "usage_limit": coupon.usage_limit,
                "used_count": coupon.used_count,
                "target_type": coupon.target_type,
                "target_category_id": coupon.target_category_id,
                "target_subcategory_id": coupon.target_subcategory_id,
                "target_product_id": coupon.target_product_id,
                "target_category_name": coupon.target_category.category_name if coupon.target_category else None,
                "target_subcategory_name": coupon.target_subcategory.sub_category_name if coupon.target_subcategory else None,
                "target_product_name": coupon.target_product.pname if coupon.target_product else None,
                "created_at": coupon.created_at.isoformat() if coupon.created_at else None,
                "updated_at": coupon.updated_at.isoformat() if coupon.updated_at else None
            }
            coupons_data.append(coupon_dict)
        
        # Encrypt the response data
        encrypted_data = encrypt_payload({
            "success": True,
            "coupons": coupons_data
        })
        
        return {
            "success": True,
            "encrypted_data": encrypted_data,
            "message": "Coupons retrieved successfully"
        }, 200
        
    except Exception as e:
        print(f"❌ Get coupons error: {str(e)}")
        return {"error": "Failed to retrieve coupons"}, 500

def get_coupon_by_id(coupon_id):
    """Get coupon by ID with encryption"""
    try:
        coupon = Coupon.query.get(coupon_id)
        if not coupon:
            return {"error": "Coupon not found"}, 404
        
        coupon_data = {
            "id": coupon.id,
            "code": coupon.code,
            "discount_type": coupon.discount_type,
            "discount_value": coupon.discount_value,
            "start_date": coupon.start_date.isoformat() if coupon.start_date else None,
            "end_date": coupon.end_date.isoformat() if coupon.end_date else None,
            "is_active": coupon.is_active,
            "description": coupon.description,
            "min_order_amount": coupon.min_order_amount,
            "max_discount_amount": coupon.max_discount_amount,
            "usage_limit": coupon.usage_limit,
            "used_count": coupon.used_count,
            "target_type": coupon.target_type,
            "target_category_id": coupon.target_category_id,
            "target_subcategory_id": coupon.target_subcategory_id,
            "target_product_id": coupon.target_product_id,
            "target_category_name": coupon.target_category.category_name if coupon.target_category else None,
            "target_subcategory_name": coupon.target_subcategory.sub_category_name if coupon.target_subcategory else None,
            "target_product_name": coupon.target_product.pname if coupon.target_product else None,
            "created_at": coupon.created_at.isoformat() if coupon.created_at else None,
            "updated_at": coupon.updated_at.isoformat() if coupon.updated_at else None
        }
        
        # Encrypt the response data
        encrypted_data = encrypt_payload({
            "success": True,
            "coupon": coupon_data
        })
        
        return {
            "success": True,
            "encrypted_data": encrypted_data,
            "message": "Coupon retrieved successfully"
        }, 200
        
    except Exception as e:
        print(f"❌ Get coupon error: {str(e)}")
        return {"error": "Failed to retrieve coupon"}, 500

def create_coupon(encrypted_data):
    """Create new coupon with encrypted data"""
    try:
        # Decrypt the incoming data
        decrypted_data = decrypt_payload(encrypted_data)
        
        # Extract required fields
        code = decrypted_data.get("code")
        discount_type = decrypted_data.get("discount_type")
        discount_value = decrypted_data.get("discount_value")
        start_date = decrypted_data.get("start_date")
        end_date = decrypted_data.get("end_date")
        
        if not all([code, discount_type, discount_value, start_date, end_date]):
            return {"error": "Code, discount type, discount value, start date, and end date are required"}, 400
        
        # Check if coupon code already exists
        existing_coupon = Coupon.query.filter_by(code=code).first()
        if existing_coupon:
            return {"error": "Coupon with this code already exists"}, 400
        
        # Parse dates
        try:
            start_date = datetime.fromisoformat(start_date)
            end_date = datetime.fromisoformat(end_date)
        except ValueError:
            return {"error": "Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"}, 400
        
        # Validate dates
        if start_date >= end_date:
            return {"error": "End date must be after start date"}, 400
        
        # Create new coupon
        new_coupon = Coupon(
            code=code,
            discount_type=discount_type,
            discount_value=float(discount_value),
            start_date=start_date,
            end_date=end_date,
            description=decrypted_data.get("description", ""),
            min_order_amount=float(decrypted_data.get("min_order_amount", 0)),
            max_discount_amount=float(decrypted_data.get("max_discount_amount", 0)) if decrypted_data.get("max_discount_amount") else None,
            usage_limit=int(decrypted_data.get("usage_limit", 0)) if decrypted_data.get("usage_limit") else None,
            target_type=decrypted_data.get("target_type", "all"),
            target_category_id=int(decrypted_data.get("target_category_id")) if decrypted_data.get("target_category_id") else None,
            target_subcategory_id=int(decrypted_data.get("target_subcategory_id")) if decrypted_data.get("target_subcategory_id") else None,
            target_product_id=int(decrypted_data.get("target_product_id")) if decrypted_data.get("target_product_id") else None
        )
        
        db.session.add(new_coupon)
        db.session.commit()
        
        # Return encrypted response
        coupon_data = {
            "id": new_coupon.id,
            "code": new_coupon.code,
            "discount_type": new_coupon.discount_type,
            "discount_value": new_coupon.discount_value,
            "start_date": new_coupon.start_date.isoformat(),
            "end_date": new_coupon.end_date.isoformat(),
            "is_active": new_coupon.is_active,
            "description": new_coupon.description,
            "min_order_amount": new_coupon.min_order_amount,
            "max_discount_amount": new_coupon.max_discount_amount,
            "usage_limit": new_coupon.usage_limit,
            "used_count": new_coupon.used_count,
            "target_type": new_coupon.target_type,
            "target_category_id": new_coupon.target_category_id,
            "target_subcategory_id": new_coupon.target_subcategory_id,
            "target_product_id": new_coupon.target_product_id
        }
        
        encrypted_response = encrypt_payload({
            "success": True,
            "coupon": coupon_data,
            "message": "Coupon created successfully"
        })
        
        return {
            "success": True,
            "encrypted_data": encrypted_response,
            "message": "Coupon created successfully"
        }, 201
        
    except Exception as e:
        print(f"❌ Create coupon error: {str(e)}")
        db.session.rollback()
        return {"error": "Failed to create coupon"}, 500

def update_coupon(coupon_id, encrypted_data):
    """Update coupon with encrypted data"""
    try:
        # Decrypt the incoming data
        decrypted_data = decrypt_payload(encrypted_data)
        
        # Find coupon
        coupon = Coupon.query.get(coupon_id)
        if not coupon:
            return {"error": "Coupon not found"}, 404
        
        # Extract fields
        code = decrypted_data.get("code")
        discount_type = decrypted_data.get("discount_type")
        discount_value = decrypted_data.get("discount_value")
        start_date = decrypted_data.get("start_date")
        end_date = decrypted_data.get("end_date")
        
        if not all([code, discount_type, discount_value, start_date, end_date]):
            return {"error": "Code, discount type, discount value, start date, and end date are required"}, 400
        
        # Check if code already exists (excluding current coupon)
        existing_coupon = Coupon.query.filter(
            Coupon.code == code,
            Coupon.id != coupon_id
        ).first()
        if existing_coupon:
            return {"error": "Coupon with this code already exists"}, 400
        
        # Parse dates
        try:
            start_date = datetime.fromisoformat(start_date)
            end_date = datetime.fromisoformat(end_date)
        except ValueError:
            return {"error": "Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"}, 400
        
        # Validate dates
        if start_date >= end_date:
            return {"error": "End date must be after start date"}, 400
        
        # Update coupon
        coupon.code = code
        coupon.discount_type = discount_type
        coupon.discount_value = float(discount_value)
        coupon.start_date = start_date
        coupon.end_date = end_date
        coupon.description = decrypted_data.get("description", "")
        coupon.min_order_amount = float(decrypted_data.get("min_order_amount", 0))
        coupon.max_discount_amount = float(decrypted_data.get("max_discount_amount", 0)) if decrypted_data.get("max_discount_amount") else None
        coupon.usage_limit = int(decrypted_data.get("usage_limit", 0)) if decrypted_data.get("usage_limit") else None
        coupon.target_type = decrypted_data.get("target_type", "all")
        coupon.target_category_id = int(decrypted_data.get("target_category_id")) if decrypted_data.get("target_category_id") else None
        coupon.target_subcategory_id = int(decrypted_data.get("target_subcategory_id")) if decrypted_data.get("target_subcategory_id") else None
        coupon.target_product_id = int(decrypted_data.get("target_product_id")) if decrypted_data.get("target_product_id") else None
        
        db.session.commit()
        
        # Return encrypted response
        coupon_data = {
            "id": coupon.id,
            "code": coupon.code,
            "discount_type": coupon.discount_type,
            "discount_value": coupon.discount_value,
            "start_date": coupon.start_date.isoformat(),
            "end_date": coupon.end_date.isoformat(),
            "is_active": coupon.is_active,
            "description": coupon.description,
            "min_order_amount": coupon.min_order_amount,
            "max_discount_amount": coupon.max_discount_amount,
            "usage_limit": coupon.usage_limit,
            "used_count": coupon.used_count,
            "target_type": coupon.target_type,
            "target_category_id": coupon.target_category_id,
            "target_subcategory_id": coupon.target_subcategory_id,
            "target_product_id": coupon.target_product_id
        }
        
        encrypted_response = encrypt_payload({
            "success": True,
            "coupon": coupon_data,
            "message": "Coupon updated successfully"
        })
        
        return {
            "success": True,
            "encrypted_data": encrypted_response,
            "message": "Coupon updated successfully"
        }, 200
        
    except Exception as e:
        print(f"❌ Update coupon error: {str(e)}")
        db.session.rollback()
        return {"error": "Failed to update coupon"}, 500

def delete_coupon(coupon_id):
    """Delete coupon by ID"""
    try:
        coupon = Coupon.query.get(coupon_id)
        if not coupon:
            return {"error": "Coupon not found"}, 404
        
        db.session.delete(coupon)
        db.session.commit()
        
        return {
            "success": True,
            "message": "Coupon deleted successfully"
        }, 200
        
    except Exception as e:
        print(f"❌ Delete coupon error: {str(e)}")
        db.session.rollback()
        return {"error": "Failed to delete coupon"}, 500

def get_categories_for_coupon():
    """Get all categories for coupon target selection"""
    try:
        categories = Category.query.all()
        categories_data = []
        
        for category in categories:
            category_dict = {
                "id": category.id,
                "name": category.category_name,
                "description": category.description
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
        print(f"❌ Get categories for coupon error: {str(e)}")
        return {"error": "Failed to retrieve categories"}, 500

def get_subcategories_for_coupon(category_id=None):
    """Get subcategories for coupon target selection"""
    try:
        if category_id:
            subcategories = SubCategory.query.filter_by(cid=category_id).all()
        else:
            subcategories = SubCategory.query.all()
        
        subcategories_data = []
        
        for subcategory in subcategories:
            subcategory_dict = {
                "id": subcategory.id,
                "name": subcategory.sub_category_name,
                "category_id": subcategory.cid,
                "category_name": subcategory.category.category_name if subcategory.category else None
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
        print(f"❌ Get subcategories for coupon error: {str(e)}")
        return {"error": "Failed to retrieve subcategories"}, 500

def get_products_for_coupon(subcategory_id=None, category_id=None):
    """Get products for coupon target selection"""
    try:
        if subcategory_id:
            products = Product.query.filter_by(sid=subcategory_id).all()
        elif category_id:
            products = Product.query.filter_by(cid=category_id).all()
        else:
            products = Product.query.all()
        
        products_data = []
        
        for product in products:
            product_dict = {
                "id": product.id,
                "name": product.pname,
                "category_id": product.cid,
                "category_name": product.category.category_name if product.category else None,
                "subcategory_id": product.sid,
                "subcategory_name": product.subcategory.sub_category_name if product.subcategory else None
            }
            products_data.append(product_dict)
        
        # Encrypt the response data
        encrypted_data = encrypt_payload({
            "success": True,
            "products": products_data
        })
        
        return {
            "success": True,
            "encrypted_data": encrypted_data,
            "message": "Products retrieved successfully"
        }, 200
        
    except Exception as e:
        print(f"❌ Get products for coupon error: {str(e)}")
        return {"error": "Failed to retrieve products"}, 500 
