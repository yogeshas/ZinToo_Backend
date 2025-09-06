from typing import List, Optional, Dict, Any
import json
from extensions import db
from models.order import Order, OrderItem
from models.customer import Customer
from models.delivery_loyalty import Delivery_Loyalty
from datetime import datetime


def _serialize_order(order: Order) -> Dict[str, Any]:
    order_dict = order.as_dict()

    # Add human-readable delivery address
    def _format_delivery_address_text(raw_address: Any) -> Optional[str]:
        try:
            address_obj = raw_address if isinstance(raw_address, dict) else json.loads(raw_address or "{}")
            parts: List[str] = []
            for key in [
                "address_line1",
                "address_line2",
                "city",
                "state",
                "postal_code",
                "country",
            ]:
                value = address_obj.get(key)
                if value:
                    value_str = str(value).strip()
                    if value_str:
                        parts.append(value_str)
            return ", ".join(parts) if parts else None
        except Exception:
            return None

    delivery_address_text = _format_delivery_address_text(order_dict.get("delivery_address"))
    if delivery_address_text:
        order_dict["delivery_address_text"] = delivery_address_text

    # Attach customer summary
    customer: Optional[Customer] = Customer.query.get(order.customer_id)
    if customer:
        order_dict["customer"] = {
            "id": customer.id,
            "username": customer.username,
            "email": customer.email,
            "phone_number": customer.get_phone_number(),
        }
        # Duplicate phone to top-level for easy access in clients
        order_dict["customer_phone_number"] = customer.get_phone_number()

    # Attach items with basic product snapshot already on OrderItem
    items: List[OrderItem] = (
        OrderItem.query.filter_by(order_id=order.id)
        .order_by(OrderItem.id.asc())
        .all()
    )
    order_dict["items"] = [
        {
            "id": item.id,
            "product_id": item.product_id,
            "product_name": item.product_name,
            "product_image": item.product_image,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "total_price": item.total_price,
            "selected_size": getattr(item, 'selected_size', None),
            "status": getattr(item, 'status', 'pending'),
            "delivery_track": getattr(item, 'delivery_track', None),
            "delivery_track_display": _get_delivery_track_display(getattr(item, 'delivery_track', 'normal')),
            "delivery_guy_id": getattr(item, 'delivery_guy_id', None),
        }
        for item in items
    ]

    # Add delivery purpose information
    try:
        from models.exchange import Exchange
        exchanges = Exchange.query.filter_by(order_id=order.id).all()
        
        if exchanges:
            order_dict["delivery_purpose"] = "exchange"
            order_dict["exchange_count"] = len(exchanges)
            order_dict["exchange_statuses"] = [ex.status for ex in exchanges]
        else:
            order_dict["delivery_purpose"] = "normal"
            order_dict["exchange_count"] = 0
            order_dict["exchange_statuses"] = []
    except Exception as e:
        print(f"Error getting delivery purpose: {e}")
        order_dict["delivery_purpose"] = "unknown"
        order_dict["exchange_count"] = 0
        order_dict["exchange_statuses"] = []

    return order_dict


