from models.exchange import Exchange
from models.order import Order, OrderItem
from models.product import Product
from extensions import db
from sqlalchemy import text, inspect
from datetime import datetime
from sqlalchemy import and_

def create_exchange(customer_id, order_id, order_item_id, product_id, new_size, reason=None):
    """Create a new exchange request"""
    try:
        # Ensure table exists (helps when DB migrations haven't been run yet)
        try:
            insp = inspect(db.engine)
            if not insp.has_table("exchange"):
                db.session.execute(text(
                    """
                    CREATE TABLE IF NOT EXISTS exchange (
                        id INT PRIMARY KEY AUTO_INCREMENT,
                        order_id INT NOT NULL,
                        order_item_id INT NOT NULL,
                        customer_id INT NOT NULL,
                        product_id INT NOT NULL,
                        old_size VARCHAR(20) NOT NULL,
                        new_size VARCHAR(20) NOT NULL,
                        reason TEXT,
                        status VARCHAR(50) NOT NULL DEFAULT 'initiated',
                        admin_notes TEXT,
                        approved_by INT,
                        approved_at DATETIME NULL,
                        delivery_guy_id INT,
                        assigned_at DATETIME NULL,
                        delivered_at DATETIME NULL,
                        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                    )
                    """
                ))
                db.session.commit()
        except Exception as _e:
            # If creation fails, proceed; subsequent operations may still work if table exists
            print(f"[EXCHANGE SERVICE] Ensure table error (safe to ignore if already exists): {_e}")

        print(f"[EXCHANGE SERVICE] Creating exchange: customer_id={customer_id}, order_id={order_id}, order_item_id={order_item_id}, product_id={product_id}, new_size={new_size}")
        
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
        print(f"[EXCHANGE SERVICE] Product size attribute: {hasattr(product, 'size')}")
        print(f"[EXCHANGE SERVICE] Product size value: {product.size}")
        
        if not hasattr(product, 'size') or not product.size:
            print(f"[EXCHANGE SERVICE] Product size not available")
            return {"error": "Product size not available"}, 400
        
        # Parse sizes (handle both string and dict formats)
        sizes = {}
        if isinstance(product.size, str):
            try:
                # Try to parse as JSON first
                import json
                if product.size.strip().startswith("{"):
                    sizes = json.loads(product.size)
                    print(f"[EXCHANGE SERVICE] Parsed sizes from JSON: {sizes}")
                else:
                    # Fallback to eval for legacy format
                    sizes = eval(product.size) if product.size else {}
                    print(f"[EXCHANGE SERVICE] Parsed sizes from eval: {sizes}")
            except Exception as e:
                print(f"[EXCHANGE SERVICE] Error parsing size string: {e}")
                sizes = {}
        elif isinstance(product.size, dict):
            sizes = product.size
            print(f"[EXCHANGE SERVICE] Using size dict: {sizes}")
        
        print(f"[EXCHANGE SERVICE] Final sizes: {sizes}")
        print(f"[EXCHANGE SERVICE] Requested size: {new_size}")
        print(f"[EXCHANGE SERVICE] Size available: {new_size in sizes}")
        print(f"[EXCHANGE SERVICE] Size count: {sizes.get(new_size, 0)}")
        
        if new_size not in sizes or sizes.get(new_size, 0) <= 0:
            print(f"[EXCHANGE SERVICE] Size {new_size} not available")
            return {"error": f"Size {new_size} is not available"}, 400
        
        # Do NOT reserve at request time as per business rule; reserve on approval

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
            old_size='N/A',  # Order items don't store size, so we use N/A
            new_size=new_size,
            reason=reason,
            status="initiated"
        )
        
        print(f"[EXCHANGE SERVICE] Exchange object created: {exchange}")
        
        db.session.add(exchange)
        db.session.commit()
        
        print(f"[EXCHANGE SERVICE] Exchange saved to database with ID: {exchange.id}")
        
        return {"success": True, "message": "Exchange request created successfully", "exchange_id": exchange.id}, 201
        
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
            
            # Add product information
            if exchange.product:
                exchange_dict["product"] = exchange.product.as_dict()
            
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
                # Add customer info
                if exchange.order.customer:
                    exchange_dict["customer"] = exchange.order.customer.as_dict()
            
            # Add product information
            if exchange.product:
                exchange_dict["product"] = exchange.product.as_dict()
            
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
            if exchange.order.customer:
                exchange_dict["customer"] = exchange.order.customer.as_dict()
        
        if exchange.product:
            exchange_dict["product"] = exchange.product.as_dict()
        
        if exchange.admin:
            exchange_dict["admin"] = exchange.admin.as_dict()
        
        if exchange.delivery_guy:
            exchange_dict["delivery_guy"] = exchange.delivery_guy.as_dict()
        
        return {"success": True, "exchange": exchange_dict}, 200
        
    except Exception as e:
        print(f"Get exchange by ID error: {str(e)}")
        return {"error": "Failed to fetch exchange"}, 500

def approve_exchange(exchange_id, admin_id, admin_notes=None):
    """Approve an exchange request"""
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

        # Reserve inventory for new size at approval time (decrement new size)
        product = Product.query.get(exchange.product_id)
        if product and hasattr(product, 'size') and product.size:
            try:
                import json
                sizes = {}
                if isinstance(product.size, str):
                    if product.size.strip().startswith("{"):
                        sizes = json.loads(product.size)
                    else:
                        sizes = eval(product.size) if product.size else {}
                elif isinstance(product.size, dict):
                    sizes = product.size
                if sizes.get(exchange.new_size, 0) <= 0:
                    return {"error": f"Size {exchange.new_size} is no longer available"}, 400
                sizes[exchange.new_size] = int(sizes.get(exchange.new_size, 0)) - 1
                product.size = json.dumps(sizes)
            except Exception as e:
                db.session.rollback()
                print(f"[EXCHANGE SERVICE] Reserve on approve failed: {e}")
                return {"error": "Failed to reserve size on approval"}, 500

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
    """Assign delivery guy for exchange"""
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

def mark_exchange_delivered(exchange_id):
    """Mark exchange as delivered"""
    try:
        exchange = Exchange.query.get(exchange_id)
        if not exchange:
            return {"error": "Exchange not found"}, 404
        
        success, message = exchange.mark_delivered()
        if not success:
            return {"error": message}, 400
        
        # When delivered, add the returned old size back to inventory (+1)
        product = Product.query.get(exchange.product_id)
        if product and hasattr(product, 'size') and product.size:
            try:
                import json
                sizes = {}
                if isinstance(product.size, str):
                    if product.size.strip().startswith("{"):
                        sizes = json.loads(product.size)
                    else:
                        sizes = eval(product.size)
                elif isinstance(product.size, dict):
                    sizes = product.size
                old_sz = exchange.old_size or ''
                if old_sz:
                    sizes[old_sz] = int(sizes.get(old_sz, 0)) + 1
                    product.size = json.dumps(sizes)
            except Exception as e:
                print(f"[EXCHANGE SERVICE] Failed to restock old size on delivery: {e}")
                # continue; not fatal for marking delivered
        
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
            if exchange.product:
                exchange_dict["product"] = exchange.product.as_dict()
            
            exchanges_data.append(exchange_dict)
        
        return {"success": True, "exchanges": exchanges_data}, 200
        
    except Exception as e:
        print(f"Get exchanges by status error: {str(e)}")
        return {"error": "Failed to fetch exchanges"}, 500
