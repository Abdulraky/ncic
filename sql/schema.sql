-- NCIC Intelligence Lab Database Schema
-- Compatible with both SQLite and PostgreSQL
-- For PostgreSQL migration, run: psql -U postgres -d ncic_db -f sql/schema.sql

-- Officials/Politicians table
CREATE TABLE IF NOT EXISTS officials (
    official_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    office VARCHAR(100),
    county VARCHAR(100),
    constituency VARCHAR(100),
    party VARCHAR(100),
    verified_x BOOLEAN DEFAULT FALSE,
    twitter VARCHAR(255),
    facebook VARCHAR(255),
    youtube VARCHAR(255),
    tiktok VARCHAR(255),
    instagram VARCHAR(255),
    website VARCHAR(255),
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Evidence collections (grouped evidence items)
CREATE TABLE IF NOT EXISTS evidence_collections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    official_id VARCHAR(50) NOT NULL,
    official_name VARCHAR(255) NOT NULL,
    collection_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pending',
    post_count INTEGER DEFAULT 0,
    media_count INTEGER DEFAULT 0,
    total_size_bytes INTEGER DEFAULT 0,
    archive_path TEXT,
    FOREIGN KEY(official_id) REFERENCES officials(official_id)
);

-- Individual evidence items (posts, screenshots, etc)
CREATE TABLE IF NOT EXISTS evidence_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    collection_id INTEGER NOT NULL,
    item_type VARCHAR(50),
    source_url TEXT,
    file_path TEXT,
    sha256_hash VARCHAR(64),
    md5_hash VARCHAR(32),
    file_size_bytes INTEGER,
    mime_type VARCHAR(100),
    captured_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(collection_id) REFERENCES evidence_collections(id)
);

-- Verification results (authenticity scores)
CREATE TABLE IF NOT EXISTS verification_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    evidence_item_id INTEGER NOT NULL,
    authenticity_score INTEGER,
    status VARCHAR(50),
    verified_account BOOLEAN,
    url_valid BOOLEAN,
    metadata_intact BOOLEAN,
    timestamp_verified BOOLEAN,
    no_editing BOOLEAN,
    sha256_verified BOOLEAN,
    screenshot_captured BOOLEAN,
    json_preserved BOOLEAN,
    result_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(evidence_item_id) REFERENCES evidence_items(id)
);

-- Audit log for compliance
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action VARCHAR(100) NOT NULL,
    user_agent VARCHAR(255),
    evidence_item_id INTEGER,
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(evidence_item_id) REFERENCES evidence_items(id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_officials_county ON officials(county);
CREATE INDEX IF NOT EXISTS idx_officials_party ON officials(party);
CREATE INDEX IF NOT EXISTS idx_evidence_official ON evidence_collections(official_id);
CREATE INDEX IF NOT EXISTS idx_verification_result ON verification_results(evidence_item_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created ON audit_log(created_at);
