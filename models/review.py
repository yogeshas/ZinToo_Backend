from datetime import datetime
from extensions import db


class ProductReview(db.Model):
    __tablename__ = "product_review"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customer.id"), nullable=False, index=True)

    rating = db.Column(db.Integer, nullable=False)  # 1..5
    title = db.Column(db.String(200), nullable=True)
    content = db.Column(db.Text, nullable=True)

    # Comma-separated URLs for images and videos (served via routes)
    image_urls = db.Column(db.Text, nullable=True)
    video_urls = db.Column(db.Text, nullable=True)

    is_verified_purchase = db.Column(db.Boolean, default=False)

    # moderation
    status = db.Column(db.String(20), default="pending", index=True)  # pending|approved|rejected
    admin_note = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    product = db.relationship("Product", backref="reviews", lazy=True)

    def to_dict(self):
        images = []
        videos = []
        if self.image_urls:
            images = [u.strip() for u in self.image_urls.split(",") if u and u.strip()]
        if self.video_urls:
            videos = [u.strip() for u in self.video_urls.split(",") if u and u.strip()]
        # Resolve author name lazily to avoid hard relationship requirement
        author_name = None
        try:
            from models.customer import Customer
            cust = Customer.query.get(self.customer_id) if self.customer_id else None
            if cust:
                author_name = getattr(cust, "username", None) or getattr(cust, "email", None)
        except Exception:
            author_name = None
        return {
            "id": self.id,
            "product_id": self.product_id,
            "customer_id": self.customer_id,
            "author_name": author_name,
            "rating": self.rating,
            "title": self.title,
            "content": self.content,
            "images": images,
            "videos": videos,
            "is_verified_purchase": self.is_verified_purchase,
            "status": self.status,
            "admin_note": self.admin_note,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


