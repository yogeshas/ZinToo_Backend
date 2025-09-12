# routes/admin_customer.py
from flask import Blueprint, request, jsonify
from services.customer_service import (
    get_all_customers,
    get_customer_by_id,
    update_customer_admin,
    delete_customer,
    set_customer_blocked
)
from utils.auth import require_admin_auth
from utils.crypto import encrypt_payload, decrypt_payload

admin_customer_bp = Blueprint("admin_customer", __name__)

@admin_customer_bp.route("/", methods=["GET"])
@require_admin_auth
def get_customers(current_admin):
    """Get all customers for admin panel"""
    try:
        customers = get_all_customers()
        customers_data = []
        
        for customer in customers:
            customer_dict = customer.as_dict()
            # Add additional computed fields
            if hasattr(customer, 'orders'):
                orders = list(customer.orders)
                customer_dict["orders_count"] = len(orders)
                customer_dict["total_spent"] = sum(order.total_amount for order in orders)
            else:
                customer_dict["orders_count"] = 0
                customer_dict["total_spent"] = 0
            customer_dict["blocked"] = customer.status == "blocked"
            customers_data.append(customer_dict)
        
        data = {"customers": customers_data}
        enc = encrypt_payload(data)
        return jsonify({"success": True, "encrypted_data": enc}), 200
    except Exception as e:
        print(f"Get customers route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@admin_customer_bp.route("/<int:customer_id>", methods=["GET"])
@require_admin_auth
def get_customer(current_admin, customer_id):
    """Get customer by ID with detailed information"""
    try:
        print(f"Getting customer {customer_id} for admin: {current_admin}")
        customer = get_customer_by_id(customer_id)
        if not customer:
            print(f"Customer {customer_id} not found")
            return jsonify({"error": "Customer not found"}), 404
        
        print(f"Found customer: {customer.id} - {customer.username}")
        customer_dict = customer.as_dict()
        
        # Add orders information - handle the relationship properly
        orders_data = []
        total_spent = 0.0
        
        try:
            # Check if orders relationship exists and is accessible
            if hasattr(customer, 'orders') and customer.orders is not None:
                # Convert to list to avoid InstrumentedList issues
                orders = list(customer.orders)
                print(f"Found {len(orders)} orders for customer {customer_id}")
                
                for order in orders:
                    try:
                        order_dict = order.as_dict()
                        
                        # Add order items if available
                        order_items = []
                        if hasattr(order, 'order_items') and order.order_items is not None:
                            try:
                                # Handle dynamic relationship
                                items = list(order.order_items)
                                for item in items:
                                    order_items.append(item.as_dict())
                            except Exception as e:
                                print(f"Error processing order items for order {order.id}: {e}")
                        
                        order_dict["items"] = order_items
                        orders_data.append(order_dict)
                        
                        # Calculate total spent
                        if hasattr(order, 'total_amount'):
                            total_spent += float(order.total_amount or 0)
                            
                    except Exception as e:
                        print(f"Error processing order {order.id if hasattr(order, 'id') else 'unknown'}: {e}")
                        continue
            else:
                print(f"No orders relationship found for customer {customer_id}")
                
        except Exception as e:
            print(f"Error accessing orders for customer {customer_id}: {e}")
        
        # Add refund information from wallet transactions
        refunds_data = []
        try:
            if hasattr(customer, 'wallet') and customer.wallet is not None:
                from models.wallet import WalletTransaction
                wallet = customer.wallet
                if wallet:
                    refund_transactions = WalletTransaction.query.filter_by(
                        wallet_id=wallet.id,
                        transaction_type='refund'
                    ).all()
                    for transaction in refund_transactions:
                        refunds_data.append({
                            'order_number': transaction.reference_id or 'N/A',
                            'refund_amount': transaction.amount,
                            'refund_reason': transaction.description or 'Refund',
                            'refund_status': 'Completed',
                            'refund_date': transaction.created_at.isoformat() if transaction.created_at else None
                        })
        except Exception as e:
            print(f"Error processing refunds for customer {customer_id}: {e}")
        
        # Add computed fields
        customer_dict["orders"] = orders_data
        customer_dict["orders_count"] = len(orders_data)
        customer_dict["refunds"] = refunds_data
        customer_dict["total_spent"] = total_spent
        customer_dict["blocked"] = customer.status == "blocked"
        
        print(f"Customer {customer_id} data prepared successfully")
        data = {"customer": customer_dict}
        enc = encrypt_payload(data)
        return jsonify({"success": True, "encrypted_data": enc}), 200
        
    except Exception as e:
        print(f"Get customer route error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

@admin_customer_bp.route("/<int:customer_id>", methods=["PUT"])
@require_admin_auth
def update_customer_route(current_admin, customer_id):
    print(f"🚨 HITTING ADMIN UPDATE for {customer_id}")
    print(f"🚨 ADMIN Request URL: {request.url}")
    print(f"🚨 ADMIN Request path: {request.path}")
    print(f"🚨 ADMIN Request method: {request.method}")
    print(f"🚨 ADMIN Request headers: {dict(request.headers)}")
    """Admin updates a customer"""
    try:
        encrypted_data = request.json.get("payload")
        if not encrypted_data:
            print("❌ Missing encrypted payload")
            return jsonify({"error": "Missing encrypted payload"}), 400

        data = decrypt_payload(encrypted_data)
        print(f"[ADMIN] Decrypted update data: {data}")

        # Validate required fields
        if not data:
            print("❌ Empty decrypted data")
            return jsonify({"error": "Invalid data"}), 400

        # Log what fields are being updated
        print(f"[ADMIN] Fields to update: {list(data.keys())}")
        
        # Check if location is being updated
        if "location" in data:
            print(f"[ADMIN] Location update: '{data['location']}' (type: {type(data['location'])})")
        
        # Check if phone_number is being updated
        if "phone_number" in data:
            print(f"[ADMIN] Phone update: '{data['phone_number']}' (type: {type(data['phone_number'])})")

        updated_customer = update_customer_admin(customer_id, data)
        if not updated_customer:
            print(f"❌ Customer {customer_id} not found for update")
            return jsonify({"error": "Customer not found"}), 404

        # Verify the update worked
        print(f"[ADMIN] Update successful for customer {customer_id}")
        print(f"[ADMIN] Final location: '{updated_customer.get_location()}'")
        print(f"[ADMIN] Final phone: '{updated_customer.get_phone_number()}'")

        customer_dict = updated_customer.as_dict()
        enc = encrypt_payload({"customer": customer_dict})
        return jsonify({"success": True, "encrypted_data": enc}), 200

    except Exception as e:
        print(f"[ADMIN] Update customer route error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

@admin_customer_bp.route("/<int:customer_id>", methods=["DELETE"])
@require_admin_auth
def delete_customer_route(current_admin, customer_id):
    """Delete customer"""
    try:
        customer = get_customer_by_id(customer_id)
        if not customer:
            return jsonify({"error": "Customer not found"}), 404
        
        delete_customer(customer_id)
        return jsonify({"success": True, "message": "Customer deleted successfully"}), 200
    except Exception as e:
        print(f"Delete customer route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@admin_customer_bp.route("/<int:customer_id>/block", methods=["POST"])
@require_admin_auth
def block_customer_route(current_admin, customer_id):
    try:
        customer = get_customer_by_id(customer_id)
        if not customer:
            return jsonify({"error": "Customer not found"}), 404
        
        updated_customer = set_customer_blocked(customer_id, True)  # block explicitly
        customer_dict = updated_customer.as_dict()
        enc = encrypt_payload({"customer": customer_dict})

        return jsonify({"success": True, "encrypted_data": enc}), 200
    except Exception as e:
        print(f"Block customer error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@admin_customer_bp.route("/<int:customer_id>/unblock", methods=["POST"])
@require_admin_auth
def unblock_customer_route(current_admin, customer_id):
    try:
        customer = get_customer_by_id(customer_id)
        if not customer:
            return jsonify({"error": "Customer not found"}), 404
        
        updated_customer = set_customer_blocked(customer_id, False)  # unblock explicitly
        customer_dict = updated_customer.as_dict()
        enc = encrypt_payload({"customer": customer_dict})

        return jsonify({"success": True, "encrypted_data": enc}), 200
    except Exception as e:
        print(f"Unblock customer error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500