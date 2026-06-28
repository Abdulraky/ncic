"""Official/Politician model"""
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base


class Official(Base):
    """Represents a public official or politician"""
    __tablename__ = "officials"

    official_id = Column(String(50), primary_key=True)
    name = Column(String(255), nullable=False)
    office = Column(String(100))
    county = Column(String(100))
    constituency = Column(String(100))
    party = Column(String(100))
    verified_x = Column(Boolean, default=False)
    twitter = Column(String(255))
    facebook = Column(String(255))
    youtube = Column(String(255))
    tiktok = Column(String(255))
    instagram = Column(String(255))
    website = Column(String(255))
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    evidence_collections = relationship("EvidenceCollection", back_populates="official")

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "official_id": self.official_id,
            "name": self.name,
            "office": self.office,
            "county": self.county,
            "constituency": self.constituency,
            "party": self.party,
            "verified_x": self.verified_x,
            "twitter": self.twitter,
            "facebook": self.facebook,
            "youtube": self.youtube,
            "tiktok": self.tiktok,
            "instagram": self.instagram,
            "website": self.website,
            "active": self.active,
        }