def serialize_orders_with_customer(orders: List[Order]) -> List[Dict[str, Any]]:
    """Serialize a list of orders including minimal customer summary.

    This ensures clients (e.g., Flutter) can directly show customer.username
    without additional requests.
    """
    serialized: List[Dict[str, Any]] = []
    # Preload customers to minimize queries when possible
    for order in orders:
        order_dict: Dict[str, Any] = order.as_dict()
        # Add human-readable delivery address
        try:
            address_obj = json.loads(order_dict.get("delivery_address") or "{}")
        except Exception:
            address_obj = {}
        parts: List[str] = []
        for key in [
            "address_line1",
            "address_line2",
            "city",
            "state",
            "postal_code",
            "country",
        ]:
            value = address_obj.get(key)
            if value:
                value_str = str(value).strip()
                if value_str:
                    parts.append(value_str)
        if parts:
            order_dict["delivery_address_text"] = ", ".join(parts)
        customer: Optional[Customer] = None
        try:
            customer = Customer.query.get(order.customer_id)
        except Exception:
            customer = None
        if customer:
            order_dict["customer"] = {
                "id": customer.id,
                "username": getattr(customer, "username", None),
                "email": getattr(customer, "email", None),
                "phone_number": customer.get_phone_number() if hasattr(customer, "get_phone_number") else None,
            }
            order_dict["customer_phone_number"] = customer.get_phone_number() if hasattr(customer, "get_phone_number") else None
        
        # Add delivery track and overall status
        order_dict["delivery_track"] = getattr(order, 'delivery_track', 'normal')
        order_dict["overall_status"] = getattr(order, 'overall_status', order.status)
        order_dict["delivery_track_display"] = _get_delivery_track_display(getattr(order, 'delivery_track', 'normal'))
        
        # Add assigned items information
        assigned_items = getattr(order, 'assigned_items', [])
        order_dict["assigned_items"] = []
        for item in assigned_items:
            item_dict = {
                "id": item.id,
                "product_id": item.product_id,
                "product_name": item.product_name,
                "product_image": item.product_image,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "total_price": item.total_price,
                "selected_size": getattr(item, 'selected_size', None),
                "status": getattr(item, 'status', 'pending'),
                "delivery_track": getattr(item, 'delivery_track', 'normal'),
                "delivery_track_display": _get_delivery_track_display(getattr(item, 'delivery_track', 'normal')),
                "delivery_guy_id": getattr(item, 'delivery_guy_id', None),
            }
            order_dict["assigned_items"].append(item_dict)
        
        serialized.append(order_dict)
    return serialized

def get_orders_for_delivery_guy(
    onboarding_id: int, status_filter: Optional[str] = None
) -> List[Order]:
    # NEW LOGIC: Get orders based on order_item status and delivery_track
    # Group by status and delivery_track type
    
    # Get all order items assigned to this delivery guy
    order_items = OrderItem.query.filter_by(delivery_guy_id=onboarding_id).all()
    
    if not order_items:
        return []
    
    # Group order items by order_id and determine the overall status
    order_groups = {}
    for item in order_items:
        order_id = item.order_id
        if order_id not in order_groups:
            order_groups[order_id] = {
                'items': [],
                'statuses': set(),
                'delivery_tracks': set(),
                'order': None
            }
        
        order_groups[order_id]['items'].append(item)
        order_groups[order_id]['statuses'].add(getattr(item, 'status', 'pending'))
        order_groups[order_id]['delivery_tracks'].add(getattr(item, 'delivery_track', 'normal'))
    
    # Get the actual orders
    order_ids = list(order_groups.keys())
    orders = Order.query.filter(Order.id.in_(order_ids)).all()
    
    # Attach order data to groups
    for order in orders:
        if order.id in order_groups:
            order_groups[order.id]['order'] = order
    
    # Filter based on status_filter
    filtered_orders = []
    for order_id, group in order_groups.items():
        order = group['order']
        if not order:
            continue
            
        # Determine overall status based on item statuses
        overall_status = _determine_overall_status(group['statuses'], group['delivery_tracks'])
        
        # Apply status filter
        if status_filter:
            status_filter = status_filter.lower()
            if status_filter == "assigned" or status_filter is None:
                # Show all assigned orders
                pass
            elif status_filter == "pending":
                if overall_status != "pending":
                    continue
            elif status_filter == "confirmed" or status_filter == "approved":
                if overall_status not in ["confirmed", "approved"]:
                    continue
            elif status_filter == "delivered":
                if overall_status != "delivered":
                    continue
            elif status_filter == "cancelled":
                if overall_status != "cancelled":
                    continue
            elif status_filter == "exchange":
                if "exchange_pickup" not in group['delivery_tracks']:
                    continue
            elif status_filter == "cancel_pickup":
                if "cancel_pickup" not in group['delivery_tracks']:
                    continue
            else:
                # Unknown filter
                continue
        
        # Add order with enhanced data
        order.delivery_track = _determine_delivery_track(group['delivery_tracks'])
        order.overall_status = overall_status
        order.assigned_items = group['items']
        filtered_orders.append(order)
    
    return sorted(filtered_orders, key=lambda x: x.id, reverse=True)

