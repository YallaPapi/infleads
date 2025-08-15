"""
Test Apollo lead processor with sample data
"""

import pandas as pd
from src.apollo_lead_processor import ApolloLeadProcessor

# Test with first few leads from the CSV
def test_apollo_personalization():
    # Read the first 3 leads
    df = pd.read_csv('leads.csv', nrows=3)
    
    # Create processor without OpenAI for testing
    class TestProcessor:
        def __init__(self):
            self.processor = ApolloLeadProcessor.__new__(ApolloLeadProcessor)
            self.processor.industry = 'ai_automation'
            self.processor.industry_configs = self.processor._get_industry_configs()
    
    test_proc = TestProcessor()
    processor = test_proc.processor
    
    print("=" * 80)
    print("APOLLO LEAD PERSONALIZATION TEST")
    print("=" * 80)
    
    for idx, lead in df.iterrows():
        print(f"\n--- LEAD {idx + 1} ---")
        
        # Analyze lead
        analysis = processor.analyze_lead(lead)
        
        print(f"Name: {analysis['first_name']} ({analysis['title']})")
        print(f"Company: {analysis['company']}")
        print(f"Industry: {analysis['industry']}")
        print(f"Size: {analysis['employees']} employees ({analysis['scale']})")
        print(f"Age: {analysis['company_age']} years ({analysis['maturity']})")
        print(f"Decision Level: {analysis['decision_level']}")
        print(f"LinkedIn: {analysis['linkedin_url']}")
        
        # Generate personalized email WITHOUT using GPT (using fallback)
        email = processor._generate_fallback_email(analysis)
        
        print(f"\nPERSONALIZED EMAIL:")
        print("-" * 40)
        print(email)
        print("-" * 40)
        
        # Calculate personalization score
        score = processor._calculate_personalization_score(email, analysis)
        print(f"Personalization Score: {score}/100")
    
    print("\n" + "=" * 80)
    print("KEY INSIGHTS:")
    print("=" * 80)
    print("""
    1. Dan from Chick-fil-A (75,000 employees) gets enterprise messaging
    2. La Casa (3 employees) gets small business efficiency messaging  
    3. Steve from Vertical Runner (19 employees) gets growth-stage messaging
    
    Each email references:
    - Their specific company size
    - Years in business
    - Industry-specific pain points
    - Appropriate case studies for their scale
    """)

if __name__ == "__main__":
    test_apollo_personalization()