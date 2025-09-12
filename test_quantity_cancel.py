#!/usr/bin/env python3
"""
Test script to verify quantity cancellation and status update
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from extensions import db
from config import Config
from models.order import OrderItem
from services.order_item_service import cancel_individual_product

def test_quantity_cancel():
    """Test quantity cancellation functionality"""
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    
    with app.app_context():
        try:
            # Find an order item to test with
            item = OrderItem.query.first()
            if not item:
                print("❌ No order items found to test")
                return
            
            print(f"Testing with OrderItem ID: {item.id}")
            print(f"Initial status: {item.status}")
            print(f"Initial quantity: {item.quantity}")
            print(f"Initial quantity_cancel: {item.quantity_cancel}")
            
            # Test partial cancellation
            result = cancel_individual_product(
                item_id=item.id,
                customer_id=item.order.customer_id,
                reason="Test cancellation",
                quantity=1,
                cancelled_by="test"
            )
            
            print(f"Cancellation result: {result}")
            
            # Refresh the item
            db.session.refresh(item)
            print(f"After cancellation - Status: {item.status}")
            print(f"After cancellation - Quantity Cancel: {item.quantity_cancel}")
            
        except Exception as e:
            print(f"Error during test: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_quantity_cancel()
