#!/usr/bin/env python3
"""
API routes for managing individual order items (products) within orders.
Handles individual product cancellation, refund, and exchange operations.
"""

from flask import Blueprint, request, jsonify
from functools import wraps
from services.order_item_service import (
    get_order_item_by_id,
    get_order_items_by_order_id,
    cancel_individual_product,
    request_refund_for_product,
    admin_process_refund,
    get_product_status_summary,
    assign_delivery_guy_to_order_item,
    get_available_delivery_guys
)
import jwt
from config import Config
from utils.crypto import encrypt_payload
from models.order import Order

order_items_bp = Blueprint("order_items", __name__)


def require_customer_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid authorization header"}), 401

        token = auth_header.split(" ")[1]
        try:
            # Decode token to get customer ID
            payload = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
            customer_id = payload.get("id")
            if not customer_id:
                return jsonify({"error": "Invalid token"}), 401
            
            request.customer_id = customer_id
            return f(*args, **kwargs)
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        except Exception as e:
            return jsonify({"error": "Authentication failed"}), 401

    return decorated


from utils.auth import require_admin_auth


@order_items_bp.route("/items/<int:item_id>", methods=["GET"])
@require_customer_auth
def get_order_item_details(item_id: int):
    """Get details of a specific order item"""
    try:
        customer_id = request.customer_id
        
        # Get the order item
        item = get_order_item_by_id(item_id)
        if not item:
            return jsonify({"error": "Order item not found"}), 404
        
        # Verify customer owns this order
        order = Order.query.get(item.order_id)
        if not order or order.customer_id != customer_id:
            return jsonify({"error": "Unauthorized access to order item"}), 403
        
        # Return item details
        return jsonify({
            "success": True,
            "item": item.as_dict()
        }), 200
        
    except Exception as e:
        print(f"Error getting order item details: {e}")
        return jsonify({"error": "Internal server error"}), 500


@order_items_bp.route("/orders/<int:order_id>/items", methods=["GET"])
@require_customer_auth
def get_order_items(order_id: int):
    """Get all items for a specific order with detailed status"""
    try:
        customer_id = request.customer_id
        
        # Verify customer owns this order
        order = Order.query.get(order_id)
        if not order or order.customer_id != customer_id:
            return jsonify({"error": "Unauthorized access to order"}), 403
        
        # Get product status summary
        summary = get_product_status_summary(order_id)
        if not summary["success"]:
            return jsonify({"error": summary["message"]}), 400
        
        # Encrypt the response
        encrypted_data = encrypt_payload(summary)
        
        return jsonify({
            "success": True,
            "encrypted_data": encrypted_data
        }), 200
        
    except Exception as e:
        print(f"Error getting order items: {e}")
        return jsonify({"error": "Internal server error"}), 500


@order_items_bp.route("/items/<int:item_id>/cancel", methods=["POST"])
@require_customer_auth
def cancel_product(item_id: int):
    """Cancel an individual product in an order"""
    try:
        customer_id = request.customer_id
        
        # Get request data
        data = request.get_json() or {}
        reason = data.get("reason", "Cancelled by customer")
        quantity = data.get("quantity")
        pickup_type = data.get("pickup_type", "return")  # 'return' or 'express'
        return_pickup_time = data.get("return_pickup_time")  # Optional pickup time
        pickup_time_from = data.get("pickup_time_from")  # From datetime for express
        pickup_time_to = data.get("pickup_time_to")  # To datetime for express
        payment_id = data.get("payment_id")  # Payment ID for express pickup
        payment_method = data.get("payment_method")  # Payment method for express pickup
        
        # Validate quantity
        if quantity is None:
            return jsonify({"error": "Quantity is required"}), 400
        
        if not isinstance(quantity, int) or quantity <= 0:
            return jsonify({"error": "Quantity must be a positive integer"}), 400
        
        print(f"Quantity to cancel: {quantity}")
        print(f"Return pickup time: {return_pickup_time}")
        
        # Cancel the product
        result = cancel_individual_product(
            item_id=item_id,
            customer_id=customer_id,
            reason=reason,
            quantity=quantity,
            cancelled_by="customer",
            pickup_type=pickup_type,
            return_pickup_time=return_pickup_time,
            pickup_time_from=pickup_time_from,
            pickup_time_to=pickup_time_to,
            payment_id=payment_id,
            payment_method=payment_method
        )
        
        if result["success"]:
            # Encrypt the response
            encrypted_data = encrypt_payload(result)
            return jsonify({
                "success": True,
                "encrypted_data": encrypted_data
            }), 200
        else:
            return jsonify({"error": result["message"]}), 400
        
    except Exception as e:
        print(f"Error cancelling product: {e}")
        return jsonify({"error": "Internal server error"}), 500


