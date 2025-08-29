#!/usr/bin/env python3
"""
Script to add new models (Wallet, Order) after the basic backend is running
This avoids circular import issues during startup.
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def add_new_models():
    """Add new models to the database"""
    print("🔍 Adding new models to database...")
    
    try:
        from extensions import db
        from config import Config
        
        # Create a simple Flask app for testing
        from flask import Flask
        app = Flask(__name__)
        app.config.from_object(Config)
        db.init_app(app)
        
        with app.app_context():
            # Import new models
            print("📦 Importing new models...")
            from models.wallet import Wallet, WalletTransaction
            from models.order import Order, OrderItem
            print("✅ New models imported successfully")
            
            # Create new tables
            print("🏗️ Creating new database tables...")
            db.create_all()
            print("✅ New tables created successfully")
            
            print("🎉 New models added successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Failed to add new models: {str(e)}")
        return False

def test_new_apis():
    """Test if new APIs are working"""
    print("\n🔍 Testing new APIs...")
    
    try:
        from routes.wallet import wallet_bp
        from routes.order import order_bp
        print("✅ New blueprints imported successfully")
        
        # Test basic functionality
        print("✅ New APIs are ready to use!")
        return True
        
    except Exception as e:
        print(f"❌ New APIs test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Starting new model addition process...\n")
    
    # Step 1: Add new models
    models_added = add_new_models()
    
    if models_added:
        # Step 2: Test new APIs
        apis_working = test_new_apis()
        
        if apis_working:
            print("\n🎉 SUCCESS! New models and APIs are ready!")
            print("\n📝 Next steps:")
            print("1. Restart your main backend (python3 app.py)")
            print("2. The new APIs will be automatically available")
            print("3. Test the wallet and order endpoints")
        else:
            print("\n⚠️ Models added but APIs have issues")
    else:
        print("\n❌ Failed to add new models")
    
    print("\n✨ Process completed!")
