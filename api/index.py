"""
Vercel-compatible Flask App for R27 Infinite AI Leads Agent
"""

from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import os
import json
import time
from datetime import datetime
import logging
import json as _json
import pandas as pd
from dotenv import load_dotenv
import logging
import tempfile
import io

# Load environment variables
load_dotenv()

app = Flask(__name__, template_folder='../templates', static_folder='../static')
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import our modules (with error handling for missing modules)
import sys
sys.path.append('..')

try:
    from src.providers import get_provider
    from src.email_generator import EmailGenerator
    from src.data_normalizer import DataNormalizer
    from src.industry_configs import IndustryConfig
    from src.email_scraper import WebsiteEmailScraper
    from src.keyword_expander import KeywordExpander
    from src.lead_enrichment import LeadEnricher
    from src.instantly_integration import InstantlyIntegration, convert_r27_leads_to_instantly
    MODULES_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Some modules not available: {e}")
    MODULES_AVAILABLE = False

# Simple in-memory storage (will reset on each cold start)
job_results = {}

class SimpleLeadJob:
    def __init__(self, job_id, query, limit, verify_emails=False, generate_emails=True):
        self.job_id = job_id
        self.query = query
        self.limit = limit
        self.verify_emails = verify_emails
        self.generate_emails = generate_emails
        self.status = "processing"
        self.progress = 0
        self.message = "Starting..."
        self.total_leads = 0
        self.result_data = []
        self.error = None
        
    def to_dict(self):
        return {
            'job_id': self.job_id,
            'query': self.query,
            'status': self.status,
            'progress': self.progress,
            'message': self.message,
            'total_leads': self.total_leads,
            'error': self.error,
            'leads_preview': self.result_data[:10] if self.result_data else []
        }

# ---------------------------------------------------------------------------
# Restart counter/version endpoints (parity with full app)
# ---------------------------------------------------------------------------

# Persist restart info to project data directory
def _ensure_data_dir_dev():
    try:
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        os.makedirs(data_dir, exist_ok=True)
        return data_dir
    except Exception:
        return os.path.join(os.getcwd(), 'data')

_DATA_DIR = _ensure_data_dir_dev()
_RESTART_INFO_PATH = os.path.join(_DATA_DIR, 'restart_info.json')

def _load_restart_info_internal():
    try:
        if os.path.exists(_RESTART_INFO_PATH):
            with open(_RESTART_INFO_PATH, 'r', encoding='utf-8') as f:
                return _json.load(f)
    except Exception:
        pass
    return {'counter': 0, 'last_notes': '', 'history': []}

def _save_restart_info_internal(info):
    try:
        os.makedirs(_DATA_DIR, exist_ok=True)
        with open(_RESTART_INFO_PATH, 'w', encoding='utf-8') as f:
            _json.dump(info, f, indent=2)
    except Exception as e:
        logger.warning(f"Failed to save restart info: {e}")

def _increment_restart_counter(notes: str | None = None):
    info = _load_restart_info_internal()
    try:
        info['counter'] = int(info.get('counter', 0)) + 1
    except Exception:
        info['counter'] = 1
    if notes is not None:
        info['last_notes'] = notes
    if 'history' not in info or not isinstance(info['history'], list):
        info['history'] = []
    info['history'].append({
        'timestamp': datetime.now().isoformat(timespec='seconds'),
        'counter': info.get('counter', 0),
        'notes': info.get('last_notes', '')
    })
    _save_restart_info_internal(info)
    logger.info(f"Serverless restart counter incremented to {info['counter']}")

# Increment once on import/start
_increment_restart_counter(os.getenv('RESTART_NOTES', '').strip() or None)

@app.route('/api/restart-info', methods=['GET'])
def get_restart_info():
    info = _load_restart_info_internal()
    # Only return last 5 history entries
    info['history'] = info.get('history', [])[-5:]
    return jsonify(info)

