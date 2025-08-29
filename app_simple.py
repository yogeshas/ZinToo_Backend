# app_simple.py - Simplified version for testing
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

# Import basic models first
print("🔍 Importing basic models...")
try:
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
    print("✅ Basic models imported successfully")
except Exception as e:
    print(f"❌ Basic models import failed: {str(e)}")

# Import basic blueprints
print("🔍 Importing basic blueprints...")
try:
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
    print("✅ Basic blueprints imported successfully")
except Exception as e:
    print(f"❌ Basic blueprints import failed: {str(e)}")

# Register basic blueprints
print("🔍 Registering basic blueprints...")
try:
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
    print("✅ Basic blueprints registered successfully")
    try:
        from routes.review import review_bp
        app.register_blueprint(review_bp, url_prefix='/api/reviews')
        print("✅ Review blueprint registered")
        from routes.review_comment import review_comment_bp
        app.register_blueprint(review_comment_bp, url_prefix='/api/review-comments')
        print("✅ Review comment blueprint registered")
    except Exception as e:
        print(f"⚠️ Review blueprint not registered: {e}")
except Exception as e:
    print(f"❌ Basic blueprints registration failed: {str(e)}")

def cleanup_expired_otps_background():
    """Background task to clean up expired OTPs every 10 minutes"""
    while True:
        try:
            with app.app_context():
                from services.otp_service import cleanup_expired_otps as cleanup_login_otps
                from services.forgot_password_service import cleanup_expired_password_reset_otps as cleanup_all_otps
                cleanup_login_otps()
                cleanup_all_otps()
        except Exception as e:
            print(f"OTP cleanup error: {str(e)}")
        time.sleep(600)

# Create database tables
print("🔍 Creating database tables...")
with app.app_context():
    try:
        db.create_all()
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"❌ Database table creation failed: {str(e)}")
    
    try:
        create_default_admin()
        print("✅ Default admin created successfully")
    except Exception as e:
        print(f"❌ Default admin creation failed: {str(e)}")
    
    # Try to import new models after database creation
    print("🔍 Testing new model imports...")
    try:
        from models.wallet import Wallet, WalletTransaction
        print("✅ Wallet models imported successfully")
    except Exception as e:
        print(f"❌ Wallet models import failed: {str(e)}")
    
    try:
        from models.order import Order, OrderItem
        print("✅ Order models imported successfully")
    except Exception as e:
        print(f"❌ Order models import failed: {str(e)}")
    
    # Try to import new blueprints
    print("🔍 Testing new blueprint imports...")
    try:
        from routes.wallet import wallet_bp
        from routes.order import order_bp
        
        # Register new blueprints
        app.register_blueprint(wallet_bp, url_prefix='/api/wallet')
        app.register_blueprint(order_bp, url_prefix='/api/orders')
        print("✅ New blueprints registered successfully")
        try:
            from routes.review import review_bp
            app.register_blueprint(review_bp, url_prefix='/api/reviews')
            print("✅ Review blueprint registered (extended)")
            from routes.review_comment import review_comment_bp
            app.register_blueprint(review_comment_bp, url_prefix='/api/review-comments')
            print("✅ Review comment blueprint registered (extended)")
        except Exception as e:
            print(f"⚠️ Review blueprint not registered (extended): {e}")
    except Exception as e:
        print(f"❌ New blueprints import/registration failed: {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting Flask app...")
    app.run(debug=True, host='0.0.0.0', port=5000)
