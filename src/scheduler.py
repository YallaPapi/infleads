"""
Scheduler system for automated lead generation
"""

import os
import sqlite3
import json
import threading
import time
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Any, Optional
import requests

logger = logging.getLogger(__name__)

class LeadScheduler:
    """Manages scheduled lead generation tasks"""
    
    def __init__(self, db_path: str = None):
        # Use persistent data directory
        if db_path is None:
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, 'scheduler.db')
            
        self.db_path = db_path
        self.running = False
        self.thread = None
        self._init_database()
        logger.info(f"Scheduler database: {self.db_path}")
        
    def _init_database(self):
        """Initialize the scheduler database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create schedules table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                query TEXT NOT NULL,
                limit_leads INTEGER DEFAULT 25,
                verify_emails BOOLEAN DEFAULT 0,
                interval_hours INTEGER DEFAULT 24,
                next_run TIMESTAMP,
                last_run TIMESTAMP,
                enabled BOOLEAN DEFAULT 1,
                output_format TEXT DEFAULT 'csv',
                integrations TEXT,  -- JSON array of integration configs
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create search history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                schedule_id INTEGER,
                query TEXT NOT NULL,
                leads_found INTEGER DEFAULT 0,
                emails_found INTEGER DEFAULT 0,
                emails_valid INTEGER DEFAULT 0,
                file_path TEXT,
                status TEXT DEFAULT 'pending',
                error_message TEXT,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (schedule_id) REFERENCES schedules(id)
            )
        ''')
        
        # Create search queue table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                limit_leads INTEGER DEFAULT 25,
                verify_emails BOOLEAN DEFAULT 0,
                priority INTEGER DEFAULT 5,
                status TEXT DEFAULT 'pending',
                schedule_id INTEGER,
                scheduled_time TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                result_file TEXT,
                error_message TEXT,
                FOREIGN KEY (schedule_id) REFERENCES schedules(id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def add_schedule(self, name: str, query: str, limit_leads: int = 25, 
                    verify_emails: bool = False, interval_hours: int = 24,
                    integrations: List[Dict] = None) -> int:
        """Add a new scheduled search"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        next_run = datetime.now() + timedelta(hours=interval_hours)
        integrations_json = json.dumps(integrations) if integrations else '[]'
        
        cursor.execute('''
            INSERT INTO schedules (name, query, limit_leads, verify_emails, 
                                  interval_hours, next_run, integrations)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (name, query, limit_leads, verify_emails, interval_hours, 
              next_run, integrations_json))
        
        schedule_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Added schedule {schedule_id}: {name}")
        return schedule_id
        
    def update_schedule(self, schedule_id: int, **kwargs) -> bool:
        """Update an existing schedule"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Build update query
        updates = []
        values = []
        for key, value in kwargs.items():
            if key in ['name', 'query', 'limit_leads', 'verify_emails', 
                      'interval_hours', 'enabled', 'integrations']:
                if key == 'integrations':
                    value = json.dumps(value)
                updates.append(f"{key} = ?")
                values.append(value)
        
        if not updates:
            return False
            
        values.append(schedule_id)
        query = f"UPDATE schedules SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
        
        cursor.execute(query, values)
        conn.commit()
        conn.close()
        
        return cursor.rowcount > 0
        
    def delete_schedule(self, schedule_id: int) -> bool:
        """Delete a schedule"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM schedules WHERE id = ?", (schedule_id,))
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        
        return success
        
    def get_schedules(self, enabled_only: bool = False) -> List[Dict]:
        """Get all schedules"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if enabled_only:
            cursor.execute("SELECT * FROM schedules WHERE enabled = 1 ORDER BY next_run")
        else:
            cursor.execute("SELECT * FROM schedules ORDER BY next_run")
            
        schedules = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        # Parse integrations JSON
        for schedule in schedules:
            if schedule.get('integrations'):
                schedule['integrations'] = json.loads(schedule['integrations'])
                
        return schedules
        
    def get_schedule(self, schedule_id: int) -> Optional[Dict]:
        """Get a specific schedule"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM schedules WHERE id = ?", (schedule_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            schedule = dict(row)
            if schedule.get('integrations'):
                schedule['integrations'] = json.loads(schedule['integrations'])
            return schedule
        return None
        
    def add_to_queue(self, query: str, limit_leads: int = 25, 
                    verify_emails: bool = False, priority: int = 5,
                    schedule_id: Optional[int] = None, 
                    scheduled_time: Optional[datetime] = None) -> int:
        """Add a search to the queue"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO search_queue (query, limit_leads, verify_emails, priority, schedule_id, scheduled_time)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (query, limit_leads, verify_emails, priority, schedule_id, scheduled_time))
        
        queue_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Added to queue {queue_id}: {query}")
        return queue_id
        
    def get_queue(self, status: str = None) -> List[Dict]:
        """Get items from the queue"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if status:
            cursor.execute(
                "SELECT * FROM search_queue WHERE status = ? ORDER BY priority DESC, created_at",
                (status,)
            )
        else:
            cursor.execute("SELECT * FROM search_queue ORDER BY priority DESC, created_at")
            
        items = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return items
        
    def cancel_queue_item(self, queue_id: int) -> bool:
        """Cancel a specific queue item"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM queue 
            WHERE id = ? AND status = 'pending'
        ''', (queue_id,))
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()
        return deleted
    
    def clear_queue(self) -> int:
        """Clear all pending queue items"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM queue 
            WHERE status = 'pending'
        ''')
        count = cursor.rowcount
        conn.commit()
        conn.close()
        return count
        
    def get_next_queue_item(self) -> Optional[Dict]:
        """Get the next item to process from the queue"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM search_queue 
            WHERE status = 'pending' 
            AND (scheduled_time IS NULL OR scheduled_time <= ?)
            ORDER BY scheduled_time ASC, created_at ASC 
            LIMIT 1
        ''', (datetime.now(),))
        
        row = cursor.fetchone()
        
        if row:
            item = dict(row)
            # Mark as processing
            cursor.execute(
                "UPDATE search_queue SET status = 'processing', started_at = ? WHERE id = ?",
                (datetime.now(), item['id'])
            )
            conn.commit()
            conn.close()
            return item
            
        conn.close()
        return None
        
    def update_queue_item(self, queue_id: int, status: str, 
                         result_file: str = None, error_message: str = None):
        """Update a queue item's status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if status == 'completed':
            cursor.execute('''
                UPDATE search_queue 
                SET status = ?, completed_at = ?, result_file = ?
                WHERE id = ?
            ''', (status, datetime.now(), result_file, queue_id))
        elif status == 'error':
            cursor.execute('''
                UPDATE search_queue 
                SET status = ?, completed_at = ?, error_message = ?
                WHERE id = ?
            ''', (status, datetime.now(), error_message, queue_id))
        else:
            cursor.execute(
                "UPDATE search_queue SET status = ? WHERE id = ?",
                (status, queue_id)
            )
            
        conn.commit()
        conn.close()
        
    def get_history(self, schedule_id: int = None, limit: int = 100) -> List[Dict]:
        """Get search history"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if schedule_id:
            cursor.execute(
                "SELECT * FROM search_history WHERE schedule_id = ? ORDER BY started_at DESC LIMIT ?",
                (schedule_id, limit)
            )
        else:
            cursor.execute(
                "SELECT * FROM search_history ORDER BY started_at DESC LIMIT ?",
                (limit,)
            )
            
        history = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return history
        
    def add_history(self, query: str, schedule_id: int = None, **kwargs) -> int:
        """Add a search to history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO search_history (schedule_id, query, leads_found, emails_found, 
                                       emails_valid, file_path, status, error_message,
                                       started_at, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            schedule_id, query, 
            kwargs.get('leads_found', 0),
            kwargs.get('emails_found', 0),
            kwargs.get('emails_valid', 0),
            kwargs.get('file_path'),
            kwargs.get('status', 'completed'),
            kwargs.get('error_message'),
            kwargs.get('started_at', datetime.now()),
            kwargs.get('completed_at', datetime.now())
        ))
        
        history_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return history_id
        
    def check_due_schedules(self) -> List[Dict]:
        """Check for schedules that are due to run"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM schedules 
            WHERE enabled = 1 AND next_run <= ?
            ORDER BY next_run
        ''', (datetime.now(),))
        
        due_schedules = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return due_schedules
        
    def update_next_run(self, schedule_id: int):
        """Update the next run time for a schedule"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get current schedule
        cursor.execute("SELECT interval_hours FROM schedules WHERE id = ?", (schedule_id,))
        row = cursor.fetchone()
        
        if row:
            interval_hours = row[0]
            next_run = datetime.now() + timedelta(hours=interval_hours)
            
            cursor.execute('''
                UPDATE schedules 
                SET next_run = ?, last_run = ?
                WHERE id = ?
            ''', (next_run, datetime.now(), schedule_id))
            
            conn.commit()
            
        conn.close()
        
    def start(self, process_callback=None):
        """Start the scheduler background thread"""
        if self.running:
            logger.warning("Scheduler already running")
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler, args=(process_callback,))
        self.thread.daemon = True
        self.thread.start()
        logger.info("Scheduler started")
        
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Scheduler stopped")
        
    def _run_scheduler(self, process_callback=None):
        """Main scheduler loop"""
        while self.running:
            try:
                # Check for due schedules
                due_schedules = self.check_due_schedules()
                for schedule in due_schedules:
                    logger.info(f"Running scheduled search: {schedule['name']}")
                    
                    # Add to queue
                    self.add_to_queue(
                        query=schedule['query'],
                        limit_leads=schedule['limit_leads'],
                        verify_emails=schedule['verify_emails'],
                        priority=10,  # High priority for scheduled searches
                        schedule_id=schedule['id']
                    )
                    
                    # Update next run time
                    self.update_next_run(schedule['id'])
                
                # Process queue items
                item = self.get_next_queue_item()
                if item and process_callback:
                    try:
                        # Process the search
                        result = process_callback(
                            query=item['query'],
                            limit=item['limit_leads'],
                            verify_emails=item['verify_emails']
                        )
                        
                        # Update queue item
                        self.update_queue_item(
                            item['id'], 
                            'completed',
                            result_file=result.get('file_path')
                        )
                        
                        # Add to history
                        self.add_history(
                            query=item['query'],
                            schedule_id=item.get('schedule_id'),
                            leads_found=result.get('leads_found', 0),
                            emails_found=result.get('emails_found', 0),
                            emails_valid=result.get('emails_valid', 0),
                            file_path=result.get('file_path'),
                            status='completed'
                        )
                        
                        # Process integrations if this was a scheduled search
                        if item.get('schedule_id'):
                            schedule = self.get_schedule(item['schedule_id'])
                            if schedule and schedule.get('integrations'):
                                self._process_integrations(
                                    result.get('file_path'),
                                    schedule['integrations']
                                )
                                
                    except Exception as e:
                        logger.error(f"Error processing queue item {item['id']}: {e}")
                        self.update_queue_item(
                            item['id'],
                            'error',
                            error_message=str(e)
                        )
                
                # Sleep for a bit
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(60)  # Wait longer on error
                
    def _process_integrations(self, file_path: str, integrations: List[Dict]):
        """Process integrations for completed searches"""
        for integration in integrations:
            try:
                if integration['type'] == 'instantly':
                    self._push_to_instantly(file_path, integration)
                elif integration['type'] == 'webhook':
                    self._push_to_webhook(file_path, integration)
                elif integration['type'] == 'email':
                    self._send_email_notification(file_path, integration)
                    
            except Exception as e:
                logger.error(f"Integration error ({integration['type']}): {e}")
                
    def _push_to_instantly(self, file_path: str, config: Dict):
        """Push leads to Instantly.ai"""
        # TODO: Implement Instantly.ai integration
        api_key = config.get('api_key')
        campaign_id = config.get('campaign_id')
        
        logger.info(f"Would push {file_path} to Instantly campaign {campaign_id}")
        
    def _push_to_webhook(self, file_path: str, config: Dict):
        """Send data to a webhook"""
        webhook_url = config.get('url')
        
        # Read the CSV and convert to JSON
        import pandas as pd
        df = pd.read_csv(file_path)
        data = df.to_dict('records')
        
        response = requests.post(webhook_url, json={
            'leads': data,
            'file_path': file_path,
            'timestamp': datetime.now().isoformat()
        })
        
        if response.status_code != 200:
            raise Exception(f"Webhook failed: {response.status_code}")
            
        logger.info(f"Pushed {len(data)} leads to webhook {webhook_url}")
        
    def _send_email_notification(self, file_path: str, config: Dict):
        """Send email notification when search completes"""
        # TODO: Implement email notification
        recipient = config.get('recipient')
        logger.info(f"Would email {file_path} to {recipient}")