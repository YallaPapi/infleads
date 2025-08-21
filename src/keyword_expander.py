"""
LLM-powered keyword expansion for lead generation
Generates related business types and search terms
"""

import os
import logging
import requests
import json
from typing import List, Dict, Set
from openai import OpenAI

logger = logging.getLogger(__name__)

class KeywordExpander:
    """Expands search keywords using LLM to generate related business types"""
    
    def __init__(self):
        self.openai_client = None
        
        # Initialize OpenAI client if API key is available
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key:
            self.openai_client = OpenAI(api_key=openai_key)
            logger.info("KeywordExpander initialized with OpenAI")
        else:
            logger.warning("No OpenAI API key found - keyword expansion will require OpenAI")
    
    def expand_keywords(self, base_keyword: str, location: str = "", max_variants: int = 15) -> List[Dict[str, str]]:
        """
        Expand a base keyword into related business types
        
        Args:
            base_keyword: The main search term (e.g., "lawyers")
            location: Optional location context
            max_variants: Maximum number of variants to generate
            
        Returns:
            List of dictionaries with 'keyword' and 'description' keys
        """
        logger.info(f"Expanding keyword: '{base_keyword}' for location: '{location}'")
        
        if not self.openai_client:
            raise ValueError("OpenAI client not configured. Dynamic keyword expansion requires OpenAI API key.")
        
        return self._expand_with_openai(base_keyword, location, max_variants)
    
    def _expand_with_openai(self, base_keyword: str, location: str, max_variants: int) -> List[Dict[str, str]]:
        """Use OpenAI to generate keyword variants"""
        try:
            location_context = f" in {location}" if location else ""
            
            prompt = f"""Generate {max_variants} related business types and search terms for "{base_keyword}"{location_context}.

Requirements:
- Include specific specialties, variations, and related professions
- Focus on searchable business types that would appear on Google Maps
- Include both formal and common terms
- No duplicates
- Return as JSON array with 'keyword' and 'description' fields

Example for "lawyers":
[
  {{"keyword": "personal injury lawyers", "description": "Lawyers specializing in accident and injury cases"}},
  {{"keyword": "family attorneys", "description": "Legal professionals handling divorce, custody, family law"}},
  {{"keyword": "criminal defense attorneys", "description": "Lawyers defending clients in criminal cases"}}
]

Generate for "{base_keyword}":"""

            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a business research assistant. Generate diverse, specific business search terms that would find real businesses on Google Maps."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.7
            )
            
            # Parse the JSON response
            content = response.choices[0].message.content.strip()
            
            # Extract JSON from the response (handle potential markdown formatting)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            variants = json.loads(content)
            
            # Validate and clean the results
            cleaned_variants = []
            seen_keywords = set()
            
            for variant in variants:
                if isinstance(variant, dict) and 'keyword' in variant:
                    keyword = variant['keyword'].strip().lower()
                    if keyword and keyword not in seen_keywords:
                        seen_keywords.add(keyword)
                        cleaned_variants.append({
                            'keyword': variant['keyword'].strip(),
                            'description': variant.get('description', '').strip()
                        })
            
            logger.info(f"Generated {len(cleaned_variants)} keyword variants using OpenAI")
            return cleaned_variants[:max_variants]
            
        except Exception as e:
            logger.error(f"OpenAI keyword expansion failed: {e}")
            raise RuntimeError(f"Dynamic keyword expansion failed: {e}. No fallback patterns available.")
    
    def combine_with_location(self, keywords: List[Dict[str, str]], location: str) -> List[Dict[str, str]]:
        """Combine keywords with location for final search terms"""
        if not location:
            return keywords
        
        combined = []
        for keyword_data in keywords:
            keyword = keyword_data['keyword']
            # Add location if not already present
            if location.lower() not in keyword.lower():
                combined_keyword = f"{keyword} in {location}"
            else:
                combined_keyword = keyword
            
            combined.append({
                'keyword': combined_keyword,
                'description': keyword_data['description']
            })
        
        return combined