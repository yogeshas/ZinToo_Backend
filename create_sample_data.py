#!/usr/bin/env python3
"""
Script to create sample customers and addresses for testing
Run this to populate the database with test data
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_sample_data():
    """Create sample customers and addresses"""
    print("🚀 Creating sample data for testing...")
    print("=" * 50)
    
    try:
        from app import app, db
        from models.customer import Customer
        from models.address import Address
        from models.pincode import Pincode
        
        with app.app_context():
            # Check if data already exists
            customer_count = Customer.query.count()
            address_count = Address.query.count()
            
            if customer_count > 0:
                print(f"ℹ️  Found {customer_count} existing customers")
                if address_count > 0:
                    print(f"ℹ️  Found {address_count} existing addresses")
                    print("✅ Sample data already exists!")
                    return
            
            print("📝 Creating sample customers...")
            
            # Create sample customer 1
            customer1 = Customer(
                username="john_doe",
                email="john.doe@example.com",
                status="active"
            )
            customer1.set_password("password123")
            db.session.add(customer1)
            db.session.flush()  # Get the ID
            
            print(f"✅ Created customer: {customer1.username} (ID: {customer1.id})")
            
            # Create sample customer 2
            customer2 = Customer(
                username="jane_smith",
                email="jane.smith@example.com",
                status="active"
            )
            customer2.set_password("password123")
            db.session.add(customer2)
            db.session.flush()  # Get the ID
            
            print(f"✅ Created customer: {customer2.username} (ID: {customer2.id})")
            
            # Seed pincodes for Bengaluru
            print("📍 Seeding pincodes for Bengaluru...")
            pins = [
                ("560001", "Bengaluru", "Karnataka"),
                ("560002", "Bengaluru", "Karnataka"),
                ("560003", "Bengaluru", "Karnataka"),
                ("560004", "Bengaluru", "Karnataka"),
                ("560006", "Bengaluru", "Karnataka"),
            ]
            for code, city, state in pins:
                if not Pincode.query.filter_by(code=code).first():
                    db.session.add(Pincode(code=code, city=city, state=state, is_serviceable=True))

            print("🏠 Creating sample addresses...")
            
            # Create addresses for customer 1
            address1 = Address(
                uid=customer1.id,
                name="John Doe",
                type="home",
                city="New York",
                state="NY",
                country="USA",
                zip_code="10001"
            )
            db.session.add(address1)
            
            address2 = Address(
                uid=customer1.id,
                name="John Doe",
                type="work",
                city="Brooklyn",
                state="NY",
                country="USA",
                zip_code="11201"
            )
            db.session.add(address2)
            
            # Create address for customer 2
            address3 = Address(
                uid=customer2.id,
                name="Jane Smith",
                type="home",
                city="Los Angeles",
                state="CA",
                country="USA",
                zip_code="90210"
            )
            db.session.add(address3)
            
            # Commit all changes
            db.session.commit()
            
            print("✅ Sample data created successfully!")
            print()
            print("📊 Summary:")
            print(f"   Customers: {Customer.query.count()}")
            print(f"   Addresses: {Address.query.count()}")
            print(f"   Pincodes: {Pincode.query.count()}")
            print()
            print("🔑 Test Credentials:")
            print(f"   Customer 1: {customer1.email} / password123")
            print(f"   Customer 2: {customer2.email} / password123")
            print()
            print("🌐 Test URLs:")
            print(f"   Get customer 1 addresses: GET /api/addresses/customer/{customer1.id}")
            print(f"   Get customer 2 addresses: GET /api/addresses/customer/{customer2.id}")
            print(f"   Get address 1: GET /api/addresses/{address1.id}")
            
    except Exception as e:
        print(f"❌ Error creating sample data: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_sample_data()
