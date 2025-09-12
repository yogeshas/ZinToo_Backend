#!/usr/bin/env python3
"""
Test script for image upload functionality
"""

import requests
import os
from PIL import Image
import io

def create_test_image():
    """Create a test image for uploading"""
    # Create a simple test image
    img = Image.new('RGB', (100, 100), color='red')
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    return img_buffer

def test_upload():
    """Test the upload endpoint"""
    print("Testing image upload endpoint...")
    
    # Create test image
    test_image = create_test_image()
    
    # Prepare the request
    url = "http://localhost:5000/api/products/upload-images"
    files = {
        'images': ('test_image.png', test_image, 'image/png')
    }
    
    try:
        response = requests.post(url, files=files)
        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Upload successful!")
                print(f"Uploaded files: {data.get('files', [])}")
            else:
                print(f"❌ Upload failed: {data.get('error')}")
        else:
            print(f"❌ Upload failed with status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error during upload test: {str(e)}")

if __name__ == "__main__":
    test_upload()
