# Product Requirements Document: MailTester.ninja Email Verification Integration

## Executive Summary
Integration of MailTester.ninja email verification API into the R27 Infinite AI Leads Agent to validate email addresses scraped from Google Maps, ensuring higher quality leads and better deliverability rates.

## Problem Statement
The current R27 system scrapes email addresses from Google Maps but has no way to verify if these emails are valid, active, or deliverable. This results in:
- Wasted resources contacting invalid emails
- Poor deliverability rates
- Lower conversion rates
- Potential damage to sender reputation

## Solution Overview
Integrate MailTester.ninja's email verification API to validate all scraped email addresses before lead scoring and outreach generation.

## Functional Requirements

### 1. API Integration Module
- Create new module: `src/email_verifier.py`
- Implement MailTester.ninja API client with token management
- Handle API authentication and token refresh (24-hour expiry)
- Implement retry logic and error handling

### 2. Token Management System
- Automatically request new token from `https://token.mailtester.ninja/token?key=API_KEY`
- Store token with expiration timestamp
- Auto-refresh token before expiration (23-hour refresh cycle)
- Handle token failures gracefully with fallback mechanisms

### 3. Email Verification Pipeline
- Integrate verification after data normalization phase
- Verify emails using `https://happy.mailtester.ninja/ninja?email=EMAIL&token=TOKEN`
- Process emails in batches for efficiency
- Cache verification results to avoid duplicate API calls

### 4. Data Schema Updates
Add new fields to lead data structure:
- `email_verified`: Boolean (true/false)
- `email_status`: String (valid/invalid/catch-all/disposable/role-based)
- `email_score`: Float (0-1 confidence score)
- `mx_valid`: Boolean (domain has valid MX records)
- `smtp_valid`: Boolean (SMTP connection successful)
- `verification_date`: Timestamp

### 5. Lead Scoring Integration
- Adjust lead scores based on email verification status:
  - Valid email: +20 points
  - Catch-all: +10 points
  - Role-based: +5 points
  - Invalid/Disposable: -50 points
- Skip invalid emails from further processing

### 6. CSV Export Updates
- Include all verification fields in exported CSV
- Add verification summary statistics to export metadata
- Create separate CSV for invalid emails (quarantine list)

### 7. GUI Dashboard Updates
- Display verification status in real-time
- Show verification statistics:
  - Total emails verified
  - Valid vs Invalid ratio
  - Verification success rate
- Add filter options for email status

### 8. Configuration Management
- Add `MAILTESTER_API_KEY` to environment variables
- Create configuration for verification thresholds
- Allow toggling verification on/off
- Set rate limiting parameters

## Technical Specifications

### API Endpoints
1. **Token Generation**
   - URL: `https://token.mailtester.ninja/token`
   - Method: GET
   - Parameters: `key={API_KEY}`
   - Response: `{token: "...", expires: "..."}`

2. **Email Verification**
   - URL: `https://happy.mailtester.ninja/ninja`
   - Method: GET
   - Parameters: `email={EMAIL}&token={TOKEN}`
   - Response: JSON with verification details

### Error Handling
- 401: Token expired - regenerate token
- 429: Rate limit - implement exponential backoff
- 500: Server error - retry with backoff
- Network errors - queue for retry

### Performance Requirements
- Verify 100 emails per minute minimum
- Cache hit ratio > 80% for duplicate emails
- Token refresh latency < 1 second
- API timeout: 10 seconds per request

## Implementation Phases

### Phase 1: Core Integration (Priority: High)
1. Create email verifier module
2. Implement token management
3. Basic email verification functionality
4. Integration with existing pipeline

### Phase 2: Enhanced Features (Priority: Medium)
1. Batch processing optimization
2. Caching layer implementation
3. Advanced error handling
4. Verification statistics

### Phase 3: UI/UX Updates (Priority: Low)
1. GUI dashboard updates
2. Real-time verification display
3. Export options for verified data
4. Verification reports

## Success Metrics
- Email verification accuracy > 95%
- Reduce bounce rate by 80%
- Increase lead quality score by 30%
- API integration uptime > 99.9%

## Dependencies
- MailTester.ninja API subscription
- Python requests library
- Redis for caching (optional)
- Updated GUI components

## Testing Requirements
1. Unit tests for verifier module
2. Integration tests with mock API
3. Load testing for batch processing
4. End-to-end pipeline testing
5. Token refresh testing
6. Error recovery testing

## Security Considerations
- Store API key in environment variables only
- Never log email addresses in plain text
- Implement rate limiting to prevent abuse
- Use HTTPS for all API calls
- Sanitize email inputs before verification

## Rollback Plan
- Feature flag to disable verification
- Fallback to non-verified pipeline
- Cache previous verification results
- Manual verification option

## Documentation Requirements
1. API integration guide
2. Configuration documentation
3. Troubleshooting guide
4. Performance tuning guide
5. Developer documentation

## Timeline
- Week 1: Core integration and token management
- Week 2: Pipeline integration and testing
- Week 3: UI updates and optimization
- Week 4: Documentation and deployment

## Approval
- Product Owner: [Pending]
- Technical Lead: [Pending]
- QA Lead: [Pending]