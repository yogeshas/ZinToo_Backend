#!/usr/bin/env python3
"""
Test script to check crypto utilities
"""
import sys
import os

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_crypto_import():
    """Test if crypto utilities can be imported"""
    try:
        from utils.crypto import encrypt_payload, decrypt_payload
        print("✅ Crypto utilities imported successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to import crypto utilities: {e}")
        return False

def test_crypto_encryption():
    """Test encryption and decryption"""
    try:
        from utils.crypto import encrypt_payload, decrypt_payload
        from app import app
        
        with app.app_context():
            test_data = {"message": "Hello World", "number": 42}
            print(f"📝 Test data: {test_data}")
            
            # Encrypt
            encrypted = encrypt_payload(test_data)
            print(f"🔐 Encrypted: {encrypted[:50]}...")
            
            # Decrypt
            decrypted = decrypt_payload(encrypted)
            print(f"🔓 Decrypted: {decrypted}")
            
            if decrypted == test_data:
                print("✅ Encryption/decryption working correctly!")
                return True
            else:
                print("❌ Encryption/decryption failed - data mismatch!")
                return False
                
    except Exception as e:
        print(f"❌ Crypto test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔐 Crypto Utility Test")
    print("=" * 30)
    
    if test_crypto_import():
        test_crypto_encryption()
    
    print("\n🏁 Crypto test completed!")
