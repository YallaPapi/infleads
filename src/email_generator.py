"""
AI-powered email generation for outreach
"""

import os
import logging
from typing import Dict, Any
from openai import OpenAI
from .industry_configs import IndustryConfig

logger = logging.getLogger(__name__)


class EmailGenerator:
    """Generate personalized outreach emails using AI"""
    
    def __init__(self, industry: str = 'default'):
        """Initialize OpenAI client"""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-3.5-turbo"  # Fast model
        self.industry = industry
        self.config = IndustryConfig.get_config(industry)
        logger.info(f"Email generator initialized with model: {self.model}, industry: {industry}")
    
    def generate_email(self, lead: Dict[str, Any]) -> str:
        """
        Generate a personalized outreach email for a lead
        
        Args:
            lead: Lead dictionary with business information and score
            
        Returns:
            Personalized email text
        """
        prompt = self._create_email_prompt(lead)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=400
            )
            
            email = response.choices[0].message.content.strip()
            return email
            
        except Exception as e:
            logger.error(f"Error generating email for {lead.get('Name', 'Unknown')}: {e}")
            raise
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for email generation"""
        value_props = '\n- '.join(self.config['value_propositions'])
        
        return f"""You are a friendly {self.config['name']} specialist writing hyper-personalized outreach emails to local businesses. 

CRITICAL RULES:
1. Write like you're texting a friend - super casual, no corporate speak
2. Maximum 100 words (shorter = better)
3. Pick ONE specific pain point they likely have
4. Lead with value, not who you are
5. Use pattern interrupts (questions, observations, compliments)
6. Include social proof naturally (not forced)
7. End with a soft CTA (question, not demand)
8. Use their business name naturally 1-2 times max
9. Reference something specific about their location/market
10. Write at 5th grade reading level

BANNED PHRASES:
- "I hope this email finds you well"
- "I'm reaching out because"
- "I noticed that"
- "I wanted to introduce"
- "My name is"
- Any formal greetings/closings

TONE: Like you already know them. Skip introductions.
- Including a soft call-to-action

Value propositions to consider:
- {value_props}

DO NOT:
- Use corporate jargon or buzzwords
- Write generic templates
- Be pushy or aggressive
- Make unrealistic promises
- Use excessive exclamation points

Focus on {self.config['email_focus']} and building rapport, not making a hard sell."""
    
    def _create_email_prompt(self, lead: Dict[str, Any]) -> str:
        """Create the email generation prompt for a specific lead"""
        return f"""Write a personalized outreach email for this business:

Business: {lead.get('Name', 'Unknown')}
Their weaknesses: {lead.get('LeadScoreReasoning', 'General digital presence improvements needed')}
Lead Score: {lead.get('LeadScore', 5)}/10

Write a casual, helpful email that:
1. Mentions their business by name
2. Points out ONE specific issue they have (based on weaknesses)
3. Offers a simple, actionable tip they can implement
4. Softly mentions you can help further if they're interested

Keep it under 150 words and conversational."""