def _determine_overall_status(statuses, delivery_tracks):
    """Determine overall status based on item statuses and delivery tracks"""
    statuses = list(statuses)
    delivery_tracks = list(delivery_tracks)
    
    # If any item is cancelled, overall is cancelled
    if "cancelled" in statuses:
        return "cancelled"
    
    # If any item is rejected, overall is rejected
    if "rejected" in statuses:
        return "rejected"
    
    # If any item is delivered, check if all are delivered
    if "delivered" in statuses:
        if all(status == "delivered" for status in statuses):
            return "delivered"
        else:
            return "processing"
    
    # If any item is out_for_delivery, overall is out_for_delivery
    if "out_for_delivery" in statuses:
        return "out_for_delivery"
    
    # If any item is processing, overall is processing
    if "processing" in statuses:
        return "processing"
    
    # If any item is confirmed or approved, overall is confirmed
    if "confirmed" in statuses or "approved" in statuses:
        return "confirmed"
    
    # If any item is assigned, overall is assigned
    if "assigned" in statuses:
        return "assigned"
    
    # Default to pending
    return "pending"

def _determine_delivery_track(delivery_tracks):
    """Determine delivery track type"""
    delivery_tracks = list(delivery_tracks)
    
    # Priority: exchange_pickup > cancel_pickup > normal
    if "exchange_pickup" in delivery_tracks:
        return "exchange_pickup"
    elif "cancel_pickup" in delivery_tracks:
        return "cancel_pickup"
    else:
        return "normal"

def _get_delivery_track_display(delivery_track):
    """Get human-readable delivery track display"""
    track_displays = {
        'normal': 'Normal Delivery',
        'cancel_pickup': 'Cancel Pickup',
        'exchange_pickup': 'Exchange Pickup'
    }
    return track_displays.get(delivery_track, 'Normal Delivery')


def get_order_detail_for_delivery_guy(
    onboarding_id: int, order_id: int
) -> Optional[Dict[str, Any]]:
    order: Optional[Order] = (
        Order.query.filter_by(id=order_id, delivery_guy_id=onboarding_id).first()
    )
    if not order:
        return None
    return _serialize_order(order)


def approve_order_by_delivery_guy(onboarding_id: int, order_id: int) -> Dict[str, Any]:
    """Approve an order by delivery guy"""
    try:
        # Get the order
        order = Order.query.get(order_id)
        if not order:
            return {"success": False, "message": "Order not found"}
        
        # Check if delivery guy has any items assigned in this order
        assigned_items = OrderItem.query.filter_by(
            order_id=order_id, 
            delivery_guy_id=onboarding_id
        ).all()
        
        if not assigned_items:
            return {"success": False, "message": "No items assigned to you in this order"}
        
        # Check if order can be approved
        if order.status in ["delivered", "cancelled", "rejected"]:
            return {"success": False, "message": f"Cannot approve order with status: {order.status}"}
        
        # Update assigned items status to confirmed
        for item in assigned_items:
            item.status = "confirmed"
            item.updated_at = datetime.utcnow()
        
        # Update order status to confirmed (if all items are confirmed)
        all_items = OrderItem.query.filter_by(order_id=order_id).all()
        if all(item.status in ["confirmed", "delivered"] for item in all_items):
            order.status = "confirmed"
        
        order.updated_at = datetime.utcnow()
        
        # Add approval note
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        order.delivery_notes = (order.delivery_notes or "") + f"\n[APPROVED] Order approved by delivery personnel at {timestamp}"
        
        # Update delivery loyalty table
        loyalty_record = Delivery_Loyalty.query.filter_by(delivery_user_id=onboarding_id).first()
        if loyalty_record:
            loyalty_record.add_approved_order(order_id)
            loyalty_record.last_updated = datetime.utcnow()
        
        db.session.commit()
        
        return {
            "success": True,
            "message": "Order approved successfully",
            "order": _serialize_order(order)
        }
        
    except Exception as e:
        print(f"Error approving order: {e}")
        db.session.rollback()
        return {"success": False, "message": "Failed to approve order"}

