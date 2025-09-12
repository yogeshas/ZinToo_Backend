#!/usr/bin/env python3
"""
Test script for admin customer update functionality
"""
import requests
import json
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

# Configuration
API_URL = "http://localhost:5000"
CRYPTO_SECRET = "my_super_secret_key_32chars!!"  # Make sure this matches your backend

def normalize_key(secret_str):
    key = secret_str.encode("utf-8")
    if len(key) < 32:
        key = key.ljust(32, b'\0')
    elif len(key) > 32:
        key = key[:32]
    return key

def encrypt_payload(data):
    """Encrypt data using AES-256-CBC with PKCS7 padding - DEPRECATED: Use utils.crypto instead"""
    # Import the proper encryption function
    from utils.crypto import encrypt_payload as proper_encrypt
    return proper_encrypt(data)

def test_admin_customer_update():
    """Test the admin customer update functionality"""
    
    # You'll need to get a valid admin token first
    # This is just a test - replace with actual admin credentials
    admin_token = "YOUR_ADMIN_TOKEN_HERE"  # Replace with actual token
    
    if admin_token == "YOUR_ADMIN_TOKEN_HERE":
        print("❌ Please replace admin_token with a valid token")
        return
    
    # Test data
    test_customer_id = 1  # Replace with actual customer ID
    test_data = {
        "username": "test_user_updated",
        "email": "test@example.com",
        "phone_number": "+1234567890",
        "location": "New York, USA",
        "status": "active"
    }
    
    print(f"🧪 Testing admin customer update for customer {test_customer_id}")
    print(f"📝 Test data: {test_data}")
    
    try:
        # Encrypt the payload
        encrypted_payload = encrypt_payload(test_data)
        print(f"🔐 Encrypted payload: {encrypted_payload[:50]}...")
        
        # Make the API call
        headers = {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
        
        payload = {"payload": encrypted_payload}
        
        response = requests.put(
            f"{API_URL}/api/admin/customers/{test_customer_id}",
            json=payload,
            headers=headers
        )
        
        print(f"📡 Response status: {response.status_code}")
        print(f"📡 Response headers: {dict(response.headers)}")
        print(f"📡 Response body: {response.text}")
        
        if response.status_code == 200:
            print("✅ Admin customer update test PASSED")
        else:
            print("❌ Admin customer update test FAILED")
            
    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")

if __name__ == "__main__":
    test_admin_customer_update()
