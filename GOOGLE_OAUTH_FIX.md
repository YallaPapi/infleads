# Fix Google OAuth redirect_uri_mismatch Error

## Quick Fix Steps

### 1. Go to Google Cloud Console
Visit: https://console.cloud.google.com/apis/credentials

### 2. Find Your OAuth 2.0 Client
- Look for the OAuth 2.0 Client ID you're using
- Click on it to edit

### 3. Add Authorized Redirect URIs
Add ALL of these URIs to the "Authorized redirect URIs" section:
- `http://localhost/`
- `http://localhost:8080/`
- `http://localhost:8080`
- `http://127.0.0.1:8080/`
- `http://127.0.0.1:8080`

Note: The OAuth library uses a random port if not specified, so having multiple redirect URIs ensures compatibility.

### 4. Save Changes
Click "SAVE" at the bottom

### 5. Delete Old Token
Remove the cached token if it exists:
```bash
del token.pickle
```

### 6. Re-run the Application
The app will prompt you to authenticate again with the fixed redirect URI.

## Alternative: Use Service Account (No Popups)

For fully automated operation without OAuth popups:

1. Create a service account in Google Cloud Console
2. Download the JSON key file
3. Rename it to `service_account.json` 
4. Place it in the project root
5. Share your Google Drive folder with the service account email

This eliminates all OAuth issues and popup windows.

## Testing
After fixing, test with:
```bash
python main.py "coffee shops in Austin Texas" --limit 2
```