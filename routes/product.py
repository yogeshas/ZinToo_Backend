# routes/product_routes.py
from flask import Blueprint, request, jsonify, current_app, send_from_directory
from werkzeug.utils import secure_filename
import os
from uuid import uuid4
from services.product_service import (
    create_product,
    get_product_by_id,
    get_all_products,
    get_customer_products,
    update_product,
    delete_product,
    regenerate_product_barcode,
)
from utils.barcode_image_generator import generate_barcode_image, generate_barcode_sticker_html
from utils.delivery_barcode_generator import generate_delivery_barcode_image, generate_delivery_barcode_sticker_html
from services.review_service import get_product_review_stats
from utils.crypto import encrypt_payload, decrypt_payload
from extensions import db

product_bp = Blueprint("products", __name__)
# Serve product images
@product_bp.route("/images/<path:filename>", methods=["GET"])
def serve_product_image(filename):
    base_dir = os.path.join(current_app.root_path, "assets", "img", "products")
    return send_from_directory(base_dir, filename)


# Upload multiple product images
@product_bp.route("/upload-images", methods=["POST"])
def upload_images():
    try:
        files = request.files.getlist("images")
        product_id = request.form.get("product_id")
        color_name = request.form.get("color_name")  # Optional for color-specific images
        
        if not files or all(not f or not getattr(f, "filename", None) for f in files):
            return jsonify({"success": False, "error": "No files provided"}), 400

        # Upload to S3 using environment configuration
        try:
            from utils.s3_service import S3Service
            s3_service = S3Service()
            
            allowed_ext = {"png", "jpg", "jpeg", "gif", "webp"}
            urls = []
            
            for f in files:
                if not f or not getattr(f, "filename", None):
                    continue
                    
                ext = f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else ""
                
                if ext not in allowed_ext:
                    return jsonify({"success": False, "error": f"Unsupported file type: {ext}"}), 400
                    
                mimetype = f.mimetype or ""
                if not mimetype.startswith("image/"):
                    return jsonify({"success": False, "error": "Only image files are allowed"}), 400
                
                # Upload to S3 with organized folder structure using environment configuration
                if product_id:
                    url = s3_service.upload_product_file(f, product_id, color_name)
                else:
                    url = s3_service.upload_file(f, "temp", "image", "product")
                
                if url:
                    urls.append(url)
                else:
                    return jsonify({"success": False, "error": f"Failed to upload file: {f.filename}"}), 500

            return jsonify({"success": True, "files": urls})
            
        except ValueError as s3_error:
            print(f"❌ S3 upload failed: {str(s3_error)}")
            return jsonify({"success": False, "error": f"S3 upload failed: {str(s3_error)}"}), 500
        except Exception as s3_error:
            print(f"❌ S3 upload error: {str(s3_error)}")
            return jsonify({"success": False, "error": f"S3 upload error: {str(s3_error)}"}), 500
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# GET all products (admin)
@product_bp.route("/", methods=["GET"])
def list_products():
    products = get_all_products()
    response = {"products": [p.to_dict() for p in products]}
    encrypted = encrypt_payload(response)
    return jsonify({"success": True, "encrypted_data": encrypted})

# GET customer products (filtered for customer view)
@product_bp.route("/customer", methods=["GET"])
def list_customer_products():
    products = get_customer_products()
    response = {"products": [p.to_dict() for p in products]}
    encrypted = encrypt_payload(response)
    return jsonify({"success": True, "encrypted_data": encrypted})


# GET product by ID (admin)
@product_bp.route("/<int:pid>", methods=["GET"])
def get_product(pid):
    p = get_product_by_id(pid)
    if not p:
        return jsonify({"success": False, "error": "Not found"}), 404
    stats = get_product_review_stats(p.id)
    response = {"product": p.to_dict(), "review_stats": stats}
    encrypted = encrypt_payload(response)
    return jsonify({"success": True, "encrypted_data": encrypted})

# GET customer product by ID (filtered for customer view)
@product_bp.route("/customer/<int:pid>", methods=["GET"])
def get_customer_product(pid):
    p = get_product_by_id(pid)
    if not p or not p.is_active or not p.visibility:
        return jsonify({"success": False, "error": "Product not found or not available"}), 404
    stats = get_product_review_stats(p.id)
    response = {"product": p.to_dict(), "review_stats": stats}
    encrypted = encrypt_payload(response)
    return jsonify({"success": True, "encrypted_data": encrypted})


