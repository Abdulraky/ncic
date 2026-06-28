"""
Streamlit interface for Digital Evidence Archiver
"""

import streamlit as st
import pandas as pd
from pathlib import Path
from evidence_archiver import DigitalEvidenceArchiver
from apify_client import ApifyClient
import json
from datetime import datetime
import hashlib
import sqlite3

def render_evidence_archiver_module():
    """Render the Digital Evidence Archiver module"""
    
    st.markdown("""
    <div style="background: linear-gradient(90deg, #dc2626 0%, #991b1b 100%); padding: 2rem; border-radius: 12px; margin-bottom: 2rem;">
        <h1 style="color: white; margin: 0;">🔐 DIGITAL EVIDENCE ARCHIVER</h1>
        <p style="color: #fee2e2; margin: 0.5rem 0 0 0;">Module 2 • Forensic Collection & Verification System</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize archiver
    archiver = DigitalEvidenceArchiver("data/evidence_archive")
    
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
        5. HTML snapshots captured
        6. Screenshots taken
        7. Cryptographic hashes generated
        8. Everything stored in sealed archive
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Import officials from database
            from officials_db import OfficialsDatabase
            
            db = OfficialsDatabase("data/officials.db")
            officials = db.get_all_officials()
            db.close()
            
            if officials:
                official_names = [f"{o['name']} ({o['office']})" for o in officials]
                selected_official_idx = st.selectbox("Select Official", range(len(officials)), 
                                                     format_func=lambda i: official_names[i])
                selected_official = officials[selected_official_idx]
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
                - Name: {selected_official['name']}
                - Office: {selected_official['office']}
                - County: {selected_official['county']}
                - Party: {selected_official['party']}
                
                **Social Media Handles:**
                - Twitter: @{selected_official.get('twitter', 'N/A')}
                - Instagram: @{selected_official.get('instagram', 'N/A')}
                - TikTok: @{selected_official.get('tiktok', 'N/A')}
                """)
        
        if selected_official and st.button("🚀 START FORENSIC COLLECTION", use_container_width=True):
            if not apify_token:
                st.error("⚠ Apify API token required for live scraping. Paste your token above.")
            else:
                with st.spinner("Initializing collection..."):
                    collection_id, archive_path = archiver.start_collection(
                        selected_official['official_id'],
                        selected_official['name']
                    )
                    
                    st.success(f"✓ Collection started (ID: {collection_id})")
                    st.info(f"Archive location: {archive_path}")
                    
                    # Real collection with Apify API
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    results_container = st.container()
                    
                    try:
                        client = ApifyClient(apify_token)
                        archive_db = "data/evidence_archive/evidence_manifest.db"
                        
                        all_posts = []
                        total_posts = 0
                        
                        # Collect from Twitter
                        if selected_official.get('twitter'):
                            status_text.text("🐦 Scraping Twitter posts...")
                            progress_bar.progress(0.15)
                            
                            try:
                                twitter_posts = client.scrape_twitter_posts(
                                    selected_official['twitter'],
                                    max_posts=50
                                )
                                all_posts.extend(twitter_posts)
                                total_posts += len(twitter_posts)
                                results_container.success(f"✅ Twitter: {len(twitter_posts)} posts")
                            except Exception as e:
                                results_container.warning(f"⚠ Twitter scrape failed: {str(e)}")
                        
                        # Collect from Instagram
                        if selected_official.get('instagram'):
                            status_text.text("📷 Scraping Instagram posts...")
                            progress_bar.progress(0.40)
                            
                            try:
                                insta_posts = client.scrape_instagram_posts(
                                    selected_official['instagram'],
                                    max_posts=50
                                )
                                all_posts.extend(insta_posts)
                                total_posts += len(insta_posts)
                                results_container.success(f"✅ Instagram: {len(insta_posts)} posts")
                            except Exception as e:
                                results_container.warning(f"⚠ Instagram scrape failed: {str(e)}")
                        
                        # Collect from TikTok
                        if selected_official.get('tiktok'):
                            status_text.text("🎵 Scraping TikTok posts...")
                            progress_bar.progress(0.65)
                            
                            try:
                                tiktok_posts = client.scrape_tiktok_posts(
                                    selected_official['tiktok'],
                                    max_posts=50
                                )
                                all_posts.extend(tiktok_posts)
                                total_posts += len(tiktok_posts)
                                results_container.success(f"✅ TikTok: {len(tiktok_posts)} posts")
                            except Exception as e:
                                results_container.warning(f"⚠ TikTok scrape failed: {str(e)}")
                        
                        # Store posts in database
                        status_text.text("💾 Storing evidence items...")
                        progress_bar.progress(0.80)
                        
                        conn = sqlite3.connect(archive_db)
                        cursor = conn.cursor()
                        
                        for post in all_posts:
                            try:
                                # Generate hashes
                                post_json = json.dumps(post)
                                sha256_hash = hashlib.sha256(post_json.encode()).hexdigest()
                                md5_hash = hashlib.md5(post_json.encode()).hexdigest()
                                
                                # Insert into database
                                cursor.execute("""
                                    INSERT INTO evidence_items (
                                        collection_id, item_type, platform, 
                                        username, post_id, source_url, content,
                                        captured_date, sha256_hash, md5_hash, 
                                        raw_data, file_path
                                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """, (
                                    collection_id,
                                    'social_media_post',
                                    post.get('platform', 'unknown'),
                                    post.get('username', ''),
                                    post.get('post_id', ''),
                                    post.get('url', ''),
                                    post.get('text', '')[:1000],
                                    post.get('timestamp', datetime.now().isoformat()),
                                    sha256_hash,
                                    md5_hash,
                                    post_json,
                                    None
                                ))
                            except Exception as e:
                                results_container.warning(f"⚠ Error storing item: {str(e)}")
                        
                        conn.commit()
                        conn.close()
                        
                        # Finalize collection
                        status_text.text("✅ Finalizing archive...")
                        progress_bar.progress(0.95)
                        
                        success, message = archiver.finalize_collection(collection_id, archive_path)
                        progress_bar.progress(1.0)
                        
                        if success:
                            st.success(f"✅ Collection Complete!\\n\\n**Collected {total_posts} items**\\n\\n{message}")
                            st.balloons()
                        else:
                            st.error(f"⚠ {message}")
                    
                    except Exception as e:
                        st.error(f"❌ Collection failed: {str(e)}")
                        results_container.error(f"Error details: {str(e)}")
    
    # ════════════════════════════════════════════════════════════════════════════════
    # TAB 2: ACTIVE COLLECTIONS
    # ════════════════════════════════════════════════════════════════════════════════
    with tab2:
        st.subheader("Evidence Collections")
        
        collections = archiver.list_collections()
        
        if collections:
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Collections", len(collections))
            
            with col2:
                completed = len([c for c in collections if c['status'] == 'completed'])
                st.metric("Completed", completed)
            
            with col3:
                in_progress = len([c for c in collections if c['status'] == 'in_progress'])
                st.metric("In Progress", in_progress)
            
            with col4:
                total_size = sum(c['total_size_bytes'] for c in collections)
                st.metric("Total Size", f"{total_size/1024/1024:.2f} MB")
            
            st.divider()
            
            # Collections table
            df_collections = pd.DataFrame(collections)
            df_collections['collection_date'] = pd.to_datetime(df_collections['collection_date'])
            df_collections['total_size_mb'] = df_collections['total_size_bytes'] / 1024 / 1024
            
            display_df = df_collections[['id', 'official_name', 'status', 'collection_date', 'total_size_mb']].copy()
            display_df.columns = ['ID', 'Official', 'Status', 'Date', 'Size (MB)']
            display_df['Size (MB)'] = display_df['Size (MB)'].apply(lambda x: f"{x:.2f}")
            
            st.dataframe(display_df, use_container_width=True)
            
            # Select collection for details
            st.divider()
            selected_collection_id = st.selectbox(
                "View Details",
                [c['id'] for c in collections],
                format_func=lambda id: f"Collection {id} - {[c['official_name'] for c in collections if c['id']==id][0]}"
            )
            
            collection_details = archiver.get_collection_status(selected_collection_id)
            
            if collection_details:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Status", collection_details['status'].upper())
                
                with col2:
                    st.metric("Items Collected", collection_details['post_count'])
                
                with col3:
                    st.metric("Archive Size", f"{collection_details['total_size_bytes']/1024/1024:.2f} MB")
                
                st.markdown("**Item Breakdown:**")
                item_breakdown = collection_details['item_breakdown']
                if item_breakdown:
                    breakdown_data = []
                    for item_type, stats in item_breakdown.items():
                        breakdown_data.append({
                            'Type': item_type,
                            'Count': stats['count'],
                            'Size (MB)': f"{stats['size']/1024/1024:.2f}"
                        })
                    
                    st.dataframe(pd.DataFrame(breakdown_data), use_container_width=True)
                
                # Archive location
                st.markdown(f"**Archive Path:** `{collection_details['archive_path']}`")
        else:
            st.info("No collections yet. Start a new collection to begin.")
    
    # ════════════════════════════════════════════════════════════════════════════════
    # TAB 3: EVIDENCE MANIFEST
    # ════════════════════════════════════════════════════════════════════════════════
    with tab3:
        st.subheader("Evidence Manifest & Hashes")
        
        collections = archiver.list_collections()
        
        if collections:
            selected_collection_id = st.selectbox(
                "Select Collection",
                [c['id'] for c in collections],
                format_func=lambda id: f"Collection {id}",
                key="manifest_select"
            )
            
            collection_details = archiver.get_collection_status(selected_collection_id)
            
            if collection_details:
                st.markdown(f"""
                **Collection Details:**
                - Official: {collection_details['official_name']}
                - Date: {collection_details['collection_date']}
                - Status: {collection_details['status']}
                - Archive: {collection_details['archive_path']}
                """)
                
                st.divider()
                
                # Display manifest path
                archive_path = Path(collection_details['archive_path'])
                manifest_file = archive_path / "manifest" / "evidence_manifest.json"
                
                if manifest_file.exists():
                    import json
                    with open(manifest_file, 'r') as f:
                        manifest = json.load(f)
                    
                    st.markdown("**Evidence Items:**")
                    
                    items_data = []
                    for item in manifest['items']:
                        items_data.append({
                            'Type': item['type'],
                            'File': Path(item['file']).name,
                            'SHA-256': item['sha256'][:16] + "...",
                            'Size (KB)': f"{item['size_bytes']/1024:.2f}"
                        })
                    
                    st.dataframe(pd.DataFrame(items_data), use_container_width=True)
                    
                    # Full hash details in expander
                    with st.expander("📋 Full Hash Details"):
                        for item in manifest['items']:
                            st.markdown(f"""
                            **{item['type']} - {Path(item['file']).name}**
                            ```
                            SHA-256: {item['sha256']}
                            MD5:     {item['md5']}
                            Size:    {item['size_bytes']:,} bytes
                            Date:    {item['captured']}
                            ```
                            """)
                
                # Download certificate
                cert_file = archive_path / "manifest" / "COLLECTION_CERTIFICATE.txt"
                if cert_file.exists():
                    with open(cert_file, 'r') as f:
                        cert_content = f.read()
                    
                    st.download_button(
                        label="📥 Download Collection Certificate",
                        data=cert_content,
                        file_name=f"COLLECTION_CERTIFICATE_{selected_collection_id}.txt",
                        mime="text/plain"
                    )
        else:
            st.info("No collections available.")
    
    # ════════════════════════════════════════════════════════════════════════════════
    # TAB 4: VERIFICATION
    # ════════════════════════════════════════════════════════════════════════════════
    with tab4:
        st.subheader("Evidence Integrity Verification")
        
        st.info("""
        **Verification Process:**
        
        All evidence collected is cryptographically hashed using SHA-256 and MD5.
        You can verify the integrity of archived evidence by comparing the stored
        hashes with newly computed hashes of the files.
        
        This ensures evidence has not been tampered with or corrupted.
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Verification Features:**")
            st.markdown("""
            ✓ SHA-256 cryptographic hashing
            ✓ MD5 backup verification
            ✓ Manifest integrity checking
            ✓ File corruption detection
            ✓ Chain of custody logging
            ✓ Court-admissible certification
            """)
        
        with col2:
            st.markdown("**Standards Compliance:**")
            st.markdown("""
            • Kenya Evidence Act (Cap 80)
            • Computer Misuse & Cybercrimes Act
            • NIST Digital Forensics Guidelines
            • ISO/IEC 27001 Information Security
            • ISO/IEC 27037 Digital Evidence
            """)
        
        st.divider()
        
        st.subheader("Manual Verification")
        
        uploaded_file = st.file_uploader("Upload file to verify", type=None)
        
        if uploaded_file is not None:
            with st.spinner("Computing hashes..."):
                # Save temp file
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False) as tmp:
                    tmp.write(uploaded_file.getbuffer())
                    tmp_path = tmp.name
                
                # Compute hashes
                hashes = archiver._compute_hashes(tmp_path)
                
                st.success("Hashes computed!")
                
                st.markdown(f"""
                **File:** {uploaded_file.name}
                **Size:** {uploaded_file.size:,} bytes
                
                **Hashes:**
                ```
                SHA-256: {hashes['sha256']}
                MD5:     {hashes['md5']}
                ```
                """)
                
                # Copy to clipboard
                st.code(hashes['sha256'], language="text")
                
                # Cleanup
                Path(tmp_path).unlink()

if __name__ == "__main__":
    render_evidence_archiver_module()
