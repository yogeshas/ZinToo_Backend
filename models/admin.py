# models/admin.py
from extensions import db
from passlib.context import CryptContext
import os

# Define hashing schemes (secure)
pwd_context = CryptContext(
    schemes=["bcrypt"],   # ✅ simpler & secure, stick to one
    deprecated="auto"
)

class Admin(db.Model):
    __tablename__ = "admin"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)  # shorter is enough
    status = db.Column(db.String(32), default="active")

    # ✅ Hash password before storing
    def set_password(self, password: str):
        self.password_hash = pwd_context.hash(password)

    # ✅ Verify password against hash
    def check_password(self, password: str) -> bool:
        try:
            return pwd_context.verify(password, self.password_hash)
        except Exception:
            return False

    def as_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "status": self.status,
        }


# ✅ Create default admin on boot if missing
def create_default_admin():
    try:
        # Check if any admin exists
        existing_admin = Admin.query.first()
        if existing_admin:
            print(f"ℹ️ Admin already exists: {existing_admin.username} ({existing_admin.email})")
            # Do not reset password on subsequent runs
            return

        # Create admin with your email
        admin_email = "hatchybyte@gmail.com"
        admin_username = "hatchybyte"
        admin_password = "zintoo@1234"

        admin = Admin(
            username=admin_username,
            email=admin_email,
            status="active"
        )
        admin.set_password(admin_password)
        db.session.add(admin)
        db.session.commit()
        print(f"✅ Admin created: {admin_username} ({admin_email})")
        
    except Exception as e:
        print(f"⚠️ Error creating admin: {str(e)}")
        db.session.rollback()
