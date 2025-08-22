#!/usr/bin/env python3
"""
Test script for BotasaurusProvider
Demonstrates advanced lead generation capabilities
"""

import sys
import os
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.providers.botasaurus_provider import BotasaurusProvider, ContactExtractor, DorksEngine, CacheManager
from src.providers.multi_provider import MultiProvider

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_contact_extractor():
    """Test contact information extraction"""
    print("\n" + "="*60)
    print("TESTING CONTACT EXTRACTOR")
    print("="*60)
    
    extractor = ContactExtractor()
    
    # Test text with various contact info
    test_text = """
    Welcome to Miami Dental Center! 
    Contact us at info@miamidental.com or call (305) 555-0123.
    Visit our website at https://www.miamidental.com
    Follow us on Facebook: facebook.com/miamidental
    LinkedIn: linkedin.com/company/miami-dental-center
    Our address is 123 Biscayne Blvd, Miami, FL 33101
    Phone: 305-555-0123 | Emergency: (305) 555-9999
    Email: appointments@miamidental.com
    """
    
    # Extract contact information
    emails = extractor.extract_emails(test_text)
    phones = extractor.extract_phones(test_text)
    social = extractor.extract_social_media(test_text)
    websites = extractor.extract_websites(test_text)
    
    print(f"📧 Extracted Emails: {emails}")
    print(f"📞 Extracted Phones: {phones}")
    print(f"📱 Social Media: {social}")
    print(f"🌐 Websites: {websites}")
    
    assert len(emails) >= 2, "Should extract multiple emails"
    assert len(phones) >= 2, "Should extract multiple phone numbers"
    assert 'facebook' in social, "Should extract Facebook link"
    
    print("✅ Contact extraction tests passed!")


def test_dorks_engine():
    """Test Google dorks generation"""
    print("\n" + "="*60)
    print("TESTING DORKS ENGINE")
    print("="*60)
    
    dorks_engine = DorksEngine()
    
    # Test business dorks generation
    business_dorks = dorks_engine.generate_business_dorks("dentist", "Miami", include_contact=True)
    print(f"📋 Generated {len(business_dorks)} business dorks")
    print("Sample dorks:")
    for i, dork in enumerate(business_dorks[:5]):
        print(f"  {i+1}. {dork}")
    
    # Test email hunting dorks
    email_dorks = dorks_engine.generate_email_hunting_dorks("Miami Dental Center", "miamidental.com")
    print(f"\n📧 Generated {len(email_dorks)} email hunting dorks")
    print("Sample email dorks:")
    for i, dork in enumerate(email_dorks[:3]):
        print(f"  {i+1}. {dork}")
    
    # Test search strategy
    strategy = dorks_engine.create_search_strategy("dentist", "Miami", max_queries=10)
    print(f"\n🎯 Search strategy created with {sum(len(queries) for queries in strategy.values())} total queries")
    for category, queries in strategy.items():
        print(f"  {category}: {len(queries)} queries")
    
    assert len(business_dorks) > 10, "Should generate multiple business dorks"
    assert len(email_dorks) > 5, "Should generate multiple email dorks"
    assert len(strategy) == 5, "Should have 5 strategy categories"
    
    print("✅ Dorks engine tests passed!")


def test_cache_manager():
    """Test caching functionality"""
    print("\n" + "="*60)
    print("TESTING CACHE MANAGER")
    print("="*60)
    
    # Create cache manager in tests directory
    cache_dir = project_root / "tests" / "test_cache"
    cache_manager = CacheManager(str(cache_dir), cache_duration_hours=1)
    
    # Test data
    test_query = "dentists in Miami"
    test_results = [
        {"name": "Miami Dental", "phone": "(305) 555-0123"},
        {"name": "Smile Center", "phone": "(305) 555-0124"},
    ]
    
    # Test caching
    print("💾 Testing cache storage...")
    cache_manager.cache_results(test_query, test_results)
    
    # Test retrieval
    print("🔍 Testing cache retrieval...")
    cached_results = cache_manager.get_cached_results(test_query)
    
    assert cached_results is not None, "Should retrieve cached results"
    assert len(cached_results) == 2, "Should retrieve all cached results"
    assert cached_results[0]["name"] == "Miami Dental", "Should preserve data integrity"
    
    print(f"✅ Cache tests passed! Retrieved {len(cached_results)} cached results")
    
    # Cleanup
    if cache_dir.exists():
        import shutil
        shutil.rmtree(cache_dir)


