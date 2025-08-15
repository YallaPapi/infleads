"""
Apollo Smart Personalizer - Makes the most of limited data
No LinkedIn needed - just smart analysis of what we have
"""

import os
import re
from typing import Dict, Any, List
from openai import OpenAI
import logging

logger = logging.getLogger(__name__)


class ApolloSmartPersonalizer:
    """Generate truly unique emails from Apollo data alone"""
    
    def __init__(self, service_focus: str = 'general_automation'):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.service_focus = service_focus
    
    def extract_unique_details(self, description: str) -> List[str]:
        """Extract specific, unique details from company description"""
        
        details = []
        
        # Look for specific phrases that indicate unique aspects
        patterns = {
            'geography': r'(nationwide|international|global|across the \w+|multiple locations|[0-9]+ locations|[0-9]+ states)',
            'specialization': r'(speciali[sz]e in|focus on|exclusively|only|specifically)',
            'superlatives': r'(largest|fastest|first|only|best|leading|top)',
            'numbers': r'(\d+\+? years|\d+\+? employees|\d+\+? locations|\d+\+? products|since \d{4})',
            'unique_service': r'(24/7|emergency|same-day|instant|on-demand|unlimited)',
            'target_market': r'(enterprise|small business|startup|B2B|B2C|government|non-profit)',
            'certifications': r'(certified|licensed|accredited|authorized|approved)',
            'technology': r'(proprietary|custom|AI-powered|automated|cloud-based|mobile)',
        }
        
        for category, pattern in patterns.items():
            matches = re.findall(pattern, description, re.IGNORECASE)
            for match in matches:
                details.append(f"{category}: {match}")
        
        # Extract quoted phrases (often unique value props)
        quoted = re.findall(r'"([^"]+)"', description)
        for quote in quoted:
            details.append(f"motto: {quote}")
        
        # Look for pain point indicators
        if any(word in description.lower() for word in ['always', 'ensure', 'make sure', 'guarantee']):
            details.append('emphasis: reliability/consistency')
        
        if any(word in description.lower() for word in ['family', 'personal', 'local', 'community']):
            details.append('positioning: personal/local')
        
        return details
    
    def identify_implicit_challenges(self, lead_data: Dict[str, Any]) -> List[str]:
        """Identify challenges they probably have based on their profile"""
        
        challenges = []
        
        # Size-based challenges
        employees = lead_data.get('estimated_num_employees', 0)
        if employees > 0:
            if employees < 10:
                challenges.extend([
                    'everyone wearing multiple hats',
                    'founder still handling day-to-day tasks',
                    'no dedicated ops person'
                ])
            elif employees < 50:
                challenges.extend([
                    'growing faster than processes can keep up',
                    'communication breaking down across teams',
                    'manual processes that worked at 10 people failing at 30'
                ])
            elif employees < 500:
                challenges.extend([
                    'departments working in silos',
                    'inconsistent processes across locations',
                    'middle management bottlenecks'
                ])
            else:
                challenges.extend([
                    'small inefficiencies multiplied by thousands',
                    'change management across massive org',
                    'maintaining agility at scale'
                ])
        
        # Age-based challenges
        founded = lead_data.get('organization_founded_year', 0)
        if founded > 0:
            age = 2024 - founded
            if age < 2:
                challenges.append('building foundational systems')
            elif age < 5:
                challenges.append('scaling what worked in startup mode')
            elif age > 20:
                challenges.append('modernizing legacy processes')
        
        # Industry-specific challenges
        industry = lead_data.get('industry', '').lower()
        industry_challenges = {
            'restaurants': ['phone orders during rush', 'staff turnover', 'inventory waste'],
            'real estate': ['lead response time', 'showing coordination', 'document management'],
            'retail': ['inventory accuracy', 'customer questions', 'seasonal rushes'],
            'healthcare': ['appointment no-shows', 'insurance verification', 'patient communication'],
            'manufacturing': ['supply chain visibility', 'quality control', 'order tracking'],
            'professional services': ['billable hours tracking', 'project scope creep', 'client communication'],
        }
        
        if industry in industry_challenges:
            challenges.extend(industry_challenges[industry])
        
        return challenges
    
    def generate_unique_angle(self, lead_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate a unique angle for this specific company"""
        
        description = lead_data.get('organization_short_description', '')
        details = self.extract_unique_details(description)
        challenges = self.identify_implicit_challenges(lead_data)
        
        prompt = f"""
        Generate a UNIQUE angle for reaching out to this company.
        
        Company: {lead_data.get('organization_name')}
        Industry: {lead_data.get('industry')}
        Size: {lead_data.get('estimated_num_employees', 'unknown')} employees
        Description: {description}
        
        Unique details found: {details}
        Likely challenges: {challenges[:3]}  # Top 3 most relevant
        
        Create an angle that:
        1. References something SPECIFIC from their description (not generic)
        2. Connects it to a likely challenge
        3. Suggests a specific automation solution
        
        Format:
        Hook: [One specific observation from their description]
        Challenge: [The implied problem this creates]
        Solution: [Specific automation we could build]
        
        Be creative and specific. No generic "improve efficiency" bullshit.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You're an expert at finding unique angles for B2B outreach."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=200
            )
            
            content = response.choices[0].message.content
            
            # Parse response
            angle = {
                'hook': '',
                'challenge': '',
                'solution': ''
            }
            
            for line in content.split('\n'):
                if 'Hook:' in line:
                    angle['hook'] = line.split('Hook:')[1].strip()
                elif 'Challenge:' in line:
                    angle['challenge'] = line.split('Challenge:')[1].strip()
                elif 'Solution:' in line:
                    angle['solution'] = line.split('Solution:')[1].strip()
            
            return angle
            
        except Exception as e:
            logger.error(f"Error generating angle: {e}")
            return self._fallback_angle(lead_data, details, challenges)
    
    def _fallback_angle(self, lead_data: Dict[str, Any], details: List[str], challenges: List[str]) -> Dict[str, str]:
        """Fallback angle generation without GPT"""
        
        description = lead_data.get('organization_short_description', '')
        
        # Pick most interesting detail
        hook = details[0].split(': ')[1] if details else f"{lead_data.get('organization_name')} in {lead_data.get('industry')}"
        
        # Pick most relevant challenge
        challenge = challenges[0] if challenges else "manual processes slowing growth"
        
        # Generate solution based on challenge
        solution_map = {
            'phone orders': 'AI that takes orders when lines are busy',
            'staff turnover': 'automated training and onboarding system',
            'lead response': 'instant lead qualification and routing',
            'inventory': 'predictive inventory management',
            'multiple hats': 'AI assistant that handles routine tasks',
            'manual processes': 'workflow automation for repetitive tasks'
        }
        
        solution = None
        for key, sol in solution_map.items():
            if key in challenge.lower():
                solution = sol
                break
        
        if not solution:
            solution = "custom automation for your specific workflow"
        
        return {
            'hook': f"Noticed you mention {hook}",
            'challenge': f"which probably means {challenge}",
            'solution': solution
        }
    
    def generate_personalized_email(self, lead_data: Dict[str, Any]) -> str:
        """Generate truly personalized email from Apollo data"""
        
        angle = self.generate_unique_angle(lead_data)
        first_name = lead_data.get('first_name', 'there')
        company = lead_data.get('organization_name', 'your company')
        
        # Build email using the unique angle
        email_prompt = f"""
        Generate ONLY the 2 customized middle lines of an email (no greeting, no signature, no closing).
        
        Context:
        - Company: {company}
        - Hook: {angle['hook']}
        - Their Challenge: {angle['challenge']}
        - Our Solution: {angle['solution']}
        - SERVICE FOCUS: {self.service_focus}
        
        Generate exactly 2 SIMPLE sentences:
        1. First sentence: Say something specific about their company that shows you get them (use simple words)
        2. Second sentence: Say how our AI could help them (mention AI, be specific but simple)
        
        Rules:
        - Write like you're talking to a friend, not writing a business report
        - Use simple, everyday words (6th grade level)
        - MUST mention "AI" in the solution
        - Be specific but keep it simple
        - NO corporate buzzwords or jargon
        - NO greeting, closing, or signature
        - Just 2 simple sentences
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You write simple, conversational emails at a 6th grade reading level. Use short sentences. Talk like a normal person, not a corporate robot. ONLY write 2 sentences - no greetings or closings."},
                    {"role": "user", "content": email_prompt}
                ],
                temperature=0.7,
                max_tokens=100
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            # Fallback - just return the 2 customized lines
            return f"""{angle['hook']} - {angle['challenge']}.

We could build {angle['solution']} that integrates with your existing systems."""


# Example usage
if __name__ == "__main__":
    # Test with sample Apollo data
    test_lead = {
        'first_name': 'Steve',
        'organization_name': 'Vertical Runner Corp.',
        'industry': 'sporting goods',
        'estimated_num_employees': 19,
        'organization_founded_year': 2003,
        'organization_short_description': 'Vertical Runner is a run specialty store that everyone can rely on for all of their training needs. We are always willing to go above and beyond to make sure that you are always prepared for training and race day.'
    }
    
    personalizer = ApolloSmartPersonalizer()
    
    # Extract details
    details = personalizer.extract_unique_details(test_lead['organization_short_description'])
    print("Unique details found:", details)
    
    # Identify challenges
    challenges = personalizer.identify_implicit_challenges(test_lead)
    print("Likely challenges:", challenges[:3])
    
    # Generate angle
    angle = personalizer.generate_unique_angle(test_lead)
    print("Angle:", angle)
    
    # Generate email
    email = personalizer.generate_personalized_email(test_lead)
    print("\nFinal email:")
    print(email)