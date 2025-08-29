# 🏠 Address Management System

## 📋 Overview

The Address Management System provides comprehensive CRUD operations for customer addresses with proper validation, error handling, and encryption support.

## 🚀 Quick Start

### 1. **Start the Backend**
```bash
cd ZinToo_Backend-main
python app.py
```

### 2. **Create Sample Data**
```bash
python create_sample_data.py
```

### 3. **Test the API**
```bash
python test_address_api.py
```

## 🌐 API Endpoints

### **Base URL**: `/api/addresses`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/customer/{uid}` | Get all addresses for a customer |
| `GET` | `/{aid}` | Get a specific address by ID |
| `POST` | `/` | Create a new address |
| `PUT/PATCH` | `/{aid}` | Update an existing address |
| `DELETE` | `/{aid}` | Delete an address |

## 📝 API Usage Examples

### **1. Get Customer Addresses**
```bash
GET /api/addresses/customer/1
```

**Response:**
```json
{
  "success": true,
  "addresses": [
    {
      "id": 1,
      "uid": 1,
      "name": "John Doe",
      "type": "home",
      "city": "New York",
      "state": "NY",
      "country": "USA",
      "zip_code": "10001"
    }
  ]
}
```

### **2. Get Specific Address**
```bash
GET /api/addresses/1
```

**Response:**
```json
{
  "success": true,
  "address": {
    "id": 1,
    "uid": 1,
    "name": "John Doe",
    "type": "home",
    "city": "New York",
    "state": "NY",
    "country": "USA",
    "zip_code": "10001"
  }
}
```

### **3. Create New Address**
```bash
POST /api/addresses/
Content-Type: application/json

{
  "uid": 1,
  "name": "John Doe",
  "type": "work",
  "city": "Brooklyn",
  "state": "NY",
  "country": "USA",
  "zip_code": "11201"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Address created successfully",
  "address": {
    "id": 2,
    "uid": 1,
    "name": "John Doe",
    "type": "work",
    "city": "Brooklyn",
    "state": "NY",
    "country": "USA",
    "zip_code": "11201"
  }
}
```

### **4. Update Address**
```bash
PUT /api/addresses/1
Content-Type: application/json

{
  "city": "Los Angeles",
  "state": "CA",
  "zip_code": "90210"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Address updated successfully",
  "address": {
    "id": 1,
    "uid": 1,
    "name": "John Doe",
    "type": "home",
    "city": "Los Angeles",
    "state": "CA",
    "country": "USA",
    "zip_code": "90210"
  }
}
```

### **5. Delete Address**
```bash
DELETE /api/addresses/1
```

**Response:**
```json
{
  "success": true,
  "message": "Address deleted successfully"
}
```

## 🔐 Encryption Support

The API supports encrypted payloads for enhanced security:

```bash
POST /api/addresses/
Content-Type: application/json

{
  "payload": "encrypted_base64_string"
}
```

## 📊 Database Schema

### **Address Table**
```sql
CREATE TABLE address (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    uid INTEGER NOT NULL,
    name VARCHAR(80) NOT NULL,
    type VARCHAR(20) NOT NULL DEFAULT 'home',
    city VARCHAR(50) NOT NULL,
    state VARCHAR(50) NOT NULL,
    country VARCHAR(50) NOT NULL,
    zip_code VARCHAR(20) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (uid) REFERENCES customer(id)
);
```

### **Address Types**
- `home` - Home address
- `work` - Work address  
- `other` - Other address

## 🛡️ Validation Rules

### **Required Fields**
- `uid` - Customer ID (must exist in customer table)
- `name` - Full name
- `city` - City name
- `state` - State/province
- `country` - Country name
- `zip_code` - Postal/ZIP code

### **Field Constraints**
- `name`: 1-80 characters
- `type`: Must be "home", "work", or "other"
- `city`: 1-50 characters
- `state`: 1-50 characters
- `country`: 1-50 characters
- `zip_code`: 1-20 characters

## 🔧 Error Handling

### **Common Error Responses**

#### **400 Bad Request**
```json
{
  "success": false,
  "error": "User ID is required"
}
```

#### **404 Not Found**
```json
{
  "success": false,
  "error": "Address not found"
}
```

#### **500 Internal Server Error**
```json
{
  "success": false,
  "error": "Database connection failed"
}
```

## 🧪 Testing

### **Run All Tests**
```bash
python test_address_api.py
```

### **Test Individual Components**
```bash
# Test database connection
python -c "from app import app, db; print('Database OK')"

# Test models
python -c "from models.address import Address; print('Models OK')"

# Test services
python -c "from services.address_service import create_address; print('Services OK')"
```

## 🚨 Troubleshooting

### **Common Issues**

#### **1. "Address not found" Error**
- Check if the address ID exists in the database
- Verify the customer ID is correct
- Run `python create_sample_data.py` to create test data

#### **2. "Customer not found" Error**
- Ensure the customer exists in the database
- Check the customer ID in the request
- Verify the customer table structure

#### **3. "Database connection failed" Error**
- Check database configuration in `config.py`
- Verify MySQL service is running
- Check database credentials

#### **4. "Invalid field value" Error**
- Ensure all required fields are provided
- Check field length constraints
- Verify field types (e.g., address type must be valid)

### **Debug Commands**
```bash
# Check database tables
python -c "from app import app, db; app.app_context().push(); print(db.engine.execute('SHOW TABLES').fetchall())"

# Check address count
python -c "from app import app, db; from models.address import Address; app.app_context().push(); print(Address.query.count())"

# Check customer count
python -c "from app import app, db; from models.customer import Customer; app.app_context().push(); print(Customer.query.count())"
```

## 📚 Related Files

- **Routes**: `routes/address.py`
- **Services**: `services/address_service.py`
- **Models**: `models/address.py`
- **Tests**: `test_address_api.py`
- **Sample Data**: `create_sample_data.py`

## 🎯 Next Steps

1. **Frontend Integration**: Update frontend to use correct API endpoints
2. **Authentication**: Add JWT token validation for address operations
3. **Address Validation**: Integrate with external address validation services
4. **Geocoding**: Add latitude/longitude coordinates for addresses
5. **Bulk Operations**: Support for bulk address import/export

## 📞 Support

If you encounter issues:
1. Check the error logs in the terminal
2. Run the test scripts to identify problems
3. Verify database connectivity and table structure
4. Check API endpoint URLs and request format
