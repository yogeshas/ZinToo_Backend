#!/usr/bin/env python3
"""
Migration script to add cart and wishlist tables
Run this script to create the new tables in your database
"""

from app import create_app, db
from models.cart import Cart
from models.wishlist import Wishlist

def migrate_cart_wishlist():
    """Create cart and wishlist tables"""
    app = create_app()
    
    with app.app_context():
        try:
            print("Creating cart and wishlist tables...")
            
            # Create the tables
            db.create_all()
            
            print("✅ Cart and wishlist tables created successfully!")
            print("Tables created:")
            print("  - cart")
            print("  - wishlist")
            
        except Exception as e:
            print(f"❌ Error creating tables: {str(e)}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    migrate_cart_wishlist()
