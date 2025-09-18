#!/usr/bin/env python3
"""
Script to add test pincodes for verification
"""

import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def add_test_pincodes():
    """Add test pincodes for verification"""
    print("🚀 Adding test pincodes...")
    
    try:
        from app import app, db
        from models.pincode import Pincode
        
        with app.app_context():
            # Test pincodes - mix of serviceable and non-serviceable
            test_pincodes = [
                ("560001", "Bengaluru", "Karnataka", True),
                ("560002", "Bengaluru", "Karnataka", True),
                ("560003", "Bengaluru", "Karnataka", True),
                ("560004", "Bengaluru", "Karnataka", True),
                ("560005", "Bengaluru", "Karnataka", True),
                ("560006", "Bengaluru", "Karnataka", True),
                ("560007", "Bengaluru", "Karnataka", True),
                ("560008", "Bengaluru", "Karnataka", True),
                ("560009", "Bengaluru", "Karnataka", True),
                ("560010", "Bengaluru", "Karnataka", True),
                ("110001", "New Delhi", "Delhi", True),
                ("110002", "New Delhi", "Delhi", True),
                ("400001", "Mumbai", "Maharashtra", True),
                ("400002", "Mumbai", "Maharashtra", True),
                ("600001", "Chennai", "Tamil Nadu", True),
                ("700001", "Kolkata", "West Bengal", True),
                ("380001", "Ahmedabad", "Gujarat", True),
                ("500001", "Hyderabad", "Telangana", True),
                ("800001", "Patna", "Bihar", False),  # Not serviceable
                ("900001", "Test City", "Test State", False),  # Not serviceable
            ]
            
            added_count = 0
            for code, city, state, is_serviceable in test_pincodes:
                existing = Pincode.query.filter_by(code=code).first()
                if not existing:
                    pincode = Pincode(
                        code=code,
                        city=city,
                        state=state,
                        is_serviceable=is_serviceable
                    )
                    db.session.add(pincode)
                    added_count += 1
                    print(f"✅ Added pincode: {code} ({city}, {state}) - Serviceable: {is_serviceable}")
                else:
                    print(f"ℹ️  Pincode {code} already exists")
            
            db.session.commit()
            print(f"\n✅ Successfully added {added_count} test pincodes!")
            print(f"📊 Total pincodes in database: {Pincode.query.count()}")
            
            # Show some serviceable pincodes for testing
            serviceable_pins = Pincode.query.filter_by(is_serviceable=True).limit(5).all()
            print(f"\n🧪 Test with these serviceable pincodes:")
            for pin in serviceable_pins:
                print(f"   - {pin.code} ({pin.city}, {pin.state})")
            
            non_serviceable_pins = Pincode.query.filter_by(is_serviceable=False).limit(3).all()
            print(f"\n❌ Test with these non-serviceable pincodes:")
            for pin in non_serviceable_pins:
                print(f"   - {pin.code} ({pin.city}, {pin.state})")
                
    except Exception as e:
        print(f"❌ Error adding test pincodes: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    add_test_pincodes()
