from extensions import db
from datetime import datetime
import json

class Product(db.Model):
    __tablename__ = "product"
    id = db.Column(db.Integer, primary_key=True)
    pname = db.Column(db.String(120), nullable=False)
    pdescription = db.Column(db.Text)
    # Store sizes as JSON string (e.g., {"S": 3, "M": 0, "L": 5})
    size = db.Column(db.String(1000))
    color = db.Column(db.String(20))
    # Store colors as JSON string for new color-based structure
    colors = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    tag = db.Column(db.String(50), nullable=True)
    cid = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=False)
    sid = db.Column(db.Integer, db.ForeignKey('subcategory.id'))
    image = db.Column(db.String(255), nullable=True)
    stock = db.Column(db.Integer, default=0)
    visibility = db.Column(db.Boolean, default=True)
    is_active = db.Column(db.Boolean, default=True)
    quantity = db.Column(db.Integer, default=1)
    is_returnable = db.Column(db.Boolean, default=True)
    is_cod_available = db.Column(db.Boolean, default=True)
    rating = db.Column(db.Float, default=0.0)
    is_featured = db.Column(db.Boolean, default=False)
    is_latest = db.Column(db.Boolean, default=False)
    is_trending = db.Column(db.Boolean, default=False)
    is_new = db.Column(db.Boolean, default=False)
    shared_count = db.Column(db.Integer, default=0)
    discount_value = db.Column(db.Float, default=0.0)
    barcode = db.Column(db.String(50), unique=True, nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    # Relationships
    category = db.relationship("Category", backref="products")
    subcategory = db.relationship(
        "SubCategory",
        back_populates="products",
        foreign_keys=[sid]
    )

    def get_sizes_dict(self):
        """Get sizes as a dictionary with quantity counts"""
        if not self.size:
            return {}
        
        try:
            if isinstance(self.size, str):
                if self.size.strip().startswith("{"):
                    return json.loads(self.size)
                else:
                    # Legacy format support
                    return eval(self.size) if self.size else {}
            elif isinstance(self.size, dict):
                return self.size
            else:
                return {}
        except Exception:
            return {}

    def get_available_sizes(self):
        """Get list of sizes that have stock > 0"""
        sizes = self.get_sizes_dict()
        return [size for size, qty in sizes.items() if qty > 0]

    def get_size_stock(self, size):
        """Get stock quantity for a specific size"""
        sizes = self.get_sizes_dict()
        return sizes.get(size, 0)

    def is_size_available(self, size):
        """Check if a specific size is available"""
        return self.get_size_stock(size) > 0

    def reserve_size(self, size, quantity=1):
        """Reserve/remove quantity from a specific size"""
        if not self.is_size_available(size) or self.get_size_stock(size) < quantity:
            return False, f"Insufficient stock for size {size}"
        
        sizes = self.get_sizes_dict()
        sizes[size] = max(0, sizes[size] - quantity)
        self.size = json.dumps(sizes)
        return True, f"Reserved {quantity} of size {size}"

    def add_size_stock(self, size, quantity=1):
        """Add quantity back to a specific size"""
        sizes = self.get_sizes_dict()
        sizes[size] = sizes.get(size, 0) + quantity
        self.size = json.dumps(sizes)
        return True, f"Added {quantity} to size {size}"

    def get_total_stock(self):
        """Get total stock across all sizes"""
        sizes = self.get_sizes_dict()
        return sum(sizes.values())

    def get_colors_data(self):
        """Get colors data as a list of dictionaries"""
        if not self.colors:
            return []
        
        try:
            if isinstance(self.colors, str):
                return json.loads(self.colors)
            elif isinstance(self.colors, list):
                return self.colors
            else:
                return []
        except Exception:
            return []

    def get_total_stock_from_colors(self):
        """Get total stock from colors structure"""
        colors = self.get_colors_data()
        total = 0
        for color in colors:
            if isinstance(color, dict) and color.get("sizeCounts"):
                total += sum(int(v or 0) for v in color["sizeCounts"].values())
        return total

    def to_dict(self):
        # Build images list from comma-separated storage
        images_list = []
        if self.image:
            images_list = [u.strip() for u in self.image.split(",") if u and u.strip()]

        # Pricing calculation with optional coupon(s) and tax
        original_price = float(self.price or 0)
        final_price = original_price - (original_price * (self.discount_value or 0) / 100)

        # Get sizes information
        sizes_dict = self.get_sizes_dict()
        available_sizes = self.get_available_sizes()
        total_stock = self.get_total_stock()
        
        # Get colors information
        colors_data = self.get_colors_data()
        colors_stock = self.get_total_stock_from_colors()

        result = {
            "id": self.id,
            "pname": self.pname,
            "pdescription": self.pdescription,
            "size": self.size,
            "sizes": sizes_dict,
            "available_sizes": available_sizes,
            "total_stock": total_stock,
            "color": self.color,
            "colors": colors_data,
            "colors_stock": colors_stock,
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
            "barcode": self.barcode,
            "final_price": round(final_price, 2),
            "original_price": round(original_price, 2),
            "category": self.category.category_name if self.category else None,
            "subcategory": self.subcategory.sub_category_name if self.subcategory else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        return result

    def __repr__(self):
        return f"<Product {self.pname} ({self.id})>"