# CREATE product
@product_bp.route("/", methods=["POST"])
def create():
    try:
        encrypted_request = request.json.get("data")
        if not encrypted_request:
            return jsonify({"success": False, "error": "Missing encrypted data"}), 400
            
        data = decrypt_payload(encrypted_request)
        if not data:
            return jsonify({"success": False, "error": "Invalid encrypted data"}), 400

        product = create_product(data)  # pass dict
        response = {"product": product.to_dict()}
        encrypted = encrypt_payload(response)
        return jsonify({"success": True, "encrypted_data": encrypted})
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": "Internal server error"}), 500


# UPDATE product
@product_bp.route("/<int:pid>", methods=["PUT"])
def update(pid):
    try:
        encrypted_request = request.json.get("data")
        data = decrypt_payload(encrypted_request)

        product = update_product(pid, data)
        if not product:
            return jsonify({"success": False, "error": "Not found"}), 404

        response = {"product": product.to_dict()}
        encrypted = encrypt_payload(response)
        return jsonify({"success": True, "encrypted_data": encrypted})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


# DELETE product
@product_bp.route("/<int:pid>", methods=["DELETE"])
def delete(pid):
    deleted = delete_product(pid)
    if not deleted:
        return jsonify({"success": False, "error": "Not found"}), 404
    return jsonify({"success": True, "message": "Product deleted"})


