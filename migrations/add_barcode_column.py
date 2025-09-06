#!/usr/bin/env python3
"""
Migration script to add barcode column to existing products
Run this script to add barcode column and generate barcodes for existing products
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from extensions import db
from models.product import Product
from utils.barcode_generator import generate_unique_barcode

def migrate_add_barcode_column():
    """Add barcode column and generate barcodes for existing products"""
    
    with app.app_context():
        try:
            # Check if barcode column already exists
            inspector = db.inspect(db.engine)
            columns = [column['name'] for column in inspector.get_columns('product')]
            
            if 'barcode' in columns:
                print("Barcode column already exists. Skipping column creation.")
            else:
                # Add barcode column
                print("Adding barcode column to product table...")
                db.engine.execute('ALTER TABLE product ADD COLUMN barcode VARCHAR(50)')
                db.engine.execute('CREATE UNIQUE INDEX ix_product_barcode ON product (barcode)')
                print("Barcode column added successfully.")
            
            # Generate barcodes for existing products that don't have one
            products_without_barcode = Product.query.filter(Product.barcode.is_(None)).all()
            
            if products_without_barcode:
                print(f"Found {len(products_without_barcode)} products without barcodes. Generating barcodes...")
                
                for product in products_without_barcode:
                    try:
                        barcode = generate_unique_barcode()
                        product.barcode = barcode
                        print(f"Generated barcode {barcode} for product {product.id} - {product.pname}")
                    except Exception as e:
                        print(f"Error generating barcode for product {product.id}: {str(e)}")
                        continue
                
                # Commit all changes
                db.session.commit()
                print(f"Successfully generated barcodes for {len(products_without_barcode)} products.")
            else:
                print("All products already have barcodes.")
                
        except Exception as e:
            print(f"Migration failed: {str(e)}")
            db.session.rollback()
            return False
            
    return True

if __name__ == "__main__":
    print("Starting barcode column migration...")
    success = migrate_add_barcode_column()
    
    if success:
        print("Migration completed successfully!")
    else:
        print("Migration failed!")
        sys.exit(1)
