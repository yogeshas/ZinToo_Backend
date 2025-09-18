#!/usr/bin/env python3
"""
S3 Asset Migration Script
This script migrates all local assets to S3 and updates database references.
"""

import os
import sys
import json
from pathlib import Path
from utils.s3_service import S3Service
from models.product import Product
from models.category import Category
from models.review import ProductReview
from models.widget import Widget
from models.delivery_onboarding import DeliveryOnboarding
from extensions import db
from app import app

def migrate_assets_to_s3():
    """Migrate all local assets to S3 and update database references"""
    with app.app_context():
        try:
            # Initialize S3 service
            s3_service = S3Service()
            print("✅ S3 service initialized successfully")
            
            # Migration counters
            migrated_count = 0
            error_count = 0
            
            # 1. Migrate Category Images
            print("\n🔄 Migrating Category Images...")
            categories = Category.query.all()
            for category in categories:
                if category.image and not category.image.startswith('http'):
                    try:
                        # Check if local file exists
                        local_path = os.path.join('assets', 'category', category.image)
                        if os.path.exists(local_path):
                            # Upload to S3
                            with open(local_path, 'rb') as f:
                                s3_url = s3_service.upload_file(f, "category", "image", "category")
                                if s3_url:
                                    category.image = s3_url
                                    migrated_count += 1
                                    print(f"✅ Migrated category {category.id}: {category.image}")
                                else:
                                    print(f"❌ Failed to upload category {category.id}")
                                    error_count += 1
                        else:
                            print(f"⚠️ Local file not found for category {category.id}: {local_path}")
                    except Exception as e:
                        print(f"❌ Error migrating category {category.id}: {str(e)}")
                        error_count += 1
            
            # 2. Migrate Product Images
            print("\n🔄 Migrating Product Images...")
            products = Product.query.all()
            for product in products:
                if product.image and not product.image.startswith('http'):
                    try:
                        # Handle comma-separated images
                        image_urls = [img.strip() for img in product.image.split(',') if img.strip()]
                        migrated_urls = []
                        
                        for img_url in image_urls:
                            local_path = os.path.join('assets', 'img', 'products', img_url)
                            if os.path.exists(local_path):
                                with open(local_path, 'rb') as f:
                                    s3_url = s3_service.upload_file(f, "product", "image", "product")
                                    if s3_url:
                                        migrated_urls.append(s3_url)
                                    else:
                                        migrated_urls.append(img_url)  # Keep original if upload fails
                            else:
                                migrated_urls.append(img_url)  # Keep original if file not found
                        
                        product.image = ','.join(migrated_urls)
                        migrated_count += 1
                        print(f"✅ Migrated product {product.id}: {len(migrated_urls)} images")
                        
                    except Exception as e:
                        print(f"❌ Error migrating product {product.id}: {str(e)}")
                        error_count += 1
            
            # 3. Migrate Review Media
            print("\n🔄 Migrating Review Media...")
            reviews = ProductReview.query.all()
            for review in reviews:
                if review.image_urls and not review.image_urls.startswith('http'):
                    try:
                        # Handle JSON array of image URLs
                        image_urls = json.loads(review.image_urls) if isinstance(review.image_urls, str) else review.image_urls
                        migrated_urls = []
                        
                        for img_url in image_urls:
                            if not img_url.startswith('http'):
                                local_path = os.path.join('assets', 'img', 'review_media', img_url)
                                if os.path.exists(local_path):
                                    with open(local_path, 'rb') as f:
                                        s3_url = s3_service.upload_file(f, "review", "image", "review")
                                        if s3_url:
                                            migrated_urls.append(s3_url)
                                        else:
                                            migrated_urls.append(img_url)
                                else:
                                    migrated_urls.append(img_url)
                            else:
                                migrated_urls.append(img_url)
                        
                        review.image_urls = json.dumps(migrated_urls)
                        migrated_count += 1
                        print(f"✅ Migrated review {review.id}: {len(migrated_urls)} images")
                        
                    except Exception as e:
                        print(f"❌ Error migrating review {review.id}: {str(e)}")
                        error_count += 1
                
                # Migrate video URLs
                if review.video_urls and not review.video_urls.startswith('http'):
                    try:
                        video_urls = json.loads(review.video_urls) if isinstance(review.video_urls, str) else review.video_urls
                        migrated_urls = []
                        
                        for video_url in video_urls:
                            if not video_url.startswith('http'):
                                local_path = os.path.join('assets', 'img', 'review_media', video_url)
                                if os.path.exists(local_path):
                                    with open(local_path, 'rb') as f:
                                        s3_url = s3_service.upload_file(f, "video", "video", "review")
                                        if s3_url:
                                            migrated_urls.append(s3_url)
                                        else:
                                            migrated_urls.append(video_url)
                                else:
                                    migrated_urls.append(video_url)
                            else:
                                migrated_urls.append(video_url)
                        
                        review.video_urls = json.dumps(migrated_urls)
                        migrated_count += 1
                        print(f"✅ Migrated review {review.id}: {len(migrated_urls)} videos")
                        
                    except Exception as e:
                        print(f"❌ Error migrating review {review.id} videos: {str(e)}")
                        error_count += 1
            
            # 4. Migrate Widget Images
            print("\n🔄 Migrating Widget Images...")
            widgets = Widget.query.all()
            for widget in widgets:
                if widget.images:
                    try:
                        # Parse existing images (JSON array)
                        image_paths = json.loads(widget.images) if isinstance(widget.images, str) else widget.images
                        migrated_urls = []
                        
                        for image_path in image_paths:
                            if not image_path or image_path.startswith('http'):
                                migrated_urls.append(image_path)
                                continue
                                
                            local_path = os.path.join('assets', 'img', 'widgets', os.path.basename(image_path))
                            if os.path.exists(local_path):
                                with open(local_path, 'rb') as f:
                                    s3_url = s3_service.upload_file(f, widget.id, "image", "widget")
                                    if s3_url:
                                        migrated_urls.append(s3_url)
                                        print(f"✅ Migrated widget {widget.id} image: {image_path} -> {s3_url}")
                                    else:
                                        migrated_urls.append(image_path)  # Keep original if upload fails
                            else:
                                migrated_urls.append(image_path)  # Keep original if file not found
                                print(f"⚠️ Local file not found for widget {widget.id}: {local_path}")
                        
                        # Update widget with migrated URLs
                        widget.images = json.dumps(migrated_urls)
                        migrated_count += 1
                        print(f"✅ Updated widget {widget.id} with {len(migrated_urls)} images")
                        
                    except Exception as e:
                        print(f"❌ Error migrating widget {widget.id}: {str(e)}")
                        error_count += 1
            
            # 5. Migrate Delivery Onboarding Documents
            print("\n🔄 Migrating Delivery Onboarding Documents...")
            delivery_guys = DeliveryOnboarding.query.all()
            for guy in delivery_guys:
                # Migrate profile photo
                if guy.profile_photo and not guy.profile_photo.startswith('http'):
                    try:
                        local_path = os.path.join('assets', 'onboarding', 'profile', guy.profile_photo)
                        if os.path.exists(local_path):
                            with open(local_path, 'rb') as f:
                                s3_url = s3_service.upload_file(f, "document", "image", "onboarding")
                                if s3_url:
                                    guy.profile_photo = s3_url
                                    migrated_count += 1
                                    print(f"✅ Migrated delivery guy {guy.id} profile photo")
                                else:
                                    print(f"❌ Failed to upload delivery guy {guy.id} profile photo")
                                    error_count += 1
                        else:
                            print(f"⚠️ Local file not found for delivery guy {guy.id} profile photo")
                    except Exception as e:
                        print(f"❌ Error migrating delivery guy {guy.id} profile photo: {str(e)}")
                        error_count += 1
                
                # Migrate documents
                if guy.documents:
                    try:
                        documents = json.loads(guy.documents) if isinstance(guy.documents, str) else guy.documents
                        migrated_docs = []
                        
                        for doc in documents:
                            if not doc.get('url', '').startswith('http'):
                                local_path = os.path.join('assets', 'onboarding', 'documents', doc['url'])
                                if os.path.exists(local_path):
                                    with open(local_path, 'rb') as f:
                                        s3_url = s3_service.upload_file(f, "document", "document", "onboarding")
                                        if s3_url:
                                            doc['url'] = s3_url
                                        migrated_docs.append(doc)
                                else:
                                    migrated_docs.append(doc)
                            else:
                                migrated_docs.append(doc)
                        
                        guy.documents = json.dumps(migrated_docs)
                        migrated_count += 1
                        print(f"✅ Migrated delivery guy {guy.id} documents")
                        
                    except Exception as e:
                        print(f"❌ Error migrating delivery guy {guy.id} documents: {str(e)}")
                        error_count += 1
            
            # Commit all changes
            db.session.commit()
            print(f"\n✅ Migration completed!")
            print(f"📊 Statistics:")
            print(f"   - Successfully migrated: {migrated_count} assets")
            print(f"   - Errors encountered: {error_count} assets")
            print(f"   - All database references updated to S3 URLs")
            
        except Exception as e:
            print(f"❌ Migration failed: {str(e)}")
            db.session.rollback()
            return False
    
    return True

