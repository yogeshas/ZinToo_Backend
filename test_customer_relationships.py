#!/usr/bin/env python3
"""
Test script to verify customer relationships are working correctly
"""
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from extensions import db
from models.customer import Customer
from models.order import Order
from models.wallet import Wallet

def test_customer_relationships():
    """Test customer relationships"""
    
    with app.app_context():
        try:
            # Get a customer
            customer = Customer.query.first()
            if not customer:
                print("❌ No customers found in database")
                return
            
            print(f"✅ Found customer: {customer.id} - {customer.username}")
            
            # Test orders relationship
            print(f"🔍 Testing orders relationship...")
            if hasattr(customer, 'orders'):
                print(f"✅ Customer has orders relationship")
                try:
                    orders = list(customer.orders)
                    print(f"✅ Found {len(orders)} orders")
                    
                    for order in orders:
                        print(f"  - Order {order.id}: {order.order_number} (₹{order.total_amount})")
                        
                        # Test order items
                        if hasattr(order, 'order_items'):
                            items = list(order.order_items)
                            print(f"    - {len(items)} items")
                            
                except Exception as e:
                    print(f"❌ Error accessing orders: {e}")
            else:
                print(f"❌ Customer does not have orders relationship")
            
            # Test wallet relationship
            print(f"🔍 Testing wallet relationship...")
            if hasattr(customer, 'wallet'):
                print(f"✅ Customer has wallet relationship")
                wallet = customer.wallet
                if wallet:
                    print(f"✅ Customer has wallet: {wallet.id}")
                else:
                    print(f"ℹ️ Customer has no wallet")
            else:
                print(f"❌ Customer does not have wallet relationship")
            
            # Test as_dict method
            print(f"🔍 Testing as_dict method...")
            try:
                customer_dict = customer.as_dict()
                print(f"✅ as_dict works: {list(customer_dict.keys())}")
            except Exception as e:
                print(f"❌ Error in as_dict: {e}")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_customer_relationships()
