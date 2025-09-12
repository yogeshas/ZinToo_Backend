# test_onboarding.py
import requests
import json

BASE_URL = "http://localhost:5000/api"

def test_onboarding_endpoints():
    """Test the onboarding endpoints"""
    
    print("🧪 Testing Delivery Onboarding System")
    print("=" * 50)
    
    # Test health check
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
        else:
            print("❌ Health check failed")
            return
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return
    
    # Test admin onboarding list (will fail without auth, but endpoint exists)
    try:
        response = requests.get(f"{BASE_URL}/delivery/admin/onboarding")
        if response.status_code == 401:  # Unauthorized - endpoint exists
            print("✅ Admin onboarding endpoint exists (requires auth)")
        else:
            print(f"⚠️ Admin onboarding endpoint returned: {response.status_code}")
    except Exception as e:
        print(f"❌ Admin onboarding endpoint error: {e}")
    
    # Test mobile onboarding endpoint (will fail without auth, but endpoint exists)
    try:
        response = requests.get(f"{BASE_URL}/delivery/onboard")
        if response.status_code == 401:  # Unauthorized - endpoint exists
            print("✅ Mobile onboarding endpoint exists (requires auth)")
        else:
            print(f"⚠️ Mobile onboarding endpoint returned: {response.status_code}")
    except Exception as e:
        print(f"❌ Mobile onboarding endpoint error: {e}")
    
    print("\n📋 Endpoint Summary:")
    print("- POST /api/delivery/onboard - Submit onboarding")
    print("- GET /api/delivery/onboard - Get user onboarding")
    print("- PUT /api/delivery/onboard - Update onboarding")
    print("- GET /api/delivery/admin/onboarding - Admin list")
    print("- POST /api/delivery/admin/onboarding/<id>/approve - Approve")
    print("- POST /api/delivery/admin/onboarding/<id>/reject - Reject")
    
    print("\n🎯 Next Steps:")
    print("1. Run migration: python add_delivery_onboarding_migration.py")
    print("2. Test with mobile app using auth token")
    print("3. Test admin panel with admin token")
    print("4. Verify file uploads work correctly")

if __name__ == "__main__":
    test_onboarding_endpoints()
