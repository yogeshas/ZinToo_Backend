#!/usr/bin/env python3
"""
Comprehensive test script to debug delivery OTP functionality
"""
import requests
import json

BASE_URL = "http://localhost:5000"

def test_send_otp_valid():
    """Test sending OTP with valid data"""
    print("🧪 Testing Delivery OTP Send (Valid)...")
    
    url = f"{BASE_URL}/api/delivery-mobile/auth/send-otp"
    data = {
        "email": "test@example.com"
    }
    
    print(f"📤 POST {url}")
    print(f"📝 Data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, json=data)
        print(f"📥 Response Status: {response.status_code}")
        print(f"📥 Response Body: {response.text}")
        
        if response.status_code == 200:
            print("✅ OTP sent successfully!")
            return True
        else:
            print("❌ OTP send failed!")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def test_send_otp_missing_email():
    """Test sending OTP with missing email"""
    print("\n🧪 Testing Delivery OTP Send (Missing Email)...")
    
    url = f"{BASE_URL}/api/delivery-mobile/auth/send-otp"
    data = {}
    
    print(f"📤 POST {url}")
    print(f"📝 Data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, json=data)
        print(f"📥 Response Status: {response.status_code}")
        print(f"📥 Response Body: {response.text}")
        
        if response.status_code == 400:
            print("✅ Correctly rejected missing email!")
            return True
        else:
            print("❌ Should have rejected missing email!")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def test_send_otp_empty_email():
    """Test sending OTP with empty email"""
    print("\n🧪 Testing Delivery OTP Send (Empty Email)...")
    
    url = f"{BASE_URL}/api/delivery-mobile/auth/send-otp"
    data = {"email": ""}
    
    print(f"📤 POST {url}")
    print(f"📝 Data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, json=data)
        print(f"📥 Response Status: {response.status_code}")
        print(f"📥 Response Body: {response.text}")
        
        if response.status_code == 400:
            print("✅ Correctly rejected empty email!")
            return True
        else:
            print("❌ Should have rejected empty email!")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def test_send_otp_invalid_json():
    """Test sending OTP with invalid JSON"""
    print("\n🧪 Testing Delivery OTP Send (Invalid JSON)...")
    
    url = f"{BASE_URL}/api/delivery-mobile/auth/send-otp"
    headers = {"Content-Type": "application/json"}
    
    print(f"📤 POST {url}")
    print(f"📝 Data: invalid json")
    
    try:
        response = requests.post(url, data="invalid json", headers=headers)
        print(f"📥 Response Status: {response.status_code}")
        print(f"📥 Response Body: {response.text}")
        
        if response.status_code == 400:
            print("✅ Correctly rejected invalid JSON!")
            return True
        else:
            print("❌ Should have rejected invalid JSON!")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def test_send_otp_no_content_type():
    """Test sending OTP without content type"""
    print("\n🧪 Testing Delivery OTP Send (No Content-Type)...")
    
    url = f"{BASE_URL}/api/delivery-mobile/auth/send-otp"
    data = {"email": "test@example.com"}
    
    print(f"📤 POST {url}")
    print(f"📝 Data: {json.dumps(data, indent=2)}")
    print("📝 No Content-Type header")
    
    try:
        response = requests.post(url, data=json.dumps(data))
        print(f"📥 Response Status: {response.status_code}")
        print(f"📥 Response Body: {response.text}")
        
        if response.status_code == 200:
            print("✅ OTP sent successfully without Content-Type!")
            return True
        else:
            print("❌ Failed without Content-Type!")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Comprehensive Delivery OTP Test Suite")
    print("=" * 60)
    
    results = []
    results.append(test_send_otp_valid())
    results.append(test_send_otp_missing_email())
    results.append(test_send_otp_empty_email())
    results.append(test_send_otp_invalid_json())
    results.append(test_send_otp_no_content_type())
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {sum(results)}/{len(results)} passed")
    
    if all(results):
        print("🎉 All tests passed! The API is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    print("\n🏁 Comprehensive test suite completed!")
