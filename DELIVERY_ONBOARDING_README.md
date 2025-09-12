# Delivery Onboarding System

## Overview
Complete delivery partner onboarding system with mobile app integration and admin panel management.

## Key Features
- **Mobile App**: OTP login, onboarding form, file uploads
- **Admin Panel**: Review, approve/reject applications
- **Auto Profile Creation**: Creates delivery guy profile on approval

## API Endpoints

### Mobile App
- `POST /api/delivery/onboard` - Submit onboarding
- `GET /api/delivery/onboard` - Get user onboarding
- `PUT /api/delivery/onboarding` - Update onboarding

### Admin Panel
- `GET /api/delivery/admin/onboarding` - List all
- `POST /api/delivery/admin/onboarding/<id>/approve` - Approve
- `POST /api/delivery/admin/onboarding/<id>/reject` - Reject
- `PUT /api/delivery/admin/onboarding/<id>` - Update
- `DELETE /api/delivery/admin/onboarding/<id>` - Delete

## Database Fields
- Personal: first_name, last_name, dob, phone, address
- Documents: aadhar, pan, dl, vehicle_number
- Bank: account_number, ifsc, passbook
- Status: pending/approved/rejected

## Authentication Flow
1. Email OTP verification
2. New users → onboarding form
3. Existing users → dashboard (if onboarded)
4. Admin approval creates delivery guy profile

## File Uploads
- Profile picture, RC card, bank passbook
- Stored in assets/onboarding/
- UUID-based naming for security

## Migration
Run: `python add_delivery_onboarding_migration.py`
