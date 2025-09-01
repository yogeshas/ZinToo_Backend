from models.exchange import Exchange
from models.order import Order, OrderItem
from models.product import Product
from extensions import db
from datetime import datetime
from sqlalchemy import and_

def create_exchange(customer_id, order_id, order_item_id, product_id, new_size, new_quantity=1, reason=None):
    """Create a new exchange request with size and quantity support"""
    try:
        print(f"[EXCHANGE SERVICE] Creating exchange: customer_id={customer_id}, order_id={order_id}, order_item_id={order_item_id}, product_id={product_id}, new_size={new_size}, new_quantity={new_quantity}")
        
        # Check if order exists and belongs to customer
        order = Order.query.filter_by(id=order_id, customer_id=customer_id).first()
        if not order:
            print(f"[EXCHANGE SERVICE] Order {order_id} not found for customer {customer_id}")
            return {"error": "Order not found"}, 404
        
        # Check if order item exists
        order_item = OrderItem.query.filter_by(id=order_item_id, order_id=order_id).first()
        if not order_item:
            print(f"[EXCHANGE SERVICE] Order item {order_item_id} not found for order {order_id}")
            return {"error": "Order item not found"}, 404
        
        # Check if product exists
        product = Product.query.get(product_id)
        if not product:
            print(f"[EXCHANGE SERVICE] Product {product_id} not found")
            return {"error": "Product not found"}, 404
        
        # Check if new size is available
        print(f"[EXCHANGE SERVICE] Checking size availability for product {product_id}")
        print(f"[EXCHANGE SERVICE] Product sizes: {product.get_sizes_dict()}")
        print(f"[EXCHANGE SERVICE] Requested size: {new_size}")
        print(f"[EXCHANGE SERVICE] Available sizes: {product.get_available_sizes()}")
        
        if not product.is_size_available(new_size):
            print(f"[EXCHANGE SERVICE] Size {new_size} not available")
            return {"error": f"Size {new_size} is not available"}, 400
        
        # Check if requested quantity is available
        available_quantity = product.get_size_stock(new_size)
        print(f"[EXCHANGE SERVICE] Available quantity for size {new_size}: {available_quantity}")
        print(f"[EXCHANGE SERVICE] Requested quantity: {new_quantity}")
        
        if available_quantity < new_quantity:
            print(f"[EXCHANGE SERVICE] Insufficient quantity for size {new_size}")
            return {"error": f"Only {available_quantity} available in size {new_size}"}, 400
        
        # Calculate additional payment if quantity increased
        old_quantity = order_item.quantity
        additional_payment_required = False
        additional_amount = 0.0
        
        if new_quantity > old_quantity:
            additional_payment_required = True
            additional_amount = (new_quantity - old_quantity) * order_item.unit_price
            print(f"[EXCHANGE SERVICE] Additional payment required: ₹{additional_amount}")
        
        # Check if exchange already exists for this order item
        existing_exchange = (
            Exchange.query
            .filter(
                Exchange.order_item_id == order_item_id,
                Exchange.status.in_(["initiated", "approved", "out_for_delivery"])  # pending active flows
            )
            .first()
        )
        
        if existing_exchange:
            return {"error": "Exchange request already exists for this item"}, 400
        
        # Create exchange
        print(f"[EXCHANGE SERVICE] Creating exchange object...")
        exchange = Exchange(
            order_id=order_id,
            order_item_id=order_item_id,
            customer_id=customer_id,
            product_id=product_id,
            old_size=order_item.selected_size or 'N/A',
            new_size=new_size,
            old_quantity=old_quantity,
            new_quantity=new_quantity,
            reason=reason,
            additional_payment_required=additional_payment_required,
            additional_amount=additional_amount,
            status="initiated"
        )
        
        print(f"[EXCHANGE SERVICE] Exchange object created: {exchange}")
        
        db.session.add(exchange)
        db.session.commit()
        
        print(f"[EXCHANGE SERVICE] Exchange saved to database with ID: {exchange.id}")
        
        return {
            "success": True, 
            "message": "Exchange request created successfully", 
            "exchange_id": exchange.id,
            "additional_payment_required": additional_payment_required,
            "additional_amount": additional_amount
        }, 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Create exchange error: {str(e)}")
        return {"error": "Failed to create exchange request"}, 500

