from extensions import db

class Widget(db.Model):
    __tablename__ = "widget"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    title = db.Column(db.String(100), nullable=True)  # Widget title for specific positioning
    type = db.Column(db.String(20), nullable=False, default="default")
    description = db.Column(db.String(200), nullable=True)
    page = db.Column(db.String(50), nullable=False, default="home")
    images = db.Column(db.Text, nullable=True)  # JSON or text representation of images
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<Widget {self.name} of type {self.type} on page {self.page}>"
