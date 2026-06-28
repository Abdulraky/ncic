"""
Streamlit interface for Digital Evidence Archiver (Refactored with Services)
Uses new EvidenceService and CollectorService for clean architecture
"""

import streamlit as st
import pandas as pd
import json
from datetime import datetime
import hashlib

from database import SessionLocal
from services import PoliticianService, EvidenceService, CollectorService
from config import STORAGE_PATH

def render_evidence_archiver_module():
    """Render the Digital Evidence Archiver module"""
    
    st.markdown("""
    <div style="background: linear-gradient(90deg, #dc2626 0%, #991b1b 100%); padding: 2rem; border-radius: 12px; margin-bottom: 2rem;">
        <h1 style="color: white; margin: 0;">🔐 DIGITAL EVIDENCE ARCHIVER</h1>
        <p style="color: #fee2e2; margin: 0.5rem 0 0 0;">Module 2 • Forensic Collection & Verification System</p>
    </div>
    """, unsafe_allow_html=True)
    
    db = SessionLocal()
    
    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📥 Start Collection", "📊 Active Collections", "📋 Evidence Manifest", "🔍 Verification"])
    
    # ════════════════════════════════════════════════════════════════════════════════
    # TAB 1: START COLLECTION
    # ════════════════════════════════════════════════════════════════════════════════
    with tab1:
        st.subheader("Initiate Digital Evidence Collection")
        
        st.info("""
        **Collection Process:**
        1. Select an official from the database
        2. System collects newest posts from all social media
        3. Metadata extracted and stored
        4. All media downloaded (images, videos)
        5. Cryptographic hashes generated
        6. Everything stored in sealed archive
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Get officials from service
            officials = PoliticianService.get_all_officials(db)
            
            if officials:
                official_names = {i: f"{o.name} ({o.office})" for i, o in enumerate(officials)}
                selected_idx = st.selectbox("Select Official", range(len(officials)), 
                                           format_func=lambda i: official_names[i])
                selected_official = officials[selected_idx]
            else:
                st.warning("No officials found. Please import officials first in Module 1.")
                selected_official = None
            
            # Apify API Token input
            st.markdown("**Apify API Configuration**")
            apify_token = st.text_input(
                "Apify API Token", 
                type="password",
                placeholder="Paste your Apify API token for live scraping",
                help="Get token from https://apify.com"
            )
        
        with col2:
            if selected_official:
                st.markdown(f"""
                **Selected Official:**
                - Name: {selected_official.name}
                - Office: {selected_official.office}
                - County: {selected_official.county}
                - Party: {selected_official.party}
                
                **Social Media Handles:**
                - Twitter: @{selected_official.twitter or 'N/A'}
                - Instagram: @{selected_official.instagram or 'N/A'}
                - TikTok: @{selected_official.tiktok or 'N/A'}
                """)
        
        if selected_official and st.button("🚀 START FORENSIC COLLECTION", use_container_width=True):
            if not apify_token:
                st.error("⚠ Apify API token required for live scraping. Paste your token above.")
            else:
                with st.spinner("Initializing collection..."):
                    # Create collection
                    collection = EvidenceService.create_collection(
                        db,
                        selected_official.official_id,
                        selected_official.name
                    )
                    st.success(f"✓ Collection started (ID: {collection.id})")
                    
                    # Initialize collector
                    collector = CollectorService(apify_token)
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    results_container = st.container()
                    
                    try:
                        all_posts = []
                        total_posts = 0
                        
                        # Collect from Twitter
                        if selected_official.twitter:
                            status_text.text("🐦 Scraping Twitter posts...")
                            progress_bar.progress(0.15)
                            
                            try:
                                twitter_posts = collector.collect_twitter(selected_official.twitter)
                                all_posts.extend([("twitter", p) for p in twitter_posts])
                                total_posts += len(twitter_posts)
                                results_container.success(f"✅ Twitter: {len(twitter_posts)} posts")
                            except Exception as e:
                                results_container.warning(f"⚠ Twitter scrape failed: {str(e)}")
                        
                        # Collect from Instagram
                        if selected_official.instagram:
                            status_text.text("📷 Scraping Instagram posts...")
                            progress_bar.progress(0.40)
                            
                            try:
                                insta_posts = collector.collect_instagram(selected_official.instagram)
                                all_posts.extend([("instagram", p) for p in insta_posts])
                                total_posts += len(insta_posts)
                                results_container.success(f"✅ Instagram: {len(insta_posts)} posts")
                            except Exception as e:
                                results_container.warning(f"⚠ Instagram scrape failed: {str(e)}")
                        
                        # Collect from TikTok
                        if selected_official.tiktok:
                            status_text.text("🎵 Scraping TikTok posts...")
                            progress_bar.progress(0.65)
                            
                            try:
                                tiktok_posts = collector.collect_tiktok(selected_official.tiktok)
                                all_posts.extend([("tiktok", p) for p in tiktok_posts])
                                total_posts += len(tiktok_posts)
                                results_container.success(f"✅ TikTok: {len(tiktok_posts)} posts")
                            except Exception as e:
                                results_container.warning(f"⚠ TikTok scrape failed: {str(e)}")
                        
                        # Store posts in database
                        status_text.text("💾 Storing evidence items...")
                        progress_bar.progress(0.80)
                        
                        for platform, post in all_posts:
                            try:
                                post_json = json.dumps(post)
                                sha256_hash = hashlib.sha256(post_json.encode()).hexdigest()
                                md5_hash = hashlib.md5(post_json.encode()).hexdigest()
                                
                                EvidenceService.add_evidence_item(
                                    db,
                                    collection.id,
                                    f"social_media_post_{platform}",
                                    post.get("url") or post.get("link") or "",
                                    sha256_hash=sha256_hash,
                                    md5_hash=md5_hash,
                                    file_size_bytes=len(post_json),
                                    mime_type="application/json",
                                    captured_date=datetime.fromisoformat(
                                        post.get("timestamp") or post.get("created_at") or datetime.now().isoformat()
                                    ) if isinstance(post.get("timestamp"), str) or isinstance(post.get("created_at"), str) else datetime.now()
                                )
                            except Exception as e:
                                results_container.warning(f"⚠ Error storing item: {str(e)}")
                        
                        # Update collection status
                        EvidenceService.update_collection_status(
                            db,
                            collection.id,
                            "completed",
                            post_count=total_posts
                        )
                        
                        progress_bar.progress(1.0)
                        status_text.text("✅ Collection complete")
                        results_container.success(f"✅ Successfully stored {total_posts} evidence items")
                        
                    except Exception as e:
                        st.error(f"❌ Collection failed: {str(e)}")
    
    # ════════════════════════════════════════════════════════════════════════════════
    # TAB 2: ACTIVE COLLECTIONS
    # ════════════════════════════════════════════════════════════════════════════════
    with tab2:
        st.subheader("Active Collections")
        
        collections = EvidenceService.get_all_collections(db)
        
        if collections:
            df_collections = pd.DataFrame([{
                "ID": c.id,
                "Official": c.official_name,
                "Status": c.status,
                "Posts": c.post_count,
                "Date": c.collection_date.strftime("%Y-%m-%d") if c.collection_date else "-"
            } for c in collections])
            
            st.dataframe(df_collections, use_container_width=True)
        else:
            st.info("No collections yet. Start a collection in the 'Start Collection' tab.")
    
    # ════════════════════════════════════════════════════════════════════════════════
    # TAB 3: EVIDENCE MANIFEST
    # ════════════════════════════════════════════════════════════════════════════════
    with tab3:
        st.subheader("Evidence Manifest")
        
        collections = EvidenceService.get_all_collections(db)
        
        if collections:
            selected_collection = st.selectbox(
                "Select Collection",
                collections,
                format_func=lambda c: f"{c.official_name} (ID: {c.id})"
            )
            
            items = EvidenceService.get_collection_items(db, selected_collection.id)
            
            if items:
                df_items = pd.DataFrame([{
                    "Type": item.item_type,
                    "URL": item.source_url[:60] + "..." if len(item.source_url or "") > 60 else item.source_url,
                    "SHA256": item.sha256_hash[:16] + "..." if item.sha256_hash else "-",
                    "Size": f"{item.file_size_bytes or 0} bytes",
                    "Date": item.captured_date.strftime("%Y-%m-%d") if item.captured_date else "-"
                } for item in items])
                
                st.dataframe(df_items, use_container_width=True)
            else:
                st.info("No items in this collection.")
        else:
            st.info("No collections available.")
    
    # ════════════════════════════════════════════════════════════════════════════════
    # TAB 4: VERIFICATION
    # ════════════════════════════════════════════════════════════════════════════════
    with tab4:
        st.subheader("Evidence Verification Status")
        st.info("See Module 3 (Authenticity Score) for detailed verification results.")
    
    db.close()
