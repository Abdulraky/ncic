"""
Streamlit interface for Public Officials Database (Refactored with Services)
Uses new PoliticianService layer while maintaining UI compatibility
"""

import streamlit as st
import pandas as pd
import io
from database import SessionLocal
from services import PoliticianService

def render_officials_module():
    """Render the Public Officials Database module"""
    
    st.markdown("""
    <div style="background: linear-gradient(90deg, #1d4ed8 0%, #1e40af 100%); padding: 2rem; border-radius: 12px; margin-bottom: 2rem;">
        <h1 style="color: white; margin: 0;">🏛️ PUBLIC OFFICIALS DATABASE</h1>
        <p style="color: #e0e7ff; margin: 0.5rem 0 0 0;">Module 1 • Digital Forensic Collector</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize database session
    db = SessionLocal()
    
    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "⬆️ Import Data", "🔍 Search & Filter", "📋 Records"])
    
    # ════════════════════════════════════════════════════════════════════════════════
    # TAB 1: DASHBOARD
    # ════════════════════════════════════════════════════════════════════════════════
    with tab1:
        st.subheader("Database Statistics")
        
        # Get statistics from service
        total_officials = db.query(__import__('models.politician', fromlist=['Official']).Official).count()
        verified_count = PoliticianService.get_verified_count(db)
        social_count = PoliticianService.get_with_social_media_count(db)
        counties = PoliticianService.get_unique_counties(db)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Officials", total_officials, "active records")
        
        with col2:
            st.metric("Verified on X", verified_count, "verified accounts")
        
        with col3:
            st.metric("With Social Media", social_count, "linked accounts")
        
        with col4:
            st.metric("Counties Covered", len(counties), f"{total_officials} officials")
        
        st.divider()
        
        # County distribution
        st.subheader("Geographic Distribution")
        officials_list = PoliticianService.get_all_officials(db)
        if officials_list:
            county_counts = {}
            for official in officials_list:
                if official.county:
                    county_counts[official.county] = county_counts.get(official.county, 0) + 1
            
            df_counties = pd.DataFrame(list(county_counts.items()), columns=["County", "Count"])
            col1, col2 = st.columns([2, 1])
            with col1:
                st.bar_chart(df_counties.set_index("County"))
            with col2:
                st.dataframe(df_counties, use_container_width=True)
    
    # ════════════════════════════════════════════════════════════════════════════════
    # TAB 2: IMPORT DATA
    # ════════════════════════════════════════════════════════════════════════════════
    with tab2:
        st.subheader("Import Officials from CSV")
        
        uploaded_file = st.file_uploader("Choose CSV file", type="csv")
        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            st.write("Preview:")
            st.dataframe(df.head())
            
            if st.button("Import Officials"):
                try:
                    # Convert dataframe to list of dicts for bulk import
                    records = df.to_dict('records')
                    imported = PoliticianService.import_from_csv(db, records)
                    st.success(f"✓ Imported {imported} new officials")
                except Exception as e:
                    st.error(f"Error importing: {e}")
    
    # ════════════════════════════════════════════════════════════════════════════════
    # TAB 3: SEARCH & FILTER
    # ════════════════════════════════════════════════════════════════════════════════
    with tab3:
        st.subheader("Search & Filter Officials")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            search_name = st.text_input("Search by name")
        
        with col2:
            county_filter = st.selectbox(
                "Filter by county",
                ["All"] + PoliticianService.get_unique_counties(db)
            )
        
        with col3:
            party_filter = st.text_input("Filter by party")
        
        # Apply filters
        officials = PoliticianService.get_all_officials(db)
        
        if search_name:
            officials = [o for o in officials if search_name.lower() in o.name.lower()]
        
        if county_filter != "All":
            officials = [o for o in officials if o.county == county_filter]
        
        if party_filter:
            officials = [o for o in officials if party_filter.lower() in (o.party or "").lower()]
        
        # Display results
        if officials:
            df_results = pd.DataFrame([{
                "ID": o.official_id,
                "Name": o.name,
                "Office": o.office,
                "County": o.county,
                "Party": o.party,
                "Verified X": "✓" if o.verified_x else "",
                "Twitter": o.twitter or "-",
                "Instagram": o.instagram or "-"
            } for o in officials])
            
            st.dataframe(df_results, use_container_width=True)
            st.write(f"**Found: {len(officials)} officials**")
        else:
            st.info("No officials match the search criteria")
    
    # ════════════════════════════════════════════════════════════════════════════════
    # TAB 4: ALL RECORDS
    # ════════════════════════════════════════════════════════════════════════════════
    with tab4:
        st.subheader("All Officials")
        
        officials = PoliticianService.get_all_officials(db)
        
        if officials:
            df_all = pd.DataFrame([{
                "ID": o.official_id,
                "Name": o.name,
                "Office": o.office,
                "County": o.county,
                "Constituency": o.constituency,
                "Party": o.party,
                "Verified": "✓" if o.verified_x else "",
                "Twitter": o.twitter or "-",
                "Facebook": o.facebook or "-",
                "Instagram": o.instagram or "-",
                "TikTok": o.tiktok or "-"
            } for o in officials])
            
            st.dataframe(df_all, use_container_width=True)
            
            # Export option
            csv = df_all.to_csv(index=False)
            st.download_button(
                label="Download as CSV",
                data=csv,
                file_name="officials.csv",
                mime="text/csv"
            )
        else:
            st.info("No officials in database")
    
    db.close()