def reject_order_by_delivery_guy(onboarding_id: int, order_id: int, rejection_reason: str) -> Dict[str, Any]:
    """Reject an order by delivery guy"""
    try:
        print(f"🔍 [REJECT ORDER] Delivery guy {onboarding_id} trying to reject order {order_id}")
        
        # Get the order
        order = Order.query.get(order_id)
        if not order:
            print(f"❌ [REJECT ORDER] Order {order_id} not found")
            return {"success": False, "message": "Order not found"}
        
        print(f"✅ [REJECT ORDER] Found order {order_id} with status: {order.status}")
        
        # Check if delivery guy has any items assigned in this order
        assigned_items = OrderItem.query.filter_by(
            order_id=order_id, 
            delivery_guy_id=onboarding_id
        ).all()
        
        print(f"🔍 [REJECT ORDER] Found {len(assigned_items)} items assigned to delivery guy {onboarding_id}")
        
        if not assigned_items:
            # Let's also check if there are any items in the order at all
            all_items = OrderItem.query.filter_by(order_id=order_id).all()
            print(f"🔍 [REJECT ORDER] Total items in order: {len(all_items)}")
            for item in all_items:
                print(f"   - Item {item.id}: delivery_guy_id={getattr(item, 'delivery_guy_id', None)}, status={getattr(item, 'status', 'unknown')}")
            
            return {"success": False, "message": "No items assigned to you in this order"}
        
        # Check if order can be rejected
        if order.status in ["delivered", "cancelled"]:
            return {"success": False, "message": f"Cannot reject order with status: {order.status}"}
        
        # Update assigned items status to rejected
        for item in assigned_items:
            item.status = "rejected"
            item.updated_at = datetime.utcnow()
        
        # Update order status to rejected (if all items are rejected)
        all_items = OrderItem.query.filter_by(order_id=order_id).all()
        if all(item.status == "rejected" for item in all_items):
            order.status = "rejected"
        
        order.updated_at = datetime.utcnow()
        
        # Add rejection note
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        order.delivery_notes = (order.delivery_notes or "") + f"\n[REJECTED] Order rejected by delivery personnel at {timestamp}. Reason: {rejection_reason}"
        
        # Update delivery loyalty table
        loyalty_record = Delivery_Loyalty.query.filter_by(delivery_user_id=onboarding_id).first()
        if loyalty_record:
            loyalty_record.add_rejected_order(order_id)
            loyalty_record.last_updated = datetime.utcnow()
        
        db.session.commit()
        
        return {
            "success": True,
            "message": "Order rejected successfully",
            "order": _serialize_order(order)
        }
        
    except Exception as e:
        print(f"Error rejecting order: {e}")
        db.session.rollback()
        return {"success": False, "message": "Failed to reject order"}

