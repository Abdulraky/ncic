"""
Configuration management for NCIC Intelligence Lab MVP
Hardcoded for MVP testing - will move to .env later
"""
import os
from pathlib import Path

# Database configuration
DB_PATH = Path(__file__).parent / "data" / "ncic.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Storage paths
STORAGE_PATH = Path(__file__).parent / "storage"
RAW_STORAGE = STORAGE_PATH / "raw"
SCREENSHOTS_PATH = STORAGE_PATH / "screenshots"
MEDIA_PATH = STORAGE_PATH / "media"

# Ensure storage directories exist
for path in [RAW_STORAGE, SCREENSHOTS_PATH, MEDIA_PATH]:
    path.mkdir(parents=True, exist_ok=True)

# Apify configuration (hardcoded for MVP)
APIFY_TOKEN = os.getenv("APIFY_TOKEN", "")

# Server configuration
STREAMLIT_PORT = 8501
API_PORT = 8000

# Logging
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Evidence configuration
MAX_POSTS_PER_PLATFORM = 50
EVIDENCE_EXPIRY_DAYS = 365
