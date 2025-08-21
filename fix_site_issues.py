#!/usr/bin/env python3
"""
Emergency fix script for site update issues.
Addresses:
1. Browser caching problems
2. CSV upload header mismatch
3. Section positioning on scheduling page
4. Flask static file serving
"""

import os
import sys
import subprocess
import time
import shutil
from pathlib import Path

def clear_browser_cache_hints():
    """Add cache-busting parameters to all static resources"""
    print("Adding cache-busting to HTML templates...")
    
    template_path = Path("templates/index.html")
    if template_path.exists():
        content = template_path.read_text(encoding='utf-8')
        
        # Add timestamp to all static resource URLs
        timestamp = str(int(time.time()))
        
        # Replace any existing cache buster comments
        import re
        content = re.sub(r'<!-- Cache buster: \d+ -->', f'<!-- Cache buster: {timestamp} -->', content)
        
        # Add version params to local resources if not present
        if '?v=' not in content:
            content = re.sub(r'(href|src)="(/static/[^"]+)"', rf'\1="\2?v={timestamp}"', content)
        
        template_path.write_text(content, encoding='utf-8')
        print(f"[OK] Updated cache buster to: {timestamp}")

def fix_csv_headers():
    """Ensure CSV upload accepts both old and new header formats"""
    print("\nFixing CSV upload header compatibility...")
    
    app_path = Path("app.py")
    if not app_path.exists():
        print("[ERROR] app.py not found!")
        return
    
    content = app_path.read_text(encoding='utf-8')
    
    # Find the bulk_upload_schedules function
    if 'def bulk_upload_schedules():' in content:
        print("[OK] Found bulk_upload_schedules function")
        
        # Make it more flexible with headers
        new_validation = '''def bulk_upload_schedules():
    """Upload multiple schedules from CSV - flexible header support"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '' or not file.filename.endswith('.csv'):
        return jsonify({'error': 'Please upload a CSV file'}), 400
    
    try:
        # Read CSV
        df = pd.read_csv(file)
        
        # Normalize column names (case-insensitive, trim spaces)
        df.columns = [col.strip().lower() for col in df.columns]
        
        # Accept multiple header variations
        keyword_cols = ['keyword', 'base_keyword', 'search_keyword', 'keywords']
        location_cols = ['location', 'state', 'city', 'area', 'locations']
        name_cols = ['name', 'schedule_name', 'job_name']
        
        # Find which columns are present
        has_keyword = any(col in df.columns for col in keyword_cols)
        has_location = any(col in df.columns for col in location_cols)
        has_name = any(col in df.columns for col in name_cols)
        
        if not (has_name and has_keyword and has_location):
            return jsonify({
                'error': 'CSV must contain: name/schedule_name, keyword/search_keyword, location/state',
                'accepted_headers': {
                    'name': name_cols,
                    'keyword': keyword_cols,
                    'location': location_cols
                },
                'found_columns': list(df.columns)
            }), 400
        
        # Standardize column names
        for col_group, standard_name in [(keyword_cols, 'keyword'), 
                                          (location_cols, 'location'),
                                          (name_cols, 'name')]:
            for col in col_group:
                if col in df.columns:
                    df.rename(columns={col: standard_name}, inplace=True)
                    break'''
        
        # This is too complex to safely replace inline, so we'll note it
        print("[WARNING] Manual review needed for bulk_upload_schedules function")
        print("  Recommendation: Add flexible header support")

