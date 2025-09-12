#!/usr/bin/env python3
"""
Test script to verify frontend-backend crypto compatibility
This simulates the frontend crypto implementation in Python
"""

import base64
import json
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import os

def normalize_key(secret: str) -> str:
    """Normalize key to exactly 32 bytes (same as frontend)"""
    key = secret
    if len(key) < 32:
        key = key.ljust(32, '\0')
    elif len(key) > 32:
        key = key[:32]
    return key

def frontend_encrypt(data: any) -> str:
    """Simulate frontend encryption (CryptoJS equivalent)"""
    try:
        secret = "my_super_secret_key_32chars!!"
        key = normalize_key(secret).encode('utf-8')
        json_data = json.dumps(data)
        
        # Generate random IV (16 bytes) - same as CryptoJS.lib.WordArray.random(16)
        iv = os.urandom(16)
        
        # Encrypt with AES-256-CBC and PKCS7 padding
        cipher = AES.new(key, AES.MODE_CBC, iv)
        padded_data = pad(json_data.encode('utf-8'), AES.block_size)
        encrypted_data = cipher.encrypt(padded_data)
        
        # Combine IV + ciphertext and base64 encode
        combined = iv + encrypted_data
        return base64.b64encode(combined).decode('utf-8')
        
    except Exception as e:
        print(f"Frontend encryption failed: {e}")
        raise

def frontend_decrypt(encrypted_data: str) -> any:
    """Simulate frontend decryption (CryptoJS equivalent)"""
    try:
        secret = "my_super_secret_key_32chars!!"
        key = normalize_key(secret).encode('utf-8')
        
        # Decode base64
        combined = base64.b64decode(encrypted_data)
        
        # Extract IV (first 16 bytes) and ciphertext
        iv = combined[:16]
        ciphertext = combined[16:]
        
        # Decrypt
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted_padded = cipher.decrypt(ciphertext)
        decrypted_data = unpad(decrypted_padded, AES.block_size)
        
        # Convert to string and parse JSON
        decrypted_string = decrypted_data.decode('utf-8')
        return json.loads(decrypted_string)
        
    except Exception as e:
        print(f"Frontend decryption failed: {e}")
        raise

def test_compatibility():
    """Test frontend-backend compatibility"""
    print("=== TESTING FRONTEND-BACKEND CRYPTO COMPATIBILITY ===\n")
    
    # Test data
    test_data = {
        'widgets': [{'id': 1, 'name': 'Test Widget'}],
        'categories': [{'id': 1, 'name': 'Electronics'}],
        'products': [{'id': 1, 'name': 'Test Product', 'price': 99.99}]
    }
    
    print("1. Testing frontend encryption/decryption:")
    try:
        encrypted = frontend_encrypt(test_data)
        print(f"   ✅ Frontend encryption successful")
        print(f"   Length: {len(encrypted)}")
        
        decrypted = frontend_decrypt(encrypted)
        print(f"   ✅ Frontend decryption successful: {decrypted == test_data}")
        
    except Exception as e:
        print(f"   ❌ Frontend error: {e}")
        return
    
    print("\n2. Testing cross-compatibility:")
    try:
        # Import backend functions with app context
        import sys
        sys.path.append('.')
        from app import app
        from utils.crypto import encrypt_payload, decrypt_payload
        
        with app.app_context():
            # Backend encrypts, frontend decrypts
            backend_encrypted = encrypt_payload(test_data)
            frontend_decrypted = frontend_decrypt(backend_encrypted)
            print(f"   ✅ Backend→Frontend: {frontend_decrypted == test_data}")
            
            # Frontend encrypts, backend decrypts
            frontend_encrypted = frontend_encrypt(test_data)
            backend_decrypted = decrypt_payload(frontend_encrypted)
            print(f"   ✅ Frontend→Backend: {backend_decrypted == test_data}")
        
    except Exception as e:
        print(f"   ❌ Cross-compatibility error: {e}")
    
    print("\n3. Testing data structure:")
    try:
        raw_data = base64.b64decode(encrypted)
        print(f"   Raw data length: {len(raw_data)}")
        print(f"   IV length: {len(raw_data[:16])} bytes")
        print(f"   Ciphertext length: {len(raw_data[16:])} bytes")
        print(f"   ✅ Structure correct: IV(16) + Ciphertext({len(raw_data[16:])})")
        
    except Exception as e:
        print(f"   ❌ Structure test error: {e}")

if __name__ == "__main__":
    test_compatibility()