def out_for_delivery_order_by_delivery_guy(delivery_guy_id: int, order_id: int, out_for_delivery_reason: str, is_exchange: bool = False) -> Dict[str, Any]:
    """Out for delivery an order by delivery guy with exchange status tracking"""
    try:
        order = Order.query.get(order_id)
        if not order:
            return {"success": False, "message": "Order not found"}
        
        # Check if delivery guy has any items assigned in this order
        assigned_items = OrderItem.query.filter_by(
            order_id=order_id, 
            delivery_guy_id=delivery_guy_id
        ).all()
        
        if not assigned_items:
            return {"success": False, "message": "No items assigned to you in this order"}

        # Auto-detect if this is an exchange delivery if not explicitly specified
        if not is_exchange:
            from models.exchange import Exchange
            exchanges = Exchange.query.filter_by(order_id=order_id, delivery_guy_id=delivery_guy_id).all()
            is_exchange = len(exchanges) > 0
            if is_exchange:
                print(f"Auto-detected exchange delivery for order {order_id}")

        # Update assigned items status to out for delivery
        for item in assigned_items:
            item.status = "out_for_delivery"
            item.updated_at = datetime.utcnow()
        
        # Update order status to out for delivery (if all items are out for delivery)
        all_items = OrderItem.query.filter_by(order_id=order_id).all()
        if all(item.status in ["out_for_delivery", "delivered"] for item in all_items):
            order.status = "out_for_delivery"
        
        order.updated_at = datetime.utcnow()
        
        # Set exchange delivery flag
        order.is_exchange_delivery = is_exchange
        
        # Add out for delivery note with delivery type
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        delivery_type = "EXCHANGE" if is_exchange else "NORMAL"
        
        order.delivery_notes = (order.delivery_notes or "") + f"\n[OUT FOR DELIVERY - {delivery_type}] Order out for delivery by delivery personnel at {timestamp}. Reason: {out_for_delivery_reason}"

        # If this is an exchange delivery, also update exchange status
        if is_exchange:
            from models.exchange import Exchange
            exchanges = Exchange.query.filter_by(order_id=order_id, delivery_guy_id=delivery_guy_id).all()
            
            if exchanges:
                for exchange in exchanges:
                    if exchange.status == "assigned":  # Only update if exchange is assigned for delivery
                        exchange.status = "out_for_delivery"
                        exchange.updated_at = datetime.utcnow()
                        print(f"Updated exchange {exchange.id} status to out_for_delivery")
                    else:
                        print(f"Exchange {exchange.id} status is {exchange.status}, not updating")
            else:
                print(f"No exchanges found for order {order_id} assigned to delivery guy {delivery_guy_id}")

        db.session.commit()

        return {
            "success": True, 
            "message": f"Order marked as out for delivery ({delivery_type.lower()}) successfully",
            "order": _serialize_order(order),
            "delivery_type": delivery_type.lower(),
            "is_exchange": is_exchange
        }
        
    except Exception as e:
        print(f"Error out for delivery order: {e}")
        db.session.rollback()
        return {"success": False, "message": "Failed to mark order as out for delivery"}

def delivered_order_by_delivery_guy(delivery_guy_id: int, order_id: int, delivered_reason: str) -> Dict[str, Any]:
    """Delivered an order by delivery guy with exchange status tracking"""
    try:
        order = Order.query.get(order_id)
        if not order:
            return {"success": False, "message": "Order not found"}
        
        # Check if delivery guy has any items assigned in this order
        assigned_items = OrderItem.query.filter_by(
            order_id=order_id, 
            delivery_guy_id=delivery_guy_id
        ).all()
        
        if not assigned_items:
            return {"success": False, "message": "No items assigned to you in this order"}

        # Check if this was an exchange delivery
        is_exchange = getattr(order, 'is_exchange_delivery', False)
        
        # Update assigned items status to delivered
        for item in assigned_items:
            item.status = "delivered"
            item.updated_at = datetime.utcnow()
        
        # Update order status to delivered (if all items are delivered)
        all_items = OrderItem.query.filter_by(order_id=order_id).all()
        if all(item.status == "delivered" for item in all_items):
            order.status = "delivered"
        
        order.updated_at = datetime.utcnow()
        
        # Add delivered note with delivery type
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        delivery_type = "EXCHANGE" if is_exchange else "NORMAL"
        
        order.delivery_notes = (order.delivery_notes or "") + f"\n[DELIVERED - {delivery_type}] Order delivered by delivery personnel at {timestamp}. Reason: {delivered_reason}"

        # If this was an exchange delivery, also update exchange status
        if is_exchange:
            from models.exchange import Exchange
            exchanges = Exchange.query.filter_by(order_id=order_id, delivery_guy_id=delivery_guy_id).all()
            
            if exchanges:
                for exchange in exchanges:
                    if exchange.status == "out_for_delivery":  # Only update if exchange is out for delivery
                        exchange.status = "delivered"
                        exchange.delivered_at = datetime.utcnow()
                        exchange.updated_at = datetime.utcnow()
                        print(f"Updated exchange {exchange.id} status to delivered")
                    else:
                        print(f"Exchange {exchange.id} status is {exchange.status}, not updating")
            else:
                print(f"No exchanges found for order {order_id} assigned to delivery guy {delivery_guy_id}")

        db.session.commit()

        return {
            "success": True,
            "message": f"Order delivered successfully ({delivery_type.lower()})",
            "order": _serialize_order(order),
            "delivery_type": delivery_type.lower(),
            "is_exchange": is_exchange
        }
        
    except Exception as e:
        print(f"Error delivering order: {e}")
        db.session.rollback()
        return {"success": False, "message": "Failed to deliver order"}


