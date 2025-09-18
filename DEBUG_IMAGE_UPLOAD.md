# 🔍 Debug Image Upload - What You'll See

## Debug Logging Added

I've added comprehensive debug logging to track exactly what's happening when `yogeshas918899@gmail.com` tries to update their profile photos.

## What the Debug Logs Will Show

### 1. **Mobile App Side** (`api_service_updated.dart`)
```
🔍 [DEBUG MOBILE APP] Making PUT request to update delivery onboarding: http://dev.zintoo.in:5000/api/delivery/onboard
🔍 [DEBUG] Headers: {Authorization: Bearer <token>, ...}
🔍 [DEBUG] Form fields: {first_name: Yogesh, last_name: Test, ...}
🔍 [DEBUG] Files count: 6
🔍 [DEBUG] File 0: field=profile_picture, filename=IMG_123.jpg, length=12345
🔍 [DEBUG] File 1: field=aadhar_card, filename=IMG_124.jpg, length=12346
🔍 [DEBUG] File 2: field=pan_card, filename=IMG_125.jpg, length=12347
🔍 [DEBUG] File 3: field=dl, filename=IMG_126.jpg, length=12348
🔍 [DEBUG] File 4: field=rc_card, filename=IMG_127.jpg, length=12349
🔍 [DEBUG] File 5: field=bank_passbook, filename=IMG_128.jpg, length=12350
```

### 2. **Backend Route** (`routes/delivery_onboarding.py`)
```
🔍 [DEBUG UPDATE ONBOARDING] Processing files for email: yogeshas918899@gmail.com
🔍 [DEBUG] Available files: ['profile_picture', 'aadhar_card', 'pan_card', 'dl', 'rc_card', 'bank_passbook']
🔍 [DEBUG] Form data received: {'first_name': 'Yogesh', 'last_name': 'Test', ...}
🔍 [DEBUG] Checking 5 document fields: ['aadhar_card', 'pan_card', 'dl', 'rc_card', 'bank_passbook']

🔍 [DEBUG] Found aadhar_card file: filename='IMG_124.jpg', content_type='image/jpeg', size=12346
🔍 [DEBUG] Processing aadhar_card: IMG_124.jpg
✅ [SUCCESS] Uploaded aadhar_card to S3: https://zintoodev.s3.ap-south-1.amazonaws.com/delivery_onboarding/document_abc123.jpg
🔍 [DEBUG] Updated data[aadhar_card] = https://zintoodev.s3.ap-south-1.amazonaws.com/delivery_onboarding/document_abc123.jpg

🔍 [DEBUG] Found profile_picture file: filename='IMG_123.jpg', content_type='image/jpeg', size=12345
🔍 [DEBUG] Processing profile_picture: IMG_123.jpg
✅ [SUCCESS] Uploaded profile_picture to S3: https://zintoodev.s3.ap-south-1.amazonaws.com/delivery_onboarding/image_def456.jpg
🔍 [DEBUG] Updated data[profile_picture] = https://zintoodev.s3.ap-south-1.amazonaws.com/delivery_onboarding/image_def456.jpg

🔍 [DEBUG] Final data to be updated: {'first_name': 'Yogesh', 'profile_picture': 'https://...', 'aadhar_card': 'https://...', ...}
🔍 [DEBUG] Images in data: [('profile_picture', 'https://...'), ('aadhar_card', 'https://...'), ...]
```

### 3. **Database Update Service** (`services/delivery_onboarding_service.py`)
```
🔍 [DEBUG UPDATE SERVICE] Updating onboarding ID: 123
🔍 [DEBUG] Data received: {'first_name': 'Yogesh', 'profile_picture': 'https://...', ...}
🔍 [DEBUG] Found onboarding record: yogeshas918899@gmail.com
🔍 [DEBUG] Current image fields before update:
  - profile_picture: null
  - aadhar_card: null
  - pan_card: null
  - dl: null
  - rc_card: null
  - bank_passbook: null

🔍 [DEBUG] Set profile_picture = https://zintoodev.s3.ap-south-1.amazonaws.com/delivery_onboarding/image_def456.jpg
🔍 [DEBUG] Set aadhar_card = https://zintoodev.s3.ap-south-1.amazonaws.com/delivery_onboarding/document_abc123.jpg
🔍 [DEBUG] Set pan_card = https://zintoodev.s3.ap-south-1.amazonaws.com/delivery_onboarding/document_xyz789.jpg
🔍 [DEBUG] Updated fields: ['profile_picture: null -> https://...', 'aadhar_card: null -> https://...', ...]
🔍 [DEBUG] Committing to database...
✅ [SUCCESS] Database updated successfully
🔍 [DEBUG] Final image fields after update:
  - profile_picture: https://zintoodev.s3.ap-south-1.amazonaws.com/delivery_onboarding/image_def456.jpg
  - aadhar_card: https://zintoodev.s3.ap-south-1.amazonaws.com/delivery_onboarding/document_abc123.jpg
  - pan_card: https://zintoodev.s3.ap-south-1.amazonaws.com/delivery_onboarding/document_xyz789.jpg
  - dl: https://zintoodev.s3.ap-south-1.amazonaws.com/delivery_onboarding/document_abc456.jpg
  - rc_card: https://zintoodev.s3.ap-south-1.amazonaws.com/delivery_onboarding/document_def789.jpg
  - bank_passbook: https://zintoodev.s3.ap-south-1.amazonaws.com/delivery_onboarding/document_ghi123.jpg
```

## How to See the Debug Logs

1. **Check the terminal where your Flask app is running**
2. **Look for lines starting with 🔍 [DEBUG]**
3. **The logs will show exactly:**
   - What files are being sent from the mobile app
   - What files are received by the backend
   - Whether S3 uploads are successful
   - What data is being saved to the database
   - The final values in the database after update

## What to Look For

### ✅ **If Working Correctly:**
- All files show as "Found" and "Processing"
- S3 uploads show "✅ [SUCCESS]"
- Database shows "Set field = URL"
- Final fields show the S3 URLs

### ❌ **If There's an Issue:**
- Files show as "not found in request files"
- S3 uploads show "❌ [ERROR]"
- Database shows "Field not found in onboarding model"
- Final fields still show "null"

## Next Steps

1. **Test the mobile app** - Try updating profile photos
2. **Check the terminal logs** - Look for the debug output
3. **Share the logs** - Copy the debug output so we can see exactly what's happening

The debug logs will tell us exactly where the problem is occurring!
