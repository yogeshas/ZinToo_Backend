# Google OAuth Setup Guide

## Backend Configuration

Your backend is now configured with Google OAuth support. Here's what has been set up:

### 1. Configuration (config.py)
- **Google Client ID**: `882155261447-0ujfdj72iqk9bintaik3pe1anpoonn4e.apps.googleusercontent.com`
- **Redirect URI**: `http://localhost:5000/api/auth/google/callback`
- **Client Secret**: Set via environment variable `GOOGLE_CLIENT_SECRET`

### 2. API Endpoints

#### Get Google OAuth URL
```
GET /api/auth/google
```
Returns the Google OAuth URL for frontend redirection.

#### Google OAuth Callback
```
GET /api/auth/google/callback?code=...
```
Handles the OAuth callback from Google and logs in existing users.

#### Google Registration
```
POST /api/customers/google/register
```
Registers new users with Google OAuth data.

### 3. Frontend Integration

Your frontend code is already set up to work with these endpoints:

```javascript
// Get Google OAuth URL
const response = await fetch(`${API_URL}/api/auth/google`);
const data = await response.json();
if (data.success && data.auth_url) {
    window.location.href = data.auth_url;
}

// Register with Google data
const data = await request("google/register", googleData);
```

## Google Cloud Console Setup

To complete the setup, you need to configure your Google OAuth app:

### 1. Go to Google Cloud Console
- Visit: https://console.cloud.google.com/
- Select your project or create a new one

### 2. Enable Google+ API
- Go to "APIs & Services" > "Library"
- Search for "Google+ API" and enable it

### 3. Configure OAuth Consent Screen
- Go to "APIs & Services" > "OAuth consent screen"
- Choose "External" user type
- Fill in required fields:
  - App name: Your app name
  - User support email: Your email
  - Developer contact: Your email
- Add scopes: `openid`, `email`, `profile`

### 4. Create OAuth 2.0 Credentials
- Go to "APIs & Services" > "Credentials"
- Click "Create Credentials" > "OAuth 2.0 Client IDs"
- Application type: "Web application"
- Name: Your app name
- Authorized redirect URIs:
  - `http://localhost:5000/api/auth/google/callback` (for development)
  - `https://yourdomain.com/api/auth/google/callback` (for production)

### 5. Get Client Secret
- Copy the Client Secret from the credentials page
- Set it in your environment variables:
  ```bash
  export GOOGLE_CLIENT_SECRET="your_client_secret_here"
  ```

## Testing

Run the test script to verify the integration:

```bash
python test_google_oauth.py
```

## Environment Variables

Create a `.env` file in your project root:

```env
GOOGLE_CLIENT_ID=882155261447-0ujfdj72iqk9bintaik3pe1anpoonn4e.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret_here
GOOGLE_REDIRECT_URI=http://localhost:5000/api/auth/google/callback
```

## Frontend Usage

Your frontend is already configured to use these endpoints. The Google OAuth flow will work as follows:

1. User clicks "Continue with Google"
2. Frontend calls `/api/auth/google` to get OAuth URL
3. User is redirected to Google for authentication
4. Google redirects back to `/api/auth/google/callback`
5. Backend processes the callback and either:
   - Logs in existing user, or
   - Returns user data for registration
6. Frontend calls `/api/customers/google/register` if needed
7. User is logged in with JWT token

## Troubleshooting

### Common Issues:

1. **"Invalid client" error**: Check that your Client ID and Secret are correct
2. **"Redirect URI mismatch"**: Ensure the redirect URI in Google Console matches your backend
3. **"Access blocked"**: Check OAuth consent screen configuration
4. **CORS errors**: Ensure your frontend domain is allowed in Google Console

### Debug Steps:

1. Check backend logs for detailed error messages
2. Verify environment variables are loaded correctly
3. Test the OAuth URL generation endpoint
4. Check Google Cloud Console for any restrictions

## Security Notes

- Never commit your Client Secret to version control
- Use environment variables for sensitive configuration
- Consider using different OAuth apps for development and production
- Regularly rotate your Client Secret
