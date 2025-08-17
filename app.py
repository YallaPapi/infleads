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

# Load environment variables FIRST
load_dotenv()

# Import our modules
from src.providers import get_provider
from src.lead_scorer import LeadScorer
from src.email_generator import EmailGenerator
# from src.drive_uploader import DriveUploader  # Removed - using local downloads instead
from src.data_normalizer import DataNormalizer
from src.industry_configs import IndustryConfig
from src.apollo_lead_processor import ApolloLeadProcessor
from src.email_verifier import MailTesterVerifier, EmailStatus
from src.scheduler import LeadScheduler
from src.email_scraper import WebsiteEmailScraper

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Store job status
jobs = {}
apollo_jobs = {}

# Initialize scheduler
scheduler = LeadScheduler()

def process_scheduled_search(query: str, limit: int, verify_emails: bool):
    """Process a scheduled search"""
    job_id = f"scheduled_{int(time.time())}"
    job = LeadGenerationJob(job_id, query, limit, verify_emails=verify_emails)
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
    def __init__(self, job_id, query, limit, industry='default', verify_emails=False):
        self.job_id = job_id
        self.query = query
        self.limit = limit
        self.industry = industry
        self.verify_emails = verify_emails
        self.status = "starting"
        self.progress = 0
        self.message = "Initializing..."
        self.result_file = None
        self.share_link = None
        self.error = None
        self.leads_data = []
        self.total_leads = 0
        self.average_score = 0
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
            'average_score': self.average_score,
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
        
        print(f"DEBUG: Getting provider...")
        try:
            provider = get_provider('auto')  # Auto-detects best available (NOT APIFY)
            print(f"DEBUG: Got provider: {provider.__class__.__name__}")
            logger.info(f"Using provider: {provider.__class__.__name__}")
            print(f"DEBUG: Fetching places for query: {job.query}, limit: {job.limit}")
            raw_leads = provider.fetch_places(job.query, job.limit)
            print(f"DEBUG: Got {len(raw_leads) if raw_leads else 0} leads")
        except Exception as e:
            print(f"DEBUG: Provider error: {e}")
            logger.error(f"Provider error: {e}", exc_info=True)
            job.status = "error"
            job.error = f"Provider error: {str(e)}"
            return
        
        if not raw_leads:
            job.status = "error"
            job.error = "No leads found for this query"
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
        
        # Step 2.3: Scrape emails from websites (FREE!)
        job.status = "scraping_emails"
        job.progress = 32
        job.message = "Scraping emails from websites..."
        
        try:
            scraper = WebsiteEmailScraper()
            normalized_leads = scraper.scrape_emails_bulk(normalized_leads, max_workers=5)
            emails_found = sum(1 for lead in normalized_leads 
                             if lead.get('Email') and lead['Email'] != 'NA')
            logger.info(f"Found {emails_found} emails from website scraping")
            job.message = f"Found {emails_found} emails from websites"
        except Exception as e:
            logger.error(f"Email scraping failed: {e}")
        
        # Step 2.5: Email Verification (if enabled)
        if job.verify_emails and os.getenv('MAILTESTER_API_KEY'):
            job.status = "verifying_emails"
            job.progress = 35
            job.message = "Verifying email addresses..."
            
            try:
                verifier = MailTesterVerifier()
                verified_leads = []
                
                for i, lead in enumerate(normalized_leads):
                    email = lead.get('Email', '').strip()
                    
                    if email and email != 'NA':
                        try:
                            result = verifier.verify_email(email)
                            
                            # Add verification data
                            lead['email_verified'] = result.status == EmailStatus.VALID
                            lead['email_status'] = result.status.value
                            lead['email_score'] = result.score
                            
                            job.emails_verified += 1
                            if result.status == EmailStatus.VALID:
                                job.valid_emails += 1
                                
                            # Adjust scoring boost
                            if result.status == EmailStatus.VALID:
                                lead['email_quality_boost'] = 20
                            elif result.status == EmailStatus.CATCH_ALL:
                                lead['email_quality_boost'] = 10
                            elif result.status in [EmailStatus.INVALID, EmailStatus.DISPOSABLE]:
                                lead['email_quality_boost'] = -50
                            else:
                                lead['email_quality_boost'] = 0
                        except Exception as e:
                            logger.warning(f"Email verification failed for {email}: {e}")
                            lead['email_verified'] = False
                            lead['email_status'] = 'error'
                            lead['email_quality_boost'] = 0
                    else:
                        lead['email_verified'] = False
                        lead['email_status'] = 'missing'
                        lead['email_quality_boost'] = -10
                    
                    verified_leads.append(lead)
                    job.progress = 35 + int((i + 1) / len(normalized_leads) * 5)
                    job.message = f"Verified {i + 1}/{len(normalized_leads)} emails"
                
                normalized_leads = verified_leads
                logger.info(f"Email verification complete: {job.valid_emails}/{job.emails_verified} valid")
                
            except Exception as e:
                logger.error(f"Email verification service error: {e}")
                job.message = "Email verification skipped due to error"
        
        # Step 3: Score leads
        job.status = "scoring"
        job.progress = 40
        job.message = "Scoring leads with AI..."
        
        scorer = LeadScorer(industry=job.industry)
        scored_leads = []
        scores = []
        
        for i, lead in enumerate(normalized_leads):
            try:
                score, reasoning = scorer.score_lead(lead)
                
                # Apply email quality boost if email was verified
                if 'email_quality_boost' in lead:
                    original_score = score
                    score = max(0, min(100, score + lead['email_quality_boost']))
                    if lead['email_quality_boost'] != 0:
                        reasoning += f" Email verification: {lead.get('email_status', 'unknown')} (score adjusted by {lead['email_quality_boost']:+d} points)."
                
                lead['LeadScore'] = score
                lead['LeadScoreReasoning'] = reasoning
                scored_leads.append(lead)
                scores.append(score)
                job.progress = 40 + int((i + 1) / len(normalized_leads) * 20)
                job.message = f"Scored {i + 1}/{len(normalized_leads)} leads"
            except Exception as e:
                logger.error(f"Failed to score lead: {e}")
                lead['LeadScore'] = 'NA'
                lead['LeadScoreReasoning'] = 'Scoring failed'
                scored_leads.append(lead)
        
        # Calculate average score
        if scores:
            job.average_score = round(sum(scores) / len(scores), 1)
        
        # Step 4: Generate emails
        job.status = "generating_emails"
        job.progress = 60
        job.message = "Generating personalized emails..."
        
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
        
        # Store leads data for preview
        job.leads_data = final_leads
        
        # Step 5: Create CSV
        job.status = "creating_csv"
        job.progress = 85
        job.message = "Creating CSV file..."
        
        # Ensure output directory exists
        os.makedirs('output', exist_ok=True)
        
        # Create filename
        date_str = datetime.now().strftime('%Y-%m-%d_%H%M%S')
        safe_query = job.query.replace(' ', '_').replace(',', '')[:30]
        filename = f"{date_str}_{safe_query}.csv"
        filepath = os.path.join('output', filename)
        
        # Create DataFrame with exact column order (including email fields)
        columns = ['Name', 'Address', 'Phone', 'Email', 'Website', 'SocialMediaLinks', 
                  'Reviews', 'Images', 'LeadScore', 'LeadScoreReasoning']
        
        # Add email verification columns if email verification was enabled
        if job.verify_emails:
            columns.extend(['email_verified', 'email_status', 'email_quality_boost'])
        
        # Add DraftEmail at the end
        columns.append('DraftEmail')
        
        df = pd.DataFrame(final_leads)
        
        # Ensure all columns exist
        for col in columns:
            if col not in df.columns:
                df[col] = 'NA'
        
        # Reorder columns
        df = df[columns]
        
        # Save to CSV
        df.to_csv(filepath, index=False)
        job.result_file = filepath
        
        # Step 6: Skip Google Drive - just save locally
        job.status = "finalizing"
        job.progress = 90
        job.message = "Finalizing CSV file..."
        
        # No more Google Drive BS - just save locally
        job.share_link = None
        job.message = f"CSV ready for download: {filename}"
        
        # Complete
        job.status = "completed"
        job.progress = 100
        job.message = f"Successfully generated {len(final_leads)} leads!"
        
    except Exception as e:
        logger.error(f"Job failed: {e}", exc_info=True)
        job.status = "error"
        job.error = str(e)
        job.message = "Job failed"

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/api/generate', methods=['POST'])
def generate_leads():
    """Start a new lead generation job"""
    data = request.json
    query = data.get('query', '')
    limit = int(data.get('limit', 25))
    industry = data.get('industry', 'default')
    verify_emails = data.get('verify_emails', False)
    
    if not query:
        return jsonify({'error': 'Query is required'}), 400
    
    # Create job
    job_id = f"job_{int(time.time())}"
    job = LeadGenerationJob(job_id, query, limit, industry, verify_emails)
    jobs[job_id] = job
    
    # Start processing in background
    thread = threading.Thread(target=process_leads, args=(job,))
    thread.start()
    
    return jsonify({'job_id': job_id})

@app.route('/api/status/<job_id>')
def get_status(job_id):
    """Get job status"""
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify(jobs[job_id].to_dict())

@app.route('/api/download/<job_id>')
def download_csv(job_id):
    """Download the CSV file"""
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    job = jobs[job_id]
    if not job.result_file or not os.path.exists(job.result_file):
        return jsonify({'error': 'File not ready'}), 404
    
    return send_file(job.result_file, as_attachment=True, mimetype='text/csv')

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

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    # Test provider
    provider = get_provider('auto')
    provider_name = provider.__class__.__name__
    
    # Test fetching
    test_results = []
    try:
        test_results = provider.fetch_places('test query', 1)
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
        interval_hours=data.get('interval_hours', 24),
        integrations=data.get('integrations', [])
    )
    return jsonify({'id': schedule_id, 'success': True})

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

if __name__ == '__main__':
    print("\n" + "="*50)
    print("R27 Infinite AI Leads Agent - Web Interface")
    print("="*50)
    print("\nStarting server at: http://localhost:5000")
    print("\nPress Ctrl+C to stop")
    print("="*50 + "\n")
    
    app.run(debug=False, port=5000)