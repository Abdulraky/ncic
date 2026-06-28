"""
Authenticity Verification Engine for Digital Evidence
Checks integrity, metadata, timestamps, and cryptographic signatures
"""

import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
from pathlib import Path


class AuthenticityVerifier:
    """Verifies authenticity of collected evidence"""
    
    # Verification check definitions
    VERIFICATION_CHECKS = {
        "verified_account": {
            "name": "Verified account",
            "description": "Account has official verification badge",
            "icon": "✔"
        },
        "url_valid": {
            "name": "URL valid",
            "description": "Original post URL is accessible and valid",
            "icon": "✔"
        },
        "metadata_intact": {
            "name": "Metadata intact",
            "description": "Post metadata (date, likes, engagement) is complete",
            "icon": "✔"
        },
        "timestamp_verified": {
            "name": "Timestamp verified",
            "description": "Post timestamp is consistent with archival time",
            "icon": "✔"
        },
        "no_editing": {
            "name": "No evidence of editing",
            "description": "Post shows no signs of edit history or modification",
            "icon": "✔"
        },
        "sha256_verified": {
            "name": "SHA256 verified",
            "description": "Cryptographic hash matches content",
            "icon": "✔"
        },
        "screenshot_captured": {
            "name": "Screenshot captured",
            "description": "Visual proof-of-posting screenshot exists",
            "icon": "✔"
        },
        "json_preserved": {
            "name": "Original JSON preserved",
            "description": "Raw JSON data from source is stored",
            "icon": "✔"
        }
    }
    
    def __init__(self):
        """Initialize authenticity verifier"""
        self.checks_passed = {}
        self.check_details = {}
        self.authenticity_score = 0
    
    def verify_evidence(self, evidence_item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify all authenticity checks for an evidence item
        
        Args:
            evidence_item: Dictionary containing evidence data
            
        Returns:
            Dictionary with verification results and score
        """
        self.checks_passed = {}
        self.check_details = {}
        
        # Run all verification checks
        self._check_verified_account(evidence_item)
        self._check_url_valid(evidence_item)
        self._check_metadata_intact(evidence_item)
        self._check_timestamp_verified(evidence_item)
        self._check_no_editing(evidence_item)
        self._check_sha256_verified(evidence_item)
        self._check_screenshot_captured(evidence_item)
        self._check_json_preserved(evidence_item)
        
        # Calculate authenticity score
        self.authenticity_score = self._calculate_score()
        
        return {
            "authenticity_score": self.authenticity_score,
            "checks_passed": self.checks_passed,
            "check_details": self.check_details,
            "verification_time": datetime.now().isoformat(),
            "status": "authentic" if self.authenticity_score >= 80 else "needs_review"
        }
    
    def _check_verified_account(self, evidence_item: Dict[str, Any]) -> None:
        """Check if account has official verification"""
        try:
            raw_data = evidence_item.get("raw_data", {})
            
            # Check Twitter
            if evidence_item.get("platform") == "twitter":
                is_verified = raw_data.get("user", {}).get("verified", False) or \
                             raw_data.get("verified", False)
            
            # Check Instagram
            elif evidence_item.get("platform") == "instagram":
                is_verified = raw_data.get("owner", {}).get("is_verified", False) or \
                             raw_data.get("is_verified", False)
            
            # Check TikTok
            elif evidence_item.get("platform") == "tiktok":
                is_verified = raw_data.get("author", {}).get("verified", False) or \
                             raw_data.get("verified", False)
            
            else:
                is_verified = False
            
            self.checks_passed["verified_account"] = is_verified
            self.check_details["verified_account"] = {
                "passed": is_verified,
                "reason": "Account has official verification badge" if is_verified else "Account not verified"
            }
        except Exception as e:
            self.checks_passed["verified_account"] = False
            self.check_details["verified_account"] = {
                "passed": False,
                "reason": f"Error checking verification: {str(e)}"
            }
    
    def _check_url_valid(self, evidence_item: Dict[str, Any]) -> None:
        """Check if original URL is valid and accessible"""
        try:
            url = evidence_item.get("url")
            
            if not url:
                self.checks_passed["url_valid"] = False
                self.check_details["url_valid"] = {
                    "passed": False,
                    "reason": "No URL found in evidence"
                }
                return
            
            # For now, simple check - URL exists and is non-empty
            # In production, would actually test URL accessibility
            is_valid = bool(url) and (url.startswith("http://") or url.startswith("https://"))
            
            self.checks_passed["url_valid"] = is_valid
            self.check_details["url_valid"] = {
                "passed": is_valid,
                "url": url,
                "reason": "URL format is valid" if is_valid else "Invalid URL format"
            }
        except Exception as e:
            self.checks_passed["url_valid"] = False
            self.check_details["url_valid"] = {
                "passed": False,
                "reason": f"Error validating URL: {str(e)}"
            }
    
    def _check_metadata_intact(self, evidence_item: Dict[str, Any]) -> None:
        """Check if metadata is complete and intact"""
        try:
            required_fields = ["username", "text", "timestamp", "platform"]
            missing_fields = [f for f in required_fields if not evidence_item.get(f)]
            
            is_intact = len(missing_fields) == 0
            
            self.checks_passed["metadata_intact"] = is_intact
            self.check_details["metadata_intact"] = {
                "passed": is_intact,
                "missing_fields": missing_fields,
                "reason": "All metadata fields present" if is_intact else f"Missing: {', '.join(missing_fields)}"
            }
        except Exception as e:
            self.checks_passed["metadata_intact"] = False
            self.check_details["metadata_intact"] = {
                "passed": False,
                "reason": f"Error checking metadata: {str(e)}"
            }
    
    def _check_timestamp_verified(self, evidence_item: Dict[str, Any]) -> None:
        """Check if timestamp is reasonable and verified"""
        try:
            timestamp_str = evidence_item.get("timestamp")
            capture_date = evidence_item.get("capture_date")
            
            if not timestamp_str:
                self.checks_passed["timestamp_verified"] = False
                self.check_details["timestamp_verified"] = {
                    "passed": False,
                    "reason": "No timestamp found"
                }
                return
            
            # Parse timestamps - handle multiple formats
            try:
                post_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except:
                try:
                    post_time = datetime.strptime(timestamp_str, "%a %b %d %H:%M:%S +0000 %Y")
                except:
                    post_time = datetime.now()
            
            # Check if timestamp is reasonable (not in future, not too old)
            now = datetime.now(post_time.tzinfo) if post_time.tzinfo else datetime.now()
            is_reasonable = post_time <= now and post_time > (now - timedelta(days=365*10))
            
            self.checks_passed["timestamp_verified"] = is_reasonable
            self.check_details["timestamp_verified"] = {
                "passed": is_reasonable,
                "timestamp": timestamp_str,
                "reason": "Timestamp is valid" if is_reasonable else "Timestamp appears invalid or manipulated"
            }
        except Exception as e:
            self.checks_passed["timestamp_verified"] = False
            self.check_details["timestamp_verified"] = {
                "passed": False,
                "reason": f"Error verifying timestamp: {str(e)}"
            }
    
    def _check_no_editing(self, evidence_item: Dict[str, Any]) -> None:
        """Check for evidence of post editing"""
        try:
            raw_data = evidence_item.get("raw_data", {})
            
            # Look for edit history or edit markers
            has_edit_history = False
            
            if evidence_item.get("platform") == "twitter":
                # Check for edit metadata
                has_edit_history = bool(raw_data.get("edit_history_tweet_ids")) or \
                                 raw_data.get("edited_at") is not None
            
            elif evidence_item.get("platform") == "instagram":
                # Instagram shows edited timestamp
                has_edit_history = raw_data.get("taken_at") != raw_data.get("caption_timestamp")
            
            is_unedited = not has_edit_history
            
            self.checks_passed["no_editing"] = is_unedited
            self.check_details["no_editing"] = {
                "passed": is_unedited,
                "reason": "No evidence of editing" if is_unedited else "Post shows evidence of editing"
            }
        except Exception as e:
            self.checks_passed["no_editing"] = False
            self.check_details["no_editing"] = {
                "passed": False,
                "reason": f"Error checking for edits: {str(e)}"
            }
    
    def _check_sha256_verified(self, evidence_item: Dict[str, Any]) -> None:
        """Verify SHA256 hash of content"""
        try:
            content_hash = evidence_item.get("sha256_hash")
            text_content = evidence_item.get("text", "")
            
            if not content_hash:
                self.checks_passed["sha256_verified"] = False
                self.check_details["sha256_verified"] = {
                    "passed": False,
                    "reason": "No hash found in evidence"
                }
                return
            
            # Compute hash of current text
            computed_hash = hashlib.sha256(text_content.encode()).hexdigest()
            hashes_match = computed_hash == content_hash
            
            self.checks_passed["sha256_verified"] = hashes_match
            self.check_details["sha256_verified"] = {
                "passed": hashes_match,
                "stored_hash": content_hash[:16] + "...",
                "reason": "SHA256 hash verified" if hashes_match else "Hash mismatch - content may have been modified"
            }
        except Exception as e:
            self.checks_passed["sha256_verified"] = False
            self.check_details["sha256_verified"] = {
                "passed": False,
                "reason": f"Error verifying hash: {str(e)}"
            }
    
    def _check_screenshot_captured(self, evidence_item: Dict[str, Any]) -> None:
        """Check if screenshot exists"""
        try:
            screenshot_path = evidence_item.get("screenshot_path")
            
            has_screenshot = bool(screenshot_path)
            
            if has_screenshot:
                # Check if file actually exists
                path = Path(screenshot_path)
                has_screenshot = path.exists()
            
            self.checks_passed["screenshot_captured"] = has_screenshot
            self.check_details["screenshot_captured"] = {
                "passed": has_screenshot,
                "path": screenshot_path if has_screenshot else None,
                "reason": "Screenshot captured and stored" if has_screenshot else "No screenshot found"
            }
        except Exception as e:
            self.checks_passed["screenshot_captured"] = False
            self.check_details["screenshot_captured"] = {
                "passed": False,
                "reason": f"Error checking screenshot: {str(e)}"
            }
    
    def _check_json_preserved(self, evidence_item: Dict[str, Any]) -> None:
        """Check if original JSON is preserved"""
        try:
            raw_data = evidence_item.get("raw_data")
            
            has_raw_json = bool(raw_data) and isinstance(raw_data, dict) and len(raw_data) > 0
            
            self.checks_passed["json_preserved"] = has_raw_json
            self.check_details["json_preserved"] = {
                "passed": has_raw_json,
                "size_kb": len(json.dumps(raw_data)) / 1024 if has_raw_json else 0,
                "reason": "Original JSON data preserved" if has_raw_json else "No raw JSON found"
            }
        except Exception as e:
            self.checks_passed["json_preserved"] = False
            self.check_details["json_preserved"] = {
                "passed": False,
                "reason": f"Error checking JSON: {str(e)}"
            }
    
    def _calculate_score(self) -> int:
        """Calculate authenticity score as percentage of passed checks"""
        total_checks = len(self.checks_passed)
        
        if total_checks == 0:
            return 0
        
        passed_checks = sum(1 for passed in self.checks_passed.values() if passed)
        score = int((passed_checks / total_checks) * 100)
        
        return score
    
    def get_check_status(self, check_key: str) -> Tuple[bool, str]:
        """Get status of a specific check"""
        passed = self.checks_passed.get(check_key, False)
        detail = self.check_details.get(check_key, {})
        reason = detail.get("reason", "Check not performed")
        
        return passed, reason
    
    def get_failed_checks(self) -> List[Dict[str, Any]]:
        """Get list of all failed checks"""
        failed = []
        
        for check_key, passed in self.checks_passed.items():
            if not passed:
                check_info = self.VERIFICATION_CHECKS.get(check_key, {})
                detail = self.check_details.get(check_key, {})
                
                failed.append({
                    "check_key": check_key,
                    "name": check_info.get("name"),
                    "reason": detail.get("reason", "Failed"),
                    "details": detail
                })
        
        return failed
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate complete verification report"""
        return {
            "authenticity_score": self.authenticity_score,
            "total_checks": len(self.checks_passed),
            "passed_checks": sum(1 for p in self.checks_passed.values() if p),
            "failed_checks": len([p for p in self.checks_passed.values() if not p]),
            "check_results": self.checks_passed,
            "check_details": self.check_details,
            "failed_checks_list": self.get_failed_checks(),
            "status": "AUTHENTIC" if self.authenticity_score >= 80 else "NEEDS_REVIEW" if self.authenticity_score >= 50 else "SUSPICIOUS",
            "generated_at": datetime.now().isoformat()
        }
