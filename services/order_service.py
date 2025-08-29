# services/order_service.py
from models.order import Order, OrderItem
from models.product import Product
from models.customer import Customer
from extensions import db
from utils.crypto import encrypt_payload, decrypt_payload
from datetime import datetime, timedelta
import json

def create_order(customer_id: int, order_data: dict):
    """Create a new order"""
    try:
        print(f"[ORDER SERVICE] Creating order for customer: {customer_id}")
        print(f"[ORDER SERVICE] Order data received: {order_data}")
        
        # Extract order data
        items = order_data.get("items", [])
        delivery_address = order_data.get("delivery_address", {})
        delivery_type = order_data.get("delivery_type", "standard")  # Fixed: frontend sends delivery_type
        scheduled_time = order_data.get("scheduled_time")
        payment_method = order_data.get("payment_method", "cod")
        payment_id = order_data.get("payment_id")
        
        print(f"[ORDER SERVICE] Extracted data: items={len(items)}, delivery_type={delivery_type}, scheduled_time={scheduled_time}")
        
        # Calculate pricing
        subtotal = order_data.get("subtotal", 0)
        delivery_fee = order_data.get("delivery_fee", 0)
        platform_fee = order_data.get("platform_fee", 5)
        discount_amount = order_data.get("discount_amount", 0)
        total_amount = order_data.get("total", 0)
        
        print(f"[ORDER SERVICE] Pricing: subtotal={subtotal}, delivery_fee={delivery_fee}, total={total_amount}")
        
        # Create order
        order = Order(
            customer_id=customer_id,
            order_number="",  # Will be generated after commit
            status="pending",
            delivery_address=json.dumps(delivery_address),
            delivery_type=delivery_type,  # Fixed: use delivery_type
            scheduled_time=datetime.fromisoformat(scheduled_time) if scheduled_time else None,
            delivery_fee=delivery_fee,
            payment_method=payment_method,
            payment_id=payment_id,
            payment_status="pending",
            subtotal=subtotal,
            delivery_fee_amount=delivery_fee,
            platform_fee=platform_fee,
            discount_amount=discount_amount,
            total_amount=total_amount
        )
        
        # Calculate estimated delivery
        if delivery_type == "express":
            order.estimated_delivery = datetime.utcnow() + timedelta(hours=1)  # 60 minutes
        elif delivery_type == "standard":
            order.estimated_delivery = datetime.utcnow() + timedelta(days=2)
        elif delivery_type == "scheduled" and scheduled_time:
            try:
                # Try to parse scheduled_time safely
                if isinstance(scheduled_time, str):
                    order.estimated_delivery = datetime.fromisoformat(scheduled_time)
                else:
                    order.estimated_delivery = datetime.utcnow() + timedelta(days=1)
            except ValueError:
                print(f"[ORDER SERVICE] Invalid scheduled_time format: {scheduled_time}")
                order.estimated_delivery = datetime.utcnow() + timedelta(days=1)
        
        print(f"[ORDER SERVICE] Creating order object...")
        db.session.add(order)
        db.session.flush()  # Get the order ID
        
        # Generate order number
        order.order_number = order.generate_order_number()
        print(f"[ORDER SERVICE] Order created with ID: {order.id}, Number: {order.order_number}")
        
        # Create order items
        print(f"[ORDER SERVICE] Creating {len(items)} order items...")
        item_sizes_log = []
        for item_data in items:
            product = Product.query.get(item_data["product_id"])
            if not product:
                print(f"[ORDER SERVICE] Product {item_data['product_id']} not found, skipping")
                continue
            
            # Deduct size-specific inventory if size provided
            chosen_size = item_data.get("size")
            if chosen_size:
                try:
                    # Parse JSON sizes if present
                    sizes_map = {}
                    if product.size and isinstance(product.size, str) and product.size.strip().startswith("{"):
                        sizes_map = json.loads(product.size)
                    if chosen_size in sizes_map and sizes_map[chosen_size] > 0:
                        sizes_map[chosen_size] = max(0, int(sizes_map[chosen_size]) - int(item_data.get("quantity", 1)))
                        product.size = json.dumps(sizes_map)
                except Exception as e:
                    print(f"[ORDER SERVICE] Failed updating size map for product {product.id}: {e}")
            
            # Deduct total stock (fallback or along with size)
            try:
                product.stock = max(0, int(product.stock or 0) - int(item_data.get("quantity", 1)))
                # Keep quantity aligned to stock for storefront consistency
                product.quantity = product.stock
            except Exception as e:
                print(f"[ORDER SERVICE] Failed updating stock for product {product.id}: {e}")

            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=item_data["quantity"],
                unit_price=item_data["price"],
                total_price=item_data["price"] * item_data["quantity"],
                product_name=product.pname,
                product_image=product.image
            )
            db.session.add(order_item)
            print(f"[ORDER SERVICE] Added order item: {product.pname} x {item_data['quantity']}")
            # Log size chosen for refund/exchange tracking
            try:
                chosen_size = item_data.get("size")
                if chosen_size:
                    # Ensure we have an ID
                    db.session.flush()
                    item_sizes_log.append({
                        "order_item_id": order_item.id,
                        "product_id": product.id,
                        "size": chosen_size,
                        "quantity": int(item_data.get("quantity", 1))
                    })
            except Exception as e:
                print(f"[ORDER SERVICE] Failed to log item size: {e}")
        # Commit item-level deductions and attach sizes log to delivery_notes
        db.session.flush()
        try:
            notes = {}
            if order.delivery_notes:
                try:
                    notes = json.loads(order.delivery_notes)
                except Exception:
                    notes = {}
            if item_sizes_log:
                notes["item_sizes"] = item_sizes_log
                order.delivery_notes = json.dumps(notes)
        except Exception as e:
            print(f"[ORDER SERVICE] Failed to save item sizes log: {e}")
        
        print(f"[ORDER SERVICE] Committing to database...")
        db.session.commit()
        print(f"[ORDER SERVICE] Order committed successfully")
        
        # Get complete order data
        order_data = order.as_dict()
        order_data["items"] = [item.as_dict() for item in order.order_items]
        
        print(f"[ORDER SERVICE] Final order data: {order_data}")
        
        # Encrypt the response data
        encrypted_data = encrypt_payload({
            "success": True,
            "order": order_data,
            "message": "Order created successfully"
        })
        
        print(f"[ORDER SERVICE] Encrypted response created")
        
        return {
            "success": True,
            "encrypted_data": encrypted_data,
            "message": "Order created successfully"
        }, 201
        
    except Exception as e:
        print(f"❌ Create order error: {str(e)}")
        db.session.rollback()
        return {"error": "Failed to create order"}, 500

