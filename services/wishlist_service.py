from models.wishlist import Wishlist
from models.product import Product
from models.customer import Customer
from extensions import db
from sqlalchemy.exc import IntegrityError
from datetime import datetime

def add_to_wishlist(customer_id: int, product_id: int):
    """Add product to wishlist"""
    try:
        # Check if product exists
        product = Product.query.get(product_id)
        if not product:
            raise ValueError("Product not found")
        
        # Check if customer exists
        customer = Customer.query.get(customer_id)
        if not customer:
            raise ValueError("Customer not found")
        
        # Check if item already exists in wishlist
        existing_wishlist_item = Wishlist.query.filter_by(
            customer_id=customer_id, 
            product_id=product_id
        ).first()
        
        if existing_wishlist_item:
            raise ValueError("Product already in wishlist")
        
        # Create new wishlist item
        wishlist_item = Wishlist(
            customer_id=customer_id,
            product_id=product_id
        )
        db.session.add(wishlist_item)
        db.session.commit()
        return wishlist_item
            
    except IntegrityError as e:
        db.session.rollback()
        raise ValueError(f"Database error: {str(e)}")
    except Exception as e:
        db.session.rollback()
        raise ValueError(f"Error adding to wishlist: {str(e)}")

def remove_from_wishlist(customer_id: int, product_id: int):
    """Remove item from wishlist"""
    try:
        wishlist_item = Wishlist.query.filter_by(
            customer_id=customer_id,
            product_id=product_id
        ).first()
        
        if not wishlist_item:
            raise ValueError("Wishlist item not found")
        
        db.session.delete(wishlist_item)
        db.session.commit()
        return True
        
    except Exception as e:
        db.session.rollback()
        raise ValueError(f"Error removing from wishlist: {str(e)}")

def remove_wishlist_item_by_id(wishlist_id: int):
    """Remove wishlist item by ID"""
    try:
        wishlist_item = Wishlist.query.get(wishlist_id)
        if not wishlist_item:
            raise ValueError("Wishlist item not found")
        
        db.session.delete(wishlist_item)
        db.session.commit()
        return True
        
    except Exception as e:
        db.session.rollback()
        raise ValueError(f"Error removing wishlist item: {str(e)}")

def get_customer_wishlist(customer_id: int):
    """Get all wishlist items for a customer"""
    try:
        wishlist_items = Wishlist.query.filter_by(customer_id=customer_id).all()
        return wishlist_items
    except Exception as e:
        raise ValueError(f"Error getting wishlist: {str(e)}")

def get_wishlist_item(wishlist_id: int):
    """Get specific wishlist item"""
    try:
        wishlist_item = Wishlist.query.get(wishlist_id)
        return wishlist_item
    except Exception as e:
        raise ValueError(f"Error getting wishlist item: {str(e)}")

def clear_customer_wishlist(customer_id: int):
    """Clear all wishlist items for a customer"""
    try:
        wishlist_items = Wishlist.query.filter_by(customer_id=customer_id).all()
        for item in wishlist_items:
            db.session.delete(item)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        raise ValueError(f"Error clearing wishlist: {str(e)}")

def get_wishlist_count(customer_id: int):
    """Get total number of items in customer's wishlist"""
    try:
        count = Wishlist.query.filter_by(customer_id=customer_id).count()
        return count
    except Exception as e:
        raise ValueError(f"Error getting wishlist count: {str(e)}")

def is_product_in_wishlist(customer_id: int, product_id: int):
    """Check if a product is in customer's wishlist"""
    try:
        wishlist_item = Wishlist.query.filter_by(
            customer_id=customer_id,
            product_id=product_id
        ).first()
        return wishlist_item is not None
    except Exception as e:
        raise ValueError(f"Error checking wishlist: {str(e)}")
