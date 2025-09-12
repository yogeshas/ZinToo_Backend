from extensions import db


class Pincode(db.Model):
    __tablename__ = "pincode"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)
    is_serviceable = db.Column(db.Boolean, default=True, index=True)

    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    def to_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "city": self.city,
            "state": self.state,
            "is_serviceable": self.is_serviceable,
        }


