"""Service for evidence analysis and verification"""
from sqlalchemy.orm import Session
from models import VerificationResult, EvidenceItem, AuditLog
from authenticity_verifier import AuthenticityVerifier
import json
import logging

logger = logging.getLogger(__name__)


class AnalysisService:
    """Business logic for evidence analysis and authenticity verification"""

    def __init__(self):
        self.verifier = AuthenticityVerifier()

    def verify_evidence(
        self,
        db: Session,
        evidence_item_id: int,
        save_result: bool = True
    ) -> dict:
        """Verify an evidence item's authenticity"""
        try:
            # Get the evidence item
            evidence = db.query(EvidenceItem).filter(
                EvidenceItem.id == evidence_item_id
            ).first()
            
            if not evidence:
                raise ValueError(f"Evidence item not found: {evidence_item_id}")
            
            # Run verification
            result = self.verifier.verify_evidence(evidence.to_dict())
            
            # Optionally save result to database
            if save_result:
                verification = VerificationResult(
                    evidence_item_id=evidence_item_id,
                    authenticity_score=result.get("authenticity_score"),
                    status=result.get("status"),
                    verified_account=result.get("checks_passed", {}).get("verified_account"),
                    url_valid=result.get("checks_passed", {}).get("url_valid"),
                    metadata_intact=result.get("checks_passed", {}).get("metadata_intact"),
                    timestamp_verified=result.get("checks_passed", {}).get("timestamp_verified"),
                    no_editing=result.get("checks_passed", {}).get("no_editing"),
                    sha256_verified=result.get("checks_passed", {}).get("sha256_verified"),
                    screenshot_captured=result.get("checks_passed", {}).get("screenshot_captured"),
                    json_preserved=result.get("checks_passed", {}).get("json_preserved"),
                    result_json=json.dumps(result)
                )
                db.add(verification)
                
                # Log the verification action
                audit = AuditLog(
                    action="VERIFY_EVIDENCE",
                    evidence_item_id=evidence_item_id,
                    details=f"Authenticity score: {result.get('authenticity_score')}"
                )
                db.add(audit)
                db.commit()
                logger.info(f"Verified evidence {evidence_item_id}, score: {result.get('authenticity_score')}")
            
            return result
        except Exception as e:
            db.rollback()
            logger.error(f"Error verifying evidence: {e}")
            raise

    @staticmethod
    def get_verification_result(db: Session, verification_id: int) -> VerificationResult:
        """Get a specific verification result"""
        return db.query(VerificationResult).filter(
            VerificationResult.id == verification_id
        ).first()

    @staticmethod
    def get_evidence_verification_history(
        db: Session,
        evidence_item_id: int
    ) -> list:
        """Get all verification results for an evidence item"""
        return db.query(VerificationResult).filter(
            VerificationResult.evidence_item_id == evidence_item_id
        ).order_by(VerificationResult.created_at.desc()).all()

    @staticmethod
    def get_all_results(db: Session) -> list:
        """Get all verification results"""
        return db.query(VerificationResult).all()

    @staticmethod
    def get_results_summary(db: Session) -> dict:
        """Get summary statistics of verification results"""
        results = AnalysisService.get_all_results(db)
        
        if not results:
            return {
                "total": 0,
                "authentic": 0,
                "needs_review": 0,
                "suspicious": 0,
                "avg_score": 0
            }
        
        summary = {
            "total": len(results),
            "authentic": len([r for r in results if r.status == "authentic"]),
            "needs_review": len([r for r in results if r.status == "needs_review"]),
            "suspicious": len([r for r in results if r.status == "suspicious"]),
            "avg_score": int(sum(r.authenticity_score for r in results) / len(results))
        }
        
        return summary
