"""
Debug utilities module for development and monitoring.
Handles restart counter, debug logging, and monitoring features.
"""

import json
import os
import logging
import queue
from collections import deque
from datetime import datetime
from typing import Dict, Any, List, Optional

from .config import PathConfig, DebugConfig

logger = logging.getLogger(__name__)


class RestartCounter:
    """Manages the development restart counter"""
    
    def __init__(self):
        """Initialize the restart counter"""
        self.info = self._load_info()
        self._increment_on_start()
    
    def _load_info(self) -> Dict[str, Any]:
        """Load restart info from file"""
        if os.path.exists(PathConfig.RESTART_INFO_PATH):
            try:
                with open(PathConfig.RESTART_INFO_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load restart info: {e}")
                return self._default_info()
        return self._default_info()
    
    def _default_info(self) -> Dict[str, Any]:
        """Get default restart info structure"""
        return {
            'counter': 0,
            'last_notes': '',
            'history': []
        }
    
    def _save_info(self):
        """Save restart info to file"""
        try:
            with open(PathConfig.RESTART_INFO_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.info, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save restart info: {e}")
    
    def _increment_on_start(self):
        """Increment counter on startup"""
        if not DebugConfig.ENABLE_RESTART_COUNTER:
            return
        
        notes = os.getenv('RESTART_NOTES', '').strip() or None
        self.increment(notes)
    
    def increment(self, notes: Optional[str] = None):
        """
        Increment the restart counter.
        
        Args:
            notes: Optional notes about this restart
        """
        self.info['counter'] = int(self.info.get('counter', 0)) + 1
        
        if notes is not None:
            self.info['last_notes'] = notes
        
        if 'history' not in self.info or not isinstance(self.info['history'], list):
            self.info['history'] = []
        
        self.info['history'].append({
            'timestamp': datetime.now().isoformat(timespec='seconds'),
            'counter': self.info['counter'],
            'notes': self.info.get('last_notes', '')
        })
        
        # Keep only last 50 history entries
        if len(self.info['history']) > 50:
            self.info['history'] = self.info['history'][-50:]
        
        self._save_info()
        logger.info(f"Dev restart counter incremented to {self.info['counter']}")
    
    def get_info(self) -> Dict[str, Any]:
        """Get current restart info"""
        return {
            'counter': self.info.get('counter', 0),
            'last_notes': self.info.get('last_notes', ''),
            'history': self.info.get('history', [])[-5:]  # Last 5 entries
        }
    
    def set_notes(self, notes: str):
        """
        Set notes for the current session.
        
        Args:
            notes: Notes to set
        """
        self.info['last_notes'] = notes
        
        if 'history' not in self.info:
            self.info['history'] = []
        
        self.info['history'].append({
            'timestamp': datetime.now().isoformat(timespec='seconds'),
            'counter': self.info.get('counter', 0),
            'notes': notes
        })
        
        self._save_info()


class DebugLogHandler(logging.Handler):
    """Custom log handler that stores logs for the debug terminal"""
    
    def __init__(self, buffer_size: int = None):
        """
        Initialize the debug log handler.
        
        Args:
            buffer_size: Maximum number of log entries to keep
        """
        super().__init__()
        self.buffer_size = buffer_size or DebugConfig.DEBUG_LOG_BUFFER_SIZE
        self.logs = deque(maxlen=self.buffer_size)
        self.subscribers: List[queue.Queue] = []
    
    def emit(self, record: logging.LogRecord):
        """Handle a log record"""
        try:
            log_entry = self._format_log_entry(record)
            self.logs.append(log_entry)
            self._notify_subscribers(log_entry)
        except Exception:
            pass  # Ignore errors in logging handler
    
    def _format_log_entry(self, record: logging.LogRecord) -> Dict[str, Any]:
        """Format a log record as a dictionary"""
        return {
            'timestamp': datetime.fromtimestamp(record.created).strftime('%H:%M:%S.%f')[:-3],
            'level': record.levelname,
            'name': record.name,
            'message': self.format(record)
        }
    
    def _notify_subscribers(self, log_entry: Dict[str, Any]):
        """Notify all SSE subscribers of new log entry"""
        for subscriber_queue in self.subscribers[:]:  # Copy to avoid modification during iteration
            try:
                subscriber_queue.put_nowait(log_entry)
            except queue.Full:
                # Remove full queues
                self.subscribers.remove(subscriber_queue)
    
    def subscribe(self) -> queue.Queue:
        """
        Subscribe to log updates.
        
        Returns:
            Queue that will receive log entries
        """
        subscriber_queue = queue.Queue(maxsize=100)
        self.subscribers.append(subscriber_queue)
        return subscriber_queue
    
    def unsubscribe(self, subscriber_queue: queue.Queue):
        """
        Unsubscribe from log updates.
        
        Args:
            subscriber_queue: Queue to unsubscribe
        """
        if subscriber_queue in self.subscribers:
            self.subscribers.remove(subscriber_queue)
    
    def get_recent_logs(self, count: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent log entries.
        
        Args:
            count: Number of recent logs to return
        
        Returns:
            List of log entries
        """
        return list(self.logs)[-count:]


class DebugTerminal:
    """Manages the debug terminal functionality"""
    
    def __init__(self):
        """Initialize the debug terminal"""
        self.enabled = DebugConfig.ENABLE_DEBUG_TERMINAL
        self.log_handler = None
        
        if self.enabled:
            self._setup_logging()
    
    def _setup_logging(self):
        """Set up debug logging handler"""
        self.log_handler = DebugLogHandler()
        self.log_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        
        # Add to root logger
        logging.getLogger().addHandler(self.log_handler)
        logger.info("Debug terminal logging initialized")
    
    def get_logs(self, count: int = 100) -> List[Dict[str, Any]]:
        """Get recent log entries"""
        if not self.log_handler:
            return []
        return self.log_handler.get_recent_logs(count)
    
    def subscribe(self) -> Optional[queue.Queue]:
        """Subscribe to log updates"""
        if not self.log_handler:
            return None
        return self.log_handler.subscribe()
    
    def unsubscribe(self, subscriber_queue: queue.Queue):
        """Unsubscribe from log updates"""
        if self.log_handler:
            self.log_handler.unsubscribe(subscriber_queue)


class SystemMonitor:
    """Monitors system status and health"""
    
    @staticmethod
    def get_debug_info() -> Dict[str, Any]:
        """
        Get comprehensive debug information.
        
        Returns:
            Dictionary with system debug information
        """
        import psutil
        import sys
        
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            
            return {
                'system': {
                    'python_version': sys.version,
                    'platform': sys.platform,
                    'pid': os.getpid()
                },
                'memory': {
                    'rss_mb': round(memory_info.rss / 1024 / 1024, 2),
                    'vms_mb': round(memory_info.vms / 1024 / 1024, 2),
                    'percent': round(process.memory_percent(), 2)
                },
                'cpu': {
                    'percent': process.cpu_percent(interval=0.1),
                    'num_threads': process.num_threads()
                },
                'environment': {
                    'debug_mode': DebugConfig.ENABLE_DETAILED_LOGGING,
                    'log_level': logging.getLogger().level
                }
            }
        except Exception as e:
            logger.error(f"Failed to get debug info: {e}")
            return {
                'error': str(e),
                'basic_info': {
                    'python_version': sys.version,
                    'platform': sys.platform
                }
            }


# Global instances
_restart_counter = None
_debug_terminal = None

def get_restart_counter() -> RestartCounter:
    """Get or create the global restart counter instance"""
    global _restart_counter
    if _restart_counter is None:
        _restart_counter = RestartCounter()
    return _restart_counter

def get_debug_terminal() -> DebugTerminal:
    """Get or create the global debug terminal instance"""
    global _debug_terminal
    if _debug_terminal is None:
        _debug_terminal = DebugTerminal()
    return _debug_terminal