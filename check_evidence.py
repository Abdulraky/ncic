"""
Check evidence database
"""
import sqlite3
from pathlib import Path

db_path = Path("data/evidence_archive/evidence_manifest.db")
if db_path.exists():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("=== Evidence Database Tables ===")
    for table in tables:
        table_name = table[0]
        print(f"  - {table_name}")
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"    Rows: {count}")
    
    conn.close()
else:
    print("No evidence database found")
