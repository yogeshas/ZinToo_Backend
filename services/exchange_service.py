from models.exchange import Exchange
from models.delivery_onboarding import DeliveryOnboarding
from models.order import Order
from models.product import Product
from extensions import db
from datetime import datetime

def get_exchanges_for_delivery_guy(delivery_guy_id):
    """Get all exchanges assigned to a delivery guy"""
    try:
        exchanges = Exchange.query.filter_by(delivery_guy_id=delivery_guy_id).all()
        
        result = []
        for exchange in exchanges:
            exchange_data = exchange.to_dict()
            # Add customer information if available
            if exchange.order and exchange.order.customer:
                exchange_data['customer'] = {
                    'id': exchange.order.customer.id,
                    'name': exchange.order.customer.username,
                    'email': exchange.order.customer.email,
                    'phone': exchange.order.customer.get_phone_number()
                }
            result.append(exchange_data)
        
        return result
    except Exception as e:
        print(f"Error getting exchanges for delivery guy: {str(e)}")
        return []

def get_exchange_detail_for_delivery_guy(delivery_guy_id, exchange_id):
    """Get detailed exchange information for delivery guy"""
    try:
        exchange = Exchange.query.filter_by(
            id=exchange_id, 
            delivery_guy_id=delivery_guy_id
        ).first()
        
        if not exchange:
            return None
        
        exchange_data = exchange.to_dict()
        
        # Add detailed information
        if exchange.order and exchange.order.customer:
            exchange_data['customer'] = {
                'id': exchange.order.customer.id,
                'name': exchange.order.customer.username,
                'email': exchange.order.customer.email,
                'phone': exchange.order.customer.get_phone_number(),
                'address': exchange.order.customer.get_location()
            }
        
        # Add product information
        if exchange.original_product:
            exchange_data['original_product'] = {
                'id': exchange.original_product.id,
                'name': exchange.original_product.pname,
                'barcode': exchange.original_product.barcode,
                'price': exchange.original_product.price
            }
        
        if exchange.exchange_product:
            exchange_data['exchange_product'] = {
                'id': exchange.exchange_product.id,
                'name': exchange.exchange_product.pname,
                'barcode': exchange.exchange_product.barcode,
                'price': exchange.exchange_product.price
            }
        
        return exchange_data
        
    except Exception as e:
        print(f"Error getting exchange detail: {str(e)}")
        return None

def create_exchange(customer_id, order_id, original_product_id, exchange_product_id, reason, quantity=1, order_item_id=None, new_size=None, new_color=None):
    """Create a new exchange request"""
    try:
        # Validate that the order belongs to the customer
        order = Order.query.filter_by(id=order_id, customer_id=customer_id).first()
        if not order:
            return {"error": "Order not found or access denied"}, 404
        
        # Validate products exist
        original_product = Product.query.get(original_product_id)
        exchange_product = Product.query.get(exchange_product_id)
        
        if not original_product or not exchange_product:
            return {"error": "One or more products not found"}, 404
        
        # Get the order item to get old_size and old_quantity
        from models.order import OrderItem
        order_item = OrderItem.query.get(order_item_id) if order_item_id else None
        
        if not order_item:
            return {"error": "Order item not found"}, 404
        
        # Create exchange
        exchange = Exchange(
            customer_id=customer_id,
            order_id=order_id,
            order_item_id=order_item_id,
            product_id=original_product_id,
            old_size=order_item.selected_size or "Unknown",
            new_size=new_size or "Unknown",
            old_color=order_item.selected_color or "Unknown",
            new_color=new_color or "Unknown",
            old_quantity=order_item.quantity or 1,
            new_quantity=quantity,
            reason=reason,
            status="initiated"
        )
        
        db.session.add(exchange)
        db.session.commit()
        
        return {
            "success": True,
            "message": "Exchange request created successfully",
            "exchange": exchange.to_dict()
        }, 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Error creating exchange: {str(e)}")
        return {"error": "Failed to create exchange request"}, 500

def get_customer_exchanges(customer_id, limit=20):
    """Get all exchanges for a specific customer"""
    try:
        exchanges = Exchange.query.filter_by(customer_id=customer_id)\
            .order_by(Exchange.created_at.desc())\
            .limit(limit).all()
        
        result = []
        for exchange in exchanges:
            exchange_data = exchange.to_dict()
            result.append(exchange_data)
        
        return {
            "success": True,
            "exchanges": result,
            "total": len(result)
        }, 200
        
    except Exception as e:
        print(f"Error getting customer exchanges: {str(e)}")
        return {"error": "Failed to get exchanges"}, 500

def get_all_exchanges(limit=50):
    """Get all exchanges for admin"""
    try:
        exchanges = Exchange.query.order_by(Exchange.created_at.desc())\
            .limit(limit).all()
        
        result = []
        for exchange in exchanges:
            exchange_data = exchange.to_dict()
            # Add customer information
            if exchange.customer:
                exchange_data['customer'] = {
                    'id': exchange.customer.id,
                    'name': exchange.customer.username,
                    'email': exchange.customer.email,
                    'phone': exchange.customer.get_phone_number()
                }
            result.append(exchange_data)
        
        return {
            "success": True,
            "exchanges": result,
            "total": len(result)
        }, 200
        
    except Exception as e:
        print(f"Error getting all exchanges: {str(e)}")
        return {"error": "Failed to get exchanges"}, 500

