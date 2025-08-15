"""
Apollo Lead Processor with Deep Personalization
Analyzes Apollo CSV data and generates hyper-personalized emails
"""

import os
import logging
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional
from openai import OpenAI
from .smart_lead_analyzer import SmartLeadAnalyzer
from .apollo_smart_personalizer import ApolloSmartPersonalizer

logger = logging.getLogger(__name__)


class ApolloLeadProcessor:
    """Process Apollo leads with deep personalization"""
    
    def __init__(self, service_focus: str = 'general_automation', use_smart_analysis: bool = False):
        """Initialize with service focus"""
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.service_focus = service_focus
        self.use_smart_analysis = use_smart_analysis
        # Use the new smart personalizer by default
        self.smart_personalizer = ApolloSmartPersonalizer(service_focus=service_focus)
        if use_smart_analysis:
            self.smart_analyzer = SmartLeadAnalyzer()
    
    def analyze_lead(self, lead: pd.Series) -> Dict[str, Any]:
        """Deep analysis of a single lead from Apollo data"""
        
        # Extract key data points
        analysis = {
            'first_name': lead.get('first_name', ''),
            'title': lead.get('title', ''),
            'company': lead.get('organization_name', ''),
            'email': lead.get('email', ''),
            'linkedin_url': lead.get('linkedin_url', ''),
            'employees': int(lead.get('estimated_num_employees', 0)) if pd.notna(lead.get('estimated_num_employees')) else 0,
            'revenue': float(lead.get('organization_annual_revenue', 0)) if pd.notna(lead.get('organization_annual_revenue')) else 0,
            'founded_year': int(lead.get('organization_founded_year', 0)) if pd.notna(lead.get('organization_founded_year')) else 0,
            'industry': lead.get('industry', 'general'),
            'description': lead.get('organization_short_description', ''),
            'city': lead.get('city', ''),
            'phone': lead.get('organization_phone', '')
        }
        
        # Calculate derived insights
        current_year = datetime.now().year
        analysis['company_age'] = current_year - analysis['founded_year'] if analysis['founded_year'] > 0 else 0
        
        # Determine company scale
        if analysis['employees'] == 0:
            analysis['scale'] = 'unknown'
        elif analysis['employees'] < 10:
            analysis['scale'] = 'micro'
        elif analysis['employees'] < 50:
            analysis['scale'] = 'small'
        elif analysis['employees'] < 500:
            analysis['scale'] = 'medium'
        else:
            analysis['scale'] = 'enterprise'
        
        # Determine company maturity
        if analysis['company_age'] == 0:
            analysis['maturity'] = 'unknown'
        elif analysis['company_age'] < 2:
            analysis['maturity'] = 'startup'
        elif analysis['company_age'] < 5:
            analysis['maturity'] = 'early-stage'
        elif analysis['company_age'] < 10:
            analysis['maturity'] = 'growth-stage'
        elif analysis['company_age'] < 20:
            analysis['maturity'] = 'established'
        else:
            analysis['maturity'] = 'legacy'
        
        # Identify decision maker level
        title_lower = analysis['title'].lower()
        if any(x in title_lower for x in ['ceo', 'founder', 'owner', 'president']):
            analysis['decision_level'] = 'executive'
        elif any(x in title_lower for x in ['coo', 'operations', 'vp']):
            analysis['decision_level'] = 'senior'
        elif any(x in title_lower for x in ['director', 'head']):
            analysis['decision_level'] = 'management'
        elif any(x in title_lower for x in ['manager']):
            analysis['decision_level'] = 'middle_management'
        else:
            analysis['decision_level'] = 'unknown'
        
        return analysis
    
    def generate_personalized_email(self, analysis: Dict[str, Any]) -> str:
        """Generate hyper-personalized email based on lead analysis - ONLY 2 LINES"""
        
        # Build the prompt for GPT
        prompt = f"""
        Generate ONLY 2 customized sentences for an email (no greeting, no closing).
        
        COMPANY INFO:
        - Company: {analysis['company']}
        - Industry: {analysis['industry']}
        - Size: {analysis['employees']} employees ({analysis['scale']})
        - Age: {analysis['company_age']} years ({analysis['maturity']})
        - Description: {analysis['description'][:200]}
        
        SERVICE FOCUS: {self.service_focus}
        
        Generate exactly 2 SIMPLE sentences:
        1. First: Say something specific about their company (simple words, like talking to a friend)
        2. Second: Say how our AI could help them (MUST mention AI, be specific but simple)
        
        Rules:
        - Write at 6th grade reading level
        - Talk like a normal person, not a robot
        - MUST mention "AI" in the solution
        - NO corporate buzzwords
        - NO greeting, closing, or signature
        - Just 2 simple sentences
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You write simple emails at 6th grade level. Use short sentences. Talk like a normal person. ONLY 2 sentences, no greetings or closings."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=100
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating email: {e}")
            return f"Your {analysis['industry']} company with {analysis['employees']} employees likely faces scaling challenges.\n\nWe could build automation specifically for {analysis['industry']} that addresses these pain points."
    
    def generate_smart_email(self, lead: pd.Series) -> str:
        """Generate email using smart analysis instead of templates"""
        
        # Research the company
        research = self.smart_analyzer.research_company(lead.to_dict())
        
        # Generate personalized email based on research
        email = self.smart_analyzer.generate_personalized_email(lead.to_dict(), research)
        
        return email
    
    def process_apollo_csv(self, csv_path: str, output_path: str = None, max_leads: int = 100) -> pd.DataFrame:
        """Process entire Apollo CSV and generate personalized emails"""
        
        # Read Apollo data
        df = pd.read_csv(csv_path)
        
        # Limit to max_leads for faster processing
        if len(df) > max_leads:
            logger.info(f"CSV has {len(df)} leads, limiting to first {max_leads} for faster processing")
            df = df.head(max_leads)
        
        logger.info(f"Processing {len(df)} leads from Apollo")
        
        # Process each lead
        results = []
        for idx, lead in df.iterrows():
            try:
                # Analyze lead
                analysis = self.analyze_lead(lead)
                
                # Generate personalized email using the new smart personalizer
                try:
                    email = self.smart_personalizer.generate_personalized_email(lead.to_dict())
                except Exception as e:
                    logger.error(f"Error with smart personalizer: {e}")
                    # Fallback to basic personalization
                    email = self.generate_personalized_email(analysis)
                
                # Compile results
                result = {
                    'first_name': analysis['first_name'],
                    'title': analysis['title'],
                    'company': analysis['company'],
                    'email': analysis['email'],
                    'linkedin_url': analysis['linkedin_url'],
                    'industry': analysis['industry'],
                    'employees': analysis['employees'],
                    'company_age': analysis['company_age'],
                    'scale': analysis['scale'],
                    'maturity': analysis['maturity'],
                    'decision_level': analysis['decision_level'],
                    'personalized_email': email,
                    'personalization_score': self._calculate_personalization_score(email, analysis)
                }
                
                results.append(result)
                logger.info(f"Processed {idx+1}/{len(df)}: {analysis['company']}")
                
            except Exception as e:
                logger.error(f"Error processing lead {idx}: {e}")
                continue
        
        # Create results DataFrame
        results_df = pd.DataFrame(results)
        
        # Save if output path provided
        if output_path:
            results_df.to_csv(output_path, index=False)
            logger.info(f"Saved personalized emails to {output_path}")
        
        return results_df
    
    def _calculate_personalization_score(self, email: str, analysis: Dict[str, Any]) -> int:
        """Score how personalized the email is (0-100)"""
        
        score = 0
        email_lower = email.lower()
        
        # Check for name usage
        if analysis['first_name'].lower() in email_lower:
            score += 20
        
        # Check for company mention
        if analysis['company'].lower() in email_lower:
            score += 20
        
        # Check for industry reference
        if analysis['industry'] in email_lower:
            score += 15
        
        # Check for scale/size mention
        if str(analysis['employees']) in email or analysis['scale'] in email_lower:
            score += 15
        
        # Check for location mention
        if analysis['city'].lower() in email_lower:
            score += 10
        
        # Check for description reference
        if analysis['description'] and any(word in email_lower for word in analysis['description'].lower().split()[:5]):
            score += 10
        
        return min(score, 100)


# CLI usage
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Process Apollo leads with personalization')
    parser.add_argument('csv_path', help='Path to Apollo CSV file')
    parser.add_argument('--output', help='Output CSV path', default='personalized_leads.csv')
    parser.add_argument('--focus', help='Service focus', default='general_automation')
    
    args = parser.parse_args()
    
    processor = ApolloLeadProcessor(service_focus=args.focus)
    results = processor.process_apollo_csv(args.csv_path, args.output)
    
    print(f"\nProcessed {len(results)} leads")
    print(f"Average personalization score: {results['personalization_score'].mean():.1f}/100")
    print(f"Output saved to: {args.output}")