def cleanup_local_assets():
    """Clean up local assets after successful migration"""
    try:
        import shutil
        
        # Define asset directories to clean up
        asset_dirs = [
            'assets/category',
            'assets/img/products',
            'assets/img/review_media',
            'assets/img/widgets',
            'assets/onboarding/profile',
            'assets/onboarding/documents'
        ]
        
        print("\n🧹 Cleaning up local assets...")
        for asset_dir in asset_dirs:
            if os.path.exists(asset_dir):
                shutil.rmtree(asset_dir)
                print(f"✅ Removed {asset_dir}")
        
        print("✅ Local asset cleanup completed")
        
    except Exception as e:
        print(f"⚠️ Warning: Could not clean up local assets: {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting S3 Asset Migration...")
    print("=" * 50)
    
    # Run migration
    success = migrate_assets_to_s3()
    
    if success:
        print("\n" + "=" * 50)
        print("✅ Migration completed successfully!")
        
        # Ask user if they want to clean up local assets
        response = input("\n🧹 Do you want to clean up local assets? (y/N): ").strip().lower()
        if response in ['y', 'yes']:
            cleanup_local_assets()
        else:
            print("ℹ️ Local assets preserved. You can clean them up manually later.")
    else:
        print("\n" + "=" * 50)
        print("❌ Migration failed. Please check the errors above.")
        sys.exit(1)
