#!/usr/bin/env python3
"""
Flask Web GUI for R27 Infinite AI Leads Agent
"""

from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import os
import json
import threading
import time
from datetime import datetime, timedelta
import pandas as pd
from dotenv import load_dotenv
import logging
import pickle
from collections import deque
from flask import Response
import queue
import tempfile
import zipfile

# Load environment variables FIRST
load_dotenv()

# Import our modules
from src.providers import get_provider
# Lead scoring functionality removed
from src.email_generator import EmailGenerator
# from src.drive_uploader import DriveUploader  # Removed - using local downloads instead
from src.data_normalizer import DataNormalizer
from src.industry_configs import IndustryConfig
from src.apollo_lead_processor import ApolloLeadProcessor
from src.email_verifier import MailTesterVerifier, EmailStatus
from src.scheduler import LeadScheduler
from src.email_scraper import WebsiteEmailScraper
from src.keyword_expander import KeywordExpander
from src.search_history import SearchHistoryManager
from src.providers.openstreetmap_provider import OpenStreetMapProvider
from src.providers.yellowpages_api_provider import YellowPagesAPIProvider
from src.lead_enrichment import LeadEnricher
from src.instantly_integration import InstantlyIntegration, CampaignTemplates, convert_r27_leads_to_instantly, create_campaign_from_r27_leads

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
CORS(app)

# In-memory log storage for debugging terminal
debug_logs = deque(maxlen=1000)  # Keep last 1000 log entries
log_subscribers = []

class DebugLogHandler(logging.Handler):
    """Custom log handler that stores logs for the debug terminal"""
    def emit(self, record):
        try:
            log_entry = {
                'timestamp': datetime.fromtimestamp(record.created).strftime('%H:%M:%S.%f')[:-3],
                'level': record.levelname,
                'name': record.name,
                'message': self.format(record)
            }
            debug_logs.append(log_entry)
            
            # Notify all SSE subscribers
            for subscriber_queue in log_subscribers[:]:  # Copy to avoid modification during iteration
                try:
                    subscriber_queue.put_nowait(log_entry)
                except queue.Full:
                    log_subscribers.remove(subscriber_queue)
        except Exception:
            pass  # Ignore errors in logging handler

# Configure comprehensive logging
debug_handler = DebugLogHandler()
debug_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/flask_app.log'),
        logging.StreamHandler(),
        debug_handler
    ]
)
logger = logging.getLogger(__name__)

# Store job status
jobs = {}
apollo_jobs = {}

# Job persistence
COMPLETED_JOBS_FILE = 'data/completed_jobs.json'

def ensure_data_dir():
    """Ensure data directory exists"""
    os.makedirs('data', exist_ok=True)

def save_completed_job(job):
    """Save completed job to persistent storage"""
    ensure_data_dir()
    
    # Load existing completed jobs
    completed_jobs = load_completed_jobs()
    
    # Create job record
    job_record = {
        'job_id': job.job_id,
        'query': job.query,
        'limit': job.limit,
        'status': job.status,
        'total_leads': job.total_leads,
        'emails_verified': job.emails_verified,
        'valid_emails': job.valid_emails,
        'result_file': job.result_file,
        'share_link': job.share_link,
        'error': job.error,
        'completed_at': datetime.now().isoformat(),
        'verify_emails': job.verify_emails,
        'generate_emails': job.generate_emails,
        'export_verified_only': job.export_verified_only,
        'advanced_scraping': job.advanced_scraping
    }
    
    # Add to completed jobs (keep only last 100 jobs)
    completed_jobs[job.job_id] = job_record
    
    # Keep only the 100 most recent jobs
    if len(completed_jobs) > 100:
        # Sort by completion time and keep most recent 100
        sorted_jobs = sorted(completed_jobs.items(), 
                           key=lambda x: x[1].get('completed_at', ''), 
                           reverse=True)
        completed_jobs = dict(sorted_jobs[:100])
    
    # Save to file
    try:
        with open(COMPLETED_JOBS_FILE, 'w') as f:
            json.dump(completed_jobs, f, indent=2)
        logger.info(f"Saved completed job {job.job_id} to persistent storage")
    except Exception as e:
        logger.error(f"Failed to save completed job: {e}")

