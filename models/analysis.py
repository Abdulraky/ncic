"""Analysis and verification models"""
from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base


class VerificationResult(Base):
    """Represents the result of verifying an evidence item"""
    __tablename__ = "verification_results"

    id = Column(Integer, primary_key=True)
    evidence_item_id = Column(Integer, ForeignKey("evidence_items.id"), nullable=False)
    authenticity_score = Column(Integer)
    status = Column(String(50))
    verified_account = Column(Boolean)
    url_valid = Column(Boolean)
    metadata_intact = Column(Boolean)
    timestamp_verified = Column(Boolean)
    no_editing = Column(Boolean)
    sha256_verified = Column(Boolean)
    screenshot_captured = Column(Boolean)
    json_preserved = Column(Boolean)
    result_json = Column(Text)  # Full JSON result stored as text
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    evidence_item = relationship("EvidenceItem", back_populates="verification_results")

    def to_dict(self):
        return {
            "id": self.id,
            "evidence_item_id": self.evidence_item_id,
            "authenticity_score": self.authenticity_score,
            "status": self.status,
            "verified_account": self.verified_account,
            "url_valid": self.url_valid,
            "metadata_intact": self.metadata_intact,
            "timestamp_verified": self.timestamp_verified,
            "no_editing": self.no_editing,
            "sha256_verified": self.sha256_verified,
            "screenshot_captured": self.screenshot_captured,
            "json_preserved": self.json_preserved,
        }


class AuditLog(Base):
    """Audit trail for compliance and forensics"""
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True)
    action = Column(String(100), nullable=False)
    user_agent = Column(String(255))
    evidence_item_id = Column(Integer, ForeignKey("evidence_items.id"))
    details = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "action": self.action,
            "user_agent": self.user_agent,
            "evidence_item_id": self.evidence_item_id,
            "details": self.details,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
