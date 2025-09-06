#!/usr/bin/env python3
"""
Test script for delivery barcode generation functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.delivery_barcode_generator import generate_delivery_barcode_image, generate_delivery_barcode_sticker_html

def test_delivery_barcode_generation():
    """Test delivery barcode image generation"""
    
    print("Testing delivery barcode image generation...")
    
    # Test barcode
    test_barcode = "ZT20241201123456ABC123"
    test_product_name = "Premium Wireless Headphones"
    test_product_id = 12345
    
    try:
        # Test delivery image generation
        print(f"Generating delivery barcode image for: {test_barcode}")
        image_data = generate_delivery_barcode_image(test_barcode, test_product_name, test_product_id)
        
        if image_data:
            print("✓ Delivery barcode image generated successfully")
            print(f"  Image data length: {len(image_data)} characters")
            print(f"  Image format: {image_data[:50]}...")
        else:
            print("✗ Failed to generate delivery barcode image")
            return False
        
        # Test delivery HTML generation
        print("\nGenerating delivery barcode sticker HTML...")
        html_content = generate_delivery_barcode_sticker_html(test_barcode, test_product_name, test_product_id)
        
        if html_content and "delivery" in html_content.lower():
            print("✓ Delivery barcode sticker HTML generated successfully")
            print(f"  HTML length: {len(html_content)} characters")
            
            # Save HTML to file for testing
            with open("test_delivery_barcode_sticker.html", "w") as f:
                f.write(html_content)
            print("  HTML saved to test_delivery_barcode_sticker.html")
        else:
            print("✗ Failed to generate delivery barcode sticker HTML")
            return False
        
        # Test with minimal data
        print("\nTesting with minimal data...")
        minimal_image = generate_delivery_barcode_image(test_barcode)
        if minimal_image:
            print("✓ Minimal delivery barcode image generated successfully")
        else:
            print("✗ Failed to generate minimal delivery barcode image")
            return False
        
        print("\n✓ All delivery barcode tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Error during testing: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_delivery_barcode_generation()
    if not success:
        sys.exit(1)
    else:
        print("\n🚚 Delivery barcode generation is working perfectly!")
        print("You can open 'test_delivery_barcode_sticker.html' in your browser to see the delivery sticker preview.")
        print("This barcode is optimized for delivery personnel scanning!")
