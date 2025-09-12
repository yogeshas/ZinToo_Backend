# routes/admin_order.py
from flask import Blueprint, request, jsonify
from services.order_service import (
    get_all_orders,
    update_order_status,
    cancel_order
)
from services.order_item_service import assign_delivery_guy_to_order_bulk
from services.wallet_service import refund_to_wallet
from models.delivery_onboarding import DeliveryOnboarding
from models.order import Order
from extensions import db
from datetime import datetime
from utils.auth import require_admin_auth
from utils.crypto import encrypt_payload, decrypt_payload

admin_order_bp = Blueprint("admin_order", __name__)

@admin_order_bp.route("/", methods=["GET"])
@admin_order_bp.route("", methods=["GET"])
@require_admin_auth
def get_orders(current_admin):
    """Get all orders for admin panel"""
    try:
        orders = get_all_orders()
        orders_data = []
        
        for order in orders:
            order_dict = order.as_dict()
            # Add customer information
            if hasattr(order, 'customer') and order.customer:
                order_dict["customer"] = order.customer.as_dict()
            
            # Add order items
            order_items = []
            if hasattr(order, 'order_items'):
                for item in order.order_items:
                    order_items.append(item.as_dict())
            order_dict["items"] = order_items
            
            orders_data.append(order_dict)
        
        data = {"orders": orders_data}
        enc = encrypt_payload(data)
        return jsonify({"success": True, "encrypted_data": enc}), 200
    except Exception as e:
        print(f"Get orders route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@admin_order_bp.route("/<int:order_id>", methods=["GET"])
@require_admin_auth
def get_order(current_admin, order_id):
    """Get order by ID with detailed information"""
    try:
        order = Order.query.get(order_id)
        if not order:
            return jsonify({"error": "Order not found"}), 404
        
        order_dict = order.as_dict()
        
        # Add customer information
        if hasattr(order, 'customer') and order.customer:
            order_dict["customer"] = order.customer.as_dict()
        
        # Add order items
        order_items = []
        if hasattr(order, 'order_items'):
            for item in order.order_items:
                order_items.append(item.as_dict())
        order_dict["items"] = order_items
        
        data = {"order": order_dict}
        enc = encrypt_payload(data)
        return jsonify({"success": True, "encrypted_data": enc}), 200
    except Exception as e:
        print(f"Get order route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@admin_order_bp.route("/<int:order_id>/status", methods=["PUT"])
@require_admin_auth
def update_status(current_admin, order_id):
    """Update order status"""
    try:
        encrypted_data = request.json.get("payload")
        if not encrypted_data:
            return jsonify({"error": "Missing encrypted payload"}), 400
        
        data = decrypt_payload(encrypted_data)
        status = data.get("status")
        
        if not status:
            return jsonify({"error": "Status is required"}), 400
        
        result, status_code = update_order_status(order_id, status)
        
        if status_code != 200:
            return jsonify(result), status_code
        
        # Get the updated order
        updated_order = Order.query.get(order_id)
        if not updated_order:
            return jsonify({"error": "Order not found"}), 404
        
        order_dict = updated_order.as_dict()
        
        # Add customer information
        if hasattr(updated_order, 'customer') and updated_order.customer:
            order_dict["customer"] = updated_order.customer.as_dict()
        
        # Add order items
        order_items = []
        if hasattr(updated_order, 'order_items'):
            for item in updated_order.order_items:
                order_items.append(item.as_dict())
        order_dict["items"] = order_items
        
        data = {"order": order_dict}
        enc = encrypt_payload(data)
        return jsonify({"success": True, "encrypted_data": enc}), 200
    except Exception as e:
        print(f"Update order status route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@admin_order_bp.route("/<int:order_id>/refund", methods=["POST"])
@require_admin_auth
def update_refund_status(current_admin, order_id):
    """Update payment refund status; if set to refunded, auto-credit wallet"""
    try:
        encrypted_data = request.json.get("payload")
        if not encrypted_data:
            return jsonify({"error": "Missing encrypted payload"}), 400
        data = decrypt_payload(encrypted_data)
        new_status = data.get("payment_status")  # refund_initiated | refunded
        if new_status not in ["refund_initiated", "refunded"]:
            return jsonify({"error": "Invalid payment status"}), 400

        order = Order.query.get(order_id)
        if not order:
            return jsonify({"error": "Order not found"}), 404

        # Update payment status
        order.payment_status = new_status
        order.status = "refund_initiated" if new_status == "refund_initiated" else "refunded"
        # Track in delivery_notes cancel_flow if present
        try:
            import json as _json
            notes = _json.loads(order.delivery_notes) if order.delivery_notes else {}
        except Exception:
            notes = {}
        flow = notes.get("cancel_flow", [])
        if new_status == "refund_initiated":
            flow.append({"status": "refund_initiated", "at": datetime.utcnow().isoformat()})
        elif new_status == "refunded":
            flow.append({"status": "refunded", "at": datetime.utcnow().isoformat()})
        notes["cancel_flow"] = flow
        try:
            import json as _json
            order.delivery_notes = _json.dumps(notes)
        except Exception:
            pass

        # Auto credit wallet if marking refunded
        if new_status == "refunded":
            try:
                res, status = refund_to_wallet(order.customer_id, float(order.total_amount or 0.0), "Order refund", f"ORDER-{order.id}")
                # ignore result; it's credited to wallet
            except Exception as e:
                print(f"Refund credit error: {e}")

            # Restore stock and sizes for refunded order
            try:
                # Recover order items and size log from delivery_notes
                from models.product import Product
                import json as _json
                sizes_log = []
                try:
                    notes = _json.loads(order.delivery_notes) if order.delivery_notes else {}
                    sizes_log = notes.get("item_sizes", [])
                except Exception:
                    sizes_log = []
                # Build map order_item_id -> log
                id_to_log = {entry.get("order_item_id"): entry for entry in sizes_log if entry.get("order_item_id")}
                for item in order.order_items:
                    product = Product.query.get(item.product_id)
                    if not product:
                        continue
                    # restore total stock
                    try:
                        product.stock = int(product.stock or 0) + int(item.quantity or 0)
                        product.quantity = product.stock
                    except Exception:
                        pass
                    # restore size-specific if available
                    log = id_to_log.get(item.id)
                    if log and log.get("size"):
                        try:
                            sizes_map = {}
                            if product.size and isinstance(product.size, str) and product.size.strip().startswith("{"):
                                sizes_map = _json.loads(product.size)
                            chosen = log.get("size")
                            qty = int(log.get("quantity", 1))
                            sizes_map[chosen] = int(sizes_map.get(chosen, 0)) + qty
                            product.size = _json.dumps(sizes_map)
                        except Exception as e:
                            print(f"Failed restoring size for product {product.id}: {e}")
                db.session.flush()
            except Exception as e:
                print(f"Stock restore error: {e}")

        db.session.commit()

        # Return updated order
        updated = Order.query.get(order_id)
        order_dict = updated.as_dict()
        if hasattr(updated, 'customer') and updated.customer:
            order_dict["customer"] = updated.customer.as_dict()
        items = []
        if hasattr(updated, 'order_items'):
            for it in updated.order_items:
                items.append(it.as_dict())
        order_dict["items"] = items
        enc = encrypt_payload({"order": order_dict})
        return jsonify({"success": True, "encrypted_data": enc}), 200
    except Exception as e:
        print(f"Update refund status route error: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "Internal server error"}), 500

@admin_order_bp.route("/<int:order_id>/cancel", methods=["POST"])
@require_admin_auth
def cancel_order_route(current_admin, order_id):
    """Cancel an order"""
    try:
        cancelled_order = cancel_order(order_id)
        
        if not cancelled_order:
            return jsonify({"error": "Order not found"}), 404
        
        order_dict = cancelled_order.as_dict()
        
        # Add customer information
        if hasattr(cancelled_order, 'customer') and cancelled_order.customer:
            order_dict["customer"] = cancelled_order.customer.as_dict()
        
        # Add order items
        order_items = []
        if hasattr(cancelled_order, 'order_items'):
            for item in cancelled_order.order_items:
                order_items.append(item.as_dict())
        order_dict["items"] = order_items
        
        data = {"order": order_dict}
        enc = encrypt_payload(data)
        return jsonify({"success": True, "encrypted_data": enc}), 200
    except Exception as e:
        print(f"Cancel order route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@admin_order_bp.route("/delivery-personnel/available", methods=["GET"])
@require_admin_auth
def get_available_delivery_personnel(current_admin):
    """Get all available approved delivery personnel for reassignment"""
    try:
        # Get all approved delivery personnel
        available_personnel = DeliveryOnboarding.query.filter_by(status="approved").all()
        
        personnel_data = []
        for person in available_personnel:
            # Get their current active orders count
            active_orders = Order.query.filter_by(
                delivery_guy_id=person.id,
                status="assigned"
            ).count()
            
            personnel_data.append({
                "id": person.id,
                "name": f"{person.first_name} {person.last_name}".strip(),
                "phone_number": person.primary_number,
                "email": person.email,
                "active_orders": active_orders,
                "status": person.status,
                "created_at": person.created_at.isoformat() if person.created_at else None
            })
        
        # Sort by active orders count (fewer orders first)
        personnel_data.sort(key=lambda x: x["active_orders"])
        
        data = {"delivery_personnel": personnel_data}
        enc = encrypt_payload(data)
        return jsonify({"success": True, "encrypted_data": enc}), 200
        
    except Exception as e:
        print(f"Get available delivery personnel error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@admin_order_bp.route("/<int:order_id>/reassign", methods=["POST"])
@require_admin_auth
def reassign_rejected_order(current_admin, order_id):
    """Reassign a rejected order to another delivery personnel"""
    try:
        encrypted_data = request.json.get("payload")
        if not encrypted_data:
            return jsonify({"error": "Missing encrypted payload"}), 400
        
        data = decrypt_payload(encrypted_data)
        new_delivery_guy_id = data.get("delivery_guy_id")
        reassignment_reason = data.get("reassignment_reason", "Order reassigned by admin")
        
        if not new_delivery_guy_id:
            return jsonify({"error": "New delivery guy ID is required"}), 400
        
        # Get the order
        order = Order.query.get(order_id)
        if not order:
            return jsonify({"error": "Order not found"}), 404
        
        # Check if order is rejected
        if order.status != "rejected":
            return jsonify({"error": "Only rejected orders can be reassigned"}), 400
        
        # Verify the new delivery guy exists and is approved
        new_delivery_guy = DeliveryOnboarding.query.filter_by(
            id=new_delivery_guy_id,
            status="approved"
        ).first()
        
        if not new_delivery_guy:
            return jsonify({"error": "New delivery guy not found or not approved"}), 404
        
        # Get the previous delivery guy info for notes
        previous_delivery_guy = None
        if order.delivery_guy_id:
            previous_delivery_guy = DeliveryOnboarding.query.get(order.delivery_guy_id)
        
        # Reassign the order
        previous_delivery_guy_id = order.delivery_guy_id
        order.delivery_guy_id = new_delivery_guy_id
        order.status = "assigned"  # Change status back to assigned
        order.assigned_at = datetime.utcnow()
        
        # Add reassignment note
        reassignment_note = f"\n[REASSIGNED] Order reassigned by admin at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"
        if previous_delivery_guy:
            reassignment_note += f" from {previous_delivery_guy.first_name} {previous_delivery_guy.last_name} (ID: {previous_delivery_guy_id})"
        reassignment_note += f" to {new_delivery_guy.first_name} {new_delivery_guy.last_name} (ID: {new_delivery_guy_id})"
        reassignment_note += f". Reason: {reassignment_reason}"
        
        order.delivery_notes = (order.delivery_notes or "") + reassignment_note
        
        db.session.commit()
        
        # Get the updated order with delivery guy info
        order_dict = order.as_dict()
        
        # Add new delivery guy information
        order_dict["delivery_guy"] = {
            "id": new_delivery_guy.id,
            "name": f"{new_delivery_guy.first_name} {new_delivery_guy.last_name}".strip(),
            "phone_number": new_delivery_guy.primary_number,
            "email": new_delivery_guy.email
        }
        
        # Add customer information
        if hasattr(order, 'customer') and order.customer:
            order_dict["customer"] = order.customer.as_dict()
        
        # Add order items
        order_items = []
        if hasattr(order, 'order_items'):
            for item in order.order_items:
                order_items.append(item.as_dict())
        order_dict["items"] = order_items
        
        data = {"order": order_dict}
        enc = encrypt_payload(data)
        return jsonify({"success": True, "encrypted_data": enc}), 200
        
    except Exception as e:
        print(f"Reassign order route error: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "Internal server error"}), 500

@admin_order_bp.route("/rejected", methods=["GET"])
@require_admin_auth
def get_rejected_orders(current_admin):
    """Get all rejected orders that can be reassigned"""
    try:
        # Get all rejected orders
        rejected_orders = Order.query.filter_by(status="rejected").all()
        
        orders_data = []
        for order in rejected_orders:
            order_dict = order.as_dict()
            
            # Add customer information
            if hasattr(order, 'customer') and order.customer:
                order_dict["customer"] = order.customer.as_dict()
            
            # Add order items
            order_items = []
            if hasattr(order, 'order_items'):
                for item in order.order_items:
                    order_items.append(item.as_dict())
            order_dict["items"] = order_items
            
            # Add previous delivery guy info if available
            if order.delivery_guy_id:
                previous_delivery_guy = DeliveryOnboarding.query.get(order.delivery_guy_id)
                if previous_delivery_guy:
                    order_dict["previous_delivery_guy"] = {
                        "id": previous_delivery_guy.id,
                        "name": f"{previous_delivery_guy.first_name} {previous_delivery_guy.last_name}".strip(),
                        "phone_number": previous_delivery_guy.primary_number,
                        "email": previous_delivery_guy.email
                    }
            
            orders_data.append(order_dict)
        
        data = {"rejected_orders": orders_data}
        enc = encrypt_payload(data)
        return jsonify({"success": True, "encrypted_data": enc}), 200
        
    except Exception as e:
        print(f"Get rejected orders error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@admin_order_bp.route("/<int:order_id>/assign-delivery-bulk", methods=["POST"])
@require_admin_auth
def assign_delivery_bulk(current_admin, order_id):
    """Assign delivery guy to all items in an order (bulk assignment)"""
    try:
        admin_id = current_admin["id"]
        
        # Get request data (encrypted payload)
        data = request.get_json() or {}
        payload = data.get("payload")
        
        if not payload:
            return jsonify({"error": "Missing encrypted payload"}), 400
        
        # Decrypt the payload
        try:
            decrypted_data = decrypt_payload(payload)
        except Exception as e:
            print(f"Error decrypting payload: {e}")
            return jsonify({"error": "Invalid encrypted payload"}), 401
        
        delivery_guy_id = decrypted_data.get("delivery_guy_id")
        notes = decrypted_data.get("notes", "")
        
        if not delivery_guy_id:
            return jsonify({"error": "Delivery guy ID is required"}), 400
        
        # Assign delivery guy to all items in the order
        result = assign_delivery_guy_to_order_bulk(
            order_id=order_id,
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
        print(f"Error assigning delivery to order (bulk): {e}")
        return jsonify({"error": "Internal server error"}), 500
