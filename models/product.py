from extensions import db
from datetime import datetime

class Product(db.Model):
    __tablename__ = "product"
    id = db.Column(db.Integer, primary_key=True)
    pname = db.Column(db.String(120), nullable=False)
    pdescription = db.Column(db.Text)
    # Store sizes as JSON string (e.g., {"S": 3, "M": 0}) or CSV for legacy
    size = db.Column(db.String(1000))
    color = db.Column(db.String(20))
    price = db.Column(db.Float, nullable=False)
    tag = db.Column(db.String(50), nullable=True)
    cid = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=False)
    sid = db.Column(db.Integer, db.ForeignKey('subcategory.id'))  # <-- Make sure this matches the correct table name
    image = db.Column(db.String(255), nullable=True)  # Assuming image is a string path to the image file
    stock = db.Column(db.Integer, default=0)  # Assuming stock is an integer count of available items
    visibility = db.Column(db.Boolean, default=True)  # Assuming visibility is a boolean flag
    is_active = db.Column(db.Boolean, default=True)  # Assuming is_active indicates if the product is active
    quantity = db.Column(db.Integer, default=1)  # Assuming quantity is the number of items in stock
   
   
    is_returnable = db.Column(db.Boolean, default=True)  # Assuming is_returnable indicates if the product can be returned
    is_cod_available = db.Column(db.Boolean, default=True)  
    rating = db.Column(db.Float, default=0.0)
    is_featured = db.Column(db.Boolean, default=False)
    is_latest = db.Column(db.Boolean, default=False)
    is_trending = db.Column(db.Boolean, default=False)
    is_new = db.Column(db.Boolean, default=False)
    shared_count = db.Column(db.Integer, default=0)
    discount_value = db.Column(db.Float, default=0.0)
    # comments = db.relationship("Comment", backref="product", lazy=True)
    # reviews = db.relationship("Review", backref="product", lazy=True)
    # orders = db.relationship("Order", backref="product", lazy=True)
    # carts = db.relationship("Cart", backref="product", lazy=True)
    # wishlists = db.relationship("Wishlist", backref="product", lazy=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    # Define relationships if needed, e.g., with Category and SubCategory
    category = db.relationship("Category", backref="products")
    

    subcategory = db.relationship(
        "SubCategory",
        back_populates="products",
        foreign_keys=[sid]
    )
    def to_dict(self):
        # Build images list from comma-separated storage
        images_list = []
        if self.image:
            images_list = [u.strip() for u in self.image.split(",") if u and u.strip()]

        # Pricing calculation with optional coupon(s) and tax
        original_price = float(self.price or 0)
        final_price = original_price - (original_price * (self.discount_value or 0) / 100)

        

        result = {
            "id": self.id,
            "pname": self.pname,
            "pdescription": self.pdescription,
            "size": self.size,
            "color": self.color,
            "price": self.price,
            "tag": self.tag,
            "cid": self.cid,
            "sid": self.sid,
            "image": self.image,
            "images": images_list,
            "stock": self.stock,
            "visibility": self.visibility,
            "is_active": self.is_active,
            "quantity": self.quantity,
            "discount_value": self.discount_value,
            "is_returnable": self.is_returnable,
            "is_cod_available": self.is_cod_available,
            "rating": self.rating,
            "is_featured": self.is_featured,
            "is_latest": self.is_latest,
            "is_trending": self.is_trending,
            "is_new": self.is_new,
            "shared_count": self.shared_count,
            "final_price": round(final_price, 2),
            "original_price": round(original_price, 2),
            "category": self.category.category_name if self.category else None,
            "subcategory": self.subcategory.sub_category_name if self.subcategory else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        # Attempt to expose structured sizes map if JSON stored
        try:
            if self.size and self.size.strip().startswith("{"):
                import json as _json
                result["sizes"] = _json.loads(self.size)
        except Exception:
            pass
        return result
    def __repr__(self):
        return f"<Product {self.pname} ({self.id})>"
