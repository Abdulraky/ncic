"""
NCIC Intelligence Lab - MVP Main Application
Refactored for new database and services structure
"""
import streamlit as st
import pandas as pd
from pathlib import Path

# Database and services imports
from database import init_db, SessionLocal
from models import Official, EvidenceCollection, EvidenceItem, VerificationResult
from services import PoliticianService, EvidenceService, AnalysisService, CollectorService
from config import STREAMLIT_PORT

# Legacy modules (will be refactored gradually)
from officials_module import render_officials_module
from evidence_archiver_module import render_evidence_archiver_module
from authenticity_module import render_authenticity_module

# ──────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="NCIC Intelligence Lab - MVP", layout="wide")

# Initialize database on first run
if "db_initialized" not in st.session_state:
    init_db()
    st.session_state.db_initialized = True


# ──────────────────────────────────────────────────────────────────────────────
# STYLES
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;500;600;700&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"], .stApp { 
    background-color: #09111f !important; 
    color: #c9d4e3; 
    font-family: 'DM Sans', sans-serif; 
}

h1, h2, h3 { font-family: 'Rajdhani', sans-serif !important; letter-spacing: 0.04em; }
h1 { color: #e8edf5 !important; font-size: 2rem !important; font-weight: 700 !important; }
h2 { color: #c9d4e3 !important; font-size: 1.3rem !important; font-weight: 600 !important; }

.stButton > button { 
    background: linear-gradient(90deg,#1d4ed8 0%,#1e40af 100%) !important; 
    color: white !important; 
    border: none !important; 
    border-radius: 8px !important; 
    font-family: 'Rajdhani',sans-serif !important; 
    font-size: 15px !important; 
    font-weight: 600 !important; 
}

section[data-testid="stSidebar"] { 
    background: #070e1c !important; 
    border-right: 1px solid #111f35 !important; 
}
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# SIDEBAR & MODULE SELECTION
# ──────────────────────────────────────────────────────────────────────────────
st.sidebar.markdown("### 📦 MODULES")
module = st.sidebar.radio(
    "Select Module",
    [
        "🔍 X-Scraper",
        "🏛️ Officials DB",
        "🔐 Evidence Archiver",
        "🔍 Authenticity Score"
    ]
)

st.sidebar.markdown("---")
st.sidebar.markdown("""
**MVP Status**: Restructured  
**Database**: SQLite (SQLAlchemy ORM)  
**Services**: Enabled  
**Port**: 8501
""")


# ──────────────────────────────────────────────────────────────────────────────
# HEADER
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align: center; margin-bottom: 2rem;">
    <h1 style="margin: 0; font-size: 2.2rem;">🔍 NCIC INTELLIGENCE LAB</h1>
    <p style="color: #3d5a7a; font-size: 0.9rem; letter-spacing: 0.1em; margin-top: 0.5rem;">
        AUTOMATED CROSS-CHANNEL FORENSIC ANALYSIS PROTOCOL — ADMISSIBLE EVIDENCE AGGREGATOR
    </p>
    <p style="color: #15803d; font-family: 'Courier New', monospace; font-size: 0.85rem; margin-top: 0.8rem;">
        ✓ SYSTEM ACTIVE
    </p>
</div>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# MODULE ROUTING
# ──────────────────────────────────────────────────────────────────────────────
if module == "🏛️ Officials DB":
    render_officials_module()

elif module == "🔐 Evidence Archiver":
    render_evidence_archiver_module()

elif module == "🔍 Authenticity Score":
    render_authenticity_module()

elif module == "🔍 X-Scraper":
    st.markdown("### 🔍 X-Scraper (Research Mode)")
    st.info("Placeholder for Twitter/X scraper research mode")


# ──────────────────────────────────────────────────────────────────────────────
# DATABASE STATUS (Debug Info)
# ──────────────────────────────────────────────────────────────────────────────
if st.sidebar.checkbox("🔧 Debug Info"):
    with st.sidebar.expander("Database Status"):
        try:
            db = SessionLocal()
            officials_count = db.query(Official).count()
            collections_count = db.query(EvidenceCollection).count()
            items_count = db.query(EvidenceItem).count()
            db.close()
            
            st.write(f"**Officials**: {officials_count}")
            st.write(f"**Collections**: {collections_count}")
            st.write(f"**Evidence Items**: {items_count}")
        except Exception as e:
            st.error(f"Database error: {e}")