@order_items_bp.route("/items/<int:item_id>/refund", methods=["POST"])
@require_customer_auth
def request_product_refund(item_id: int):
    """Request refund for a cancelled product"""
    try:
        customer_id = request.customer_id
        
        # Get request data
        data = request.get_json() or {}
        reason = data.get("reason", "Refund requested by customer")
        refund_amount = data.get("refund_amount")
        
        # Request refund
        result = request_refund_for_product(
            item_id=item_id,
            customer_id=customer_id,
            reason=reason,
            refund_amount=refund_amount
        )
        
        if result["success"]:
            # Encrypt the response
            encrypted_data = encrypt_payload(result)
            return jsonify({
                "success": True,
                "encrypted_data": encrypted_data
            }), 200
        else:
            return jsonify({"error": result["message"]}), 400
        
    except Exception as e:
        print(f"Error requesting refund: {e}")
        return jsonify({"error": "Internal server error"}), 500


@order_items_bp.route("/items/<int:item_id>/refund/process", methods=["POST"])
@require_admin_auth
def process_product_refund(current_admin, item_id: int):
    """Admin processes refund for a product"""
    try:
        admin_id = current_admin["id"]
        
        # Get request data (encrypted payload)
        data = request.get_json() or {}
        payload = data.get("payload")
        
        if not payload:
            return jsonify({"error": "Missing encrypted payload"}), 400
        
        # Decrypt the payload
        try:
            from utils.crypto import decrypt_payload
            decrypted_data = decrypt_payload(payload)
        except Exception as e:
            print(f"Error decrypting payload: {e}")
            return jsonify({"error": "Invalid encrypted payload"}), 401
        
        refund_status = decrypted_data.get("refund_status")
        admin_notes = decrypted_data.get("admin_notes", "")
        refund_amount = decrypted_data.get("refund_amount")
        
        if not refund_status:
            return jsonify({"error": "Refund status is required"}), 402
        
       
        # Process refund
        print(f"[ROUTE DEBUG] Calling admin_process_refund with item_id={item_id}, admin_id={admin_id}, refund_status={refund_status}")
        
        result = admin_process_refund(
            item_id=item_id,
            admin_id=admin_id,
            refund_status=refund_status,
            admin_notes=admin_notes,
            refund_amount=refund_amount
        )
        
        print(f"[ROUTE DEBUG] admin_process_refund returned: {result}")
        
        if result["success"]:
            print(f"[ROUTE DEBUG] ✅ Refund successful, encrypting response")
            try:
                # Encrypt the response
                encrypted_data = encrypt_payload(result)
                print(f"[ROUTE DEBUG] ✅ Response encrypted successfully")
                return jsonify({
                    "success": True,
                    "encrypted_data": encrypted_data
                }), 200
            except Exception as e:
                print(f"[ROUTE DEBUG] ❌ Encryption failed: {e}")
                return jsonify({"error": "Failed to encrypt response"}), 500
        else:
            print(f"[ROUTE DEBUG] ❌ Refund failed: {result['message']}")
            return jsonify({"error": result["message"]}), 406
        
    except Exception as e:
        print(f"Error processing refund: {e}")
        return jsonify({"error": "Internal server error"}), 500


@order_items_bp.route("/orders/<int:order_id>/status-summary", methods=["GET"])
@require_customer_auth
def get_order_status_summary(order_id: int):
    """Get comprehensive status summary for an order including all products"""
    try:
        customer_id = request.customer_id
        
        # Verify customer owns this order
        order = Order.query.get(order_id)
        if not order or order.customer_id != customer_id:
            return jsonify({"error": "Unauthorized access to order"}), 403
        
        # Get product status summary
        summary = get_product_status_summary(order_id)
        print(f"Summary: {summary}")
        if not summary["success"]:
            return jsonify({"error": summary["message"]}), 400
        
        # Add order-level information
        summary["order"] = {
            "id": order.id,
            "order_number": order.order_number,
            "status": order.status,
            "payment_status": order.payment_status,
            "total_amount": order.total_amount,
            "subtotal": order.subtotal,
            "delivery_fee": order.delivery_fee_amount,
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "estimated_delivery": order.estimated_delivery.isoformat() if order.estimated_delivery else None
        }
        
        # Encrypt the response
        encrypted_data = encrypt_payload(summary)
        
        return jsonify({
            "success": True,
            "encrypted_data": encrypted_data
        }), 200
        
    except Exception as e:
        print(f"Error getting order status summary: {e}")
        return jsonify({"error": "Internal server error"}), 500


