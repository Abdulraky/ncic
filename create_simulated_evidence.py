#!/usr/bin/env python
"""Create simulated evidence data for end-to-end workflow testing"""
import sqlite3
import json
from datetime import datetime, timedelta
import hashlib

# Initialize evidence database
archive_db = "data/evidence_archive/evidence_manifest.db"
conn = sqlite3.connect(archive_db)
cursor = conn.cursor()

# Create a test collection
cursor.execute("""
    INSERT INTO evidence_collection (official_id, official_name, collection_date, status)
    VALUES (?, ?, ?, ?)
""", ('OFF001', 'John Mwangi', datetime.now().isoformat(), 'completed'))
conn.commit()

# Get the collection ID
cursor.execute("SELECT MAX(id) FROM evidence_collection")
collection_id = cursor.fetchone()[0]

# Create simulated posts
test_posts = [
    {
        'platform': 'twitter',
        'username': 'JohnMwangi',
        'post_id': 'tw_001',
        'text': 'Proud to announce new infrastructure projects for Nairobi. #Development',
        'url': 'https://twitter.com/JohnMwangi/status/123456',
        'timestamp': (datetime.now() - timedelta(days=1)).isoformat(),
        'author': 'John Mwangi',
        'verified': True,
        'likes': 1250
    },
    {
        'platform': 'twitter',
        'username': 'JohnMwangi',
        'post_id': 'tw_002',
        'text': 'Thank you all for the support during the election campaign. Together we build.',
        'url': 'https://twitter.com/JohnMwangi/status/123457',
        'timestamp': (datetime.now() - timedelta(days=2)).isoformat(),
        'author': 'John Mwangi',
        'verified': True,
        'likes': 2100
    },
    {
        'platform': 'instagram',
        'username': 'johnmwangi',
        'post_id': 'ig_001',
        'text': 'Visit to Kibera settlement - engaging with constituents',
        'url': 'https://instagram.com/p/ABC123',
        'timestamp': (datetime.now() - timedelta(days=3)).isoformat(),
        'author': 'John Mwangi',
        'verified': False,
        'likes': 5430
    },
    {
        'platform': 'tiktok',
        'username': '@johnmwangi',
        'post_id': 'tt_001',
        'text': 'Behind the scenes of governance - meet the team',
        'url': 'https://www.tiktok.com/@johnmwangi/video/123456',
        'timestamp': (datetime.now() - timedelta(days=4)).isoformat(),
        'author': 'John Mwangi',
        'verified': False,
        'likes': 8900
    }
]

# Store simulated posts with hashing
for post in test_posts:
    post_json = json.dumps(post)
    sha256_hash = hashlib.sha256(post_json.encode()).hexdigest()
    md5_hash = hashlib.md5(post_json.encode()).hexdigest()
    
    cursor.execute("""
        INSERT INTO evidence_items (
            collection_id, item_type, source_url,
            sha256_hash, md5_hash, file_size_bytes,
            mime_type, captured_date, file_path
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        collection_id,
        'social_media_post',
        post['url'],
        sha256_hash,
        md5_hash,
        len(post_json),
        'application/json',
        post['timestamp'],
        None
    ))

conn.commit()
conn.close()

print(f"✅ Created simulated evidence collection (ID: {collection_id})")
print(f"✅ Inserted {len(test_posts)} test posts from 3 platforms:")
for platform in ['twitter', 'instagram', 'tiktok']:
    count = len([p for p in test_posts if p['platform'] == platform])
    print(f"   - {platform.capitalize()}: {count} posts")
print(f"\n✅ Ready for Module 3 (Authenticity Verification) testing")
