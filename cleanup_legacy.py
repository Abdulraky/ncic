#!/usr/bin/env python3
"""
Remove the 5 legacy officials from the database
Keep only the 218 officials from Government Roster
"""
import logging
from database import SessionLocal
from models.politician import Official
from models.evidence import EvidenceCollection, EvidenceItem

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def remove_legacy_officials():
    """Remove the 5 legacy test officials and their associated data"""
    
    db = SessionLocal()
    
    try:
        # The 5 legacy officials to remove
        legacy_names = [
            "John Mwangi",
            "Jane Muthoni", 
            "Peter Kipchoge",
            "Mary Kiplagat",
            "Mike Murithi"
        ]
        
        removed_count = 0
        collections_removed = 0
        items_removed = 0
        
        for name in legacy_names:
            official = db.query(Official).filter(Official.name == name).first()
            if official:
                # Delete associated evidence items first
                collections = db.query(EvidenceCollection).filter(
                    EvidenceCollection.official_id == official.official_id
                ).all()
                
                for collection in collections:
                    items = db.query(EvidenceItem).filter(
                        EvidenceItem.collection_id == collection.id
                    ).all()
                    for item in items:
                        db.delete(item)
                        items_removed += 1
                    
                    db.delete(collection)
                    collections_removed += 1
                
                # Now delete the official
                db.delete(official)
                removed_count += 1
                logger.info(f"Removed: {name}")
        
        db.commit()
        
        # Show final counts
        total = db.query(Official).count()
        with_twitter = db.query(Official).filter(
            Official.twitter.isnot(None),
            Official.twitter != ''
        ).count()
        
        logger.info("=" * 60)
        logger.info("CLEANUP COMPLETE")
        logger.info("=" * 60)
        logger.info(f"✅ Removed officials: {removed_count}")
        logger.info(f"✅ Removed collections: {collections_removed}")
        logger.info(f"✅ Removed items: {items_removed}")
        logger.info(f"📊 Total officials remaining: {total}")
        logger.info(f"🐦 With Twitter handles: {with_twitter}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    remove_legacy_officials()
