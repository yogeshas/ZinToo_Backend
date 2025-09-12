#!/usr/bin/env python3
"""
Test script for barcode image generation functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.barcode_image_generator import generate_barcode_image, generate_barcode_sticker_html

def test_barcode_image_generation():
    """Test barcode image generation"""
    
    print("Testing barcode image generation...")
    
    # Test barcode
    test_barcode = "ZT20241201123456ABC123"
    test_product_name = "Test Product Name"
    test_product_id = 123
    
    try:
        # Test image generation
        print(f"Generating barcode image for: {test_barcode}")
        image_data = generate_barcode_image(test_barcode, test_product_name, test_product_id)
        
        if image_data:
            print("✓ Barcode image generated successfully")
            print(f"  Image data length: {len(image_data)} characters")
            print(f"  Image format: {image_data[:50]}...")
        else:
            print("✗ Failed to generate barcode image")
            return False
        
        # Test HTML generation
        print("\nGenerating barcode sticker HTML...")
        html_content = generate_barcode_sticker_html(test_barcode, test_product_name, test_product_id)
        
        if html_content and "barcode" in html_content.lower():
            print("✓ Barcode sticker HTML generated successfully")
            print(f"  HTML length: {len(html_content)} characters")
            
            # Save HTML to file for testing
            with open("test_barcode_sticker.html", "w") as f:
                f.write(html_content)
            print("  HTML saved to test_barcode_sticker.html")
        else:
            print("✗ Failed to generate barcode sticker HTML")
            return False
        
        # Test with minimal data
        print("\nTesting with minimal data...")
        minimal_image = generate_barcode_image(test_barcode)
        if minimal_image:
            print("✓ Minimal barcode image generated successfully")
        else:
            print("✗ Failed to generate minimal barcode image")
            return False
        
        print("\n✓ All barcode image tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Error during testing: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_barcode_image_generation()
    if not success:
        sys.exit(1)
    else:
        print("\n🎉 Barcode image generation is working perfectly!")
        print("You can open 'test_barcode_sticker.html' in your browser to see the sticker preview.")
