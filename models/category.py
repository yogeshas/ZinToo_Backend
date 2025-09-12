from extensions import db

class Category(db.Model):
    __tablename__ = "category"
    id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(80), nullable=False)
    category_count = db.Column(db.Integer, default=0)
    image = db.Column(db.String(255), nullable=True)  # Store image path
    subcategories = db.relationship(
        "SubCategory",
        backref="category",
        lazy=True,
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Category {self.category_name}>"
