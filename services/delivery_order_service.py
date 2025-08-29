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
        }
        for item in items
    ]

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
        serialized.append(order_dict)
    return serialized

def get_orders_for_delivery_guy(
    onboarding_id: int, status_filter: Optional[str] = None
) -> List[Order]:
    query = Order.query.filter_by(delivery_guy_id=onboarding_id)

    if status_filter:
        status_filter = status_filter.lower()
        if status_filter in ("approved", "active"):
            query = query.filter(
                Order.status.in_(
                    [
                        "confirmed",
                        "processing",
                        "shipped",
                        "out_for_delivery",
                    ]
                )
            )
        elif status_filter in ("cancelled", "canceled"):
            query = query.filter(Order.status == "cancelled")
        elif status_filter in ("delivered", "completed"):
            query = query.filter(Order.status == "delivered")
        elif status_filter == "rejected":
            query = query.filter(Order.status == "rejected")
        elif status_filter == "assigned":
            # Any order assigned to the delivery guy regardless of status
            pass
        else:
            # Unknown filter: return empty to be explicit
            return []

    return query.order_by(Order.id.desc()).all()


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
        order = Order.query.filter_by(id=order_id, delivery_guy_id=onboarding_id).first()
        if not order:
            return {"success": False, "message": "Order not found or not assigned to you"}
        
        # Check if order can be approved
        if order.status in ["delivered", "cancelled", "rejected"]:
            return {"success": False, "message": f"Cannot approve order with status: {order.status}"}
        
        # Update order status to confirmed
        order.status = "confirmed"
        order.updated_at = datetime.utcnow()
        
        # Add approval note
        order.delivery_notes = (order.delivery_notes or "") + f"\n[APPROVED] Order approved by delivery personnel at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"
        
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
        # Get the order
        order = Order.query.filter_by(id=order_id, delivery_guy_id=onboarding_id).first()
        if not order:
            return {"success": False, "message": "Order not found or not assigned to you"}
        
        # Check if order can be rejected
        if order.status in ["delivered", "cancelled"]:
            return {"success": False, "message": f"Cannot reject order with status: {order.status}"}
        
        # Update order status to rejected
        order.status = "rejected"
        order.updated_at = datetime.utcnow()
        
        # Add rejection note
        order.delivery_notes = (order.delivery_notes or "") + f"\n[REJECTED] Order rejected by delivery personnel at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}. Reason: {rejection_reason}"
        
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

def out_for_delivery_order_by_delivery_guy(delivery_guy_id: int, order_id: int, out_for_delivery_reason: str) -> Dict[str, Any]:
    """Out for delivery an order by delivery guy"""
    try:
        order = Order.query.filter_by(id=order_id, delivery_guy_id=delivery_guy_id).first()
        if not order:
            return {"success": False, "message": "Order not found or not assigned to you"}

        # Update order status to out for delivery
        order.status = "out_for_delivery"
        order.updated_at = datetime.utcnow()
        
        # Add out for delivery note
        order.delivery_notes = (order.delivery_notes or "") + f"\n[OUT FOR DELIVERY] Order out for delivery by delivery personnel at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}. Reason: {out_for_delivery_reason}"


        db.session.commit()

        return {
            "success": True,
            "message": "Order out for delivery successfully",
            "order": _serialize_order(order)
        }
        
    except Exception as e:
        print(f"Error out for delivery order: {e}")
        db.session.rollback()
        return {"success": False, "message": "Failed to out for delivery order"}

def delivered_order_by_delivery_guy(delivery_guy_id: int, order_id: int, delivered_reason: str) -> Dict[str, Any]:
    """Delivered an order by delivery guy"""
    try:
        order = Order.query.filter_by(id=order_id, delivery_guy_id=delivery_guy_id).first()
        if not order:
            return {"success": False, "message": "Order not found or not assigned to you"}

        # Update order status to delivered
        order.status = "delivered"
        order.updated_at = datetime.utcnow()
        
        # Add delivered note
        order.delivery_notes = (order.delivery_notes or "") + f"\n[DELIVERED] Order delivered by delivery personnel at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}. Reason: {delivered_reason}"

        db.session.commit()

        return {
            "success": True,
            "message": "Order delivered successfully",
            "order": _serialize_order(order)
        }
        
    except Exception as e:
        print(f"Error delivering order: {e}")
        db.session.rollback()
        return {"success": False, "message": "Failed to deliver order"}

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
