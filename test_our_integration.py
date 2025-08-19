#!/usr/bin/env python3
"""
Test our actual InstantlyIntegration class
"""

import os
import sys
sys.path.append('.')

from dotenv import load_dotenv
from src.instantly_integration import InstantlyIntegration, InstantlyLead

load_dotenv()

def test_our_integration():
    api_key = os.getenv('INSTANTLY_API_KEY')
    
    if not api_key:
        print("ERROR: No INSTANTLY_API_KEY found")
        return
        
    print(f"Testing with API key: {api_key[:10]}...")
    
    # Initialize our integration
    instantly = InstantlyIntegration(api_key)
    
    print("\n" + "="*60)
    print("TEST 1: Getting campaigns using our integration")
    print("="*60)
    
    try:
        campaigns = instantly.get_campaigns()
        print(f"SUCCESS: Found {len(campaigns)} campaigns using our integration")
        
        if campaigns:
            campaign = campaigns[0]
            campaign_id = campaign.get('id')
            print(f"Campaign ID: {campaign_id}")
            print(f"Campaign name: {campaign.get('name')}")
            
            print("\n" + "="*60)
            print("TEST 2: Creating lead using our integration")
            print("="*60)
            
            # Create test lead
            test_leads = [
                InstantlyLead(
                    email="test-integration@example.com",
                    first_name="Integration",
                    last_name="Test",
                    company_name="Test Integration Co"
                )
            ]
            
            result = instantly.add_leads_to_campaign(campaign_id, test_leads)
            print(f"Add leads result: {result}")
            
        else:
            print("ERROR: No campaigns found")
            
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_our_integration()
