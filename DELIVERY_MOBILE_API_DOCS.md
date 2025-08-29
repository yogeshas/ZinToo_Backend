# Delivery Guy Mobile App API Documentation

## 🚚 **Complete Mobile App Backend for Delivery Guys**

### **Base URL**: `http://localhost:5000/api/delivery-mobile`

---

## 🔐 **Authentication Flow**

### **1. Send OTP**
**POST** `/auth/send-otp`

**Request Body:**
```json
{
  "email": "delivery@example.com"
}
```

**Response:**
```json
{
  "success": true,
  "message": "OTP sent successfully"
}
```

### **2. Verify OTP & Login/Register**
**POST** `/auth/verify-otp`

**Request Body:**
```json
{
  "email": "delivery@example.com",
  "otp": "123456"
}
```

**Response (New User):**
```json
{
  "success": true,
  "encrypted_data": "ENCRYPTED_DATA",
  "decrypted_data": {
    "success": true,
    "message": "New user created",
    "is_new_user": true,
    "is_onboarded": false,
    "auth_token": "abc123...",
    "user": {
      "id": 1,
      "email": "delivery@example.com",
      "phone_number": "",
      "is_verified": true,
      "is_onboarded": false,
      "delivery_guy_id": null
    }
  }
}
```

**Response (Existing User):**
```json
{
  "success": true,
  "encrypted_data": "ENCRYPTED_DATA",
  "decrypted_data": {
    "success": true,
    "message": "Login successful",
    "is_new_user": false,
    "is_onboarded": true,
    "auth_token": "abc123...",
    "user": {
      "id": 1,
      "email": "delivery@example.com",
      "phone_number": "+91-9876543210",
      "is_verified": true,
      "is_onboarded": true,
      "delivery_guy_id": 1
    }
  }
}
```

### **3. Complete Onboarding (New Users Only)**
**POST** `/auth/onboarding`

**Headers:**
```
Authorization: Bearer YOUR_AUTH_TOKEN
```

**Request Body:**
```json
{
  "payload": "ENCRYPTED_DATA",
  "decrypted_data": {
    "phone_number": "+91-9876543210",
    "name": "Rahul Kumar",
    "vehicle_type": "bike",
    "vehicle_number": "DL-01-AB-1234"
  }
}
```

**Response:**
```json
{
  "success": true,
  "encrypted_data": "ENCRYPTED_DATA",
  "decrypted_data": {
    "success": true,
    "message": "Onboarding completed successfully",
    "delivery_guy": {
      "id": 1,
      "name": "Rahul Kumar",
      "phone_number": "+91-9876543210",
      "email": "delivery@example.com",
      "vehicle_type": "bike",
      "vehicle_number": "DL-01-AB-1234",
      "status": "active",
      "rating": 0.0,
      "total_deliveries": 0,
      "completed_deliveries": 0
    }
  }
}
```

### **4. Logout**
**POST** `/auth/logout`

**Headers:**
```
Authorization: Bearer YOUR_AUTH_TOKEN
```

**Response:**
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

---

## 📊 **Dashboard & Profile**

### **5. Get Dashboard Data**
**GET** `/dashboard`

**Headers:**
```
Authorization: Bearer YOUR_AUTH_TOKEN
```

**Response:**
```json
{
  "success": true,
  "encrypted_data": "ENCRYPTED_DATA",
  "decrypted_data": {
    "delivery_guy": {
      "id": 1,
      "name": "Rahul Kumar",
      "phone_number": "+91-9876543210",
      "email": "delivery@example.com",
      "vehicle_type": "bike",
      "vehicle_number": "DL-01-AB-1234",
      "status": "active",
      "rating": 4.5,
      "total_deliveries": 25,
      "completed_deliveries": 23,
      "active_orders_count": 2
    },
    "stats": {
      "total_orders": 25,
      "active_orders": 2,
      "completed_orders": 23,
      "today_orders": 3,
      "rating": 4.5,
      "total_earnings": 12500.0
    },
    "recent_orders": [
      {
        "id": 1,
        "order_number": "ORD202508230845301",
        "status": "out_for_delivery",
        "total_amount": 1595.0,
        "delivery_address": "123 Test Street, New Delhi",
        "customer_id": 1
      }
    ]
  }
}
```

### **6. Get Profile**
**GET** `/profile`

**Headers:**
```
Authorization: Bearer YOUR_AUTH_TOKEN
```

**Response:**
```json
{
  "success": true,
  "encrypted_data": "ENCRYPTED_DATA",
  "decrypted_data": {
    "delivery_guy": {
      "id": 1,
      "name": "Rahul Kumar",
      "phone_number": "+91-9876543210",
      "email": "delivery@example.com",
      "vehicle_type": "bike",
      "vehicle_number": "DL-01-AB-1234",
      "status": "active",
      "rating": 4.5,
      "total_deliveries": 25,
      "completed_deliveries": 23,
      "active_orders_count": 2
    },
    "user": {
      "id": 1,
      "email": "delivery@example.com",
      "phone_number": "+91-9876543210",
      "is_verified": true,
      "is_onboarded": true,
      "delivery_guy_id": 1
    }
  }
}
```

