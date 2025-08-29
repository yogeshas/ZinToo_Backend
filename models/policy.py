from extensions import db

class Policy(db.Model):
    __tablename__ = "policy"
    id = db.Column(db.Integer, primary_key=True)
    policy_name = db.Column(db.String(100), nullable=False)
    policy_description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    is_active = db.Column(db.Boolean, default=True)  # Assuming is_active indicates if the policy is currently active

    def __repr__(self):
        return f"<Policy {self.policy_name} ({self.id})>"
