#!/usr/bin/env python3
"""
Test script to debug delivery OTP functionality
"""
import requests
import json

BASE_URL = "http://localhost:5000"

def test_send_otp():
    """Test sending OTP to delivery personnel"""
    print("🧪 Testing Delivery OTP Send...")
    
    url = f"{BASE_URL}/api/delivery-mobile/auth/send-otp"
    data = {
        "email": "test@example.com"
    }
    
    print(f"📤 POST {url}")
    print(f"📝 Data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, json=data)
        print(f"📥 Response Status: {response.status_code}")
        print(f"📥 Response Headers: {dict(response.headers)}")
        print(f"📥 Response Body: {response.text}")
        
        if response.status_code == 200:
            print("✅ OTP sent successfully!")
        else:
            print("❌ OTP send failed!")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

def test_verify_otp():
    """Test verifying OTP for delivery personnel"""
    print("\n🧪 Testing Delivery OTP Verify...")
    
    url = f"{BASE_URL}/api/delivery-mobile/auth/verify-otp"
    data = {
        "email": "test@example.com",
        "otp": "123456"
    }
    
    print(f"📤 POST {url}")
    print(f"📝 Data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, json=data)
        print(f"📥 Response Status: {response.status_code}")
        print(f"📥 Response Headers: {dict(response.headers)}")
        print(f"📥 Response Body: {response.text}")
        
        if response.status_code == 200:
            print("✅ OTP verified successfully!")
        else:
            print("❌ OTP verification failed!")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    print("🚀 Delivery OTP Test Suite")
    print("=" * 50)
    
    test_send_otp()
    test_verify_otp()
    
    print("\n🏁 Test suite completed!")
