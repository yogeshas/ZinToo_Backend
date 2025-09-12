#!/usr/bin/env python3
"""
Test script to verify both ADD and EDIT category functionality with S3
"""

import requests
import json
from io import BytesIO
from PIL import Image
import time

def create_test_image(color='blue', size=(200, 200)):
    """Create a test image for upload"""
    img = Image.new('RGB', size, color=color)
    img_io = BytesIO()
    img.save(img_io, format='PNG')
    img_io.seek(0)
    return img_io

def test_add_category():
    """Test adding a new category with image"""
    print("🧪 Testing ADD Category with S3 Image Upload")
    print("=" * 60)
    
    # Create test image
    image_data = create_test_image('green', (300, 300))
    
    # Test data
    category_data = {
        "name": f"New Category {int(time.time())}",
        "description": "Testing ADD category with S3 image upload"
    }
    
    # Prepare files for upload
    files = {
        'image': ('add_category.png', image_data, 'image/png')
    }
    
    # Data payload (in production, this would be encrypted)
    data = {
        'payload': json.dumps(category_data)
    }
    
    try:
        print("📤 Adding new category...")
        response = requests.post(
            'http://localhost:5000/api/categories/',
            files=files,
            data=data,
            timeout=30
        )
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 201:
            result = response.json()
            print("✅ SUCCESS: Category added!")
            print(f"📝 Response: {json.dumps(result, indent=2)}")
            return result
        else:
            print(f"❌ FAILED: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return None

def test_edit_category(category_id):
    """Test editing an existing category with new image"""
    print(f"\n🧪 Testing EDIT Category {category_id} with S3 Image Upload")
    print("=" * 60)
    
    # Create test image with different color
    image_data = create_test_image('red', (250, 250))
    
    # Test data
    category_data = {
        "name": f"Updated Category {int(time.time())}",
        "description": "Testing EDIT category with S3 image upload"
    }
    
    # Prepare files for upload
    files = {
        'image': ('edit_category.png', image_data, 'image/png')
    }
    
    # Data payload (in production, this would be encrypted)
    data = {
        'payload': json.dumps(category_data)
    }
    
    try:
        print("📤 Editing existing category...")
        response = requests.put(
            f'http://localhost:5000/api/categories/{category_id}',
            files=files,
            data=data,
            timeout=30
        )
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS: Category updated!")
            print(f"📝 Response: {json.dumps(result, indent=2)}")
            return result
        else:
            print(f"❌ FAILED: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return None

def test_get_categories():
    """Test getting categories to see S3 URLs"""
    print("\n🧪 Testing GET Categories (to see S3 URLs)")
    print("=" * 60)
    
    try:
        response = requests.get('http://localhost:5000/api/categories/', timeout=10)
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS: Categories retrieved!")
            print(f"📝 Has encrypted data: {'encrypted_data' in result}")
            
            if 'encrypted_data' in result:
                print(f"🔐 Encrypted data length: {len(result['encrypted_data'])} characters")
                print("📋 Note: In production, frontend would decrypt this data")
            
            return result
        else:
            print(f"❌ FAILED: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return None

def show_react_integration_notes():
    """Show important notes for React.js integration"""
    print("\n🚀 React.js Integration Notes")
    print("=" * 60)
    
    print("""
📋 Important Notes for Your React.js Frontend:

1. ✅ ADD Category:
   - POST /api/categories/ with image file
   - Image uploaded to S3: s3://zintoo/category/
   - S3 URL saved in database
   - Frontend gets complete S3 URL in response

2. ✅ EDIT Category:
   - PUT /api/categories/{id} with new image file
   - Old S3 image deleted automatically
   - New image uploaded to S3
   - New S3 URL saved in database
   - Frontend gets updated S3 URL in response

3. 🖼️ Display Images:
   - Use S3 URLs directly: category.image
   - No need to construct URLs
   - Images served directly from S3
   - No backend image serving needed

4. 🔐 Encryption (Production):
   - Always encrypt payload data
   - Use your encryption/decryption functions
   - Backend expects encrypted data

5. 📝 Frontend Code:
   ```javascript
   // For both ADD and EDIT
   const formData = new FormData();
   formData.append('image', imageFile);
   formData.append('payload', encryptPayload(categoryData));
   
   // ADD
   const response = await fetch('/api/categories/', {
     method: 'POST',
     body: formData
   });
   
   // EDIT
   const response = await fetch(`/api/categories/${categoryId}`, {
     method: 'PUT',
     body: formData
   });
   ```
""")

if __name__ == "__main__":
    print("🚀 Category ADD & EDIT Test with S3")
    print("=" * 60)
    
    # Test 1: Add category
    add_result = test_add_category()
    
    # Test 2: Get categories to see current state
    get_result = test_get_categories()
    
    # Test 3: Edit category (if we have one)
    edit_result = None
    if add_result and 'encrypted_data' in add_result:
        # In a real scenario, you'd decrypt the data to get the category ID
        # For testing, we'll use a known ID or create one
        print("\n💡 Note: Edit test requires a valid category ID")
        print("   In production, you'd get this from the decrypted response")
    
    # Show integration notes
    show_react_integration_notes()
    
    print(f"\n📊 Test Results:")
    print(f"   ADD: {'✅ Success' if add_result else '❌ Failed'}")
    print(f"   GET: {'✅ Success' if get_result else '❌ Failed'}")
    print(f"   EDIT: {'✅ Success' if edit_result else '⏭️ Skipped (needs category ID)'}")
