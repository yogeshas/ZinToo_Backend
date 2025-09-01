#!/usr/bin/env python3
"""
Test script to check exchange table data and relationships
"""

from app import app
from extensions import db
from models.exchange import Exchange
from models.order import Order
from models.customer import Customer
from models.product import Product

def test_exchange_data():
    """Test exchange data and relationships"""
    try:
        with app.app_context():
            print("🔍 Testing Exchange Data...")
            
            # Check if exchange table exists
            inspector = db.inspect(db.engine)
            if 'exchange' not in inspector.get_table_names():
                print("❌ Exchange table does not exist!")
                return
            
            # Get all exchanges
            exchanges = Exchange.query.all()
            print(f"📊 Found {len(exchanges)} exchanges")
            
            if not exchanges:
                print("ℹ️ No exchanges found in database")
                return
            
            # Test first exchange
            exchange = exchanges[0]
            print(f"\n🔍 Testing Exchange ID: {exchange.id}")
            print(f"  - Order ID: {exchange.order_id}")
            print(f"  - Customer ID: {exchange.customer_id}")
            print(f"  - Product ID: {exchange.product_id}")
            print(f"  - Status: {exchange.status}")
            
            # Test order relationship
            print(f"\n📦 Testing Order Relationship:")
            if exchange.order:
                print(f"  ✅ Order found: {exchange.order.order_number}")
                print(f"  - Order status: {exchange.order.status}")
                
                # Test customer through order
                if exchange.order.customer:
                    print(f"  ✅ Customer through order: {exchange.order.customer.username}")
                    print(f"  - Customer email: {exchange.order.customer.email}")
                else:
                    print(f"  ❌ No customer found through order")
            else:
                print(f"  ❌ No order found")
            
            # Test direct customer relationship
            print(f"\n👤 Testing Direct Customer Relationship:")
            if exchange.customer:
                print(f"  ✅ Direct customer: {exchange.customer.username}")
                print(f"  - Customer email: {exchange.customer.email}")
            else:
                print(f"  ❌ No direct customer found")
            
            # Test product relationship
            print(f"\n🛍️ Testing Product Relationship:")
            if exchange.product:
                print(f"  ✅ Product found: {exchange.product.pname}")
                print(f"  - Product price: {exchange.product.price}")
            else:
                print(f"  ❌ No product found")
            
            # Test as_dict method
            print(f"\n📋 Testing as_dict method:")
            exchange_dict = exchange.as_dict()
            print(f"  - Exchange dict keys: {list(exchange_dict.keys())}")
            
            # Test with relationships
            if exchange.order:
                order_dict = exchange.order.as_dict()
                print(f"  - Order dict keys: {list(order_dict.keys())}")
                
                if exchange.order.customer:
                    customer_dict = exchange.order.customer.as_dict()
                    print(f"  - Customer dict keys: {list(customer_dict.keys())}")
                    print(f"  - Customer username: {customer_dict.get('username')}")
                    print(f"  - Customer name field: {customer_dict.get('name')}")
            
            if exchange.product:
                product_dict = exchange.product.to_dict()
                print(f"  - Product dict keys: {list(product_dict.keys())}")
                print(f"  - Product pname: {product_dict.get('pname')}")
                print(f"  - Product name field: {product_dict.get('name')}")
            
            print("\n✅ Exchange data test completed!")
            
    except Exception as e:
        print(f"❌ Error testing exchange data: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_exchange_data()
