import sqlite3

conn = sqlite3.connect('data/scheduler.db')
cursor = conn.cursor()

cursor.execute("""
    SELECT id, query, verify_emails, generate_emails 
    FROM search_queue 
    WHERE id >= 46
    ORDER BY id DESC
    LIMIT 5
""")

results = cursor.fetchall()
print("ID | Query | Verify Emails | Generate Emails")
print("-" * 60)
for row in results:
    print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]}")

conn.close()