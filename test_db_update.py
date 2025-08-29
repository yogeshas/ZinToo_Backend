#!/usr/bin/env python3
"""
Test script to check database updates
"""
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from extensions import db
from models.customer import Customer

def test_customer_update():
    """Test customer update functionality"""
    with app.app_context():
        try:
            # Get a customer
            customer = Customer.query.first()
            if not customer:
                print("No customers found in database")
                return
            
            print(f"Testing with customer: {customer.id} - {customer.username}")
            print(f"Before update - Status: {customer.status}, Phone: {customer.get_phone_number()}")
            
            # Test status update
            customer.status = "blocked"
            db.session.commit()
            print(f"After status update - Status: {customer.status}")
            
            # Test phone update
            customer.set_phone_number("1234567890")
            db.session.commit()
            print(f"After phone update - Phone: {customer.get_phone_number()}")
            
            # Refresh from database
            db.session.refresh(customer)
            print(f"After refresh - Status: {customer.status}, Phone: {customer.get_phone_number()}")
            
            # Test location update
            customer.set_location("Test Location")
            db.session.commit()
            print(f"After location update - Location: {customer.get_location()}")
            
            print("Database update test completed successfully")
            
        except Exception as e:
            print(f"Error during test: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_customer_update()
