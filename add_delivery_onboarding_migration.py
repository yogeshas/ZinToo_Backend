# add_delivery_onboarding_migration.py
from app import app
from extensions import db
from models.delivery_onboarding import DeliveryOnboarding

def add_delivery_onboarding_table():
    """Add delivery_onboarding table to database"""
    try:
        with app.app_context():
            # Create the table
            db.create_all()
            
            # Check if table exists
            inspector = db.inspect(db.engine)
            if 'delivery_onboarding' in inspector.get_table_names():
                print("✅ Delivery onboarding table created successfully")
            else:
                print("❌ Failed to create delivery onboarding table")
                
    except Exception as e:
        print(f"❌ Error creating delivery onboarding table: {e}")

if __name__ == "__main__":
    add_delivery_onboarding_table()
