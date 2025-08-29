#!/usr/bin/env python3
"""
Create review-related tables directly using SQLAlchemy metadata.
This safely creates only missing tables and won't drop/alter existing ones.
"""

from app import app
from extensions import db
from models.review import ProductReview
from models.review_comment import ReviewComment
from models.pincode import Pincode


def create_tables():
    with app.app_context():
        ProductReview.__table__.create(bind=db.engine, checkfirst=True)
        ReviewComment.__table__.create(bind=db.engine, checkfirst=True)
        Pincode.__table__.create(bind=db.engine, checkfirst=True)
        print("✅ Ensured product_review, review_comment, and pincode tables exist")


if __name__ == "__main__":
    create_tables()


