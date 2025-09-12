import random
import string
from datetime import datetime
from models.product import Product
from extensions import db

def generate_unique_barcode():
    """
    Generate a unique barcode for products.
    Format: ZT + timestamp + random string
    Example: ZT20241201123456ABC123
    """
    max_attempts = 10
    
    for attempt in range(max_attempts):
        # Get current timestamp
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Generate random string (3 letters + 3 numbers)
        random_letters = ''.join(random.choices(string.ascii_uppercase, k=3))
        random_numbers = ''.join(random.choices(string.digits, k=3))
        
        # Combine to create barcode
        barcode = f"ZT{timestamp}{random_letters}{random_numbers}"
        
        # Check if barcode already exists
        existing_product = Product.query.filter_by(barcode=barcode).first()
        if not existing_product:
            return barcode
    
    # If we couldn't generate a unique barcode after max attempts, raise an error
    raise ValueError("Unable to generate unique barcode after multiple attempts")

def regenerate_barcode(product_id):
    """
    Regenerate barcode for an existing product
    """
    product = Product.query.get(product_id)
    if not product:
        raise ValueError("Product not found")
    
    new_barcode = generate_unique_barcode()
    product.barcode = new_barcode
    db.session.commit()
    
    return new_barcode

def validate_barcode_format(barcode):
    """
    Validate barcode format
    Expected format: ZT + 14 digits (timestamp) + 3 letters + 3 numbers
    Total length: 22 characters
    """
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
