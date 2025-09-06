#!/usr/bin/env python3
"""
Improved Delivery Order Service

This service provides better debugging and error handling for delivery orders API.
"""

from typing import List, Dict, Any, Optional
from models.order import Order, OrderItem
from models.delivery_onboarding import DeliveryOnboarding
from utils.crypto import encrypt_payload, decrypt_payload
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_orders_for_delivery_guy_improved(
    onboarding_id: int, 
    status_filter: Optional[str] = None,
    debug: bool = False
) -> List[Order]:
    """
    Improved function to get orders for delivery guy with better debugging
    
    Args:
        onboarding_id: The delivery guy's onboarding ID
        status_filter: Optional status filter
        debug: Enable debug logging
    
    Returns:
        List of orders assigned to the delivery guy
    """
    
    if debug:
        logger.info(f"🔍 Getting orders for delivery guy ID: {onboarding_id}")
        logger.info(f"🔍 Status filter: {status_filter}")
    
    try:
        # First, verify the delivery guy exists and is approved
        delivery_guy = DeliveryOnboarding.query.get(onboarding_id)
        if not delivery_guy:
            logger.error(f"❌ Delivery guy with ID {onboarding_id} not found")
            return []
        
        if delivery_guy.status != "approved":
            logger.error(f"❌ Delivery guy {onboarding_id} is not approved (status: {delivery_guy.status})")
            return []
        
        if debug:
            logger.info(f"✅ Delivery guy found: {delivery_guy.first_name} {delivery_guy.last_name}")
        
        # Build the query
        query = Order.query.filter_by(delivery_guy_id=onboarding_id)
        
        if debug:
            # Log the base query
            logger.info(f"🔍 Base query: Orders with delivery_guy_id = {onboarding_id}")
        
        # Apply status filter
        if status_filter:
            status_filter = status_filter.lower()
            if debug:
                logger.info(f"🔍 Applying status filter: {status_filter}")
            
            if status_filter in ("approved", "active"):
                query = query.filter(
                    Order.status.in_([
                        "confirmed",
                        "processing", 
                        "shipped",
                        "out_for_delivery",
                        "assigned"
                    ])
                )
                if debug:
                    logger.info("🔍 Filtered for active orders")
            elif status_filter in ("cancelled", "canceled"):
                query = query.filter(Order.status == "cancelled")
                if debug:
                    logger.info("🔍 Filtered for cancelled orders")
            elif status_filter in ("delivered", "completed"):
                query = query.filter(Order.status == "delivered")
                if debug:
                    logger.info("🔍 Filtered for delivered orders")
            elif status_filter == "rejected":
                query = query.filter(Order.status == "rejected")
                if debug:
                    logger.info("🔍 Filtered for rejected orders")
            elif status_filter == "assigned":
                # Any order assigned to the delivery guy regardless of status
                if debug:
                    logger.info("🔍 Showing all assigned orders")
                pass
            elif status_filter == "pending":
                query = query.filter(Order.status == "pending")
                if debug:
                    logger.info("🔍 Filtered for pending orders")
            else:
                logger.warning(f"⚠️ Unknown status filter: {status_filter}")
                return []
        
        # Execute the query
        orders = query.order_by(Order.id.desc()).all()
        
        if debug:
            logger.info(f"✅ Found {len(orders)} orders for delivery guy {onboarding_id}")
            for order in orders:
                logger.info(f"   - Order {order.order_number}: {order.status}")
        
        return orders
        
    except Exception as e:
        logger.error(f"❌ Error getting orders for delivery guy {onboarding_id}: {str(e)}")
        return []

def get_order_items_for_delivery_guy_improved(
    onboarding_id: int,
    status_filter: Optional[str] = None,
    debug: bool = False
) -> List[OrderItem]:
    """
    Get order items assigned to delivery guy
    
    Args:
        onboarding_id: The delivery guy's onboarding ID
        status_filter: Optional status filter
        debug: Enable debug logging
    
    Returns:
        List of order items assigned to the delivery guy
    """
    
    if debug:
        logger.info(f"🔍 Getting order items for delivery guy ID: {onboarding_id}")
    
    try:
        # Verify the delivery guy exists
        delivery_guy = DeliveryOnboarding.query.get(onboarding_id)
        if not delivery_guy or delivery_guy.status != "approved":
            logger.error(f"❌ Delivery guy {onboarding_id} not found or not approved")
            return []
        
        # Build the query for order items
        query = OrderItem.query.filter_by(delivery_guy_id=onboarding_id)
        
        # Apply status filter
        if status_filter:
            status_filter = status_filter.lower()
            if status_filter in ("approved", "active"):
                query = query.filter(
                    OrderItem.status.in_([
                        "confirmed",
                        "processing",
                        "shipped", 
                        "out_for_delivery",
                        "assigned"
                    ])
                )
            elif status_filter in ("cancelled", "canceled"):
                query = query.filter(OrderItem.status == "cancelled")
            elif status_filter in ("delivered", "completed"):
                query = query.filter(OrderItem.status == "delivered")
            elif status_filter == "rejected":
                query = query.filter(OrderItem.status == "rejected")
            elif status_filter == "assigned":
                query = query.filter(OrderItem.status == "assigned")
            elif status_filter == "pending":
                query = query.filter(OrderItem.status == "pending")
        
        # Execute the query
        order_items = query.order_by(OrderItem.id.desc()).all()
        
        if debug:
            logger.info(f"✅ Found {len(order_items)} order items for delivery guy {onboarding_id}")
            for item in order_items:
                logger.info(f"   - Item {item.id}: {item.product_name} - {item.status}")
        
        return order_items
        
    except Exception as e:
        logger.error(f"❌ Error getting order items for delivery guy {onboarding_id}: {str(e)}")
        return []

