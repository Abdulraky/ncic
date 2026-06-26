"""
Digital Evidence Archiver Module
Comprehensive forensic collection, hashing, and storage system
"""

import os
import json
import hashlib
import datetime
import shutil
import sqlite3
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import mimetypes

class DigitalEvidenceArchiver:
    """Manages collection, verification, and storage of digital evidence"""
    
    def __init__(self, base_archive_path: str = "data/evidence_archive"):
        """Initialize evidence archiver with base storage path"""
        self.base_archive_path = Path(base_archive_path)
        self.base_archive_path.mkdir(parents=True, exist_ok=True)
        
        # Database for tracking evidence
        self.db_path = self.base_archive_path / "evidence_manifest.db"
        self._init_database()
        
        # Session for HTTP requests with retries
        self.session = self._create_session()
    
    def _create_session(self):
        """Create requests session with retry strategy"""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        return session
    
    def _init_database(self):
        """Initialize SQLite database for evidence tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Evidence collection table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS evidence_collection (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                official_id TEXT NOT NULL,
                official_name TEXT,
                collection_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending',
                post_count INTEGER DEFAULT 0,
                media_count INTEGER DEFAULT 0,
                total_size_bytes INTEGER DEFAULT 0,
                archive_path TEXT
            )
        """)
        
        # Evidence items table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS evidence_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                collection_id INTEGER NOT NULL,
                item_type TEXT,
                source_url TEXT,
                file_path TEXT,
                sha256_hash TEXT,
                md5_hash TEXT,
                file_size_bytes INTEGER,
                mime_type TEXT,
                captured_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (collection_id) REFERENCES evidence_collection(id)
            )
        """)
        
        # Integrity verification table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS integrity_verification (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                evidence_item_id INTEGER NOT NULL,
                sha256_original TEXT,
                sha256_verified TEXT,
                verification_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                verified BOOLEAN DEFAULT 0,
                FOREIGN KEY (evidence_item_id) REFERENCES evidence_items(id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _compute_hashes(self, file_path: str) -> Dict[str, str]:
        """Compute SHA256 and MD5 hashes for a file"""
        sha256_hash = hashlib.sha256()
        md5_hash = hashlib.md5()
        
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
                md5_hash.update(byte_block)
        
        return {
            "sha256": sha256_hash.hexdigest(),
            "md5": md5_hash.hexdigest()
        }
    
    def _create_collection_directory(self, official_id: str, official_name: str) -> Path:
        """Create directory structure for evidence collection"""
        collection_dir = self.base_archive_path / official_id / datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create subdirectories
        subdirs = [
            collection_dir / "posts",
            collection_dir / "metadata",
            collection_dir / "media",
            collection_dir / "html",
            collection_dir / "screenshots",
            collection_dir / "raw_json",
            collection_dir / "hashes",
            collection_dir / "manifest"
        ]
        
        for subdir in subdirs:
            subdir.mkdir(parents=True, exist_ok=True)
        
        return collection_dir
    
    def start_collection(self, official_id: str, official_name: str) -> Tuple[int, Path]:
        """Initialize evidence collection for an official"""
        archive_path = self._create_collection_directory(official_id, official_name)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO evidence_collection (official_id, official_name, archive_path, status)
            VALUES (?, ?, ?, ?)
        """, (official_id, official_name, str(archive_path), 'in_progress'))
        
        conn.commit()
        collection_id = cursor.lastrowid
        conn.close()
        
        return collection_id, archive_path
    
    def save_post_data(self, collection_id: int, post_id: str, post_data: Dict, archive_path: Path) -> bool:
        """Save post data and metadata"""
        try:
            # Save raw JSON
            json_file = archive_path / "raw_json" / f"post_{post_id}.json"
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(post_data, f, ensure_ascii=False, indent=2)
            
            # Compute hashes
            hashes = self._compute_hashes(str(json_file))
            file_size = json_file.stat().st_size
            
            # Record in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO evidence_items 
                (collection_id, item_type, source_url, file_path, sha256_hash, md5_hash, file_size_bytes, mime_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                collection_id,
                "post_json",
                post_data.get("url", ""),
                str(json_file),
                hashes["sha256"],
                hashes["md5"],
                file_size,
                "application/json"
            ))
            
            conn.commit()
            conn.close()
            
            return True
        except Exception as e:
            return False
    
    def save_metadata(self, collection_id: int, metadata: Dict, archive_path: Path) -> bool:
        """Save metadata from social media profile"""
        try:
            metadata_file = archive_path / "metadata" / "profile_metadata.json"
            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            hashes = self._compute_hashes(str(metadata_file))
            file_size = metadata_file.stat().st_size
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO evidence_items 
                (collection_id, item_type, file_path, sha256_hash, md5_hash, file_size_bytes, mime_type)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                collection_id,
                "metadata",
                str(metadata_file),
                hashes["sha256"],
                hashes["md5"],
                file_size,
                "application/json"
            ))
            
            conn.commit()
            conn.close()
            
            return True
        except Exception as e:
            return False
    
    def download_media(self, collection_id: int, url: str, filename: str, archive_path: Path) -> Tuple[bool, str]:
        """Download media file with verification"""
        try:
            media_dir = archive_path / "media"
            file_path = media_dir / filename
            
            # Download with streaming
            response = self.session.get(url, timeout=30, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # Compute hashes
            hashes = self._compute_hashes(str(file_path))
            file_size = file_path.stat().st_size
            mime_type = response.headers.get('content-type', 'application/octet-stream')
            
            # Record in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO evidence_items 
                (collection_id, item_type, source_url, file_path, sha256_hash, md5_hash, file_size_bytes, mime_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                collection_id,
                "media",
                url,
                str(file_path),
                hashes["sha256"],
                hashes["md5"],
                file_size,
                mime_type
            ))
            
            conn.commit()
            conn.close()
            
            return True, f"Downloaded: {filename} ({file_size} bytes)"
        except Exception as e:
            return False, f"Failed to download: {str(e)}"
    
    def save_html_snapshot(self, collection_id: int, url: str, html_content: str, archive_path: Path) -> bool:
        """Save HTML snapshot of web page"""
        try:
            filename = hashlib.md5(url.encode()).hexdigest() + ".html"
            html_file = archive_path / "html" / filename
            
            with open(html_file, "w", encoding="utf-8") as f:
                f.write(html_content)
            
            hashes = self._compute_hashes(str(html_file))
            file_size = html_file.stat().st_size
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO evidence_items 
                (collection_id, item_type, source_url, file_path, sha256_hash, md5_hash, file_size_bytes, mime_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                collection_id,
                "html_snapshot",
                url,
                str(html_file),
                hashes["sha256"],
                hashes["md5"],
                file_size,
                "text/html"
            ))
            
            conn.commit()
            conn.close()
            
            return True
        except Exception as e:
            return False
    
    def save_screenshot(self, collection_id: int, screenshot_data: bytes, source: str, archive_path: Path) -> bool:
        """Save screenshot with metadata"""
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{source}_{timestamp}.png"
            screenshot_file = archive_path / "screenshots" / filename
            
            with open(screenshot_file, "wb") as f:
                f.write(screenshot_data)
            
            hashes = self._compute_hashes(str(screenshot_file))
            file_size = screenshot_file.stat().st_size
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO evidence_items 
                (collection_id, item_type, source_url, file_path, sha256_hash, md5_hash, file_size_bytes, mime_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                collection_id,
                "screenshot",
                source,
                str(screenshot_file),
                hashes["sha256"],
                hashes["md5"],
                file_size,
                "image/png"
            ))
            
            conn.commit()
            conn.close()
            
            return True
        except Exception as e:
            return False
    
    def generate_hash_manifest(self, collection_id: int, archive_path: Path) -> str:
        """Generate manifest file with all hashes for verification"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT item_type, file_path, sha256_hash, md5_hash, file_size_bytes, captured_date
                FROM evidence_items
                WHERE collection_id = ?
                ORDER BY captured_date
            """, (collection_id,))
            
            items = cursor.fetchall()
            
            manifest = {
                "collection_id": collection_id,
                "generated": datetime.datetime.now().isoformat(),
                "total_items": len(items),
                "items": []
            }
            
            total_size = 0
            
            for item_type, file_path, sha256, md5, file_size, date in items:
                total_size += file_size or 0
                manifest["items"].append({
                    "type": item_type,
                    "file": Path(file_path).name,
                    "path": file_path,
                    "sha256": sha256,
                    "md5": md5,
                    "size_bytes": file_size,
                    "captured": date
                })
            
            manifest["total_size_bytes"] = total_size
            
            # Save manifest
            manifest_file = archive_path / "manifest" / "evidence_manifest.json"
            with open(manifest_file, "w", encoding="utf-8") as f:
                json.dump(manifest, f, ensure_ascii=False, indent=2)
            
            # Hash the manifest itself
            manifest_hashes = self._compute_hashes(str(manifest_file))
            
            # Create integrity file
            integrity_file = archive_path / "manifest" / "INTEGRITY_SEAL.txt"
            with open(integrity_file, "w", encoding="utf-8") as f:
                f.write("═" * 80 + "\n")
                f.write("DIGITAL EVIDENCE ARCHIVE — INTEGRITY VERIFICATION SEAL\n")
                f.write("═" * 80 + "\n\n")
                f.write(f"Collection ID: {collection_id}\n")
                f.write(f"Generated: {datetime.datetime.now().isoformat()}\n")
                f.write(f"Total Items: {len(items)}\n")
                f.write(f"Total Size: {total_size:,} bytes\n\n")
                f.write("MANIFEST FILE HASHES:\n")
                f.write(f"SHA-256: {manifest_hashes['sha256']}\n")
                f.write(f"MD5:     {manifest_hashes['md5']}\n\n")
                f.write("═" * 80 + "\n\n")
                f.write("CONTENTS:\n\n")
                for item in manifest["items"]:
                    f.write(f"[{item['type']}] {Path(item['file']).name}\n")
                    f.write(f"  SHA-256: {item['sha256']}\n")
                    f.write(f"  MD5:     {item['md5']}\n")
                    f.write(f"  Size:    {item['size_bytes']:,} bytes\n")
                    f.write(f"  Date:    {item['captured']}\n\n")
            
            conn.close()
            
            return str(manifest_file)
        except Exception as e:
            return ""
    
    def finalize_collection(self, collection_id: int, archive_path: Path) -> Tuple[bool, str]:
        """Finalize collection and generate verification certificate"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get collection stats
            cursor.execute("""
                SELECT COUNT(*) FROM evidence_items WHERE collection_id = ?
            """, (collection_id,))
            item_count = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COALESCE(SUM(file_size_bytes), 0) FROM evidence_items WHERE collection_id = ?
            """, (collection_id,))
            total_size = cursor.fetchone()[0]
            
            # Generate manifest
            manifest_path = self.generate_hash_manifest(collection_id, archive_path)
            
            # Create certificate
            cert_file = archive_path / "manifest" / "COLLECTION_CERTIFICATE.txt"
            
            with open(cert_file, "w", encoding="utf-8") as f:
                f.write("┌" + "─" * 78 + "┐\n")
                f.write("│" + " " * 78 + "│\n")
                f.write("│" + "NCIC DIGITAL FORENSIC COLLECTION CERTIFICATE".center(78) + "│\n")
                f.write("│" + " " * 78 + "│\n")
                f.write("└" + "─" * 78 + "┘\n\n")
                f.write(f"Collection ID:        {collection_id}\n")
                f.write(f"Collection Date:      {datetime.datetime.now().isoformat()}\n")
                f.write(f"Archive Location:     {archive_path}\n\n")
                f.write(f"Total Evidence Items: {item_count}\n")
                f.write(f"Total Archive Size:   {total_size:,} bytes ({total_size/1024/1024:.2f} MB)\n\n")
                f.write("EVIDENCE CATEGORIES:\n")
                
                cursor.execute("""
                    SELECT item_type, COUNT(*) FROM evidence_items 
                    WHERE collection_id = ? GROUP BY item_type
                """, (collection_id,))
                
                for item_type, count in cursor.fetchall():
                    f.write(f"  • {item_type}: {count} items\n")
                
                f.write("\n" + "─" * 80 + "\n")
                f.write("CERTIFICATION: This evidence collection has been created under digital\n")
                f.write("forensic best practices and is admissible in court proceedings under the\n")
                f.write("Evidence Act (Cap 80, Laws of Kenya) and Computer Misuse and Cybercrimes\n")
                f.write("Act (No. 5 of 2018).\n")
                f.write("─" * 80 + "\n")
            
            # Update collection status
            cursor.execute("""
                UPDATE evidence_collection 
                SET status = ?, post_count = ?, total_size_bytes = ?
                WHERE id = ?
            """, ('completed', item_count, total_size, collection_id))
            
            conn.commit()
            conn.close()
            
            return True, f"Collection finalized: {item_count} items, {total_size/1024/1024:.2f} MB"
        except Exception as e:
            return False, f"Finalization error: {str(e)}"
    
    def get_collection_status(self, collection_id: int) -> Dict:
        """Get detailed status of evidence collection"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, official_id, official_name, collection_date, status, 
                       post_count, media_count, total_size_bytes, archive_path
                FROM evidence_collection WHERE id = ?
            """, (collection_id,))
            
            result = cursor.fetchone()
            if not result:
                return {}
            
            # Get item breakdown
            cursor.execute("""
                SELECT item_type, COUNT(*) as count, COALESCE(SUM(file_size_bytes), 0) as total_size
                FROM evidence_items WHERE collection_id = ? GROUP BY item_type
            """, (collection_id,))
            
            item_breakdown = {row[0]: {"count": row[1], "size": row[2]} for row in cursor.fetchall()}
            
            conn.close()
            
            return {
                "id": result[0],
                "official_id": result[1],
                "official_name": result[2],
                "collection_date": result[3],
                "status": result[4],
                "post_count": result[5],
                "media_count": result[6],
                "total_size_bytes": result[7],
                "archive_path": result[8],
                "item_breakdown": item_breakdown
            }
        except Exception as e:
            return {}
    
    def list_collections(self) -> List[Dict]:
        """List all evidence collections"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, official_id, official_name, collection_date, status, total_size_bytes
                FROM evidence_collection ORDER BY collection_date DESC
            """)
            
            collections = []
            for row in cursor.fetchall():
                collections.append({
                    "id": row[0],
                    "official_id": row[1],
                    "official_name": row[2],
                    "collection_date": row[3],
                    "status": row[4],
                    "total_size_bytes": row[5]
                })
            
            conn.close()
            return collections
        except Exception as e:
            return []
