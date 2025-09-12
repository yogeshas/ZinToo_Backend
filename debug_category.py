#!/usr/bin/env python3
"""
Debug script to test category creation with proper encryption
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from utils.crypto import encrypt_payload, decrypt_payload
from io import BytesIO
from PIL import Image

def create_test_image():
    """Create a test image in memory"""
    img = Image.new('RGB', (100, 100), color='red')
    img_io = BytesIO()
    img.save(img_io, format='PNG')
    img_io.seek(0)
    return img_io

def test_encryption():
    """Test encryption/decryption"""
    print("🧪 Testing encryption/decryption...")
    
    with app.app_context():
        test_data = {
            "name": "Test Category S3",
            "description": "Test category with S3 image storage"
        }
        
        try:
            # Encrypt data
            encrypted = encrypt_payload(test_data)
            print(f"✅ Encryption successful: {encrypted[:50]}...")
            
            # Decrypt data
            decrypted = decrypt_payload(encrypted)
            print(f"✅ Decryption successful: {decrypted}")
            
            return encrypted
        except Exception as e:
            print(f"❌ Encryption/Decryption failed: {str(e)}")
            return None

def test_category_creation():
    """Test category creation with proper encryption"""
    print("\n🧪 Testing category creation with encryption...")
    
    with app.app_context():
        try:
            from services.category_service import create_category
            
            # Create test image
            img_data = create_test_image()
            
            # Create mock file object
            class MockFile:
                def __init__(self, data, filename):
                    self.data = data
                    self.filename = filename
                    self.content_type = 'image/png'
                
                def read(self, size=-1):
                    return self.data.read(size)
                
                def seek(self, position):
                    self.data.seek(position)
            
            test_file = MockFile(img_data, 'test_category.png')
            
            # Test data
            test_data = {
                "name": "Test Category S3 Debug",
                "description": "Test category with S3 image storage - Debug"
            }
            
            # Encrypt data
            encrypted_data = encrypt_payload(test_data)
            print(f"Encrypted data: {encrypted_data[:50]}...")
            
            # Test category creation
            result, status = create_category(encrypted_data, test_file)
            print(f"Status: {status}")
            print(f"Result: {result}")
            
            if status == 201:
                print("✅ Category creation successful!")
                return True
            else:
                print("❌ Category creation failed!")
                return False
                
        except Exception as e:
            print(f"❌ Category creation error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    print("🚀 Starting Category Debug Tests")
    print("=" * 50)
    
    # Test 1: Encryption/Decryption
    encrypted_data = test_encryption()
    
    if encrypted_data:
        # Test 2: Category creation
        test_category_creation()
    
    print("\n🎉 Debug Tests Complete!")
