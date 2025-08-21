"""
Lead processing module.
Handles the core business logic for processing lead generation jobs.
"""

import os
import logging
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional

from .config import CSVConfig, JobConfig, PathConfig
from .utils import (
    sanitize_filename, 
    generate_timestamp_filename,
    remove_duplicates,
    calculate_progress
)
from .data_normalizer import DataNormalizer
from .email_generator import EmailGenerator
from .email_verifier import MailTesterVerifier, EmailStatus
from .email_scraper import WebsiteEmailScraper
from .search_history import SearchHistoryManager
from .instantly_integration import InstantlyIntegration, convert_r27_leads_to_instantly

logger = logging.getLogger(__name__)


class LeadProcessor:
    """Processes lead generation jobs"""
    
    def __init__(self):
        """Initialize the lead processor"""
        self.normalizer = DataNormalizer()
        self.email_generator = EmailGenerator()
        self.email_verifier = MailTesterVerifier()
        self.email_scraper = WebsiteEmailScraper()
        self.search_history = SearchHistoryManager()
        self.instantly = InstantlyIntegration()
    
    def process_job(self, job, provider):
        """
        Main processing pipeline for a lead generation job.
        
        Args:
            job: LeadGenerationJob instance
            provider: Lead provider instance
        """
        try:
            logger.info(f"Starting lead processing for job {job.job_id}")
            job.started_at = datetime.now()
            
            # Step 1: Fetch leads
            raw_leads = self._fetch_leads(job, provider)
            if not raw_leads:
                job.set_error("No leads found")
                return
            
            # Step 2: Normalize leads
            normalized_leads = self._normalize_leads(job, raw_leads)
            if not normalized_leads:
                job.set_error("Failed to normalize leads")
                return
            
            # Step 3: Scrape emails from websites
            if job.advanced_scraping:
                self._scrape_emails(job, normalized_leads)
            
            # Step 4: Verify emails
            if job.verify_emails:
                self._verify_emails(job, normalized_leads)
            
            # Step 5: Generate personalized emails
            if job.generate_emails:
                self._generate_emails(job, normalized_leads)
            
            # Step 6: Save results
            output_file = self._save_results(job, normalized_leads)
            job.result_file = output_file
            
            # Step 7: Add to Instantly if requested
            if job.add_to_instantly and job.instantly_campaign:
                self._add_to_instantly(job, normalized_leads)
            
            # Step 8: Track search history
            self._track_search_history(job)
            
            # Complete the job
            job.complete()
            logger.info(f"Job {job.job_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Error processing job {job.job_id}: {e}")
            job.set_error(str(e))
    
    def _fetch_leads(self, job, provider) -> List[Dict[str, Any]]:
        """Fetch leads from provider"""
        job.update_status("fetching", "Fetching leads...", 10)
        
        all_raw_leads = []
        seen_places = set()
        
        for query_idx, current_query in enumerate(job.queries):
            if job.cancelled:
                return []
            
            # Calculate progress for this query
            query_progress = 10 + (query_idx * 20 // len(job.queries))
            job.update_status("fetching", f"Fetching leads for: {current_query}", query_progress)
            
            # Adjust limit for multi-query requests
            effective_limit = job.limit if len(job.queries) == 1 else min(job.limit * 2, 100)
            
            logger.info(f"Fetching places for query: '{current_query}', limit: {effective_limit}")
            raw_leads_for_query = provider.fetch_places(current_query, effective_limit)
            
            if not raw_leads_for_query:
                logger.warning(f"No leads returned for query: {current_query}")
                continue
            
            # Process and deduplicate leads
            query_leads_added = 0
            for lead in raw_leads_for_query:
                unique_id = self._get_lead_unique_id(lead)
                
                if unique_id and unique_id not in seen_places:
                    seen_places.add(unique_id)
                    
                    # Parse and add search metadata
                    search_metadata = self._parse_search_query(current_query)
                    lead.update(search_metadata)
                    lead['full_query'] = current_query
                    
                    all_raw_leads.append(lead)
                    query_leads_added += 1
            
            logger.info(f"Added {query_leads_added} unique leads from query '{current_query}'")
        
        job.total_leads = len(all_raw_leads)
        logger.info(f"Total unique leads fetched: {job.total_leads}")
        
        return all_raw_leads
    
    def _normalize_leads(self, job, raw_leads: List[Dict]) -> List[Dict]:
        """Normalize lead data"""
        job.update_status("processing", "Normalizing lead data...", 30)
        
        try:
            normalized_leads = self.normalizer.normalize(raw_leads)
            logger.info(f"Normalized {len(normalized_leads)} leads successfully")
            return normalized_leads
        except Exception as e:
            logger.error(f"Failed to normalize leads: {e}")
            return []
    
    def _scrape_emails(self, job, leads: List[Dict]):
        """Scrape emails from lead websites"""
        job.update_status("processing", "Scraping emails from websites...", 40)
        
        try:
            scraped_emails = self.email_scraper.scrape_emails(leads)
            
            # Update leads with scraped emails
            for lead, email in zip(leads, scraped_emails):
                if email and email != 'NA':
                    lead['Email'] = email
                    job.emails_found += 1
            
            logger.info(f"Found {job.emails_found} emails from website scraping")
        except Exception as e:
            logger.error(f"Error scraping emails: {e}")
    
    def _verify_emails(self, job, leads: List[Dict]):
        """Verify email addresses"""
        job.update_status("verifying", "Verifying email addresses...", 50)
        
        emails_to_verify = []
        for lead in leads:
            email = lead.get('Email', 'NA')
            if email and email != 'NA':
                emails_to_verify.append(email)
        
        if not emails_to_verify:
            logger.info("No emails to verify")
            return
        
        job.emails_verified = len(emails_to_verify)
        
        # Sequential verification to avoid 403 errors
        logger.info(f"Starting sequential verification of {len(emails_to_verify)} emails")
        
        for idx, email in enumerate(emails_to_verify):
            if job.cancelled:
                break
            
            progress = 50 + (idx * 20 // len(emails_to_verify))
            job.update_status("verifying", f"Verifying email {idx+1}/{len(emails_to_verify)}", progress)
            
            try:
                result = self.email_verifier.verify_email(email)
                
                # Update lead with verification result
                for lead in leads:
                    if lead.get('Email') == email:
                        lead['email_verified'] = 'TRUE' if result['is_valid'] else ''
                        lead['email_status'] = result.get('status', 'unknown')
                        lead['email_quality_boost'] = result.get('quality_score', 0)
                        
                        if result['is_valid']:
                            job.valid_emails += 1
                        else:
                            job.invalid_emails += 1
                        break
                        
            except Exception as e:
                logger.error(f"Failed to verify {email}: {e}")
        
        logger.info(f"Email verification complete: {job.valid_emails}/{job.emails_verified} valid")
    
    def _generate_emails(self, job, leads: List[Dict]):
        """Generate personalized email content"""
        job.update_status("generating", "Generating personalized emails...", 70)
        
        try:
            for idx, lead in enumerate(leads):
                if job.cancelled:
                    break
                
                progress = 70 + (idx * 15 // len(leads))
                job.update_status("generating", f"Generating email {idx+1}/{len(leads)}", progress)
                
                email_content = self.email_generator.generate(lead, job.industry)
                lead['DraftEmail'] = email_content
            
            logger.info(f"Generated emails for {len(leads)} leads")
        except Exception as e:
            logger.error(f"Error generating emails: {e}")
    
    def _save_results(self, job, leads: List[Dict]) -> str:
        """Save results to CSV file"""
        job.update_status("saving", "Saving results to CSV...", 85)
        
        # Prepare filename
        safe_query = sanitize_filename(job.query, max_length=30)
        timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
        filename = f"{timestamp}_{safe_query}.csv"
        output_path = os.path.join(PathConfig.OUTPUT_DIR, filename)
        
        # Filter leads if export_verified_only is enabled
        export_leads = leads
        if job.export_verified_only:
            export_leads = [lead for lead in leads 
                          if lead.get('email_verified') == 'TRUE']
            logger.info(f"Exporting only verified leads: {len(export_leads)}/{len(leads)}")
        
        # Create DataFrame with standard columns
        df_data = []
        for lead in export_leads:
            row = {}
            for col in CSVConfig.STANDARD_COLUMNS:
                if col in lead:
                    row[col] = lead[col]
                else:
                    row[col] = CSVConfig.DEFAULT_VALUES.get(col, 'NA')
            df_data.append(row)
        
        df = pd.DataFrame(df_data, columns=CSVConfig.STANDARD_COLUMNS)
        
        # Save to CSV
        df.to_csv(output_path, index=False)
        logger.info(f"Saved {len(df_data)} leads to {output_path}")
        
        return output_path
    
    def _add_to_instantly(self, job, leads: List[Dict]):
        """Add leads to Instantly campaign"""
        job.update_status("processing", "Adding leads to Instantly...", 90)
        
        try:
            # Convert leads to Instantly format
            instantly_leads = convert_r27_leads_to_instantly(leads)
            
            # Add to campaign
            result = self.instantly.add_leads_to_campaign(
                job.instantly_campaign,
                instantly_leads
            )
            
            if result.get('success'):
                logger.info(f"Successfully added {len(instantly_leads)} leads to Instantly campaign")
            else:
                logger.error(f"Failed to add leads to Instantly: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"Error adding leads to Instantly: {e}")
    
    def _track_search_history(self, job):
        """Track search in history"""
        try:
            self.search_history.add_search(
                query=job.query,
                results_count=job.total_leads,
                provider='multi' if len(job.queries) > 1 else 'auto'
            )
        except Exception as e:
            logger.warning(f"Failed to track search history: {e}")
    
    def _get_lead_unique_id(self, lead: Dict) -> Optional[Any]:
        """Get unique identifier for a lead"""
        place_id = lead.get('place_id')
        if place_id:
            return place_id
        
        # Fallback to name + address
        if lead.get('name') and lead.get('address'):
            return (lead['name'], lead['address'])
        
        return None
    
    def _parse_search_query(self, query: str) -> Dict[str, str]:
        """Parse search query into keyword and location"""
        query_parts = query.split(' in ')
        
        if len(query_parts) == 2:
            return {
                'search_keyword': query_parts[0].strip(),
                'search_location': query_parts[1].strip()
            }
        
        # Fallback parsing
        words = query.split()
        if len(words) >= 3:
            potential_location_words = 2 if len(words) > 4 else min(2, len(words) - 1)
            return {
                'search_keyword': ' '.join(words[:-potential_location_words]),
                'search_location': ' '.join(words[-potential_location_words:])
            }
        elif len(words) == 2:
            return {
                'search_keyword': words[0],
                'search_location': words[1]
            }
        else:
            return {
                'search_keyword': query,
                'search_location': ''
            }