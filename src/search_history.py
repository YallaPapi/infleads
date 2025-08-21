"""
Search History and Favorites Management
Stores search history and favorite searches in SQLite database
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
import os

class SearchHistoryManager:
    def __init__(self, db_path: str = 'data/search_history.db'):
        """Initialize the search history manager with SQLite database"""
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Create tables if they don't exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Search history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    limit_leads INTEGER,
                    verify_emails BOOLEAN,
                    generate_emails BOOLEAN,
                    export_verified_only BOOLEAN,
                    advanced_scraping BOOLEAN,
                    results_count INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Favorite searches table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS favorite_searches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    query TEXT NOT NULL,
                    limit_leads INTEGER,
                    verify_emails BOOLEAN,
                    generate_emails BOOLEAN,
                    export_verified_only BOOLEAN,
                    advanced_scraping BOOLEAN,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Search suggestions table (for autocomplete)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS search_suggestions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    keyword TEXT UNIQUE NOT NULL,
                    frequency INTEGER DEFAULT 1,
                    last_used DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
    
    def add_search(self, query: str, limit_leads: int = 25, verify_emails: bool = True,
                   generate_emails: bool = False, export_verified_only: bool = False,
                   advanced_scraping: bool = False, results_count: int = 0):
        """Add a search to history"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO search_history 
                (query, limit_leads, verify_emails, generate_emails, 
                 export_verified_only, advanced_scraping, results_count)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (query, limit_leads, verify_emails, generate_emails,
                  export_verified_only, advanced_scraping, results_count))
            
            # Update search suggestions
            self._update_suggestions(query)
            conn.commit()
    
    def _update_suggestions(self, query: str):
        """Update search suggestions based on query"""
        # Extract keywords from query
        keywords = query.lower().split()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for keyword in keywords:
                if len(keyword) > 2:  # Only store keywords with 3+ characters
                    cursor.execute('''
                        INSERT INTO search_suggestions (keyword, frequency, last_used)
                        VALUES (?, 1, CURRENT_TIMESTAMP)
                        ON CONFLICT(keyword) DO UPDATE SET
                        frequency = frequency + 1,
                        last_used = CURRENT_TIMESTAMP
                    ''', (keyword,))
    
    def get_history(self, limit: int = 50) -> List[Dict]:
        """Get recent search history"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM search_history 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_suggestions(self, prefix: str, limit: int = 10) -> List[str]:
        """Get search suggestions based on prefix"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT keyword FROM search_suggestions
                WHERE keyword LIKE ?
                ORDER BY frequency DESC, last_used DESC
                LIMIT ?
            ''', (f'{prefix}%', limit))
            return [row[0] for row in cursor.fetchall()]
    
    def add_favorite(self, name: str, query: str, limit_leads: int = 25,
                    verify_emails: bool = True, generate_emails: bool = False,
                    export_verified_only: bool = False, advanced_scraping: bool = False):
        """Add a favorite search"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO favorite_searches
                (name, query, limit_leads, verify_emails, generate_emails,
                 export_verified_only, advanced_scraping)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (name, query, limit_leads, verify_emails, generate_emails,
                  export_verified_only, advanced_scraping))
            conn.commit()
            return cursor.lastrowid
    
    def get_favorites(self) -> List[Dict]:
        """Get all favorite searches"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM favorite_searches ORDER BY created_at DESC')
            return [dict(row) for row in cursor.fetchall()]
    
    def delete_favorite(self, favorite_id: int):
        """Delete a favorite search"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM favorite_searches WHERE id = ?', (favorite_id,))
            conn.commit()
    
    def get_popular_searches(self, limit: int = 10) -> List[Dict]:
        """Get most popular searches based on frequency"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT query, COUNT(*) as count, MAX(timestamp) as last_used
                FROM search_history
                GROUP BY query
                ORDER BY count DESC, last_used DESC
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    def clear_history(self, older_than_days: int = 30):
        """Clear old search history"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM search_history
                WHERE timestamp < datetime('now', ? || ' days')
            ''', (-older_than_days,))
            conn.commit()
            return cursor.rowcount