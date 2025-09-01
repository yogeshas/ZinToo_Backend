#!/usr/bin/env python3
"""
Remove Foreign Key Constraint Script

This script removes the foreign key constraint that's preventing
delivery_guy_id updates in the delivery_guy_auth table.
"""

from extensions import db

def remove_foreign_key_constraint():
    """Remove the foreign key constraint from delivery_guy_auth table"""
    try:
        print("🔧 Removing foreign key constraint...")
        
        # Remove the foreign key constraint
        from sqlalchemy import text
        db.session.execute(text("ALTER TABLE delivery_guy_auth DROP FOREIGN KEY delivery_guy_auth_ibfk_1"))
        db.session.commit()
        
        print("✅ Foreign key constraint removed successfully!")
        
        # Verify the constraint is gone
        result = db.session.execute(text("""
            SELECT CONSTRAINT_NAME 
            FROM information_schema.KEY_COLUMN_USAGE 
            WHERE TABLE_SCHEMA = 'zintoo' 
            AND TABLE_NAME = 'delivery_guy_auth' 
            AND COLUMN_NAME = 'delivery_guy_id'
        """))
        
        constraints = result.fetchall()
        if not constraints:
            print("✅ No foreign key constraints found on delivery_guy_id column")
        else:
            print(f"⚠️ Found constraints: {constraints}")
            
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error removing foreign key constraint: {e}")
        raise

if __name__ == "__main__":
    print("🚀 Remove Foreign Key Constraint Script")
    print("=" * 40)
    
    try:
        # Import and create Flask app context
        from app import app
        
        with app.app_context():
            remove_foreign_key_constraint()
            print("\n✅ Script completed successfully!")
    except Exception as e:
        print(f"\n❌ Script failed: {e}")
        exit(1)
