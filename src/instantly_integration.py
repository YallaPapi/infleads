"""
Instantly.ai Integration for Campaign Management
Handles email campaign creation, lead import, and sequence management
"""

import requests
import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class InstantlyLead:
    """Lead data structure for Instantly import"""
    email: str
    first_name: str = ""
    last_name: str = ""
    company_name: str = ""
    phone: str = ""
    website: str = ""
    location: str = ""
    industry: str = ""
    job_title: str = ""
    custom_variables: Dict[str, str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to Instantly API format"""
        data = {
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "company_name": self.company_name,
            "phone": self.phone,
            "website": self.website,
        }
        
        # Add custom variables for additional fields
        if self.custom_variables:
            data.update(self.custom_variables)
        
        # Add location and industry as custom variables
        if self.location:
            data["location"] = self.location
        if self.industry:
            data["industry"] = self.industry
        if self.job_title:
            data["job_title"] = self.job_title
            
        # Keep email field even if empty (required by API)
        result = {}
        for k, v in data.items():
            if k == 'email' or v:  # Always include email
                result[k] = v if v else ''
        return result


@dataclass
class CampaignTemplate:
    """Email campaign template"""
    name: str
    subject_lines: List[str]
    email_templates: List[str]
    follow_up_delays: List[int]  # Days between emails
    max_follow_ups: int = 3
    
    
class InstantlyIntegration:
    """Instantly.ai API integration for email campaigns"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.instantly.ai/api/v2"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
    def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Make API request to Instantly V2"""
        url = f"{self.base_url}/{endpoint}"
        
        # LOG EVERYTHING
        print(f"\n{'='*60}")
        print(f"INSTANTLY API CALL:")
        print(f"Method: {method}")
        print(f"URL: {url}")
        print(f"Headers: {self.headers}")
        if data:
            print(f"Data: {json.dumps(data, indent=2)[:1000]}")
        print(f"{'='*60}\n")
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers, params=data)
            elif method.upper() == "POST":
                response = requests.post(url, headers=self.headers, json=data)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=self.headers, json=data)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=self.headers, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            print(f"RESPONSE Status: {response.status_code}")
            print(f"RESPONSE Headers: {dict(response.headers)}")
            print(f"RESPONSE Body: {response.text[:500]}")
            
            response.raise_for_status()
            
            # Handle empty responses
            if not response.text.strip():
                return []
                
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"\n!!!!! INSTANTLY API ERROR !!!!!")
            print(f"Error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response Status: {e.response.status_code}")
                print(f"Response Body: {e.response.text}")
            print(f"!!!!! END ERROR !!!!!\n")
            raise
            
    def get_accounts(self) -> List[Dict]:
        """Get all email accounts"""
        return self._make_request("GET", "accounts")
        
    def get_campaigns(self) -> List[Dict]:
        """Get all campaigns"""
        result = self._make_request("GET", "campaigns")
        # V2 API returns campaigns directly as array or in 'data' field
        if isinstance(result, dict):
            if 'data' in result:
                return result['data']
            elif 'items' in result:
                return result['items']
            elif 'campaigns' in result:
                return result['campaigns']
            # If dict but no known field, return empty
            print(f"DEBUG: Unexpected campaigns response structure: {list(result.keys())}")
            return []
        return result if isinstance(result, list) else []
        
    def create_campaign(self, name: str, template: CampaignTemplate, 
                       account_emails: List[str]) -> Dict:
        """Create a new email campaign"""
        
        # Build email sequence
        sequence = []
        for i, (subject, body) in enumerate(zip(template.subject_lines, template.email_templates)):
            step = {
                "step_number": i + 1,
                "subject": subject,
                "body": body,
                "delay_days": template.follow_up_delays[i] if i < len(template.follow_up_delays) else 1
            }
            sequence.append(step)
            
        campaign_data = {
            "name": name,
            "sequence": sequence,
            "account_emails": account_emails,
            "campaign_schedule": {
                "schedules": [
                    {
                        "name": "Default Schedule",
                        "timing": {
                            "from": "09:00",
                            "to": "18:00"
                        },
                        "days": {
                            "1": True,  # Monday
                            "2": True,  # Tuesday
                            "3": True,  # Wednesday
                            "4": True,  # Thursday
                            "5": True   # Friday
                        },
                        "timezone": "UTC"
                    }
                ],
                "start_date": "",
                "end_date": ""
            },
            "daily_limit": 50,  # Emails per day per account
            "text_only": True,
            "stop_on_reply": True,
            "link_tracking": False,
            "open_tracking": False,
            "stop_on_auto_reply": False
        }
        
        return self._make_request("POST", "campaigns", campaign_data)
        
    def add_leads_to_campaign(self, campaign_id: str, leads: List[InstantlyLead]) -> Dict:
        """Add leads to campaign using Instantly v2 API"""
        
        # Convert leads to Instantly format
        instantly_leads = []
        for lead in leads:
            lead_data = lead.to_dict()
            
            # CRITICAL: Ensure email field exists (required by API)
            if 'email' not in lead_data or not lead_data.get('email'):
                print(f"WARNING: Skipping lead without email: {lead_data.get('first_name', 'Unknown')}")
                continue
                
            # Remove problematic fields
            lead_data.pop('draft_email', None)
            lead_data.pop('DraftEmail', None)
            lead_data.pop('campaign_id', None)  # Don't use campaign_id
            
            # Add the campaign using the correct field name
            lead_data['campaign'] = campaign_id
            
            instantly_leads.append(lead_data)
        
        if not instantly_leads:
            print("WARNING: No leads with valid emails to send to Instantly")
            return {"success": False, "message": "No valid email addresses found"}
        
        print(f"DEBUG: Sending {len(instantly_leads)} leads to campaign {campaign_id}")
        if instantly_leads:
            print(f"DEBUG: First lead data: {instantly_leads[0]}")
        
        # Send to Instantly with campaign assignment
        print(f"\n{'*'*60}")
        print(f"ADDING {len(instantly_leads)} LEADS TO INSTANTLY CAMPAIGN")
        print(f"Campaign ID: {campaign_id}")
        print(f"{'*'*60}\n")
        
        results = []
        failed = []
        
        for i, lead_data in enumerate(instantly_leads, 1):
            print(f"\n--- Lead {i}/{len(instantly_leads)} ---")
            print(f"Email: {lead_data.get('email')}")
            print(f"Name: {lead_data.get('first_name')} {lead_data.get('last_name')}")
            print(f"Campaign: {lead_data.get('campaign')}")
            
            try:
                # Send lead with campaign assignment
                result = self._make_request("POST", "leads", lead_data)
                
                if isinstance(result, dict) and 'id' in result:
                    results.append(result)
                    print(f"[SUCCESS] Lead added to campaign")
                    print(f"Lead ID: {result.get('id')}")
                    
                    # Check if campaign was assigned
                    if 'campaign' in result:
                        print(f"Campaign confirmed: {result.get('campaign')}")
                else:
                    print(f"[WARNING] Unexpected response format")
                    print(f"Response: {json.dumps(result, indent=2)[:200]}")
                    
            except Exception as e:
                print(f"[FAILED] Could not add lead")
                print(f"Error: {str(e)}")
                failed.append(lead_data.get('email'))
                continue
        
        print(f"\n{'='*60}")
        print(f"FINAL RESULTS:")
        print(f"Total leads processed: {len(instantly_leads)}")
        print(f"Successfully added: {len(results)}")
        print(f"Failed: {len(failed)}")
        if failed:
            print(f"Failed emails: {failed}")
        print(f"{'='*60}\n")
        
        if results:
            return {"success": True, "added": len(results), "failed": len(failed)}
        else:
            raise Exception(f"ALL {len(instantly_leads)} leads failed to add to Instantly!")
        
    def bulk_import_leads(self, leads: List[InstantlyLead], 
                         campaign_name: str = None) -> Dict:
        """Import leads in bulk, optionally to specific campaign"""
        
        # Convert leads to Instantly format
        instantly_leads = []
        for lead in leads:
            lead_data = lead.to_dict()
            if campaign_name:
                lead_data["campaign"] = campaign_name
            instantly_leads.append(lead_data)
            
        # Split into batches (Instantly has limits)
        batch_size = 1000
        results = []
        
        for i in range(0, len(instantly_leads), batch_size):
            batch = instantly_leads[i:i + batch_size]
            batch_data = {"leads": batch}
            
            result = self._make_request("POST", "leads", batch_data)
            results.append(result)
            
            # Rate limiting
            if len(instantly_leads) > batch_size:
                time.sleep(1)
                
        return {
            "total_leads": len(instantly_leads),
            "batches": len(results),
            "results": results
        }
        
    def get_campaign_stats(self, campaign_id: str) -> Dict:
        """Get campaign performance statistics"""
        return self._make_request("GET", f"campaign/{campaign_id}/stats")
        
    def pause_campaign(self, campaign_id: str) -> Dict:
        """Pause a campaign"""
        return self._make_request("PUT", f"campaign/{campaign_id}/pause")
        
    def resume_campaign(self, campaign_id: str) -> Dict:
        """Resume a paused campaign"""
        return self._make_request("PUT", f"campaign/{campaign_id}/resume")
        
    def delete_campaign(self, campaign_id: str) -> Dict:
        """Delete a campaign"""
        return self._make_request("DELETE", f"campaign/{campaign_id}")
        
    def get_lead_status(self, lead_email: str) -> Dict:
        """Get status of specific lead"""
        return self._make_request("GET", "lead/status", {"email": lead_email})
        
    def update_lead(self, lead_email: str, updates: Dict) -> Dict:
        """Update lead information"""
        data = {"email": lead_email, "updates": updates}
        return self._make_request("PUT", "lead/update", data)
        
    def remove_lead_from_campaign(self, campaign_id: str, lead_email: str) -> Dict:
        """Remove lead from campaign"""
        data = {"campaign_id": campaign_id, "email": lead_email}
        return self._make_request("DELETE", "lead/remove", data)
        

class CampaignTemplates:
    """Pre-built campaign templates for different industries"""
    
    @staticmethod
    def get_real_estate_template() -> CampaignTemplate:
        """Real estate outreach template"""
        return CampaignTemplate(
            name="Real Estate Outreach",
            subject_lines=[
                "Quick question about your property listings",
                "Following up on marketing opportunities",
                "Last chance - property marketing proposal"
            ],
            email_templates=[
                """Hi {{first_name}},

I noticed {{company_name}} has some great property listings in {{location}}. 

I help real estate professionals like you increase lead generation by 40% through targeted digital marketing campaigns.

Would you be interested in a quick 15-minute call to discuss how this could work for your business?

Best regards,
{{sender_name}}""",

                """Hi {{first_name}},

I sent a quick message last week about helping {{company_name}} with lead generation.

Many real estate professionals are missing out on qualified leads because their marketing isn't reaching the right audience.

Here's a case study of how we helped a similar agency: [link]

Still interested in that 15-minute call?

Best,
{{sender_name}}""",

                """Hi {{first_name}},

This is my final follow-up about the lead generation opportunity for {{company_name}}.

If you're not interested, no worries - just let me know and I'll stop reaching out.

But if you'd like to see how we can help you get more qualified leads, here's a direct link to book a call: [calendar_link]

Best regards,
{{sender_name}}"""
            ],
            follow_up_delays=[3, 5, 7],
            max_follow_ups=3
        )
        
    @staticmethod
    def get_lawyer_template() -> CampaignTemplate:
        """Legal services outreach template"""
        return CampaignTemplate(
            name="Legal Services Outreach",
            subject_lines=[
                "Client acquisition strategy for {{company_name}}",
                "Quick follow-up on client growth",
                "Final follow-up - client acquisition"
            ],
            email_templates=[
                """Hi {{first_name}},

I help law firms in {{location}} increase their client acquisition by 50% through targeted digital marketing.

{{company_name}} caught my attention because of your expertise in {{industry}}.

Would you be open to a brief call to discuss how this could work for your practice?

Best regards,
{{sender_name}}""",

                """Hi {{first_name}},

Following up on my message about client acquisition for {{company_name}}.

Here's what we typically see with law firms:
- 3x increase in qualified leads within 90 days
- 50% reduction in client acquisition costs
- Better targeting of ideal client demographics

Interested in learning more?

Best,
{{sender_name}}""",

                """Hi {{first_name}},

This is my last follow-up about the client acquisition opportunity.

If you're not the right person for this, could you point me to whoever handles marketing for {{company_name}}?

Otherwise, here's a link to schedule a quick call: [calendar_link]

Best regards,
{{sender_name}}"""
            ],
            follow_up_delays=[4, 6, 8],
            max_follow_ups=3
        )
        
    @staticmethod
    def get_restaurant_template() -> CampaignTemplate:
        """Restaurant/hospitality outreach template"""
        return CampaignTemplate(
            name="Restaurant Outreach",
            subject_lines=[
                "Increase {{company_name}}'s online orders by 40%",
                "Quick follow-up on online ordering",
                "Last chance - restaurant marketing opportunity"
            ],
            email_templates=[
                """Hi {{first_name}},

{{company_name}} looks like an amazing restaurant in {{location}}!

I help restaurants increase their online orders by 40% through targeted social media marketing and delivery app optimization.

Would you be interested in a quick chat about how this could work for your restaurant?

Best,
{{sender_name}}""",

                """Hi {{first_name}},

Following up on my message about increasing online orders for {{company_name}}.

Most restaurants are leaving money on the table because they're not optimizing their:
- Google My Business listings
- Social media presence  
- Delivery app profiles

Quick 15-minute call to show you what I mean?

Best,
{{sender_name}}""",

                """Hi {{first_name}},

Final follow-up about the online ordering opportunity for {{company_name}}.

If this isn't a priority right now, no problem - just let me know.

But if you'd like to see how we can help increase your online orders, here's my calendar: [calendar_link]

Best regards,
{{sender_name}}"""
            ],
            follow_up_delays=[2, 4, 6],
            max_follow_ups=3
        )

    @staticmethod
    def get_generic_b2b_template() -> CampaignTemplate:
        """Generic B2B outreach template"""
        return CampaignTemplate(
            name="Generic B2B Outreach",
            subject_lines=[
                "Quick question about {{company_name}}",
                "Following up on growth opportunity",
                "Final follow-up - business opportunity"
            ],
            email_templates=[
                """Hi {{first_name}},

I noticed {{company_name}} and was impressed by your work in {{industry}}.

I help businesses like yours {{value_proposition}}.

Would you be open to a brief conversation about how this might work for {{company_name}}?

Best regards,
{{sender_name}}""",

                """Hi {{first_name}},

I reached out last week about {{value_proposition}} for {{company_name}}.

Here's a quick case study of similar results we achieved: {{case_study_link}}

Still interested in exploring this opportunity?

Best,
{{sender_name}}""",

                """Hi {{first_name}},

This is my final follow-up about the opportunity for {{company_name}}.

If you're not interested, just let me know and I'll stop reaching out.

Otherwise, here's a direct link to schedule a call: {{calendar_link}}

Best regards,
{{sender_name}}"""
            ],
            follow_up_delays=[3, 5, 7],
            max_follow_ups=3
        )


def map_to_industry(search_term):
    """Map search keywords and business types to actual industries"""
    if not search_term:
        return 'Other'
        
    search_lower = search_term.lower()
    
    # Food & Beverage Industry
    if any(word in search_lower for word in ['restaurant', 'food', 'dining', 'cafe', 'coffee', 'bar', 'pub', 'bakery', 'pizza', 'mexican', 'italian', 'chinese', 'thai', 'indian', 'sushi', 'burger', 'fast food', 'catering']):
        return 'Food and Beverage'
    
    # Healthcare Industry
    elif any(word in search_lower for word in ['doctor', 'dentist', 'medical', 'clinic', 'hospital', 'pharmacy', 'health', 'dental', 'physician', 'therapy', 'chiropractor', 'veterinarian', 'optometrist']):
        return 'Healthcare'
    
    # Legal Services Industry
    elif any(word in search_lower for word in ['lawyer', 'attorney', 'legal', 'law firm', 'court', 'litigation', 'paralegal']):
        return 'Legal Services'
    
    # Real Estate Industry
    elif any(word in search_lower for word in ['real estate', 'realtor', 'property', 'mortgage', 'broker', 'homes', 'apartments', 'commercial property']):
        return 'Real Estate'
    
    # Automotive Industry
    elif any(word in search_lower for word in ['auto', 'car', 'mechanic', 'dealership', 'garage', 'automotive', 'repair', 'oil change', 'tire']):
        return 'Automotive'
    
    # Beauty & Wellness Industry
    elif any(word in search_lower for word in ['salon', 'spa', 'beauty', 'hair', 'nail', 'massage', 'cosmetic', 'barber', 'wellness', 'fitness', 'gym']):
        return 'Beauty and Wellness'
    
    # Retail Industry
    elif any(word in search_lower for word in ['store', 'shop', 'retail', 'boutique', 'clothing', 'electronics', 'furniture', 'pharmacy', 'grocery', 'supermarket']):
        return 'Retail'
    
    # Professional Services Industry
    elif any(word in search_lower for word in ['accounting', 'consultant', 'marketing', 'advertising', 'insurance', 'financial', 'tax', 'bookkeeping', 'architect', 'engineer']):
        return 'Professional Services'
    
    # Hospitality Industry
    elif any(word in search_lower for word in ['hotel', 'motel', 'lodging', 'accommodation', 'resort', 'bed and breakfast', 'airbnb']):
        return 'Hospitality'
    
    # Construction Industry
    elif any(word in search_lower for word in ['construction', 'contractor', 'builder', 'plumber', 'electrician', 'roofing', 'flooring', 'hvac', 'landscaping']):
        return 'Construction'
    
    # Education Industry
    elif any(word in search_lower for word in ['school', 'education', 'tutor', 'training', 'academy', 'university', 'college', 'learning']):
        return 'Education'
    
    # Entertainment Industry
    elif any(word in search_lower for word in ['entertainment', 'music', 'theater', 'event', 'wedding', 'party', 'photography', 'videography']):
        return 'Entertainment'
    
    # Default fallback
    else:
        return 'Other'


def convert_r27_leads_to_instantly(leads_data: List[Dict]) -> List[InstantlyLead]:
    """Convert R27 lead format to Instantly lead format"""
    instantly_leads = []
    
    for lead in leads_data:
        # Extract name parts
        name = lead.get('Name', '').strip()
        name_parts = name.split(' ', 1) if name else ['', '']
        first_name = name_parts[0] if len(name_parts) > 0 else ''
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        # Create custom variables for ALL additional data from CSV
        custom_vars = {}
        
        # Map selected fields from the lead data as custom variables
        # REMOVED DraftEmail to avoid encoding issues
        field_mapping = {
            'SocialMediaLinks': 'social_media_links', 
            'Reviews': 'reviews',
            'Images': 'images',
            'Rating': 'rating',
            'ReviewCount': 'review_count',
            'GoogleBusinessClaimed': 'google_business_claimed',
            'email_source': 'email_source',
            'email_quality_boost': 'email_quality_boost',
            # 'DraftEmail': 'draft_email',  # REMOVED - causes encoding issues
            'SearchKeyword': 'search_term',  # Keep original search term
            'Location': 'search_location',
            'LeadScore': 'lead_score'
        }
        
        # Add business name as custom variable
        if lead.get('Name'):
            custom_vars['business_name'] = str(lead['Name'])
        
        # Add industry as custom variable (mapped to actual industries)
        industry = None
        if lead.get('SearchKeyword'):
            industry = map_to_industry(lead['SearchKeyword'])
        elif lead.get('types'):
            industry = map_to_industry(lead['types'])
        
        if industry:
            custom_vars['industry'] = industry
        
        # Parse address to extract city only
        if lead.get('Address') and lead.get('Address') != 'NA':
            address = str(lead['Address'])
            # Remove quotes if present
            address = address.strip('"')
            # Extract city from address format: "Street, City, State Zip, Country"
            try:
                parts = address.split(', ')
                if len(parts) >= 2:
                    city = parts[1].strip()  # Get the city part
                    custom_vars['city'] = city
            except:
                # If parsing fails, skip the address
                pass
        
        # Add other available fields as custom variables
        for original_field, custom_field in field_mapping.items():
            if lead.get(original_field) is not None and lead.get(original_field) != 'NA':
                # Convert to string and handle different data types
                value = lead[original_field]
                if isinstance(value, bool):
                    custom_vars[custom_field] = str(value).lower()
                elif isinstance(value, (int, float)):
                    custom_vars[custom_field] = str(value)
                else:
                    custom_vars[custom_field] = str(value)
            
        instantly_lead = InstantlyLead(
            email=lead.get('Email', ''),
            first_name=first_name,
            last_name=last_name,
            company_name=lead.get('Name', ''),  # Business name
            phone=lead.get('Phone', ''),
            website=lead.get('Website', ''),
            location=lead.get('Location', ''),
            industry=industry or 'Other',  # Use mapped industry
            custom_variables=custom_vars
        )
        
        instantly_leads.append(instantly_lead)
        
    return instantly_leads


# Example usage functions
def create_campaign_from_r27_leads(instantly_api: InstantlyIntegration, 
                                   leads_data: List[Dict], 
                                   campaign_name: str,
                                   template_type: str = "generic") -> Dict:
    """Create complete campaign from R27 leads"""
    
    # Convert leads
    instantly_leads = convert_r27_leads_to_instantly(leads_data)
    
    # Get template
    templates = {
        "real_estate": CampaignTemplates.get_real_estate_template(),
        "lawyer": CampaignTemplates.get_lawyer_template(), 
        "restaurant": CampaignTemplates.get_restaurant_template(),
        "generic": CampaignTemplates.get_generic_b2b_template()
    }
    
    template = templates.get(template_type, templates["generic"])
    
    # Get available email accounts
    accounts = instantly_api.get_accounts()
    
    # Handle different account structures (V2 API format)
    account_emails = []
    if isinstance(accounts, dict) and 'items' in accounts:
        # V2 API returns accounts in 'items' array with 'status' field
        items = accounts['items']
        account_emails = [acc.get('email') for acc in items if acc.get('email') and acc.get('status') == 1]
    elif isinstance(accounts, list) and accounts:
        if isinstance(accounts[0], dict):
            account_emails = [acc.get('email') for acc in accounts if acc.get('email') and acc.get('is_active', True)]
    
    if not account_emails:
        raise ValueError("No active email accounts found in Instantly")
    
    # Create campaign
    campaign = instantly_api.create_campaign(
        name=campaign_name,
        template=template,
        account_emails=account_emails[:1]  # Use first account
    )
    
    # Add leads to campaign
    if instantly_leads:
        lead_result = instantly_api.add_leads_to_campaign(
            campaign['campaign_id'], 
            instantly_leads
        )
        
        return {
            "campaign": campaign,
            "leads_added": lead_result,
            "total_leads": len(instantly_leads)
        }
    
    return {"campaign": campaign, "leads_added": None, "total_leads": 0}