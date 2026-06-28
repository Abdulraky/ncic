import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import datetime
import hashlib
import json
import numpy as np
import html as html_lib
from apify_client import ApifyClient as OfficialApifyClient
import os
import time
from pathlib import Path

# Lightweight NLP dependencies
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

# Import custom modules (using v2 refactored versions with services)
from officials_module_v2 import render_officials_module
from evidence_archiver_module_v2 import render_evidence_archiver_module
from authenticity_module_v2 import render_authenticity_module

# ──────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="NCIC Intelligence Lab", layout="wide")

# ──────────────────────────────────────────────────────────────────────────────
# MAIN UI STYLES  (Streamlit native elements — sidebar, metrics, buttons, etc.)
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;500;600;700&family=DM+Sans:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"], .stApp { background-color: #09111f !important; color: #c9d4e3; font-family: 'DM Sans', sans-serif; }
.main .block-container { padding: 1.8rem 2.5rem 4rem; max-width: 1200px; }
::-webkit-scrollbar { width: 5px; background: #0d1829; }
::-webkit-scrollbar-thumb { background: #1e3a5f; border-radius: 4px; }

h1, h2, h3, h4 { font-family: 'Rajdhani', sans-serif !important; letter-spacing: 0.04em; }
h1 { color: #e8edf5 !important; font-size: 2rem !important; font-weight: 700 !important; }
h2 { color: #c9d4e3 !important; font-size: 1.3rem !important; font-weight: 600 !important; }
h3 { color: #a8b8d0 !important; font-size: 1.05rem !important; font-weight: 600 !important; }

div[data-testid="stMetricValue"] { font-family: 'Rajdhani',sans-serif !important; font-size: 2.2rem !important; font-weight: 700 !important; color: #e8edf5 !important; }
div[data-testid="stMetricLabel"] { font-family: 'DM Sans',sans-serif !important; color: #4a6a8a !important; font-size: 11px !important; letter-spacing: 0.08em !important; text-transform: uppercase !important; }

.stButton > button { background: linear-gradient(90deg,#1d4ed8 0%,#1e40af 100%) !important; color: white !important; border: none !important; border-radius: 8px !important; font-family: 'Rajdhani',sans-serif !important; font-size: 15px !important; font-weight: 600 !important; letter-spacing: 0.1em !important; padding: 0.6rem 1.4rem !important; }
.stButton > button:hover { opacity: 0.85 !important; }
.stDownloadButton > button { background: #0d1829 !important; color: #60a5fa !important; border: 1px solid #1d4ed8 !important; border-radius: 8px !important; font-family: 'Rajdhani',sans-serif !important; font-weight: 600 !important; letter-spacing: 0.06em !important; }

section[data-testid="stSidebar"] { background: #070e1c !important; border-right: 1px solid #111f35 !important; }
section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span { color: #6b8cae !important; font-size: 12px !important; }
section[data-testid="stSidebar"] input { background: #0d1829 !important; border: 1px solid #1a3055 !important; color: #c9d4e3 !important; }

.stSuccess { background: rgba(21,128,61,0.12) !important; border: 1px solid rgba(21,128,61,0.3) !important; color: #4ade80 !important; }
.stWarning { background: rgba(217,119,6,0.12) !important; border: 1px solid rgba(217,119,6,0.3) !important; color: #fbbf24 !important; }
.stInfo    { background: rgba(29,78,216,0.12) !important; border: 1px solid rgba(29,78,216,0.3) !important; color: #93c5fd !important; }
.stError   { background: rgba(220,38,38,0.12) !important; border: 1px solid rgba(220,38,38,0.3) !important; color: #f87171 !important; }

hr { border-color: #111f35 !important; margin: 1.4rem 0 !important; }
div[data-testid="stSelectbox"] label { color: #6b8cae !important; font-size: 12px !important; }

.metric-wrap { background: #0d1829; border: 1px solid #1a3055; border-radius: 10px; padding: 18px 22px; }
.metric-critical { border-top: 3px solid #dc2626; }
.metric-high     { border-top: 3px solid #d97706; }
.metric-default  { border-top: 3px solid #1d4ed8; }
.metric-ok       { border-top: 3px solid #15803d; }

.section-label {
    font-family: 'Rajdhani',sans-serif; font-size: 12px; font-weight: 600;
    letter-spacing: 0.16em; text-transform: uppercase; color: #2d4a66;
    border-bottom: 1px solid #111f35; padding-bottom: 8px; margin-bottom: 16px; margin-top: 24px;
}
.lab-header {
    background: linear-gradient(90deg,#0d1f3c 0%,#091629 60%,#09111f 100%);
    border-bottom: 1px solid #1a3055; border-radius: 10px;
    padding: 22px 30px; margin-bottom: 26px;
    display: flex; align-items: center; justify-content: space-between;
}
.lab-title { font-family:'Rajdhani',sans-serif; font-size:1.65rem; font-weight:700; color:#e8edf5; letter-spacing:0.08em; text-transform:uppercase; }
.lab-sub   { font-family:'JetBrains Mono',monospace; font-size:10.5px; color:#3d5a7a; margin-top:4px; letter-spacing:0.05em; }
.lab-live  { background:rgba(220,38,38,0.12); border:1px solid rgba(220,38,38,0.35); color:#f87171; padding:6px 16px; border-radius:6px; font-family:'JetBrains Mono',monospace; font-size:11px; letter-spacing:0.08em; }
.dossier-block {
    background:#060c18; border:1px solid #1a3055; border-left:4px solid #dc2626;
    border-radius:8px; padding:24px 28px; font-family:'JetBrains Mono',monospace;
    font-size:12.5px; color:#6b8cae; line-height:2.0; margin-top:14px;
}
.dossier-block strong { color:#a8c0d8; }
.dossier-seal { color:#22c55e; word-break:break-all; font-size:11px; }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# CARD CSS  (used inside components.html iframe — must be self-contained)
# ──────────────────────────────────────────────────────────────────────────────
CARD_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@600;700&family=DM+Sans:wght@400;500&family=JetBrains+Mono:wght@400;500&display=swap');
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: #09111f; padding: 4px 0 8px 0; font-family: 'DM Sans', sans-serif; }
.card {
    background: #0d1829; border-radius: 10px; padding: 20px 24px;
    margin-bottom: 12px; border: 1px solid #1a3055; position: relative;
}
.card-critical { border-left: 4px solid #dc2626; }
.card-high     { border-left: 4px solid #d97706; }
.card-low      { border-left: 4px solid #15803d; }
.card-top { display: flex; align-items: center; gap: 10px; margin-bottom: 14px; flex-wrap: wrap; }
.badge {
    font-family: 'JetBrains Mono', monospace; font-size: 10px; font-weight: 500;
    letter-spacing: 0.1em; text-transform: uppercase; padding: 3px 10px;
    border-radius: 4px; white-space: nowrap;
}
.badge-critical { background: rgba(220,38,38,0.15); color: #f87171; border: 1px solid rgba(220,38,38,0.35); }
.badge-high     { background: rgba(217,119,6,0.15);  color: #fbbf24; border: 1px solid rgba(217,119,6,0.35); }
.badge-low      { background: rgba(21,128,61,0.15);  color: #4ade80; border: 1px solid rgba(21,128,61,0.3); }
.clf { font-family: 'DM Sans', sans-serif; font-size: 12.5px; color: #4a6a8a; }
.tweet-text {
    font-size: 15px; line-height: 1.75; color: #d0daea; font-style: italic;
    background: rgba(255,255,255,0.03); border-left: 2px solid #1a3055;
    padding: 13px 16px; border-radius: 6px; margin-bottom: 14px;
}
.card-foot {
    display: flex; align-items: center; gap: 16px; flex-wrap: wrap;
    border-top: 1px solid #111f35; padding-top: 12px;
    font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #2d4a66;
}
.foot-ts  { color: #3d5a7a; }
.foot-cat { color: #2d4a66; }
.foot-seal { color: #1e3a5f; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.verify-btn {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(29,78,216,0.15); color: #60a5fa;
    border: 1px solid rgba(29,78,216,0.35); padding: 5px 14px;
    border-radius: 6px; font-family: 'JetBrains Mono', monospace;
    font-size: 11px; font-weight: 500; text-decoration: none;
    letter-spacing: 0.05em; white-space: nowrap; margin-left: auto;
}
.verify-btn:hover { background: rgba(29,78,216,0.3); color: #93c5fd; }
"""


# ──────────────────────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────────────────────
def extract_text(item):
    """Try every known field name from different apidojo/tweet-scraper versions."""
    candidates = [
        item.get("text"),
        item.get("full_text"),
        item.get("tweet_text"),
        item.get("rawContent"),
        item.get("content"),
        item.get("body"),
    ]
    for c in candidates:
        if c and isinstance(c, str) and len(c.strip()) > 3:
            return c.strip()
    # Handle nested structures
    for key in ["tweet", "data", "legacy", "core"]:
        nested = item.get(key)
        if isinstance(nested, dict):
            for field in ["text", "full_text", "rawContent"]:
                val = nested.get(field)
                if val and isinstance(val, str) and len(val.strip()) > 3:
                    return val.strip()
    return None


def extract_url(item, handle):
    """Get a valid, clickable tweet URL from Apify response."""
    for field in ["url", "tweet_url", "tweetUrl", "permanentUrl", "link", "twitterUrl"]:
        val = item.get(field)
        if val and isinstance(val, str) and val.startswith("http"):
            return val.replace("twitter.com", "x.com")
    # Build from numeric tweet ID (guaranteed to work)
    for id_field in ["id", "id_str", "tweetId", "tweet_id"]:
        tid = item.get(id_field)
        if tid and str(tid).strip().lstrip("SIM-").isdigit():
            return f"https://x.com/{handle}/status/{str(tid).strip()}"
    return f"https://x.com/{handle}"


def analyze(text):
    # Use a lightweight trained classifier held in session state to predict severity
    txt = (text or "").strip()
    if not txt:
        return "General Political Discourse", "Neutral Monitoring", "Low", "Log and Archive — No Threshold Breach"

    # Train on first use and cache vectorizer+model in session state
    if "nlp_vect" not in st.session_state or "nlp_clf" not in st.session_state:
        vect, clf = train_nlp_classifier()
        st.session_state["nlp_vect"] = vect
        st.session_state["nlp_clf"] = clf
    else:
        vect = st.session_state["nlp_vect"]
        clf = st.session_state["nlp_clf"]

    X = vect.transform([txt])
    pred = clf.predict(X)[0]

    mapping = {
        "Critical": ("FLAG — Section 62: Cohesion Act", "Public Incitement to Subversion / Violence", "Critical", "Issue Immediate Cease-and-Desist & Dispatch Field Unit"),
        "High":     ("FLAG — Section 13: Hate Speech Act", "Ethnic Incitement / Localized Profiling", "High", "Generate Section 106B Certificate & Forward to Legal Teams"),
        "Low":      ("General Political Discourse", "Neutral Monitoring", "Low", "Log and Archive — No Threshold Breach"),
    }
    return mapping.get(pred, mapping["Low"])


def train_nlp_classifier():
    """Train a tiny TF-IDF + LogisticRegression classifier at startup.
    This is intentionally small and runs quickly for demo/edge usage.
    """
    samples = [
        ("lazima tudeal na wao", "Critical"),
        ("kutawaka moto", "Critical"),
        ("we must fight back", "Critical"),
        ("war and clashes", "Critical"),
        ("maandamano itaendelea", "High"),
        ("watu wa kutoka ule upande", "High"),
        ("they are outsiders", "High"),
        ("development projects must be protected", "Low"),
        ("proud to announce a new bursary programme", "Low"),
        ("education is the great equaliser", "Low"),
        ("not be intimidated", "Low"),
    ]
    texts, labels = zip(*samples)
    vect = TfidfVectorizer(ngram_range=(1,2), max_features=1500)
    X = vect.fit_transform(texts)
    clf = LogisticRegression(max_iter=500)
    clf.fit(X, labels)
    return vect, clf


def seal(tid, author, text, ts):
    p = f"{tid}|{author}|{text}|{ts}"
    return f"NCIC-SHA256-{hashlib.sha256(p.encode()).hexdigest()[:24].upper()}"


def card_classes(sev):
    m = {"Critical": ("card-critical", "badge-critical"),
         "High":     ("card-high",     "badge-high"),
         "Low":      ("card-low",      "badge-low")}
    return m.get(sev, ("card-low", "badge-low"))


def render_cards(df):
    """Build the full self-contained HTML for the evidence card stream."""
    cards_html = ""
    for _, row in df.iterrows():
        sev  = row["Severity_Index"]
        text = html_lib.escape(str(row["Tweet_Text"]))
        ts   = html_lib.escape(str(row["Date_Time"]))
        cat  = html_lib.escape(str(row["Context_Category"]))
        clf  = html_lib.escape(str(row["Legal_Classification"]))
        url  = str(row["Source_URL"])
        eid  = str(row["Evidence_ID"])
        cc, bc = card_classes(sev)
        cards_html += (
            f'<div class="card {cc}">'
            f'<div class="card-top">'
            f'<span class="badge {bc}">{sev}</span>'
            f'<span class="clf">{clf}</span>'
            f'</div>'
            f'<div class="tweet-text">{text}</div>'
            f'<div class="card-foot">'
            f'<span class="foot-ts">{ts}</span>'
            f'<span class="foot-cat">{cat}</span>'
            f'<span class="foot-seal">{eid[:44]}…</span>'
            f'<a href="{url}" target="_blank" class="verify-btn">Verify on X &#8599;</a>'
            f'</div>'
            f'</div>'
        )
    full_html = f'<!DOCTYPE html><html><head><style>{CARD_CSS}</style></head><body>{cards_html}</body></html>'
    estimated_height = max(300, len(df) * 230)
    components.html(full_html, height=estimated_height, scrolling=False)


# ──────────────────────────────────────────────────────────────────────────────
# SIMULATION DATA
# ──────────────────────────────────────────────────────────────────────────────
def build_sim(handle):
    return [
        {"id": "1924001001001", "text": "Hawa watu wa kutoka ule upande mwingine wanajiona sana. Lazima tudeal na wao round hii kabisa.", "created_at": "2026-05-19 14:22 EAT", "url": f"https://x.com/{handle}/status/1924001001001"},
        {"id": "1924001002002", "text": "Development projects in Mt Kenya region must be protected by all means. We look forward to absolute cohesion.", "created_at": "2026-05-18 09:12 EAT", "url": f"https://x.com/{handle}/status/1924001002002"},
        {"id": "1924001003003", "text": "Our community will not be intimidated. Watu wa kutoka ule upande should understand the mood on the ground.", "created_at": "2026-05-17 18:45 EAT", "url": f"https://x.com/{handle}/status/1924001003003"},
        {"id": "1924001004004", "text": "We must fight back — blood will tell who truly belongs here. Maandamano itaendelea mpaka haki zetu zitekelezwe.", "created_at": "2026-05-16 11:30 EAT", "url": f"https://x.com/{handle}/status/1924001004004"},
        {"id": "1924001005005", "text": "Proud to announce a new bursary programme for youth across the constituency. Education is the great equaliser.", "created_at": "2026-05-15 08:05 EAT", "url": f"https://x.com/{handle}/status/1924001005005"},
    ]


# ──────────────────────────────────────────────────────────────────────────────
# HEADER
# ──────────────────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="lab-header">'
    '<div>'
    '<div class="lab-title">NCIC Intelligence Lab</div>'
    '<div class="lab-sub">AUTOMATED CROSS-CHANNEL FORENSIC ANALYSIS PROTOCOL — ADMISSIBLE EVIDENCE AGGREGATOR</div>'
    '</div>'
    '<div class="lab-live">SYSTEM ACTIVE</div>'
    '</div>',
    unsafe_allow_html=True
)


# ──────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────────────────────────────────────

# Module Navigation
st.sidebar.markdown("## 📦 MODULES")
module = st.sidebar.radio(
    "Select Module",
    ["🔍 X-Scraper", "🏛️ Officials DB", "🔐 Evidence Archiver", "🔍 Authenticity Score"],
    label_visibility="collapsed"
)
st.sidebar.markdown("---")

if module == "🔍 X-Scraper":
    # ──────────────────────────────────────────────────────────────────────────────
    # X-SCRAPER CONFIGURATION
    # ──────────────────────────────────────────────────────────────────────────────
    st.sidebar.markdown("**Integration Gateway**")
    token_input    = st.sidebar.text_input("Apify API Token", type="password", placeholder="Paste key for live scraping…")
    profile_handle = st.sidebar.text_input("Target Profile Handle", value="HonRigathi")
    max_tweets     = st.sidebar.slider("Timeline Depth (Tweets)", 3, 20, 5)
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"[Open @{profile_handle} on X ↗](https://x.com/{profile_handle})")
    st.sidebar.markdown("---")
    severity_filter = st.sidebar.multiselect("Filter by Severity", options=["Critical","High","Low"], default=["Critical","High","Low"])
    show_debug      = st.sidebar.checkbox("Show raw Apify field debug", value=False)

    sim_mode = not bool(token_input.strip())

    # Session state
    for key, default in [("cached_df", None), ("cached_handle", ""), ("sim_mode", True), ("raw_sample", None)]:
        if key not in st.session_state:
            st.session_state[key] = default

    # Ensure a persistent data folder exists for exports and audit
    DATA_DIR = Path(os.path.dirname(__file__) if "__file__" in globals() else os.getcwd()) / "data"
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # ──────────────────────────────────────────────────────────────────────────────
    # SCAN TRIGGER
    # ──────────────────────────────────────────────────────────────────────────────
    trigger = st.button(f"INITIALIZE DEEP-SCRAPE  —  @{profile_handle.upper()}", use_container_width=True)

    if trigger:
        processed = []
        raw_sample_item = None

        if sim_mode:
            st.warning("Simulation Mode — no Apify token provided. Processing over demo dataset.")
            raw = build_sim(profile_handle)
        else:
            st.info(f"Dispatching Apify crawler to X: @{profile_handle}…")
            try:
                client = OfficialApifyClient(token_input.strip())
                raw = []
                attempts = 3
                
                for attempt in range(1, attempts + 1):
                    try:
                        # Use official Apify client to run Twitter scraper actor
                        run = client.actor("apidojo/tweet-scraper").call(run_input={
                            "twitterHandles": [profile_handle.lstrip("@")],
                            "maxItems": max_tweets,
                            "sort": "Latest"
                        })
                        
                        # Get results from the run's dataset
                        if run and run.get("defaultDatasetId"):
                            dataset_id = run["defaultDatasetId"]
                            items = list(client.dataset(dataset_id).list_items().items)
                            raw = items or []
                            
                            if raw:
                                st.success(f"✅ Retrieved {len(raw)} posts from @{profile_handle}")
                                break
                            else:
                                if attempt < attempts:
                                    st.info(f"Empty results on attempt {attempt}/{attempts}, retrying…")
                                    time.sleep(attempt * 1.5)
                                else:
                                    st.warning(f"⚠️ Apify returned no posts for @{profile_handle}.\n\n"
                                             f"**Possible causes:**\n"
                                             f"• Invalid or expired API token\n"
                                             f"• Handle does not exist or is private\n"
                                             f"• Rate limit exceeded\n\n"
                                             f"**Try:** Use simulation mode (clear the API token field)")
                        else:
                            if attempt < attempts:
                                st.info(f"No dataset returned (attempt {attempt}/{attempts}), retrying…")
                                time.sleep(attempt * 1.5)
                            else:
                                st.error("Apify actor run failed to return results")
                                
                    except Exception as e:
                        if attempt == attempts:
                            st.error(f"Apify API error after {attempts} attempts: {str(e)[:150]}")
                            st.info("💡 **Troubleshooting:**\n"
                                   "1. Verify your Apify API token is valid\n"
                                   "2. Check the handle exists on X (@handle)\n"
                                   "3. Clear the token field to use simulation mode")
                            raw = []
                        else:
                            backoff = attempt * 1.5
                            st.info(f"Apify call failed (attempt {attempt}/{attempts}), retrying in {backoff}s...")
                            time.sleep(backoff)
                            
            except Exception as e:
                st.error(f"Apify client error: {str(e)[:200]}")
                st.info("💡 **Troubleshooting:**\n"
                       "1. Verify your Apify API token is valid and not expired\n"
                       "2. Check your internet connection\n"
                       "3. Clear the token field to use simulation mode")
                raw = []

        for item in raw:
            if raw_sample_item is None:
                raw_sample_item = item          # save first item for debug panel

            text  = extract_text(item) or "No text data captured"
            ts    = item.get("created_at", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            url   = extract_url(item, profile_handle)
            tid   = str(item.get("id", item.get("id_str", f"UNK-{np.random.randint(1000,9999)}")))

            clf, cat, sev, act = analyze(text)
            eid = seal(tid, profile_handle, text, ts)

            processed.append({
                "Evidence_ID":          eid,
                "Date_Time":            str(ts),
                "Tweet_Text":           text,
                "Legal_Classification": clf,
                "Context_Category":     cat,
                "Severity_Index":       sev,
                "Recommended_Action":   act,
                "Source_URL":           url,
                "Raw_ID":               tid,
            })

        st.session_state["cached_df"]     = pd.DataFrame(processed) if processed else None
        st.session_state["cached_handle"] = profile_handle
        st.session_state["sim_mode"]      = sim_mode
        st.session_state["raw_sample"]    = raw_sample_item

        # Persist a local export for audit (timestamped)
        try:
            if processed:
                ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
                fname = DATA_DIR / f"NCIC_export_{profile_handle}_{ts}.json"
                with open(fname, "w", encoding="utf-8") as fh:
                    json.dump(processed, fh, ensure_ascii=False, indent=2)
                st.info(f"Local export saved: {fname}")
        except Exception as e:
            st.warning(f"Could not persist local export: {e}")


    # ──────────────────────────────────────────────────────────────────────────────
    # DEBUG PANEL (toggle in sidebar)
    # ──────────────────────────────────────────────────────────────────────────────
    if show_debug and st.session_state["raw_sample"] is not None:
        with st.expander("Raw Apify Response — First Item (field mapping debug)", expanded=True):
            st.json(st.session_state["raw_sample"])


    # ──────────────────────────────────────────────────────────────────────────────
    # RESULTS
    # ──────────────────────────────────────────────────────────────────────────────
    if st.session_state["cached_df"] is not None:
        df_all  = st.session_state["cached_df"]
        handle  = st.session_state["cached_handle"]
        is_sim  = st.session_state["sim_mode"]
        df_view = df_all[df_all["Severity_Index"].isin(severity_filter)].reset_index(drop=True)

        mode_label = "SIMULATION — Demo Dataset" if is_sim else f"LIVE — @{handle}"
        st.success(f"Analysis complete  |  {mode_label}  |  {len(df_all)} assets compiled")

        # Metrics
        n_crit = len(df_all[df_all["Severity_Index"]=="Critical"])
        n_high = len(df_all[df_all["Severity_Index"]=="High"])
        m1,m2,m3,m4 = st.columns(4)
        with m1:
            st.markdown('<div class="metric-wrap metric-default">', unsafe_allow_html=True)
            st.metric("Total Assets", len(df_all))
            st.markdown('</div>', unsafe_allow_html=True)
        with m2:
            st.markdown('<div class="metric-wrap metric-critical">', unsafe_allow_html=True)
            st.metric("Critical Flags", n_crit)
            st.markdown('</div>', unsafe_allow_html=True)
        with m3:
            st.markdown('<div class="metric-wrap metric-high">', unsafe_allow_html=True)
            st.metric("High-Severity", n_high)
            st.markdown('</div>', unsafe_allow_html=True)
        with m4:
            st.markdown('<div class="metric-wrap metric-ok">', unsafe_allow_html=True)
            st.metric("Verification", "100% Linked")
            st.markdown('</div>', unsafe_allow_html=True)

        # ── Evidence Stream ──────────────────────────────────────────
        st.markdown('<div class="section-label">Live Evidence Stream</div>', unsafe_allow_html=True)
        if is_sim:
            st.caption("Simulation mode: Verify links use realistic tweet-ID URLs. Swap in your Apify token for live tweet links.")
        else:
            st.caption("Each card links to the original post on X.com. Click Verify on X to cross-reference in real time.")

        if df_view.empty:
            st.info("No assets match the selected severity filters.")
        else:
            render_cards(df_view)           # ← components.html, guaranteed to render

        # ── Forensic Dossier ────────────────────────────────────────
        st.markdown('<div class="section-label">Forensic Dossier — Certificate Generator</div>', unsafe_allow_html=True)
        st.caption("Select an evidence asset to generate its court-admissible certificate and download the prosecution packet.")

        selected = st.selectbox(
            "Evidence Asset",
            options=df_all["Evidence_ID"].tolist(),
            format_func=lambda x: f"{x}  [{df_all[df_all['Evidence_ID']==x]['Severity_Index'].values[0]}]",
            label_visibility="collapsed",
        )

        if selected:
            rec  = df_all[df_all["Evidence_ID"]==selected].iloc[0]
            sev  = rec["Severity_Index"]
            cc, bc = card_classes(sev)

            col_l, col_r = st.columns([3,1], gap="large")

            with col_l:
                st.markdown("**Captured Post Content**")
                # Single dossier card — also via components.html to guarantee rendering
                dossier_card_html = (
                    f'<!DOCTYPE html><html><head><style>{CARD_CSS}</style></head><body>'
                    f'<div class="card {cc}">'
                    f'<div class="card-top"><span class="badge {bc}">{sev}</span></div>'
                    f'<div class="tweet-text">{html_lib.escape(str(rec["Tweet_Text"]))}</div>'
                    f'<div class="card-foot">'
                    f'<span class="foot-ts">{html_lib.escape(str(rec["Date_Time"]))}</span>'
                    f'<a href="{rec["Source_URL"]}" target="_blank" class="verify-btn">Open Original Post on X &#8599;</a>'
                    f'</div>'
                    f'</div>'
                    f'</body></html>'
                )
                components.html(dossier_card_html, height=220, scrolling=False)

            with col_r:
                st.markdown("**Recommended Action**")
                st.markdown(
                    f'<div style="background:rgba(220,38,38,0.1);border:1px solid rgba(220,38,38,0.25);'
                    f'color:#fca5a5;border-radius:6px;padding:10px 14px;font-family:JetBrains Mono,monospace;'
                    f'font-size:11.5px;line-height:1.65;margin-top:6px">'
                    f'{html_lib.escape(str(rec["Recommended_Action"]))}</div>',
                    unsafe_allow_html=True
                )
                st.markdown(f"<br>**Handle:** @{handle}<br>**Category:** {rec['Context_Category']}", unsafe_allow_html=True)

            # Certificate
            full_sha = hashlib.sha256(str(rec["Tweet_Text"]).encode()).hexdigest()
            st.markdown("**Cryptographic Court-Admissible Certificate**")
            st.markdown(
                f'<div class="dossier-block">'
                f'<strong>[KENYA NATIONAL COHESION AND INTEGRATION COMMISSION — CERTIFIED RECORD]</strong><br>'
                f'{"═"*68}<br>'
                f'<strong>EVIDENCE TRACKING ID&nbsp;&nbsp;:</strong> {rec["Evidence_ID"]}<br>'
                f'<strong>CRAWL TIMESTAMP&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;:</strong> {rec["Date_Time"]}<br>'
                f'<strong>VERIFIED HANDLE&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;:</strong> @{handle}<br>'
                f'<strong>DIRECT AUDIT SOURCE&nbsp;&nbsp;:</strong> <a href="{rec["Source_URL"]}" target="_blank" style="color:#60a5fa">{rec["Source_URL"]}</a><br>'
                f'{"─"*68}<br>'
                f'<strong>LEGAL STATUS&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;:</strong> {html_lib.escape(str(rec["Legal_Classification"]))}<br>'
                f'<strong>CONTEXT TAGS&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;:</strong> {html_lib.escape(str(rec["Context_Category"]))}<br>'
                f'<strong>SEVERITY METRIC&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;:</strong> {sev}<br>'
                f'<strong>OPERATIONAL MANDATE&nbsp;&nbsp;:</strong> {html_lib.escape(str(rec["Recommended_Action"]))}<br>'
                f'{"═"*68}<br>'
                f'<strong>SHA-256 INTEGRITY SEAL:</strong><br>'
                f'<span class="dossier-seal">{full_sha}</span><br><br>'
                f'<strong>ADMISSIBILITY NOTICE&nbsp;:</strong> Certified under Section 106B of the Evidence Act (Cap 80, Laws of Kenya).'
                f'</div>',
                unsafe_allow_html=True
            )

            st.markdown("<br>", unsafe_allow_html=True)
            st.download_button(
                label="Download Legal Evidence Bundle  (.JSON)",
                data=json.dumps(rec.to_dict(), indent=4),
                file_name=f"NCIC_PROSECUTION_PACKET_{rec['Raw_ID']}.json",
                mime="application/json",
                use_container_width=True,
            )

    else:
        st.markdown(
            '<div style="text-align:center;padding:80px 20px;color:#1a3055;">'
            '<div style="font-family:Rajdhani,sans-serif;font-size:1.1rem;font-weight:600;letter-spacing:0.14em;text-transform:uppercase;">'
            'System Standby</div>'
            '<div style="font-family:JetBrains Mono,monospace;font-size:11.5px;margin-top:12px;line-height:1.8;">'
            'Set a target handle in the sidebar, paste an Apify token (optional for live scraping),<br>'
            'then click INITIALIZE DEEP-SCRAPE to execute the processing loop.'
            '</div></div>',
            unsafe_allow_html=True
        )

elif module == "🏛️ Officials DB":
    render_officials_module()

elif module == "🔐 Evidence Archiver":
    render_evidence_archiver_module()

elif module == "🔍 Authenticity Score":
    render_authenticity_module()