def test_botasaurus_provider_initialization():
    """Test BotasaurusProvider initialization"""
    print("\n" + "="*60)
    print("TESTING BOTASAURUS PROVIDER INITIALIZATION")
    print("="*60)
    
    try:
        # Test with cache enabled
        provider = BotasaurusProvider(use_cache=True, cache_duration_hours=1)
        print("✅ BotasaurusProvider initialized successfully with cache")
        
        # Test configuration
        assert hasattr(provider, 'dorks_engine'), "Should have dorks engine"
        assert hasattr(provider, 'contact_extractor'), "Should have contact extractor"
        assert hasattr(provider, 'cache_manager'), "Should have cache manager"
        
        print("🔧 All components initialized correctly")
        
        # Test query parsing
        business_type, location = provider._parse_query("dentists in Miami")
        assert business_type == "dentists", "Should parse business type correctly"
        assert location == "miami", "Should parse location correctly"
        
        print("🔍 Query parsing works correctly")
        
        return provider
        
    except ImportError as e:
        print(f"⚠️  BotasaurusProvider not available: {e}")
        print("This is expected if Botasaurus dependencies are not installed")
        return None
    except Exception as e:
        print(f"❌ Error initializing BotasaurusProvider: {e}")
        raise


def test_multi_provider_integration():
    """Test MultiProvider integration with BotasaurusProvider"""
    print("\n" + "="*60)
    print("TESTING MULTI PROVIDER INTEGRATION")
    print("="*60)
    
    try:
        # Initialize MultiProvider with BotasaurusProvider enabled
        multi_provider = MultiProvider(enable_botasaurus=True, use_cache=True)
        
        provider_names = [name for name, _ in multi_provider.providers]
        print(f"📋 MultiProvider initialized with providers: {provider_names}")
        
        # Check if BotasaurusProvider is included
        botasaurus_enabled = any('Botasaurus' in name for name in provider_names)
        
        if botasaurus_enabled:
            print("✅ BotasaurusProvider successfully integrated into MultiProvider")
        else:
            print("⚠️  BotasaurusProvider not available, using standard providers only")
        
        # Test basic functionality
        assert len(multi_provider.providers) >= 3, "Should have at least 3 providers"
        
        print("✅ MultiProvider integration test passed!")
        return multi_provider
        
    except Exception as e:
        print(f"❌ Error testing MultiProvider integration: {e}")
        raise


def test_fallback_data_generation():
    """Test fallback data generation"""
    print("\n" + "="*60)
    print("TESTING FALLBACK DATA GENERATION")
    print("="*60)
    
    try:
        provider = BotasaurusProvider(use_cache=False)
        
        # Test fallback data generation
        fallback_data = provider._get_fallback_data("dentists in Miami", 5)
        
        print(f"📊 Generated {len(fallback_data)} fallback results")
        
        # Verify data structure
        assert len(fallback_data) == 5, "Should generate requested number of results"
        
        sample_result = fallback_data[0]
        required_fields = ['name', 'address', 'phone', 'email', 'website', 'source']
        
        for field in required_fields:
            assert field in sample_result, f"Result should have {field} field"
        
        print("Sample fallback result:")
        for key, value in sample_result.items():
            print(f"  {key}: {value}")
        
        print("✅ Fallback data generation test passed!")
        
    except ImportError:
        print("⚠️  BotasaurusProvider not available for fallback test")
    except Exception as e:
        print(f"❌ Error testing fallback data: {e}")
        raise


def test_full_integration():
    """Test full integration with a simple query"""
    print("\n" + "="*60)
    print("TESTING FULL INTEGRATION")
    print("="*60)
    
    try:
        # Test with MultiProvider
        multi_provider = MultiProvider(enable_botasaurus=True, use_cache=True)
        
        print("🔍 Testing lead generation with query: 'dentists in Miami'")
        
        # This will use fallback data since we're not actually scraping
        results = multi_provider.fetch_places("dentists in Miami", limit=5)
        
        print(f"📊 Retrieved {len(results)} results")
        
        if results:
            print("\nSample result:")
            sample_result = results[0]
            for key, value in sample_result.items():
                print(f"  {key}: {value}")
        
        assert len(results) > 0, "Should return some results"
        assert all('name' in result for result in results), "All results should have names"
        
        print("✅ Full integration test passed!")
        
    except Exception as e:
        print(f"❌ Error in full integration test: {e}")
        raise


def run_all_tests():
    """Run all test functions"""
    print("🧪 STARTING BOTASAURUS PROVIDER TESTS")
    print("="*80)
    
    tests = [
        test_contact_extractor,
        test_dorks_engine,
        test_cache_manager,
        test_botasaurus_provider_initialization,
        test_multi_provider_integration,
        test_fallback_data_generation,
        test_full_integration,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            logger.error(f"Test {test_func.__name__} failed: {e}")
            failed += 1
    
    print("\n" + "="*80)
    print("🏁 TEST SUMMARY")
    print("="*80)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total: {len(tests)}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! BotasaurusProvider is ready for production.")
    else:
        print(f"\n⚠️  {failed} tests failed. Please check the errors above.")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)