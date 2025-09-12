# models/delivery_onboarding.py
from extensions import db
from datetime import datetime

class DeliveryOnboarding(db.Model):
    __tablename__ = "delivery_onboarding"
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Personal Information
    first_name = db.Column(db.String(100), nullable=True)  # Make nullable for initial creation
    last_name = db.Column(db.String(100), nullable=True)  # Make nullable for initial creation
    dob = db.Column(db.Date, nullable=True)  # Make dob nullable since it's filled during onboarding
    email = db.Column(db.String(120), nullable=True)  # Make email optional, not unique
    primary_number = db.Column(db.String(20), nullable=True, unique=True)  # Make nullable for initial creation
    secondary_number = db.Column(db.String(20), nullable=True)
    blood_group = db.Column(db.String(10), nullable=True)
    address = db.Column(db.Text, nullable=True)  # Make nullable for initial creation
    language = db.Column(db.String(50), default="English")
    profile_picture = db.Column(db.String(500), nullable=True)
    referral_code = db.Column(db.String(50), nullable=True)
    
    # Identity Documents
    aadhar_card = db.Column(db.String(12), nullable=True, unique=True)  # Make nullable for initial creation
    pan_card = db.Column(db.String(10), nullable=True, unique=True)  # Make nullable for initial creation
    dl = db.Column(db.String(20), nullable=True, unique=True)  # Driving License - Make nullable for initial creation
    
    # Vehicle Information
    vehicle_number = db.Column(db.String(20), nullable=True, unique=True)  # Make nullable for initial creation
    rc_card = db.Column(db.String(500), nullable=True)  # RC Card image path
    
    # Bank Information
    bank_account_number = db.Column(db.String(50), nullable=True)  # Make nullable for initial creation
    ifsc_code = db.Column(db.String(20), nullable=True)  # Make nullable for initial creation
    bank_passbook = db.Column(db.String(500), nullable=True)  # Passbook image path
    name_as_per_bank = db.Column(db.String(100), nullable=True)
    
    # Status and Relationships
    status = db.Column(db.String(20), default="pending")  # pending, document_submitted, profile_complete, approved, rejected
    
    # Document Submission Status
    profile_submitted = db.Column(db.Boolean, default=False)
    documents_submitted = db.Column(db.Boolean, default=False)
    vehicle_docs_submitted = db.Column(db.Boolean, default=False)
    bank_docs_submitted = db.Column(db.Boolean, default=False)
    
    # Verification Status
    profile_verified = db.Column(db.Boolean, default=False)
    documents_verified = db.Column(db.Boolean, default=False)
    vehicle_verified = db.Column(db.Boolean, default=False)
    bank_verified = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Admin notes
    admin_notes = db.Column(db.Text, nullable=True)
    approved_by = db.Column(db.Integer, db.ForeignKey("admin.id"), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    
    # Delivery Guy ID - Links to the delivery guy system
    delivery_guy_id = db.Column(db.Integer, nullable=True)
    
    # Relationships
    delivery_loyalties = db.relationship("Delivery_Loyalty", back_populates="delivery_user")

    def __repr__(self):
        return f"<DeliveryOnboarding {self.first_name} {self.last_name} - {self.primary_number}>"

    def as_dict(self):
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": f"{self.first_name} {self.last_name}",
            "dob": self.dob.isoformat() if self.dob else None,
            "email": self.email,
            "primary_number": self.primary_number,
            "secondary_number": self.secondary_number,
            "blood_group": self.blood_group,
            "address": self.address,
            "language": self.language,
            "profile_picture": self.profile_picture,
            "referral_code": self.referral_code,
            "aadhar_card": self.aadhar_card,
            "pan_card": self.pan_card,
            "dl": self.dl,
            "vehicle_number": self.vehicle_number,
            "rc_card": self.rc_card,
            "bank_account_number": self.bank_account_number,
            "ifsc_code": self.ifsc_code,
            "bank_passbook": self.bank_passbook,
            "name_as_per_bank": self.name_as_per_bank,
            "status": self.status,
            "profile_submitted": self.profile_submitted,
            "documents_submitted": self.documents_submitted,
            "vehicle_docs_submitted": self.vehicle_docs_submitted,
            "bank_docs_submitted": self.bank_docs_submitted,
            "profile_verified": self.profile_verified,
            "documents_verified": self.documents_verified,
            "vehicle_verified": self.vehicle_verified,
            "bank_verified": self.bank_verified,
            "admin_notes": self.admin_notes,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "delivery_guy_id": self.delivery_guy_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def update_status(self, new_status, admin_id=None, notes=None):
        """Update onboarding status"""
        self.status = new_status
        self.updated_at = datetime.utcnow()
        
        if new_status == "approved":
            self.approved_by = admin_id
            self.approved_at = datetime.utcnow()
        
        if notes:
            self.admin_notes = notes
            
        db.session.commit()

    def is_ready_for_approval(self):
        """Check if onboarding is ready for approval"""
        return (
            self.profile_submitted and
            self.documents_submitted and
            self.vehicle_docs_submitted and
            self.bank_docs_submitted
        )

    def get_completion_percentage(self):
        """Get completion percentage of onboarding"""
        completed = 0
        total = 4
        
        if self.profile_submitted:
            completed += 1
        if self.documents_submitted:
            completed += 1
        if self.vehicle_docs_submitted:
            completed += 1
        if self.bank_docs_submitted:
            completed += 1
            
        return (completed / total) * 100

    def get_status_display(self):
        """Get human-readable status display"""
        if self.status == "approved":
            return "Approved"
        elif self.status == "rejected":
            return "Rejected"
        elif self.is_ready_for_approval():
            return "Ready for Approval"
        elif self.get_completion_percentage() >= 75:
            return "Almost Complete"
        elif self.get_completion_percentage() >= 50:
            return "In Progress"
        else:
            return "Started"