@app.route('/api/restart-notes', methods=['POST'])
def set_restart_notes():
    try:
        payload = request.get_json(force=True) or {}
        notes = str(payload.get('notes', '')).strip()
        info = _load_restart_info_internal()
        info['last_notes'] = notes
        if 'history' not in info or not isinstance(info['history'], list):
            info['history'] = []
        info['history'].append({
            'timestamp': datetime.now().isoformat(timespec='seconds'),
            'counter': info.get('counter', 0),
            'notes': notes
        })
        _save_restart_info_internal(info)
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Failed to set restart notes: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def process_leads_sync(job):
    """Synchronous lead processing for Vercel"""
    try:
        if not MODULES_AVAILABLE:
            job.status = "error"
            job.error = "Required modules not available"
            return
            
        job.status = "fetching"
        job.progress = 20
        job.message = "Fetching leads from Google Maps..."
        
        # Get provider
        provider = get_provider('auto')
        raw_leads = provider.fetch_places(job.query, job.limit)
        
        if not raw_leads:
            job.status = "error"
            job.error = "No leads found"
            return
        
        job.progress = 40
        job.message = f"Found {len(raw_leads)} businesses, normalizing..."
        
        # Normalize data
        normalizer = DataNormalizer()
        normalized_leads = normalizer.normalize(raw_leads)
        
        job.progress = 60
        job.message = "Processing leads..."
        
        # Email scraping with smart batching for serverless
        try:
            scraper = WebsiteEmailScraper()
            # Use more workers for better performance, but limit to avoid timeout
            max_workers = min(5, len(normalized_leads))
            normalized_leads = scraper.scrape_contacts_bulk(normalized_leads, max_workers=max_workers)
        except Exception as e:
            logger.warning(f"Email scraping failed: {e}")
        
        job.progress = 80
        job.message = "Finalizing results..."
        
        # Skip email generation for now in Vercel (too slow)
        for lead in normalized_leads:
            lead['DraftEmail'] = 'Email generation disabled in serverless mode'
        
        job.result_data = normalized_leads
        job.total_leads = len(normalized_leads)
        job.status = "completed"
        job.progress = 100
        job.message = f"Successfully generated {len(normalized_leads)} leads!"
        
    except Exception as e:
        logger.error(f"Job failed: {e}")
        job.status = "error"
        job.error = str(e)
        job.message = "Job failed"

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index_simple.html')

@app.route('/api/generate', methods=['POST'])
def generate_leads():
    """Start a new lead generation job (synchronous for Vercel)"""
    try:
        data = request.json
        query = data.get('query', '')
        limit = int(data.get('limit', 25))
        verify_emails = data.get('verify_emails', False)
        generate_emails = data.get('generate_emails', False)  # Disabled for serverless
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        # Create job
        job_id = f"job_{int(time.time())}"
        job = SimpleLeadJob(job_id, query, limit, verify_emails, generate_emails)
        
        # Process synchronously (no background tasks in serverless)
        process_leads_sync(job)
        
        # Store result
        job_results[job_id] = job
        
        return jsonify({'job_id': job_id})
        
    except Exception as e:
        logger.error(f"Generate leads error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/status/<job_id>')
def get_status(job_id):
    """Get job status"""
    if job_id not in job_results:
        return jsonify({'error': 'Job not found'}), 404
    
    job = job_results[job_id]
    return jsonify(job.to_dict())

@app.route('/api/download/<job_id>')
def download_csv(job_id):
    """Download CSV file"""
    if job_id not in job_results:
        return jsonify({'error': 'Job not found'}), 404
    
    job = job_results[job_id]
    if job.status != 'completed' or not job.result_data:
        return jsonify({'error': 'Job not completed or no data'}), 404
    
    # Create CSV in memory
    df = pd.DataFrame(job.result_data)
    
    # Ensure required columns exist
    required_columns = ['Name', 'Address', 'Phone', 'Email', 'Website', 'DraftEmail']
    for col in required_columns:
        if col not in df.columns:
            df[col] = 'NA'
    
    # Create CSV string
    csv_string = df.to_csv(index=False)
    
    # Create file-like object
    output = io.StringIO(csv_string)
    output.seek(0)
    
    # Convert to bytes
    csv_bytes = io.BytesIO(csv_string.encode('utf-8'))
    csv_bytes.seek(0)
    
    filename = f"leads_{job.query.replace(' ', '_')[:20]}_{int(time.time())}.csv"
    
    return send_file(
        csv_bytes,
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    try:
        provider = get_provider('auto')
        return jsonify({
            'status': 'healthy',
            'provider': provider.__class__.__name__,
            'google_api_key': bool(os.getenv('GOOGLE_API_KEY')),
            'serverless_mode': True
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/expand-keywords', methods=['POST'])
def expand_keywords():
    """Expand keywords (simplified for serverless)"""
    try:
        data = request.json
        keyword = data.get('keyword', '')
        location = data.get('location', '')
        
        if not keyword:
            return jsonify({'error': 'Keyword required'}), 400
        
        # Simple keyword expansion (no LLM calls in basic version)
        variants = [
            {'keyword': f"{keyword} in {location}" if location else keyword, 'description': 'Original query'},
            {'keyword': f"{keyword} near {location}" if location else f"{keyword} services", 'description': 'Alternative phrasing'},
            {'keyword': f"best {keyword} {location}" if location else f"best {keyword}", 'description': 'Quality focused'},
        ]
        
        return jsonify({
            'success': True,
            'base_keyword': keyword,
            'location': location,
            'variants': variants,
            'count': len(variants)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Vercel entry point
def handler(request):
    return app(request.environ, lambda status, headers: None)

if __name__ == '__main__':
    app.run(debug=True, port=5000)