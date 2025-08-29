#!/usr/bin/env python3
"""
Test script to check model imports and identify issues
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test importing different models to identify issues"""
    
    print("🔍 Testing model imports...")
    
    # Test basic imports
    try:
        from extensions import db
        print("✅ extensions.db imported successfully")
    except Exception as e:
        print(f"❌ extensions.db import failed: {str(e)}")
        return False
    
    # Test existing models
    models_to_test = [
        ("Category", "models.category"),
        ("SubCategory", "models.subcategory"),
        ("Customer", "models.customer"),
        ("Product", "models.product"),
        ("Cart", "models.cart"),
        ("Wishlist", "models.wishlist"),
        ("Admin", "models.admin"),
        ("Address", "models.address"),
        ("Widget", "models.widget"),
        ("Coupon", "models.coupons"),
    ]
    
    working_models = []
    failed_models = []
    
    for model_name, module_path in models_to_test:
        try:
            module = __import__(module_path, fromlist=[model_name])
            model_class = getattr(module, model_name)
            print(f"✅ {model_name} imported successfully")
            working_models.append(model_name)
        except Exception as e:
            print(f"❌ {model_name} import failed: {str(e)}")
            failed_models.append((model_name, str(e)))
    
    # Test new models
    print("\n🔍 Testing new models...")
    new_models_to_test = [
        ("Wallet", "models.wallet"),
        ("WalletTransaction", "models.wallet"),
        ("Order", "models.order"),
        ("OrderItem", "models.order"),
    ]
    
    for model_name, module_path in new_models_to_test:
        try:
            module = __import__(module_path, fromlist=[model_name])
            model_class = getattr(module, model_name)
            print(f"✅ {model_name} imported successfully")
            working_models.append(model_name)
        except Exception as e:
            print(f"❌ {model_name} import failed: {str(e)}")
            failed_models.append((model_name, str(e)))
    
    # Summary
    print(f"\n📊 Summary:")
    print(f"✅ Working models: {len(working_models)}")
    print(f"❌ Failed models: {len(failed_models)}")
    
    if failed_models:
        print(f"\n❌ Failed imports:")
        for model_name, error in failed_models:
            print(f"  - {model_name}: {error}")
    
    return len(failed_models) == 0

def test_database_connection():
    """Test database connection and table creation"""
    print("\n🔍 Testing database connection...")
    
    try:
        from extensions import db
        from config import Config
        
        # Create a simple Flask app for testing
        from flask import Flask
        app = Flask(__name__)
        app.config.from_object(Config)
        db.init_app(app)
        
        with app.app_context():
            # Test if we can create tables
            db.create_all()
            print("✅ Database tables created successfully")
            
            # Test if we can query the database
            result = db.session.execute("SELECT 1")
            print("✅ Database query successful")
            
    except Exception as e:
        print(f"❌ Database test failed: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Starting import and database tests...\n")
    
    imports_ok = test_imports()
    db_ok = test_database_connection()
    
    if imports_ok and db_ok:
        print("\n🎉 All tests passed! Your backend should work correctly.")
    else:
        print("\n⚠️ Some tests failed. Check the errors above.")
    
    print("\n✨ Test completed!")
