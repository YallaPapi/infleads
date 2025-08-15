#!/usr/bin/env python3
"""
Test script for R27 Infinite AI Leads Agent
"""

import os
import sys
from dotenv import load_dotenv

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Load environment variables
load_dotenv()

def test_imports():
    """Test all imports work"""
    print("Testing imports...")
    try:
        from src.providers import get_provider
        from src.lead_scorer import LeadScorer
        from src.email_generator import EmailGenerator
        from src.drive_uploader import DriveUploader
        from src.data_normalizer import DataNormalizer
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_environment():
    """Test environment variables"""
    print("\nTesting environment variables...")
    
    required = {
        'APIFY_API_KEY': False,
        'OPENAI_API_KEY': False,
    }
    
    for var in required:
        if os.getenv(var):
            print(f"✅ {var} is set")
            required[var] = True
        else:
            print(f"❌ {var} is missing")
    
    # Check for Google Drive credentials
    if os.path.exists('service_account.json'):
        print("✅ service_account.json found (no popups)")
    elif os.path.exists('credentials.json'):
        print("⚠️  credentials.json found (will popup on first run)")
    else:
        print("❌ No Google Drive credentials found")
        required['DRIVE_CREDS'] = False
    
    return all(required.values())

def test_apify_connection():
    """Test Apify connection"""
    print("\nTesting Apify connection...")
    try:
        from src.providers import get_provider
        provider = get_provider('apify')
        # Just test initialization
        print("✅ Apify provider initialized")
        return True
    except Exception as e:
        print(f"❌ Apify connection failed: {e}")
        return False

def test_mini_pipeline():
    """Test a mini version of the pipeline"""
    print("\nTesting mini pipeline with sample data...")
    try:
        from src.data_normalizer import DataNormalizer
        from src.lead_scorer import LeadScorer
        from src.email_generator import EmailGenerator
        
        # Sample lead
        sample_lead = {
            'Name': 'Test Business',
            'Address': '123 Main St, Miami, FL',
            'Phone': '555-1234',
            'Website': 'NA',  # No website - should score high
            'SocialMediaLinks': 'NA',
            'Reviews': '3.2 stars (15 reviews)',
            'Images': '2',
            'Rating': 3.2,
            'ReviewCount': 15,
            'GoogleBusinessClaimed': False
        }
        
        # Test normalizer
        normalizer = DataNormalizer()
        normalized = normalizer.normalize([sample_lead])
        print("✅ Data normalizer working")
        
        # Test scorer
        scorer = LeadScorer()
        score, reasoning = scorer.score_lead(normalized[0])
        print(f"✅ Lead scorer working - Score: {score}/10")
        print(f"   Reasoning: {reasoning[:100]}...")
        
        normalized[0]['LeadScore'] = score
        normalized[0]['LeadScoreReasoning'] = reasoning
        
        # Test email generator
        email_gen = EmailGenerator()
        email = email_gen.generate_email(normalized[0])
        print(f"✅ Email generator working")
        print(f"   Email preview: {email[:100]}...")
        
        return True
    except Exception as e:
        print(f"❌ Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("=" * 50)
    print("R27 Infinite AI Leads Agent - System Test")
    print("=" * 50)
    
    results = []
    
    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Environment", test_environment()))
    
    if results[1][1]:  # Only test connections if environment is set
        results.append(("Apify Connection", test_apify_connection()))
        results.append(("Mini Pipeline", test_mini_pipeline()))
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    all_passed = all(r[1] for r in results)
    
    if all_passed:
        print("\n🎉 All tests passed! System is ready to use.")
        print("\nRun the system with:")
        print('  python main.py "dentists in Miami" --limit 5')
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())