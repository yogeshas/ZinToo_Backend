#!/usr/bin/env python3
"""
Test script for S3 category image integration
Run this script to test the S3 functionality
"""

import os
import sys
from io import BytesIO
from PIL import Image

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.s3_service import s3_service
from services.category_service import save_category_image, delete_category_image

def create_test_image():
    """Create a test image in memory"""
    # Create a simple test image
    img = Image.new('RGB', (100, 100), color='red')
    img_io = BytesIO()
    img.save(img_io, format='PNG')
    img_io.seek(0)
    
    # Create a mock file object
    class MockFile:
        def __init__(self, data, filename):
            self.data = data
            self.filename = filename
            self.content_type = 'image/png'
        
        def read(self, size=-1):
            return self.data.read(size)
        
        def seek(self, position):
            self.data.seek(position)
    
    return MockFile(img_io, 'test_category.png')

def test_s3_upload():
    """Test S3 file upload"""
    print("🧪 Testing S3 file upload...")
    
    try:
        # Create test image
        test_file = create_test_image()
        
        # Test upload
        s3_url = save_category_image(test_file, 999)  # Using test category ID
        
        if s3_url:
            print(f"✅ Upload successful: {s3_url}")
            return s3_url
        else:
            print("❌ Upload failed")
            return None
            
    except Exception as e:
        print(f"❌ Upload test error: {str(e)}")
        return None

def test_s3_delete(s3_url):
    """Test S3 file deletion"""
    print("🧪 Testing S3 file deletion...")
    
    try:
        success = delete_category_image(s3_url)
        if success:
            print("✅ Delete successful")
        else:
            print("❌ Delete failed")
        return success
        
    except Exception as e:
        print(f"❌ Delete test error: {str(e)}")
        return False

def test_s3_file_exists(s3_url):
    """Test S3 file existence check"""
    print("🧪 Testing S3 file existence check...")
    
    try:
        exists = s3_service.file_exists(s3_url)
        print(f"✅ File exists: {exists}")
        return exists
        
    except Exception as e:
        print(f"❌ Existence check error: {str(e)}")
        return False

def main():
    """Main test function"""
    print("🚀 Starting S3 Category Integration Tests")
    print("=" * 50)
    
    # Check if S3 credentials are configured
    from config import Config
    if not Config.AWS_ACCESS_KEY_ID or not Config.AWS_SECRET_ACCESS_KEY:
        print("❌ AWS credentials not configured!")
        print("Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in your environment")
        return
    
    print(f"📦 S3 Bucket: {Config.S3_BUCKET_NAME}")
    print(f"🌍 AWS Region: {Config.AWS_REGION}")
    print(f"📁 Category Folder: {Config.S3_CATEGORY_FOLDER}")
    print()
    
    # Test 1: Upload file
    s3_url = test_s3_upload()
    if not s3_url:
        print("❌ Upload test failed, stopping tests")
        return
    
    print()
    
    # Test 2: Check file exists
    test_s3_file_exists(s3_url)
    print()
    
    # Test 3: Delete file
    test_s3_delete(s3_url)
    print()
    
    # Test 4: Check file no longer exists
    test_s3_file_exists(s3_url)
    print()
    
    print("🎉 S3 Category Integration Tests Complete!")

if __name__ == "__main__":
    main()
