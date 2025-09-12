from extensions import db

class DeliveryUsers(db.Model):
    __tablename__ = "deliveryusers"
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    blood_group = db.Column(db.String(10), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    language = db.Column(db.String(50), nullable=False)
    refferral_code = db.Column(db.String(50), unique=True, nullable=True)
    refferral_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default="active")
    aadhaar_photo = db.Column(db.String(20), unique=True, nullable=False)
    pan_photo = db.Column(db.String(20), unique=True, nullable=False)
    vehicle_number = db.Column(db.String(50), nullable=False)
    rc_card_photo = db.Column(db.String(20), unique=True, nullable=False)
    license_photo = db.Column(db.String(20), unique=True, nullable=False)
    passbook_photo = db.Column(db.String(20), unique=True, nullable=False)
    bank_name = db.Column(db.String(50), nullable=False)
    account_number = db.Column(db.String(50), nullable=False)
    ifsc_code = db.Column(db.String(20), nullable=False)
    name_as_per_bank = db.Column(db.String(100), nullable=False)
    contact_number_1 = db.Column(db.String(20), nullable=False)
    contact_number_2 = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    delivery_loyalties = db.relationship("Delivery_Loyalty", back_populates="delivery_user")
    # Relationship to Order
    orders = db.relationship("Order", back_populates="delivery_user")
    payouts = db.relationship("Payout", back_populates="delivery_user")

    def __repr__(self):
        return f"<DeliveryUser {self.name} with ID {self.id}>"