@order_items_bp.route("/orders/<int:order_id>/status-summary/admin", methods=["GET"])
@require_admin_auth
def get_order_status_summary_admin(current_admin, order_id: int):
    """Admin gets comprehensive status summary for any order"""
    try:
        admin_id = current_admin["id"]
        
        # Get product status summary
        summary = get_product_status_summary(order_id)
        if not summary["success"]:
            return jsonify({"error": summary["message"]}), 400
        
        # Get order details
        order = Order.query.get(order_id)
        if order:
            summary["order"] = {
                "id": order.id,
                "order_number": order.order_number,
                "customer_id": order.customer_id,
                "status": order.status,
                "payment_status": order.payment_status,
                "total_amount": order.total_amount,
                "subtotal": order.subtotal,
                "delivery_fee": order.delivery_fee_amount,
                "delivery_address": order.delivery_address,
                "delivery_type": order.delivery_type,
                "payment_method": order.payment_method,
                "created_at": order.created_at.isoformat() if order.created_at else None,
                "estimated_delivery": order.estimated_delivery.isoformat() if order.estimated_delivery else None,
                "delivery_guy_id": order.delivery_guy_id,
                "assigned_at": order.assigned_at.isoformat() if order.assigned_at else None
            }
        
        # Encrypt the response
        encrypted_data = encrypt_payload(summary)
        
        return jsonify({
            "success": True,
            "encrypted_data": encrypted_data
        }), 200
        
    except Exception as e:
        print(f"Error getting order status summary (admin): {e}")
        return jsonify({"error": "Internal server error"}), 500


