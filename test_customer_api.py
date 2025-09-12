#!/usr/bin/env python3
import requests
import json
from utils.crypto import decrypt_payload

def test_customer_products():
    """Test the customer products API to verify color data structure"""
    try:
        # Make request to customer products API
        response = requests.get("http://localhost:5000/api/products/customer")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API Response Status: 200")
            print(f"✅ Success: {data.get('success')}")
            
            if data.get('encrypted_data'):
                # Decrypt the data
                decrypted = decrypt_payload(data['encrypted_data'])
                products = decrypted.get('products', [])
                
                print(f"✅ Found {len(products)} products")
                
                # Check first few products for color data structure
                for i, product in enumerate(products[:3]):  # Check first 3 products
                    print(f"\n--- Product {i+1}: {product.get('pname', 'Unknown')} ---")
                    print(f"ID: {product.get('id')}")
                    print(f"Price: {product.get('price')}")
                    print(f"Stock: {product.get('stock')}")
                    
                    # Check legacy color/size data
                    print(f"Legacy Color: {product.get('color')}")
                    print(f"Legacy Size: {product.get('size')}")
                    print(f"Legacy Sizes Dict: {product.get('sizes')}")
                    
                    # Check new colors data structure
                    colors = product.get('colors', [])
                    print(f"Colors Array: {len(colors)} colors")
                    
                    if colors:
                        for j, color in enumerate(colors):
                            print(f"  Color {j+1}: {color.get('name')}")
                            print(f"    Sizes: {color.get('sizes', [])}")
                            print(f"    Size Counts: {color.get('sizeCounts', {})}")
                            print(f"    Images: {len(color.get('images', []))} images")
                    else:
                        print("  No colors data (legacy product)")
                    
                    # Check main images
                    images = product.get('images', [])
                    print(f"Main Images: {len(images)} images")
                    
                    print("-" * 50)
                
                return True
            else:
                print("❌ No encrypted data in response")
                return False
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("Testing Customer Products API...")
    test_customer_products()