def get_exchange_by_id(exchange_id):
    """Get exchange by ID"""
    try:
        exchange = Exchange.query.get(exchange_id)
        if not exchange:
            return {"error": "Exchange not found"}, 404
        
        exchange_data = exchange.to_dict()
        
        # Add customer information
        if exchange.customer:
            exchange_data['customer'] = {
                'id': exchange.customer.id,
                'name': exchange.customer.username,
                'email': exchange.customer.email,
                'phone': exchange.customer.get_phone_number()
            }
        
        # Add product information
        if exchange.original_product:
            exchange_data['original_product'] = {
                'id': exchange.original_product.id,
                'name': exchange.original_product.pname,
                'barcode': exchange.original_product.barcode,
                'price': exchange.original_product.price
            }
        
        if exchange.exchange_product:
            exchange_data['exchange_product'] = {
                'id': exchange.exchange_product.id,
                'name': exchange.exchange_product.pname,
                'barcode': exchange.exchange_product.barcode,
                'price': exchange.exchange_product.price
            }
        
        return {
            "success": True,
            "exchange": exchange_data
        }, 200
        
    except Exception as e:
        print(f"Error getting exchange by ID: {str(e)}")
        return {"error": "Failed to get exchange"}, 500

def approve_exchange(exchange_id, admin_id, admin_notes=None):
    """Approve an exchange request"""
    try:
        exchange = Exchange.query.get(exchange_id)
        if not exchange:
            return {"error": "Exchange not found"}, 404
        
        print(f"🔍 DEBUG: Exchange {exchange_id} current status: {exchange.status}")
        
        # Allow approval from any status except already approved or rejected
        if exchange.status in ["approved", "rejected"]:
            return {"error": f"Exchange is already {exchange.status} and cannot be approved"}, 400
        
        exchange.status = "approved"
        exchange.admin_notes = admin_notes
        exchange.updated_at = datetime.now()
        
        db.session.commit()
        
        return {
            "success": True,
            "message": "Exchange approved successfully",
            "exchange": exchange.to_dict()
        }, 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Error approving exchange: {str(e)}")
        return {"error": "Failed to approve exchange"}, 500

def reject_exchange(exchange_id, admin_id, reason):
    """Reject an exchange request"""
    try:
        exchange = Exchange.query.get(exchange_id)
        if not exchange:
            return {"error": "Exchange not found"}, 404
        
        if exchange.status != "pending":
            return {"error": "Exchange is not in pending status"}, 400
        
        exchange.status = "rejected"
        exchange.rejection_reason = reason
        exchange.updated_at = datetime.now()
        
        db.session.commit()
        
        return {
            "success": True,
            "message": "Exchange rejected successfully",
            "exchange": exchange.to_dict()
        }, 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Error rejecting exchange: {str(e)}")
        return {"error": "Failed to reject exchange"}, 500

def assign_delivery(exchange_id, delivery_guy_id):
    """Assign delivery guy to exchange"""
    try:
        exchange = Exchange.query.get(exchange_id)
        if not exchange:
            return {"error": "Exchange not found"}, 404
        
        # Verify delivery guy exists and is approved
        delivery_guy = DeliveryOnboarding.query.filter_by(
            id=delivery_guy_id, 
            status="approved"
        ).first()
        
        if not delivery_guy:
            return {"error": "Delivery guy not found or not approved"}, 404
        
        exchange.delivery_guy_id = delivery_guy_id
        exchange.status = "assigned"
        exchange.updated_at = datetime.now()
        
        db.session.commit()
        
        return {
            "success": True,
            "message": "Delivery guy assigned successfully",
            "exchange": exchange.to_dict()
        }, 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Error assigning delivery: {str(e)}")
        return {"error": "Failed to assign delivery"}, 500

def start_delivery(exchange_id):
    """Start delivery for exchange"""
    try:
        exchange = Exchange.query.get(exchange_id)
        if not exchange:
            return {"error": "Exchange not found"}, 404
        
        if exchange.status != "assigned":
            return {"error": "Exchange is not assigned to delivery"}, 400
        
        exchange.status = "out_for_delivery"
        exchange.updated_at = datetime.now()
        
        db.session.commit()
        
        return {
            "success": True,
            "message": "Delivery started successfully",
            "exchange": exchange.to_dict()
        }, 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Error starting delivery: {str(e)}")
        return {"error": "Failed to start delivery"}, 500

def mark_exchange_delivered(exchange_id):
    """Mark exchange as delivered"""
    try:
        exchange = Exchange.query.get(exchange_id)
        if not exchange:
            return {"error": "Exchange not found"}, 404
        
        if exchange.status not in ["assigned", "out_for_delivery"]:
            return {"error": "Exchange is not ready for delivery"}, 400
        
        exchange.status = "delivered"
        exchange.delivered_at = datetime.now()
        exchange.updated_at = datetime.now()
        
        db.session.commit()
        
        return {
            "success": True,
            "message": "Exchange marked as delivered successfully",
            "exchange": exchange.to_dict()
        }, 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Error marking exchange as delivered: {str(e)}")
        return {"error": "Failed to mark exchange as delivered"}, 500

def get_exchanges_by_status(status, limit=50):
    """Get exchanges by status"""
    try:
        exchanges = Exchange.query.filter_by(status=status)\
            .order_by(Exchange.created_at.desc())\
            .limit(limit).all()
        
        result = []
        for exchange in exchanges:
            exchange_data = exchange.to_dict()
            # Add customer information
            if exchange.customer:
                exchange_data['customer'] = {
                    'id': exchange.customer.id,
                    'name': exchange.customer.username,
                    'email': exchange.customer.email,
                    'phone': exchange.customer.get_phone_number()
                }
            result.append(exchange_data)
        
        return {
            "success": True,
            "exchanges": result,
            "total": len(result),
            "status": status
        }, 200
        
    except Exception as e:
        print(f"Error getting exchanges by status: {str(e)}")
        return {"error": "Failed to get exchanges"}, 500