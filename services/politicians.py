"""Service for managing politicians/officials"""
from sqlalchemy.orm import Session
from models import Official
import logging

logger = logging.getLogger(__name__)


class PoliticianService:
    """Business logic for official/politician management"""

    @staticmethod
    def add_official(db: Session, official_data: dict) -> Official:
        """Add a new official to the database"""
        try:
            official = Official(**official_data)
            db.add(official)
            db.commit()
            db.refresh(official)
            logger.info(f"Added official: {official.name}")
            return official
        except Exception as e:
            db.rollback()
            logger.error(f"Error adding official: {e}")
            raise

    @staticmethod
    def get_all_officials(db: Session) -> list:
        """Get all officials"""
        return db.query(Official).all()

    @staticmethod
    def get_official(db: Session, official_id: str) -> Official:
        """Get a specific official by ID"""
        return db.query(Official).filter(Official.official_id == official_id).first()

    @staticmethod
    def get_officials_by_county(db: Session, county: str) -> list:
        """Get officials by county"""
        return db.query(Official).filter(Official.county == county).all()

    @staticmethod
    def get_officials_by_party(db: Session, party: str) -> list:
        """Get officials by party"""
        return db.query(Official).filter(Official.party == party).all()

    @staticmethod
    def update_official(db: Session, official_id: str, update_data: dict) -> Official:
        """Update an official"""
        try:
            official = PoliticianService.get_official(db, official_id)
            if not official:
                raise ValueError(f"Official not found: {official_id}")
            
            for key, value in update_data.items():
                setattr(official, key, value)
            
            db.commit()
            db.refresh(official)
            logger.info(f"Updated official: {official_id}")
            return official
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating official: {e}")
            raise

    @staticmethod
    def delete_official(db: Session, official_id: str) -> bool:
        """Delete an official"""
        try:
            official = PoliticianService.get_official(db, official_id)
            if not official:
                raise ValueError(f"Official not found: {official_id}")
            
            db.delete(official)
            db.commit()
            logger.info(f"Deleted official: {official_id}")
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting official: {e}")
            raise

    @staticmethod
    def get_verified_count(db: Session) -> int:
        """Get count of verified officials"""
        return db.query(Official).filter(Official.verified_x == True).count()

    @staticmethod
    def get_with_social_media_count(db: Session) -> int:
        """Get count of officials with social media handles"""
        from sqlalchemy import or_
        return db.query(Official).filter(
            or_(
                Official.twitter != None,
                Official.facebook != None,
                Official.instagram != None,
                Official.tiktok != None
            )
        ).count()

    @staticmethod
    def get_active_count(db: Session) -> int:
        """Get count of active officials"""
        return db.query(Official).filter(Official.active == True).count()

    @staticmethod
    def get_unique_counties(db: Session) -> list:
        """Get list of unique counties"""
        return [row[0] for row in db.query(Official.county).distinct().all() if row[0]]

    @staticmethod
    def import_from_csv(db: Session, csv_data: list) -> int:
        """Bulk import officials from CSV data"""
        count = 0
        try:
            for row in csv_data:
                existing = PoliticianService.get_official(db, row.get("official_id"))
                if not existing:
                    PoliticianService.add_official(db, row)
                    count += 1
            logger.info(f"Imported {count} officials from CSV")
            return count
        except Exception as e:
            db.rollback()
            logger.error(f"Error importing officials: {e}")
            raise
