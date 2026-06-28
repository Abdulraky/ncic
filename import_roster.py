#!/usr/bin/env python3
"""
Import Government Roster Master List into the database
Loads 218 officials from the June 2026 roster
"""
import pandas as pd
import logging
from pathlib import Path
from database import SessionLocal, init_db
from models.politician import Official
from services.politicians import PoliticianService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_official_id(name: str, office: str) -> str:
    """Generate a unique official_id from name and office"""
    import hashlib
    combined = f"{name}-{office}".lower().strip()
    hash_obj = hashlib.md5(combined.encode())
    return hash_obj.hexdigest()[:16]

def import_government_roster():
    """Import officials from Government Roster Master List CSV"""
    
    # Read CSV
    csv_path = Path("data/Government Roster Master List - June 2026.csv")
    if not csv_path.exists():
        logger.error(f"CSV file not found: {csv_path}")
        return
    
    df = pd.read_csv(csv_path)
    logger.info(f"Loaded {len(df)} officials from {csv_path}")
    
    # Initialize database
    init_db()
    db = SessionLocal()
    
    try:
        imported = 0
        skipped = 0
        
        for idx, row in df.iterrows():
            try:
                name = row['Official Name'].strip()
                office = row['Designated Office / Role'].strip()
                twitter_handle = row['Twitter Handle'].strip() if pd.notna(row['Twitter Handle']) else None
                
                # Generate unique ID
                official_id = generate_official_id(name, office)
                
                # Check if already exists
                existing = db.query(Official).filter(Official.official_id == official_id).first()
                if existing:
                    skipped += 1
                    continue
                
                # Create official
                official = Official(
                    official_id=official_id,
                    name=name,
                    office=office,
                    twitter=twitter_handle,
                    verified_x=bool(twitter_handle),  # Mark as verified if has Twitter
                    active=True
                )
                
                db.add(official)
                imported += 1
                
                if imported % 50 == 0:
                    logger.info(f"Imported {imported} officials...")
                
            except Exception as e:
                logger.error(f"Error importing row {idx}: {e}")
                continue
        
        # Commit all changes
        db.commit()
        
        # Show summary
        total = db.query(Official).count()
        with_twitter = db.query(Official).filter(Official.twitter.isnot(None)).count()
        
        logger.info("=" * 60)
        logger.info("IMPORT COMPLETE")
        logger.info("=" * 60)
        logger.info(f"✅ Imported: {imported} new officials")
        logger.info(f"⊘ Skipped: {skipped} duplicates")
        logger.info(f"📊 Total officials in database: {total}")
        logger.info(f"🐦 Officials with Twitter: {with_twitter}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Error during import: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    import_government_roster()
