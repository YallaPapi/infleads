#!/usr/bin/env python3
"""
Integration test for Google Maps scraping + Email verification
"""

import os
import sys
import json
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.providers import get_provider
from src.data_normalizer import DataNormalizer
from src.email_verifier import MailTesterVerifier, EmailStatus

# Load environment variables
load_dotenv()

def test_google_maps_scraping():
    """Test Google Maps data fetching"""
    print("\n" + "="*60)
    print("TESTING GOOGLE MAPS SCRAPING")
    print("="*60)
    
    # Check for Apify API key
    if not os.getenv('APIFY_API_KEY'):
        print("❌ APIFY_API_KEY not found")
        print("Please add to .env file: APIFY_API_KEY=your_key_here")
        return None
    
    print("✅ Apify API key found")
    
    try:
        # Initialize provider
        provider = get_provider('apify')
        print("✅ Apify provider initialized")
        
        # Test with a small query
        query = "coffee shops in Austin"
        limit = 3
        print(f"\nFetching: '{query}' (limit: {limit})")
        
        # Fetch data
        raw_leads = provider.fetch_places(query, limit)
        print(f"✅ Fetched {len(raw_leads)} leads")
        
        # Normalize data
        normalizer = DataNormalizer()
        normalized = normalizer.normalize(raw_leads)
        print(f"✅ Normalized {len(normalized)} leads")
        
        # Display results
        print("\nLead Data:")
        print("-" * 40)
        for i, lead in enumerate(normalized, 1):
            print(f"\n{i}. {lead.get('Name', 'Unknown')}")
            print(f"   Address: {lead.get('Address', 'NA')}")
            print(f"   Phone: {lead.get('Phone', 'NA')}")
            print(f"   Email: {lead.get('Email', 'NA')}")
            print(f"   Website: {lead.get('Website', 'NA')}")
            print(f"   Rating: {lead.get('Rating', 0)}")
            print(f"   Reviews: {lead.get('Reviews', 'NA')}")
        
        return normalized
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_email_verification(leads):
    """Test email verification on real leads"""
    print("\n" + "="*60)
    print("TESTING EMAIL VERIFICATION")
    print("="*60)
    
    if not leads:
        print("❌ No leads to verify")
        return
    
    # Check for MailTester API key
    if not os.getenv('MAILTESTER_API_KEY'):
        print("❌ MAILTESTER_API_KEY not found")
        print("Please add to .env file: MAILTESTER_API_KEY=your_key_here")
        return
    
    print("✅ MailTester API key found")
    
    try:
        # Initialize verifier
        verifier = MailTesterVerifier()
        print("✅ Verifier initialized")
        
        # Test emails from leads
        print("\nVerifying emails from leads:")
        print("-" * 40)
        
        emails_found = False
        for lead in leads:
            email = lead.get('Email', 'NA')
            
            if email and email != 'NA':
                emails_found = True
                print(f"\nVerifying: {email}")
                print(f"From: {lead.get('Name', 'Unknown')}")
                
                result = verifier.verify_email(email)
                
                print(f"Status: {result.status.value}")
                print(f"Score: {result.score}")
                print(f"MX Valid: {result.mx_valid}")
                print(f"SMTP Valid: {result.smtp_valid}")
                
                if result.status == EmailStatus.VALID:
                    print("✅ Valid email!")
                elif result.status == EmailStatus.INVALID:
                    print("❌ Invalid email")
                elif result.status == EmailStatus.CATCH_ALL:
                    print("⚠️ Catch-all domain")
                else:
                    print(f"ℹ️ {result.status.value}")
        
        if not emails_found:
            print("\n⚠️ No emails found in Google Maps data")
            print("This is common - Google Maps doesn't always provide emails")
            print("\nTesting with a known email instead:")
            
            test_email = "test@google.com"
            print(f"\nVerifying: {test_email}")
            result = verifier.verify_email(test_email)
            print(f"Status: {result.status.value}")
            print(f"Score: {result.score}")
            print(f"MX Valid: {result.mx_valid}")
            print(f"SMTP Valid: {result.smtp_valid}")
        
        # Show cache stats
        stats = verifier.get_cache_stats()
        print(f"\nCache Stats:")
        print(f"  Total entries: {stats['total_entries']}")
        print(f"  Valid entries: {stats['valid_entries']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


def test_full_pipeline():
    """Test the complete pipeline"""
    print("\n" + "="*60)
    print("FULL PIPELINE TEST")
    print("="*60)
    
    # Test Google Maps
    leads = test_google_maps_scraping()
    
    if leads:
        # Test Email Verification
        test_email_verification(leads)
        
        print("\n" + "="*60)
        print("✅ INTEGRATION TEST COMPLETE")
        print("="*60)
        
        # Summary
        print("\nSummary:")
        print(f"- Google Maps: ✅ Working ({len(leads)} leads fetched)")
        
        has_emails = any(l.get('Email', 'NA') != 'NA' for l in leads)
        if has_emails:
            print(f"- Email Extraction: ✅ Working")
        else:
            print(f"- Email Extraction: ⚠️ No emails in Google Maps data (common)")
        
        if os.getenv('MAILTESTER_API_KEY'):
            print(f"- Email Verification: ✅ API configured")
        else:
            print(f"- Email Verification: ❌ API key missing")
    else:
        print("\n❌ Pipeline failed at Google Maps stage")


if __name__ == "__main__":
    print("="*60)
    print("R27 INTEGRATION TEST")
    print("Google Maps + Email Verification")
    print("="*60)
    
    # Check environment
    print("\nEnvironment Check:")
    print("-" * 40)
    
    apify_key = "✅" if os.getenv('APIFY_API_KEY') else "❌"
    mailtester_key = "✅" if os.getenv('MAILTESTER_API_KEY') else "❌"
    
    print(f"APIFY_API_KEY: {apify_key}")
    print(f"MAILTESTER_API_KEY: {mailtester_key}")
    
    if apify_key == "❌":
        print("\n⚠️ Missing APIFY_API_KEY - Google Maps won't work")
        print("Get your key from: https://console.apify.com/account/integrations")
    
    if mailtester_key == "❌":
        print("\n⚠️ Missing MAILTESTER_API_KEY - Email verification won't work")
        print("Get your key from: https://mailtester.ninja/")
    
    # Run tests
    test_full_pipeline()