def get_customer_exchanges(customer_id, limit=20):
    """Get all exchanges for a customer"""
    try:
        exchanges = Exchange.query.filter_by(customer_id=customer_id)\
            .order_by(Exchange.created_at.desc())\
            .limit(limit)\
            .all()
        
        exchanges_data = []
        for exchange in exchanges:
            exchange_dict = exchange.as_dict()
            
            # Add order information
            if exchange.order:
                exchange_dict["order"] = exchange.order.as_dict()
            
            # Add customer information (try direct relationship first, then through order)
            customer_data = None
            if exchange.customer:
                customer_data = exchange.customer.as_dict()
            elif exchange.order and exchange.order.customer:
                customer_data = exchange.order.customer.as_dict()
            
            if customer_data:
                # Add name field for frontend compatibility
                customer_data["name"] = customer_data.get("username", "Unknown")
                exchange_dict["customer"] = customer_data
            
            # Add product information
            if exchange.product:
                product_data = exchange.product.to_dict()
                # Add name field for frontend compatibility
                product_data["name"] = product_data.get("pname", "Unknown")
                exchange_dict["product"] = product_data
            
            exchanges_data.append(exchange_dict)
        
        return {"success": True, "exchanges": exchanges_data}, 200
        
    except Exception as e:
        print(f"Get customer exchanges error: {str(e)}")
        return {"error": "Failed to fetch exchanges"}, 500

def get_all_exchanges(limit=50):
    """Get all exchanges for admin panel"""
    try:
        exchanges = Exchange.query.order_by(Exchange.created_at.desc()).limit(limit).all()
        
        exchanges_data = []
        for exchange in exchanges:
            exchange_dict = exchange.as_dict()
            
            # Add order information
            if exchange.order:
                exchange_dict["order"] = exchange.order.as_dict()
            
            # Add customer information (try direct relationship first, then through order)
            customer_data = None
            if exchange.customer:
                customer_data = exchange.customer.as_dict()
            elif exchange.order and exchange.order.customer:
                customer_data = exchange.order.customer.as_dict()
            
            if customer_data:
                # Add name field for frontend compatibility
                customer_data["name"] = customer_data.get("username", "Unknown")
                exchange_dict["customer"] = customer_data
            
            # Add product information
            if exchange.product:
                product_data = exchange.product.to_dict()
                # Add name field for frontend compatibility
                product_data["name"] = product_data.get("pname", "Unknown")
                exchange_dict["product"] = product_data
            
            # Add admin info
            if exchange.admin:
                exchange_dict["admin"] = exchange.admin.as_dict()
            
            # Add delivery guy info
            if exchange.delivery_guy:
                exchange_dict["delivery_guy"] = exchange.delivery_guy.as_dict()
            
            exchanges_data.append(exchange_dict)
        
        return {"success": True, "exchanges": exchanges_data}, 200
        
    except Exception as e:
        print(f"Get all exchanges error: {str(e)}")
        return {"error": "Failed to fetch exchanges"}, 500

def get_exchange_by_id(exchange_id):
    """Get exchange by ID"""
    try:
        exchange = Exchange.query.get(exchange_id)
        if not exchange:
            return {"error": "Exchange not found"}, 404
        
        exchange_dict = exchange.as_dict()
        
        # Add related information
        if exchange.order:
            exchange_dict["order"] = exchange.order.as_dict()
        
        # Add customer information (try direct relationship first, then through order)
        customer_data = None
        if exchange.customer:
            customer_data = exchange.customer.as_dict()
        elif exchange.order and exchange.order.customer:
            customer_data = exchange.order.customer.as_dict()
        
        if customer_data:
            # Add name field for frontend compatibility
            customer_data["name"] = customer_data.get("username", "Unknown")
            exchange_dict["customer"] = customer_data
        
        if exchange.product:
            product_data = exchange.product.to_dict()
            # Add name field for frontend compatibility
            product_data["name"] = product_data.get("pname", "Unknown")
            exchange_dict["product"] = product_data
        
        if exchange.admin:
            exchange_dict["admin"] = exchange.admin.as_dict()
        
        if exchange.delivery_guy:
            exchange_dict["delivery_guy"] = exchange.delivery_guy.as_dict()
        
        return {"success": True, "exchange": exchange_dict}, 200
        
    except Exception as e:
        print(f"Get exchange by ID error: {str(e)}")
        return {"error": "Failed to fetch exchange"}, 500

