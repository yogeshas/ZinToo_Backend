from extensions import db
from datetime import datetime

class Address(db.Model):
    __tablename__ = "address"
    
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.Integer, db.ForeignKey("customer.id"), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    type = db.Column(db.String(20), nullable=False, default="home")
    address_line1 = db.Column(db.String(200), nullable=True)  # Street address
    address_line2 = db.Column(db.String(200), nullable=True)  # Floor/Apartment
    city = db.Column(db.String(50), nullable=False)
    state = db.Column(db.String(50), nullable=False)
    country = db.Column(db.String(50), nullable=False)
    zip_code = db.Column(db.String(20), nullable=False)
    landmark = db.Column(db.String(100), nullable=True)  # Landmark
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship - commented out to avoid circular import issues
    # customer = db.relationship("Customer", backref="addresses")
    
    def __repr__(self):
        return f"<Address {self.name} for Customer {self.uid}>"
    
    def as_dict(self):
        """Convert address to dictionary"""
        return {
            "id": self.id,
            "uid": self.uid,
            "name": self.name,
            "type": self.type,
            "address_line1": self.address_line1,
            "address_line2": self.address_line2,
            "city": self.city,
            "state": self.state,
            "country": self.country,
            "zip_code": self.zip_code,
            "landmark": self.landmark,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    def validate(self):
        """Validate address data"""
        errors = []
        
        if not self.name or len(self.name.strip()) == 0:
            errors.append("Name is required")
        
        if not self.city or len(self.city.strip()) == 0:
            errors.append("City is required")
        
        if not self.state or len(self.state.strip()) == 0:
            errors.append("State is required")
        
        if not self.country or len(self.country.strip()) == 0:
            errors.append("Country is required")
        
        if not self.zip_code or len(self.zip_code.strip()) == 0:
            errors.append("Zip code is required")
        
        if self.type not in ["home", "work", "other"]:
            errors.append("Type must be home, work, or other")
        
        return errors
