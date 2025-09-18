#!/bin/bash

# Test Notification Script using curl
# Usage: ./test_notification_curl.sh

echo "🧪 Testing ZinToo Push Notifications"
echo "====================================="

# Configuration
BASE_URL="http://localhost:5000"
USER_EMAIL="yogeshas91889@gmail.com"

echo "📧 Testing for user: $USER_EMAIL"
echo ""

# Test 1: Register device token (if needed)
echo "1️⃣ Testing device token registration..."
echo "Note: This requires a valid auth token from the mobile app"
echo ""

# Test 2: Send test notification
echo "2️⃣ Testing notification sending..."
echo "Note: This requires a valid auth token from the mobile app"
echo ""

# Example curl commands (you need to replace AUTH_TOKEN with actual token)
echo "📋 Example curl commands:"
echo ""
echo "# Register device token:"
echo "curl -X POST \"$BASE_URL/api/delivery-mobile/notifications/register-device\" \\"
echo "  -H \"Authorization: Bearer YOUR_AUTH_TOKEN\" \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{\"payload\": \"ENCRYPTED_PAYLOAD\"}'"
echo ""
echo "# Send test notification:"
echo "curl -X POST \"$BASE_URL/api/delivery-mobile/notifications/test\" \\"
echo "  -H \"Authorization: Bearer YOUR_AUTH_TOKEN\" \\"
echo "  -H \"Content-Type: application/json\""
echo ""

echo "🔧 To get a valid auth token:"
echo "1. Login to the mobile app with email: $USER_EMAIL"
echo "2. Copy the auth token from the response"
echo "3. Replace YOUR_AUTH_TOKEN in the curl commands above"
echo ""

echo "📱 Or run the Python test script:"
echo "python3 test_notification.py"
