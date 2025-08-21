"""
Job management module for handling lead generation jobs.
Separates job lifecycle management from the main application logic.
"""

import json
import os
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging

from .config import PathConfig, JobConfig

logger = logging.getLogger(__name__)


class JobStatus:
    """Job status constants"""
    STARTING = "starting"
    FETCHING = "fetching"
    PROCESSING = "processing"
    VERIFYING = "verifying"
    GENERATING = "generating"
    SAVING = "saving"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


class LeadGenerationJob:
    """Represents a lead generation job with all its metadata and state"""
    
    def __init__(self, job_id: str, query: str, limit: int, 
                 industry: str = 'default',
                 verify_emails: bool = True,
                 generate_emails: bool = True,
                 export_verified_only: bool = False,
                 advanced_scraping: bool = False,
                 queries: Optional[List[str]] = None,
                 add_to_instantly: bool = False,
                 instantly_campaign: str = ''):
        """
        Initialize a new lead generation job.
        
        Args:
            job_id: Unique identifier for the job
            query: Primary search query
            limit: Maximum number of leads to fetch
            industry: Industry configuration to use
            verify_emails: Whether to verify email addresses
            generate_emails: Whether to generate email content
            export_verified_only: Export only verified emails
            advanced_scraping: Use advanced website scraping
            queries: List of queries for multi-query jobs
            add_to_instantly: Auto-add to Instantly campaign
            instantly_campaign: Instantly campaign ID
        """
        self.job_id = job_id
        self.query = query
        self.queries = queries or [query] if query else []
        self.limit = limit
        self.industry = industry
        
        # Email processing flags
        self.verify_emails = JobConfig.VERIFY_EMAILS_DEFAULT  # Always True per requirements
        self.generate_emails = generate_emails
        self.export_verified_only = export_verified_only
        self.advanced_scraping = advanced_scraping
        
        # Instantly integration
        self.add_to_instantly = add_to_instantly
        self.instantly_campaign = instantly_campaign
        
        # Job state
        self.status = JobStatus.STARTING
        self.progress = 0
        self.message = "Initializing..."
        self.result_file = None
        self.cancelled = False
        self.share_link = None
        self.error = None
        
        # Statistics
        self.total_leads = 0
        self.emails_found = 0
        self.emails_verified = 0
        self.valid_emails = 0
        self.invalid_emails = 0
        
        # Timing
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
        
        # Results
        self.leads = []
        self.results = {}
        
        logger.info(f"Job {job_id} created: {len(self.queries)} queries, limit={limit}")
    
    def update_status(self, status: str, message: str = None, progress: int = None):
        """Update job status and optionally message and progress"""
        self.status = status
        if message is not None:
            self.message = message
        if progress is not None:
            self.progress = progress
        logger.debug(f"Job {self.job_id} status: {status} - {message}")
    
    def set_error(self, error_message: str):
        """Set job error state"""
        self.status = JobStatus.ERROR
        self.error = error_message
        self.message = f"Error: {error_message}"
        logger.error(f"Job {self.job_id} error: {error_message}")
    
    def cancel(self):
        """Cancel the job"""
        self.cancelled = True
        self.status = JobStatus.CANCELLED
        self.message = "Job cancelled by user"
        logger.info(f"Job {self.job_id} cancelled")
    
    def complete(self):
        """Mark job as completed"""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.now()
        self.progress = 100
        self.message = f"Completed: {self.total_leads} leads found"
        logger.info(f"Job {self.job_id} completed: {self.total_leads} leads")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary for serialization"""
        return {
            'job_id': self.job_id,
            'query': self.query,
            'queries': self.queries,
            'limit': self.limit,
            'industry': self.industry,
            'status': self.status,
            'progress': self.progress,
            'message': self.message,
            'result_file': self.result_file,
            'share_link': self.share_link,
            'error': self.error,
            'total_leads': self.total_leads,
            'emails_found': self.emails_found,
            'emails_verified': self.emails_verified,
            'valid_emails': self.valid_emails,
            'invalid_emails': self.invalid_emails,
            'verify_emails': self.verify_emails,
            'generate_emails': self.generate_emails,
            'export_verified_only': self.export_verified_only,
            'advanced_scraping': self.advanced_scraping,
            'add_to_instantly': self.add_to_instantly,
            'instantly_campaign': self.instantly_campaign,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }


class JobManager:
    """Manages all lead generation jobs"""
    
    def __init__(self):
        """Initialize the job manager"""
        self.active_jobs: Dict[str, LeadGenerationJob] = {}
        self.completed_jobs: Dict[str, Dict[str, Any]] = {}
        self._load_completed_jobs()
        logger.info("JobManager initialized")
    
    def create_job(self, job_id: str = None, **kwargs) -> LeadGenerationJob:
        """
        Create a new job.
        
        Args:
            job_id: Optional job ID (auto-generated if not provided)
            **kwargs: Job parameters passed to LeadGenerationJob
        
        Returns:
            Created LeadGenerationJob instance
        """
        if job_id is None:
            job_id = f"job_{int(time.time() * 1000)}"
        
        job = LeadGenerationJob(job_id, **kwargs)
        self.active_jobs[job_id] = job
        return job
    
    def get_job(self, job_id: str) -> Optional[LeadGenerationJob]:
        """Get a job by ID (active or completed)"""
        # Check active jobs first
        if job_id in self.active_jobs:
            return self.active_jobs[job_id]
        
        # Check completed jobs
        if job_id in self.completed_jobs:
            # Return a dict representation for completed jobs
            return self.completed_jobs[job_id]
        
        return None
    
    def complete_job(self, job_id: str):
        """Mark a job as completed and move to persistent storage"""
        if job_id not in self.active_jobs:
            logger.warning(f"Attempted to complete non-existent job: {job_id}")
            return
        
        job = self.active_jobs[job_id]
        job.complete()
        
        # Save to persistent storage
        self._save_completed_job(job)
        
        # Remove from active jobs
        del self.active_jobs[job_id]
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel an active job"""
        if job_id in self.active_jobs:
            self.active_jobs[job_id].cancel()
            return True
        return False
    
    def get_active_jobs(self) -> List[Dict[str, Any]]:
        """Get all active jobs as dictionaries"""
        return [job.to_dict() for job in self.active_jobs.values()]
    
    def get_completed_jobs(self) -> List[Dict[str, Any]]:
        """Get all completed jobs"""
        return list(self.completed_jobs.values())
    
    def _save_completed_job(self, job: LeadGenerationJob):
        """Save completed job to persistent storage"""
        # Create job record
        job_record = job.to_dict()
        
        # Add to completed jobs
        self.completed_jobs[job.job_id] = job_record
        
        # Keep only the most recent jobs
        if len(self.completed_jobs) > JobConfig.MAX_COMPLETED_JOBS_STORAGE:
            # Sort by completion time and keep most recent
            sorted_jobs = sorted(
                self.completed_jobs.items(),
                key=lambda x: x[1].get('completed_at', ''),
                reverse=True
            )
            self.completed_jobs = dict(sorted_jobs[:JobConfig.MAX_COMPLETED_JOBS_STORAGE])
        
        # Save to file
        try:
            with open(PathConfig.COMPLETED_JOBS_FILE, 'w') as f:
                json.dump(self.completed_jobs, f, indent=2)
            logger.info(f"Saved completed job {job.job_id} to persistent storage")
        except Exception as e:
            logger.error(f"Failed to save completed job: {e}")
    
    def _load_completed_jobs(self):
        """Load completed jobs from persistent storage"""
        if not os.path.exists(PathConfig.COMPLETED_JOBS_FILE):
            return
        
        try:
            with open(PathConfig.COMPLETED_JOBS_FILE, 'r') as f:
                self.completed_jobs = json.load(f)
            logger.info(f"Loaded {len(self.completed_jobs)} completed jobs from storage")
        except Exception as e:
            logger.error(f"Failed to load completed jobs: {e}")
            self.completed_jobs = {}


class ApolloJob:
    """Represents an Apollo lead enrichment job"""
    
    def __init__(self, job_id: str, csv_file: str):
        """
        Initialize an Apollo job.
        
        Args:
            job_id: Unique job identifier
            csv_file: Path to CSV file to process
        """
        self.job_id = job_id
        self.csv_file = csv_file
        self.status = JobStatus.STARTING
        self.progress = 0
        self.message = "Initializing Apollo processing..."
        self.result_file = None
        self.error = None
        self.total_leads = 0
        self.enriched_leads = 0
        self.created_at = datetime.now()
        self.completed_at = None
        
        logger.info(f"Apollo job {job_id} created for file: {csv_file}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'job_id': self.job_id,
            'csv_file': self.csv_file,
            'status': self.status,
            'progress': self.progress,
            'message': self.message,
            'result_file': self.result_file,
            'error': self.error,
            'total_leads': self.total_leads,
            'enriched_leads': self.enriched_leads,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }


# Global job manager instance
_job_manager = None

def get_job_manager() -> JobManager:
    """Get or create the global job manager instance"""
    global _job_manager
    if _job_manager is None:
        _job_manager = JobManager()
    return _job_manager