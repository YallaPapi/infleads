#!/usr/bin/env python3
"""
R27 Infinite AI Leads Agent
Automated lead generation pipeline with AI-powered scoring and outreach
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import pandas as pd
from dotenv import load_dotenv
from tqdm import tqdm
import time

# Import modules (to be created)
from src.providers import get_provider
from src.lead_scorer import LeadScorer
from src.email_generator import EmailGenerator
# from src.drive_uploader import DriveUploader  # Removed - local downloads only
from src.data_normalizer import DataNormalizer

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/r27_agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def validate_environment():
    """Validate required environment variables are present"""
    required_vars = {
        'APIFY_API_KEY': 'Apify API key for Google Maps scraping',
        'OPENAI_API_KEY': 'OpenAI API key for lead scoring and email generation'
    }
    
    missing = []
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing.append(f"{var} ({description})")
    
    # Google Drive no longer required - removed check
    
    if missing:
        logger.error("Missing required configuration:")
        for item in missing:
            logger.error(f"  - {item}")
        sys.exit(1)
    
    logger.info("All required environment variables validated")


def main():
    """Main execution pipeline"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='R27 Infinite AI Leads Agent')
    parser.add_argument('query', help='Search query (e.g., "dentists in Miami")')
    parser.add_argument('--limit', type=int, default=25, help='Number of results to fetch (default: 25)')
    parser.add_argument('--provider', default='apify', choices=['apify', 'google'], 
                       help='Data provider to use (default: apify)')
    parser.add_argument('--industry', default='default', 
                       help='Industry type for scoring (default, restaurant, dental, coffee_equipment, law_firm, real_estate, fitness, automotive, beauty_salon, home_services)')
    parser.add_argument('--no-upload', action='store_true', help='Skip Google Drive upload')
    parser.add_argument('--output-dir', default='output', help='Output directory for CSV files')
    
    args = parser.parse_args()
    
    # Validate environment
    validate_environment()
    
    logger.info(f"Starting R27 Infinite AI Leads Agent")
    logger.info(f"Query: {args.query}")
    logger.info(f"Limit: {args.limit}")
    logger.info(f"Provider: {args.provider}")
    logger.info(f"Industry: {args.industry}")
    
    try:
        # Step 1: Fetch leads from provider
        logger.info("Step 1: Fetching leads from provider...")
        provider = get_provider(args.provider)
        raw_leads = provider.fetch_places(args.query, args.limit)
        logger.info(f"Fetched {len(raw_leads)} leads")
        
        if not raw_leads:
            logger.error("No leads fetched. Exiting.")
            sys.exit(1)
        
        # Step 2: Normalize data
        logger.info("Step 2: Normalizing lead data...")
        normalizer = DataNormalizer()
        normalized_leads = normalizer.normalize(raw_leads)
        logger.info(f"Normalized {len(normalized_leads)} leads")
        
        # Step 3: Score leads with AI
        logger.info("Step 3: Scoring leads with AI...")
        scorer = LeadScorer(industry=args.industry)
        scored_leads = []
        
        for lead in tqdm(normalized_leads, desc="Scoring leads"):
            try:
                score, reasoning = scorer.score_lead(lead)
                lead['LeadScore'] = score
                lead['LeadScoreReasoning'] = reasoning
                scored_leads.append(lead)
            except Exception as e:
                logger.error(f"Failed to score lead {lead.get('Name', 'Unknown')}: {e}")
                lead['LeadScore'] = 'NA'
                lead['LeadScoreReasoning'] = 'Scoring failed'
                scored_leads.append(lead)
        
        # Step 4: Generate personalized emails
        logger.info("Step 4: Generating personalized emails...")
        email_gen = EmailGenerator(industry=args.industry)
        final_leads = []
        
        for lead in tqdm(scored_leads, desc="Generating emails"):
            try:
                email = email_gen.generate_email(lead)
                lead['DraftEmail'] = email
                final_leads.append(lead)
            except Exception as e:
                logger.error(f"Failed to generate email for {lead.get('Name', 'Unknown')}: {e}")
                lead['DraftEmail'] = 'Email generation failed'
                final_leads.append(lead)
        
        # Step 5: Create CSV
        logger.info("Step 5: Creating CSV file...")
        
        # Ensure output directory exists
        os.makedirs(args.output_dir, exist_ok=True)
        
        # Create filename
        date_str = datetime.now().strftime('%Y-%m-%d')
        safe_query = args.query.replace(' ', '_').replace(',', '')[:50]
        filename = f"{date_str}_{safe_query}.csv"
        filepath = os.path.join(args.output_dir, filename)
        
        # Create DataFrame with exact column order
        columns = ['Name', 'Address', 'Phone', 'Website', 'SocialMediaLinks', 
                  'Reviews', 'Images', 'LeadScore', 'LeadScoreReasoning', 'DraftEmail']
        
        df = pd.DataFrame(final_leads)
        
        # Ensure all columns exist
        for col in columns:
            if col not in df.columns:
                df[col] = 'NA'
        
        # Reorder columns
        df = df[columns]
        
        # Save to CSV
        df.to_csv(filepath, index=False)
        logger.info(f"CSV saved to: {filepath}")
        
        # Step 6: Done - CSV is saved locally
        print(f"\n[SUCCESS] Your leads CSV is ready:")
        print(f"Local file: {os.path.abspath(filepath)}")
        
        # Summary statistics
        print(f"\nSummary:")
        print(f"  Total leads: {len(final_leads)}")
        
        # Calculate average score if scores are numeric
        try:
            numeric_scores = [l['LeadScore'] for l in final_leads if isinstance(l['LeadScore'], (int, float))]
            if numeric_scores:
                avg_score = sum(numeric_scores) / len(numeric_scores)
                print(f"  Average lead score: {avg_score:.1f}/10")
        except:
            pass
        
    except Exception as e:
        logger.error(f"Fatal error in pipeline: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()