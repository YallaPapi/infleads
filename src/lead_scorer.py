"""
AI-powered lead scoring using OpenAI
"""

import os
import logging
import json
from typing import Tuple, Dict, Any
from openai import OpenAI
from .industry_configs import IndustryConfig

logger = logging.getLogger(__name__)


class LeadScorer:
    """Score leads using AI based on R27 rules"""
    
    def __init__(self, industry: str = 'default'):
        """Initialize OpenAI client"""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-3.5-turbo"  # Fast model
        self.industry = industry
        self.config = IndustryConfig.get_config(industry)
        logger.info(f"Lead scorer initialized with model: {self.model}, industry: {industry}")
    
    def score_lead(self, lead: Dict[str, Any]) -> Tuple[int, str]:
        """
        Score a lead based on R27 rules
        
        Args:
            lead: Lead dictionary with business information
            
        Returns:
            Tuple of (score 0-10, reasoning)
        """
        prompt = self._create_scoring_prompt(lead)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=300
            )
            
            # Parse the response
            content = response.choices[0].message.content
            return self._parse_score_response(content)
            
        except Exception as e:
            logger.error(f"Error scoring lead {lead.get('Name', 'Unknown')}: {e}")
            raise
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for lead scoring"""
        # Build scoring rules text from config
        rules = []
        for rule_key, rule_data in self.config['scoring_rules'].items():
            rules.append(f"- +{rule_data['points']} points: {rule_data['description']}")
        rules_text = '\n'.join(rules)
        
        return f"""You are a lead scoring expert for a {self.config['name']} specialist agency. Score business leads from 0-10 based on their potential need for services.

INDUSTRY-SPECIFIC SCORING RULES:
{rules_text}

Score 8-10: Excellent lead - multiple weaknesses, high potential
Score 5-7: Good lead - some clear opportunities
Score 2-4: Fair lead - limited opportunities  
Score 0-1: Poor lead - already well-optimized

Focus on {self.config['email_focus']}.

RESPONSE FORMAT:
Score: [0-10]
Reasoning: [1-3 sentences explaining the score based on identified weaknesses]"""
    
    def _create_scoring_prompt(self, lead: Dict[str, Any]) -> str:
        """Create the scoring prompt for a specific lead"""
        return f"""Score this business lead:

Business: {lead.get('Name', 'Unknown')}
Address: {lead.get('Address', 'NA')}
Website: {lead.get('Website', 'NA')}
Phone: {lead.get('Phone', 'NA')}
Social Media: {lead.get('SocialMediaLinks', 'NA')}
Reviews: {lead.get('Reviews', 'NA')}
Rating: {lead.get('Rating', 0)}
Review Count: {lead.get('ReviewCount', 0)}
Image Count: {lead.get('Images', 'NA')}
Google Business Claimed: {lead.get('GoogleBusinessClaimed', False)}

Apply the R27 scoring rules and provide your score and reasoning."""
    
    def _parse_score_response(self, response: str) -> Tuple[int, str]:
        """Parse the AI response to extract score and reasoning"""
        lines = response.strip().split('\n')
        score = 5  # Default score
        reasoning = "Unable to parse scoring response"
        
        for line in lines:
            if line.startswith('Score:'):
                try:
                    score_str = line.replace('Score:', '').strip()
                    # Handle ranges like "8-10" by taking the average
                    if '-' in score_str:
                        parts = score_str.split('-')
                        score = int((int(parts[0]) + int(parts[1])) / 2)
                    else:
                        score = int(score_str.split('/')[0])  # Handle "8/10" format
                    score = max(0, min(10, score))  # Clamp to 0-10
                except (ValueError, IndexError, TypeError) as e:
                    logger.warning(f"Could not parse score from: {line}. Error: {e}")
            elif line.startswith('Reasoning:'):
                reasoning = line.replace('Reasoning:', '').strip()
        
        # If reasoning spans multiple lines
        if 'Reasoning:' in response:
            reasoning_start = response.index('Reasoning:') + len('Reasoning:')
            reasoning = response[reasoning_start:].strip()
        
        return score, reasoning