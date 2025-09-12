from typing import List, Optional, Dict, Any
from extensions import db
from models.review import ProductReview
from models.review_comment import ReviewComment


def list_comments(review_id: int) -> List[ReviewComment]:
    return ReviewComment.query.filter_by(review_id=review_id, parent_id=None, status="approved").order_by(ReviewComment.id.asc()).all()


def create_comment(author: Dict[str, int], data: Dict[str, Any]) -> ReviewComment:
    review_id = int(data.get("review_id"))
    if not ProductReview.query.get(review_id):
        raise ValueError("Invalid review_id")

    parent_id = int(data.get("parent_id")) if data.get("parent_id") else None
    content = (data.get("content") or "").strip()
    if not content:
        raise ValueError("Content required")

    author_type = data.get("author_type")
    if author_type not in ("customer", "admin"):
        raise ValueError("Invalid author_type")

    comment = ReviewComment(
        review_id=review_id,
        parent_id=parent_id,
        content=content,
        author_type=author_type,
        customer_id=author.get("customer_id") if author_type == "customer" else None,
        admin_id=author.get("admin_id") if author_type == "admin" else None,
        status="approved",
    )
    db.session.add(comment)
    db.session.commit()
    return comment


def moderate_comment(comment_id: int, status: str) -> Optional[ReviewComment]:
    c = ReviewComment.query.get(comment_id)
    if not c:
        return None
    if status not in ("approved", "pending", "rejected"):
        raise ValueError("Invalid status")
    c.status = status
    db.session.commit()
    return c


