from models.cart import Cart
from models.product import Product
from models.customer import Customer
from extensions import db
from sqlalchemy.exc import IntegrityError
from datetime import datetime

def add_to_cart(customer_id: int, product_id: int, quantity: int = 1, selected_size: str = None, selected_color: str = None):
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
        
        # Check if item already exists in cart with same size and color
        existing_cart_item = Cart.query.filter_by(
            customer_id=customer_id, 
            product_id=product_id,
            selected_size=selected_size,
            selected_color=selected_color
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
                quantity=quantity,
                selected_size=selected_size,
                selected_color=selected_color
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
    """Get all cart items for a customer with product sizes data"""
    try:
        # Use join to get product data including sizes
        cart_items = db.session.query(Cart, Product).join(Product).filter(Cart.customer_id == customer_id).all()
        
        # Convert to cart items with enhanced product data
        enhanced_cart_items = []
        for cart_item, product in cart_items:
            # Get the cart item as dictionary
            cart_dict = cart_item.to_dict()
            
            # Debug: Show cart item data (reduced logging)
            print(f"[CART SERVICE] Cart item {cart_item.id}: selected_size={cart_item.selected_size}, selected_color={cart_item.selected_color}")
            
            # Add product sizes data to the cart item for frontend validation
            if hasattr(product, 'size') and product.size:
                try:
                    # Parse sizes if it's a JSON string
                    if isinstance(product.size, str):
                        import json
                        cart_dict['sizes'] = json.loads(product.size)
                    else:
                        cart_dict['sizes'] = product.size
                except Exception as e:
                    print(f"[CART SERVICE] Error parsing product sizes: {e}")
                    cart_dict['sizes'] = {}
            else:
                cart_dict['sizes'] = {}
            
            # Also add product sizes to the product object for consistency
            if hasattr(product, 'size') and product.size:
                try:
                    if isinstance(product.size, str):
                        import json
                        cart_dict['product']['sizes'] = json.loads(product.size)
                    else:
                        cart_dict['product']['sizes'] = product.size
                except Exception as e:
                    print(f"[CART SERVICE] Error parsing product sizes in product: {e}")
                    cart_dict['product']['sizes'] = {}
            
            enhanced_cart_items.append(cart_dict)
        
        print(f"[CART SERVICE] Returning {len(enhanced_cart_items)} enhanced cart items")
        return enhanced_cart_items
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