def get_order_delivery_purpose(order_id: int) -> Dict[str, Any]:
    """Get delivery purpose information for an order"""
    try:
        from models.exchange import Exchange
        
        # Check if order has exchanges
        exchanges = Exchange.query.filter_by(order_id=order_id).all()
        
        if exchanges:
            # Check exchange statuses
            exchange_statuses = [ex.status for ex in exchanges]
            
            if "out_for_delivery" in exchange_statuses:
                return {
                    "purpose": "exchange",
                    "type": "exchange_delivery",
                    "exchange_count": len(exchanges),
                    "exchange_statuses": exchange_statuses,
                    "message": "Exchange delivery in progress"
                }
            elif "delivered" in exchange_statuses:
                return {
                    "purpose": "exchange",
                    "type": "exchange_completed",
                    "exchange_count": len(exchanges),
                    "exchange_statuses": exchange_statuses,
                    "message": "Exchange delivery completed"
                }
            else:
                return {
                    "purpose": "exchange",
                    "type": "exchange_pending",
                    "exchange_count": len(exchanges),
                    "exchange_statuses": exchange_statuses,
                    "message": "Exchange pending delivery"
                }
        else:
            # Check order status for normal delivery
            order = Order.query.get(order_id)
            if order and order.status == "out_for_delivery":
                return {
                    "purpose": "normal",
                    "type": "normal_delivery",
                    "message": "Normal order delivery in progress"
                }
            elif order and order.status == "delivered":
                return {
                    "purpose": "normal",
                    "type": "normal_completed",
                    "message": "Normal order delivery completed"
                }
            else:
                return {
                    "purpose": "normal",
                    "type": "normal_pending",
                    "message": "Normal order pending delivery"
                }
                
    except Exception as e:
        print(f"Error getting delivery purpose: {e}")
        return {
            "purpose": "unknown",
            "type": "unknown",
            "message": "Unable to determine delivery purpose"
        }

def get_delivery_loyalty_with_order_tracking(delivery_user_id: int) -> Optional[Dict[str, Any]]:
    """Get delivery loyalty information including order tracking"""
    try:
        loyalty_record = Delivery_Loyalty.query.filter_by(delivery_user_id=delivery_user_id).first()
        if not loyalty_record:
            return None
        
        return {
            "id": loyalty_record.id,
            "delivery_user_id": loyalty_record.delivery_user_id,
            "order_count": loyalty_record.order_count,
            "total_earnings": loyalty_record.total_earnings,
            "last_order_date": loyalty_record.last_order_date.isoformat() if loyalty_record.last_order_date else None,
            "points": loyalty_record.points,
            "tier": loyalty_record.tier,
            "last_updated": loyalty_record.last_updated.isoformat(),
            "rejected_order_ids": loyalty_record.get_rejected_order_ids(),
            "approved_order_ids": loyalty_record.get_approved_order_ids(),
            "rejected_count": len(loyalty_record.get_rejected_order_ids()),
            "approved_count": len(loyalty_record.get_approved_order_ids())
        }
        
    except Exception as e:
        print(f"Error getting delivery loyalty: {e}")
        return None
