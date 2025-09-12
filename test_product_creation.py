#!/usr/bin/env python3
"""
Test script for product creation with barcode generation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from services.product_service import create_product
from utils.crypto import encrypt_payload

def test_product_creation():
    """Test product creation with barcode generation"""
    
    print("Testing product creation...")
    
    # Test data similar to what frontend sends
    test_data = {
        "pname": "Test Product",
        "pdescription": "Test product description",
        "size": {"S": 5, "M": 10, "L": 3},
        "color": "Red",
        "price": 99.99,
        "tag": "test",
        "cid": 1,  # Assuming category 1 exists
        "sid": None,
        "stock": 18,
        "visibility": True,
        "is_active": True,
        "quantity": 18,
        "is_returnable": True,
        "is_cod_available": True,
        "rating": 0,
        "is_featured": False,
        "is_latest": False,
        "is_trending": False,
        "is_new": False,
        "shared_count": 0,
        "discount_value": 0,
        "images": []
    }
    
    with app.app_context():
        try:
            print("Creating product with test data...")
            product = create_product(test_data)
            print(f"✅ Product created successfully!")
            print(f"Product ID: {product.id}")
            print(f"Product Name: {product.pname}")
            print(f"Barcode: {product.barcode}")
            print(f"Price: {product.price}")
            print(f"Stock: {product.stock}")
            
            return True
            
        except Exception as e:
            print(f"❌ Product creation failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = test_product_creation()
    if not success:
        sys.exit(1)
    else:
        print("\n🎉 Product creation test passed!")
