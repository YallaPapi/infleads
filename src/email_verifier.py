"""
MailTester.ninja Email Verification Module

This module provides email verification functionality using the MailTester.ninja API.
It includes token management, email validation, and comprehensive error handling.
"""

import os
import re
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List
from dataclasses import dataclass
from enum import Enum

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


# Configure logging
logger = logging.getLogger(__name__)


class EmailStatus(Enum):
    """Email verification status enumeration"""
    VALID = "valid"
    INVALID = "invalid"
    CATCH_ALL = "catch-all"
    DISPOSABLE = "disposable"
    ROLE_BASED = "role-based"
    UNKNOWN = "unknown"
    ERROR = "error"


@dataclass
class VerificationResult:
    """Data class for email verification results"""
    email: str
    status: EmailStatus
    score: float = 0.0
    user: str = ""
    domain: str = ""
    mx_valid: bool = False
    smtp_valid: bool = False
    disposable: bool = False
    role_based: bool = False
    catch_all: bool = False
    free_provider: bool = False
    message: str = ""
    verified_at: datetime = None
    raw_response: Dict = None

    def __post_init__(self):
        if self.verified_at is None:
            self.verified_at = datetime.now()

    def to_dict(self) -> Dict:
        """Convert result to dictionary for CSV export"""
        return {
            'email': self.email,
            'email_verified': self.status == EmailStatus.VALID,
            'email_status': self.status.value,
            'email_score': self.score,
            'mx_valid': self.mx_valid,
            'smtp_valid': self.smtp_valid,
            'disposable': self.disposable,
            'role_based': self.role_based,
            'catch_all': self.catch_all,
            'free_provider': self.free_provider,
            'verification_date': self.verified_at.isoformat()
        }


