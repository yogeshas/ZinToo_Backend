from extensions import db

class Coupon(db.Model):
    __tablename__ = "coupon"
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    discount_type = db.Column(db.String(20), nullable=False)  # e.g., 'percentage', 'fixed'
    discount_value = db.Column(db.Float, nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    description = db.Column(db.String(200), nullable=True)
    min_order_amount = db.Column(db.Float, default=0.0)
    max_discount_amount = db.Column(db.Float, nullable=True)
    usage_limit = db.Column(db.Integer, nullable=True)
    used_count = db.Column(db.Integer, default=0)
    
    # Target fields for applying coupons
    target_type = db.Column(db.String(20), nullable=False, default='all')  # 'all', 'category', 'subcategory', 'product'
    target_category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=True)
    target_subcategory_id = db.Column(db.Integer, db.ForeignKey("subcategory.id"), nullable=True)
    target_product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=True)
    
    # Relationships
    target_category = db.relationship("Category", foreign_keys=[target_category_id])
    target_subcategory = db.relationship("SubCategory", foreign_keys=[target_subcategory_id])
    target_product = db.relationship("Product", foreign_keys=[target_product_id])
    
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    def __repr__(self):
        return f"<Coupon {self.code}>"
