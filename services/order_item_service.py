#!/usr/bin/env python3
"""
Service for managing individual order items (products) within orders.
Handles individual product cancellation, refund, and exchange operations.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from extensions import db
from models.order import Order, OrderItem, OrderHistory
from models.exchange import Exchange
from models.delivery_onboarding import DeliveryOnboarding


def get_order_item_by_id(item_id: int) -> Optional[OrderItem]:
    """Get order item by ID"""
    return OrderItem.query.get(item_id)


def get_order_items_by_order_id(order_id: int) -> List[OrderItem]:
    """Get all items for a specific order"""
    return OrderItem.query.filter_by(order_id=order_id).all()


def cancel_individual_product(
    item_id: int, 
    customer_id: int, 
    reason: str,
    quantity: int,
    cancelled_by: str = "customer",
    pickup_type: str = "return",
    return_pickup_time: str = None,
    pickup_time_from: str = None,
    pickup_time_to: str = None,
    payment_id: str = None,
    payment_method: str = None
) -> Dict[str, Any]:
    """
    Cancel an individual product in an order
    
    Args:
        item_id: OrderItem ID to cancel
        customer_id: Customer ID for verification
        reason: Reason for cancellation
        quantity: Quantity to cancel
        cancelled_by: Who initiated the cancellation (customer, admin, system)
        pickup_type: Type of pickup ('return' or 'express')
        return_pickup_time: Scheduled pickup time for cancelled items (ISO format string)
        pickup_time_from: From datetime for express pickup (ISO format string)
        pickup_time_to: To datetime for express pickup (ISO format string)
        payment_id: Payment ID for express pickup
        payment_method: Payment method for express pickup
    
    Returns:
        Dict with success status and message
    """
    try:
        # Get the order item
        item = OrderItem.query.get(item_id)
        if not item:
            return {"success": False, "message": "Order item not found"}
        
        # Verify customer owns this order
        order = Order.query.get(item.order_id)
        if not order or order.customer_id != customer_id:
            return {"success": False, "message": "Unauthorized access to order item"}
        
        # Check if item can be cancelled (allow partial cancellation)
        if item.status in ["delivered", "returned"]:
            return {"success": False, "message": f"Item cannot be cancelled in current status: {item.status}"}
        
        # Check if item is fully cancelled
        if item.status == "cancelled" and (item.quantity_cancel or 0) >= item.quantity:
            return {"success": False, "message": "Item is already fully cancelled"}
        
        # Validate quantity to cancel
        if quantity <= 0:
            return {"success": False, "message": "Cancellation quantity must be greater than 0"}
        
        # Check if quantity to cancel doesn't exceed available quantity
        available_quantity = item.quantity - (item.quantity_cancel or 0)
        if quantity > available_quantity:
            return {"success": False, "message": f"Cannot cancel {quantity} items. Only {available_quantity} items available for cancellation"}
        
        print(f"Quantity to cancel: {quantity}, Available: {available_quantity}")
        
        # Update item status and quantities
        old_quantity_cancel = item.quantity_cancel or 0
        item.quantity_cancel = old_quantity_cancel + quantity
        item.cancel_reason = reason
        item.status = "cancelled"
        item.cancel_requested_at = datetime.utcnow()
        item.cancelled_at = datetime.utcnow()
        item.cancelled_by = cancelled_by
        item.updated_at = datetime.utcnow()
        
        # Set return pickup time if provided
        if return_pickup_time:
            try:
                # Parse the ISO format string to datetime object
                pickup_datetime = datetime.fromisoformat(return_pickup_time.replace('Z', '+00:00'))
                item.return_pickup_time = pickup_datetime
                print(f"Return pickup time set to: {pickup_datetime}")
            except Exception as e:
                print(f"Error parsing return pickup time: {e}")
                # Continue without pickup time if parsing fails
        
        # Handle pickup time range for return pickup only
        if pickup_type == 'return' and pickup_time_from and pickup_time_to:
            try:
                from_datetime = datetime.fromisoformat(pickup_time_from.replace('Z', '+00:00'))
                to_datetime = datetime.fromisoformat(pickup_time_to.replace('Z', '+00:00'))
                item.return_pickup_time_from = from_datetime
                item.return_pickup_time_to = to_datetime
                # Also update the original return_pickup_time column with the from time
                item.return_pickup_time = from_datetime
                print(f"Return pickup time range set: {from_datetime} to {to_datetime}")
                print(f"Return pickup time (from) set to: {from_datetime}")
            except Exception as e:
                print(f"Error parsing pickup time range: {e}")
                # Continue without pickup time range if parsing fails
        
        # Set delivery status and payment based on pickup type
        if pickup_type == 'express':
            # For express pickup, check if payment was made
            if payment_id and payment_method:
                item.return_delivery_status = 'express_paid'  # Payment completed
                item.payment_return_delivery = 50.0  # ₹50 for express pickup
                item.payment_return_delivery_id = payment_id
                item.payment_return_delivery_method = payment_method
                print("Express pickup: Payment completed, status set to 'paid'")
            else:
                item.return_delivery_status = 'pending_payment'  # Payment pending
                item.payment_return_delivery = 50.0  # ₹50 for express pickup
                print("Express pickup: Payment pending, status set to 'pending_payment'")
            
            # For express pickup, set current time as pickup time (no range needed)
            current_time = datetime.utcnow()
            item.return_pickup_time = current_time
            item.return_pickup_time_from = current_time
            item.return_pickup_time_to = current_time
        else:
            # Regular return pickup
            item.return_delivery_status = 'scheduled'  # Also scheduled for regular return
            item.payment_return_delivery = 0.0
            print("Regular return pickup: No charge, datetime range required")
        
        print(f"Quantity cancellation: {old_quantity_cancel} + {quantity} = {item.quantity_cancel}")
        print(f"Total quantity: {item.quantity}")
        print(f"Current status: {item.status}")
        
        # If all items are cancelled, update status
        if item.quantity_cancel >= item.quantity:
            item.status = "cancelled"
            print(f"Status updated to: {item.status}")
        else:
            print(f"Partial cancellation - status remains: {item.status}")
        
        # Update order totals if needed
        _update_order_totals_after_cancellation(order, item)
        
        # Flush changes to database before commit
        db.session.flush()
        
        # Commit the transaction
        db.session.commit()
        
        # Refresh the item to get the latest data
        db.session.refresh(item)
        
        print(f"After commit - Status: {item.status}, Quantity Cancel: {item.quantity_cancel}")
        
        # Create response with detailed information
        response = {
            "success": True,
            "message": f"Product '{item.product_name}' cancelled successfully",
            "item": item.as_dict(),
            "debug_info": {
                "quantity_cancelled": quantity,
                "total_quantity": item.quantity,
                "quantity_cancel_total": item.quantity_cancel,
                "status": item.status,
                "is_fully_cancelled": item.quantity_cancel >= item.quantity,
                "return_pickup_time": item.return_pickup_time.isoformat() if item.return_pickup_time else None
            }
        }
        
        print(f"Response debug info: {response['debug_info']}")
        return response
        
    except Exception as e:
        db.session.rollback()
        print(f"Error cancelling product: {e}")
        return {"success": False, "message": "Failed to cancel product"}


def request_refund_for_product(
    item_id: int,
    customer_id: int,
    reason: str,
    refund_amount: Optional[float] = None
) -> Dict[str, Any]:
    """
    Request refund for a cancelled product
    
    Args:
        item_id: OrderItem ID to refund
        customer_id: Customer ID for verification
        reason: Reason for refund
        refund_amount: Amount to refund (defaults to item total_price)
    
    Returns:
        Dict with success status and message
    """
    try:
        # Get the order item
        item = OrderItem.query.get(item_id)
        if not item:
            return {"success": False, "message": "Order item not found"}
        
        # Verify customer owns this order
        order = Order.query.get(item.order_id)
        if not order or order.customer_id != customer_id:
            return {"success": False, "message": "Unauthorized access to order item"}
        
        # Check if item can be refunded
        if item.status != "cancelled":
            return {"success": False, "message": "Only cancelled items can be refunded"}
        
        if item.refund_status in ["requested", "initiated", "completed"]:
            return {"success": False, "message": "Refund already in progress or completed"}
        
        # Set refund amount
        if refund_amount is None:
            refund_amount = item.total_price
        
        # Update refund status
        item.refund_status = "requested"
        item.refund_reason = reason
        item.refund_amount = refund_amount
        item.refund_requested_at = datetime.utcnow()
        item.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return {
            "success": True,
            "message": f"Refund requested for '{item.product_name}' successfully",
            "item": item.as_dict()
        }
        
    except Exception as e:
        db.session.rollback()
        print(f"Error requesting refund: {e}")
        return {"success": False, "message": "Failed to request refund"}


def admin_process_refund(
    item_id: int,
    admin_id: int,
    refund_status: str,
    admin_notes: str = "",
    refund_amount: float = None
) -> Dict[str, Any]:
    print(f"[REFUND DEBUG] Processing refund for item {item_id}")
    print(f"[REFUND DEBUG] Admin ID: {admin_id}, Status: {refund_status}")
    print(f"[REFUND DEBUG] Refund amount: {refund_amount}")
    """
    Admin processes refund for a product
    
    Args:
        item_id: OrderItem ID to process refund for
        admin_id: Admin ID processing the refund
        refund_status: New refund status (initiated, completed, failed)
        admin_notes: Admin notes about the refund
        refund_amount: Amount to refund (if not provided, uses item total_price)
    
    Returns:
        Dict with success status and message
    """
    try:
        # Get the order item
        item = OrderItem.query.get(item_id)
        if not item:
            return {"success": False, "message": "Order item not found"}
        
        print(f"[REFUND DEBUG] Item {item_id} current status: {item.status}")
        print(f"[REFUND DEBUG] Item refund status: {item.refund_status}")
        
        # Check if item is cancelled
        # if item.status != "cancelled" and item.status != "refunded" and item.status != "initiated":
        #     print(f"[REFUND DEBUG] ❌ Item status '{item.status}' not allowed for refund")
        #     return {"success": False, "message": f"Only cancelled items can be refunded. Current status: {item.status}"}
        
        # print(f"[REFUND DEBUG] ✅ Item status '{item.status}' is allowed for refund")
        
        print(f"[REFUND DEBUG] ✅ Item status '{item.status}' is allowed for refund")
        
        # Set refund amount if not provided
        if refund_amount is None:
            refund_amount = float(item.total_price)
        
        print(f"[REFUND DEBUG] Final refund amount: {refund_amount}")
        print(f"[REFUND DEBUG] Item total price: {item.total_price}")
        
        # Get order information early (needed for all refund statuses)
        order = Order.query.get(item.order_id)
        if not order:
            return {"success": False, "message": "Order not found"}
        
        # Update refund status
        item.refund_status = refund_status
        item.status = refund_status
        item.refund_amount = refund_amount
        item.updated_at = datetime.utcnow()
        
        if refund_status == "completed":
            item.refunded_at = datetime.utcnow()
            
            # Add size back to product stock using new colors column structure
            if item.selected_size and item.selected_color:
                # Use quantity_cancel (the amount actually cancelled) instead of total quantity
                quantity_to_restore = item.quantity_cancel or 0
                print(f"[REFUND DEBUG] Adding {quantity_to_restore} back to {item.selected_color} {item.selected_size} for product {item.product_id}")
                from models.product import Product
                import json
                product = Product.query.get(item.product_id)
                if product and hasattr(product, 'colors'):
                    try:
                        # Parse colors JSON if present
                        if product.colors and isinstance(product.colors, str):
                            colors_data = json.loads(product.colors)
                        else:
                            colors_data = product.get_colors_data()
                        
                        # Find the selected color and add back to its size count
                        color_found = False
                        for color_data in colors_data:
                            if color_data.get('name') == item.selected_color:
                                color_found = True
                                if item.selected_size in color_data.get('sizeCounts', {}):
                                    current_count = color_data['sizeCounts'][item.selected_size]
                                    color_data['sizeCounts'][item.selected_size] = current_count + quantity_to_restore
                                    print(f"[REFUND DEBUG] Updated {item.selected_color} {item.selected_size} count: {current_count} -> {color_data['sizeCounts'][item.selected_size]} (restored {quantity_to_restore})")
                                else:
                                    print(f"[REFUND DEBUG] Warning: {item.selected_size} not found in {item.selected_color} sizes")
                                break
                        
                        if color_found:
                            # Update the product's colors column
                            product.colors = json.dumps(colors_data)
                            print(f"[REFUND DEBUG] Stock updated successfully - restored {quantity_to_restore} units")
                        else:
                            print(f"[REFUND DEBUG] Color {item.selected_color} not found in product colors")
                            
                    except Exception as e:
                        print(f"[REFUND DEBUG] Error updating product stock: {e}")
                else:
                    print(f"[REFUND DEBUG] Product not found or no colors field: {item.product_id}")
            else:
                print(f"[REFUND DEBUG] No selected size or color for item {item_id}")
            
            # Update order payment status if all items are refunded
            _update_order_payment_status_after_refund(item.order_id)
            
            # Update customer wallet (add refund amount back)
            if order.customer_id:
                print(f"[REFUND DEBUG] Updating wallet for customer {order.customer_id}, refund amount: {refund_amount}")
                try:
                    from models.wallet import Wallet, WalletTransaction
                    customer_wallet = Wallet.query.filter_by(customer_id=order.customer_id).first()
                    if customer_wallet:
                        print(f"[REFUND DEBUG] Existing wallet found, current balance: {customer_wallet.balance}")
                        customer_wallet.balance += refund_amount
                        customer_wallet.updated_at = datetime.utcnow()
                        print(f"[REFUND DEBUG] New wallet balance: {customer_wallet.balance}")
                    else:
                        # Create wallet if doesn't exist
                        print(f"[REFUND DEBUG] Creating new wallet for customer {order.customer_id}")
                        customer_wallet = Wallet(
                            customer_id=order.customer_id,
                            balance=refund_amount,
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow()
                        )
                        db.session.add(customer_wallet)
                    
                    # Add wallet transaction record
                    wallet_transaction = WalletTransaction(
                        wallet_id=customer_wallet.id,
                        transaction_type='refund',
                        amount=refund_amount,
                        description=f'Refund for cancelled product: {item.product_name}',
                        reference_id=f'OrderItem_{item.id}',
                        created_at=datetime.utcnow()
                    )
                    db.session.add(wallet_transaction)
                    print(f"[REFUND DEBUG] Wallet transaction record added")
                    
                except Exception as e:
                    print(f"[REFUND DEBUG] Error updating customer wallet: {e}")
            else:
                print(f"[REFUND DEBUG] Order not found or no customer ID")
        
        # Add admin notes to delivery notes
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        admin_note = f"\n[REFUND {refund_status.upper()}] {timestamp} - Admin {admin_id}: {admin_notes}"
        order.delivery_notes = (order.delivery_notes or "") + admin_note
        
        db.session.commit()
        
        print(f"[REFUND DEBUG] ✅ Database committed successfully")
        print(f"[REFUND DEBUG] ✅ Returning success response")
        
        return {
            "success": True,
            "message": f"Refund {refund_status} for '{item.product_name}'",
            "item": item.as_dict()
        }
        
    except Exception as e:
        db.session.rollback()
        print(f"Error processing refund: {e}")
        return {"success": False, "message": "Failed to process refund"}


def get_product_status_summary(order_id: int) -> Dict[str, Any]:
    """
    Get summary of all product statuses in an order
    
    Args:
        order_id: Order ID to get summary for
    
    Returns:
        Dict with status counts and details
    """
    try:
        items = OrderItem.query.filter_by(order_id=order_id).all()
        
        if not items:
            return {"success": False, "message": "No items found for order"}
        
        # Count statuses
        status_counts = {}
        refund_counts = {}
        exchange_counts = {}
        
        for item in items:
            # Product status counts
            status_counts[item.status] = status_counts.get(item.status, 0) + 1
            print(f"Statusssssss: {item.status}")
            # Refund status counts
            if item.refund_status != "not_applicable":
                refund_counts[item.refund_status] = refund_counts.get(item.refund_status, 0) + 1
            
            # Exchange status counts
            if item.exchange_status != "not_applicable":
                exchange_counts[item.exchange_status] = exchange_counts.get(item.exchange_status, 0) + 1
        
        # Determine overall order status
        overall_status = _determine_overall_order_status(items)
        print(f"Overall status: {overall_status}")
        return {
            "success": True,
            "order_id": order_id,
            "total_items": len(items),
            "overall_status": overall_status,
            "status_counts": status_counts,
            "refund_counts": refund_counts,
            "exchange_counts": exchange_counts,
            "items": [item.as_dict() for item in items]
        }
        
    except Exception as e:
        print(f"Error getting product status summary: {e}")
        return {"success": False, "message": "Failed to get product status summary"}


def _update_order_totals_after_cancellation(order: Order, cancelled_item: OrderItem):
    """Update order totals after cancelling an item"""
    try:
        # Recalculate order totals based on active quantities
        items = OrderItem.query.filter_by(order_id=order.id).all()
        
        new_subtotal = 0
        for item in items:
            # Calculate active quantity (total - cancelled)
            active_quantity = item.quantity - (item.quantity_cancel or 0)
            if active_quantity > 0:
                # Calculate price per unit
                unit_price = item.total_price / item.quantity if item.quantity > 0 else 0
                new_subtotal += unit_price * active_quantity
        
        new_total = new_subtotal + order.delivery_fee_amount + order.platform_fee - order.discount_amount
        
        order.subtotal = new_subtotal
        order.total_amount = new_total
        order.updated_at = datetime.utcnow()
        
        print(f"Updated order totals - Subtotal: {new_subtotal}, Total: {new_total}")
        
    except Exception as e:
        print(f"Error updating order totals: {e}")


def _update_order_payment_status_after_refund(order_id: int):
    """Update order payment status after refunds"""
    try:
        order = Order.query.get(order_id)
        if not order:
            return
        
        # Check if all items are refunded
        items = OrderItem.query.filter_by(order_id=order_id).all()
        cancelled_items = [item for item in items if item.status == "cancelled"]
        refunded_items = [item for item in cancelled_items if item.refund_status == "completed"]
        
        if len(refunded_items) == len(cancelled_items) and len(cancelled_items) > 0:
            order.payment_status = "refunded"
            order.updated_at = datetime.utcnow()
            
    except Exception as e:
        print(f"Error updating order payment status: {e}")


def _determine_overall_order_status(items: List[OrderItem]) -> str:
    """Determine overall order status based on individual item statuses"""
    if not items:
        return "unknown"
    
    # Count statuses
    status_counts = {}
    for item in items:
        status_counts[item.status] = status_counts.get(item.status, 0) + 1
    
    total_items = len(items)
    
    # If all items are delivered
    if status_counts.get("delivered", 0) == total_items:
        return "delivered"
    
    # If all items are cancelled
    if status_counts.get("cancelled", 0) == total_items:
        return "cancelled"
    
    # If some items are delivered and some cancelled
    if status_counts.get("delivered", 0) > 0 and status_counts.get("cancelled", 0) > 0:
        return "partially_delivered"
    
    # If any item is out for delivery
    if status_counts.get("out_for_delivery", 0) > 0:
        return "out_for_delivery"
    
    # If any item is shipped
    if status_counts.get("shipped", 0) > 0:
        return "shipped"
    
    # If any item is processing
    if status_counts.get("processing", 0) > 0:
        return "processing"
    
    # If any item is confirmed
    if status_counts.get("confirmed", 0) > 0:
        return "confirmed"
    
    if status_counts.get("initiated", 0) > 0:
        return "initiated"
    
    # Default to pending
    return "pending"


def assign_delivery_guy_to_order_item(
    item_id: int,
    delivery_guy_id: int,
    admin_id: int,
    notes: str = ""
) -> Dict[str, Any]:
    """
    Assign delivery guy to individual order item
    
    Args:
        item_id: OrderItem ID to assign delivery to
        delivery_guy_id: Delivery guy ID to assign
        admin_id: Admin ID making the assignment
        notes: Assignment notes
    
    Returns:
        Dict with success status and message
    """
    try:
        # Get the order item
        item = OrderItem.query.get(item_id)
        if not item:
            return {"success": False, "message": "Order item not found"}
        
        # Verify delivery guy exists
        delivery_guy = DeliveryOnboarding.query.get(delivery_guy_id)
        if not delivery_guy:
            return {"success": False, "message": "Delivery guy not found"}
        
        # Check if delivery guy is approved
        if delivery_guy.status != "approved":
            return {"success": False, "message": "Delivery guy is not approved"}
        
        # Get order information
        order = Order.query.get(item.order_id)
        if not order:
            return {"success": False, "message": "Order not found"}
        
        # Assign delivery guy to the main order (if not already assigned)
        if not order.delivery_guy_id:
            order.delivery_guy_id = delivery_guy_id
            order.assigned_at = datetime.utcnow()
        
        # Assign delivery guy to order item
        item.delivery_guy_id = delivery_guy_id
        item.status = "assigned"
        item.refund_status = "assigned"
        item.updated_at = datetime.utcnow()
        
        # Create order history entry
        history_entry = OrderHistory(
            order_id=order.id,
            delivery_guy_id=delivery_guy_id,
            status="item_assigned",
            notes=f"Individual product '{item.product_name}' assigned to delivery guy. {notes}",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.session.add(history_entry)
        
        # Update order delivery notes
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        delivery_guy_name = f"{delivery_guy.first_name} {delivery_guy.last_name}".strip()
        assignment_note = f"\n[ITEM ASSIGNED] {timestamp} - Admin {admin_id}: Product '{item.product_name}' assigned to {delivery_guy_name}. {notes}"
        order.delivery_notes = (order.delivery_notes or "") + assignment_note
        
        db.session.commit()
        
        delivery_guy_name = f"{delivery_guy.first_name} {delivery_guy.last_name}".strip()
        return {
            "success": True,
            "message": f"Product '{item.product_name}' assigned to {delivery_guy_name} successfully",
            "item": item.as_dict(),
            "delivery_guy": {
                "id": delivery_guy.id,
                "name": delivery_guy_name,
                "phone_number": delivery_guy.primary_number
            }
        }
        
    except Exception as e:
        db.session.rollback()
        print(f"Error assigning delivery to order item: {e}")
        return {"success": False, "message": "Failed to assign delivery to order item"}


def get_available_delivery_guys() -> Dict[str, Any]:
    """
    Get list of available delivery guys for assignment
    
    Returns:
        Dict with success status and delivery guys list
    """
    try:
        # Get approved delivery guys
        delivery_guys = DeliveryOnboarding.query.filter_by(status="approved").all()
        
        delivery_guys_data = []
        for guy in delivery_guys:
            # Count active orders for this delivery guy
            active_orders_count = Order.query.filter_by(
                delivery_guy_id=guy.id,
                status__in=["assigned", "confirmed", "processing", "shipped", "out_for_delivery"]
            ).count()
            
            # Count assigned order items
            assigned_items_count = OrderItem.query.filter_by(delivery_guy_id=guy.id).count()
            
            delivery_guys_data.append({
                "id": guy.id,
                "name": f"{guy.first_name} {guy.last_name}".strip(),
                "phone_number": guy.primary_number,
                "email": guy.email,
                "status": guy.status,
                "vehicle_number": guy.vehicle_number,
                "active_orders_count": active_orders_count,
                "assigned_items_count": assigned_items_count,
                "rating": getattr(guy, 'rating', 0),
                "total_deliveries": getattr(guy, 'total_deliveries', 0),
                "onboarding_details": {
                    "approved_at": guy.approved_at.isoformat() if guy.approved_at else None
                }
            })
        
        return {
            "success": True,
            "delivery_guys": delivery_guys_data,
            "total_count": len(delivery_guys_data)
        }
        
    except Exception as e:
        print(f"Error getting available delivery guys: {e}")
        return {"success": False, "message": "Failed to get available delivery guys"}


def assign_delivery_guy_to_order_bulk(
    order_id: int,
    delivery_guy_id: int,
    admin_id: int,
    notes: str = ""
) -> Dict[str, Any]:
    """
    Assign delivery guy to all items in an order (bulk assignment)
    
    Args:
        order_id: Order ID to assign delivery to
        delivery_guy_id: Delivery guy ID to assign
        admin_id: Admin ID making the assignment
        notes: Assignment notes
    
    Returns:
        Dict with success status and message
    """
    try:
        # Get the order
        order = Order.query.get(order_id)
        if not order:
            return {"success": False, "message": "Order not found"}
        
        # Verify delivery guy exists
        delivery_guy = DeliveryOnboarding.query.get(delivery_guy_id)
        if not delivery_guy:
            return {"success": False, "message": "Delivery guy not found"}
        
        # Check if delivery guy is approved
        if delivery_guy.status != "approved":
            return {"success": False, "message": "Delivery guy is not approved"}
        
        # Get all order items
        order_items = OrderItem.query.filter_by(order_id=order_id).all()
        if not order_items:
            return {"success": False, "message": "No items found in order"}
        
        # Assign delivery guy to the main order
        order.delivery_guy_id = delivery_guy_id
        order.assigned_at = datetime.utcnow()
        
        # Assign delivery guy to all items
        assigned_items = []
        for item in order_items:
            item.delivery_guy_id = delivery_guy_id
            item.updated_at = datetime.utcnow()
            assigned_items.append(item.as_dict())
        
        # Create order history entry
        history_entry = OrderHistory(
            order_id=order.id,
            delivery_guy_id=delivery_guy_id,
            status="bulk_assigned",
            notes=f"All products in order assigned to delivery guy. {notes}",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.session.add(history_entry)
        
        # Update order delivery notes
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        delivery_guy_name = f"{delivery_guy.first_name} {delivery_guy.last_name}".strip()
        assignment_note = f"\n[BULK ASSIGNED] {timestamp} - Admin {admin_id}: All products assigned to {delivery_guy_name}. {notes}"
        order.delivery_notes = (order.delivery_notes or "") + assignment_note
        
        db.session.commit()
        
        delivery_guy_name = f"{delivery_guy.first_name} {delivery_guy.last_name}".strip()
        return {
            "success": True,
            "message": f"All products in order assigned to {delivery_guy_name} successfully",
            "assigned_items": assigned_items,
            "delivery_guy": {
                "id": delivery_guy.id,
                "name": delivery_guy_name,
                "phone_number": delivery_guy.primary_number
            },
            "total_items_assigned": len(assigned_items)
        }
        
    except Exception as e:
        db.session.rollback()
        print(f"Error assigning delivery to order (bulk): {e}")
        return {"success": False, "message": "Failed to assign delivery to order"}