class MailTesterVerifier:
    """
    MailTester.ninja API client for email verification.
    
    This class handles:
    - Token management with automatic refresh
    - Email verification with sanitization
    - Batch processing capabilities
    - Comprehensive error handling
    - Result caching
    """
    
    # API endpoints
    TOKEN_ENDPOINT = "https://token.mailtester.ninja/token"
    VERIFY_ENDPOINT = "https://happy.mailtester.ninja/ninja"
    
    # Rate limiting removed for maximum speed
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the MailTester verifier.
        
        Args:
            api_key: MailTester.ninja API key. If not provided, reads from environment.
        
        Raises:
            ValueError: If no API key is provided or found in environment.
        """
        self.api_key = api_key or os.getenv('MAILTESTER_API_KEY')
        if not self.api_key:
            raise ValueError("MailTester API key not provided. Set MAILTESTER_API_KEY environment variable.")
        
        # Token management
        self._token: Optional[str] = None
        self._token_expires: Optional[datetime] = None
        
        # Result cache (simple in-memory cache)
        self._cache: Dict[str, VerificationResult] = {}
        self._cache_ttl = timedelta(hours=24)
        
        # HTTP session with retry strategy
        self.session = self._create_session()
        
        # Rate limiting removed
        
        logger.info("MailTesterVerifier initialized")
    
    def _create_session(self) -> requests.Session:
        """
        Create HTTP session with retry strategy.
        
        Returns:
            Configured requests.Session instance
        """
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        
        # Set default timeout
        session.request = lambda *args, **kwargs: requests.Session.request(
            session, 
            *args, 
            timeout=kwargs.pop('timeout', 10),
            **kwargs
        )
        
        return session
    
    def _sanitize_email(self, email: str) -> str:
        """
        Sanitize and validate email address.
        
        Args:
            email: Email address to sanitize
            
        Returns:
            Sanitized email address
            
        Raises:
            ValueError: If email is invalid
        """
        if not email:
            raise ValueError("Email address cannot be empty")
        
        # Strip whitespace and convert to lowercase
        email = email.strip().lower()
        
        # Basic RFC-compliant email regex
        email_pattern = re.compile(
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        )
        
        if not email_pattern.match(email):
            raise ValueError(f"Invalid email format: {email}")
        
        # Additional security checks
        if any(char in email for char in ['<', '>', '"', "'", ';', '&', '|', '$', '`']):
            raise ValueError(f"Email contains invalid characters: {email}")
        
        return email
    
    
    def get_token(self, force_refresh: bool = False) -> str:
        """
        Get or refresh authentication token.
        
        Args:
            force_refresh: Force token refresh even if not expired
            
        Returns:
            Valid authentication token
            
        Raises:
            requests.RequestException: If token retrieval fails
        """
        # Check if we have a valid token
        if not force_refresh and self._token and self._token_expires:
            if datetime.now() < self._token_expires:
                return self._token
        
        logger.info("Retrieving new authentication token")
        
        try:
            response = self.session.get(
                self.TOKEN_ENDPOINT,
                params={'key': self.api_key}
            )
            response.raise_for_status()
            
            data = response.json()
            self._token = data.get('token')
            
            if not self._token:
                raise ValueError("No token in response")
            
            # Set expiration to 23 hours (1 hour before actual expiry)
            self._token_expires = datetime.now() + timedelta(hours=23)
            
            logger.info("Successfully retrieved authentication token")
            return self._token
            
        except requests.RequestException as e:
            logger.error(f"Failed to retrieve token: {e}")
            raise
        except (KeyError, ValueError) as e:
            logger.error(f"Invalid token response: {e}")
            raise requests.RequestException(f"Invalid token response: {e}")
    
    def verify_email(self, email: str, use_cache: bool = True) -> VerificationResult:
        """
        Verify a single email address.
        
        Args:
            email: Email address to verify
            use_cache: Whether to use cached results
            
        Returns:
            VerificationResult object with verification details
        """
        try:
            # Sanitize email
            email = self._sanitize_email(email)
            
            # Check cache
            if use_cache and email in self._cache:
                cached_result = self._cache[email]
                if datetime.now() - cached_result.verified_at < self._cache_ttl:
                    logger.debug(f"Using cached result for {email}")
                    return cached_result
            
            # Get token
            token = self.get_token()
            
            # Make verification request
            response = self.session.get(
                self.VERIFY_ENDPOINT,
                params={
                    'email': email,
                    'token': token
                }
            )
            
            # Handle token expiration
            if response.status_code == 401:
                logger.info("Token expired, refreshing...")
                token = self.get_token(force_refresh=True)
                
                # Retry with new token
                response = self.session.get(
                    self.VERIFY_ENDPOINT,
                    params={
                        'email': email,
                        'token': token
                    }
                )
            
            response.raise_for_status()
            
            # Handle different response types
            try:
                data = response.json()
            except ValueError:
                # Response is not JSON
                logger.warning(f"Non-JSON response for {email}: {response.text}")
                return VerificationResult(
                    email=email,
                    status=EmailStatus.ERROR,
                    message=f"Invalid API response format"
                )
            
            # Check if response is a string error message
            if isinstance(data, str):
                logger.warning(f"String response for {email}: {data}")
                return VerificationResult(
                    email=email,
                    status=EmailStatus.ERROR,
                    message=data
                )
            
            # Parse response
            result = self._parse_response(email, data)
            
            # Cache result
            self._cache[email] = result
            
            logger.info(f"Verified {email}: {result.status.value}")
            return result
            
        except ValueError as e:
            # Invalid email format
            logger.warning(f"Invalid email {email}: {e}")
            return VerificationResult(
                email=email,
                status=EmailStatus.INVALID,
                message=str(e)
            )
        except requests.RequestException as e:
            # API error
            logger.error(f"API error verifying {email}: {e}")
            return VerificationResult(
                email=email,
                status=EmailStatus.ERROR,
                message=f"Verification failed: {e}"
            )
        except Exception as e:
            # Unexpected error
            logger.error(f"Unexpected error verifying {email}: {e}")
            return VerificationResult(
                email=email,
                status=EmailStatus.ERROR,
                message=f"Unexpected error: {e}"
            )
    
    def _parse_response(self, email: str, data: Dict) -> VerificationResult:
        """
        Parse API response into VerificationResult.
        
        Args:
            email: Email address being verified
            data: API response data
            
        Returns:
            Parsed VerificationResult
        """
        # Handle case where data is not a dict
        if not isinstance(data, dict):
            logger.warning(f"Invalid data type for {email}: {type(data)}")
            return VerificationResult(
                email=email,
                status=EmailStatus.ERROR,
                message=f"Invalid response data type: {type(data)}"
            )
        
        # Handle MailTester.ninja response format
        code = data.get('code', '').lower()
        message = data.get('message', '')
        detail = data.get('detail', '')
        
        # Determine status based on code and message
        # MailTester.ninja codes: ok=valid, ko=invalid, mb=catch-all/mx-issue
        if code == 'ok' or 'accepted' in message.lower():
            status = EmailStatus.VALID
            score = 100.0
        elif code == 'mb' and 'catch' in message.lower():
            status = EmailStatus.CATCH_ALL
            score = 50.0
        elif code == 'ko' or 'rejected' in message.lower():
            status = EmailStatus.INVALID
            score = 0.0
        elif code == 'mb' and 'mx error' in message.lower():
            status = EmailStatus.INVALID
            score = 0.0
        elif 'disposable' in message.lower():
            status = EmailStatus.DISPOSABLE
            score = 0.0
        elif 'role' in message.lower():
            status = EmailStatus.ROLE_BASED
            score = 30.0
        elif 'spam' in detail.lower() or 'trap' in detail.lower():
            # Special case for spam traps (like example.com)
            status = EmailStatus.INVALID
            score = 0.0
        else:
            status = EmailStatus.UNKNOWN
            score = 0.0
        
        # Extract domain from email
        domain = email.split('@')[1] if '@' in email else ''
        
        # Check for MX validity
        mx_valid = code != 'mb' and code != 'mx' and 'mx error' not in message.lower()
        
        return VerificationResult(
            email=email,
            status=status,
            score=score,
            user=email.split('@')[0] if '@' in email else '',
            domain=domain,
            mx_valid=mx_valid,
            smtp_valid=status == EmailStatus.VALID,
            disposable='disposable' in message.lower() or code == 'disposable',
            role_based='role' in message.lower() or code == 'role',
            catch_all='catch' in message.lower() or code == 'catch_all',
            free_provider=False,  # Not provided by this API
            message=f"{message} - {detail}" if detail else message,
            raw_response=data
        )
    
    def verify_batch(self, emails: List[str], use_cache: bool = True) -> List[VerificationResult]:
        """
        Verify multiple email addresses.
        
        Args:
            emails: List of email addresses to verify
            use_cache: Whether to use cached results
            
        Returns:
            List of VerificationResult objects
        """
        results = []
        total = len(emails)
        
        for i, email in enumerate(emails, 1):
            logger.info(f"Verifying email {i}/{total}: {email}")
            result = self.verify_email(email, use_cache=use_cache)
            results.append(result)
        
        return results
    
    def clear_cache(self):
        """Clear the result cache"""
        self._cache.clear()
        logger.info("Cache cleared")
    
    def get_cache_stats(self) -> Dict:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        valid_entries = sum(
            1 for result in self._cache.values()
            if datetime.now() - result.verified_at < self._cache_ttl
        )
        
        return {
            'total_entries': len(self._cache),
            'valid_entries': valid_entries,
            'expired_entries': len(self._cache) - valid_entries,
            'cache_ttl_hours': self._cache_ttl.total_seconds() / 3600
        }


def integrate_with_pipeline(verifier: MailTesterVerifier, lead_data: Dict) -> Dict:
    """
    Helper function to integrate email verification into the existing pipeline.
    
    Args:
        verifier: MailTesterVerifier instance
        lead_data: Lead data dictionary from Google Maps scraping
        
    Returns:
        Updated lead data with verification results
    """
    email = lead_data.get('email', '')
    
    if not email:
        lead_data.update({
            'email_verified': False,
            'email_status': 'missing',
            'email_score': 0.0,
            'mx_valid': False,
            'smtp_valid': False
        })
        return lead_data
    
    # Verify email
    result = verifier.verify_email(email)
    
    # Update lead data with verification results
    lead_data.update(result.to_dict())
    
    # Adjust lead score based on email verification
    current_score = lead_data.get('lead_score', 50)
    
    if result.status == EmailStatus.VALID:
        lead_data['lead_score'] = min(100, current_score + 20)
    elif result.status == EmailStatus.CATCH_ALL:
        lead_data['lead_score'] = min(100, current_score + 10)
    elif result.status == EmailStatus.ROLE_BASED:
        lead_data['lead_score'] = min(100, current_score + 5)
    elif result.status in [EmailStatus.INVALID, EmailStatus.DISPOSABLE]:
        lead_data['lead_score'] = max(0, current_score - 50)
    
    return lead_data


if __name__ == "__main__":
    # Module can be imported - no demo/test code in production
    pass