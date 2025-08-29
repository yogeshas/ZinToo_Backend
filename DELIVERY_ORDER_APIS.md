# Delivery Order APIs Documentation

## Overview
This document outlines all the APIs available for delivery personnel to manage orders, including viewing orders by status and approving/rejecting orders.

## Base URL
All APIs are prefixed with `/api/delivery`

## Authentication
All APIs require a valid Bearer token in the Authorization header:
```
Authorization: Bearer <your_auth_token>
```

## API Endpoints

### 1. View All Assigned Orders
**GET** `/api/delivery/orders`

**Description**: Get all orders assigned to the authenticated delivery personnel.

**Query Parameters**:
- `status` (optional): Filter orders by status
  - `approved` - Active orders (confirmed, processing, shipped, out_for_delivery)
  - `assigned` - All assigned orders regardless of status
  - `cancelled` - Cancelled orders
  - `delivered` - Completed orders
  - `rejected` - Rejected orders

**Response**:
```json
{
  "success": true,
  "encrypted_data": "encrypted_order_data"
}
```

### 2. View Approved/Active Orders
**GET** `/api/delivery/orders/approved`

**Description**: Get all active orders that are approved and ready for delivery.

**Response**:
```json
{
  "success": true,
  "encrypted_data": "encrypted_order_data"
}
```

### 3. View Cancelled Orders
**GET** `/api/delivery/orders/cancelled`

**Description**: Get all cancelled orders assigned to the delivery personnel.

**Response**:
```json
{
  "success": true,
  "encrypted_data": "encrypted_order_data"
}
```

### 4. View Delivered/Completed Orders
**GET** `/api/delivery/orders/delivered`

**Description**: Get all completed orders that have been delivered.

**Response**:
```json
{
  "success": true,
  "encrypted_data": "encrypted_order_data"
}
```

### 5. View Rejected Orders
**GET** `/api/delivery/orders/rejected`

**Description**: Get all rejected orders assigned to the delivery personnel.

**Response**:
```json
{
  "success": true,
  "encrypted_data": "encrypted_order_data"
}
```

### 6. View Order Details
**GET** `/api/delivery/orders/{order_id}`

**Description**: Get detailed information about a specific order.

**Path Parameters**:
- `order_id` (integer): The ID of the order to view

**Response**:
```json
{
  "success": true,
  "encrypted_data": "encrypted_order_detail"
}
```

### 7. Approve Order
**POST** `/api/delivery/orders/{order_id}/approve`

**Description**: Approve an order by the delivery personnel. This changes the order status to "confirmed".

**Path Parameters**:
- `order_id` (integer): The ID of the order to approve

**Response**:
```json
{
  "success": true,
  "encrypted_data": "encrypted_approval_data"
}
```

**Notes**:
- Only orders with status "pending" can be approved
- Orders with status "delivered", "cancelled", or "rejected" cannot be approved
- Approval adds a note to the order's delivery_notes field

### 8. Reject Order
**POST** `/api/delivery/orders/{order_id}/reject`

**Description**: Reject an order by the delivery personnel. This changes the order status to "rejected".

**Path Parameters**:
- `order_id` (integer): The ID of the order to reject

**Request Body**:
```json
{
  "rejection_reason": "Reason for rejecting the order"
}
```

**Response**:
```json
{
  "success": true,
  "encrypted_data": "encrypted_rejection_data"
}
```

**Notes**:
- Only orders with status "pending", "confirmed", "processing", "shipped", or "out_for_delivery" can be rejected
- Orders with status "delivered" or "cancelled" cannot be rejected
- Rejection adds a note to the order's delivery_notes field with the rejection reason

## Order Status Flow

```
pending → confirmed → processing → shipped → out_for_delivery → delivered
   ↓           ↓         ↓         ↓           ↓
rejected   rejected   rejected   rejected     rejected
   ↓
cancelled
```

## Error Responses

All APIs return error responses in the following format:

```json
{
  "error": "Error message description"
}
```

Common HTTP status codes:
- `200` - Success
- `400` - Bad Request (invalid data)
- `401` - Unauthorized (invalid/missing token)
- `403` - Forbidden (delivery personnel not approved)
- `404` - Not Found (order not found)
- `500` - Internal Server Error

## Usage Examples

### Approving an Order
```bash
curl -X POST "https://your-api.com/api/delivery/orders/123/approve" \
  -H "Authorization: Bearer your_auth_token" \
  -H "Content-Type: application/json"
```

### Rejecting an Order
```bash
curl -X POST "https://your-api.com/api/delivery/orders/123/reject" \
  -H "Authorization: Bearer your_auth_token" \
  -H "Content-Type: application/json" \
  -d '{"rejection_reason": "Customer address not accessible"}'
```

### Viewing Rejected Orders
```bash
curl -X GET "https://your-api.com/api/delivery/orders/rejected" \
  -H "Authorization: Bearer your_auth_token"
```

## Notes

1. **Encryption**: All response data is encrypted using the system's encryption mechanism
2. **Audit Trail**: All approve/reject actions are logged in the order's delivery_notes field
3. **Status Validation**: The system prevents invalid status transitions
4. **Authorization**: Only approved delivery personnel can access these APIs
5. **Order Assignment**: Delivery personnel can only view and manage orders assigned to them