@order_items_bp.route("/cancelled-products/admin", methods=["GET"])
@require_admin_auth
def get_cancelled_products_admin(current_admin):
    """Admin gets all individually cancelled products across all orders"""
    try:
        admin_id = current_admin["id"]
        
        from models.order import OrderItem
        from sqlalchemy import or_, desc, asc
        
        # Get query parameters for filtering and sorting
        status_filter = request.args.get('status')  # Filter by product status
        order_status_filter = request.args.get('order_status')  # Filter by order status
        sort_by = request.args.get('sort_by', 'updated_at')  # Sort field
        sort_order = request.args.get('sort_order', 'desc')  # Sort direction
        limit = request.args.get('limit', type=int)  # Limit results
        offset = request.args.get('offset', 0, type=int)  # Offset for pagination
        
        # Build the base query
        query = OrderItem.query.filter(OrderItem.quantity_cancel > 0)
        
        # Apply status filter if provided
        if status_filter:
            query = query.filter(OrderItem.status == status_filter)
        
        # Apply order status filter if provided
        if order_status_filter:
            query = query.join(Order).filter(Order.status == order_status_filter)
        
        # Apply sorting
        if sort_by == 'quantity_cancel':
            sort_column = OrderItem.quantity_cancel
        elif sort_by == 'created_at':
            sort_column = OrderItem.created_at
        elif sort_by == 'updated_at':
            sort_column = OrderItem.updated_at
        elif sort_by == 'product_name':
            sort_column = OrderItem.product_name
        else:
            sort_column = OrderItem.updated_at
        
        if sort_order == 'asc':
            query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(sort_column))
        
        # Apply pagination
        if limit:
            query = query.limit(limit).offset(offset)
        
        cancelled_products = query.all()
        
        products_data = []
        for product in cancelled_products:
            # Get order information
            order = Order.query.get(product.order_id)
            if order:
                # Get customer information
                from models.customer import Customer
                customer = None
                try:
                    customer = Customer.query.get(order.customer_id)
                except Exception as e:
                    print(f"Error fetching customer {order.customer_id}: {e}")
                    customer = None
                
                product_data = {
                    "id": product.id,
                    "order_id": product.order_id,
                    "order_number": order.order_number,
                    "customer_id": order.customer_id,
                    "product_id": product.product_id,
                    "product_name": product.product_name,
                    "quantity": product.quantity,
                    "quantity_cancel": product.quantity_cancel,
                    "quantity_remaining": product.quantity - product.quantity_cancel,
                    "unit_price": float(product.unit_price),
                    "total_price": float(product.total_price),
                    "cancelled_amount": float(product.unit_price * product.quantity_cancel),
                    "selected_size": product.selected_size,
                    "selected_color": product.selected_color,
                    "status": product.status,
                    "cancel_reason": product.cancel_reason,
                    "cancel_requested_at": product.cancel_requested_at.isoformat() if product.cancel_requested_at else None,
                    "cancelled_at": product.cancelled_at.isoformat() if product.cancelled_at else None,
                    "cancelled_by": product.cancelled_by,
                    "return_pickup_time": product.return_pickup_time.isoformat() if product.return_pickup_time else None,
                    "refund_status": product.refund_status,
                    "refund_amount": float(product.refund_amount) if product.refund_amount else None,
                    "refund_reason": product.refund_reason,
                    "refund_requested_at": product.refund_requested_at.isoformat() if product.refund_requested_at else None,
                    "refunded_at": product.refunded_at.isoformat() if product.refunded_at else None,
                    "exchange_status": product.exchange_status,
                    "exchange_id": product.exchange_id,
                    "created_at": product.created_at.isoformat() if product.created_at else None,
                    "updated_at": product.updated_at.isoformat() if product.updated_at else None,
                    # Customer information
                    "customer_name": customer.name if customer else None,
                    "customer_email": customer.email if customer else None,
                    "customer_phone": customer.get_phone_number() if customer else None,
                    # Order information
                    "order_status": order.status,
                    "order_total": float(order.total_amount) if order.total_amount else None,
                    "order_created_at": order.created_at.isoformat() if order.created_at else None,
                    "order_updated_at": order.updated_at.isoformat() if order.updated_at else None,
                    "return_pickup_time": product.return_pickup_time.isoformat() if product.return_pickup_time else None,
                    "return_pickup_time_from": product.return_pickup_time_from.isoformat() if product.return_pickup_time_from else None,
                    "return_pickup_time_to": product.return_pickup_time_to.isoformat() if product.return_pickup_time_to else None,
                    "return_delivery_status": product.return_delivery_status,
                    "payment_return_delivery": product.payment_return_delivery,
                    "payment_return_delivery_id": product.payment_return_delivery_id,
                    "payment_return_delivery_method": product.payment_return_delivery_method,
                }
                products_data.append(product_data)
        
        # Get total count for pagination (without limit/offset)
        total_count = OrderItem.query.filter(OrderItem.quantity_cancel > 0).count()
        
        # Encrypt the response
        encrypted_data = encrypt_payload({
            "products": products_data,
            "total_count": total_count,
            "returned_count": len(products_data),
            "pagination": {
                "limit": limit,
                "offset": offset,
                "has_more": (offset + len(products_data)) < total_count if limit else False
            },
            "filters_applied": {
                "status": status_filter,
                "order_status": order_status_filter,
                "sort_by": sort_by,
                "sort_order": sort_order
            }
        })
        
        return jsonify({
            "success": True,
            "encrypted_data": encrypted_data
        }), 200
        
    except Exception as e:
        print(f"Error getting cancelled products (admin): {e}")
        return jsonify({"error": "Internal server error"}), 500


@order_items_bp.route("/items/<int:item_id>/assign-delivery", methods=["POST"])
@require_admin_auth
def assign_delivery_to_order_item(current_admin, item_id: int):
    """Admin assigns delivery guy to individual order item"""
    try:
        admin_id = current_admin["id"]
        
        # Get request data (encrypted payload)
        data = request.get_json() or {}
        payload = data.get("payload")
        
        if not payload:
            return jsonify({"error": "Missing encrypted payload"}), 400
        
        # Decrypt the payload
        try:
            from utils.crypto import decrypt_payload
            decrypted_data = decrypt_payload(payload)
        except Exception as e:
            print(f"Error decrypting payload: {e}")
            return jsonify({"error": "Invalid encrypted payload"}), 401
        
        delivery_guy_id = decrypted_data.get("delivery_guy_id")
        notes = decrypted_data.get("notes", "")
        
        if not delivery_guy_id:
            return jsonify({"error": "Delivery guy ID is required"}), 400
        
        # Assign delivery guy to order item
        result = assign_delivery_guy_to_order_item(
            item_id=item_id,
            delivery_guy_id=delivery_guy_id,
            admin_id=admin_id,
            notes=notes
        )
        
        if result["success"]:
            # Encrypt the response
            encrypted_data = encrypt_payload(result)
            return jsonify({
                "success": True,
                "encrypted_data": encrypted_data
            }), 200
        else:
            return jsonify({"error": result["message"]}), 400
        
    except Exception as e:
        print(f"Error assigning delivery to order item: {e}")
        return jsonify({"error": "Internal server error"}), 500


