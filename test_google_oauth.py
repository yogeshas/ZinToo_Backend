#!/usr/bin/env python3
"""
Test script to verify Google OAuth integration
"""

import requests
import json
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import os

BASE_URL = "http://localhost:5000"
CRYPTO_SECRET = "4e8f3d1c90b2a6d73a7f8b19c4d2f50a"  # Same as backend config

def _normalize_key(secret_str: str):
    """Normalize key to exactly 32 bytes (same as backend)"""
    key = secret_str.encode("utf-8")
    padded = False
    truncated = False
    if len(key) < 32:
        key = key.ljust(32, b'\0')
        padded = True
    elif len(key) > 32:
        key = key[:32]
        truncated = True
    return key, padded, truncated

def encrypt_payload(data: any) -> str:
    """Encrypt payload using AES - same as backend"""
    try:
        key, padded, truncated = _normalize_key(CRYPTO_SECRET)
        json_data = json.dumps(data)
        
        # Generate random IV (16 bytes)
        iv = os.urandom(16)
        
        # Encrypt with AES-256-CBC and PKCS7 padding
        cipher = AES.new(key, AES.MODE_CBC, iv)
        padded_data = pad(json_data.encode('utf-8'), AES.block_size)
        encrypted_data = cipher.encrypt(padded_data)
        
        # Combine IV + ciphertext and base64 encode
        result = iv + encrypted_data
        return base64.b64encode(result).decode('utf-8')
        
    except Exception as e:
        print(f"Encryption failed: {e}")
        raise

def decrypt_payload(encrypted_data: str) -> any:
    """Decrypt payload using AES - same as backend"""
    try:
        key, padded, truncated = _normalize_key(CRYPTO_SECRET)
        
        # Decode base64
        raw_data = base64.b64decode(encrypted_data)
        iv = raw_data[:16]
        ciphertext = raw_data[16:]
        
        # Decrypt
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted_padded = cipher.decrypt(ciphertext)
        decrypted_data = unpad(decrypted_padded, AES.block_size)
        
        # Convert to string and parse JSON
        json_data = decrypted_data.decode('utf-8')
        return json.loads(json_data)
        
    except Exception as e:
        print(f"Decryption failed: {e}")
        raise

def test_google_auth_url():
    """Test getting Google OAuth URL"""
    print("=== TESTING GOOGLE AUTH URL ===\n")
    
    try:
        response = requests.get(f"{BASE_URL}/api/auth/google")
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("auth_url"):
                print("✅ Google auth URL generated successfully")
                print(f"Auth URL: {data['auth_url']}")
                return True
            else:
                print("❌ Failed to get auth URL")
                return False
        else:
            print(f"❌ Request failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_google_register():
    """Test Google registration endpoint"""
    print("\n=== TESTING GOOGLE REGISTRATION ===\n")
    
    # Test data
    google_data = {
        "email": "testuser@gmail.com",
        "name": "Test User",
        "google_id": "123456789"
    }
    
    try:
        encrypted_payload = encrypt_payload(google_data)
        
        response = requests.post(
            f"{BASE_URL}/api/customers/google/register",
            json={"data": encrypted_payload}
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.json()}")
        
        if response.status_code == 201:
            data = response.json()
            if data.get("success") and data.get("encrypted_data"):
                print("✅ Google registration successful")
                
                # Decrypt response
                decrypted_response = decrypt_payload(data["encrypted_data"])
                print(f"Decrypted response: {decrypted_response}")
                
                if decrypted_response.get("token") and decrypted_response.get("user"):
                    print("✅ Token and user data received")
                    return True
                else:
                    print("❌ Missing token or user data")
                    return False
            else:
                print("❌ Registration failed")
                return False
        else:
            print(f"❌ Request failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_google_login_existing():
    """Test Google login with existing user"""
    print("\n=== TESTING GOOGLE LOGIN (EXISTING USER) ===\n")
    
    # Test data for existing user
    login_data = {
        "email": "testuser@gmail.com",
        "password": "dummy_password"  # This won't work for Google OAuth users
    }
    
    try:
        encrypted_payload = encrypt_payload(login_data)
        
        response = requests.post(
            f"{BASE_URL}/api/customers/login",
            json={"data": encrypted_payload}
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("encrypted_data"):
                print("✅ Login successful")
                
                # Decrypt response
                decrypted_response = decrypt_payload(data["encrypted_data"])
                print(f"Decrypted response: {decrypted_response}")
                return True
            else:
                print("❌ Login failed")
                return False
        else:
            print(f"❌ Request failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_health_check():
    """Test backend health"""
    print("=== TESTING BACKEND HEALTH ===\n")
    
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.json()}")
        
        if response.status_code == 200:
            print("✅ Backend is running")
            return True
        else:
            print("❌ Backend health check failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🔐 TESTING GOOGLE OAUTH INTEGRATION\n")
    
    # Test backend health first
    if not test_health_check():
        print("❌ Backend is not running. Please start the backend first.")
        exit(1)
    
    # Test Google auth URL
    test_google_auth_url()
    
    # Test Google registration
    test_google_register()
    
    # Test login with existing user
    test_google_login_existing()
    
    print("\n=== TEST COMPLETE ===")
    print("Note: For full OAuth flow testing, you need to:")
    print("1. Set up Google OAuth credentials in Google Cloud Console")
    print("2. Add the redirect URI to your Google OAuth app")
    print("3. Test the complete flow through your frontend")
