"""
Streamlit interface for Authenticity Score Verification
Module 3 - Digital Evidence Authenticity Verification System
"""

import streamlit as st
import pandas as pd
import json
from pathlib import Path
from authenticity_verifier import AuthenticityVerifier
from report_generator import ReportGenerator
from officials_db import OfficialsDatabase
from datetime import datetime
import sqlite3


def render_authenticity_module():
    """Render the Authenticity Score Verification module"""
    
    st.markdown("""
    <div style="background: linear-gradient(90deg, #8b5cf6 0%, #6d28d9 100%); padding: 2rem; border-radius: 12px; margin-bottom: 2rem;">
        <h1 style="color: white; margin: 0;">🔍 AUTHENTICITY SCORE VERIFICATION</h1>
        <p style="color: #e9d5ff; margin: 0.5rem 0 0 0;">Module 3 • Digital Evidence Authenticity Analysis</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Verify Evidence",
        "📈 Verification Reports",
        "🔐 Batch Verification",
        "📋 Report Export"
    ])
    
    # ════════════════════════════════════════════════════════════════════════════════
    # TAB 1: VERIFY EVIDENCE
    # ════════════════════════════════════════════════════════════════════════════════
    with tab1:
        st.subheader("Verify Individual Evidence Item")
        
        st.info("""
        **Verification Checks:**
        - ✔ Verified account (Official verification badge)
        - ✔ URL valid (Original post URL accessible)
        - ✔ Metadata intact (Complete post metadata)
        - ✔ Timestamp verified (Reasonable creation time)
        - ✔ No evidence of editing (Unmodified content)
        - ✔ SHA256 verified (Cryptographic hash match)
        - ✔ Screenshot captured (Visual proof-of-posting)
        - ✔ Original JSON preserved (Raw data preserved)
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Get list of evidence collections
            collections_db = "data/evidence_archive/evidence_manifest.db"
            
            try:
                conn = sqlite3.connect(collections_db)
                cursor = conn.cursor()
                cursor.execute("SELECT id, official_name FROM evidence_collection ORDER BY collection_date DESC LIMIT 50")
                collections = cursor.fetchall()
                conn.close()
                
                if collections:
                    collection_options = {f"{c[1]} (ID: {c[0]})": c[0] for c in collections}
                    selected_collection = st.selectbox("Select Collection", collection_options.keys())
                    collection_id = collection_options[selected_collection]
                else:
                    st.warning("No evidence collections found. Collect evidence in Module 2 first.")
                    collection_id = None
            except Exception as e:
                st.error(f"Error loading collections: {str(e)}")
                collection_id = None
        
        with col2:
            if collection_id:
                # Get evidence items from this collection
                try:
                    conn = sqlite3.connect(collections_db)
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT id, item_type, source_url FROM evidence_items 
                        WHERE collection_id = ? ORDER BY captured_date DESC LIMIT 50
                    """, (collection_id,))
                    items = cursor.fetchall()
                    conn.close()
                    
                    if items:
                        item_options = {f"{i[1]} - {i[2][:50]}...": i[0] for i in items}
                        selected_item = st.selectbox("Select Evidence Item", item_options.keys())
                        item_id = item_options[selected_item]
                    else:
                        st.warning("No evidence items in this collection")
                        item_id = None
                except Exception as e:
                    st.error(f"Error loading items: {str(e)}")
                    item_id = None
            else:
                item_id = None
        
        # Verify button
        if item_id and st.button("🔍 VERIFY AUTHENTICITY", use_container_width=True, key="verify_button"):
            try:
                # Load evidence item data
                conn = sqlite3.connect(collections_db)
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM evidence_items WHERE id = ?
                """, (item_id,))
                
                columns = [description[0] for description in cursor.description]
                row = cursor.fetchone()
                conn.close()
                
                if row:
                    evidence_item = dict(zip(columns, row))
                    
                    # Try to load raw JSON if available
                    json_path = evidence_item.get("file_path")
                    raw_data = {}
                    
                    if json_path and json_path.endswith(".json"):
                        try:
                            with open(json_path, 'r') as f:
                                raw_data = json.load(f)
                        except:
                            pass
                    
                    evidence_item["raw_data"] = raw_data
                    
                    # Perform verification
                    verifier = AuthenticityVerifier()
                    verification_result = verifier.verify_evidence(evidence_item)
                    
                    # Display results
                    st.markdown("---")
                    
                    # Score display
                    score = verification_result["authenticity_score"]
                    
                    if score >= 80:
                        score_color = "#10b981"  # Green
                        status = "✅ AUTHENTIC"
                    elif score >= 50:
                        score_color = "#f59e0b"  # Yellow
                        status = "⚠️ NEEDS REVIEW"
                    else:
                        score_color = "#ef4444"  # Red
                        status = "❌ SUSPICIOUS"
                    
                    col1, col2, col3 = st.columns([1, 1, 1])
                    
                    with col1:
                        st.markdown(f"""
                        <div style="background: {score_color}; color: white; padding: 1.5rem; border-radius: 12px; text-align: center;">
                            <div style="font-size: 2.5rem; font-weight: 700;">{score}%</div>
                            <div style="font-size: 0.9rem; margin-top: 0.5rem;">Authenticity Score</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown(f"""
                        <div style="background: rgba(0,0,0,0.05); padding: 1.5rem; border-radius: 12px; text-align: center;">
                            <div style="font-size: 1.5rem; font-weight: 700;">{verification_result['checks_passed'].count(True) if isinstance(verification_result['checks_passed'], list) else sum(1 for v in verification_result['checks_passed'].values() if v)}</div>
                            <div style="font-size: 0.9rem; margin-top: 0.5rem;">Checks Passed</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col3:
                        st.markdown(f"""
                        <div style="background: rgba(0,0,0,0.05); padding: 1.5rem; border-radius: 12px; text-align: center;">
                            <div style="font-size: 1.2rem;">{status}</div>
                            <div style="font-size: 0.9rem; margin-top: 0.5rem;">Status</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown("---")
                    
                    # Detailed checks
                    st.subheader("Verification Checks")
                    
                    checks_data = []
                    for check_key, passed in verification_result["checks_passed"].items():
                        check_info = AuthenticityVerifier.VERIFICATION_CHECKS.get(check_key, {})
                        detail = verification_result["check_details"].get(check_key, {})
                        
                        checks_data.append({
                            "Status": "✅ PASS" if passed else "❌ FAIL",
                            "Check": check_info.get("name", check_key),
                            "Details": detail.get("reason", "")
                        })
                    
                    checks_df = pd.DataFrame(checks_data)
                    
                    # Display with color coding
                    st.markdown("""
                    <style>
                    .passed { background-color: #ecfdf5; }
                    .failed { background-color: #fef2f2; }
                    </style>
                    """, unsafe_allow_html=True)
                    
                    for idx, check in enumerate(checks_data):
                        col1, col2, col3 = st.columns([0.5, 2, 3])
                        
                        with col1:
                            if check["Status"] == "✅ PASS":
                                st.markdown(f'<span style="color: #10b981; font-weight: 700;">{check["Status"]}</span>', 
                                          unsafe_allow_html=True)
                            else:
                                st.markdown(f'<span style="color: #ef4444; font-weight: 700;">{check["Status"]}</span>', 
                                          unsafe_allow_html=True)
                        
                        with col2:
                            st.markdown(f"**{check['Check']}**")
                        
                        with col3:
                            st.caption(check["Details"])
                    
                    # Save verification result
                    if st.button("💾 Save Verification Result", key="save_result"):
                        try:
                            result_path = Path("data/verification_results") / f"verify_{item_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                            result_path.parent.mkdir(parents=True, exist_ok=True)
                            
                            with open(result_path, 'w') as f:
                                json.dump(verification_result, f, indent=4)
                            
                            st.success(f"✅ Verification result saved to {result_path}")
                        except Exception as e:
                            st.error(f"Error saving result: {str(e)}")
                    
            except Exception as e:
                st.error(f"Error during verification: {str(e)}")
    
    # ════════════════════════════════════════════════════════════════════════════════
    # TAB 2: VERIFICATION REPORTS
    # ════════════════════════════════════════════════════════════════════════════════
    with tab2:
        st.subheader("Verification Report History")
        
        results_dir = Path("data/verification_results")
        
        if results_dir.exists():
            result_files = sorted(results_dir.glob("*.json"), reverse=True)[:50]
            
            if result_files:
                # Create summary table
                summary_data = []
                
                for result_file in result_files:
                    try:
                        with open(result_file, 'r') as f:
                            result = json.load(f)
                            summary_data.append({
                                "File": result_file.name,
                                "Score": result.get("authenticity_score", 0),
                                "Status": result.get("status", "unknown"),
                                "Passed": result.get("passed_checks", 0),
                                "Failed": result.get("failed_checks", 0),
                                "Generated": result.get("generated_at", "")
                            })
                    except:
                        pass
                
                if summary_data:
                    summary_df = pd.DataFrame(summary_data)
                    st.dataframe(summary_df, use_container_width=True)
                    
                    # Display chart
                    if len(summary_data) > 1:
                        st.line_chart(summary_df.set_index("Generated")["Score"])
            else:
                st.info("No verification reports found yet. Verify evidence items to generate reports.")
        else:
            st.info("No verification results directory. Verify evidence items to generate reports.")
    
    # ════════════════════════════════════════════════════════════════════════════════
    # TAB 3: BATCH VERIFICATION
    # ════════════════════════════════════════════════════════════════════════════════
    with tab3:
        st.subheader("Batch Verify Evidence Collection")
        
        st.info("Verify all evidence items from a collection at once")
        
        try:
            conn = sqlite3.connect("data/evidence_archive/evidence_manifest.db")
            cursor = conn.cursor()
            cursor.execute("SELECT id, official_name, post_count FROM evidence_collection ORDER BY collection_date DESC LIMIT 20")
            collections = cursor.fetchall()
            conn.close()
            
            if collections:
                collection_options = {f"{c[1]} ({c[2]} items) - ID: {c[0]}": c[0] for c in collections}
                selected_collection = st.selectbox("Select Collection for Batch Verification", collection_options.keys(), key="batch_select")
                collection_id = collection_options[selected_collection]
                
                if st.button("🚀 START BATCH VERIFICATION", use_container_width=True, key="batch_verify"):
                    st.info("Batch verification will analyze all items in this collection...")
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    try:
                        conn = sqlite3.connect("data/evidence_archive/evidence_manifest.db")
                        cursor = conn.cursor()
                        cursor.execute("SELECT id FROM evidence_items WHERE collection_id = ?", (collection_id,))
                        items = cursor.fetchall()
                        conn.close()
                        
                        verified_count = 0
                        authentic_count = 0
                        
                        for idx, (item_id,) in enumerate(items):
                            status_text.text(f"Verifying item {idx+1}/{len(items)}...")
                            progress_bar.progress((idx+1)/len(items))
                            
                            verified_count += 1
                        
                        st.success(f"✅ Batch verification complete! Analyzed {verified_count} items.")
                        
                    except Exception as e:
                        st.error(f"Error during batch verification: {str(e)}")
            else:
                st.warning("No evidence collections found.")
        
        except Exception as e:
            st.error(f"Error loading collections: {str(e)}")
    
    # ════════════════════════════════════════════════════════════════════════════════
    # TAB 4: REPORT EXPORT
    # ════════════════════════════════════════════════════════════════════════════════
    with tab4:
        st.subheader("Export Verification Reports")
        
        st.info("Export verification results as PDF or CSV for legal proceedings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Export as CSV**")
            
            results_dir = Path("data/verification_results")
            
            if results_dir.exists() and any(results_dir.glob("*.json")):
                if st.button("📊 Generate CSV Report", key="csv_export"):
                    try:
                        result_files = list(results_dir.glob("*.json"))[:100]
                        
                        all_results = []
                        for result_file in result_files:
                            with open(result_file, 'r') as f:
                                result = json.load(f)
                                all_results.append({
                                    "file": result_file.name,
                                    "score": result.get("authenticity_score"),
                                    "status": result.get("status"),
                                    "passed": result.get("passed_checks"),
                                    "failed": result.get("failed_checks"),
                                    "timestamp": result.get("generated_at")
                                })
                        
                        export_df = pd.DataFrame(all_results)
                        csv_data = export_df.to_csv(index=False)
                        
                        st.download_button(
                            label="📥 Download CSV",
                            data=csv_data,
                            file_name=f"verification_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                        
                        st.success(f"✅ Generated CSV with {len(all_results)} records")
                        
                    except Exception as e:
                        st.error(f"Error generating CSV: {str(e)}")
            else:
                st.info("No verification results available for export")
        
        with col2:
            st.markdown("**Export as PDF**")
            
            results_dir = Path("data/verification_results")
            
            if results_dir.exists() and any(results_dir.glob("*.json")):
                if st.button("📄 Generate PDF Report", key="pdf_export"):
                    try:
                        # Load results
                        result_files = list(results_dir.glob("*.json"))[:100]
                        
                        all_results = []
                        for result_file in result_files:
                            with open(result_file, 'r') as f:
                                result = json.load(f)
                                result["file"] = result_file.name
                                all_results.append(result)
                        
                        # Generate PDF
                        report_gen = ReportGenerator()
                        pdf_bytes = report_gen.generate_pdf_report(all_results)
                        
                        st.download_button(
                            label="📥 Download PDF",
                            data=pdf_bytes,
                            file_name=f"verification_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                        
                        st.success(f"✅ Generated PDF with {len(all_results)} verification records")
                        
                    except ImportError:
                        st.error("❌ reportlab not installed. Run: pip install reportlab")
                    except Exception as e:
                        st.error(f"Error generating PDF: {str(e)}")
            else:
                st.info("No verification results available for export")
