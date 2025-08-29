from models.cart import Cart
from models.product import Product
from models.customer import Customer
from extensions import db
from sqlalchemy.exc import IntegrityError
from datetime import datetime

def add_to_cart(customer_id: int, product_id: int, quantity: int = 1):
    """Add product to cart or update quantity if already exists"""
    try:
        # Check if product exists
        product = Product.query.get(product_id)
        if not product:
            raise ValueError("Product not found")
        
        # Check if customer exists
        customer = Customer.query.get(customer_id)
        if not customer:
            raise ValueError("Customer not found")
        
        # Check if item already exists in cart
        existing_cart_item = Cart.query.filter_by(
            customer_id=customer_id, 
            product_id=product_id
        ).first()
        
        if existing_cart_item:
            # Update quantity
            existing_cart_item.quantity += quantity
            existing_cart_item.updated_at = datetime.utcnow()
            db.session.commit()
            return existing_cart_item
        else:
            # Create new cart item
            cart_item = Cart(
                customer_id=customer_id,
                product_id=product_id,
                quantity=quantity
            )
            db.session.add(cart_item)
            db.session.commit()
            return cart_item
            
    except IntegrityError as e:
        db.session.rollback()
        raise ValueError(f"Database error: {str(e)}")
    except Exception as e:
        db.session.rollback()
        raise ValueError(f"Error adding to cart: {str(e)}")

def update_cart_quantity(cart_id: int, quantity: int):
    """Update quantity of cart item"""
    try:
        cart_item = Cart.query.get(cart_id)
        if not cart_item:
            raise ValueError("Cart item not found")
        
        if quantity <= 0:
            # Remove item if quantity is 0 or negative
            db.session.delete(cart_item)
        else:
            cart_item.quantity = quantity
            cart_item.updated_at = datetime.utcnow()
        
        db.session.commit()
        return cart_item if quantity > 0 else None
        
    except Exception as e:
        db.session.rollback()
        raise ValueError(f"Error updating cart: {str(e)}")

def remove_from_cart(cart_id: int):
    """Remove item from cart"""
    try:
        cart_item = Cart.query.get(cart_id)
        if not cart_item:
            raise ValueError("Cart item not found")
        
        db.session.delete(cart_item)
        db.session.commit()
        return True
        
    except Exception as e:
        db.session.rollback()
        raise ValueError(f"Error removing from cart: {str(e)}")

def get_customer_cart(customer_id: int):
    """Get all cart items for a customer"""
    try:
        cart_items = Cart.query.filter_by(customer_id=customer_id).all()
        return cart_items
    except Exception as e:
        raise ValueError(f"Error getting cart: {str(e)}")

def get_cart_item(cart_id: int):
    """Get specific cart item"""
    try:
        cart_item = Cart.query.get(cart_id)
        return cart_item
    except Exception as e:
        raise ValueError(f"Error getting cart item: {str(e)}")

def clear_customer_cart(customer_id: int):
    """Clear all cart items for a customer"""
    try:
        cart_items = Cart.query.filter_by(customer_id=customer_id).all()
        for item in cart_items:
            db.session.delete(item)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        raise ValueError(f"Error clearing cart: {str(e)}")

def get_cart_count(customer_id: int):
    """Get total number of items in customer's cart"""
    try:
        count = Cart.query.filter_by(customer_id=customer_id).count()
        return count
    except Exception as e:
        raise ValueError(f"Error getting cart count: {str(e)}")
