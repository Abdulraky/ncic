"""
Streamlit interface for Authenticity Score Verification (Refactored with Services)
Module 3 - Uses new AnalysisService for verification workflow
"""

import streamlit as st
import pandas as pd
import json
from datetime import datetime

from database import SessionLocal
from services import EvidenceService, AnalysisService
from authenticity_verifier import AuthenticityVerifier
from report_generator import ReportGenerator

def render_authenticity_module():
    """Render the Authenticity Score Verification module"""
    
    st.markdown("""
    <div style="background: linear-gradient(90deg, #8b5cf6 0%, #6d28d9 100%); padding: 2rem; border-radius: 12px; margin-bottom: 2rem;">
        <h1 style="color: white; margin: 0;">🔍 AUTHENTICITY SCORE VERIFICATION</h1>
        <p style="color: #e9d5ff; margin: 0.5rem 0 0 0;">Module 3 • Digital Evidence Authenticity Analysis</p>
    </div>
    """, unsafe_allow_html=True)
    
    db = SessionLocal()
    
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
            # Get collections from service
            collections = EvidenceService.get_all_collections(db)
            
            if collections:
                collection_display = {f"{c.official_name} (ID: {c.id})": c for c in collections}
                selected_display = st.selectbox("Select Collection", collection_display.keys())
                selected_collection = collection_display[selected_display]
            else:
                st.warning("No evidence collections found. Collect evidence in Module 2 first.")
                selected_collection = None
        
        with col2:
            if selected_collection:
                # Get items from service
                items = EvidenceService.get_collection_items(db, selected_collection.id)
                
                if items:
                    item_display = {f"{i.item_type} - {(i.source_url or '')[:50]}...": i for i in items}
                    selected_item_display = st.selectbox("Select Evidence Item", item_display.keys())
                    selected_item = item_display[selected_item_display]
                else:
                    st.warning("No evidence items in this collection")
                    selected_item = None
            else:
                selected_item = None
        
        # Verify button
        if selected_item and st.button("🔍 VERIFY AUTHENTICITY", use_container_width=True, key="verify_button"):
            try:
                # Verify using service
                analysis_service = AnalysisService()
                verification_result = analysis_service.verify_evidence(db, selected_item.id, save_result=True)
                
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
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown(f"""
                    <div style="text-align: center; padding: 20px; background: rgba(255,255,255,0.05); border-radius: 10px;">
                        <div style="color: {score_color}; font-size: 2.5em; font-weight: bold;">{score}%</div>
                        <div style="color: #888; font-size: 0.9em; margin-top: 5px;">Authenticity Score</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    checks_passed = sum(verification_result.get("checks_passed", {}).values())
                    st.markdown(f"""
                    <div style="text-align: center; padding: 20px; background: rgba(255,255,255,0.05); border-radius: 10px;">
                        <div style="color: #fff; font-size: 2.5em; font-weight: bold;">{checks_passed}</div>
                        <div style="color: #888; font-size: 0.9em; margin-top: 5px;">Checks Passed</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    st.markdown(f"""
                    <div style="text-align: center; padding: 20px; background: rgba(255,255,255,0.05); border-radius: 10px;">
                        <div style="color: {score_color}; font-size: 2.5em; font-weight: bold;">{status}</div>
                        <div style="color: #888; font-size: 0.9em; margin-top: 5px;">Status</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("---")
                st.subheader("Verification Checks")
                
                # Display individual checks
                for check_name, details in verification_result.get("check_details", {}).items():
                    passed = details.get("passed", False)
                    message = details.get("message", "")
                    icon = "✅ PASS" if passed else "❌ FAIL"
                    
                    col1, col2, col3 = st.columns([0.5, 2, 3])
                    with col1:
                        st.write(icon)
                    with col2:
                        st.write(f"**{check_name}**")
                    with col3:
                        st.write(message)
                
                # Save result button
                if st.button("💾 Save Verification Result"):
                    st.success(f"✓ Verification result saved (ID: {verification_result.get('id', 'N/A')})")
                
            except Exception as e:
                st.error(f"Verification failed: {str(e)}")
    
    # ════════════════════════════════════════════════════════════════════════════════
    # TAB 2: VERIFICATION REPORTS
    # ════════════════════════════════════════════════════════════════════════════════
    with tab2:
        st.subheader("Verification Reports")
        
        analysis_service = AnalysisService()
        results = analysis_service.get_all_results(db)
        summary = analysis_service.get_results_summary(db)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Results", summary["total"])
        with col2:
            st.metric("Authentic", summary["authentic"])
        with col3:
            st.metric("Needs Review", summary["needs_review"])
        with col4:
            st.metric("Suspicious", summary["suspicious"])
        
        if results:
            df_results = pd.DataFrame([{
                "ID": r.id,
                "Evidence ID": r.evidence_item_id,
                "Score": r.authenticity_score,
                "Status": r.status,
                "Checks": sum([
                    r.verified_account, r.url_valid, r.metadata_intact, r.timestamp_verified,
                    r.no_editing, r.sha256_verified, r.screenshot_captured, r.json_preserved
                ]),
                "Date": r.created_at.strftime("%Y-%m-%d") if r.created_at else "-"
            } for r in results])
            
            st.dataframe(df_results, use_container_width=True)
        else:
            st.info("No verification results yet. Verify evidence in the tab above.")
    
    # ════════════════════════════════════════════════════════════════════════════════
    # TAB 3: BATCH VERIFICATION
    # ════════════════════════════════════════════════════════════════════════════════
    with tab3:
        st.subheader("Batch Verification")
        
        collections = EvidenceService.get_all_collections(db)
        
        if collections:
            selected_collection = st.selectbox(
                "Select Collection for Batch Verification",
                collections,
                format_func=lambda c: f"{c.official_name} (ID: {c.id})"
            )
            
            if st.button("🚀 Start Batch Verification"):
                items = EvidenceService.get_collection_items(db, selected_collection.id)
                
                if items:
                    progress_bar = st.progress(0)
                    verified_count = 0
                    
                    analysis_service = AnalysisService()
                    
                    for idx, item in enumerate(items):
                        try:
                            analysis_service.verify_evidence(db, item.id, save_result=True)
                            verified_count += 1
                        except Exception as e:
                            st.warning(f"Error verifying item {item.id}: {str(e)}")
                        
                        progress_bar.progress((idx + 1) / len(items))
                    
                    st.success(f"✅ Batch verification complete: {verified_count}/{len(items)} items verified")
                else:
                    st.warning("No items to verify in this collection")
        else:
            st.info("No collections available for batch verification")
    
    # ════════════════════════════════════════════════════════════════════════════════
    # TAB 4: REPORT EXPORT
    # ════════════════════════════════════════════════════════════════════════════════
    with tab4:
        st.subheader("Export Verification Reports")
        st.write("Export verification results as PDF or CSV for legal proceedings")
        
        analysis_service = AnalysisService()
        results = analysis_service.get_all_results(db)
        
        if results:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Export as CSV")
                
                if st.button("📥 Download CSV Report"):
                    try:
                        generator = ReportGenerator()
                        csv_data = generator.generate_csv_report(results)
                        st.download_button(
                            label="CSV Report",
                            data=csv_data,
                            file_name=f"verification_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                    except Exception as e:
                        st.error(f"Error generating CSV: {str(e)}")
            
            with col2:
                st.subheader("Export as PDF")
                
                if st.button("📥 Download PDF Report"):
                    try:
                        generator = ReportGenerator()
                        pdf_data = generator.generate_pdf_report(results)
                        st.download_button(
                            label="PDF Report",
                            data=pdf_data,
                            file_name=f"verification_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                            mime="application/pdf"
                        )
                    except Exception as e:
                        st.error(f"Error generating PDF: {str(e)}")
        else:
            st.info("No verification results available for export")
    
    db.close()
