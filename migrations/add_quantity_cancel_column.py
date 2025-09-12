#!/usr/bin/env python3
"""
Migration to add quantity_cancel column to order_item table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from extensions import db
from config import Config

def add_quantity_cancel_column():
    """Add quantity_cancel column to order_item table"""
    try:
        # Check if column already exists
        with db.engine.connect() as connection:
            result = connection.execute(db.text("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'order_item' 
                AND COLUMN_NAME = 'quantity_cancel'
            """))
            
            if result.fetchone():
                print("✅ quantity_cancel column already exists in order_item table")
                return True
            
            # Add the column with default value 0
            connection.execute(db.text("""
                ALTER TABLE order_item 
                ADD COLUMN quantity_cancel INTEGER DEFAULT 0 NOT NULL
            """))
            connection.commit()
        print("✅ Successfully added quantity_cancel column to order_item table")
        return True
    except Exception as e:
        if "Duplicate column name" in str(e):
            print("✅ quantity_cancel column already exists in order_item table")
            return True
        print(f"❌ Error adding quantity_cancel column: {e}")
        return False

if __name__ == "__main__":
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    
    with app.app_context():
        add_quantity_cancel_column()
