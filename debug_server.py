#!/usr/bin/env python3
"""
Simple debug server for real-time log monitoring
"""

from flask import Flask, jsonify
from flask_cors import CORS
import os
import time
import threading

app = Flask(__name__)
CORS(app)

@app.route('/api/logs')
def get_logs():
    """Get recent logs from the main app"""
    recent_logs = []
    try:
        log_file = 'logs/flask_app.log'
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                lines = f.readlines()[-100:]  # Get last 100 lines
                for line in lines:
                    recent_logs.append(line.strip())
        else:
            recent_logs = ["Log file not found - app may not be running"]
    except Exception as e:
        recent_logs = [f"Error reading log file: {str(e)}"]
    
    return jsonify({
        "status": "working",
        "timestamp": time.time(),
        "recent_logs": recent_logs,
        "log_count": len(recent_logs)
    })

@app.route('/api/test')
def test():
    """Test endpoint"""
    return {"status": "debug server working", "timestamp": time.time()}

if __name__ == '__main__':
    print("Debug Server Starting on http://localhost:5001")
    print("Test endpoint: http://localhost:5001/api/test")
    print("Logs endpoint: http://localhost:5001/api/logs")
    app.run(host='127.0.0.1', port=5001, debug=False)