### **7. Update Profile**
**PUT** `/profile/update`

**Headers:**
```
Authorization: Bearer YOUR_AUTH_TOKEN
```

**Request Body:**
```json
{
  "payload": "ENCRYPTED_DATA",
  "decrypted_data": {
    "name": "Rahul Kumar Updated",
    "phone_number": "+91-9876543211",
    "vehicle_type": "car",
    "vehicle_number": "DL-02-CD-5678",
    "current_location": "Connaught Place, New Delhi"
  }
}
```

**Response:**
```json
{
  "success": true,
  "encrypted_data": "ENCRYPTED_DATA",
  "decrypted_data": {
    "delivery_guy": {
      "id": 1,
      "name": "Rahul Kumar Updated",
      "phone_number": "+91-9876543211",
      "email": "delivery@example.com",
      "vehicle_type": "car",
      "vehicle_number": "DL-02-CD-5678",
      "current_location": "Connaught Place, New Delhi",
      "status": "active",
      "rating": 4.5,
      "total_deliveries": 25,
      "completed_deliveries": 23,
      "active_orders_count": 2
    }
  }
}
```

---

## 📦 **Orders Management**

### **8. Get All Orders**
**GET** `/orders`

**Headers:**
```
Authorization: Bearer YOUR_AUTH_TOKEN
```

**Response:**
```json
{
  "success": true,
  "encrypted_data": "ENCRYPTED_DATA",
  "decrypted_data": {
    "orders": [
      {
        "id": 1,
        "order_number": "ORD202508230845301",
        "status": "out_for_delivery",
        "total_amount": 1595.0,
        "delivery_address": "123 Test Street, New Delhi",
        "customer_id": 1,
        "delivery_guy_id": 1,
        "assigned_at": "2025-08-23T08:45:30",
        "delivery_notes": "Fragile items"
      }
    ]
  }
}
```

### **9. Get Active Orders**
**GET** `/orders/active`

**Headers:**
```
Authorization: Bearer YOUR_AUTH_TOKEN
```

**Response:**
```json
{
  "success": true,
  "encrypted_data": "ENCRYPTED_DATA",
  "decrypted_data": {
    "orders": [
      {
        "id": 1,
        "order_number": "ORD202508230845301",
        "status": "out_for_delivery",
        "total_amount": 1595.0,
        "delivery_address": "123 Test Street, New Delhi",
        "customer_id": 1,
        "delivery_guy_id": 1,
        "assigned_at": "2025-08-23T08:45:30",
        "delivery_notes": "Fragile items"
      }
    ]
  }
}
```

---

## 🔄 **Complete User Flow**

### **New User Flow:**
1. **Send OTP** → Enter email
2. **Verify OTP** → Get auth token, `is_new_user: true`
3. **Complete Onboarding** → Add phone, name, vehicle details
4. **Access Dashboard** → View orders and stats

### **Existing User Flow:**
1. **Send OTP** → Enter email
2. **Verify OTP** → Get auth token, `is_new_user: false`
3. **Access Dashboard** → View orders and stats

---

## 🛠️ **Setup Instructions**

### **1. Create Database Tables**
```bash
cd ZinToo_Backend-main
python3 create_delivery_auth_tables.py
```

### **2. Configure Email Settings (Optional)**
Set environment variables for email:
```bash
export SMTP_SERVER=smtp.gmail.com
export SMTP_PORT=587
export SMTP_USERNAME=your-email@gmail.com
export SMTP_PASSWORD=your-app-password
```

### **3. Start Backend**
```bash
python3 app.py
```

---

## 📱 **Mobile App Integration**

### **Authentication Headers**
For all authenticated requests, include:
```
Authorization: Bearer YOUR_AUTH_TOKEN
Content-Type: application/json
```

### **Error Handling**
All APIs return consistent error format:
```json
{
  "error": "Error message"
}
```

### **Success Response Format**
```json
{
  "success": true,
  "encrypted_data": "ENCRYPTED_DATA"
}
```

---

## 🎯 **Key Features**

✅ **Email OTP Authentication**  
✅ **New User Onboarding**  
✅ **Existing User Login**  
✅ **Dashboard with Stats**  
✅ **Order Management**  
✅ **Profile Management**  
✅ **Token-based Authentication**  
✅ **Encrypted Responses**  
✅ **Error Handling**  

---

## 🚀 **Ready for Mobile App Development!**

The backend is now complete with:
- **Authentication system** with email OTP
- **User onboarding** for new delivery guys
- **Dashboard** with performance metrics
- **Order management** for assigned orders
- **Profile management** for delivery guys
- **Secure API endpoints** with token authentication

You can now build your mobile app using these APIs! 📱✨