def get_combined_orders_for_delivery_guy(
    onboarding_id: int,
    status_filter: Optional[str] = None,
    debug: bool = False
) -> Dict[str, Any]:
    """
    Get both orders and order items for delivery guy
    
    Args:
        onboarding_id: The delivery guy's onboarding ID
        status_filter: Optional status filter
        debug: Enable debug logging
    
    Returns:
        Dictionary with orders and order items
    """
    
    if debug:
        logger.info(f"🔍 Getting combined data for delivery guy ID: {onboarding_id}")
    
    try:
        # Get orders
        orders = get_orders_for_delivery_guy_improved(onboarding_id, status_filter, debug)
        
        # Get order items
        order_items = get_order_items_for_delivery_guy_improved(onboarding_id, status_filter, debug)
        
        # Combine the results
        result = {
            "orders": orders,
            "order_items": order_items,
            "total_orders": len(orders),
            "total_items": len(order_items),
            "delivery_guy_id": onboarding_id,
            "status_filter": status_filter
        }
        
        if debug:
            logger.info(f"✅ Combined result: {len(orders)} orders, {len(order_items)} items")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error getting combined data for delivery guy {onboarding_id}: {str(e)}")
        return {
            "orders": [],
            "order_items": [],
            "total_orders": 0,
            "total_items": 0,
            "delivery_guy_id": onboarding_id,
            "status_filter": status_filter,
            "error": str(e)
        }

def debug_delivery_guy_assignments(onboarding_id: int) -> Dict[str, Any]:
    """
    Debug function to check delivery guy assignments
    
    Args:
        onboarding_id: The delivery guy's onboarding ID
    
    Returns:
        Debug information about the delivery guy's assignments
    """
    
    logger.info(f"🔍 Debugging assignments for delivery guy ID: {onboarding_id}")
    
    try:
        # Check delivery guy exists
        delivery_guy = DeliveryOnboarding.query.get(onboarding_id)
        if not delivery_guy:
            return {
                "error": f"Delivery guy with ID {onboarding_id} not found",
                "delivery_guy": None,
                "orders": [],
                "order_items": []
            }
        
        # Get all orders assigned to this delivery guy
        orders = Order.query.filter_by(delivery_guy_id=onboarding_id).all()
        
        # Get all order items assigned to this delivery guy
        order_items = OrderItem.query.filter_by(delivery_guy_id=onboarding_id).all()
        
        # Get orders that have items assigned to this delivery guy
        order_ids_with_items = [item.order_id for item in order_items]
        orders_with_items = Order.query.filter(Order.id.in_(order_ids_with_items)).all()
        
        debug_info = {
            "delivery_guy": {
                "id": delivery_guy.id,
                "name": f"{delivery_guy.first_name} {delivery_guy.last_name}",
                "email": delivery_guy.email,
                "status": delivery_guy.status,
                "phone": delivery_guy.phone_number
            },
            "orders_directly_assigned": [
                {
                    "id": order.id,
                    "order_number": order.order_number,
                    "status": order.status,
                    "assigned_at": order.assigned_at.isoformat() if order.assigned_at else None
                }
                for order in orders
            ],
            "order_items_assigned": [
                {
                    "id": item.id,
                    "order_id": item.order_id,
                    "product_name": item.product_name,
                    "status": item.status
                }
                for item in order_items
            ],
            "orders_with_assigned_items": [
                {
                    "id": order.id,
                    "order_number": order.order_number,
                    "status": order.status,
                    "delivery_guy_id": order.delivery_guy_id
                }
                for order in orders_with_items
            ],
            "summary": {
                "total_orders_directly_assigned": len(orders),
                "total_order_items_assigned": len(order_items),
                "total_orders_with_assigned_items": len(orders_with_items)
            }
        }
        
        logger.info(f"✅ Debug info generated for delivery guy {onboarding_id}")
        return debug_info
        
    except Exception as e:
        logger.error(f"❌ Error debugging delivery guy {onboarding_id}: {str(e)}")
        return {
            "error": str(e),
            "delivery_guy": None,
            "orders": [],
            "order_items": []
        }
