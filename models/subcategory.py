from extensions import db

class SubCategory(db.Model):
    __tablename__ = "subcategory"
    id = db.Column(db.Integer, primary_key=True)
    sub_category_name = db.Column(db.String(80), nullable=False)
    cid = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=False)
    sub_category_count = db.Column(db.Integer, default=0)
    products = db.relationship(
        "Product",
        back_populates="subcategory",
        foreign_keys="[Product.sid]"
    )
