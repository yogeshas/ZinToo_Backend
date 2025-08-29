#!/usr/bin/env python3
"""
Test script to demonstrate the complete delivery authentication flow
"""
import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_complete_auth_flow():
    """Test the complete authentication flow"""
    print("🚀 Testing Complete Delivery Authentication Flow")
    print("=" * 60)
    
    email = "test@example.com"
    
    # Step 1: Send OTP
    print("\n📤 Step 1: Sending OTP...")
    url = f"{BASE_URL}/api/delivery-mobile/auth/send-otp"
    data = {"email": email}
    
    try:
        response = requests.post(url, json=data)
        print(f"📥 Response Status: {response.status_code}")
        print(f"📥 Response Body: {response.text}")
        
        if response.status_code != 200:
            print("❌ OTP send failed!")
            return False
            
        print("✅ OTP sent successfully!")
        
    except Exception as e:
        print(f"❌ OTP send request failed: {e}")
        return False
    
    # Step 2: Verify OTP (using a test OTP - in real app, user enters the OTP)
    print("\n🔐 Step 2: Verifying OTP...")
    print("⚠️  Note: This test uses a hardcoded OTP. In real app, user enters the OTP from email.")
    
    url = f"{BASE_URL}/api/delivery-mobile/auth/verify-otp"
    data = {"email": email, "otp": "123456"}  # This will likely fail, but shows the flow
    
    try:
        response = requests.post(url, json=data)
        print(f"📥 Response Status: {response.status_code}")
        print(f"📥 Response Body: {response.text}")
        
        if response.status_code == 200:
            print("✅ OTP verification successful!")
            response_data = response.json()
            
            # Extract auth token from decrypted data
            if "decrypted_data" in response_data:
                decrypted_data = response_data["decrypted_data"]
                auth_token = decrypted_data.get("auth_token")
                
                if auth_token:
                    print(f"🔑 Auth Token: {auth_token[:20]}...")
                    
                    # Step 3: Use auth token to access protected endpoint
                    print("\n🔒 Step 3: Accessing protected endpoint...")
                    url = f"{BASE_URL}/api/delivery/onboard"
                    headers = {"Authorization": f"Bearer {auth_token}"}
                    
                    try:
                        response = requests.get(url, headers=headers)
                        print(f"📥 Response Status: {response.status_code}")
                        print(f"📥 Response Body: {response.text}")
                        
                        if response.status_code == 200:
                            print("✅ Protected endpoint accessed successfully!")
                            return True
                        else:
                            print("❌ Protected endpoint access failed!")
                            return False
                            
                    except Exception as e:
                        print(f"❌ Protected endpoint request failed: {e}")
                        return False
                else:
                    print("❌ No auth token in response!")
                    return False
            else:
                print("❌ No decrypted data in response!")
                return False
        else:
            print("❌ OTP verification failed!")
            print("💡 This is expected if using a hardcoded OTP.")
            print("💡 In real app, user would enter the actual OTP from email.")
            return False
            
    except Exception as e:
        print(f"❌ OTP verification request failed: {e}")
        return False

def test_with_real_otp():
    """Test with a real OTP (requires manual input)"""
    print("\n🧪 Testing with Real OTP")
    print("=" * 40)
    
    email = input("Enter email: ").strip()
    if not email:
        print("❌ Email is required!")
        return False
    
    # Step 1: Send OTP
    print(f"\n📤 Sending OTP to {email}...")
    url = f"{BASE_URL}/api/delivery-mobile/auth/send-otp"
    data = {"email": email}
    
    try:
        response = requests.post(url, json=data)
        if response.status_code != 200:
            print(f"❌ OTP send failed: {response.text}")
            return False
            
        print("✅ OTP sent! Check your email/console for the OTP.")
        
    except Exception as e:
        print(f"❌ OTP send failed: {e}")
        return False
    
    # Step 2: Get OTP from user
    otp = input("Enter the OTP from email/console: ").strip()
    if not otp:
        print("❌ OTP is required!")
        return False
    
    # Step 3: Verify OTP
    print(f"\n🔐 Verifying OTP: {otp}...")
    url = f"{BASE_URL}/api/delivery-mobile/auth/verify-otp"
    data = {"email": email, "otp": otp}
    
    try:
        response = requests.post(url, json=data)
        print(f"📥 Response Status: {response.status_code}")
        print(f"📥 Response Body: {response.text}")
        
        if response.status_code == 200:
            response_data = response.json()
            
            if "decrypted_data" in response_data:
                decrypted_data = response_data["decrypted_data"]
                auth_token = decrypted_data.get("auth_token")
                
                if auth_token:
                    print(f"🔑 Auth Token: {auth_token[:20]}...")
                    
                    # Step 4: Test protected endpoint
                    print(f"\n🔒 Testing protected endpoint...")
                    url = f"{BASE_URL}/api/delivery/onboard"
                    headers = {"Authorization": f"Bearer {auth_token}"}
                    
                    response = requests.get(url, headers=headers)
                    print(f"📥 Response Status: {response.status_code}")
                    print(f"📥 Response Body: {response.text}")
                    
                    if response.status_code == 200:
                        print("✅ Complete flow successful!")
                        return True
                    else:
                        print("❌ Protected endpoint failed!")
                        return False
                else:
                    print("❌ No auth token!")
                    return False
            else:
                print("❌ No decrypted data!")
                return False
        else:
            print("❌ OTP verification failed!")
            return False
            
    except Exception as e:
        print(f"❌ OTP verification failed: {e}")
        return False

if __name__ == "__main__":
    print("🚚 Delivery Authentication Flow Test")
    print("=" * 50)
    
    print("Choose test mode:")
    print("1. Test with hardcoded OTP (will fail but shows flow)")
    print("2. Test with real OTP (requires manual input)")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        test_complete_auth_flow()
    elif choice == "2":
        test_with_real_otp()
    else:
        print("❌ Invalid choice!")
    
    print("\n�� Test completed!")
