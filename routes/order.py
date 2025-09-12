# routes/order.py
from flask import Blueprint, request, jsonify
from services.order_service import (
    create_order,
    get_order_by_id,
    get_customer_orders,
    update_order_status,
    cancel_order
)
from utils.auth import require_customer_auth, require_admin_auth
from utils.crypto import decrypt_payload
from extensions import db

order_bp = Blueprint("order", __name__)

@order_bp.route("/", methods=["POST"])
@require_customer_auth
def place_order(current_customer):
    """Create a new order"""
    try:
        print(f"[ORDER ROUTE] Creating new order for customer: {current_customer['id']}")
        customer_id = current_customer["id"]
        encrypted_data = request.json.get("payload") or request.json.get("data")
        if not encrypted_data:
            print(f"[ORDER ROUTE] Missing encrypted data")
            return jsonify({"error": "Missing encrypted payload or data"}), 400
        
        print(f"[ORDER ROUTE] Encrypted data received: {encrypted_data[:50]}...")
        decrypted_data = decrypt_payload(encrypted_data)
        print(f"[ORDER ROUTE] Decrypted data: {decrypted_data}")
        
        # Add customer_id to order data
        order_data = decrypted_data
        order_data["customer_id"] = customer_id
        
        # Debug coupon data specifically
        print(f"[ORDER ROUTE] Coupon data in order: coupon_id={order_data.get('coupon_id')}, coupon_code={order_data.get('coupon_code')}")
        print(f"[ORDER ROUTE] Final order data: {order_data}")
        res, status = create_order(customer_id, order_data)
        return jsonify(res), status
    except Exception as e:
        print(f"Place order route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@order_bp.route("/<int:order_id>", methods=["GET"])
@require_customer_auth
def get_order(current_customer, order_id):
    """Get order by ID"""
    try:
        customer_id = current_customer["id"]
        res, status = get_order_by_id(order_id, customer_id)
        return jsonify(res), status
    except Exception as e:
        print(f"Get order route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@order_bp.route("/customer", methods=["GET"])
@require_customer_auth
def get_my_orders(current_customer):
    """Get all orders for current customer"""
    try:
        customer_id = current_customer["id"]
        limit = request.args.get("limit", 20, type=int)
        
        res, status = get_customer_orders(customer_id, limit)
        return jsonify(res), status
    except Exception as e:
        print(f"Get customer orders route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@order_bp.route("/<int:order_id>/status", methods=["PUT"])
@require_customer_auth
def update_status(current_customer, order_id):
    """Update order status"""
    try:
        customer_id = current_customer["id"]
        encrypted_data = request.json.get("payload") or request.json.get("data")
        if not encrypted_data:
            return jsonify({"error": "Missing encrypted payload or data"}), 400
        
        decrypted_data = decrypt_payload(encrypted_data)
        status = decrypted_data.get("status")
        print(f"[ORDER ROUTE] Status: {status}")
        
        if not status:
            return jsonify({"error": "Status is required"}), 400
        
        res, status_code = update_order_status(order_id, status, customer_id)
        return jsonify(res), status_code
    except Exception as e:
        print(f"Update order status route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@order_bp.route("/<int:order_id>/cancel", methods=["POST"])
@require_customer_auth
def cancel_my_order(current_customer, order_id):
    """Cancel an order"""
    try:
        customer_id = current_customer["id"]
        res, status = cancel_order(order_id, customer_id)
        return jsonify(res), status
    except Exception as e:
        print(f"Cancel order route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@order_bp.route("/<int:order_id>/exchange", methods=["POST"])
@require_customer_auth
def create_exchange_request(current_customer, order_id):
    """Create an exchange request for an order"""
    try:
        customer_id = current_customer["id"]
        encrypted_data = request.json.get("payload") or request.json.get("data")
        
        print(f"[EXCHANGE ROUTE] Received request for order {order_id}")
        print(f"[EXCHANGE ROUTE] Encrypted data: {encrypted_data[:100] if encrypted_data else 'None'}...")
        
        if not encrypted_data:
            return jsonify({"error": "Missing encrypted payload or data"}), 400
        
        decrypted_data = decrypt_payload(encrypted_data)
        print(f"[EXCHANGE ROUTE] Decrypted data: {decrypted_data}")
        
        order_item_id = decrypted_data.get("order_item_id")
        product_id = decrypted_data.get("product_id")
        new_size = decrypted_data.get("new_size")
        new_color = decrypted_data.get("new_color")
        new_quantity = decrypted_data.get("new_quantity", 1)  # Default to 1 if not provided
        reason = decrypted_data.get("reason")
        
        print(f"[EXCHANGE ROUTE] Parsed fields: order_item_id={order_item_id}, product_id={product_id}, new_size={new_size}, new_color={new_color}, new_quantity={new_quantity}, reason={reason}")
        
        if not all([order_item_id, product_id, new_size]):
            return jsonify({"error": "Missing required fields: order_item_id, product_id, new_size"}), 400
        
        # Import exchange service
        from services.exchange_service import create_exchange
        print(f"[EXCHANGE ROUTE] Calling create_exchange service...")
        # For size exchange, both original and exchange product are the same (product_id)
        res, status = create_exchange(customer_id, order_id, product_id, product_id, reason, new_quantity, order_item_id, new_size, new_color)
        print(f"[EXCHANGE ROUTE] Service response: {res}, status: {status}")
        return jsonify(res), status
        
    except Exception as e:
        print(f"Create exchange request route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@order_bp.route("/<int:order_id>/track", methods=["GET"])
@require_customer_auth
def track_order(current_customer, order_id):
    """Track order status and delivery"""
    try:
        customer_id = current_customer["id"]
        res, status = get_order_by_id(order_id, customer_id)
        
        if status != 200:
            return jsonify(res), status
        
        # Decrypt the response to get order data
        from utils.crypto import decrypt_payload
        order_data = decrypt_payload(res["encrypted_data"])
        order = order_data["order"]
        
        # Calculate delivery progress
        delivery_progress = {
            "order_placed": True,
            "confirmed": order["status"] in ["confirmed", "processing", "shipped", "delivered"],
            "processing": order["status"] in ["processing", "shipped", "delivered"],
            "shipped": order["status"] in ["shipped", "delivered"],
            "delivered": order["status"] == "delivered"
        }
        
        # Calculate estimated time remaining
        estimated_delivery = None
        if order["estimated_delivery"]:
            from datetime import datetime
            estimated = datetime.fromisoformat(order["estimated_delivery"])
            now = datetime.utcnow()
            if estimated > now:
                time_diff = estimated - now
                if time_diff.days > 0:
                    estimated_delivery = f"{time_diff.days} days"
                elif time_diff.seconds > 3600:
                    hours = time_diff.seconds // 3600
                    estimated_delivery = f"{hours} hours"
                else:
                    minutes = time_diff.seconds // 60
                    estimated_delivery = f"{minutes} minutes"
            else:
                estimated_delivery = "Overdue"
        
        tracking_data = {
            "order_id": order["id"],
            "order_number": order["order_number"],
            "status": order["status"],
            "delivery_type": order["delivery_type"],
            "estimated_delivery": order["estimated_delivery"],
            "estimated_time_remaining": estimated_delivery,
            "delivery_progress": delivery_progress,
            "delivery_address": order["delivery_address"],
            "payment_status": order["payment_status"]
        }
        
        # Encrypt tracking data
        from utils.crypto import encrypt_payload
        encrypted_tracking = encrypt_payload({
            "success": True,
            "tracking": tracking_data,
            "message": "Order tracking information retrieved successfully"
        })
        
        return jsonify({
            "success": True,
            "encrypted_data": encrypted_tracking,
            "message": "Order tracking information retrieved successfully"
        }), 200
        
    except Exception as e:
        print(f"Track order route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@order_bp.route("/cancelled/admin", methods=["GET"])
@require_admin_auth
def get_cancelled_orders_admin():
    """Admin gets all cancelled orders"""
    try:
        from utils.auth import require_admin_auth
        from utils.crypto import encrypt_payload
        from models.order import Order
        from sqlalchemy import and_
        
        # Check admin authentication
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid authorization header"}), 401

        token = auth_header.split(" ")[1]
        try:
            from config import Config
            import jwt
            payload = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
            admin_id = payload.get("id")
            if not admin_id:
                return jsonify({"error": "Invalid admin token"}), 401
        except Exception as e:
            return jsonify({"error": "Admin authentication failed"}), 401
        
        # Get all cancelled orders
        cancelled_orders = Order.query.filter(
            and_(
                Order.status == 'cancelled',
                Order.updated_at.isnot(None)
            )
        ).all()
        
        orders_data = []
        for order in cancelled_orders:
            order_data = {
                "id": order.id,
                "order_number": order.order_number,
                "customer_id": order.customer_id,
                "status": order.status,
                "delivery_type": order.delivery_type,
                "delivery_address": order.delivery_address,
                "payment_method": order.payment_method,
                "payment_status": order.payment_status,
                "subtotal": float(order.subtotal),
                "delivery_fee_amount": float(order.delivery_fee_amount) if order.delivery_fee_amount else 0,
                "platform_fee": float(order.platform_fee) if order.platform_fee else 0,
                "discount_amount": float(order.discount_amount) if order.discount_amount else 0,
                "total_amount": float(order.total_amount),
                "created_at": order.created_at.isoformat() if order.created_at else None,
                "updated_at": order.updated_at.isoformat() if order.updated_at else None,
                "estimated_delivery": order.estimated_delivery.isoformat() if order.estimated_delivery else None,
                "delivery_notes": order.delivery_notes,
                "delivery_guy_id": order.delivery_guy_id,
                "assigned_at": order.assigned_at.isoformat() if order.assigned_at else None
            }
            orders_data.append(order_data)
        
        # Encrypt the response
        encrypted_data = encrypt_payload({
            "orders": orders_data,
            "total_count": len(orders_data)
        })
        
        return jsonify({
            "success": True,
            "encrypted_data": encrypted_data
        }), 200
        
    except Exception as e:
        print(f"Error getting cancelled orders (admin): {e}")
        return jsonify({"error": "Internal server error"}), 500

@order_bp.route("/<int:order_id>/items", methods=["GET"])
@require_admin_auth
def get_order_items(admin_user, order_id):
    """Get all items for a specific order (admin only)"""
    try:
        print(f"[ORDER ITEMS] Getting items for order: {order_id}")
        
        from models.order import Order, OrderItem
        from utils.crypto import encrypt_payload
        
        # Check if order exists
        order = Order.query.get(order_id)
        if not order:
            return jsonify({"error": "Order not found"}), 404
        
        # Get all order items
        order_items = OrderItem.query.filter_by(order_id=order_id).all()
        
        # Convert to dictionary format
        items_data = []
        for item in order_items:
            items_data.append({
                'id': item.id,
                'product_id': item.product_id,
                'product_name': item.product_name,
                'quantity': item.quantity,
                'selected_size': item.selected_size,
                'unit_price': item.unit_price,
                'total_price': item.total_price,
                'status': item.status,
                'refund_status': item.refund_status,
                'refund_amount': item.refund_amount,
                'exchange_status': item.exchange_status,
                'cancel_reason': item.cancel_reason,
                'cancel_requested_at': item.cancel_requested_at.isoformat() if item.cancel_requested_at else None,
                'cancelled_at': item.cancelled_at.isoformat() if item.cancelled_at else None,
                'cancelled_by': item.cancelled_by
            })
        
        result = {
            'order_id': order_id,
            'order_number': order.order_number,
            'customer_id': order.customer_id,
            'items': items_data
        }
        
        encrypted_result = encrypt_payload(result)
        return jsonify({'encrypted_data': encrypted_result}), 200
        
    except Exception as e:
        print(f"[ORDER ITEMS] Error getting order items: {str(e)}")
        return jsonify({"error": f"Failed to get order items: {str(e)}"}), 500

@order_bp.route("/<int:order_id>/refund/process", methods=["POST"])
@require_admin_auth
def process_order_refund(admin_user, order_id):
    """Process order-level refund for all cancelled products"""
    try:
        print(f"[ORDER REFUND] 🚀 Processing FULL ORDER REFUND for order: {order_id}")
        print(f"[ORDER REFUND] 💡 This will refund ALL items regardless of their current status")
        
        # Import all required modules first
        from models.order import Order, OrderItem
        from models.wallet import Wallet, WalletTransaction
        from models.product import Product
        from utils.crypto import encrypt_payload
        from datetime import datetime
        
        order = Order.query.get(order_id)
        if not order:
            return jsonify({"error": "Order not found"}), 404
        
        print(f"[ORDER REFUND] Found order: {order.id}, Status: {order.status}, Payment Status: {order.payment_status}")
        print(f"[ORDER REFUND] Database session active: {db.session.is_active}")
        
        # Show all order items and their statuses for debugging
        all_order_items = OrderItem.query.filter_by(order_id=order_id).all()
        print(f"[ORDER REFUND] Total order items: {len(all_order_items)}")
        for item in all_order_items:
            print(f"[ORDER REFUND] Item {item.id}: {item.product_name}, Status: {item.status}, Refund Status: {item.refund_status}, Amount: {item.total_price}")
        
        # Get ALL items that need refund (not already refunded) - FULL ORDER REFUND
        items_to_refund = OrderItem.query.filter(
            OrderItem.order_id == order_id,
            OrderItem.refund_status != 'completed'
        ).all()
        
        print(f"[ORDER REFUND] Found {len(items_to_refund)} items that need refund (FULL ORDER)")
        for item in items_to_refund:
            print(f"[ORDER REFUND] Item {item.id}: {item.product_name}, Status: {item.status}, Refund Status: {item.refund_status}, Amount: {item.total_price}")
        
        if not items_to_refund:
            # Check if all items are already refunded
            all_items = OrderItem.query.filter_by(order_id=order_id).all()
            refunded_items = [item for item in all_items if item.refund_status == 'completed']
            if refunded_items:
                return jsonify({
                    "error": "All products in this order have already been refunded",
                    "already_refunded_count": len(refunded_items),
                    "total_order_amount": sum(item.total_price for item in all_items),
                    "total_refunded_amount": sum(item.refund_amount for item in refunded_items)
                }), 400
            else:
                return jsonify({"error": "No products found for refund"}), 400
        
        total_refund_amount = 0
        processed_items = []
        
        # Process refund for each item (FULL ORDER REFUND)
        for item in items_to_refund:
            print(f"[ORDER REFUND] Processing item: {item.id}, Product: {item.product_name}, Amount: {item.total_price}")
            print(f"[ORDER REFUND] Before update - refund_status: {item.refund_status}, refund_amount: {item.refund_amount}")
            
            # Update item refund status
            item.refund_status = 'completed'
            item.refund_amount = item.total_price
            item.refunded_at = datetime.utcnow()
            print(f"[ORDER REFUND] ✅ Updated item {item.id} refund status to 'completed'")
            print(f"[ORDER REFUND] After update - refund_status: {item.refund_status}, refund_amount: {item.refund_amount}")
            
            # Add to total refund amount
            total_refund_amount += item.total_price
            print(f"[ORDER REFUND] 💰 Added ₹{item.total_price} to total refund amount. Total: ₹{total_refund_amount}")
            
            # Restore product size to stock automatically
            if item.selected_size and item.quantity:
                product = Product.query.get(item.product_id)
                if product:
                    try:
                        old_stock = getattr(product, f'size_{item.selected_size}', 0)
                        product.add_size_stock(item.selected_size, item.quantity)
                        new_stock = getattr(product, f'size_{item.selected_size}', 0)
                        print(f"[ORDER REFUND] 📦 Restored {item.quantity} items of size {item.selected_size} to product {product.pname}")
                        print(f"[ORDER REFUND] 📦 Stock changed from {old_stock} to {new_stock}")
                    except Exception as e:
                        print(f"[ORDER REFUND] ❌ Error restoring stock: {e}")
                else:
                    print(f"[ORDER REFUND] ❌ Product {item.product_id} not found for stock restoration")
            else:
                print(f"[ORDER REFUND] ⚠️ No size or quantity for item {item.id}, skipping stock restoration")
            
            processed_items.append({
                'id': item.id,
                'product_name': item.product_name,
                'amount': item.total_price,
                'size': item.selected_size,
                'quantity': item.quantity
            })
        
        # Update customer wallet automatically
        customer_wallet = Wallet.query.filter_by(customer_id=order.customer_id).first()
        if not customer_wallet:
            customer_wallet = Wallet(customer_id=order.customer_id, balance=0)
            db.session.add(customer_wallet)
            print(f"[ORDER REFUND] 💳 Created new wallet for customer {order.customer_id}")
        else:
            print(f"[ORDER REFUND] 💳 Found existing wallet for customer {order.customer_id}, current balance: ₹{customer_wallet.balance}")
        
        old_balance = customer_wallet.balance
        customer_wallet.balance += total_refund_amount
        print(f"[ORDER REFUND] 💰 Added ₹{total_refund_amount} to customer {order.customer_id} wallet")
        print(f"[ORDER REFUND] 💰 Wallet balance changed from ₹{old_balance} to ₹{customer_wallet.balance}")
        
        # Create wallet transaction record
        wallet_transaction = WalletTransaction(
            wallet_id=customer_wallet.id,
            amount=total_refund_amount,
            transaction_type='refund',
            description=f'Order #{order.order_number} refund - {len(processed_items)} products',
            reference_id=order_id
        )
        db.session.add(wallet_transaction)
        print(f"[ORDER REFUND] 📝 Created wallet transaction record: ₹{total_refund_amount} refund")
        
        # Commit all changes
        db.session.commit()
        print(f"[ORDER REFUND] ✅ All database changes committed successfully")
        
        # Verify the changes were actually saved
        print(f"[ORDER REFUND] 🔍 Verifying database changes...")
        for item in items_to_refund:
            db.session.refresh(item)
            print(f"[ORDER REFUND] Item {item.id}: refund_status = {item.refund_status}, refund_amount = {item.refund_amount}")
        
        # Update main order status and payment status
        order.status = 'refunded'
        order.payment_status = 'refunded'
        order.updated_at = datetime.utcnow()
        print(f"[ORDER REFUND] 🎯 Updated order {order_id} status to 'refunded'")
        print(f"[ORDER REFUND] 🎯 Updated order {order_id} payment status to 'refunded'")
        
        # Update delivery_notes with tracking information
        try:
            import json
            notes = json.loads(order.delivery_notes) if order.delivery_notes else {}
            flow = notes.get("cancel_flow", [])
            
            # Initialize cancel_flow if it doesn't exist
            if not flow:
                print(f"[ORDER REFUND] 📝 Initializing new cancel_flow for order {order_id}")
                flow = []
            
            # Add cancellation step if not already present (for orders that weren't previously cancelled)
            if not any(step.get("status") == "cancel_request_initiated" for step in flow):
                flow.append({"status": "cancel_request_initiated", "at": datetime.utcnow().isoformat()})
                print(f"[ORDER REFUND] 📝 Added 'cancel_request_initiated' to tracking flow")
            
            # Add refund processing steps to tracking
            if not any(step.get("status") == "refund_initiated" for step in flow):
                flow.append({"status": "refund_initiated", "at": datetime.utcnow().isoformat()})
                print(f"[ORDER REFUND] 📝 Added 'refund_initiated' to tracking flow")
            
            if not any(step.get("status") == "refunded" for step in flow):
                flow.append({"status": "refunded", "at": datetime.utcnow().isoformat()})
                print(f"[ORDER REFUND] 📝 Added 'refunded' to tracking flow")
            
            notes["cancel_flow"] = flow
            order.delivery_notes = json.dumps(notes)
            print(f"[ORDER REFUND] 📝 Updated delivery_notes with tracking data: {flow}")
        except Exception as e:
            print(f"[ORDER REFUND] ⚠️ Warning: Could not update tracking data: {e}")
        
        # Commit the order status changes
        db.session.commit()
        print(f"[ORDER REFUND] ✅ Order status changes committed successfully")
        
        print(f"[ORDER REFUND] 🎉 REFUND COMPLETED SUCCESSFULLY!")
        print(f"[ORDER REFUND] 📊 Summary: {len(processed_items)} products refunded, ₹{total_refund_amount} added to wallet")
        print(f"[ORDER REFUND] 📊 Order #{order.order_number} status updated to 'refunded'")
        
        result = {
            'message': 'Order refund processed successfully',
            'order_id': order_id,
            'total_refund_amount': total_refund_amount,
            'processed_items': processed_items,
            'customer_wallet_balance': customer_wallet.balance
        }
        
        encrypted_result = encrypt_payload(result)
        return jsonify({'encrypted_data': encrypted_result}), 200
        
    except Exception as e:
        print(f"[ORDER REFUND] ❌ Exception occurred: {str(e)}")
        print(f"[ORDER REFUND] ❌ Exception type: {type(e).__name__}")
        import traceback
        print(f"[ORDER REFUND] ❌ Traceback: {traceback.format_exc()}")
        
        try:
            db.session.rollback()
            print(f"[ORDER REFUND] ✅ Database session rolled back")
        except Exception as rollback_error:
            print(f"[ORDER REFUND] ❌ Failed to rollback: {rollback_error}")
        
        return jsonify({"error": f"Failed to process order refund: {str(e)}"}), 500

