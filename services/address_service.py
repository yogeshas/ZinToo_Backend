from models.address import Address
from extensions import db

def create_address(uid, data):
    """Create a new address for a customer. 'data' is a dict with keys:
    name, type, city, state, country, zip_code (or zipCode)
    """
    try:
        print(f"[ADDRESS SERVICE] Creating address for uid: {uid}")
        print(f"[ADDRESS SERVICE] Data received: {data}")
        
        # Validate required fields
        required_fields = ["name", "city", "state", "country", "zip_code"]
        for field in required_fields:
            if not data.get(field):
                raise ValueError(f"Field '{field}' is required")
        
        address = Address(
            uid=uid,
            name=data.get("name", "").strip(),
            type=data.get("type", "home"),
            address_line1=data.get("address_line1", "").strip(),
            address_line2=data.get("address_line2", "").strip(),
            city=data.get("city", "").strip(),
            state=data.get("state", "").strip(),
            country=data.get("country", "").strip(),
            zip_code=data.get("zip_code") or data.get("zipCode") or "",
            landmark=data.get("landmark", "").strip(),
        )
        
        print(f"[ADDRESS SERVICE] Address object created: {address}")
        db.session.add(address)
        db.session.commit()
        print(f"[ADDRESS SERVICE] Address saved with ID: {address.id}")
        return address
        
    except Exception as e:
        print(f"[ADDRESS SERVICE] Error creating address: {str(e)}")
        db.session.rollback()
        raise e


def get_addresses_by_customer(uid):
    """Get all addresses for a specific customer"""
    try:
        # Simply return addresses for the given uid without customer validation
        # This avoids potential circular import issues
        return Address.query.filter_by(uid=uid).all()
        
    except Exception as e:
        print(f"Error getting addresses for customer {uid}: {str(e)}")
        raise e


def get_address_by_id(aid):
    """Get a specific address by ID"""
    try:
        address = Address.query.get(aid)
        if not address:
            raise ValueError(f"Address with ID {aid} not found")
        return address
        
    except Exception as e:
        raise e


def update_address(aid, data):
    """Update an existing address"""
    try:
        print(f"[ADDRESS SERVICE] Updating address ID: {aid}")
        print(f"[ADDRESS SERVICE] Update data: {data}")
        
        address = get_address_by_id(aid)
        if not address:
            print(f"[ADDRESS SERVICE] Address {aid} not found")
            return None
        
        # Update allowed fields
        allowed_fields = ["name", "type", "address_line1", "address_line2", "city", "state", "country", "zip_code", "landmark"]
        for field in allowed_fields:
            if field in data and data[field] is not None:
                if field == "zip_code":
                    address.zip_code = str(data[field]).strip()
                else:
                    setattr(address, field, str(data[field]).strip())
                print(f"[ADDRESS SERVICE] Updated field {field} to: {data[field]}")
        
        db.session.commit()
        print(f"[ADDRESS SERVICE] Address {aid} updated successfully")
        return address
        
    except Exception as e:
        print(f"[ADDRESS SERVICE] Error updating address {aid}: {str(e)}")
        db.session.rollback()
        raise e


def delete_address(aid):
    """Delete an address"""
    try:
        print(f"[ADDRESS SERVICE] Deleting address ID: {aid}")
        
        address = get_address_by_id(aid)
        if not address:
            print(f"[ADDRESS SERVICE] Address {aid} not found for deletion")
            return False
        
        db.session.delete(address)
        db.session.commit()
        print(f"[ADDRESS SERVICE] Address {aid} deleted successfully")
        return True
        
    except Exception as e:
        print(f"[ADDRESS SERVICE] Error deleting address {aid}: {str(e)}")
        db.session.rollback()
        raise e


def get_address_count_by_customer(uid):
    """Get the count of addresses for a customer"""
    try:
        return Address.query.filter_by(uid=uid).count()
    except Exception as e:
        raise e
