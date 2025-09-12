#!/usr/bin/env python3
"""
Test script for barcode generation functionality
"""

import sys
import os
import random
import string
from datetime import datetime

def generate_test_barcode():
    """Generate a test barcode without database dependency"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_letters = ''.join(random.choices(string.ascii_uppercase, k=3))
    random_numbers = ''.join(random.choices(string.digits, k=3))
    return f"ZT{timestamp}{random_letters}{random_numbers}"

def validate_barcode_format(barcode):
    """Validate barcode format"""
    if not barcode:
        return False
    
    if len(barcode) != 22:
        return False
    
    if not barcode.startswith('ZT'):
        return False
    
    # Check if timestamp part is numeric (14 digits)
    timestamp_part = barcode[2:16]
    if not timestamp_part.isdigit():
        return False
    
    # Check if random part has 3 letters + 3 numbers
    random_part = barcode[16:]
    if len(random_part) != 6:
        return False
    
    letters = random_part[:3]
    numbers = random_part[3:]
    
    if not letters.isalpha() or not letters.isupper():
        return False
    
    if not numbers.isdigit():
        return False
    
    return True

def test_barcode_generation():
    """Test barcode generation and validation"""
    
    print("Testing barcode generation...")
    
    # Test generating multiple barcodes
    barcodes = []
    for i in range(5):
        barcode = generate_test_barcode()
        barcodes.append(barcode)
        print(f"Generated barcode {i+1}: {barcode}")
        
        # Validate format
        is_valid = validate_barcode_format(barcode)
        print(f"  Format validation: {'✓' if is_valid else '✗'}")
        
        if not is_valid:
            print(f"  ERROR: Invalid barcode format!")
            return False
    
    # Check uniqueness
    if len(set(barcodes)) == len(barcodes):
        print("✓ All barcodes are unique")
    else:
        print("✗ Duplicate barcodes found!")
        return False
    
    # Test validation with invalid formats
    print("\nTesting validation with invalid formats...")
    invalid_barcodes = [
        "ZT12345678901234567890",  # Too short
        "ZT12345678901234567890123",  # Too long
        "AB12345678901234567890",  # Wrong prefix
        "ZT1234567890123456789A",  # Invalid characters
        "ZT1234567890123456789a",  # Lowercase letters
        "",  # Empty
        None,  # None
    ]
    
    for invalid_barcode in invalid_barcodes:
        is_valid = validate_barcode_format(invalid_barcode)
        if is_valid:
            print(f"✗ ERROR: Should be invalid but passed validation: {invalid_barcode}")
            return False
        else:
            print(f"✓ Correctly rejected invalid barcode: {invalid_barcode}")
    
    print("\n✓ All tests passed!")
    return True

if __name__ == "__main__":
    success = test_barcode_generation()
    if not success:
        sys.exit(1)
