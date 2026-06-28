"""Service for managing evidence and archiving"""
from sqlalchemy.orm import Session
from models import EvidenceCollection, EvidenceItem
import logging

logger = logging.getLogger(__name__)


class EvidenceService:
    """Business logic for evidence management and archiving"""

    @staticmethod
    def create_collection(
        db: Session, 
        official_id: str, 
        official_name: str,
        status: str = "pending"
    ) -> EvidenceCollection:
        """Create a new evidence collection"""
        try:
            collection = EvidenceCollection(
                official_id=official_id,
                official_name=official_name,
                status=status
            )
            db.add(collection)
            db.commit()
            db.refresh(collection)
            logger.info(f"Created evidence collection for {official_name}")
            return collection
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating collection: {e}")
            raise

    @staticmethod
    def get_collection(db: Session, collection_id: int) -> EvidenceCollection:
        """Get a specific collection"""
        return db.query(EvidenceCollection).filter(
            EvidenceCollection.id == collection_id
        ).first()

    @staticmethod
    def get_collections_by_official(db: Session, official_id: str) -> list:
        """Get all collections for an official"""
        return db.query(EvidenceCollection).filter(
            EvidenceCollection.official_id == official_id
        ).all()

    @staticmethod
    def add_evidence_item(
        db: Session,
        collection_id: int,
        item_type: str,
        source_url: str,
        file_path: str = None,
        sha256_hash: str = None,
        md5_hash: str = None,
        file_size_bytes: int = None,
        mime_type: str = None,
        captured_date = None
    ) -> EvidenceItem:
        """Add an evidence item to a collection"""
        try:
            item = EvidenceItem(
                collection_id=collection_id,
                item_type=item_type,
                source_url=source_url,
                file_path=file_path,
                sha256_hash=sha256_hash,
                md5_hash=md5_hash,
                file_size_bytes=file_size_bytes,
                mime_type=mime_type,
                captured_date=captured_date
            )
            db.add(item)
            db.commit()
            db.refresh(item)
            logger.info(f"Added evidence item to collection {collection_id}")
            return item
        except Exception as e:
            db.rollback()
            logger.error(f"Error adding evidence item: {e}")
            raise

    @staticmethod
    def get_evidence_item(db: Session, item_id: int) -> EvidenceItem:
        """Get a specific evidence item"""
        return db.query(EvidenceItem).filter(EvidenceItem.id == item_id).first()

    @staticmethod
    def get_collection_items(db: Session, collection_id: int) -> list:
        """Get all items in a collection"""
        return db.query(EvidenceItem).filter(
            EvidenceItem.collection_id == collection_id
        ).all()

    @staticmethod
    def update_collection_status(
        db: Session,
        collection_id: int,
        status: str,
        post_count: int = None,
        media_count: int = None,
        total_size_bytes: int = None
    ) -> EvidenceCollection:
        """Update collection status and metrics"""
        try:
            collection = EvidenceService.get_collection(db, collection_id)
            if not collection:
                raise ValueError(f"Collection not found: {collection_id}")
            
            collection.status = status
            if post_count is not None:
                collection.post_count = post_count
            if media_count is not None:
                collection.media_count = media_count
            if total_size_bytes is not None:
                collection.total_size_bytes = total_size_bytes
            
            db.commit()
            db.refresh(collection)
            logger.info(f"Updated collection {collection_id} status to {status}")
            return collection
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating collection: {e}")
            raise

    @staticmethod
    def get_all_collections(db: Session) -> list:
        """Get all evidence collections"""
        return db.query(EvidenceCollection).all()
