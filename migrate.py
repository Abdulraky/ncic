"""
Phase 2 - Step 1: Data Migration Script
Migrates data from old SQLite databases to new ORM schema
"""
import sqlite3
from pathlib import Path
from datetime import datetime
import json

from database import SessionLocal, init_db
from models import Official, EvidenceCollection, EvidenceItem, VerificationResult
from services import PoliticianService, EvidenceService

print("=" * 60)
print("PHASE 2 - DATA MIGRATION")
print("=" * 60)

# Initialize new database
print("\n[1/4] Initializing new database schema...")
init_db()
print("✓ Database initialized")

# Get session
db = SessionLocal()

# ──────────────────────────────────────────────────────────────────────────────
# MIGRATE OFFICIALS
# ──────────────────────────────────────────────────────────────────────────────
print("\n[2/4] Migrating officials...")
old_officials_db = Path("data/officials.db")

if old_officials_db.exists():
    old_conn = sqlite3.connect(old_officials_db)
    old_cursor = old_conn.cursor()
    
    old_cursor.execute("""
        SELECT official_id, name, office, county, constituency, party,
               verified_x, twitter, facebook, youtube, tiktok, instagram, 
               website, active, created_at
        FROM officials
    """)
    
    officials = old_cursor.fetchall()
    migrated = 0
    
    for official in officials:
        official_id, name, office, county, constituency, party, verified_x, \
        twitter, facebook, youtube, tiktok, instagram, website, active, created_at = official
        
        try:
            new_official = Official(
                official_id=official_id,
                name=name,
                office=office,
                county=county,
                constituency=constituency,
                party=party,
                verified_x=bool(verified_x),
                twitter=twitter,
                facebook=facebook,
                youtube=youtube,
                tiktok=tiktok,
                instagram=instagram,
                website=website,
                active=bool(active),
                created_at=datetime.fromisoformat(created_at) if created_at else datetime.utcnow()
            )
            db.add(new_official)
            migrated += 1
        except Exception as e:
            print(f"  ⚠ Error migrating {official_id}: {e}")
    
    db.commit()
    old_conn.close()
    print(f"✓ Migrated {migrated} officials")
else:
    print("❌ Old officials database not found")

# ──────────────────────────────────────────────────────────────────────────────
# MIGRATE EVIDENCE
# ──────────────────────────────────────────────────────────────────────────────
print("\n[3/4] Migrating evidence collections and items...")
old_evidence_db = Path("data/evidence_archive/evidence_manifest.db")

if old_evidence_db.exists():
    old_conn = sqlite3.connect(old_evidence_db)
    old_cursor = old_conn.cursor()
    
    # Get collections
    old_cursor.execute("""
        SELECT id, official_id, official_name, collection_date, status, 
               post_count, media_count, total_size_bytes, archive_path
        FROM evidence_collection
    """)
    
    collections = old_cursor.fetchall()
    collection_map = {}  # Map old ID to new ID
    
    for collection in collections:
        old_id, official_id, official_name, collection_date, status, \
        post_count, media_count, total_size_bytes, archive_path = collection
        
        try:
            new_collection = EvidenceCollection(
                official_id=official_id,
                official_name=official_name,
                collection_date=datetime.fromisoformat(collection_date) if collection_date else datetime.utcnow(),
                status=status,
                post_count=post_count,
                media_count=media_count,
                total_size_bytes=total_size_bytes,
                archive_path=archive_path
            )
            db.add(new_collection)
            db.flush()
            collection_map[old_id] = new_collection.id
        except Exception as e:
            print(f"  ⚠ Error migrating collection {old_id}: {e}")
    
    db.commit()
    print(f"✓ Migrated {len(collection_map)} evidence collections")
    
    # Get items
    old_cursor.execute("""
        SELECT id, collection_id, item_type, source_url, file_path,
               sha256_hash, md5_hash, file_size_bytes, mime_type, captured_date
        FROM evidence_items
    """)
    
    items = old_cursor.fetchall()
    migrated_items = 0
    
    for item in items:
        old_id, old_collection_id, item_type, source_url, file_path, \
        sha256_hash, md5_hash, file_size_bytes, mime_type, captured_date = item
        
        new_collection_id = collection_map.get(old_collection_id)
        
        if not new_collection_id:
            print(f"  ⚠ Skipping item {old_id}: collection {old_collection_id} not found")
            continue
        
        try:
            new_item = EvidenceItem(
                collection_id=new_collection_id,
                item_type=item_type,
                source_url=source_url,
                file_path=file_path,
                sha256_hash=sha256_hash,
                md5_hash=md5_hash,
                file_size_bytes=file_size_bytes,
                mime_type=mime_type,
                captured_date=datetime.fromisoformat(captured_date) if captured_date else None
            )
            db.add(new_item)
            migrated_items += 1
        except Exception as e:
            print(f"  ⚠ Error migrating item {old_id}: {e}")
    
    db.commit()
    old_conn.close()
    print(f"✓ Migrated {migrated_items} evidence items")
else:
    print("❌ Old evidence database not found")

# ──────────────────────────────────────────────────────────────────────────────
# VERIFY MIGRATION
# ──────────────────────────────────────────────────────────────────────────────
print("\n[4/4] Verifying migration...")
officials_count = db.query(Official).count()
collections_count = db.query(EvidenceCollection).count()
items_count = db.query(EvidenceItem).count()

print(f"✓ New database contains:")
print(f"  - {officials_count} officials")
print(f"  - {collections_count} evidence collections")
print(f"  - {items_count} evidence items")

db.close()

print("\n" + "=" * 60)
print("✅ MIGRATION COMPLETE")
print("=" * 60)
print("\nNext steps:")
print("  1. Test end-to-end workflow with new app.py")
print("  2. Verify all data accessible through services")
print("  3. Refactor existing modules to use new services")
