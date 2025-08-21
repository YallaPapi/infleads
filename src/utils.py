"""
Utility functions module.
Contains common helper functions used throughout the application.
"""

import os
import re
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


def sanitize_filename(filename: str, max_length: int = 100) -> str:
    """
    Sanitize a string to be safe for use as a filename.
    
    Args:
        filename: The filename to sanitize
        max_length: Maximum length of the filename
    
    Returns:
        Sanitized filename
    """
    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    sanitized = re.sub(r'[^\w\s\-_.]', '_', sanitized)
    sanitized = re.sub(r'[\s]+', '_', sanitized)
    sanitized = re.sub(r'_+', '_', sanitized)
    
    # Trim to max length
    if len(sanitized) > max_length:
        # Keep file extension if present
        if '.' in sanitized:
            name, ext = sanitized.rsplit('.', 1)
            sanitized = name[:max_length - len(ext) - 1] + '.' + ext
        else:
            sanitized = sanitized[:max_length]
    
    return sanitized.strip('_')


def generate_timestamp_filename(prefix: str, extension: str = 'csv') -> str:
    """
    Generate a filename with timestamp.
    
    Args:
        prefix: Prefix for the filename
        extension: File extension (without dot)
    
    Returns:
        Timestamped filename
    """
    timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
    safe_prefix = sanitize_filename(prefix)
    return f"{timestamp}_{safe_prefix}.{extension}"


def ensure_directory(path: str) -> str:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Directory path
    
    Returns:
        The path that was ensured
    """
    try:
        os.makedirs(path, exist_ok=True)
        return path
    except Exception as e:
        logger.error(f"Failed to create directory {path}: {e}")
        raise


def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """
    Safely parse JSON string with fallback.
    
    Args:
        json_str: JSON string to parse
        default: Default value if parsing fails
    
    Returns:
        Parsed JSON or default value
    """
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError) as e:
        logger.debug(f"JSON parse error: {e}")
        return default


def safe_dict_get(dictionary: Dict, keys: Union[str, List[str]], default: Any = None) -> Any:
    """
    Safely get nested dictionary value.
    
    Args:
        dictionary: Dictionary to search
        keys: Key or list of keys for nested access
        default: Default value if key not found
    
    Returns:
        Value at key path or default
    """
    if isinstance(keys, str):
        keys = [keys]
    
    current = dictionary
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    
    return current


def format_phone_number(phone: str) -> str:
    """
    Format a phone number to a consistent format.
    
    Args:
        phone: Phone number string
    
    Returns:
        Formatted phone number
    """
    if not phone:
        return 'NA'
    
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    
    # Format based on length
    if len(digits) == 10:  # US number without country code
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits[0] == '1':  # US number with country code
        return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    else:
        # Return original if format is unknown
        return phone


def format_percentage(value: float, decimals: int = 1) -> str:
    """
    Format a value as a percentage string.
    
    Args:
        value: Value between 0 and 1
        decimals: Number of decimal places
    
    Returns:
        Formatted percentage string
    """
    percentage = value * 100
    return f"{percentage:.{decimals}f}%"


def truncate_string(text: str, max_length: int = 100, suffix: str = '...') -> str:
    """
    Truncate a string to a maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncated
    
    Returns:
        Truncated string
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def clean_email(email: str) -> str:
    """
    Clean and validate an email address.
    
    Args:
        email: Email address to clean
    
    Returns:
        Cleaned email or 'NA' if invalid
    """
    if not email or email.upper() == 'NA':
        return 'NA'
    
    # Basic email validation regex
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    email = email.strip().lower()
    
    if re.match(email_pattern, email):
        return email
    
    return 'NA'


def parse_boolean(value: Any) -> bool:
    """
    Parse various representations of boolean values.
    
    Args:
        value: Value to parse
    
    Returns:
        Boolean value
    """
    if isinstance(value, bool):
        return value
    
    if isinstance(value, str):
        return value.lower() in ('true', 'yes', '1', 'on', 'enabled')
    
    return bool(value)


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
    
    Returns:
        Human-readable size string
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    
    return f"{size_bytes:.1f} TB"


def merge_dictionaries(*dicts: Dict, deep: bool = False) -> Dict:
    """
    Merge multiple dictionaries.
    
    Args:
        *dicts: Dictionaries to merge
        deep: Whether to perform deep merge
    
    Returns:
        Merged dictionary
    """
    result = {}
    
    for dictionary in dicts:
        if not dictionary:
            continue
        
        if deep:
            # Deep merge
            for key, value in dictionary.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = merge_dictionaries(result[key], value, deep=True)
                else:
                    result[key] = value
        else:
            # Shallow merge
            result.update(dictionary)
    
    return result


def batch_list(items: List, batch_size: int) -> List[List]:
    """
    Split a list into batches.
    
    Args:
        items: List to batch
        batch_size: Size of each batch
    
    Returns:
        List of batches
    """
    return [items[i:i + batch_size] for i in range(0, len(items), batch_size)]


def remove_duplicates(items: List[Dict], key: str) -> List[Dict]:
    """
    Remove duplicate dictionaries from a list based on a key.
    
    Args:
        items: List of dictionaries
        key: Key to check for duplicates
    
    Returns:
        List with duplicates removed
    """
    seen = set()
    result = []
    
    for item in items:
        if key in item:
            value = item[key]
            if value not in seen:
                seen.add(value)
                result.append(item)
        else:
            result.append(item)
    
    return result


def calculate_progress(current: int, total: int) -> int:
    """
    Calculate percentage progress.
    
    Args:
        current: Current value
        total: Total value
    
    Returns:
        Progress percentage (0-100)
    """
    if total <= 0:
        return 100 if current > 0 else 0
    
    return min(100, max(0, int((current / total) * 100)))


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable format.
    
    Args:
        seconds: Duration in seconds
    
    Returns:
        Human-readable duration string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


class RateLimiter:
    """Simple rate limiter for API calls"""
    
    def __init__(self, max_calls: int, period: float):
        """
        Initialize rate limiter.
        
        Args:
            max_calls: Maximum number of calls allowed
            period: Time period in seconds
        """
        self.max_calls = max_calls
        self.period = period
        self.calls = []
    
    def can_call(self) -> bool:
        """Check if a call can be made"""
        import time
        now = time.time()
        
        # Remove old calls outside the period
        self.calls = [call_time for call_time in self.calls 
                     if now - call_time < self.period]
        
        return len(self.calls) < self.max_calls
    
    def record_call(self):
        """Record that a call was made"""
        import time
        self.calls.append(time.time())
    
    def wait_if_needed(self):
        """Wait if rate limit would be exceeded"""
        import time
        while not self.can_call():
            time.sleep(0.1)
        self.record_call()