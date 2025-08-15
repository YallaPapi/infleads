# MailTester.ninja API Documentation

## Overview
MailTester.ninja provides a REST API for email verification services. The API uses a two-step authentication process with temporary tokens.

## Authentication

### Token Generation
Tokens are required for all API requests and are valid for 24 hours.

**Endpoint:** `https://token.mailtester.ninja/token`  
**Method:** GET  
**Parameters:**
- `key` (required): Your API key

**Example Request:**
```bash
GET https://token.mailtester.ninja/token?key=YOUR_API_KEY
```

**Example Response:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires": "2024-01-15T12:00:00Z",
  "status": "success"
}
```

## Email Verification

### Single Email Verification
Verify a single email address.

**Endpoint:** `https://happy.mailtester.ninja/ninja`  
**Method:** GET  
**Parameters:**
- `email` (required): Email address to verify
- `token` (required): Authentication token

**Example Request:**
```bash
GET https://happy.mailtester.ninja/ninja?email=john.doe@example.com&token=YOUR_TOKEN
```

**Example Response:**
```json
{
  "email": "john.doe@example.com",
  "user": "john.doe",
  "domain": "example.com",
  "status": "valid",
  "score": 0.95,
  "mx": {
    "accepts_mail": true,
    "records": [
      {
        "priority": 10,
        "host": "mail.example.com"
      }
    ]
  },
  "smtp": {
    "valid": true,
    "reason": "250 OK"
  },
  "disposable": false,
  "role_based": false,
  "catch_all": false,
  "free": false,
  "code": 200,
  "message": "Email is valid and deliverable",
  "connections": {
    "smtp": true,
    "mx": true,
    "dns": true
  }
}
```

## Response Status Codes

### Email Status Values
- `valid`: Email is valid and deliverable
- `invalid`: Email is invalid or undeliverable
- `catch-all`: Domain accepts all emails (catch-all)
- `disposable`: Temporary/disposable email address
- `role-based`: Role-based address (info@, support@, etc.)
- `unknown`: Unable to determine status

### HTTP Status Codes
- `200`: Success
- `400`: Bad Request (missing parameters)
- `401`: Unauthorized (invalid or expired token)
- `429`: Rate limit exceeded
- `500`: Internal server error

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `email` | string | The email address that was verified |
| `user` | string | Local part of the email (before @) |
| `domain` | string | Domain part of the email (after @) |
| `status` | string | Verification status |
| `score` | float | Confidence score (0-1) |
| `mx.accepts_mail` | boolean | Whether domain has valid MX records |
| `mx.records` | array | List of MX records for domain |
| `smtp.valid` | boolean | SMTP verification result |
| `smtp.reason` | string | SMTP response message |
| `disposable` | boolean | Is disposable email |
| `role_based` | boolean | Is role-based email |
| `catch_all` | boolean | Domain is catch-all |
| `free` | boolean | Is free email provider |
| `code` | integer | Response code |
| `message` | string | Human-readable message |
| `connections` | object | Connection test results |

## Rate Limits
- Default: 100 requests per minute
- Burst: 500 requests per hour
- Daily limit: Varies by plan

## Best Practices

### Token Management
```python
import requests
import time
from datetime import datetime, timedelta

class MailTesterClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.token = None
        self.token_expires = None
    
    def get_token(self):
        """Get or refresh token if expired"""
        if self.token and self.token_expires > datetime.now():
            return self.token
        
        response = requests.get(
            f"https://token.mailtester.ninja/token",
            params={"key": self.api_key}
        )
        
        if response.status_code == 200:
            data = response.json()
            self.token = data["token"]
            # Refresh 1 hour before expiry
            self.token_expires = datetime.now() + timedelta(hours=23)
            return self.token
        else:
            raise Exception(f"Failed to get token: {response.status_code}")
    
    def verify_email(self, email):
        """Verify a single email address"""
        token = self.get_token()
        
        response = requests.get(
            "https://happy.mailtester.ninja/ninja",
            params={
                "email": email,
                "token": token
            }
        )
        
        if response.status_code == 401:
            # Token expired, refresh and retry
            self.token = None
            token = self.get_token()
            response = requests.get(
                "https://happy.mailtester.ninja/ninja",
                params={"email": email, "token": token}
            )
        
        return response.json()
```

### Batch Processing
```python
def verify_batch(emails, client):
    """Verify multiple emails with rate limiting"""
    results = []
    
    for email in emails:
        try:
            result = client.verify_email(email)
            results.append(result)
            
            # Rate limiting (100/min = 0.6 seconds between requests)
            time.sleep(0.6)
            
        except Exception as e:
            results.append({
                "email": email,
                "status": "error",
                "message": str(e)
            })
    
    return results
```

### Error Handling
```python
def verify_with_retry(email, client, max_retries=3):
    """Verify email with exponential backoff retry"""
    for attempt in range(max_retries):
        try:
            return client.verify_email(email)
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise
            
            # Exponential backoff: 2^attempt seconds
            wait_time = 2 ** attempt
            time.sleep(wait_time)
```

## Integration Example (Node.js)
```javascript
const axios = require('axios');

class MailTesterClient {
    constructor(apiKey) {
        this.apiKey = apiKey;
        this.token = null;
        this.tokenExpires = null;
    }
    
    async getToken() {
        if (this.token && this.tokenExpires > Date.now()) {
            return this.token;
        }
        
        const response = await axios.get('https://token.mailtester.ninja/token', {
            params: { key: this.apiKey }
        });
        
        this.token = response.data.token;
        this.tokenExpires = Date.now() + (23 * 60 * 60 * 1000); // 23 hours
        
        return this.token;
    }
    
    async verifyEmail(email) {
        const token = await this.getToken();
        
        try {
            const response = await axios.get('https://happy.mailtester.ninja/ninja', {
                params: { email, token }
            });
            
            return response.data;
        } catch (error) {
            if (error.response?.status === 401) {
                // Token expired, refresh and retry
                this.token = null;
                const newToken = await this.getToken();
                
                const response = await axios.get('https://happy.mailtester.ninja/ninja', {
                    params: { email, token: newToken }
                });
                
                return response.data;
            }
            throw error;
        }
    }
}

// Usage
const client = new MailTesterClient('YOUR_API_KEY');
const result = await client.verifyEmail('test@example.com');
console.log(result);
```

## Webhook Support
Currently not documented - contact support for webhook integration.

## Support
- Email: support@mailtester.ninja
- Documentation: https://mailtester-ninja.gitbook.io/
- API Status: https://status.mailtester.ninja/

## Notes
- Token expiration is strictly enforced at 24 hours
- Consider implementing token refresh logic for long-running processes
- Cache verification results to avoid duplicate API calls
- Use connection pooling for better performance
- Implement circuit breaker pattern for resilience