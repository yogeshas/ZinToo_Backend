#!/usr/bin/env python3
"""
Test script for category API with S3 integration
"""

import requests
import json
from io import BytesIO
from PIL import Image

def create_test_image():
    """Create a test image in memory"""
    img = Image.new('RGB', (100, 100), color='green')
    img_io = BytesIO()
    img.save(img_io, format='PNG')
    img_io.seek(0)
    return img_io

def test_category_creation():
    """Test category creation via API"""
    print("🧪 Testing category creation via API...")
    
    # Create test image
    img_data = create_test_image()
    
    # Test data (unencrypted for testing)
    test_data = {
        "name": "Test Category S3",
        "description": "Test category with S3 image storage"
    }
    
    # Prepare the request
    files = {
        'image': ('test_category.png', img_data, 'image/png')
    }
    
    data = {
        'payload': json.dumps(test_data)  # Send unencrypted for testing
    }
    
    try:
        response = requests.post(
            'http://localhost:5000/api/categories/',
            files=files,
            data=data,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 201:
            print("✅ Category creation successful!")
            return True
        else:
            print("❌ Category creation failed!")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {str(e)}")
        return False

def test_get_categories():
    """Test getting categories"""
    print("\n🧪 Testing get categories...")
    
    try:
        response = requests.get('http://localhost:5000/api/categories/', timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:500]}...")
        
        if response.status_code == 200:
            print("✅ Get categories successful!")
            return True
        else:
            print("❌ Get categories failed!")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Category API Tests")
    print("=" * 50)
    
    # Test 1: Get existing categories
    test_get_categories()
    
    # Test 2: Create new category
    test_category_creation()
    
    print("\n🎉 API Tests Complete!")
