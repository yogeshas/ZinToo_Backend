#!/usr/bin/env python3
"""
Test script to check admin routes
"""
import requests
import json
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

BASE_URL = "http://localhost:5000"
CRYPTO_SECRET = "my_super_secret_key_32chars!!"

def encrypt_payload(data):
    """Encrypt payload using AES - DEPRECATED: Use utils.crypto instead"""
    # Import the proper encryption function
    from utils.crypto import encrypt_payload as proper_encrypt
    return proper_encrypt(data)

def test_admin_login():
    """Test admin login"""
    print("Testing admin login...")
    
    # Encrypt the login data
    login_data = {
        "email": "admin@zintoo.com",
        "password": "admin123"
    }
    
    encrypted_payload = encrypt_payload(login_data)
    
    response = requests.post(f"{BASE_URL}/api/admin/login", json={"payload": encrypted_payload})
    print(f"Login response: {response.status_code}")
    print(f"Login data: {response.json()}")
    
    if response.status_code == 200:
        return response.json().get("token_uuid")
    return None

def test_admin_otp_verification(token_uuid):
    """Test admin OTP verification"""
    print("Testing admin OTP verification...")
    
    # For testing, we'll use a dummy OTP
    otp_data = {
        "token_uuid": token_uuid,
        "otp_code": "123456"  # This might not work, but let's try
    }
    
    encrypted_payload = encrypt_payload(otp_data)
    
    response = requests.post(f"{BASE_URL}/api/admin/verify-otp", json={"payload": encrypted_payload})
    print(f"OTP verification response: {response.status_code}")
    print(f"OTP verification data: {response.json()}")
    
    if response.status_code == 200:
        return response.json().get("token")
    return None

def test_admin_customers(token):
    """Test admin customers endpoint"""
    print("Testing admin customers endpoint...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/admin/customers/", headers=headers)
    print(f"Customers response: {response.status_code}")
    print(f"Customers data: {response.json()}")

if __name__ == "__main__":
    print("Testing admin routes...")
    
    # Test login
    token_uuid = test_admin_login()
    if token_uuid:
        print(f"Got token_uuid: {token_uuid}")
        
        # Test OTP verification
        token = test_admin_otp_verification(token_uuid)
        if token:
            print(f"Got token: {token}")
            
            # Test customers endpoint
            test_admin_customers(token)
        else:
            print("Failed to get token from OTP verification")
    else:
        print("Failed to get token_uuid from login")