# REGENERATE BARCODE
@product_bp.route("/<int:pid>/regenerate-barcode", methods=["POST"])
def regenerate_barcode(pid):
    try:
        result = regenerate_product_barcode(pid)
        if result["success"]:
            response = {"barcode": result["barcode"]}
            encrypted = encrypt_payload(response)
            return jsonify({"success": True, "encrypted_data": encrypted})
        else:
            return jsonify({"success": False, "error": result["error"]}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# GENERATE BARCODE IMAGE
@product_bp.route("/<int:pid>/barcode-image", methods=["GET"])
def get_barcode_image(pid):
    try:
        product = get_product_by_id(pid)
        if not product:
            return jsonify({"success": False, "error": "Product not found"}), 404
        
        if not product.barcode:
            return jsonify({"success": False, "error": "Product has no barcode"}), 400
        
        # Check if barcode image already exists in database
        if product.barcode_image:
            response = {"barcode_image": product.barcode_image}
            encrypted = encrypt_payload(response)
            return jsonify({"success": True, "encrypted_data": encrypted})
        
        # Generate delivery-optimized barcode image
        image_data = generate_delivery_barcode_image(
            product.barcode, 
            product.pname, 
            product.id
        )
        
        if not image_data:
            return jsonify({"success": False, "error": "Failed to generate barcode image"}), 500
        
        # Save barcode image to database
        product.barcode_image = image_data
        db.session.commit()
        
        response = {"barcode_image": image_data}
        encrypted = encrypt_payload(response)
        return jsonify({"success": True, "encrypted_data": encrypted})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# GENERATE BARCODE STICKER HTML FOR PRINTING
@product_bp.route("/<int:pid>/barcode-sticker", methods=["GET"])
def get_barcode_sticker(pid):
    try:
        product = get_product_by_id(pid)
        if not product:
            return jsonify({"success": False, "error": "Product not found"}), 404
        
        if not product.barcode:
            return jsonify({"success": False, "error": "Product has no barcode"}), 400
        
        # Generate delivery-optimized sticker HTML
        html_content = generate_delivery_barcode_sticker_html(
            product.barcode,
            product.pname,
            product.id
        )
        
        # Return HTML directly, not encrypted
        return html_content, 200, {'Content-Type': 'text/html; charset=utf-8'}
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# GET PRODUCT STOCK ANALYTICS FOR DASHBOARD
@product_bp.route("/stock-analytics", methods=["GET"])
def get_product_stock_analytics():
    try:
        from models.product import Product
        
        # Get all active products with their colors and sizes data
        products = Product.query.filter_by(is_active=True, visibility=True).all()
        
        analytics_data = []
        for product in products:
            colors_data = product.get_colors_data()
            if colors_data:  # Only include products that have colors data
                product_analytics = {
                    "id": product.id,
                    "name": product.pname,
                    "total_stock": 0,
                    "current_stock": [],
                    "out_of_stock": []
                }
                
                for color in colors_data:
                    if isinstance(color, dict) and color.get("name") and color.get("sizeCounts"):
                        color_name = color["name"]
                        size_counts = color.get("sizeCounts", {})
                        
                        # Process each size and its count
                        for size, count in size_counts.items():
                            count_int = int(count or 0)
                            product_analytics["total_stock"] += count_int
                            
                            if count_int > 0:
                                # Current stock
                                product_analytics["current_stock"].append({
                                    "color": color_name,
                                    "size": size,
                                    "count": count_int
                                })
                            else:
                                # Out of stock
                                product_analytics["out_of_stock"].append({
                                    "color": color_name,
                                    "size": size,
                                    "count": 0
                                })
                
                # Only include products that have some data
                if product_analytics["current_stock"] or product_analytics["out_of_stock"]:
                    analytics_data.append(product_analytics)
        
        response = {"success": True, "data": analytics_data}
        return jsonify(response)
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# GET PRODUCT PRICING ANALYTICS FOR DASHBOARD
@product_bp.route("/pricing-analytics", methods=["GET"])
def get_product_pricing_analytics():
    try:
        from models.product import Product
        
        # Get all active products with their pricing data
        products = Product.query.filter_by(is_active=True, visibility=True).all()
        
        analytics_data = {
            "total_products": len(products),
            "total_original_price": 0,
            "total_actual_price": 0,
            "total_discount_amount": 0,
            "total_final_price": 0,
            "total_profit_amount": 0,
            "average_profit_margin": 0,
            "products": []
        }
        
        for product in products:
            # Calculate pricing
            original_price = float(product.price or 0)
            actual_price = float(product.actual_price or 0)
            discount_value = float(product.discount_value or 0)
            
            # Calculate final price after discount
            discount_amount = (original_price * discount_value) / 100
            final_price = original_price - discount_amount
            
            # Calculate profit (final_price - actual_price)
            profit_amount = final_price - actual_price if actual_price > 0 else 0
            profit_margin = (profit_amount / final_price * 100) if final_price > 0 else 0
            
            # Add to totals
            analytics_data["total_original_price"] += original_price
            analytics_data["total_actual_price"] += actual_price
            analytics_data["total_discount_amount"] += discount_amount
            analytics_data["total_final_price"] += final_price
            analytics_data["total_profit_amount"] += profit_amount
            
            # Product details
            product_data = {
                "id": product.id,
                "name": product.pname,
                "original_price": round(original_price, 2),
                "actual_price": round(actual_price, 2),
                "discount_value": round(discount_value, 2),
                "discount_amount": round(discount_amount, 2),
                "final_price": round(final_price, 2),
                "profit_amount": round(profit_amount, 2),
                "profit_margin": round(profit_margin, 2),
                "stock": product.get_total_stock_from_colors() or product.stock or 0
            }
            
            analytics_data["products"].append(product_data)
        
        # Calculate average profit margin
        if analytics_data["total_final_price"] > 0:
            analytics_data["average_profit_margin"] = round(
                (analytics_data["total_profit_amount"] / analytics_data["total_final_price"]) * 100, 2
            )
        
        # Round all totals
        analytics_data["total_original_price"] = round(analytics_data["total_original_price"], 2)
        analytics_data["total_actual_price"] = round(analytics_data["total_actual_price"], 2)
        analytics_data["total_discount_amount"] = round(analytics_data["total_discount_amount"], 2)
        analytics_data["total_final_price"] = round(analytics_data["total_final_price"], 2)
        analytics_data["total_profit_amount"] = round(analytics_data["total_profit_amount"], 2)
        
        response = {"success": True, "data": analytics_data}
        return jsonify(response)
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# GET ORDER SALES ANALYTICS FOR DASHBOARD
@product_bp.route("/order-sales-analytics", methods=["GET"])
def get_order_sales_analytics():
    try:
        from models.order import Order, OrderItem
        from models.product import Product
        
        # Get all delivered orders (not cancelled)
        delivered_orders = Order.query.filter(
            Order.status.in_(['delivered', 'confirmed', 'processing', 'shipped'])
        ).all()
        
        analytics_data = {
            "total_orders": len(delivered_orders),
            "total_sales_amount": 0,
            "total_items_sold": 0,
            "average_order_value": 0,
            "top_products": [],
            "recent_orders": []
        }
        
        # Calculate totals
        for order in delivered_orders:
            analytics_data["total_sales_amount"] += order.total_amount
            
            # Get order items for this order
            order_items = OrderItem.query.filter_by(order_id=order.id).all()
            for item in order_items:
                analytics_data["total_items_sold"] += item.quantity
        
        # Calculate average order value
        if analytics_data["total_orders"] > 0:
            analytics_data["average_order_value"] = round(
                analytics_data["total_sales_amount"] / analytics_data["total_orders"], 2
            )
        
        # Get top selling products
        from sqlalchemy import func
        top_products_query = db.session.query(
            Product.pname,
            func.sum(OrderItem.quantity).label('total_quantity'),
            func.sum(OrderItem.total_price).label('total_revenue')
        ).join(OrderItem, Product.id == OrderItem.product_id)\
         .join(Order, OrderItem.order_id == Order.id)\
         .filter(Order.status.in_(['delivered', 'confirmed', 'processing', 'shipped']))\
         .group_by(Product.id, Product.pname)\
         .order_by(func.sum(OrderItem.quantity).desc())\
         .limit(10).all()
        
        analytics_data["top_products"] = [
            {
                "name": product_name,
                "quantity_sold": int(total_quantity),
                "revenue": float(total_revenue)
            }
            for product_name, total_quantity, total_revenue in top_products_query
        ]
        
        # Get recent orders
        recent_orders = Order.query.filter(
            Order.status.in_(['delivered', 'confirmed', 'processing', 'shipped'])
        ).order_by(Order.created_at.desc()).limit(5).all()
        
        analytics_data["recent_orders"] = [
            {
                "order_number": order.order_number,
                "total_amount": order.total_amount,
                "status": order.status,
                "created_at": order.created_at.isoformat() if order.created_at else None
            }
            for order in recent_orders
        ]
        
        # Round totals
        analytics_data["total_sales_amount"] = round(analytics_data["total_sales_amount"], 2)
        
        response = {"success": True, "data": analytics_data}
        return jsonify(response)
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# GET ORDER PROFIT ANALYTICS FOR DASHBOARD
@product_bp.route("/order-profit-analytics", methods=["GET"])
def get_order_profit_analytics():
    try:
        from models.order import Order, OrderItem
        from models.product import Product
        
        # Get all delivered orders (not cancelled)
        delivered_orders = Order.query.filter(
            Order.status.in_(['delivered', 'confirmed', 'processing', 'shipped'])
        ).all()
        
        analytics_data = {
            "total_orders": len(delivered_orders),
            "total_revenue": 0,
            "total_cost": 0,
            "total_profit": 0,
            "profit_margin": 0,
            "top_profitable_products": [],
            "profit_by_order": []
        }
        
        # Calculate profit for each order
        for order in delivered_orders:
            order_items = OrderItem.query.filter_by(order_id=order.id).all()
            order_revenue = 0
            order_cost = 0
            
            for item in order_items:
                # Get product details
                product = Product.query.get(item.product_id)
                if product:
                    # Revenue from this item
                    item_revenue = item.total_price
                    order_revenue += item_revenue
                    
                    # Cost for this item (actual_price * quantity)
                    item_cost = (product.actual_price or 0) * item.quantity
                    order_cost += item_cost
            
            order_profit = order_revenue - order_cost
            
            analytics_data["total_revenue"] += order_revenue
            analytics_data["total_cost"] += order_cost
            analytics_data["total_profit"] += order_profit
            
            # Store profit by order
            analytics_data["profit_by_order"].append({
                "order_number": order.order_number,
                "revenue": round(order_revenue, 2),
                "cost": round(order_cost, 2),
                "profit": round(order_profit, 2),
                "profit_margin": round((order_profit / order_revenue * 100) if order_revenue > 0 else 0, 2)
            })
        
        # Calculate overall profit margin
        if analytics_data["total_revenue"] > 0:
            analytics_data["profit_margin"] = round(
                (analytics_data["total_profit"] / analytics_data["total_revenue"]) * 100, 2
            )
        
        # Get top profitable products
        from sqlalchemy import func
        profitable_products_query = db.session.query(
            Product.pname,
            func.sum(OrderItem.quantity).label('total_quantity'),
            func.sum(OrderItem.total_price).label('total_revenue'),
            func.sum((Product.actual_price * OrderItem.quantity)).label('total_cost')
        ).join(OrderItem, Product.id == OrderItem.product_id)\
         .join(Order, OrderItem.order_id == Order.id)\
         .filter(Order.status.in_(['delivered', 'confirmed', 'processing', 'shipped']))\
         .group_by(Product.id, Product.pname, Product.actual_price)\
         .order_by((func.sum(OrderItem.total_price) - func.sum(Product.actual_price * OrderItem.quantity)).desc())\
         .limit(10).all()
        
        analytics_data["top_profitable_products"] = [
            {
                "name": product_name,
                "quantity_sold": int(total_quantity),
                "revenue": float(total_revenue),
                "cost": float(total_cost or 0),
                "profit": float(total_revenue - (total_cost or 0)),
                "profit_margin": round(((total_revenue - (total_cost or 0)) / total_revenue * 100) if total_revenue > 0 else 0, 2)
            }
            for product_name, total_quantity, total_revenue, total_cost in profitable_products_query
        ]
        
        # Round totals
        analytics_data["total_revenue"] = round(analytics_data["total_revenue"], 2)
        analytics_data["total_cost"] = round(analytics_data["total_cost"], 2)
        analytics_data["total_profit"] = round(analytics_data["total_profit"], 2)
        
        response = {"success": True, "data": analytics_data}
        return jsonify(response)
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# VERIFY BARCODE
@product_bp.route("/verify-barcode/<barcode_number>", methods=["GET"])
def verify_barcode(barcode_number):
    try:
        from models.product import Product
        
        # Find product by barcode
        product = Product.query.filter_by(barcode=barcode_number).first()
        
        if not product:
            return jsonify({"success": False, "error": "Barcode not found"}), 404
        
        # Prepare response data
        response_data = {
            "product_id": product.id,
            "product_name": product.pname,
            "barcode": product.barcode,
            "price": product.original_price or product.price,
            "category_id": product.cid,
            "subcategory_id": product.sid,
            "stock": product.stock,
            "is_active": product.is_active,
            "created_at": product.created_at.isoformat() if product.created_at else None,
            "updated_at": product.updated_at.isoformat() if product.updated_at else None,
            
        }
        
        response = {"success": True, "data": response_data}
        return jsonify(encrypt_payload(response))
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@product_bp.route('/customer-order-locations', methods=['GET'])
def get_customer_order_locations():
    """
    Get customer order locations for map visualization
    Returns addresses and order counts for mapping
    """
    try:
        from models.order import Order
        from models.customer import Customer
        from sqlalchemy import func
        
        # Get all delivered orders with customer info
        delivered_orders = Order.query.filter(
            Order.status.in_(['delivered', 'confirmed', 'processing', 'shipped'])
        ).join(Customer).all()
        
        # Group orders by delivery address
        address_orders = {}
        for order in delivered_orders:
            address = order.delivery_address
            if address and address.strip():
                # Parse address if it's JSON
                try:
                    import json
                    if address.startswith('{'):
                        address_data = json.loads(address)
                        # Create a readable address string
                        address_parts = []
                        if address_data.get('address_line1'):
                            address_parts.append(address_data['address_line1'])
                        if address_data.get('address_line2'):
                            address_parts.append(address_data['address_line2'])
                        if address_data.get('city'):
                            address_parts.append(address_data['city'])
                        if address_data.get('state'):
                            address_parts.append(address_data['state'])
                        if address_data.get('postal_code'):
                            address_parts.append(address_data['postal_code'])
                        address = ', '.join(address_parts) if address_parts else order.delivery_address
                except:
                    # If parsing fails, use original address
                    pass
                
                if address not in address_orders:
                    address_orders[address] = {
                        'address': address,
                        'order_count': 0,
                        'total_amount': 0,
                        'customers': set(),
                        'recent_orders': []
                    }
                
                address_orders[address]['order_count'] += 1
                address_orders[address]['total_amount'] += order.total_amount
                address_orders[address]['customers'].add(order.customer_id)
                
                # Add recent order info
                address_orders[address]['recent_orders'].append({
                    'order_id': order.id,
                    'order_number': order.order_number,
                    'customer_name': order.customer.name if order.customer and order.customer.name else (order.customer.username if order.customer else "Unknown"),
                    'total_amount': order.total_amount,
                    'status': order.status,
                    'created_at': order.created_at.isoformat() if order.created_at else None
                })
        
        # Convert to list and sort by order count
        locations_data = []
        for address, data in address_orders.items():
            locations_data.append({
                'address': data['address'],
                'order_count': data['order_count'],
                'total_amount': round(data['total_amount'], 2),
                'unique_customers': len(data['customers']),
                'recent_orders': data['recent_orders'][-5:]  # Last 5 orders
            })
        
        # Sort by order count (descending)
        locations_data.sort(key=lambda x: x['order_count'], reverse=True)
        
        # Calculate summary stats
        total_locations = len(locations_data)
        total_orders = sum(loc['order_count'] for loc in locations_data)
        total_amount = sum(loc['total_amount'] for loc in locations_data)
        
        analytics_data = {
            "total_locations": total_locations,
            "total_orders": total_orders,
            "total_amount": round(total_amount, 2),
            "locations": locations_data
        }
        
        return jsonify({
            "success": True,
            "data": analytics_data
        }), 200

    except Exception as e:
        print(f"Error in get_customer_order_locations: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
