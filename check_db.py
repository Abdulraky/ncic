"""
Check current database state
"""
import sqlite3
from pathlib import Path

db_path = Path("data/officials.db")
if db_path.exists():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("=== Tables in current database ===")
    for table in tables:
        print(f"  - {table[0]}")
        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cursor.fetchone()[0]
        print(f"    Rows: {count}")
    
    # Check officials
    cursor.execute("SELECT COUNT(*) FROM officials")
    officials_count = cursor.fetchone()[0]
    print(f"\n✓ Found {officials_count} officials in current database")
    
    # Check evidence
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%evidence%'")
    evidence_tables = cursor.fetchall()
    print(f"✓ Found {len(evidence_tables)} evidence-related tables")
    
    conn.close()
else:
    print("❌ No existing database found")
