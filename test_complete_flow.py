#!/usr/bin/env python3
"""
Comprehensive test for the complete delivery authentication and onboarding flow
"""
import requests
import json

BASE_URL = "http://localhost:5000"

def test_complete_flow():
    """Test the complete flow: OTP → Auth → Onboarding"""
    print("🚀 Testing Complete Delivery Flow")
    print("=" * 50)
    
    email = "test@example.com"
    auth_token = None
    
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
        print(f"❌ OTP send failed: {e}")
        return False
    
    # Step 2: Get OTP from user
    print("\n🔐 Step 2: Enter the OTP from console...")
    otp = input("Enter OTP: ").strip()
    
    if not otp:
        print("❌ OTP is required!")
        return False
    
    # Step 3: Verify OTP
    print(f"\n🔐 Step 3: Verifying OTP: {otp}...")
    url = f"{BASE_URL}/api/delivery-mobile/auth/verify-otp"
    data = {"email": email, "otp": otp}
    
    try:
        response = requests.post(url, json=data)
        print(f"📥 Response Status: {response.status_code}")
        print(f"📥 Response Body: {response.text}")
        
        if response.status_code == 200:
            response_data = response.json()
            auth_token = response_data.get("auth_token")
            is_onboarded = response_data.get("is_onboarded", False)
            
            if auth_token:
                print(f"✅ OTP verified! Auth Token: {auth_token[:20]}...")
                print(f"📊 Is Onboarded: {is_onboarded}")
                
                # Step 4: Test onboarding endpoints
                print(f"\n🔒 Step 4: Testing onboarding endpoints...")
                
                # Test GET onboarding status
                print("\n📋 Testing GET /api/delivery/onboard...")
                url = f"{BASE_URL}/api/delivery/onboard"
                headers = {"Authorization": f"Bearer {auth_token}"}
                
                try:
                    response = requests.get(url, headers=headers)
                    print(f"📥 Response Status: {response.status_code}")
                    print(f"📥 Response Body: {response.text}")
                    
                    if response.status_code == 200:
                        print("✅ GET onboarding successful!")
                        onboarding_data = response.json()
                        print(f"📊 Onboarding Status: {onboarding_data.get('onboarding', {}).get('status', 'N/A')}")
                    elif response.status_code == 404:
                        print("✅ No onboarding record found (expected for new user)")
                    else:
                        print("❌ GET onboarding failed!")
                        return False
                        
                except Exception as e:
                    print(f"❌ GET onboarding failed: {e}")
                    return False
                
                # Test POST onboarding (create new onboarding)
                if not is_onboarded:
                    print("\n📝 Testing POST /api/delivery/onboard...")
                    url = f"{BASE_URL}/api/delivery/onboard"
                    headers = {"Authorization": f"Bearer {auth_token}"}
                    
                    # Sample onboarding data
                    form_data = {
                        "first_name": "John",
                        "last_name": "Doe",
                        "dob": "1990-01-01",
                        "primary_number": "+91-9876543210",
                        "blood_group": "O+",
                        "address": "123 Test Street, New Delhi",
                        "language": "English",
                        "vehicle_number": "DL-01-AB-1234",
                        "bank_account_number": "1234567890",
                        "ifsc_code": "SBIN0001234",
                        "name_as_per_bank": "John Doe"
                    }
                    
                    try:
                        response = requests.post(url, data=form_data, headers=headers)
                        print(f"📥 Response Status: {response.status_code}")
                        print(f"📥 Response Body: {response.text}")
                        
                        if response.status_code in [200, 201]:
                            print("✅ POST onboarding successful!")
                        else:
                            print("❌ POST onboarding failed!")
                            return False
                            
                    except Exception as e:
                        print(f"❌ POST onboarding failed: {e}")
                        return False
                
                print("\n🎉 Complete flow test successful!")
                return True
                
            else:
                print("❌ No auth token in response!")
                return False
        else:
            print("❌ OTP verification failed!")
            return False
            
    except Exception as e:
        print(f"❌ OTP verification failed: {e}")
        return False

if __name__ == "__main__":
    test_complete_flow()
    print("\n�� Test completed!")