def approve_exchange(exchange_id, admin_id, admin_notes=None):
    """Approve an exchange request with size-based inventory management"""
    try:
        exchange = Exchange.query.get(exchange_id)
        if not exchange:
            return {"error": "Exchange not found"}, 404
        
        success, message = exchange.approve(admin_id)
        if not success:
            return {"error": message}, 400
        
        # Update admin notes if provided
        if admin_notes:
            exchange.admin_notes = admin_notes

        # Handle inventory changes on approval
        product = Product.query.get(exchange.product_id)
        if product:
            try:
                # Reserve new size inventory
                success, msg = product.reserve_size(exchange.new_size, exchange.new_quantity)
                if not success:
                    return {"error": msg}, 400
                
                # Add old size back to inventory (if it was a valid size)
                if exchange.old_size and exchange.old_size != 'N/A':
                    product.add_size_stock(exchange.old_size, exchange.old_quantity)
                
                print(f"[EXCHANGE SERVICE] Inventory updated: {msg}")
                
            except Exception as e:
                db.session.rollback()
                print(f"[EXCHANGE SERVICE] Inventory update failed: {e}")
                return {"error": "Failed to update inventory on approval"}, 500

        db.session.commit()
        
        return {"success": True, "message": message}, 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Approve exchange error: {str(e)}")
        return {"error": "Failed to approve exchange"}, 500

def reject_exchange(exchange_id, admin_id, reason):
    """Reject an exchange request"""
    try:
        exchange = Exchange.query.get(exchange_id)
        if not exchange:
            return {"error": "Exchange not found"}, 404
        
        success, message = exchange.reject(admin_id, reason)
        if not success:
            return {"error": message}, 400
        
        db.session.commit()
        
        return {"success": True, "message": message}, 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Reject exchange error: {str(e)}")
        return {"error": "Failed to reject exchange"}, 500

def assign_delivery(exchange_id, delivery_guy_id):
    """Assign delivery guy for exchange (admin action)"""
    try:
        exchange = Exchange.query.get(exchange_id)
        if not exchange:
            return {"error": "Exchange not found"}, 404
        
        success, message = exchange.assign_delivery(delivery_guy_id)
        if not success:
            return {"error": message}, 400
        
        db.session.commit()
        
        return {"success": True, "message": message}, 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Assign delivery error: {str(e)}")
        return {"error": "Failed to assign delivery"}, 500

def start_delivery(exchange_id):
    """Start delivery (delivery team action)"""
    try:
        exchange = Exchange.query.get(exchange_id)
        if not exchange:
            return {"error": "Exchange not found"}, 404
        
        success, message = exchange.start_delivery()
        if not success:
            return {"error": message}, 400
        
        db.session.commit()
        
        return {"success": True, "message": message}, 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Start delivery error: {str(e)}")
        return {"error": "Failed to start delivery"}, 500

def mark_exchange_delivered(exchange_id):
    """Mark exchange as delivered"""
    try:
        exchange = Exchange.query.get(exchange_id)
        if not exchange:
            return {"error": "Exchange not found"}, 404
        
        success, message = exchange.mark_delivered()
        if not success:
            return {"error": message}, 400
        
        # When delivered, the inventory changes are already handled at approval time
        # No additional inventory changes needed here
        
        db.session.commit()
        
        return {"success": True, "message": message}, 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Mark delivered error: {str(e)}")
        return {"error": "Failed to mark as delivered"}, 500

def get_exchanges_by_status(status, limit=50):
    """Get exchanges by status"""
    try:
        exchanges = Exchange.query.filter_by(status=status)\
            .order_by(Exchange.created_at.desc())\
            .limit(limit)\
            .all()
        
        exchanges_data = []
        for exchange in exchanges:
            exchange_dict = exchange.as_dict()
            
            # Add basic related info
            if exchange.order:
                exchange_dict["order"] = exchange.order.as_dict()
            
            # Add customer information (try direct relationship first, then through order)
            customer_data = None
            if exchange.customer:
                customer_data = exchange.customer.as_dict()
            elif exchange.order and exchange.order.customer:
                customer_data = exchange.order.customer.as_dict()
            
            if customer_data:
                # Add name field for frontend compatibility
                customer_data["name"] = customer_data.get("username", "Unknown")
                exchange_dict["customer"] = customer_data
            
            if exchange.product:
                product_data = exchange.product.to_dict()
                # Add name field for frontend compatibility
                product_data["name"] = product_data.get("pname", "Unknown")
                exchange_dict["product"] = product_data
            
            exchanges_data.append(exchange_dict)
        
        return {"success": True, "exchanges": exchanges_data}, 200
        
    except Exception as e:
        print(f"Get exchanges by status error: {str(e)}")
        return {"error": "Failed to fetch exchanges"}, 500