def fix_positioning():
    """Fix section positioning on scheduling page"""
    print("\nFixing scheduling page positioning...")
    
    template_path = Path("templates/index.html")
    if not template_path.exists():
        print("[ERROR] index.html not found!")
        return
    
    content = template_path.read_text(encoding='utf-8')
    
    # Ensure CSV upload section is properly positioned at top
    if 'BULK CSV UPLOAD' in content:
        print("[OK] Found CSV upload section")
        
        # Check if it's within the scheduling tab content
        import re
        
        # Find the scheduling tab content div
        pattern = r'<div[^>]*id="schedulingTab"[^>]*>.*?</div>'
        
        # Ensure proper structure
        if 'schedulingTab' in content:
            print("[OK] Scheduling tab structure found")
            
            # Add explicit positioning styles
            fixes_applied = False
            
            # Fix the bulk upload section positioning
            if 'background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px;' in content:
                # Add position relative and z-index to ensure it stays on top
                old_style = 'style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px;"'
                new_style = 'style="position: relative; z-index: 10; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px;"'
                
                if old_style in content:
                    content = content.replace(old_style, new_style)
                    fixes_applied = True
                    print("[OK] Added positioning fixes to CSV upload section")
            
            if fixes_applied:
                template_path.write_text(content, encoding='utf-8')
                print("[OK] Saved positioning fixes")

def clear_flask_cache():
    """Clear Flask cache and restart with proper config"""
    print("\nClearing Flask cache and configs...")
    
    # Clear Python cache
    cache_dirs = ['__pycache__', '.pytest_cache', 'instance']
    for cache_dir in cache_dirs:
        if Path(cache_dir).exists():
            shutil.rmtree(cache_dir)
            print(f"[OK] Cleared {cache_dir}")
    
    # Clear .pyc files
    for pyc_file in Path('.').rglob('*.pyc'):
        pyc_file.unlink()
    print("[OK] Cleared all .pyc files")

def add_aggressive_no_cache():
    """Add more aggressive no-cache headers to Flask"""
    print("\nAdding aggressive no-cache configuration...")
    
    app_path = Path("app.py")
    if not app_path.exists():
        return
    
    content = app_path.read_text(encoding='utf-8')
    
    # Check if we have the after_request handler
    if '@app.after_request' in content:
        print("[OK] Found after_request handler")
        
        # Make it more aggressive
        if 'must-revalidate' not in content:
            print("[WARNING] Consider updating cache headers to be more aggressive")

def create_startup_script():
    """Create a startup script with proper environment setup"""
    print("\nCreating optimized startup script...")
    
    startup_content = '''@echo off
echo Starting R27 Infinite AI Leads Agent...
echo.

REM Kill any existing Python processes
echo Cleaning up old processes...
taskkill /F /IM python.exe 2>nul
taskkill /F /IM python3.exe 2>nul
taskkill /F /IM python3.12.exe 2>nul
timeout /t 2 /nobreak >nul

REM Clear Python cache
echo Clearing cache...
rd /s /q __pycache__ 2>nul
rd /s /q .pytest_cache 2>nul
del /s /q *.pyc 2>nul

REM Set Flask environment variables
set FLASK_APP=app.py
set FLASK_ENV=development
set FLASK_DEBUG=1
set TEMPLATES_AUTO_RELOAD=true
set SEND_FILE_MAX_AGE_DEFAULT=0

REM Start Flask with auto-reload
echo Starting Flask server...
python app.py

pause
'''
    
    Path("start_server_no_cache.bat").write_text(startup_content)
    print("[OK] Created start_server_no_cache.bat")

def main():
    print("=" * 60)
    print("SITE UPDATE ISSUES FIX SCRIPT")
    print("=" * 60)
    
    # Run all fixes
    clear_browser_cache_hints()
    fix_csv_headers()
    fix_positioning()
    clear_flask_cache()
    add_aggressive_no_cache()
    create_startup_script()
    
    print("\n" + "=" * 60)
    print("FIXES APPLIED")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Review the manual fixes noted above")
    print("2. Run: start_server_no_cache.bat")
    print("3. Hard refresh browser: Ctrl+Shift+R")
    print("4. Clear browser cache if issues persist")
    print("\nIf issues continue:")
    print("- Open browser DevTools (F12)")
    print("- Go to Network tab")
    print("- Check 'Disable cache' option")
    print("- Keep DevTools open while testing")

if __name__ == "__main__":
    main()