@order_items_bp.route("/delivery-guys/available", methods=["GET"])
@require_admin_auth
def get_available_delivery_guys_for_items(current_admin):
    """Get available delivery guys for order item assignment"""
    try:
        admin_id = current_admin["id"]
        
        # Get available delivery guys
        result = get_available_delivery_guys()
        
        if result["success"]:
            # Encrypt the response
            encrypted_data = encrypt_payload(result)
            return jsonify({
                "success": True,
                "encrypted_data": encrypted_data
            }), 200
        else:
            return jsonify({"error": result["message"]}), 400
        
    except Exception as e:
        print(f"Error getting available delivery guys: {e}")
        return jsonify({"error": "Internal server error"}), 500


@order_items_bp.route("/sales", methods=["GET"])
def get_sales_data():
    """
    Get sales data for dashboard tiles
    Query parameters:
    - cancelled_by: Filter by cancellation status (null for non-cancelled)
    - include_price: Include price calculations
    - start_date: Start date for filtering (YYYY-MM-DD)
    - end_date: End date for filtering (YYYY-MM-DD)
    """
    try:
        from models.order import OrderItem
        from sqlalchemy import func, and_
        from datetime import datetime
        
        # Get query parameters
        cancelled_by = request.args.get('cancelled_by')
        include_price = request.args.get('include_price', 'false').lower() == 'true'
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Build base query
        query = OrderItem.query
        
        # Filter by cancellation status
        if cancelled_by == 'null' or cancelled_by is None:
            query = query.filter(OrderItem.cancelled_by.is_(None))
        elif cancelled_by:
            query = query.filter(OrderItem.cancelled_by == cancelled_by)
        
        # Filter by date range
        if start_date:
            try:
                start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(OrderItem.created_at >= start_datetime)
            except ValueError:
                return jsonify({"error": "Invalid start_date format. Use YYYY-MM-DD"}), 400
        
        if end_date:
            try:
                end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
                # Add 23:59:59 to include the entire day
                end_datetime = end_datetime.replace(hour=23, minute=59, second=59)
                query = query.filter(OrderItem.created_at <= end_datetime)
            except ValueError:
                return jsonify({"error": "Invalid end_date format. Use YYYY-MM-DD"}), 400
        
        # Calculate total sales
        if include_price:
            # Sum of total_price for all matching order items
            total_sales = query.with_entities(func.sum(OrderItem.total_price)).scalar() or 0
        else:
            # Count of order items
            total_sales = query.count()
        
        # Get additional statistics
        total_items = query.count()
        
        # Get breakdown by status
        status_breakdown = query.with_entities(
            OrderItem.status,
            func.count(OrderItem.id).label('count'),
            func.sum(OrderItem.total_price).label('total_value')
        ).group_by(OrderItem.status).all()
        
        # Get recent orders (last 10)
        recent_orders = query.order_by(OrderItem.created_at.desc()).limit(10).all()
        
        return jsonify({
            "success": True,
            "total_sales": float(total_sales) if include_price else total_sales,
            "total_items": total_items,
            "status_breakdown": [
                {
                    "status": item.status,
                    "count": item.count,
                    "total_value": float(item.total_value) if item.total_value else 0
                }
                for item in status_breakdown
            ],
            "recent_orders": [
                {
                    "id": item.id,
                    "product_name": item.product_name,
                    "quantity": item.quantity,
                    "unit_price": float(item.unit_price),
                    "total_price": float(item.total_price),
                    "status": item.status,
                    "created_at": item.created_at.isoformat() if item.created_at else None
                }
                for item in recent_orders
            ],
            "filters_applied": {
                "cancelled_by": cancelled_by,
                "include_price": include_price,
                "start_date": start_date,
                "end_date": end_date
            }
        })
        
    except Exception as e:
        print(f"Error getting sales data: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500
