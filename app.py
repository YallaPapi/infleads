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
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv
import logging

# Import our modules
from src.providers import get_provider
from src.lead_scorer import LeadScorer
from src.email_generator import EmailGenerator
# from src.drive_uploader import DriveUploader  # Removed - using local downloads instead
from src.data_normalizer import DataNormalizer
from src.industry_configs import IndustryConfig
from src.apollo_lead_processor import ApolloLeadProcessor

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Store job status
jobs = {}

class LeadGenerationJob:
    def __init__(self, job_id, query, limit, industry='default'):
        self.job_id = job_id
        self.query = query
        self.limit = limit
        self.industry = industry
        self.status = "starting"
        self.progress = 0
        self.message = "Initializing..."
        self.result_file = None
        self.share_link = None
        self.error = None
        self.leads_data = []
        self.total_leads = 0
        self.average_score = 0
        
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
            'leads_preview': self.leads_data[:5] if self.leads_data else []
        }

def process_leads(job):
    """Background task to process leads"""
    try:
        # Step 1: Fetch leads
        job.status = "fetching"
        job.progress = 10
        job.message = "Fetching leads from Google Maps..."
        
        provider = get_provider('apify')
        raw_leads = provider.fetch_places(job.query, job.limit)
        
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
    
    if not query:
        return jsonify({'error': 'Query is required'}), 400
    
    # Create job
    job_id = f"job_{int(time.time())}"
    job = LeadGenerationJob(job_id, query, limit, industry)
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
    return jsonify({
        'status': 'healthy',
        'apify_configured': bool(os.getenv('APIFY_API_KEY')),
        'openai_configured': bool(os.getenv('OPENAI_API_KEY')),
        'drive_configured': os.path.exists('service_account.json') or os.path.exists('credentials.json'),
        'available_industries': IndustryConfig.get_industry_display_names()
    })

if __name__ == '__main__':
    print("\n" + "="*50)
    print("R27 Infinite AI Leads Agent - Web Interface")
    print("="*50)
    print("\nStarting server at: http://localhost:5000")
    print("\nPress Ctrl+C to stop")
    print("="*50 + "\n")
    
    app.run(debug=False, port=5000)