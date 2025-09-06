# Delivery Leave Request System

## Overview
A comprehensive leave management system for delivery personnel with both mobile app and admin panel interfaces.

## Features

### For Delivery Personnel:
- ✅ Apply for leave with date range and reason
- ✅ View all leave requests with status
- ✅ Track approval/rejection status
- ✅ View admin notes for rejected requests

### For Admin:
- ✅ View all leave requests
- ✅ Filter by status (All, Pending, Approved, Rejected)
- ✅ Approve leave requests
- ✅ Reject leave requests with mandatory notes
- ✅ View delivery personnel details

## Backend Implementation

### Database Model
**File**: `models/delivery_leave_request.py`

```python
class DeliveryLeaveRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    delivery_guy_id = db.Column(db.Integer, db.ForeignKey("delivery_onboarding.id"))
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default="pending")  # pending, approved, rejected
    admin_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    reviewed_by = db.Column(db.Integer, db.ForeignKey("admin.id"), nullable=True)
```

### API Endpoints

#### Delivery Personnel Endpoints
- **GET** `/api/leave-requests/delivery/leave-requests` - Get all leave requests for delivery guy
- **POST** `/api/leave-requests/delivery/leave-requests` - Create new leave request

#### Admin Endpoints
- **GET** `/api/leave-requests/admin/leave-requests` - Get all leave requests
- **POST** `/api/leave-requests/admin/leave-requests/{id}/approve` - Approve leave request
- **POST** `/api/leave-requests/admin/leave-requests/{id}/reject` - Reject leave request

### Request/Response Examples

#### Create Leave Request
```json
POST /api/leave-requests/delivery/leave-requests
{
  "start_date": "2024-01-15",
  "end_date": "2024-01-17",
  "reason": "Family emergency - need to attend to personal matters"
}
```

#### Approve Leave Request
```json
POST /api/leave-requests/admin/leave-requests/123/approve
{
  "admin_notes": "Approved - no conflicts with delivery schedule"
}
```

#### Reject Leave Request
```json
POST /api/leave-requests/admin/leave-requests/123/reject
{
  "admin_notes": "Rejected - insufficient notice period. Please apply at least 3 days in advance."
}
```

## Frontend Implementation

### Delivery App Integration

#### 1. Updated Delivery Dashboard
**File**: `delivery_dashboard_with_leave.dart`

Added "Leave Requests" option in the account tab that navigates to the leave management screen.

#### 2. Leave Request Screen
**File**: `leave_request_screen.dart`

**Features:**
- Two-tab interface: "My Requests" and "Apply Leave"
- Date picker for start and end dates
- Reason text field with validation
- Status-based color coding
- Admin notes display
- Refresh functionality

#### 3. API Service
**File**: `api_service_leave_requests.dart`

Handles all API communication for leave requests including:
- Getting leave requests
- Creating new requests
- Admin approval/rejection

### Admin Panel Integration

#### Admin Leave Management Screen
**File**: `admin_leave_management_screen.dart`

**Features:**
- Four-tab interface: All, Pending, Approved, Rejected
- Delivery personnel information display
- One-click approve/reject actions
- Mandatory notes for rejections
- Real-time status updates

## Setup Instructions

### 1. Backend Setup
```bash
# 1. Add the new model to your database
python create_leave_request_table.py

# 2. The API endpoints are automatically registered via app.py
# 3. Start your Flask server
python app.py
```

### 2. Frontend Setup
```dart
// 1. Add the leave request screen to your delivery app
import 'leave_request_screen.dart';

// 2. Update your delivery dashboard to include the leave option
// 3. Add the admin leave management screen to your admin panel
import 'admin_leave_management_screen.dart';
```

### 3. Dependencies
Make sure you have these Flutter packages:
```yaml
dependencies:
  intl: ^0.18.0  # For date formatting
  http: ^0.13.5  # For API calls
```

## Usage Flow

### Delivery Personnel Flow:
1. Open delivery app → Account tab
2. Tap "Leave Requests"
3. Switch to "Apply Leave" tab
4. Select start and end dates
5. Enter reason for leave
6. Submit request
7. View status in "My Requests" tab

### Admin Flow:
1. Open admin panel
2. Navigate to "Leave Management"
3. View pending requests in "Pending" tab
4. Review delivery personnel details and reason
5. Approve or reject with notes
6. Track all requests across different status tabs

## Security Features

- ✅ Authentication required for all endpoints
- ✅ Delivery personnel can only see their own requests
- ✅ Admin authentication for approval/rejection
- ✅ Input validation and sanitization
- ✅ Date validation (no past dates, end date after start date)
- ✅ Overlap prevention (no overlapping approved requests)

## Error Handling

- ✅ Network error handling
- ✅ Validation error messages
- ✅ User-friendly error display
- ✅ Loading states and progress indicators
- ✅ Success/error snackbar notifications

## Future Enhancements

- 📧 Email notifications for status changes
- 📱 Push notifications for mobile app
- 📊 Leave analytics and reporting
- 🔄 Leave request modifications
- 📅 Calendar integration
- 👥 Team leave visibility
- 📋 Leave policies and rules
- 🔔 Reminder notifications

## API Testing

You can test the API endpoints using tools like Postman or curl:

```bash
# Get leave requests (requires auth token)
curl -X GET "http://localhost:5000/api/leave-requests/delivery/leave-requests" \
  -H "Authorization: Bearer YOUR_AUTH_TOKEN"

# Create leave request
curl -X POST "http://localhost:5000/api/leave-requests/delivery/leave-requests" \
  -H "Authorization: Bearer YOUR_AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2024-01-15",
    "end_date": "2024-01-17", 
    "reason": "Family emergency"
  }'
```

## Database Schema

The system creates a new table `delivery_leave_request` with the following structure:

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| delivery_guy_id | Integer | Foreign key to delivery_onboarding |
| start_date | Date | Leave start date |
| end_date | Date | Leave end date |
| reason | Text | Reason for leave |
| status | String(20) | pending/approved/rejected |
| admin_notes | Text | Admin comments |
| created_at | DateTime | Request creation time |
| updated_at | DateTime | Last update time |
| reviewed_at | DateTime | Review completion time |
| reviewed_by | Integer | Admin who reviewed |

This system provides a complete solution for managing delivery personnel leave requests with proper authentication, validation, and user-friendly interfaces.
