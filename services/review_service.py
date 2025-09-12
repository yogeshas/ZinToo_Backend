from typing import List, Optional, Dict, Any
from extensions import db
from models.review import ProductReview
from models.product import Product


def _join_urls(urls: Optional[List[str]]) -> Optional[str]:
    if not urls:
        return None
    return ",".join([str(u).strip() for u in urls if str(u).strip()]) or None


def create_review(customer_id: int, data: Dict[str, Any]) -> ProductReview:
    product_id = int(data.get("product_id"))
    rating = int(data.get("rating"))
    if rating < 1 or rating > 5:
        raise ValueError("Rating must be between 1 and 5")

    if not Product.query.get(product_id):
        raise ValueError("Invalid product_id")

    review = ProductReview(
        product_id=product_id,
        customer_id=int(customer_id),
        rating=rating,
        title=data.get("title"),
        content=data.get("content"),
        image_urls=_join_urls(data.get("images")),
        video_urls=_join_urls(data.get("videos")),
        is_verified_purchase=bool(data.get("is_verified_purchase", False)),
        status="approved"
    )
    db.session.add(review)
    db.session.commit()
    _recalculate_product_rating(product_id)
    return review


def list_reviews_for_product(product_id: int, status: Optional[str] = "approved") -> List[ProductReview]:
    q = ProductReview.query.filter_by(product_id=product_id)
    if status:
        q = q.filter_by(status=status)
    return q.order_by(ProductReview.id.desc()).all()


def list_reviews_for_admin(product_id: Optional[int] = None, status: Optional[str] = None) -> List[ProductReview]:
    q = ProductReview.query
    if product_id:
        q = q.filter_by(product_id=product_id)
    if status:
        q = q.filter_by(status=status)
    return q.order_by(ProductReview.id.desc()).all()


def update_review_status(review_id: int, status: str, admin_note: Optional[str] = None) -> Optional[ProductReview]:
    review = ProductReview.query.get(review_id)
    if not review:
        return None
    if status not in ("pending", "approved", "rejected"):
        raise ValueError("Invalid status")
    review.status = status
    if admin_note is not None:
        review.admin_note = admin_note
    db.session.commit()
    _recalculate_product_rating(review.product_id)
    return review


def add_media_to_review(review_id: int, images: Optional[List[str]] = None, videos: Optional[List[str]] = None) -> Optional[ProductReview]:
    review = ProductReview.query.get(review_id)
    if not review:
        return None
    current_images = [u.strip() for u in (review.image_urls or "").split(",") if u.strip()]
    current_videos = [u.strip() for u in (review.video_urls or "").split(",") if u.strip()]
    if images:
        current_images.extend([u for u in images if u.strip()])
    if videos:
        current_videos.extend([u for u in videos if u.strip()])
    review.image_urls = _join_urls(current_images)
    review.video_urls = _join_urls(current_videos)
    db.session.commit()
    return review


def _recalculate_product_rating(product_id: int) -> None:
    try:
        approved = ProductReview.query.with_entities(ProductReview.rating).filter_by(product_id=product_id, status="approved").all()
        if not approved:
            product = Product.query.get(product_id)
            if product:
                product.rating = 0.0
                db.session.commit()
            return
        ratings = [r[0] for r in approved]
        avg = round(sum(ratings) / len(ratings), 2)
        product = Product.query.get(product_id)
        if product:
            product.rating = float(avg)
            db.session.commit()
    except Exception:
        # Likely table doesn't exist yet; ignore to avoid crashing reads
        db.session.rollback()


def get_product_review_stats(product_id: int) -> Dict[str, Any]:
    try:
        q = ProductReview.query.filter_by(product_id=product_id, status="approved")
        total = q.count()
        if total == 0:
            return {"total": 0, "average": 0.0, "breakdown": {str(i): 0 for i in range(1, 6)}}
        breakdown = {}
        for i in range(1, 6):
            breakdown[str(i)] = q.filter_by(rating=i).count()
        avg = round(sum(int(k) * v for k, v in breakdown.items()) / total, 2)
        return {"total": total, "average": avg, "breakdown": breakdown}
    except Exception:
        # Table not ready, return empty stats gracefully
        return {"total": 0, "average": 0.0, "breakdown": {str(i): 0 for i in range(1, 6)}}


