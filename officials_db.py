"""
Public Officials Database Module
Manages storage, retrieval, and search of government officials data
"""

import sqlite3
import pandas as pd
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import datetime

class OfficialsDatabase:
    def __init__(self, db_path: str = "data/officials.db"):
        """Initialize database connection and create tables if needed"""
        self.db_path = db_path
        self.conn = None
        self._ensure_db_exists()
    
    def _ensure_db_exists(self):
        """Create database and tables if they don't exist"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        cursor = conn.cursor()
        
        # Create officials table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS officials (
                official_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                office TEXT NOT NULL,
                county TEXT,
                constituency TEXT,
                party TEXT,
                verified_x BOOLEAN DEFAULT 0,
                twitter TEXT,
                facebook TEXT,
                youtube TEXT,
                tiktok TEXT,
                instagram TEXT,
                website TEXT,
                active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create search index table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS search_index (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                official_id TEXT NOT NULL,
                search_term TEXT NOT NULL,
                FOREIGN KEY (official_id) REFERENCES officials(official_id)
            )
        """)
        
        # Create import log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS import_log (
                import_id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                record_count INTEGER,
                imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'success'
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _get_conn(self):
        """Get database connection"""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def add_official(self, official_data: Dict) -> Tuple[bool, str]:
        """Add a single official to the database"""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO officials 
                (official_id, name, office, county, constituency, party, 
                 verified_x, twitter, facebook, youtube, tiktok, instagram, website, active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                official_data.get('official_id'),
                official_data.get('name'),
                official_data.get('office'),
                official_data.get('county'),
                official_data.get('constituency'),
                official_data.get('party'),
                official_data.get('verified_x', False),
                official_data.get('twitter'),
                official_data.get('facebook'),
                official_data.get('youtube'),
                official_data.get('tiktok'),
                official_data.get('instagram'),
                official_data.get('website'),
                official_data.get('active', True)
            ))
            
            conn.commit()
            return True, f"Official {official_data.get('name')} added successfully"
        except Exception as e:
            return False, f"Error adding official: {str(e)}"
    
    def import_from_csv(self, file_path: str) -> Tuple[int, str]:
        """Import officials from CSV file"""
        try:
            df = pd.read_csv(file_path)
            conn = self._get_conn()
            cursor = conn.cursor()
            
            imported_count = 0
            errors = []
            
            for idx, row in df.iterrows():
                try:
                    official_data = row.to_dict()
                    # Clean NaN values
                    official_data = {k: (v if pd.notna(v) else None) for k, v in official_data.items()}
                    
                    cursor.execute("""
                        INSERT OR REPLACE INTO officials 
                        (official_id, name, office, county, constituency, party, 
                         verified_x, facebook, youtube, tiktok, instagram, website, active)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        official_data.get('official_id'),
                        official_data.get('name'),
                        official_data.get('office'),
                        official_data.get('county'),
                        official_data.get('constituency'),
                        official_data.get('party'),
                        official_data.get('verified_x', 0),
                        official_data.get('facebook'),
                        official_data.get('youtube'),
                        official_data.get('tiktok'),
                        official_data.get('instagram'),
                        official_data.get('website'),
                        official_data.get('active', 1)
                    ))
                    imported_count += 1
                except Exception as e:
                    errors.append(f"Row {idx}: {str(e)}")
            
            # Log the import
            filename = Path(file_path).name
            cursor.execute("""
                INSERT INTO import_log (filename, record_count, status)
                VALUES (?, ?, ?)
            """, (filename, imported_count, 'success' if not errors else 'partial'))
            
            conn.commit()
            
            message = f"Imported {imported_count} officials from {filename}"
            if errors:
                message += f"\nWarnings: {len(errors)} rows had issues"
            
            return imported_count, message
        except Exception as e:
            return 0, f"Error importing CSV: {str(e)}"
    
    def import_from_json(self, file_path: str) -> Tuple[int, str]:
        """Import officials from JSON file"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Handle both list and dict formats
            if isinstance(data, dict):
                officials_list = data.get('officials', []) or [data]
            else:
                officials_list = data
            
            conn = self._get_conn()
            cursor = conn.cursor()
            
            imported_count = 0
            errors = []
            
            for official_data in officials_list:
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO officials 
                        (official_id, name, office, county, constituency, party, 
                         verified_x, facebook, youtube, tiktok, instagram, website, active)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        official_data.get('official_id'),
                        official_data.get('name'),
                        official_data.get('office'),
                        official_data.get('county'),
                        official_data.get('constituency'),
                        official_data.get('party'),
                        official_data.get('verified_x', False),
                        official_data.get('facebook'),
                        official_data.get('youtube'),
                        official_data.get('tiktok'),
                        official_data.get('instagram'),
                        official_data.get('website'),
                        official_data.get('active', True)
                    ))
                    imported_count += 1
                except Exception as e:
                    errors.append(str(e))
            
            # Log the import
            filename = Path(file_path).name
            cursor.execute("""
                INSERT INTO import_log (filename, record_count, status)
                VALUES (?, ?, ?)
            """, (filename, imported_count, 'success' if not errors else 'partial'))
            
            conn.commit()
            
            message = f"Imported {imported_count} officials from {filename}"
            if errors:
                message += f"\nWarnings: {len(errors)} rows had issues"
            
            return imported_count, message
        except Exception as e:
            return 0, f"Error importing JSON: {str(e)}"
    
    def search_officials(self, query: str, fields: List[str] = None) -> List[Dict]:
        """Search officials by query across specified fields"""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            if fields is None:
                fields = ['name', 'office', 'party', 'constituency', 'county']
            
            # Build search query
            search_conditions = " OR ".join([f"{field} LIKE ?" for field in fields])
            query_param = f"%{query}%"
            params = [query_param] * len(fields)
            
            cursor.execute(f"""
                SELECT * FROM officials 
                WHERE {search_conditions}
                ORDER BY name
            """, params)
            
            results = [dict(row) for row in cursor.fetchall()]
            return results
        except Exception as e:
            return []
    
    def get_all_officials(self, active_only: bool = True) -> List[Dict]:
        """Get all officials from database"""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            if active_only:
                cursor.execute("SELECT * FROM officials WHERE active = 1 ORDER BY name")
            else:
                cursor.execute("SELECT * FROM officials ORDER BY name")
            
            results = [dict(row) for row in cursor.fetchall()]
            return results
        except Exception as e:
            return []
    
    def get_officials_by_office(self, office: str) -> List[Dict]:
        """Get all officials in a specific office"""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM officials WHERE office = ? AND active = 1 ORDER BY name",
                (office,)
            )
            
            results = [dict(row) for row in cursor.fetchall()]
            return results
        except Exception as e:
            return []
    
    def get_officials_by_county(self, county: str) -> List[Dict]:
        """Get all officials in a specific county"""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM officials WHERE county = ? AND active = 1 ORDER BY name",
                (county,)
            )
            
            results = [dict(row) for row in cursor.fetchall()]
            return results
        except Exception as e:
            return []
    
    def get_offices(self) -> List[str]:
        """Get list of all unique offices"""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            cursor.execute("SELECT DISTINCT office FROM officials ORDER BY office")
            offices = [row[0] for row in cursor.fetchall() if row[0]]
            return offices
        except Exception as e:
            return []
    
    def get_counties(self) -> List[str]:
        """Get list of all unique counties"""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            cursor.execute("SELECT DISTINCT county FROM officials ORDER BY county")
            counties = [row[0] for row in cursor.fetchall() if row[0]]
            return counties
        except Exception as e:
            return []
    
    def get_parties(self) -> List[str]:
        """Get list of all unique parties"""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            cursor.execute("SELECT DISTINCT party FROM officials ORDER BY party")
            parties = [row[0] for row in cursor.fetchall() if row[0]]
            return parties
        except Exception as e:
            return []
    
    def update_official(self, official_id: str, updates: Dict) -> Tuple[bool, str]:
        """Update an official's information"""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            # Build update query
            set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
            values = list(updates.values()) + [official_id]
            
            cursor.execute(f"""
                UPDATE officials 
                SET {set_clause}, updated_at = CURRENT_TIMESTAMP
                WHERE official_id = ?
            """, values)
            
            conn.commit()
            return True, f"Official {official_id} updated successfully"
        except Exception as e:
            return False, f"Error updating official: {str(e)}"
    
    def delete_official(self, official_id: str) -> Tuple[bool, str]:
        """Soft delete an official (mark as inactive)"""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE officials 
                SET active = 0, updated_at = CURRENT_TIMESTAMP
                WHERE official_id = ?
            """, (official_id,))
            
            conn.commit()
            return True, f"Official {official_id} marked as inactive"
        except Exception as e:
            return False, f"Error deleting official: {str(e)}"
    
    def get_statistics(self) -> Dict:
        """Get database statistics"""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            # Total officials
            cursor.execute("SELECT COUNT(*) FROM officials WHERE active = 1")
            total = cursor.fetchone()[0]
            
            # By office
            cursor.execute("""
                SELECT office, COUNT(*) as count 
                FROM officials 
                WHERE active = 1 
                GROUP BY office
            """)
            by_office = dict(cursor.fetchall())
            
            # By county
            cursor.execute("""
                SELECT county, COUNT(*) as count 
                FROM officials 
                WHERE active = 1 AND county IS NOT NULL
                GROUP BY county
            """)
            by_county = dict(cursor.fetchall())
            
            # Verified on X
            cursor.execute("SELECT COUNT(*) FROM officials WHERE verified_x = 1 AND active = 1")
            verified_x = cursor.fetchone()[0]
            
            # With social media
            cursor.execute("""
                SELECT COUNT(*) FROM officials 
                WHERE active = 1 AND (facebook IS NOT NULL OR youtube IS NOT NULL OR tiktok IS NOT NULL OR instagram IS NOT NULL)
            """)
            with_socials = cursor.fetchone()[0]
            
            return {
                'total_active': total,
                'by_office': by_office,
                'by_county': by_county,
                'verified_x': verified_x,
                'with_socials': with_socials
            }
        except Exception as e:
            return {}
    
    def export_to_csv(self, output_path: str = "data/officials_export.csv") -> Tuple[bool, str]:
        """Export all officials to CSV"""
        try:
            officials = self.get_all_officials(active_only=False)
            df = pd.DataFrame(officials)
            df.to_csv(output_path, index=False)
            return True, f"Exported {len(officials)} officials to {output_path}"
        except Exception as e:
            return False, f"Error exporting to CSV: {str(e)}"
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
