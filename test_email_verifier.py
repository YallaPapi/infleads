#!/usr/bin/env python3
"""
Test script for MailTester.ninja email verification integration
"""

import os
import sys
import json
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.email_verifier import MailTesterVerifier, EmailStatus, VerificationResult

# Load environment variables
load_dotenv()

def test_email_verifier():
    """Test the email verification functionality"""
    
    print("=" * 60)
    print("MailTester.ninja Email Verification Test")
    print("=" * 60)
    
    # Check for API key
    if not os.getenv('MAILTESTER_API_KEY'):
        print("\n❌ ERROR: MAILTESTER_API_KEY not found in environment variables")
        print("Please add your MailTester.ninja API key to .env file:")
        print("MAILTESTER_API_KEY=your_api_key_here")
        return
    
    print("\n✅ API key found")
    
    # Initialize verifier
    try:
        verifier = MailTesterVerifier()
        print("✅ Verifier initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize verifier: {e}")
        return
    
    # Test emails
    test_emails = [
        "test@gmail.com",           # Valid free email
        "info@example.com",          # Role-based email
        "invalid.email",             # Invalid format
        "test@tempmail.com",         # Likely disposable
        "john.doe@microsoft.com",    # Corporate email
        "",                          # Empty email
        "test@nonexistentdomain12345.com"  # Non-existent domain
    ]
    
    print("\n" + "=" * 60)
    print("Testing Individual Email Verification")
    print("=" * 60)
    
    for email in test_emails:
        print(f"\nTesting: '{email}'")
        print("-" * 40)
        
        try:
            result = verifier.verify_email(email)
            
            print(f"Status: {result.status.value}")
            print(f"Score: {result.score}")
            print(f"MX Valid: {result.mx_valid}")
            print(f"SMTP Valid: {result.smtp_valid}")
            print(f"Disposable: {result.disposable}")
            print(f"Role-based: {result.role_based}")
            print(f"Catch-all: {result.catch_all}")
            print(f"Free provider: {result.free_provider}")
            
            if result.message:
                print(f"Message: {result.message}")
            
            # Test dictionary conversion
            dict_result = result.to_dict()
            assert 'email' in dict_result
            assert 'email_verified' in dict_result
            assert 'email_status' in dict_result
            print("✅ Dictionary conversion successful")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Test batch verification
    print("\n" + "=" * 60)
    print("Testing Batch Email Verification")
    print("=" * 60)
    
    batch_emails = [
        "test1@example.com",
        "test2@example.com",
        "test3@example.com"
    ]
    
    try:
        print(f"\nVerifying batch of {len(batch_emails)} emails...")
        results = verifier.verify_batch(batch_emails)
        
        for result in results:
            print(f"  {result.email}: {result.status.value} (score: {result.score})")
        
        print("✅ Batch verification successful")
    except Exception as e:
        print(f"❌ Batch verification failed: {e}")
    
    # Test cache functionality
    print("\n" + "=" * 60)
    print("Testing Cache Functionality")
    print("=" * 60)
    
    cache_stats = verifier.get_cache_stats()
    print(f"Cache entries: {cache_stats['total_entries']}")
    print(f"Valid entries: {cache_stats['valid_entries']}")
    print(f"Expired entries: {cache_stats['expired_entries']}")
    print(f"TTL (hours): {cache_stats['cache_ttl_hours']}")
    
    # Test cached result
    if test_emails[0]:
        print(f"\nRe-verifying '{test_emails[0]}' (should use cache)...")
        result = verifier.verify_email(test_emails[0])
        print(f"Result: {result.status.value} (from cache)")
    
    # Test pipeline integration
    print("\n" + "=" * 60)
    print("Testing Pipeline Integration")
    print("=" * 60)
    
    from src.email_verifier import integrate_with_pipeline
    
    test_lead = {
        'Name': 'Test Company',
        'Address': '123 Main St',
        'Phone': '555-1234',
        'Email': 'contact@testcompany.com',
        'Website': 'https://testcompany.com',
        'lead_score': 50
    }
    
    print(f"\nOriginal lead score: {test_lead['lead_score']}")
    print(f"Email: {test_lead['Email']}")
    
    updated_lead = integrate_with_pipeline(verifier, test_lead)
    
    print(f"Updated lead score: {updated_lead['lead_score']}")
    print(f"Email verified: {updated_lead.get('email_verified', 'N/A')}")
    print(f"Email status: {updated_lead.get('email_status', 'N/A')}")
    print(f"Email score: {updated_lead.get('email_score', 'N/A')}")
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)
    
    # Clear cache
    verifier.clear_cache()
    print("\nCache cleared.")

if __name__ == "__main__":
    test_email_verifier()