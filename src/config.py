"""
Configuration module for the infleads application.
Centralizes all configuration settings, constants, and environment variables.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Application Configuration
class AppConfig:
    """Flask application configuration"""
    TEMPLATES_AUTO_RELOAD = True
    SEND_FILE_MAX_AGE_DEFAULT = 0
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = 'logs/flask_app.log'
    
    # Development
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    TESTING = os.getenv('FLASK_TESTING', 'False').lower() == 'true'

# File Paths Configuration
class PathConfig:
    """File paths and directories configuration"""
    # Base directories
    DATA_DIR = 'data'
    LOGS_DIR = 'logs'
    OUTPUT_DIR = 'output'
    DOWNLOADS_DIR = 'downloads'
    TEMPLATES_DIR = 'templates'
    
    # Data files
    COMPLETED_JOBS_FILE = os.path.join(DATA_DIR, 'completed_jobs.json')
    RESTART_INFO_PATH = os.path.join(DATA_DIR, 'restart_info.json')
    SCHEDULER_DB = os.path.join(DATA_DIR, 'scheduler.db')
    SEARCH_HISTORY_DB = os.path.join(DATA_DIR, 'search_history.db')
    
    # Template files
    SCHEDULE_TEMPLATE = 'schedule_template.csv'
    
    @classmethod
    def ensure_directories(cls):
        """Ensure all required directories exist"""
        for dir_path in [cls.DATA_DIR, cls.LOGS_DIR, cls.OUTPUT_DIR, cls.DOWNLOADS_DIR]:
            os.makedirs(dir_path, exist_ok=True)

# Job Configuration
class JobConfig:
    """Job processing configuration"""
    MAX_COMPLETED_JOBS_STORAGE = 100
    DEFAULT_LEAD_LIMIT = 10
    MAX_LEAD_LIMIT = 500
    
    # Email verification
    VERIFY_EMAILS_DEFAULT = True  # Always enabled as per requirements
    GENERATE_EMAILS_DEFAULT = True
    EXPORT_VERIFIED_ONLY_DEFAULT = False
    ADVANCED_SCRAPING_DEFAULT = False
    
    # Timeouts (in seconds)
    JOB_TIMEOUT = 3600  # 1 hour
    EMAIL_VERIFICATION_TIMEOUT = 30
    WEBSITE_SCRAPING_TIMEOUT = 10

# API Configuration
class APIConfig:
    """External API configuration"""
    # Instantly API
    INSTANTLY_API_KEY = os.getenv('INSTANTLY_API_KEY', '')
    INSTANTLY_API_BASE_URL = 'https://api.instantly.ai/api/v2'
    
    # MailTester API
    MAILTESTER_API_KEY = os.getenv('MAILTESTER_API_KEY', '')
    MAILTESTER_API_BASE_URL = 'https://api.mailtester.com/v1'
    
    # Google Maps API
    GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY', '')
    
    # OpenAI API
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    
    # Other APIs
    PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY', '')
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')

# Debug Configuration
class DebugConfig:
    """Debug and monitoring configuration"""
    DEBUG_LOG_BUFFER_SIZE = 1000  # Number of log entries to keep in memory
    SSE_HEARTBEAT_INTERVAL = 30  # Seconds between SSE heartbeats
    
    # Feature flags for debugging
    ENABLE_DEBUG_TERMINAL = True
    ENABLE_RESTART_COUNTER = True
    ENABLE_DETAILED_LOGGING = os.getenv('DETAILED_LOGGING', 'False').lower() == 'true'

# CSV Export Configuration
class CSVConfig:
    """CSV export configuration"""
    # Standard column order - DO NOT MODIFY (critical for compatibility)
    STANDARD_COLUMNS = [
        'Name', 'Address', 'Phone', 'Email', 'Website', 
        'SocialMediaLinks', 'Reviews', 'Images', 'Rating', 
        'ReviewCount', 'GoogleBusinessClaimed', 'SearchKeyword', 
        'Location', 'email_verified', 'Email_Status', 
        'Email_Quality_Boost', 'DraftEmail', 'Email_Source', 'Email_Score'
    ]
    
    # Column mappings for backward compatibility
    COLUMN_MAPPINGS = {
        'email_status': 'Email_Status',
        'email_quality_boost': 'Email_Quality_Boost'
    }
    
    # Default values for missing fields
    DEFAULT_VALUES = {
        'Email': 'NA',
        'SocialMediaLinks': 'NA',
        'Reviews': 'NA',
        'Images': 'NA',
        'email_verified': '',
        'Email_Status': 'missing',
        'Email_Quality_Boost': -10,
        'DraftEmail': 'Email generation disabled',
        'Email_Source': None,
        'Email_Score': None
    }

# Provider Configuration
class ProviderConfig:
    """Lead provider configuration"""
    DEFAULT_PROVIDER = 'auto'
    
    # Provider priorities for cascade mode
    PROVIDER_CASCADE_ORDER = [
        'DirectGoogleMaps',
        'YellowPagesAPI',
        'OpenStreetMap',
        'FreeScraper'
    ]
    
    # Provider-specific settings
    GOOGLE_MAPS_MAX_RESULTS = 20
    YELLOWPAGES_MAX_RESULTS = 20
    OSM_MAX_RESULTS = 50
    
    # Rate limiting (requests per second)
    RATE_LIMITS = {
        'google_maps': 10,
        'yellowpages': 5,
        'openstreetmap': 20
    }

# Scheduler Configuration
class SchedulerConfig:
    """Scheduler configuration"""
    CHECK_INTERVAL = 60  # Check for scheduled tasks every 60 seconds
    MAX_RETRY_ATTEMPTS = 3
    RETRY_DELAY = 300  # 5 minutes between retries
    
    # Queue settings
    MAX_QUEUE_SIZE = 100
    DEFAULT_QUEUE_PRIORITY = 5

# All configuration classes
CONFIG_CLASSES = {
    'app': AppConfig,
    'paths': PathConfig,
    'job': JobConfig,
    'api': APIConfig,
    'debug': DebugConfig,
    'csv': CSVConfig,
    'provider': ProviderConfig,
    'scheduler': SchedulerConfig
}

def get_config(config_name=None):
    """
    Get configuration object by name.
    
    Args:
        config_name: Name of configuration class (e.g., 'app', 'job', 'api')
                    If None, returns a namespace with all configs
    
    Returns:
        Configuration class or namespace with all configs
    """
    if config_name:
        return CONFIG_CLASSES.get(config_name.lower())
    
    # Return namespace with all configs
    class ConfigNamespace:
        pass
    
    ns = ConfigNamespace()
    for name, cls in CONFIG_CLASSES.items():
        setattr(ns, name, cls)
    
    return ns

# Initialize directories on module import
PathConfig.ensure_directories()