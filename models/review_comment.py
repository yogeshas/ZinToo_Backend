from extensions import db


class ReviewComment(db.Model):
    __tablename__ = "review_comment"

    id = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(db.Integer, db.ForeignKey("product_review.id"), nullable=False, index=True)
    parent_id = db.Column(db.Integer, db.ForeignKey("review_comment.id"), nullable=True, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customer.id"), nullable=True, index=True)
    admin_id = db.Column(db.Integer, db.ForeignKey("admin.id"), nullable=True, index=True)

    author_type = db.Column(db.String(10), nullable=False)  # "customer" | "admin"
    content = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default="approved", index=True)  # approved|pending|rejected

    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    # self-referential relationship
    replies = db.relationship("ReviewComment", backref=db.backref("parent", remote_side=[id]), lazy=True)

    def to_dict(self, include_replies=True):
        # Resolve author name
        author_name = None
        try:
            if self.author_type == "admin" and self.admin_id:
                from models.admin import Admin
                adm = Admin.query.get(self.admin_id)
                author_name = getattr(adm, "username", None) or getattr(adm, "email", None)
            elif self.author_type == "customer" and self.customer_id:
                from models.customer import Customer
                cust = Customer.query.get(self.customer_id)
                author_name = getattr(cust, "username", None) or getattr(cust, "email", None)
        except Exception:
            author_name = None
        data = {
            "id": self.id,
            "review_id": self.review_id,
            "parent_id": self.parent_id,
            "author_type": self.author_type,
            "author_name": author_name,
            "customer_id": self.customer_id,
            "admin_id": self.admin_id,
            "content": self.content,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_replies:
            data["replies"] = [c.to_dict(include_replies=False) for c in self.replies if c.status == "approved"]
        return data


