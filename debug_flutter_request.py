#!/usr/bin/env python3
"""
Debug script to help identify Flutter request issues
"""
import requests
import json

BASE_URL = "http://localhost:5000"

def debug_flutter_request():
    """Debug the Flutter request to identify issues"""
    print("🐛 Debugging Flutter Request")
    print("=" * 40)
    
    # Simulate what Flutter should be sending
    print("\n📱 Simulating Flutter Request")
    
    # Step 1: Get a valid auth token first
    print("\n🔐 Step 1: Getting valid auth token...")
    
    # Send OTP
    email = "test@example.com"
    url = f"{BASE_URL}/api/delivery-mobile/auth/send-otp"
    data = {"email": email}
    
    try:
        response = requests.post(url, json=data)
        if response.status_code != 200:
            print(f"❌ OTP send failed: {response.text}")
            return False
        print("✅ OTP sent successfully")
    except Exception as e:
        print(f"❌ OTP send failed: {e}")
        return False
    
    # Get OTP from user
    otp = input("Enter the OTP from console: ").strip()
    if not otp:
        print("❌ OTP is required!")
        return False
    
    # Verify OTP
    url = f"{BASE_URL}/api/delivery-mobile/auth/verify-otp"
    data = {"email": email, "otp": otp}
    
    try:
        response = requests.post(url, json=data)
        if response.status_code != 200:
            print(f"❌ OTP verification failed: {response.text}")
            return False
        
        response_data = response.json()
        auth_token = response_data.get("auth_token")
        
        if not auth_token:
            print("❌ No auth token in response!")
            return False
        
        print(f"✅ Got auth token: {auth_token[:20]}...")
        
    except Exception as e:
        print(f"❌ OTP verification failed: {e}")
        return False
    
    # Step 2: Test the onboarding request (what Flutter should be doing)
    print("\n📋 Step 2: Testing onboarding request...")
    
    url = f"{BASE_URL}/api/delivery/onboard"
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }
    
    print(f"📤 Making request to: {url}")
    print(f"📤 Headers: {headers}")
    
    try:
        response = requests.get(url, headers=headers)
        print(f"📥 Response Status: {response.status_code}")
        print(f"📥 Response Headers: {dict(response.headers)}")
        print(f"📥 Response Body: {response.text}")
        
        if response.status_code == 200:
            print("✅ Onboarding request successful!")
            response_data = response.json()
            print(f"📊 Response data: {json.dumps(response_data, indent=2)}")
        elif response.status_code == 404:
            print("✅ No onboarding record found (expected for new user)")
        else:
            print(f"❌ Onboarding request failed with status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Onboarding request failed: {e}")
        return False
    
    print("\n🏁 Debug completed!")
    return True

def test_common_flutter_issues():
    """Test common issues that might cause 404"""
    print("\n🔍 Testing Common Flutter Issues")
    print("=" * 40)
    
    # Test 1: Missing Authorization header
    print("\n❌ Test 1: Missing Authorization header")
    try:
        response = requests.get(f"{BASE_URL}/api/delivery/onboard")
        print(f"📥 Status: {response.status_code}")
        print(f"📥 Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Wrong Authorization format
    print("\n❌ Test 2: Wrong Authorization format")
    try:
        headers = {"Authorization": "invalid_token"}
        response = requests.get(f"{BASE_URL}/api/delivery/onboard", headers=headers)
        print(f"📥 Status: {response.status_code}")
        print(f"📥 Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Wrong HTTP method
    print("\n❌ Test 3: Wrong HTTP method (POST instead of GET)")
    try:
        response = requests.post(f"{BASE_URL}/api/delivery/onboard")
        print(f"📥 Status: {response.status_code}")
        print(f"📥 Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Wrong URL
    print("\n❌ Test 4: Wrong URL")
    try:
        response = requests.get(f"{BASE_URL}/api/delivery/onboarding")
        print(f"📥 Status: {response.status_code}")
        print(f"📥 Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🚚 Flutter Request Debug Tool")
    print("=" * 50)
    
    choice = input("Choose test:\n1. Debug Flutter request\n2. Test common issues\nEnter choice (1 or 2): ").strip()
    
    if choice == "1":
        debug_flutter_request()
    elif choice == "2":
        test_common_flutter_issues()
    else:
        print("❌ Invalid choice!")
    
    print("\n🏁 Debug tool completed!")
