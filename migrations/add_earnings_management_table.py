"""
Migration: Add earnings_management table
Created: 2024-09-05
Description: Creates the earnings_management table for salary, bonus, and payout management
"""

from flask import current_app
from extensions import db
import os

def upgrade():
    """Create the earnings_management table"""
    with current_app.app_context():
        # Create the table
        db.create_all()
        print("✅ Created earnings_management table")

def downgrade():
    """Drop the earnings_management table"""
    with current_app.app_context():
        db.drop_all()
        print("❌ Dropped earnings_management table")

if __name__ == "__main__":
    # Run the migration
    from app import app
    with app.app_context():
        upgrade()
