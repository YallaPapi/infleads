#!/usr/bin/env python3
"""Clear all pending queue items"""

import requests
import json

# Get all queue items
response = requests.get('http://localhost:5000/api/queue')
queue_items = response.json()

# Count items by status
pending = [item for item in queue_items if item['status'] == 'pending']
processing = [item for item in queue_items if item['status'] == 'processing']

print(f"Found {len(queue_items)} total queue items:")
print(f"  - {len(pending)} pending")
print(f"  - {len(processing)} processing")
print(f"  - {len([i for i in queue_items if i['status'] == 'completed'])} completed")

# Clear pending items
if pending:
    print(f"\nClearing {len(pending)} pending items...")
    for item in pending:
        response = requests.delete(f'http://localhost:5000/api/queue/{item["id"]}')
        if response.status_code == 200:
            print(f"  Deleted queue item {item['id']}: {item['query']}")
        else:
            print(f"  Failed to delete item {item['id']}")

print("\nDone! Remaining queue items are either processing or completed.")
print("\nNote: The currently processing item will complete on its own.")