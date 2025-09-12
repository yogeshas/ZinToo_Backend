#!/usr/bin/env python3
"""
Test script to verify block/unblock logic
"""
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from extensions import db
from models.customer import Customer
from services.customer_service import set_customer_blocked

def test_block_logic():
    """Test block/unblock logic"""
    with app.app_context():
        try:
            # Get a customer
            customer = Customer.query.first()
            if not customer:
                print("No customers found in database")
                return
            
            print(f"Testing with customer: {customer.id} - {customer.username}")
            print(f"Initial status: {customer.status}")
            
            # Test blocking
            print("\n=== Testing BLOCK ===")
            result = set_customer_blocked(customer.id, True)
            print(f"Block result status: {result.status}")
            
            # Test unblocking
            print("\n=== Testing UNBLOCK ===")
            result = set_customer_blocked(customer.id, False)
            print(f"Unblock result status: {result.status}")
            
            # Test blocking again
            print("\n=== Testing BLOCK again ===")
            result = set_customer_blocked(customer.id, True)
            print(f"Block result status: {result.status}")
            
            print("\nBlock/unblock logic test completed successfully")
            
        except Exception as e:
            print(f"Error during test: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_block_logic()