def get_order_by_id(order_id: int, customer_id: int = None):
    """Get order by ID"""
    try:
        query = Order.query.filter_by(id=order_id)
        if customer_id:
            query = query.filter_by(customer_id=customer_id)
        
        order = query.first()
        if not order:
            return {"error": "Order not found"}, 404
        
        # Get complete order data
        order_data = order.as_dict()
        order_data["items"] = [item.as_dict() for item in order.order_items]
        
        # Encrypt the response data
        encrypted_data = encrypt_payload({
            "success": True,
            "order": order_data,
            "message": "Order retrieved successfully"
        })
        
        return {
            "success": True,
            "encrypted_data": encrypted_data,
            "message": "Order retrieved successfully"
        }, 200
        
    except Exception as e:
        print(f"❌ Get order error: {str(e)}")
        return {"error": "Failed to retrieve order"}, 500

def get_customer_orders(customer_id: int, limit: int = 20):
    """Get all orders for a customer"""
    try:
        orders = Order.query.filter_by(customer_id=customer_id)\
            .order_by(Order.id.desc())\
            .limit(limit)\
            .all()
        
        orders_data = []
        for order in orders:
            order_data = order.as_dict()
            order_data["items"] = [item.as_dict() for item in order.order_items]
            orders_data.append(order_data)
        
        # Encrypt the response data
        encrypted_data = encrypt_payload({
            "success": True,
            "orders": orders_data,
            "total_count": len(orders_data)
        })
        
        return {
            "success": True,
            "encrypted_data": encrypted_data,
            "message": "Customer orders retrieved successfully"
        }, 200
        
    except Exception as e:
        print(f"❌ Get customer orders error: {str(e)}")
        return {"error": "Failed to retrieve customer orders"}, 500

