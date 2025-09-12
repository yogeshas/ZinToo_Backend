#!/usr/bin/env python3
"""
Test script to simulate React.js frontend category upload
This shows how the frontend should interact with the API
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

def test_category_upload():
    """Test category upload as React.js frontend would do"""
    print("🧪 Testing Category Upload (React.js Frontend Simulation)")
    print("=" * 60)
    
    # Create test image
    image_data = create_test_image('green', (300, 300))
    
    # Test data (this would be encrypted in real frontend)
    category_data = {
        "name": f"Test Category {int(time.time())}",  # Unique name
        "description": "Test category for React.js frontend integration"
    }
    
    # Prepare files for upload (as React.js would)
    files = {
        'image': ('category_image.png', image_data, 'image/png')
    }
    
    # Data payload (as React.js would send)
    data = {
        'payload': json.dumps(category_data)  # In real app, this would be encrypted
    }
    
    try:
        print("📤 Uploading category with image...")
        response = requests.post(
            'http://localhost:5000/api/categories/',
            files=files,
            data=data,
            timeout=30
        )
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 201:
            result = response.json()
            print("✅ Category created successfully!")
            print(f"📝 Response: {json.dumps(result, indent=2)}")
            
            # Extract the encrypted data to show what frontend would receive
            if 'encrypted_data' in result:
                print("\n🔐 Encrypted data received (frontend would decrypt this)")
                print(f"Encrypted payload: {result['encrypted_data'][:100]}...")
            
            return True
        else:
            print(f"❌ Upload failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {str(e)}")
        return False

def test_get_categories():
    """Test getting categories to see S3 URLs"""
    print("\n🧪 Testing Get Categories (to see S3 URLs)")
    print("=" * 60)
    
    try:
        response = requests.get('http://localhost:5000/api/categories/', timeout=10)
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Categories retrieved successfully!")
            print(f"📝 Response contains encrypted data: {'encrypted_data' in result}")
            
            if 'encrypted_data' in result:
                print("🔐 Encrypted data received (frontend would decrypt this)")
                print(f"Encrypted payload length: {len(result['encrypted_data'])} characters")
            
            return True
        else:
            print(f"❌ Get categories failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {str(e)}")
        return False

def show_react_integration_guide():
    """Show how to integrate with React.js frontend"""
    print("\n🚀 React.js Frontend Integration Guide")
    print("=" * 60)
    
    print("""
📋 Frontend Integration Steps:

1. 📤 UPLOAD CATEGORY WITH IMAGE:
   ```javascript
   const uploadCategory = async (categoryData, imageFile) => {
     const formData = new FormData();
     formData.append('image', imageFile);
     formData.append('payload', JSON.stringify(categoryData)); // Encrypt this in production
     
     const response = await fetch('/api/categories/', {
       method: 'POST',
       body: formData
     });
     
     return await response.json();
   };
   ```

2. 📥 GET CATEGORIES (with S3 URLs):
   ```javascript
   const getCategories = async () => {
     const response = await fetch('/api/categories/');
     const result = await response.json();
     
     // Decrypt the encrypted_data in production
     const categories = result.encrypted_data; // This contains S3 URLs
     return categories;
   };
   ```

3. 🖼️ DISPLAY IMAGES:
   ```jsx
   const CategoryCard = ({ category }) => (
     <div>
       <h3>{category.name}</h3>
       <p>{category.description}</p>
       {category.image && (
         <img 
           src={category.image} 
           alt={category.name}
           style={{ width: '200px', height: '200px' }}
         />
       )}
     </div>
   );
   ```

4. 🔐 ENCRYPTION (Production):
   ```javascript
   // Use your encryption library
   const encryptedPayload = encrypt(JSON.stringify(categoryData));
   formData.append('payload', encryptedPayload);
   ```

📝 Important Notes:
- Images are stored in S3: s3://zintoo/category/
- URLs returned: https://zintoo.s3.us-east-1.amazonaws.com/category/category_123_abc123.png
- No backend image serving needed - direct S3 access
- Frontend gets complete S3 URLs in API responses
""")

if __name__ == "__main__":
    print("🚀 Category Upload Test for React.js Frontend")
    print("=" * 60)
    
    # Test 1: Upload category
    upload_success = test_category_upload()
    
    # Test 2: Get categories
    get_success = test_get_categories()
    
    # Show integration guide
    show_react_integration_guide()
    
    print(f"\n🎉 Test Results:")
    print(f"   Upload: {'✅ Success' if upload_success else '❌ Failed'}")
    print(f"   Get: {'✅ Success' if get_success else '❌ Failed'}")
