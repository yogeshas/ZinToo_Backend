from models.order import OrderItem
from models.order import Order
from models.delivery_onboarding import DeliveryOnboarding
from extensions import db

def get_cancelled_order_items_for_delivery_guy(delivery_guy_id):
    """Get all cancelled order items assigned to a delivery guy"""
    try:
        # Get cancelled order items from orders assigned to this delivery guy
        cancelled_items = db.session.query(OrderItem).join(
            Order, OrderItem.order_id == Order.id
        ).filter(
            Order.delivery_guy_id == delivery_guy_id,
            OrderItem.status == "cancelled"
        ).all()
        
        result = []
        for item in cancelled_items:
            item_data = item.to_dict()
            
            # Add order information
            if item.order:
                item_data['order'] = {
                    'id': item.order.id,
                    'order_number': item.order.order_number,
                    'status': item.order.status,
                    'created_at': item.order.created_at.isoformat() if item.order.created_at else None
                }
                
                # Add customer information
                if item.order.customer:
                    item_data['customer'] = {
                        'id': item.order.customer.id,
                        'name': item.order.customer.name,
                        'email': item.order.customer.email,
                        'phone': item.order.customer.phone
                    }
            
            # Add product information
            if item.product:
                item_data['product'] = {
                    'id': item.product.id,
                    'name': item.product.pname,
                    'barcode': item.product.barcode,
                    'price': item.product.price
                }
            
            result.append(item_data)
        
        return result
    except Exception as e:
        print(f"Error getting cancelled order items for delivery guy: {str(e)}")
        return []

def get_order_item_detail_for_delivery_guy(delivery_guy_id, item_id):
    """Get detailed order item information for delivery guy"""
    try:
        item = db.session.query(OrderItem).join(
            Order, OrderItem.order_id == Order.id
        ).filter(
            Order.delivery_guy_id == delivery_guy_id,
            OrderItem.id == item_id
        ).first()
        
        if not item:
            return None
        
        item_data = item.to_dict()
        
        # Add detailed order information
        if item.order:
            item_data['order'] = {
                'id': item.order.id,
                'order_number': item.order.order_number,
                'status': item.order.status,
                'total_amount': item.order.total_amount,
                'created_at': item.order.created_at.isoformat() if item.order.created_at else None
            }
            
            # Add customer information
            if item.order.customer:
                item_data['customer'] = {
                    'id': item.order.customer.id,
                    'name': item.order.customer.name,
                    'email': item.order.customer.email,
                    'phone': item.order.customer.phone,
                    'address': item.order.customer.address
                }
        
        # Add detailed product information
        if item.product:
            item_data['product'] = {
                'id': item.product.id,
                'name': item.product.pname,
                'barcode': item.product.barcode,
                'price': item.product.price,
                'description': item.product.pdescription,
                'images': item.product.images if hasattr(item.product, 'images') else []
            }
        
        return item_data
        
    except Exception as e:
        print(f"Error getting order item detail: {str(e)}")
        return None