def load_completed_jobs():
    """Load completed jobs from persistent storage"""
    if not os.path.exists(COMPLETED_JOBS_FILE):
        return {}
    
    try:
        with open(COMPLETED_JOBS_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load completed jobs: {e}")
        return {}

def get_job_info(job_id):
    """Get job info from memory or persistent storage"""
    # First check active jobs in memory
    if job_id in jobs:
        return jobs[job_id]
    
    # Then check completed jobs from storage
    completed_jobs = load_completed_jobs()
    if job_id in completed_jobs:
        return completed_jobs[job_id]
    
    return None

# Initialize scheduler
scheduler = LeadScheduler()

# Initialize search history manager
search_history = SearchHistoryManager()

def process_scheduled_search(query: str, limit: int, verify_emails: bool, generate_emails: bool = True):
    """Process a scheduled search"""
    job_id = f"scheduled_{int(time.time())}"
    job = LeadGenerationJob(job_id, query, limit, verify_emails=verify_emails, generate_emails=generate_emails)
    jobs[job_id] = job
    
    # Process the job synchronously for scheduler
    process_leads(job)
    
    return {
        'file_path': job.result_file,
        'leads_found': job.total_leads,
        'emails_found': job.emails_verified,
        'emails_valid': job.valid_emails
    }

# Start the scheduler with the processing callback
scheduler.start(process_callback=process_scheduled_search)

class LeadGenerationJob:
    def __init__(self, job_id, query, limit, industry='default', verify_emails=False, generate_emails=True, export_verified_only=False, advanced_scraping=False, queries=None, add_to_instantly=False, instantly_campaign=''):
        self.job_id = job_id
        self.query = query
        self.queries = queries or [query] if query else []  # Support multiple queries
        self.limit = limit
        # DEBUG: Print job initialization
        print(f"FLASK DEBUG: Job created with {len(self.queries)} queries: {self.queries}")
        print(f"FLASK DEBUG: Limit per query: {self.limit}")
        self.industry = industry
        self.verify_emails = verify_emails
        self.generate_emails = generate_emails  # New toggle for email generation
        self.export_verified_only = export_verified_only  # New toggle for verified emails only
        self.advanced_scraping = advanced_scraping  # New toggle for advanced website scraping
        self.add_to_instantly = add_to_instantly  # Auto-add to Instantly campaign
        self.instantly_campaign = instantly_campaign  # Instantly campaign ID
        self.status = "starting"
        self.progress = 0
        self.message = "Initializing..."
        self.result_file = None
        self.cancelled = False
        self.share_link = None
        self.error = None
        self.leads_data = []
        self.total_leads = 0
        self.emails_verified = 0
        self.valid_emails = 0
        
    def to_dict(self):
        return {
            'job_id': self.job_id,
            'query': self.query,
            'limit': self.limit,
            'status': self.status,
            'progress': self.progress,
            'message': self.message,
            'result_file': self.result_file,
            'share_link': self.share_link,
            'error': self.error,
            'total_leads': self.total_leads,
            'emails_verified': self.emails_verified,
            'valid_emails': self.valid_emails,
            'leads_preview': self.leads_data[:50] if self.leads_data else []  # Show first 50 leads
        }

def process_leads(job):
    """Background task to process leads"""
    print(f"DEBUG: Starting process_leads for job {job.job_id}")
    try:
        # Step 1: Fetch leads
        job.status = "fetching"
        job.progress = 10
        job.message = "Fetching leads from Google Maps..."
        
        logger.info(f"Getting provider for job {job.job_id}")
        try:
            # For multi-query requests, use DirectGoogleMapsProvider for more predictable results
            if len(job.queries) > 1:
                from src.providers.serp_provider import DirectGoogleMapsProvider
                provider = DirectGoogleMapsProvider()
                logger.info(f"Using DirectGoogleMapsProvider for multi-query request ({len(job.queries)} queries)")
            else:
                provider = get_provider('auto')  # Auto-detects best available (NOT APIFY)
                logger.info(f"Using provider: {provider.__class__.__name__}")
            
            # Check API key availability
            if hasattr(provider, 'api_key') and not provider.api_key:
                error_msg = "Google API key not configured. Please set GOOGLE_API_KEY environment variable."
                logger.error(error_msg)
                job.status = "error"
                job.error = error_msg
                return
            
            all_raw_leads = []
            seen_places = set()
            
            for current_query in job.queries:
                # When using multiple queries, increase the limit per query to get more total results
                # This helps overcome individual provider limitations
                effective_limit = job.limit if len(job.queries) == 1 else min(job.limit * 2, 100)
                logger.info(f"Fetching places for query: '{current_query}', limit: {effective_limit} (original: {job.limit})")
                raw_leads_for_query = provider.fetch_places(current_query, effective_limit)
                logger.info(f"Provider returned {len(raw_leads_for_query) if raw_leads_for_query else 0} leads for '{current_query}'")
                
                # Add leads from this query, deduplicating as we go
                query_leads_added = 0
                for lead in raw_leads_for_query or []:
                    place_id = lead.get('place_id')
                    unique_identifier = None
                    
                    if place_id:
                        unique_identifier = place_id
                    elif lead.get('name') and lead.get('address'):
                        # Fallback deduplication for providers without place_id
                        unique_identifier = (lead['name'], lead['address'])
                    
                    if unique_identifier and unique_identifier not in seen_places:
                        seen_places.add(unique_identifier)
                        # Add the search query to each lead so we know what search found it
                        # Parse out the keyword and location from the query
                        # Typical format: "keyword in location" or "keyword location"
                        query_parts = current_query.split(' in ')
                        if len(query_parts) == 2:
                            search_keyword = query_parts[0].strip()
                            location = query_parts[1].strip()
                        else:
                            # Fallback: assume last 2-3 words are location
                            words = current_query.split()
                            if len(words) >= 3:
                                # Common patterns: "lawyers las vegas", "coffee shops austin"
                                # Check if last words look like a location
                                potential_location_words = 2 if len(words) > 4 else min(2, len(words) - 1)
                                search_keyword = ' '.join(words[:-potential_location_words])
                                location = ' '.join(words[-potential_location_words:])
                            elif len(words) == 2:
                                search_keyword = words[0]
                                location = words[1]
                            else:
                                search_keyword = current_query
                                location = ''
                        
                        lead['search_keyword'] = search_keyword
                        lead['search_location'] = location
                        lead['full_query'] = current_query
                        all_raw_leads.append(lead)
                        query_leads_added += 1
                
                logger.info(f"Added {query_leads_added} unique leads from query '{current_query}' (after deduplication)")

            raw_leads = all_raw_leads
            logger.info(f"Total unique leads from all {len(job.queries)} queries: {len(raw_leads)}")
            
            # DEBUG: Log query processing details
            logger.info(f"DEBUG: Multi-query processing summary:")
            logger.info(f"  - Number of queries: {len(job.queries)}")
            logger.info(f"  - Original limit per query: {job.limit}")
            logger.info(f"  - Total raw leads collected: {len(raw_leads)}")
            logger.info(f"  - Queries: {job.queries}")
            print(f"FLASK DEBUG: Multi-query summary - {len(job.queries)} queries, {len(raw_leads)} total leads")
            print(f"FLASK DEBUG: Job queries list: {job.queries}")
            print(f"FLASK DEBUG: Using provider: {provider.__class__.__name__}")
            
            # DEBUG: Log raw lead data
            if raw_leads:
                print(f"FLASK DEBUG: First raw lead keys: {list(raw_leads[0].keys())}")
                print(f"FLASK DEBUG: First raw lead name: {raw_leads[0].get('name', 'NOT_FOUND')}")
                print(f"FLASK DEBUG: First raw lead phone: {raw_leads[0].get('phone', 'NOT_FOUND')}")
                logger.info(f"DEBUG: First raw lead keys: {list(raw_leads[0].keys())}")
                logger.info(f"DEBUG: First raw lead name: {raw_leads[0].get('name', 'NOT_FOUND')}")
                logger.info(f"DEBUG: First raw lead phone: {raw_leads[0].get('phone', 'NOT_FOUND')}")
            
        except Exception as e:
            error_msg = f"Provider error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            job.status = "error"
            job.error = error_msg
            return
        
        if not raw_leads:
            error_msg = f"No leads found for query: '{job.query}'. This could be due to: 1) Invalid API key, 2) API quota exceeded, 3) No businesses match the query, 4) Geographic restrictions."
            logger.warning(error_msg)
            job.status = "error"
            job.error = error_msg
            return
        
        job.total_leads = len(raw_leads)
        job.progress = 25
        job.message = f"Found {len(raw_leads)} businesses"
        
        # Step 2: Normalize data
        job.status = "normalizing"
        job.progress = 30
        job.message = "Normalizing lead data..."
        
        normalizer = DataNormalizer()
        normalized_leads = normalizer.normalize(raw_leads)
        
        # DEBUG: Log normalized data
        if normalized_leads:
            print(f"FLASK DEBUG: First normalized lead keys: {list(normalized_leads[0].keys())}")
            print(f"FLASK DEBUG: First normalized lead Name: {normalized_leads[0].get('Name', 'NOT_FOUND')}")
            print(f"FLASK DEBUG: First normalized lead Phone: {normalized_leads[0].get('Phone', 'NOT_FOUND')}")
            logger.info(f"DEBUG: First normalized lead keys: {list(normalized_leads[0].keys())}")
            logger.info(f"DEBUG: First normalized lead Name: {normalized_leads[0].get('Name', 'NOT_FOUND')}")
            logger.info(f"DEBUG: First normalized lead Phone: {normalized_leads[0].get('Phone', 'NOT_FOUND')}")
        
        # Step 2.3: Scrape emails and contact info from websites (FREE!)
        if job.advanced_scraping:
            job.status = "scraping_contacts"
            job.progress = 32
            job.message = "Scraping emails and contact info from websites..."
        else:
            job.status = "scraping_emails"
            job.progress = 32
            job.message = "Scraping emails from websites..."
        
        try:
            scraper = WebsiteEmailScraper()
            normalized_leads = scraper.scrape_contacts_bulk(normalized_leads, max_workers=5, advanced_scraping=job.advanced_scraping)
            emails_found = sum(1 for lead in normalized_leads 
                             if lead.get('Email') and lead['Email'] != 'NA')
            
            if job.advanced_scraping:
                names_found = sum(1 for lead in normalized_leads 
                                if lead.get('FirstName') and lead['FirstName'] != 'NA')
                logger.info(f"Found {emails_found} emails and {names_found} contact names from website scraping")
                job.message = f"Found {emails_found} emails and {names_found} names from websites"
            else:
                logger.info(f"Found {emails_found} emails from website scraping")
                job.message = f"Found {emails_found} emails from websites"
        except Exception as e:
            logger.error(f"Website scraping failed: {e}")
        
        # Step 2.5: Email Verification (if enabled) - PARALLEL PROCESSING
        if job.verify_emails and os.getenv('MAILTESTER_API_KEY'):
            job.status = "verifying_emails"
            job.progress = 35
            job.message = "Verifying email addresses..."
            
            try:
                from concurrent.futures import ThreadPoolExecutor, as_completed
                import threading
                
                verifier = MailTesterVerifier()
                
                # Prepare emails for verification
                emails_to_verify = []
                email_lead_map = {}
                
                for i, lead in enumerate(normalized_leads):
                    email = lead.get('Email', '').strip()
                    if email and email != 'NA':
                        emails_to_verify.append((i, email))
                        email_lead_map[email] = i
                
                logger.info(f"Starting parallel verification of {len(emails_to_verify)} emails")
                
                # Thread-safe counters
                completed_count = [0]  # Use list for mutable counter
                lock = threading.Lock()
                
                def verify_single_email(email_data):
                    """Verify a single email with thread safety"""
                    idx, email = email_data
                    try:
                        result = verifier.verify_email(email)
                        
                        with lock:
                            # Update counters safely
                            job.emails_verified += 1
                            if result.status == EmailStatus.VALID:
                                job.valid_emails += 1
                            
                            # Update progress
                            completed_count[0] += 1
                            progress_pct = int((completed_count[0] / len(emails_to_verify)) * 10)
                            job.progress = 35 + progress_pct
                            job.message = f"Verified {completed_count[0]}/{len(emails_to_verify)} emails"
                        
                        return (idx, email, result, None)
                    except Exception as e:
                        logger.warning(f"Email verification failed for {email}: {e}")
                        return (idx, email, None, str(e))
                
                # Use ThreadPoolExecutor for parallel processing
                # Limit to 5 threads to respect API rate limits while gaining speed
                max_workers = min(5, len(emails_to_verify))
                
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    # Submit all verification tasks
                    future_to_email = {
                        executor.submit(verify_single_email, email_data): email_data 
                        for email_data in emails_to_verify
                    }
                    
                    # Process results as they complete
                    for future in as_completed(future_to_email):
                        if job.cancelled:
                            executor.shutdown(wait=False)
                            break
                            
                        try:
                            idx, email, result, error = future.result()
                            lead = normalized_leads[idx]
                            
                            if result:
                                # Add verification data
                                lead['email_verified'] = result.status == EmailStatus.VALID
                                lead['email_status'] = result.status.value
                                lead['email_score'] = result.score
                                
                                # Adjust scoring boost
                                if result.status == EmailStatus.VALID:
                                    lead['email_quality_boost'] = 20
                                elif result.status == EmailStatus.CATCH_ALL:
                                    lead['email_quality_boost'] = 10
                                elif result.status in [EmailStatus.INVALID, EmailStatus.DISPOSABLE]:
                                    lead['email_quality_boost'] = -50
                                else:
                                    lead['email_quality_boost'] = 0
                            else:
                                # Verification failed
                                lead['email_verified'] = False
                                lead['email_status'] = 'error'
                                lead['email_quality_boost'] = 0
                        except Exception as e:
                            logger.error(f"Error processing verification result: {e}")
                
                # Set default values for leads without emails
                for lead in normalized_leads:
                    if not lead.get('Email') or lead.get('Email') == 'NA':
                        lead['email_verified'] = False
                        lead['email_status'] = 'missing'
                        lead['email_quality_boost'] = -10
                
                logger.info(f"Parallel email verification complete: {job.valid_emails}/{job.emails_verified} valid")
                
            except Exception as e:
                logger.error(f"Email verification service error: {e}")
                job.message = "Email verification skipped due to error"
        
        # Lead scoring functionality removed - skip directly to email generation
        scored_leads = normalized_leads
        job.progress = 60
        job.message = "SCORING REMOVED - Leads processed, preparing for next step..."
        print("DEBUG: SCORING HAS BEEN REMOVED FROM THIS CODE")
        
        # Step 4: Generate emails (conditional)
        logger.info(f"DEBUG: job.generate_emails = {job.generate_emails}")
        print(f"FLASK DEBUG: job.generate_emails = {job.generate_emails}")
        
        if job.generate_emails:
            job.status = "generating_emails"
            job.progress = 60
            job.message = "Generating personalized emails..."
            
            print("FLASK DEBUG: Taking email generation branch")
            logger.info("DEBUG: Taking email generation branch")
            
            email_gen = EmailGenerator(industry=job.industry)
            final_leads = []
            
            for i, lead in enumerate(scored_leads):
                try:
                    email = email_gen.generate_email(lead)
                    lead['DraftEmail'] = email
                    final_leads.append(lead)
                    job.progress = 60 + int((i + 1) / len(scored_leads) * 20)
                    job.message = f"Generated {i + 1}/{len(scored_leads)} emails"
                except Exception as e:
                    logger.error(f"Failed to generate email: {e}")
                    lead['DraftEmail'] = 'Email generation failed'
                    final_leads.append(lead)
        else:
            # Skip email generation - just add empty email field
            job.status = "finalizing"
            job.progress = 75
            job.message = "Finalizing leads data..."
            
            print("FLASK DEBUG: Skipping email generation branch")
            logger.info("DEBUG: Skipping email generation branch")
            
            final_leads = []
            for lead in scored_leads:
                lead['DraftEmail'] = 'Email generation disabled'
                final_leads.append(lead)
        
        # Apply verified email filter if requested
        if job.export_verified_only and job.verify_emails:
            filtered_leads = []
            for lead in final_leads:
                if lead.get('email_verified') == True or lead.get('email_status') == 'valid':
                    filtered_leads.append(lead)
            
            original_count = len(final_leads)
            
            # If filtering would remove ALL leads, keep them all with a warning
            if len(filtered_leads) == 0 and original_count > 0:
                logger.warning(f"Export verified only would filter ALL {original_count} leads! Keeping all leads instead.")
                job.message = f"Warning: No verified emails found, exporting all {original_count} leads"
            else:
                final_leads = filtered_leads
                logger.info(f"Filtered leads: {original_count} -> {len(final_leads)} (verified emails only)")
                job.message = f"Filtered to {len(final_leads)} leads with verified emails"
        
        # Store leads data for preview
        job.leads_data = final_leads
        
        # DEBUG: Log final leads data for preview
        if final_leads:
            logger.info(f"DEBUG: Final leads count for preview: {len(final_leads)}")
            logger.info(f"DEBUG: First final lead keys: {list(final_leads[0].keys())}")
            logger.info(f"DEBUG: First final lead Name: {final_leads[0].get('Name', 'NOT_FOUND')}")  
            logger.info(f"DEBUG: First final lead Phone: {final_leads[0].get('Phone', 'NOT_FOUND')}")
            logger.info(f"DEBUG: First final lead Email: {final_leads[0].get('Email', 'NOT_FOUND')}")
        
        # Step 5: Create CSV
        job.status = "creating_csv"
        job.progress = 85
        job.message = "Creating CSV file..."
        
        # Ensure output directory exists
        os.makedirs('output', exist_ok=True)
        
        # Create filename
        date_str = datetime.now().strftime('%Y-%m-%d_%H%M%S')
        # Debug: Print the original query
        print(f"FLASK DEBUG: Original job.query: '{job.query}'")
        # Sanitize query for filename - remove invalid filename characters
        import re
        safe_query = re.sub(r'[<>:"/\\|?*]', '_', job.query.replace(' ', '_'))[:30]
        print(f"FLASK DEBUG: Sanitized safe_query: '{safe_query}'")
        filename = f"{date_str}_{safe_query}.csv"
        print(f"FLASK DEBUG: Final filename: '{filename}'")
        filepath = os.path.join('output', filename)
        
        # DEBUG: Log what we're about to save
        logger.info(f"DEBUG: About to save CSV with {len(final_leads)} leads")
        if not final_leads:
            logger.error("ERROR: final_leads is empty! Cannot create CSV with data.")
            # If we have scored_leads but no final_leads, use scored_leads instead
            if scored_leads:
                logger.info(f"Using scored_leads instead: {len(scored_leads)} leads")
                final_leads = scored_leads
                for lead in final_leads:
                    if 'DraftEmail' not in lead:
                        lead['DraftEmail'] = 'N/A'
        
        # Create DataFrame with complete column order including Name, Address, SearchKeyword and Location
        columns = ['Name', 'Address', 'Phone', 'Email', 'Website', 'SearchKeyword', 'Location']
        
        # Add email verification column if email verification was enabled
        if job.verify_emails:
            columns.append('email_verified')
        
        # Add DraftEmail at the end
        columns.append('DraftEmail')
        
        logger.info(f"Creating DataFrame with {len(final_leads)} leads")
        df = pd.DataFrame(final_leads)
        
        # CRITICAL FIX: Standardize CSV column names for consistency
        column_mapping = {
            # Email verification fields - standardize to PascalCase for CSV
            'email_status': 'Email_Status',
            'email_verified': 'Email_Verified', 
            'email_score': 'Email_Score',
            'email_quality_boost': 'Email_Quality_Boost',
            'mx_valid': 'MX_Valid',
            'smtp_valid': 'SMTP_Valid',
            'email_source': 'Email_Source',
            
            # Review fields standardization  
            'reviews': 'Reviews',
            'review_count': 'ReviewCount',
            
            # Social media standardization
            'social_media_links': 'SocialMediaLinks',
            
            # Other standardizations
            'draft_email': 'DraftEmail',
            'lead_score': 'LeadScore'
        }
        
        # Apply column renaming
        df = df.rename(columns=column_mapping)
        
        # Log DataFrame info
        logger.info(f"DataFrame shape: {df.shape}")
        logger.info(f"Standardized CSV columns: {list(df.columns)}")
        if not df.empty:
            logger.info(f"First row data: {df.iloc[0].to_dict()}")
        
        # Ensure all columns exist
        for col in columns:
            if col not in df.columns:
                df[col] = 'NA'
        
        # Reorder columns - only select columns that exist
        available_columns = [col for col in columns if col in df.columns]
        df = df[available_columns]
        
        # Save to CSV
        logger.info(f"Saving CSV to {filepath} with {len(df)} rows")
        df.to_csv(filepath, index=False)
        job.result_file = filepath
        
        # Step 6: Skip Google Drive - just save locally
        job.status = "finalizing"
        job.progress = 90
        job.message = "Finalizing CSV file..."
        
        # No more Google Drive BS - just save locally
        job.share_link = None
        job.message = f"CSV ready for download: {filename}"
        
        # Step 7: Add to Instantly campaign if enabled
        if job.add_to_instantly and job.instantly_campaign and final_leads:
            try:
                job.status = "adding_to_instantly"
                job.progress = 95
                job.message = "Adding leads to Instantly campaign..."
                
                api_key = os.getenv('INSTANTLY_API_KEY')
                if api_key:
                    # Filter for verified emails only
                    leads_for_instantly = [
                        lead for lead in final_leads
                        if lead.get('Email') and lead.get('Email') not in ('', 'NA') 
                        and (str(lead.get('email_status','')).lower() == 'valid' or str(lead.get('Email_Status','')).lower() == 'valid' or str(lead.get('Email_Verified','')).lower() in ('true','1','yes'))
                    ]
                    
                    if leads_for_instantly:
                        print(f"\n{'#'*60}")
                        print(f"FLASK: Preparing to send {len(leads_for_instantly)} leads to Instantly")
                        print(f"FLASK: Campaign ID: {job.instantly_campaign}")
                        print(f"FLASK: API Key present: {bool(api_key)}")
                        
                        instantly = InstantlyIntegration(api_key)
                        instantly_leads = convert_r27_leads_to_instantly(leads_for_instantly)
                        
                        print(f"FLASK: Converted to {len(instantly_leads)} Instantly lead objects")
                        
                        # Use working add_leads_to_campaign method (bulk import deprecated)
                        result = instantly.add_leads_to_campaign(job.instantly_campaign, instantly_leads)
                        
                        print(f"FLASK: Result from Instantly: {result}")
                        
                        # Handle add_leads_to_campaign result format
                        if result.get('success') and result.get('added', 0) > 0:
                            added_count = result.get('added', 0)
                            failed_count = result.get('failed', 0)
                            
                            logger.info(f"Added {added_count} leads to Instantly campaign - {failed_count} failed")
                            
                            if failed_count == 0:
                                job.message = f"✅ Generated {len(final_leads)} leads and successfully added ALL {added_count} to Instantly!"
                            else:
                                job.message = f"⚠️ Generated {len(final_leads)} leads - {added_count} added to Instantly, {failed_count} failed"
                        else:
                            logger.warning(f"Instantly lead import completely failed: {result}")
                            job.message = f"✅ Generated {len(final_leads)} leads but ❌ Instantly lead import failed completely"
                        
                        print(f"{'#'*60}\n")
                    else:
                        print("FLASK: No verified leads to send to Instantly")
                        logger.warning("No verified leads to add to Instantly campaign")
                        job.message = f"Successfully generated {len(final_leads)} leads (no verified emails for Instantly)"
                else:
                    logger.warning("Instantly API key not configured")
                    job.message = f"Successfully generated {len(final_leads)} leads (Instantly API key missing)"
                    
            except Exception as e:
                # Handle unicode encoding errors in exception message
                try:
                    error_msg = str(e)
                except:
                    error_msg = "Response encoding error (but check Instantly - leads may have been added successfully)"
                
                logger.error(f"Failed to add leads to Instantly: {error_msg}")
                job.message = f"Successfully generated {len(final_leads)} leads (Instantly status: {error_msg})"
        
        # Complete
        job.status = "completed"
        job.progress = 100
        if not hasattr(job, 'message') or 'Instantly' not in job.message:
            job.message = f"Successfully generated {len(final_leads)} leads!"
        
        # Save completed job to persistent storage
        save_completed_job(job)
        
        # Track in search history
        try:
            search_history.add_search(
                query=job.query,
                limit_leads=job.limit,
                verify_emails=job.verify_emails,
                generate_emails=job.generate_emails,
                export_verified_only=job.export_verified_only,
                advanced_scraping=job.advanced_scraping,
                results_count=len(final_leads)
            )
        except Exception as e:
            logger.warning(f"Failed to track search history: {e}")
        
    except Exception as e:
        logger.error(f"Job failed: {e}", exc_info=True)
        job.status = "error"
        job.error = str(e)
        job.message = "Job failed"
        # Persist errored job so it shows up in completed list
        save_completed_job(job)

@app.route('/')
def index():
    """Render the main page with cache-busting headers"""
    from flask import make_response
    import time
    
    # Create response with cache-busting
    response = make_response(render_template('index.html', cache_buster=int(time.time())))
    
    # Add headers to prevent caching
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response

@app.route('/test')
def test():
    """Test route to verify HTML rendering"""
    return render_template('test.html')

@app.route('/api/debug-simple')
def debug_simple():
    """Simple debug endpoint to test functionality"""
    return {
        "debug_logs_count": len(debug_logs) if 'debug_logs' in globals() else 0,
        "recent_logs": list(debug_logs)[-5:] if 'debug_logs' in globals() and debug_logs else []
    }

@app.route('/api/debug-test')
def debug_test():
    """Simple debug test endpoint"""
    return {"status": "working", "debug_logs_count": len(debug_logs)}

@app.route('/api/debug-logs')
def debug_logs_stream():
    """Server-Sent Events stream for real-time debug logs"""
    def generate():
        subscriber_queue = queue.Queue(maxsize=100)
        log_subscribers.append(subscriber_queue)
        
        try:
            # Send recent logs first
            for log_entry in list(debug_logs):
                yield f"data: {json.dumps(log_entry)}\n\n"
            
            # Then stream new logs
            while True:
                try:
                    log_entry = subscriber_queue.get(timeout=30)
                    yield f"data: {json.dumps(log_entry)}\n\n"
                except queue.Empty:
                    # Send keepalive
                    yield f"data: {json.dumps({'keepalive': True})}\n\n"
        finally:
            if subscriber_queue in log_subscribers:
                log_subscribers.remove(subscriber_queue)
    
    return Response(generate(), mimetype='text/plain', headers={
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Content-Type': 'text/event-stream',
    })

@app.route('/api/generate', methods=['POST'])
def generate_leads():
    """Start a new lead generation job"""
    data = request.json
    query = data.get('query', '')
    queries = data.get('queries', [query] if query else [])  # Handle multiple queries
    limit = int(data.get('limit', 25))
    industry = data.get('industry', 'default')
    verify_emails = data.get('verify_emails', False)
    generate_emails = data.get('generate_emails', True) # Default to True
    export_verified_only = data.get('export_verified_only', False)
    advanced_scraping = data.get('advanced_scraping', False)
    providers = data.get('providers', ['google_maps'])  # New provider selection
    add_to_instantly = data.get('add_to_instantly', False)
    instantly_campaign = data.get('instantly_campaign', '')
    
    # Debug logging
    logger.info(f"DEBUG: Request data: {data}")
    logger.info(f"DEBUG: generate_emails from request: {generate_emails}")
    logger.info(f"DEBUG: advanced_scraping from request: {advanced_scraping}")
    
    if not query:
        return jsonify({'error': 'Query is required'}), 400
    
    if not providers:
        return jsonify({'error': 'At least one data source must be selected'}), 400
    
    # If multi-provider search is requested, use the multi-provider flow
    if len(providers) > 1 or (len(providers) == 1 and providers[0] != 'google_maps'):
        return handle_multi_provider_generate(data)
    
    # Create job for Google Maps only
    job_id = f"job_{int(time.time())}"
    job = LeadGenerationJob(job_id, query, limit, industry, verify_emails, generate_emails, export_verified_only, advanced_scraping, queries, add_to_instantly, instantly_campaign)
    jobs[job_id] = job
    
    # Start processing in background
    thread = threading.Thread(target=process_leads, args=(job,))
    thread.start()
    
    return jsonify({'job_id': job_id})

def handle_multi_provider_generate(data):
    """Handle multi-provider lead generation"""
    try:
        query = data.get('query', '')
        queries = data.get('queries', [query] if query else [])
        limit = int(data.get('limit', 25))
        verify_emails = data.get('verify_emails', False)
        generate_emails = data.get('generate_emails', True)
        export_verified_only = data.get('export_verified_only', False)
        providers = data.get('providers', ['google_maps'])
        add_to_instantly = data.get('add_to_instantly', False)
        instantly_campaign = data.get('instantly_campaign', '')
        
        logger.info(f"Multi-provider search: {providers} for query: {query}")
        
        job_id = f"multi_job_{int(time.time())}"
        
        # Create a modified job for multi-provider
        job = LeadGenerationJob(
            job_id, 
            query, 
            limit, 
            'default', 
            verify_emails, 
            generate_emails,
            export_verified_only,
            False,  # advanced_scraping not needed for multi-provider
            queries,
            add_to_instantly,
            instantly_campaign
        )
        jobs[job_id] = job
        
        # Process multi-provider search
        thread = threading.Thread(target=process_multi_provider_leads, args=(job, providers))
        thread.start()
        
        return jsonify({'job_id': job_id})
        
    except Exception as e:
        logger.error(f"Multi-provider search failed: {e}")
        return jsonify({'error': str(e)}), 500

def process_multi_provider_leads(job, providers):
    """Process leads using multiple providers"""
    try:
        job.status = "fetching"
        job.progress = 10
        job.message = f"Searching across {len(providers)} data sources..."
        
        all_results = []
        
        for query in job.queries:
            logger.info(f"Searching '{query}' across providers: {providers}")
            
            # Parse query to extract business type and location
            if ' in ' in query:
                business_type, location = query.split(' in ', 1)
            else:
                business_type = query
                location = None
            
            # Google Maps
            if 'google_maps' in providers and os.getenv('GOOGLE_API_KEY'):
                try:
                    job.message = "Searching Google Maps..."
                    google_provider = get_provider('auto')
                    google_results = google_provider.fetch_places(query, job.limit)
                    logger.info(f"Google Maps found {len(google_results)} results")
                    
                    for result in google_results:
                        normalized = {
                            'Name': result.get('name', ''),
                            'Address': result.get('address', ''),
                            'Phone': result.get('phone', 'Not available'),
                            'Website': result.get('website', 'Not available'),
                            'SearchKeyword': business_type,
                            'Location': location or 'No location specified',
                            'data_source': 'Google Maps'
                        }
                        all_results.append(normalized)
                except Exception as e:
                    logger.error(f"Google Maps provider error: {e}")
            
            # OpenStreetMap
            if 'openstreetmap' in providers:
                try:
                    job.message = "Searching OpenStreetMap..."
                    osm_provider = OpenStreetMapProvider()
                    osm_results = osm_provider.search_businesses(business_type, location, limit=job.limit)
                    logger.info(f"OpenStreetMap found {len(osm_results)} results")
                    
                    for result in osm_results:
                        normalized = {
                            'Name': result.get('name', ''),
                            'Address': result.get('address', ''),
                            'Phone': result.get('phone', 'Not available'),
                            'Website': result.get('website', 'Not available'),
                            'SearchKeyword': business_type,
                            'Location': location or 'No location specified',
                            'data_source': 'OpenStreetMap'
                        }
                        all_results.append(normalized)
                except Exception as e:
                    logger.error(f"OpenStreetMap provider error: {e}")
            
            # Yellow Pages
            if 'yellowpages' in providers:
                try:
                    job.message = "Searching Yellow Pages..."
                    yp_provider = YellowPagesAPIProvider()
                    yp_results = yp_provider.search_businesses(business_type, location, limit=job.limit)
                    logger.info(f"Yellow Pages found {len(yp_results)} results")
                    
                    for result in yp_results:
                        normalized = {
                            'Name': result.get('name', ''),
                            'Address': result.get('address', ''),
                            'Phone': result.get('phone', 'Not available'),
                            'Website': result.get('website', 'Not available'),
                            'SearchKeyword': business_type,
                            'Location': location or 'No location specified',
                            'data_source': 'Yellow Pages'
                        }
                        all_results.append(normalized)
                except Exception as e:
                    logger.error(f"Yellow Pages provider error: {e}")
        
        job.progress = 50
        job.message = f"Found {len(all_results)} leads from {len(providers)} sources..."
        
        # Deduplicate results
        seen = set()
        unique_results = []
        for result in all_results:
            name = result.get('Name', '').lower().strip()
            address = result.get('Address', '').lower().strip()
            key = (name, address[:50] if address else '')
            
            if key not in seen and name and name not in ['unknown business', '']:
                seen.add(key)
                unique_results.append(result)
        
        job.progress = 70
        job.message = f"Deduplicated to {len(unique_results)} unique leads..."
        
        # Save results to CSV
        job.progress = 90
        job.message = "Preparing CSV file..."
        
        if unique_results:
            df = pd.DataFrame(unique_results)
            timestamp = int(time.time())
            filename = f'leads_multi_provider_{timestamp}.csv'
            filepath = os.path.join('output', filename)
            
            os.makedirs('output', exist_ok=True)
            df.to_csv(filepath, index=False)
            
            job.result_file = filepath
            job.leads_data = unique_results
            job.total_leads = len(unique_results)
            job.status = "completed"
            job.progress = 100
            job.message = f"✅ Found {len(unique_results)} unique leads from {len(providers)} providers!"
            
            # Persist completed multi-provider job
            save_completed_job(job)
            
            logger.info(f"Multi-provider search completed: {len(unique_results)} leads saved to {filename}")
        else:
            job.status = "completed"
            job.progress = 100
            job.message = "No leads found from selected providers"
            job.total_leads = 0
            logger.info("Multi-provider search completed with no results")
            
    except Exception as e:
        job.status = "error"
        job.error = str(e)
        job.message = f"Multi-provider search failed: {str(e)}"
        logger.error(f"Multi-provider search error: {e}")

@app.route('/api/status/<job_id>')
def get_status(job_id):
    """Get job status with detailed error information"""
    # First check active jobs in memory
    if job_id in jobs:
        job_data = jobs[job_id].to_dict()
        logger.debug(f"Returning status for job {job_id}: {job_data['status']}")
        return jsonify(job_data)
    
    # Check completed jobs from persistent storage
    completed_jobs = load_completed_jobs()
    if job_id in completed_jobs:
        job_record = completed_jobs[job_id]
        logger.debug(f"Returning completed job status for {job_id}: {job_record['status']}")
        return jsonify(job_record)
    
    logger.warning(f"Job {job_id} not found in active or completed jobs")
    return jsonify({'error': 'Job not found'}), 404

@app.route('/api/cancel/<job_id>', methods=['POST'])
def cancel_job(job_id):
    """Cancel a running job"""
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    job = jobs[job_id]
    
    # Mark job as cancelled
    job.cancelled = True
    job.status = 'cancelled'
    job.message = 'Job cancelled by user'
    
    logger.info(f"Job {job_id} cancelled by user")
    
    return jsonify({
        'success': True,
        'message': 'Job cancelled successfully'
    })

@app.route('/api/download/<job_id>')
def download_csv(job_id):
    """Download the CSV file"""
    # First check if job exists in memory
    if job_id in jobs:
        job = jobs[job_id]
        if hasattr(job, 'result_file') and job.result_file and os.path.exists(job.result_file):
            return send_file(job.result_file, as_attachment=True, mimetype='text/csv')
    
    # Check completed jobs from persistent storage
    completed_jobs = load_completed_jobs()
    if job_id in completed_jobs:
        job_record = completed_jobs[job_id]
        result_file = job_record.get('result_file')
        if result_file and os.path.exists(result_file):
            return send_file(result_file, as_attachment=True, mimetype='text/csv')
    
    # Fallback: Look for the most recent file that matches this job pattern
    output_dir = 'output'
    if os.path.exists(output_dir):
        # Get all CSV files, sorted by modification time (newest first)
        csv_files = []
        for filename in os.listdir(output_dir):
            if filename.endswith('.csv'):
                filepath = os.path.join(output_dir, filename)
                if os.path.isfile(filepath):
                    csv_files.append((filepath, os.path.getmtime(filepath)))
        
        # Sort by modification time, newest first
        csv_files.sort(key=lambda x: x[1], reverse=True)
        
        # Return the most recent CSV file
        if csv_files:
            most_recent_file = csv_files[0][0]
            return send_file(most_recent_file, as_attachment=True, mimetype='text/csv')
    
    return jsonify({'error': 'File not found'}), 404

@app.route('/api/active-jobs', methods=['GET'])
def get_active_jobs():
    """Get currently active/running jobs"""
    active_jobs = []

    # Regular lead generation jobs
    for job_id, job in jobs.items():
        if hasattr(job, 'status') and job.status not in ['completed', 'failed', 'cancelled', 'error']:
            active_jobs.append({
                'job_id': job_id,
                'query': getattr(job, 'query', 'Unknown'),
                'status': getattr(job, 'status', 'unknown'),
                'progress': getattr(job, 'progress', 0),
                'message': getattr(job, 'message', ''),
                'type': 'lead_generation'
            })

    # Apollo jobs
    for job_id, job in apollo_jobs.items():
        if hasattr(job, 'status') and job.status not in ['completed', 'failed', 'cancelled', 'error']:
            active_jobs.append({
                'job_id': job_id,
                'query': 'Apollo Processing',
                'status': getattr(job, 'status', 'unknown'),
                'progress': getattr(job, 'progress', 0),
                'message': getattr(job, 'message', ''),
                'type': 'apollo'
            })

    return jsonify({
        'active_jobs': active_jobs,
        'total_active': len(active_jobs),
        'total_jobs_tracked': len(jobs),
        'total_apollo_tracked': len(apollo_jobs)
    })

@app.route('/api/completed-jobs')
def get_completed_jobs():
    """Get list of completed jobs"""
    # Check if active jobs are requested
    if request.args.get('active') == 'true':
        active_jobs = []
        
        # Check regular jobs
        for job_id, job in jobs.items():
            if hasattr(job, 'status') and job.status not in ['completed', 'failed', 'cancelled']:
                active_jobs.append({
                    'job_id': job_id,
                    'query': getattr(job, 'query', 'Unknown'),
                    'status': getattr(job, 'status', 'unknown'),
                    'progress': getattr(job, 'progress', 0),
                    'message': getattr(job, 'message', ''),
                    'type': 'lead_generation'
                })
        
        # Check apollo jobs
        for job_id, job in apollo_jobs.items():
            if hasattr(job, 'status') and job.status not in ['completed', 'failed', 'cancelled']:
                active_jobs.append({
                    'job_id': job_id,
                    'query': 'Apollo Processing',
                    'status': getattr(job, 'status', 'unknown'),
                    'progress': getattr(job, 'progress', 0),
                    'message': getattr(job, 'message', ''),
                    'type': 'apollo'
                })
        
        return jsonify({
            'active_jobs': active_jobs,
            'total_active': len(active_jobs),
            'total_jobs_tracked': len(jobs),
            'total_apollo_tracked': len(apollo_jobs)
        })
    
    # Check if debug mode is requested
    debug_mode = request.args.get('debug') == 'true'
    
    if debug_mode:
        return {
            "debug_info": {
                "debug_logs_count": len(debug_logs) if 'debug_logs' in globals() else 0,
                "recent_logs": list(debug_logs)[-10:] if 'debug_logs' in globals() and debug_logs else [],
                "log_subscribers": len(log_subscribers) if 'log_subscribers' in globals() else 0
            }
        }
    
    completed_jobs = load_completed_jobs()
    # Convert to list and sort by completion time (newest first)
    jobs_list = list(completed_jobs.values())
    jobs_list.sort(key=lambda x: x.get('completed_at', ''), reverse=True)
    return jsonify(jobs_list)

@app.route('/api/debug-info')
def get_debug_info():
    """Get debug information and recent logs"""
    import logging
    
    # Get recent logs from the file
    recent_logs = []
    try:
        with open('logs/flask_app.log', 'r') as f:
            lines = f.readlines()[-50:]  # Get last 50 lines
            for line in lines:
                recent_logs.append(line.strip())
    except Exception as e:
        recent_logs = [f"Error reading log file: {str(e)}"]
    
    return {
        "status": "working", 
        "recent_logs": recent_logs,
        "current_jobs": len(jobs),
        "debug_logs_available": 'debug_logs' in globals()
    }

@app.route('/api/expand-keywords', methods=['POST'])
def expand_keywords():
    """Expand a keyword into related search terms using LLM"""
    try:
        data = request.json
        base_keyword = data.get('keyword', '').strip()
        location = data.get('location', '').strip()
        
        if not base_keyword:
            return jsonify({'error': 'Keyword is required'}), 400
        
        # Initialize keyword expander
        expander = KeywordExpander()
        
        # Generate keyword variants
        variants = expander.expand_keywords(base_keyword, location, max_variants=20)
        
        # Combine with location if provided
        if location:
            variants = expander.combine_with_location(variants, location)
        
        logger.info(f"Generated {len(variants)} keyword variants for '{base_keyword}'")
        
        return jsonify({
            'success': True,
            'base_keyword': base_keyword,
            'location': location,
            'variants': variants,
            'count': len(variants)
        })
        
    except Exception as e:
        logger.error(f"Keyword expansion failed: {e}", exc_info=True)
        return jsonify({'error': f'Keyword expansion failed: {str(e)}'}), 500

class ApolloJob:
    def __init__(self, job_id, filename, max_leads=100, service_focus='general_automation'):
        self.job_id = job_id
        self.filename = filename
        self.max_leads = max_leads
        self.service_focus = service_focus
        self.status = "processing"
        self.progress = 0
        self.total_leads = 0
        self.processed_leads = 0
        self.message = "Starting..."
        self.result_file = None
        self.error = None
        self.cancelled = False
        
    def to_dict(self):
        return {
            'job_id': self.job_id,
            'status': self.status,
            'progress': self.progress,
            'total_leads': self.total_leads,
            'processed_leads': self.processed_leads,
            'message': self.message,
            'result_file': self.result_file,
            'error': self.error
        }

# Store Apollo jobs
apollo_jobs = {}

def process_apollo_background(job):
    """Background task to process Apollo CSV"""
    temp_path = job.filename
    
    try:
        # Read CSV to get total count
        df = pd.read_csv(temp_path)
        total_in_file = len(df)
        
        # Limit processing
        job.total_leads = min(total_in_file, job.max_leads)
        job.message = f"Processing {job.total_leads} of {total_in_file} leads..."
        
        if total_in_file > job.max_leads:
            df = df.head(job.max_leads)
        
        # Process with Apollo processor
        service_focus = job.service_focus if hasattr(job, 'service_focus') else 'general_automation'
        processor = ApolloLeadProcessor(service_focus=service_focus)
        
        # Generate output filename
        output_filename = f"apollo_personalized_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        output_path = os.path.join('output', output_filename)
        
        # Process each lead with progress updates
        results = []
        for idx, lead in df.iterrows():
            if job.cancelled:
                job.status = "cancelled"
                job.message = "Processing cancelled by user"
                break
                
            try:
                # Process single lead
                analysis = processor.analyze_lead(lead)
                email = processor.smart_personalizer.generate_personalized_email(lead.to_dict())
                
                result = {
                    'first_name': analysis['first_name'],
                    'title': analysis['title'],
                    'company': analysis['company'],
                    'email': analysis['email'],
                    'personalized_email': email
                }
                results.append(result)
                
                # Update progress
                job.processed_leads = idx + 1
                job.progress = int((job.processed_leads / job.total_leads) * 100)
                job.message = f"Processed {job.processed_leads}/{job.total_leads} leads"
                
            except Exception as e:
                logger.error(f"Error processing lead {idx}: {e}")
                continue
        
        if not job.cancelled:
            # Save results
            results_df = pd.DataFrame(results)
            results_df.to_csv(output_path, index=False)
            
            job.result_file = output_filename
            job.status = "completed"
            job.progress = 100
            job.message = f"Successfully processed {len(results)} leads!"
        
    except Exception as e:
        logger.error(f"Apollo job failed: {e}", exc_info=True)
        job.status = "error"
        job.error = str(e)
        job.message = "Processing failed"
    
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.route('/api/process-apollo', methods=['POST'])
def process_apollo():
    """Start Apollo CSV processing job"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '' or not file.filename.endswith('.csv'):
        return jsonify({'error': 'Please upload a CSV file'}), 400
    
    # Save uploaded file temporarily
    temp_path = os.path.join('output', f'temp_apollo_{int(time.time())}.csv')
    file.save(temp_path)
    
    # Create job
    job_id = f"apollo_{int(time.time())}"
    max_leads = int(request.form.get('max_leads', 100))
    service_focus = request.form.get('service_focus', 'general_automation')
    job = ApolloJob(job_id, temp_path, max_leads, service_focus)
    apollo_jobs[job_id] = job
    
    # Start processing in background
    thread = threading.Thread(target=process_apollo_background, args=(job,))
    thread.start()
    
    return jsonify({'job_id': job_id})

@app.route('/api/apollo-status/<job_id>')
def apollo_status(job_id):
    """Get Apollo job status"""
    if job_id not in apollo_jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify(apollo_jobs[job_id].to_dict())

@app.route('/api/apollo-cancel/<job_id>', methods=['POST'])
def apollo_cancel(job_id):
    """Cancel Apollo job"""
    if job_id not in apollo_jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    apollo_jobs[job_id].cancelled = True
    return jsonify({'success': True, 'message': 'Job cancelled'})

@app.route('/api/download-apollo/<filename>')
def download_apollo(filename):
    """Download processed Apollo CSV"""
    filepath = os.path.join('output', filename)
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    
    return send_file(filepath, as_attachment=True, mimetype='text/csv', download_name=filename)

# Search History & Favorites API
@app.route('/api/search-history')
def get_search_history():
    """Get recent search history"""
    history = search_history.get_history(limit=50)
    return jsonify(history)

@app.route('/api/search-suggestions')
def get_search_suggestions():
    """Get search suggestions based on prefix"""
    prefix = request.args.get('q', '')
    if len(prefix) < 2:
        return jsonify([])
    suggestions = search_history.get_suggestions(prefix, limit=10)
    return jsonify(suggestions)

@app.route('/api/favorites', methods=['GET', 'POST'])
def handle_favorites():
    """Get or add favorite searches"""
    if request.method == 'GET':
        favorites = search_history.get_favorites()
        return jsonify(favorites)
    else:
        data = request.json
        favorite_id = search_history.add_favorite(
            name=data.get('name'),
            query=data.get('query'),
            limit_leads=data.get('limit_leads', 25),
            verify_emails=data.get('verify_emails', False),
            generate_emails=data.get('generate_emails', False),
            export_verified_only=data.get('export_verified_only', False),
            advanced_scraping=data.get('advanced_scraping', False)
        )
        return jsonify({'id': favorite_id, 'success': True})

@app.route('/api/favorites/<int:favorite_id>', methods=['DELETE'])
def delete_favorite(favorite_id):
    """Delete a favorite search"""
    search_history.delete_favorite(favorite_id)
    return jsonify({'success': True})

@app.route('/api/popular-searches')
def get_popular_searches():
    """Get most popular searches"""
    popular = search_history.get_popular_searches(limit=10)
    return jsonify(popular)

# CSV Template Download
@app.route('/api/csv-template')
def download_csv_template():
    """Download CSV template for bulk upload"""
    template_data = {
        'name': ['Search 1', 'Search 2', 'Search 3'],
        'query': ['dentists in New York', 'lawyers in Los Angeles', 'restaurants in Chicago'],
        'limit_leads': [100, 50, 25],
        'verify_emails': [True, True, False],
        'interval_minutes': [15, 30, 60]
    }
    df = pd.DataFrame(template_data)
    
    # Create temp file
    temp_file = 'temp/search_template.csv'
    os.makedirs('temp', exist_ok=True)
    df.to_csv(temp_file, index=False)
    
    return send_file(temp_file, as_attachment=True, download_name='search_template.csv')

# Export in different formats
@app.route('/api/export/<job_id>/<format>')
def export_format(job_id, format):
    """Export job results in different formats (json, xml, xlsx)"""
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    job = jobs[job_id]
    if not job.leads_data:
        return jsonify({'error': 'No data to export'}), 404
    
    # Create temp directory
    os.makedirs('temp', exist_ok=True)
    
    if format == 'json':
        temp_file = f'temp/{job_id}.json'
        with open(temp_file, 'w') as f:
            json.dump(job.leads_data, f, indent=2)
        return send_file(temp_file, as_attachment=True, download_name=f'{job.query}.json')
    
    elif format == 'xml':
        temp_file = f'temp/{job_id}.xml'
        df = pd.DataFrame(job.leads_data)
        df.to_xml(temp_file, root_name='leads', row_name='lead')
        return send_file(temp_file, as_attachment=True, download_name=f'{job.query}.xml')
    
    elif format == 'xlsx':
        temp_file = f'temp/{job_id}.xlsx'
        df = pd.DataFrame(job.leads_data)
        df.to_excel(temp_file, index=False, sheet_name='Leads')
        return send_file(temp_file, as_attachment=True, download_name=f'{job.query}.xlsx')
    
    else:
        return jsonify({'error': 'Invalid format. Use json, xml, or xlsx'}), 400

# Bulk operations for queue
@app.route('/api/queue/bulk-delete', methods=['POST'])
def bulk_delete_queue():
    """Delete multiple queue items"""
    data = request.json
    queue_ids = data.get('queue_ids', [])
    
    for queue_id in queue_ids:
        scheduler.cancel_queue_item(queue_id)
    
    return jsonify({'success': True, 'deleted': len(queue_ids)})

@app.route('/api/queue/clear', methods=['POST'])
def clear_queue():
    """Clear entire queue"""
    count = scheduler.clear_queue()
    return jsonify({'success': True, 'cleared': count})

# Provider status
@app.route('/api/providers/status')
def get_providers_status():
    """Get status of all available providers"""
    from src.providers import get_available_providers
    
    providers = get_available_providers()
    status = []
    
    for provider_name in providers:
        try:
            provider = get_provider(provider_name)
            # Test with a simple query
            test_results = provider.fetch_places("test", 1)
            status.append({
                'name': provider_name,
                'status': 'active',
                'available': True,
                'test_success': len(test_results) > 0 if test_results else False
            })
        except Exception as e:
            status.append({
                'name': provider_name,
                'status': 'error',
                'available': False,
                'error': str(e)
            })
    
    return jsonify(status)

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    # Test provider
    provider = get_provider('auto')
    provider_name = provider.__class__.__name__
    
    # Test fetching
    test_results = []
    try:
        test_results = provider.fetch_places("coffee shop Austin", 1)
    except:
        pass
    
    return jsonify({
        'status': 'healthy',
        'provider': provider_name,
        'google_api_key': bool(os.getenv('GOOGLE_API_KEY')),
        'google_api_key_value': os.getenv('GOOGLE_API_KEY', '')[:10] + '...' if os.getenv('GOOGLE_API_KEY') else 'None',
        'test_fetch_worked': len(test_results) > 0,
        'openai_configured': bool(os.getenv('OPENAI_API_KEY')),
        'available_industries': IndustryConfig.get_industry_display_names()
    })

# Scheduler endpoints
@app.route('/api/schedules', methods=['GET'])
def get_schedules():
    """Get all scheduled searches"""
    schedules = scheduler.get_schedules()
    return jsonify(schedules)

@app.route('/api/schedules', methods=['POST'])
def create_schedule():
    """Create a new scheduled search"""
    data = request.json
    schedule_id = scheduler.add_schedule(
        name=data['name'],
        query=data['query'],
        limit_leads=data.get('limit_leads', 25),
        verify_emails=data.get('verify_emails', False),
        generate_emails=data.get('generate_emails', True),  # New parameter
        interval_hours=data.get('interval_hours', 24),
        integrations=data.get('integrations', [])
    )
    return jsonify({'schedule_id': schedule_id})

@app.route('/api/schedules/<int:schedule_id>', methods=['GET'])
def get_schedule(schedule_id):
    """Get a specific schedule"""
    schedule = scheduler.get_schedule(schedule_id)
    if schedule:
        return jsonify(schedule)
    return jsonify({'error': 'Schedule not found'}), 404

@app.route('/api/schedules/<int:schedule_id>', methods=['PUT'])
def update_schedule(schedule_id):
    """Update a schedule"""
    data = request.json
    success = scheduler.update_schedule(schedule_id, **data)
    return jsonify({'success': success})

@app.route('/api/schedules/<int:schedule_id>', methods=['DELETE'])
def delete_schedule(schedule_id):
    """Delete a schedule"""
    success = scheduler.delete_schedule(schedule_id)
    return jsonify({'success': success})

@app.route('/api/queue', methods=['GET'])
def get_queue():
    """Get the search queue"""
    status = request.args.get('status')
    queue_items = scheduler.get_queue(status)
    return jsonify(queue_items)

@app.route('/api/queue', methods=['POST'])
def add_to_queue():
    """Add a search to the queue"""
    data = request.json
    queue_id = scheduler.add_to_queue(
        query=data['query'],
        limit_leads=data.get('limit_leads', 25),
        verify_emails=data.get('verify_emails', False),
        priority=data.get('priority', 5)
    )
    return jsonify({'id': queue_id, 'success': True})

@app.route('/api/history', methods=['GET'])
def get_history():
    """Get search history"""
    schedule_id = request.args.get('schedule_id', type=int)
    limit = request.args.get('limit', 100, type=int)
    history = scheduler.get_history(schedule_id, limit)
    return jsonify(history)

@app.route('/api/schedules/bulk-upload', methods=['POST'])
def bulk_upload_schedules():
    """Upload multiple schedules from CSV"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '' or not file.filename.endswith('.csv'):
        return jsonify({'error': 'Please upload a CSV file'}), 400
    
    try:
        # Read CSV
        df = pd.read_csv(file)
        
        # Validate required columns
        required_cols = ['name', 'query', 'limit_leads']
        if not all(col in df.columns for col in required_cols):
            return jsonify({'error': f'CSV must contain columns: {", ".join(required_cols)}'}), 400
        
        # Process each row with staggered scheduling
        added_schedules = []
        errors = []
        
        # Default interval between searches (in minutes)
        default_interval_minutes = 15
        base_time = datetime.now()
        
        for idx, row in df.iterrows():
            try:
                # Get values with defaults
                name = str(row['name'])
                query = str(row['query'])
                
                # Handle "max" as limit_leads value
                limit_str = str(row.get('limit_leads', '25')).lower()
                if limit_str == 'max':
                    limit_leads = 1000  # Maximum allowed
                else:
                    limit_leads = int(limit_str)
                    
                verify_emails = str(row.get('verify_emails', 'false')).lower() == 'true'
                
                # Get interval from CSV or use default
                interval_minutes = int(row.get('interval_minutes', default_interval_minutes))
                
                # Calculate scheduled time for this search
                scheduled_time = base_time + timedelta(minutes=interval_minutes * idx)
                
                # Check if this should be a recurring schedule or one-time queue item
                interval_hours = int(row.get('interval_hours', 0))
                
                if interval_hours > 0:
                    schedule_id = scheduler.add_schedule(
                        name=name,
                        query=query,
                        limit_leads=limit_leads,
                        verify_emails=verify_emails,
                        interval_hours=interval_hours
                    )
                    added_schedules.append({
                        'row': idx + 1,
                        'name': name,
                        'type': 'schedule',
                        'id': schedule_id
                    })
                else:
                    # Add directly to queue for one-time execution with scheduled time
                    queue_id = scheduler.add_to_queue(
                        query=query,
                        limit_leads=limit_leads,
                        verify_emails=verify_emails,
                        priority=1,  # All same priority = process in order
                        scheduled_time=scheduled_time
                    )
                    added_schedules.append({
                        'row': idx + 1,
                        'name': name,
                        'type': 'queue',
                        'id': queue_id,
                        'scheduled_time': scheduled_time.strftime('%Y-%m-%d %H:%M:%S')
                    })
                    
            except Exception as e:
                errors.append({
                    'row': idx + 1,
                    'error': str(e)
                })
        
        return jsonify({
            'success': True,
            'added': added_schedules,
            'errors': errors,
            'total_processed': len(df),
            'total_added': len(added_schedules),
            'total_errors': len(errors)
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to process CSV: {str(e)}'}), 400

@app.route('/api/schedules/template')
def download_schedule_template():
    """Download the CSV template for bulk scheduling"""
    return send_file('schedule_template.csv', 
                    as_attachment=True, 
                    mimetype='text/csv',
                    download_name='schedule_template.csv')

# Enhanced Provider and Enrichment Endpoints

@app.route('/api/providers/available', methods=['GET'])
def get_provider_status():
    """Get list of available data providers"""
    providers = {
        'google_maps': {
            'name': 'Google Maps Places API',
            'configured': bool(os.getenv('GOOGLE_API_KEY')),
            'description': 'Primary business directory search',
            'cost': 'Paid API'
        },
        'openstreetmap': {
            'name': 'OpenStreetMap Overpass API',
            'configured': True,  # Always available
            'description': 'Free open-source business directory',
            'cost': 'Completely Free'
        },
        'yellowpages': {
            'name': 'Yellow Pages API',
            'configured': True,  # Hosted API, no key required
            'description': 'US business directory via hosted API',
            'cost': 'Free'
        }
    }
    return jsonify(providers)


@app.route('/api/enrich-leads', methods=['POST'])
def enrich_leads():
    """Enrich existing leads with additional data"""
    try:
        data = request.json
        leads = data.get('leads', [])
        
        if not leads:
            return jsonify({'error': 'No leads provided'}), 400
            
        enrichment = LeadEnricher()
        enriched_leads = []
        
        for lead in leads:
            enriched = enrichment.enrich_lead(lead)
            enriched_leads.append(enriched)
            
        return jsonify({
            'success': True,
            'enriched_leads': enriched_leads,
            'total_processed': len(leads)
        })
        
    except Exception as e:
        logger.error(f"Lead enrichment failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/instantly/campaigns', methods=['GET'])
def get_instantly_campaigns():
    """Get Instantly campaigns"""
    try:
        api_key = os.getenv('INSTANTLY_API_KEY')
        if not api_key:
            return jsonify({'error': 'Instantly API key not configured'}), 400
            
        instantly = InstantlyIntegration(api_key)
        campaigns = instantly.get_campaigns()
        
        return jsonify(campaigns)
        
    except Exception as e:
        logger.error(f"Failed to get Instantly campaigns: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/instantly/create-campaign', methods=['POST'])
def create_instantly_campaign():
    """Create new Instantly campaign from leads"""
    try:
        data = request.json
        leads = data.get('leads', [])
        campaign_name = data.get('campaign_name', f"Campaign {datetime.now().strftime('%Y%m%d_%H%M%S')}")
        template_type = data.get('template_type', 'generic')
        
        api_key = os.getenv('INSTANTLY_API_KEY')
        if not api_key:
            return jsonify({'error': 'Instantly API key not configured'}), 400
            
        if not leads:
            return jsonify({'error': 'No leads provided'}), 400
            
        instantly = InstantlyIntegration(api_key)
        result = create_campaign_from_r27_leads(
            instantly, leads, campaign_name, template_type
        )
        
        return jsonify({
            'success': True,
            'campaign_created': result
        })
        
    except Exception as e:
        logger.error(f"Failed to create Instantly campaign: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/instantly/configure', methods=['POST'])
def configure_instantly_account():
    """Save Instantly API key and test connection"""
    try:
        data = request.json
        api_key = data.get('api_key', '').strip()
        
        if not api_key:
            return jsonify({'error': 'API key is required'}), 400
        
        # Test the API key
        instantly = InstantlyIntegration(api_key)
        
        # Try to get account info to validate the key
        try:
            accounts = instantly.get_accounts()
            campaigns = instantly.get_campaigns()
            
            # Save the API key to environment (temporarily for this session)
            # In production, you'd want to save this securely to a database
            os.environ['INSTANTLY_API_KEY'] = api_key
            
            return jsonify({
                'success': True,
                'account_info': f"{len(accounts)} email accounts, {len(campaigns)} campaigns",
                'accounts': len(accounts),
                'campaigns': len(campaigns)
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Invalid API key or connection failed: {str(e)}'
            }), 400
            
    except Exception as e:
        logger.error(f"Failed to configure Instantly account: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/instantly/status', methods=['GET'])
def get_instantly_status():
    """Check current Instantly connection status"""
    try:
        api_key = os.getenv('INSTANTLY_API_KEY')
        if not api_key or api_key == 'your_instantly_api_key_here':
            return jsonify({
                'success': False,
                'error': 'API key not configured'
            })
        
        # Test the connection
        instantly = InstantlyIntegration(api_key)
        try:
            accounts = instantly.get_accounts()
            campaigns = instantly.get_campaigns()
            
            return jsonify({
                'success': True,
                'account_info': f"{len(accounts)} email accounts, {len(campaigns)} campaigns",
                'accounts': len(accounts),
                'campaigns': len(campaigns)
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Connection failed: {str(e)}'
            })
            
    except Exception as e:
        logger.error(f"Failed to check Instantly status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/instantly/templates', methods=['GET'])
def get_campaign_templates():
    """Get available campaign templates"""
    templates = {
        'real_estate': {
            'name': 'Real Estate Outreach',
            'description': 'Template for real estate professionals',
            'emails': 3,
            'follow_up_days': [3, 5, 7]
        },
        'lawyer': {
            'name': 'Legal Services Outreach', 
            'description': 'Template for law firms and legal services',
            'emails': 3,
            'follow_up_days': [4, 6, 8]
        },
        'restaurant': {
            'name': 'Restaurant Outreach',
            'description': 'Template for restaurants and hospitality',
            'emails': 3,
            'follow_up_days': [2, 4, 6]
        },
        'generic': {
            'name': 'Generic B2B Outreach',
            'description': 'General business-to-business template',
            'emails': 3,
            'follow_up_days': [3, 5, 7]
        }
    }
    return jsonify(templates)

@app.route('/api/multi-provider-search', methods=['POST'])
def multi_provider_search():
    """Search across multiple providers simultaneously"""
    try:
        data = request.json
        query = data.get('query', '')
        location = data.get('location', '')
        limit = data.get('limit', 25)
        providers = data.get('providers', ['google_maps'])
        
        if not query:
            return jsonify({'error': 'Query required'}), 400
            
        all_results = []
        provider_results = {}
        
        # Google Maps
        if 'google_maps' in providers and os.getenv('GOOGLE_API_KEY'):
            try:
                google_provider = get_provider('auto')
                google_results = google_provider.fetch_places(f"{query} {location}".strip(), limit)
                # Normalize Google results to match our schema
                normalized_google = []
                for result in google_results:
                    normalized = {
                        'name': result.get('name', ''),
                        'address': result.get('address', ''),
                        'phone': result.get('phone', 'Not available'),
                        'website': result.get('website', 'Not available'),
                        'latitude': result.get('latitude'),
                        'longitude': result.get('longitude'),
                        'business_type': result.get('business_type', 'Business'),
                        'data_source': 'Google Maps'
                    }
                    normalized_google.append(normalized)
                    
                provider_results['google_maps'] = {
                    'count': len(normalized_google),
                    'results': normalized_google
                }
                all_results.extend(normalized_google)
            except Exception as e:
                logger.error(f"Google Maps provider error: {e}")
                provider_results['google_maps'] = {'error': str(e), 'count': 0}
        
        # OpenStreetMap
        if 'openstreetmap' in providers:
            try:
                osm_provider = OpenStreetMapProvider()
                osm_results = osm_provider.search_businesses(query, location, limit)
                provider_results['openstreetmap'] = {
                    'count': len(osm_results),
                    'results': osm_results
                }
                all_results.extend(osm_results)
            except Exception as e:
                logger.error(f"OpenStreetMap provider error: {e}")
                provider_results['openstreetmap'] = {'error': str(e), 'count': 0}
        
        # Yellow Pages
        if 'yellowpages' in providers:
            try:
                yp_provider = YellowPagesAPIProvider()
                yp_results = yp_provider.search_businesses(query, location, limit)
                provider_results['yellowpages'] = {
                    'count': len(yp_results),
                    'results': yp_results
                }
                all_results.extend(yp_results)
            except Exception as e:
                logger.error(f"Yellow Pages provider error: {e}")
                provider_results['yellowpages'] = {'error': str(e), 'count': 0}
        
        # Deduplicate by name and address (phone/email might not be available)
        seen = set()
        unique_results = []
        for result in all_results:
            # Create a more robust deduplication key
            name = result.get('name', '').lower().strip()
            address = result.get('address', '').lower().strip()
            phone = result.get('phone', '').strip()
            
            # Skip if no name
            if not name or name == 'unknown business':
                continue
            
            # Create deduplication key
            key = (name, address[:50] if address else '')  # First 50 chars of address
            
            if key not in seen:
                seen.add(key)
                unique_results.append(result)
        
        return jsonify({
            'success': True,
            'total_results': len(all_results),
            'unique_results': len(unique_results),
            'provider_breakdown': provider_results,
            'results': unique_results
        })
        
    except Exception as e:
        logger.error(f"Multi-provider search failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/test-provider')
def test_provider():
    """Test the provider configuration and API connectivity"""
    try:
        logger.info("Testing provider configuration...")
        # Test the MultiProvider directly
        provider = get_provider('auto')
        
        cascade_status = []
        if hasattr(provider, 'providers'):
            for p_name, p_instance in provider.providers:
                p_status = {'name': p_name, 'api_key_configured': False, 'test_fetch_worked': False, 'error': None}
                
                if hasattr(p_instance, 'api_key'):
                    p_status['api_key_configured'] = bool(p_instance.api_key)
                
                try:
                    test_results = p_instance.fetch_places("coffee shop Austin", 1)
                    p_status['test_fetch_worked'] = len(test_results) > 0
                except Exception as e:
                    p_status['error'] = str(e)
                cascade_status.append(p_status)
            
        # Overall test for the main provider
        overall_test_results = []
        try:
            overall_test_results = provider.fetch_places("coffee shop Austin", 1)
            overall_test_worked = len(overall_test_results) > 0
        except:
            overall_test_worked = False
            
        response_data = {
            'status': 'healthy',
            'main_provider': provider.__class__.__name__,
            'main_provider_test_worked': overall_test_worked,
            'google_api_key': bool(os.getenv('GOOGLE_API_KEY')),
            'google_api_key_value': os.getenv('GOOGLE_API_KEY', '')[:10] + '...' if os.getenv('GOOGLE_API_KEY') else 'None',
            'openai_configured': bool(os.getenv('OPENAI_API_KEY')),
            'available_industries': IndustryConfig.get_industry_display_names(),
            'multi_provider_cascade_status': cascade_status if cascade_status else 'N/A'
        }
        
        logger.info(f"Provider test completed: {response_data}")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Provider test failed: {e}", exc_info=True)
        return jsonify({
            'error': str(e),
            'provider_class': 'Failed to initialize',
            'traceback': str(e)
        }), 500

@app.route('/api/active-jobs-test', methods=['GET'])
def get_active_jobs_test():
    """Get currently active/running jobs - test version"""
    print("DEBUG: Active jobs TEST endpoint hit!")
    return jsonify({
        'active_jobs': [],
        'total_active': 0,
        'debug': 'TEST Route is working!',
        'timestamp': str(datetime.now())
    })

@app.route('/api/instantly/retry-import', methods=['POST'])
def retry_instantly_import():
    data = request.json or {}
    job_id = data.get('job_id')
    campaign_id = data.get('campaign_id')
    if not job_id or not campaign_id:
        return jsonify({'error': 'job_id and campaign_id are required'}), 400

    # Load job data from persistence or memory
    job_info = None
    if job_id in jobs:
        job_info = jobs[job_id].to_dict()
    else:
        completed = load_completed_jobs()
        job_info = completed.get(job_id)

    if not job_info:
        return jsonify({'error': 'Job not found'}), 404

    # Read CSV and convert to Instantly leads
    try:
        result_file = job_info.get('result_file')
        if not result_file or not os.path.exists(result_file):
            return jsonify({'error': 'Result file missing on disk'}), 404

        df = pd.read_csv(result_file)
        leads = df.to_dict(orient='records')

        # Filter to verified emails only if verification columns exist
        filtered = []
        for l in leads:
            email = str(l.get('Email', '')).strip()
            if not email or email == 'NA':
                continue
            status = str(l.get('Email_Status', '')).lower()
            verified_flag = str(l.get('Email_Verified', '')).lower()
            if status == 'valid' or verified_flag in ('true', '1', 'yes'):
                filtered.append(l)
        instantly_leads = convert_r27_leads_to_instantly(filtered)

        api_key = os.getenv('INSTANTLY_API_KEY')
        if not api_key:
            return jsonify({'error': 'INSTANTLY_API_KEY not configured'}), 400

        inst = InstantlyIntegration(api_key)
        result = inst.add_leads_to_campaign(campaign_id, instantly_leads)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Retry Instantly import failed: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

# Alias routes to avoid path mismatch issues
@app.route('/api/instantly/import', methods=['POST'])
def instantly_import_alias():
    return retry_instantly_import()

@app.route('/api/instantly/retry_import', methods=['POST'])
def instantly_retry_import_alias():
    return retry_instantly_import()

@app.route('/api/instantly/add-leads', methods=['POST'])
def instantly_add_leads_alias():
    return retry_instantly_import()

@app.route('/api/instantly/retry-import-batch', methods=['POST'])
def retry_instantly_import_batch():
    data = request.json or {}
    job_ids = data.get('job_ids') or []
    campaign_id = data.get('campaign_id')
    if not job_ids or not campaign_id:
        return jsonify({'error': 'job_ids (array) and campaign_id are required'}), 400

    try:
        api_key = os.getenv('INSTANTLY_API_KEY')
        if not api_key:
            return jsonify({'error': 'INSTANTLY_API_KEY not configured'}), 400

        # Collect leads from all jobs
        all_leads = []
        for job_id in job_ids:
            # Load job info
            job_info = None
            if job_id in jobs:
                job_info = jobs[job_id].to_dict()
            else:
                completed = load_completed_jobs()
                job_info = completed.get(job_id)

            if not job_info:
                logger.warning(f"Job not found for batch import: {job_id}")
                continue

            result_file = job_info.get('result_file')
            if not result_file or not os.path.exists(result_file):
                logger.warning(f"Result file missing for job {job_id}")
                continue

            # Read CSV and convert
            df = pd.read_csv(result_file)
            records = df.to_dict(orient='records')
            filtered = []
            for r in records:
                email = str(r.get('Email', '')).strip()
                if not email or email == 'NA':
                    continue
                status = str(r.get('Email_Status', '')).lower()
                verified_flag = str(r.get('Email_Verified', '')).lower()
                if status == 'valid' or verified_flag in ('true', '1', 'yes'):
                    filtered.append(r)
            all_leads.extend(filtered)

        if not all_leads:
            return jsonify({'success': False, 'message': 'No valid leads with emails found across selected jobs'})

        inst = InstantlyIntegration(api_key)
        instantly_leads = convert_r27_leads_to_instantly(all_leads)
        result = inst.add_leads_to_campaign(campaign_id, instantly_leads)
        return jsonify({'success': True, **result, 'jobs_processed': len(job_ids)})
    except Exception as e:
        logger.error(f"Batch Instantly import failed: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/download-batch', methods=['POST'])
def download_batch():
    data = request.json or {}
    job_ids = data.get('job_ids') or []
    if not job_ids:
        return jsonify({'error': 'job_ids (array) is required'}), 400

    try:
        # Create a temporary zip file
        tmp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(tmp_dir, f"leads_batch_{int(time.time())}.zip")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for job_id in job_ids:
                job_info = None
                if job_id in jobs:
                    job_info = jobs[job_id].to_dict()
                else:
                    completed = load_completed_jobs()
                    job_info = completed.get(job_id)

                if not job_info:
                    continue

                result_file = job_info.get('result_file')
                if result_file and os.path.exists(result_file):
                    # Add to zip with a friendly name
                    base_name = os.path.basename(result_file)
                    zf.write(result_file, arcname=base_name)

        return send_file(zip_path, as_attachment=True, download_name=os.path.basename(zip_path), mimetype='application/zip')
    except Exception as e:
        logger.error(f"Batch download failed: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/routes')
def list_routes():
    return jsonify(sorted(str(r) for r in app.url_map.iter_rules()))

# Trailing-slash variants for Instantly import endpoints
app.add_url_rule('/api/instantly/retry-import/', view_func=retry_instantly_import, methods=['POST'])
app.add_url_rule('/api/instantly/import/', view_func=instantly_import_alias, methods=['POST'])
app.add_url_rule('/api/instantly/retry_import/', view_func=instantly_retry_import_alias, methods=['POST'])
app.add_url_rule('/api/instantly/add-leads/', view_func=instantly_add_leads_alias, methods=['POST'])



if __name__ == '__main__':
    print("\n" + "="*50)
    print("UPDATED - R27 Infinite AI Leads Agent - SCORING REMOVED")
    print("="*50)
    print("\nStarting server at: http://localhost:5000")
    print("\nPress Ctrl+C to stop")
    print("="*50 + "\n")
    
    app.run(debug=False, port=5000)