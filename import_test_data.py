#!/usr/bin/env python
"""Import test officials data"""
import pandas as pd
from officials_db import OfficialsDatabase

# Read the test CSV
df = pd.read_csv('test_officials.csv')

# Initialize database
db = OfficialsDatabase("data/officials.db")

# Import each official
for _, row in df.iterrows():
    official_data = row.to_dict()
    success, message = db.add_official(official_data)
    print(f"{message}")

# Verify import
db.close()
db = OfficialsDatabase("data/officials.db")
officials = db.get_all_officials()
print(f"\n✅ Imported {len(officials)} officials")
for official in officials:
    print(f"  - {official['name']} ({official['office']}) | Twitter: {official.get('twitter', 'N/A')}")
db.close()
