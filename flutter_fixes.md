# Flutter Onboarding Screen Fixes

## Key Issues and Solutions

### 1. Import Path Issues
**Problem**: Incorrect import paths
**Solution**: Update import paths in your Flutter code:

```dart
// Update these import paths to match your project structure
import '../../../core/services/api_service.dart';
import './documents_screen.dart';
```

### 2. Form Validation Improvements
**Problem**: Missing validation for some fields
**Solution**: Add proper validation:

```dart
// Add trim() to all text validators
validator: (value) => (value == null || value.trim().isEmpty)
    ? 'Please enter first name'
    : null,
```

### 3. Loading State Management
**Problem**: No loading state during submission
**Solution**: Add loading state:

```dart
bool _isSubmitting = false;

// In _submitForm method:
setState(() {
  _isSubmitting = true;
});

// Disable form fields during submission:
enabled: !_isSubmitting,

// Update submit button:
onPressed: _isSubmitting ? null : _submitForm,
```

### 4. Better Error Handling
**Problem**: Generic error messages
**Solution**: Improve error handling:

```dart
// In _submitForm method:
} catch (e) {
  print('Onboarding error: $e');
  
  ScaffoldMessenger.of(context).showSnackBar(
    SnackBar(
      content: Text('Network error: $e'),
      backgroundColor: Colors.red,
      duration: const Duration(seconds: 5),
    ),
  );
} finally {
  setState(() {
    _isSubmitting = false;
  });
}
```

### 5. Form Data Trimming
**Problem**: Extra whitespace in form data
**Solution**: Trim all form data:

```dart
final formData = {
  'first_name': _firstNameController.text.trim(),
  'last_name': _lastNameController.text.trim(),
  // ... trim all other fields
};
```

### 6. Keyboard Types
**Problem**: Wrong keyboard types for some fields
**Solution**: Set appropriate keyboard types:

```dart
// Bank account number
keyboardType: TextInputType.number,

// IFSC code
keyboardType: TextInputType.text,
textCapitalization: TextCapitalization.characters,

// Vehicle number
keyboardType: TextInputType.text,
```

### 7. Submit Button Loading State
**Problem**: No visual feedback during submission
**Solution**: Add loading indicator:

```dart
child: _isSubmitting
    ? const Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          SizedBox(
            width: 20,
            height: 20,
            child: CircularProgressIndicator(
              strokeWidth: 2,
              valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
            ),
          ),
          SizedBox(width: 12),
          Text(
            'Submitting...',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
          ),
        ],
      )
    : const Text(
        'Complete Setup',
        style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
      ),
```

## Backend Connection Test

To test if your Flutter app can connect to the backend:

1. **Check Base URL**: Ensure `BASE_URL` in your `.env` file is correct:
   ```
   BASE_URL=http://127.0.0.1:5000
   ```

2. **Test API Service**: Add debug prints to your API service:
   ```dart
   print('Making GET request to: $uri');
   print('Headers: $headers');
   print('Response: ${response.statusCode} - ${response.body}');
   ```

3. **Verify Backend**: The backend is now working correctly and should accept requests from your Flutter app.

## Common Issues

1. **404 Error**: Fixed - backend routes are now properly registered
2. **Authentication Error**: Fixed - token validation is working
3. **Form Submission**: Should work with the above fixes
4. **File Upload**: Profile picture upload should work correctly

## Next Steps

1. Apply the fixes above to your Flutter code
2. Test the onboarding submission
3. Check the backend logs for any errors
4. Verify the document upload screen works correctly
