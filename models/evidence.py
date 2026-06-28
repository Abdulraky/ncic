"""Evidence and post models"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base


class EvidenceCollection(Base):
    """Represents a collection of evidence items for an official"""
    __tablename__ = "evidence_collections"

    id = Column(Integer, primary_key=True)
    official_id = Column(String(50), ForeignKey("officials.official_id"), nullable=False)
    official_name = Column(String(255), nullable=False)
    collection_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default="pending")
    post_count = Column(Integer, default=0)
    media_count = Column(Integer, default=0)
    total_size_bytes = Column(Integer, default=0)
    archive_path = Column(Text)

    # Relationships
    official = relationship("Official", back_populates="evidence_collections")
    evidence_items = relationship("EvidenceItem", back_populates="collection")

    def to_dict(self):
        return {
            "id": self.id,
            "official_id": self.official_id,
            "official_name": self.official_name,
            "collection_date": self.collection_date.isoformat() if self.collection_date else None,
            "status": self.status,
            "post_count": self.post_count,
            "media_count": self.media_count,
            "total_size_bytes": self.total_size_bytes,
        }


class EvidenceItem(Base):
    """Represents a single piece of evidence (post, screenshot, etc)"""
    __tablename__ = "evidence_items"

    id = Column(Integer, primary_key=True)
    collection_id = Column(Integer, ForeignKey("evidence_collections.id"), nullable=False)
    item_type = Column(String(50))
    source_url = Column(Text)
    file_path = Column(Text)
    sha256_hash = Column(String(64))
    md5_hash = Column(String(32))
    file_size_bytes = Column(Integer)
    mime_type = Column(String(100))
    captured_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    collection = relationship("EvidenceCollection", back_populates="evidence_items")
    verification_results = relationship("VerificationResult", back_populates="evidence_item")

    def to_dict(self):
        return {
            "id": self.id,
            "collection_id": self.collection_id,
            "item_type": self.item_type,
            "source_url": self.source_url,
            "file_path": self.file_path,
            "sha256_hash": self.sha256_hash,
            "md5_hash": self.md5_hash,
            "file_size_bytes": self.file_size_bytes,
            "mime_type": self.mime_type,
            "captured_date": self.captured_date.isoformat() if self.captured_date else None,
        }
