#!/usr/bin/env python3
"""
Add generate_emails column to scheduler database
"""

import sqlite3
import os

def migrate_database():
    db_path = 'data/scheduler.db'
    
    if not os.path.exists(db_path):
        print(f"Database {db_path} does not exist")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(search_queue)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'generate_emails' not in columns:
            print("Adding generate_emails column to search_queue table...")
            cursor.execute('''
                ALTER TABLE search_queue 
                ADD COLUMN generate_emails BOOLEAN DEFAULT 0
            ''')
            conn.commit()
            print("[OK] Added generate_emails column to search_queue")
        else:
            print("generate_emails column already exists")
            
        # Check schedules table too
        cursor.execute("PRAGMA table_info(schedules)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'generate_emails' not in columns:
            print("Adding generate_emails column to schedules table...")
            cursor.execute('''
                ALTER TABLE schedules 
                ADD COLUMN generate_emails BOOLEAN DEFAULT 0
            ''')
            conn.commit()
            print("[OK] Added generate_emails column to schedules")
        else:
            print("generate_emails column already exists in schedules")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()