def update_order_status(order_id: int, status: str, customer_id: int = None):
    """Update order status"""
    try:
        query = Order.query.filter_by(id=order_id)
        if customer_id:
            query = query.filter_by(customer_id=customer_id)
        
        order = query.first()
        if not order:
            return {"error": "Order not found"}, 404
        
        # Validate status
        valid_statuses = ["pending", "confirmed", "processing", "shipped", "delivered", "cancelled", "rejected"]
        if status not in valid_statuses:
            return {"error": "Invalid status"}, 400
        
        order.status = status
        order.updated_at = datetime.utcnow()
        
        # Update payment status if order is delivered
        if status == "delivered" and order.payment_method == "cod":
            order.payment_status = "completed"
        
        db.session.commit()
        
        # Encrypt the response data
        encrypted_data = encrypt_payload({
            "success": True,
            "order_id": order.id,
            "new_status": order.status,
            "message": f"Order status updated to {status}"
        })
        
        return {
            "success": True,
            "encrypted_data": encrypted_data,
            "message": "Order status updated successfully"
        }, 200
        
    except Exception as e:
        print(f"❌ Update order status error: {str(e)}")
        db.session.rollback()
        return {"error": "Failed to update order status"}, 500

def cancel_order(order_id: int, customer_id: int = None):
    """Cancel an order or initiate return if within window"""
    try:
        query = Order.query.filter_by(id=order_id)
        if customer_id:
            query = query.filter_by(customer_id=customer_id)
        
        order = query.first()
        if not order:
            return {"error": "Order not found"}, 404
        
        # If delivered, allow return within 24 hours; else block cancellation for shipped
        if order.status in ["shipped", "delivered"]:
            if order.status == "delivered":
                try:
                    delivered_at = order.updated_at or datetime.utcnow()
                    if datetime.utcnow() - delivered_at > timedelta(hours=24):
                        return {"error": "Return window expired"}, 400
                except Exception:
                    return {"error": "Return window expired"}, 400
                # Track return flow in delivery_notes
                try:
                    notes = json.loads(order.delivery_notes) if order.delivery_notes else {}
                except Exception:
                    notes = {}
                flow = notes.get("return_flow", [])
                flow.append({"status": "return_requested", "at": datetime.utcnow().isoformat()})
                notes["return_flow"] = flow
                # Reflect return in main status for frontend/admin visibility
                order.status = "return_requested"
                order.delivery_notes = json.dumps(notes)
                order.updated_at = datetime.utcnow()
                db.session.commit()
                return {"success": True, "message": "Return request initiated"}, 200
            return {"error": "Cannot cancel shipped order"}, 400
        
        # Regular cancellation flow for pre-shipment orders
        try:
            notes = json.loads(order.delivery_notes) if order.delivery_notes else {}
        except Exception:
            notes = {}
        flow = notes.get("cancel_flow", [])
        flow.append({"status": "cancel_request_initiated", "at": datetime.utcnow().isoformat()})
        # Reflect cancel requested in main status for visibility
        order.status = "cancel_requested"
        order.updated_at = datetime.utcnow()
        
        # Handle refunds
        if order.payment_status == "completed" and order.payment_method in ["wallet", "razorpay"]:
            flow.append({"status": "refund_initiated", "at": datetime.utcnow().isoformat()})
            if order.payment_method == "wallet":
                order.payment_status = "refunded"
                flow.append({"status": "refunded", "at": datetime.utcnow().isoformat()})
            else:
                order.payment_status = "refund_initiated"
        notes["cancel_flow"] = flow
        order.delivery_notes = json.dumps(notes)
        
        db.session.commit()
        return {"success": True, "message": "Order cancelled successfully"}, 200
        
    except Exception as e:
        print(f"❌ Cancel order error: {str(e)}")
        db.session.rollback()
        return {"error": "Failed to cancel order"}, 500

def get_all_orders():
    """Get all orders for admin panel"""
    try:
        orders = Order.query.order_by(Order.id.desc()).all()
        return orders
    except Exception as e:
        print(f"❌ Get all orders error: {str(e)}")
        return []

def get_order_by_id(order_id: int):
    """Get order by ID"""
    try:
        order = Order.query.get(order_id)
        return order
    except Exception as e:
        print(f"❌ Get order by ID error: {str(e)}")
        return None
