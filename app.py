# app.py
from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from extensions import db, migrate, mail
from datetime import datetime
import time

# Create Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
migrate.init_app(app, db)
mail.init_app(app)

# Setup CORS
CORS(app, resources={
    r"/api/*": {
        "origins": ["*"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["Content-Type"],
    }
}, supports_credentials=True)

# Health check endpoint
@app.route('/api/health')
def health_check():
    return jsonify({
        'success': True,
        'message': 'Backend is running',
        'timestamp': datetime.now().isoformat()
    })

# Static file serving for assets
@app.route('/assets/<path:filename>')
def serve_assets(filename):
    """Serve static files from assets directory"""
    from flask import send_from_directory
    import os
    
    # Security check - ensure file path is within assets directory
    allowed_path = os.path.join(app.root_path, 'assets')
    full_path = os.path.join(app.root_path, 'assets', filename)
    
    # Check if the resolved path is within the allowed directory
    if not os.path.commonpath([os.path.abspath(full_path), os.path.abspath(allowed_path)]) == os.path.abspath(allowed_path):
        return jsonify({"error": "Access denied"}), 403
    
    if not os.path.exists(full_path):
        return jsonify({"error": "File not found"}), 404
    
    return send_from_directory(os.path.dirname(full_path), os.path.basename(filename))

# Import models to register them with SQLAlchemy (after app creation)
from models.category import Category
from models.subcategory import SubCategory
from models.customer import Customer
from models.product import Product
from models.cart import Cart
from models.wishlist import Wishlist
from models.admin import Admin, create_default_admin
from models.address import Address
from models.widget import Widget
from models.coupons import Coupon

# Import additional models needed across the app so metadata is complete
from models.wallet import Wallet, WalletTransaction
from models.order import Order, OrderItem
from models.delivery_auth import DeliveryGuyAuth
from models.delivery_onboarding import DeliveryOnboarding
from models.delivery_loyalty import Delivery_Loyalty
from models.otp import OTP
from models.exchange import Exchange
from models.earnings_management import EarningsManagement

# Import blueprints (after models are imported)
from routes.customer import customer_bp
from routes.product import product_bp
from routes.category import category_bp
from routes.subcategory import subcategory_bp
from routes.cart import cart_bp
from routes.wishlist import wishlist_bp
from routes.admin_cart import admin_cart_bp
from routes.admin import admin_bp
from routes.address import address_bp
from routes.widget import widget_bp
from routes.coupon import coupon_bp
from routes.pincode import pincode_bp
from routes.review import review_bp
from routes.review_comment import review_comment_bp
from routes.auth import auth_bp

# Register blueprints
app.register_blueprint(customer_bp, url_prefix='/api/customers')
app.register_blueprint(product_bp, url_prefix='/api/products')
app.register_blueprint(category_bp, url_prefix='/api/categories')
app.register_blueprint(subcategory_bp, url_prefix='/api/subcategories')
app.register_blueprint(cart_bp, url_prefix='/api/cart')
app.register_blueprint(wishlist_bp, url_prefix='/api/wishlist')
app.register_blueprint(admin_cart_bp, url_prefix='/api/admin')
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(address_bp, url_prefix='/api/addresses')
app.register_blueprint(widget_bp, url_prefix='/api/widgets')
app.register_blueprint(coupon_bp, url_prefix='/api/coupons')
app.register_blueprint(pincode_bp, url_prefix='/api/pincode')
app.register_blueprint(review_bp, url_prefix='/api/reviews')
app.register_blueprint(review_comment_bp, url_prefix='/api/review-comments')
app.register_blueprint(auth_bp, url_prefix='/api/auth')

def cleanup_expired_otps_background():
        """Background task to clean up expired OTPs every 10 minutes"""
        while True:
            try:
                with app.app_context():
                    from services.otp_service import cleanup_expired_otps as cleanup_login_otps
                    # Our forgot password cleanup now uses same logic (no purpose column)
                    from services.forgot_password_service import cleanup_expired_password_reset_otps as cleanup_all_otps
                    cleanup_login_otps()
                    cleanup_all_otps()
            except Exception as e:
                print(f"OTP cleanup error: {str(e)}")
            # Sleep for 10 minutes
            time.sleep(600)

# Note: Database tables are managed via Flask-Migrate. Avoid create_all at import time.

# Import new blueprints after models
try:
    from routes.wallet import wallet_bp
    from routes.order import order_bp
    from routes.razorpay import razorpay_bp
    from routes.referral import referral_bp
    from routes.admin_customer import admin_customer_bp
    from routes.admin_order import admin_order_bp
    from routes.delivery import delivery_bp
    from routes.delivery_mobile import delivery_mobile_bp
    from routes.delivery_onboarding import delivery_onboarding_bp
    from routes.delivery_order import delivery_order_bp
    from routes.delivery_enhanced import delivery_enhanced_bp
    from routes.delivery_orders_enhanced import delivery_orders_enhanced_bp
    from routes.delivery_leave_requests import delivery_leave_requests_bp
    from routes.earnings_management import earnings_management_bp
    from routes.exchange import exchange_bp
    from routes.order_items import order_items_bp
    
    # Register new blueprints
    app.register_blueprint(wallet_bp, url_prefix='/api/wallet')
    app.register_blueprint(order_bp, url_prefix='/api/orders')
    app.register_blueprint(razorpay_bp, url_prefix='/api/razorpay')
    app.register_blueprint(referral_bp, url_prefix='/api/referral')
    app.register_blueprint(admin_customer_bp, url_prefix='/api/admin/customers')
    app.register_blueprint(admin_order_bp, url_prefix='/api/admin/orders')
    app.register_blueprint(delivery_bp, url_prefix='/api/delivery')
    app.register_blueprint(delivery_mobile_bp, url_prefix='/api/delivery-mobile')
    app.register_blueprint(delivery_onboarding_bp, url_prefix='/api/delivery')
    app.register_blueprint(delivery_order_bp, url_prefix='/api/delivery')
    app.register_blueprint(delivery_enhanced_bp, url_prefix='/api/delivery-enhanced')
    app.register_blueprint(delivery_orders_enhanced_bp, url_prefix='/api/delivery-orders')
    app.register_blueprint(delivery_leave_requests_bp, url_prefix='/api/leave-requests')
    app.register_blueprint(earnings_management_bp, url_prefix='/api/earnings-management')
    app.register_blueprint(exchange_bp, url_prefix='/api/exchanges')
    app.register_blueprint(order_items_bp, url_prefix='/api/order-items')
    print("✅ New blueprints registered successfully")
except Exception as e:
    print(f"⚠️ Warning: Could not register new blueprints: {str(e)}")


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
