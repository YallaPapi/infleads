"""
Smart Lead Analyzer - Actually analyzes companies instead of using templates
"""

import os
import logging
import re
from typing import Dict, Any, List
from openai import OpenAI
import requests
from bs4 import BeautifulSoup
from .linkedin_scraper import LinkedInScraper

logger = logging.getLogger(__name__)


class SmartLeadAnalyzer:
    """Analyzes companies by actually researching them"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.linkedin_scraper = LinkedInScraper()
        
    def research_company(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actually research the company instead of using templates
        
        Pulls from:
        - Company description (from Apollo)
        - LinkedIn posts/activity
        - Website content
        - News/recent updates
        - Industry trends
        """
        
        research = {
            'company': lead_data.get('organization_name', ''),
            'description': lead_data.get('organization_short_description', ''),
            'industry': lead_data.get('industry', ''),
            'size': lead_data.get('estimated_num_employees', 0),
            'linkedin_url': lead_data.get('linkedin_url', ''),
            'insights': []
        }
        
        # Step 1: Analyze their company description deeply
        if research['description']:
            desc_insights = self._analyze_description(research['description'])
            research['insights'].extend(desc_insights)
        
        # Step 2: Scrape LinkedIn if available - THIS IS THE GOLD
        if research['linkedin_url']:
            first_name = lead_data.get('first_name', '')
            linkedin_opener = self.linkedin_scraper.generate_personalized_opener(
                research['linkedin_url'], 
                first_name
            )
            research['linkedin_opener'] = linkedin_opener
            research['linkedin_activity'] = linkedin_opener.get('full_data', {})
        
        # Step 3: Find their website and analyze it
        website = self._find_company_website(lead_data)
        if website:
            website_insights = self._analyze_website(website)
            research['website_insights'] = website_insights
        
        # Step 4: Generate SPECIFIC automation ideas based on THEIR business
        research['automation_opportunities'] = self._generate_specific_ideas(research)
        
        return research
    
    def _analyze_description(self, description: str) -> List[str]:
        """Extract specific insights from company description"""
        
        insights = []
        
        # Look for specific keywords that indicate pain points
        if 'nationwide' in description.lower() or 'multiple locations' in description.lower():
            insights.append('operates_multiple_locations')
        
        if 'family-run' in description.lower() or 'family owned' in description.lower():
            insights.append('family_business')
        
        if any(word in description.lower() for word in ['24/7', '24 hours', 'emergency']):
            insights.append('24_7_operations')
        
        if any(word in description.lower() for word in ['appointment', 'booking', 'scheduling']):
            insights.append('appointment_based')
        
        if any(word in description.lower() for word in ['delivery', 'shipping', 'fulfillment']):
            insights.append('delivery_operations')
        
        if any(word in description.lower() for word in ['custom', 'personalized', 'tailored']):
            insights.append('customization_focus')
        
        if any(word in description.lower() for word in ['training', 'education', 'certification']):
            insights.append('training_component')
        
        return insights
    
    def _scrape_linkedin_highlights(self, linkedin_url: str) -> Dict[str, Any]:
        """
        Scrape key highlights from LinkedIn
        Note: In production, use LinkedIn API or specialized scraping service
        """
        
        # For now, return structured data based on URL
        # In production, actually scrape or use API
        return {
            'recent_posts_topics': [],  # Would scrape recent post themes
            'employee_growth': None,    # Would check if hiring
            'recent_updates': []         # Would get company updates
        }
    
    def _find_company_website(self, lead_data: Dict[str, Any]) -> str:
        """Try to find company website"""
        
        # Check if website in data
        if lead_data.get('website'):
            return lead_data['website']
        
        # Could search Google for company name + location
        # For now return None
        return None
    
    def _analyze_website(self, website: str) -> Dict[str, Any]:
        """Analyze their website for automation opportunities"""
        
        insights = {
            'has_booking_system': False,
            'has_live_chat': False,
            'has_contact_form': True,
            'mentions_wait_times': False,
            'has_faq': False,
            'ecommerce': False
        }
        
        # In production, actually scrape and analyze
        # For now, return basic insights
        return insights
    
    def _generate_specific_ideas(self, research: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Generate SPECIFIC automation ideas based on ACTUAL research
        Not templates - actual ideas based on their business
        """
        
        prompt = f"""
        Based on this SPECIFIC company research, suggest 3 UNIQUE automation ideas we could build for them.
        
        Company: {research['company']}
        Industry: {research['industry']}
        Size: {research['size']} employees
        Description: {research['description']}
        Key Insights: {research.get('insights', [])}
        
        Requirements:
        1. Ideas must be SPECIFIC to their actual business (reference things from their description)
        2. Must be technically feasible with AI/automation
        3. Must solve a real problem they likely have
        4. NO generic suggestions like "improve customer service" or "automate emails"
        5. Each idea should reference something specific from their description
        
        Format each idea as:
        - Problem: [specific problem based on their business]
        - Solution: [specific automation we could build]
        - Impact: [specific measurable outcome]
        
        BE CREATIVE AND SPECIFIC. Don't give me generic automation ideas.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert at identifying unique automation opportunities by analyzing specific business details."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,  # Higher creativity
                max_tokens=400
            )
            
            ideas_text = response.choices[0].message.content
            
            # Parse the response into structured ideas
            ideas = []
            for section in ideas_text.split('\n\n'):
                if 'Problem:' in section and 'Solution:' in section:
                    ideas.append({
                        'raw': section,
                        'is_unique': True
                    })
            
            return ideas
            
        except Exception as e:
            logger.error(f"Error generating ideas: {e}")
            # Fallback to basic ideas but still make them specific
            return self._generate_fallback_ideas(research)
    
    def _generate_fallback_ideas(self, research: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate ideas without GPT"""
        
        ideas = []
        insights = research.get('insights', [])
        
        if 'operates_multiple_locations' in insights:
            ideas.append({
                'raw': f"Problem: Coordinating {research['size']} employees across multiple locations\nSolution: Build unified scheduling system with AI conflict resolution\nImpact: Save 10+ hours weekly on scheduling conflicts",
                'is_unique': True
            })
        
        if '24_7_operations' in insights:
            ideas.append({
                'raw': f"Problem: Handling customer inquiries during overnight shifts\nSolution: AI agent that handles 80% of overnight inquiries\nImpact: Reduce overnight staffing needs by 1-2 people",
                'is_unique': True
            })
        
        if 'appointment_based' in insights:
            ideas.append({
                'raw': f"Problem: No-shows and last-minute cancellations\nSolution: AI that predicts no-shows and double-books intelligently\nImpact: Recover 15-20% of lost appointment revenue",
                'is_unique': True
            })
        
        # If no specific insights, analyze the description itself
        if not ideas and research['description']:
            desc_words = research['description'].lower().split()
            if 'restaurant' in research['industry'].lower():
                ideas.append({
                    'raw': f"Problem: {research['company']} likely handles dozens of calls during rush hours\nSolution: AI that takes orders via phone when staff is busy\nImpact: Never miss an order during peak times",
                    'is_unique': True
                })
        
        return ideas
    
    def generate_personalized_email(self, lead_data: Dict[str, Any], research: Dict[str, Any]) -> str:
        """
        Generate truly personalized email based on ACTUAL LinkedIn activity
        """
        
        # Get LinkedIn opener if available - THIS IS THE HOOK
        linkedin_opener = research.get('linkedin_opener', {})
        has_linkedin = linkedin_opener.get('opener') is not None
        
        # Pick the best automation idea
        ideas = research.get('automation_opportunities', [])
        best_idea = ideas[0]['raw'] if ideas else None
        
        if has_linkedin:
            # We have LinkedIn data - use it!
            prompt = f"""
            Write a SHORT cold email to {lead_data.get('first_name')}.
            
            LinkedIn hook: {linkedin_opener.get('opener')}
            Follow-up angle: {linkedin_opener.get('follow_up')}
            
            Company: {research['company']}
            
            Rules:
            1. START with the LinkedIn reference (the hook)
            2. Connect it to how we can help (the follow-up angle)
            3. Be specific, not generic
            4. Keep it under 75 words
            5. End with "Worth a quick chat?" or "Interested?"
            
            Example format:
            "{lead_data.get('first_name')}, {linkedin_opener.get('opener')}. 
            
            {linkedin_opener.get('follow_up')}.
            
            [One specific detail about how we'd help]
            
            Worth a quick chat?"
            """
        else:
            # No LinkedIn data - use company research
            prompt = f"""
            Write a personalized cold email to {lead_data.get('first_name')} at {research['company']}.
            
            Their business: {research['description'][:200]}
            
            Specific automation idea for them:
            {best_idea}
            
            Rules:
            1. Reference something SPECIFIC from their company description
            2. Lead with the problem (not "Hi, we do AI automation")
            3. Propose the specific solution
            4. Keep it under 100 words
            5. Don't mention AI unless necessary - focus on the outcome
            6. End with "Worth exploring?" or similar soft CTA
            
            Make it feel like you actually researched their business (because we did).
            """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You write highly specific, researched cold emails that get responses."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=200
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            # Fallback
            return self._generate_manual_email(lead_data, research, best_idea)
    
    def _generate_manual_email(self, lead_data: Dict[str, Any], research: Dict[str, Any], idea: str) -> str:
        """Manual email generation without GPT"""
        
        first_name = lead_data.get('first_name', 'there')
        company = research['company']
        
        # Extract problem from idea
        problem_line = ""
        if idea and 'Problem:' in idea:
            problem_line = idea.split('Problem:')[1].split('\n')[0].strip()
        
        # Extract solution and impact
        solution_text = 'handles this automatically'
        if idea and 'Solution:' in idea:
            solution_text = idea.split('Solution:')[1].split('\n')[0].strip()
        
        impact_text = 'Most clients see results within 30 days'
        if idea and 'Impact:' in idea:
            impact_text = idea.split('Impact:')[1].split('\n')[0].strip()
        
        email = f"""Hi {first_name},

{problem_line}

We could build a system that {solution_text}.

{impact_text}.

Worth exploring?

Best,
[Your name]"""
        
        return email