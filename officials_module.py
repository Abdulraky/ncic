"""
Streamlit interface for Public Officials Database
"""

import streamlit as st
import pandas as pd
import io
from officials_db import OfficialsDatabase

def render_officials_module():
    """Render the Public Officials Database module"""
    
    st.markdown("""
    <div style="background: linear-gradient(90deg, #1d4ed8 0%, #1e40af 100%); padding: 2rem; border-radius: 12px; margin-bottom: 2rem;">
        <h1 style="color: white; margin: 0;">🏛️ PUBLIC OFFICIALS DATABASE</h1>
        <p style="color: #e0e7ff; margin: 0.5rem 0 0 0;">Module 1 • Digital Forensic Collector</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize database
    db = OfficialsDatabase("data/officials.db")
    
    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "⬆️ Import Data", "🔍 Search & Filter", "📋 Records"])
    
    # ════════════════════════════════════════════════════════════════════════════════
    # TAB 1: DASHBOARD
    # ════════════════════════════════════════════════════════════════════════════════
    with tab1:
        st.subheader("Database Statistics")
        
        stats = db.get_statistics()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Officials", stats.get('total_active', 0), "active records")
        
        with col2:
            st.metric("Verified on X", stats.get('verified_x', 0), "verified accounts")
        
        with col3:
            st.metric("With Social Media", stats.get('with_socials', 0), "linked accounts")
        
        with col4:
            officials = db.get_all_officials()
            unique_counties = len(db.get_counties())
            st.metric("Counties Covered", unique_counties, f"{len(officials)} officials")
        
        st.divider()
        
        # Distribution by office
        st.subheader("Distribution by Office")
        by_office = stats.get('by_office', {})
        if by_office:
            df_office = pd.DataFrame([
                {'Office': office, 'Count': count} 
                for office, count in by_office.items()
            ])
            st.bar_chart(df_office.set_index('Office'))
        else:
            st.info("No data yet. Import officials to see distribution.")
        
        # Distribution by county
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Top Counties")
            by_county = stats.get('by_county', {})
            if by_county:
                top_counties = sorted(by_county.items(), key=lambda x: x[1], reverse=True)[:10]
                df_county = pd.DataFrame([
                    {'County': county, 'Count': count} 
                    for county, count in top_counties
                ])
                st.bar_chart(df_county.set_index('County'))
            else:
                st.info("No county data available.")
        
        with col2:
            st.subheader("Quick Stats")
            st.write(f"**Active Officials**: {stats.get('total_active', 0)}")
            st.write(f"**Unique Offices**: {len(by_office)}")
            st.write(f"**Unique Counties**: {len(by_county)}")
            st.write(f"**Verification Rate**: {(stats.get('verified_x', 0) / max(1, stats.get('total_active', 1)) * 100):.1f}%")
            st.write(f"**Social Media Coverage**: {(stats.get('with_socials', 0) / max(1, stats.get('total_active', 1)) * 100):.1f}%")
    
    # ════════════════════════════════════════════════════════════════════════════════
    # TAB 2: IMPORT DATA
    # ════════════════════════════════════════════════════════════════════════════════
    with tab2:
        st.subheader("Import Officials Data")
        
        import_type = st.radio("Select import format", ["CSV", "JSON", "Manual Entry"])
        
        if import_type == "CSV":
            st.markdown("""
            **CSV Format Requirements:**
            - Headers: `official_id, name, office, county, constituency, party, verified_x, facebook, youtube, tiktok, instagram, website, active`
            - `official_id`: Unique identifier (required)
            - `name`: Full name (required)
            - `office`: Position/office type (required)
            - Other fields are optional
            """)
            
            uploaded_file = st.file_uploader("Upload CSV file", type="csv")
            
            if uploaded_file is not None:
                if st.button("Import from CSV", key="csv_import"):
                    with st.spinner("Importing..."):
                        count, message = db.import_from_csv(uploaded_file)
                        if count > 0:
                            st.success(f"✓ {message}")
                        else:
                            st.error(message)
        
        elif import_type == "JSON":
            st.markdown("""
            **JSON Format Requirements:**
            - Either a list of objects or an object with `officials` key
            - Each object should have fields: `official_id, name, office, county, constituency, party, verified_x, facebook, youtube, tiktok, instagram, website, active`
            """)
            
            uploaded_file = st.file_uploader("Upload JSON file", type="json")
            
            if uploaded_file is not None:
                if st.button("Import from JSON", key="json_import"):
                    with st.spinner("Importing..."):
                        count, message = db.import_from_json(uploaded_file)
                        if count > 0:
                            st.success(f"✓ {message}")
                        else:
                            st.error(message)
        
        else:  # Manual Entry
            st.subheader("Add Official Manually")
            
            col1, col2 = st.columns(2)
            with col1:
                official_id = st.text_input("Official ID *", key="manual_id")
                name = st.text_input("Full Name *", key="manual_name")
                office = st.selectbox("Office Type *", ["Governor", "Senator", "Woman Representative", "MP", "Cabinet Secretary", "Principal Secretary"], key="manual_office")
                county = st.text_input("County", key="manual_county")
                party = st.text_input("Political Party", key="manual_party")
            
            with col2:
                constituency = st.text_input("Constituency", key="manual_const")
                verified_x = st.checkbox("Verified on X", key="manual_verified")
                website = st.text_input("Website", key="manual_website")
                active = st.checkbox("Active", value=True, key="manual_active")
            
            st.subheader("Social Media Handles")
            col1, col2 = st.columns(2)
            with col1:
                facebook = st.text_input("Facebook", key="manual_fb")
                youtube = st.text_input("YouTube", key="manual_yt")
            with col2:
                tiktok = st.text_input("TikTok", key="manual_tt")
                instagram = st.text_input("Instagram", key="manual_ig")
            
            if st.button("Save Official"):
                if official_id and name and office:
                    official_data = {
                        'official_id': official_id,
                        'name': name,
                        'office': office,
                        'county': county,
                        'constituency': constituency,
                        'party': party,
                        'verified_x': verified_x,
                        'facebook': facebook,
                        'youtube': youtube,
                        'tiktok': tiktok,
                        'instagram': instagram,
                        'website': website,
                        'active': active
                    }
                    success, message = db.add_official(official_data)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.error("Please fill in all required fields (marked with *)")
    
    # ════════════════════════════════════════════════════════════════════════════════
    # TAB 3: SEARCH & FILTER
    # ════════════════════════════════════════════════════════════════════════════════
    with tab3:
        st.subheader("Search & Filter Officials")
        
        search_type = st.radio("Search by", ["Keyword", "Office", "County", "Party"])
        
        if search_type == "Keyword":
            search_query = st.text_input("Enter search term (name, office, party, etc.)")
            if search_query:
                results = db.search_officials(search_query)
                if results:
                    st.success(f"Found {len(results)} official(s)")
                    df = pd.DataFrame(results)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No results found")
        
        elif search_type == "Office":
            offices = db.get_offices()
            selected_office = st.selectbox("Select office", offices)
            if selected_office:
                results = db.get_officials_by_office(selected_office)
                if results:
                    st.success(f"Found {len(results)} official(s) in {selected_office}")
                    df = pd.DataFrame(results)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info(f"No officials found for {selected_office}")
        
        elif search_type == "County":
            counties = db.get_counties()
            selected_county = st.selectbox("Select county", counties)
            if selected_county:
                results = db.get_officials_by_county(selected_county)
                if results:
                    st.success(f"Found {len(results)} official(s) in {selected_county}")
                    df = pd.DataFrame(results)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info(f"No officials found in {selected_county}")
        
        else:  # Party
            parties = db.get_parties()
            selected_party = st.selectbox("Select party", parties)
            if selected_party:
                results = db.search_officials(selected_party, ['party'])
                if results:
                    st.success(f"Found {len(results)} official(s) from {selected_party}")
                    df = pd.DataFrame(results)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info(f"No officials found from {selected_party}")
    
    # ════════════════════════════════════════════════════════════════════════════════
    # TAB 4: RECORDS MANAGEMENT
    # ════════════════════════════════════════════════════════════════════════════════
    with tab4:
        st.subheader("All Records")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            show_inactive = st.checkbox("Show inactive records", value=False)
        with col2:
            if st.button("Refresh"):
                st.rerun()
        
        officials = db.get_all_officials(active_only=not show_inactive)
        
        if officials:
            df = pd.DataFrame(officials)
            
            # Display summary
            st.info(f"Showing {len(officials)} record(s)")
            
            # Display table
            st.dataframe(df, use_container_width=True)
            
            # Export options
            st.divider()
            st.subheader("Export Options")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Export to CSV"):
                    success, message = db.export_to_csv()
                    if success:
                        st.success(message)
                        # Create download button
                        csv = df.to_csv(index=False)
                        st.download_button(
                            label="Download CSV",
                            data=csv,
                            file_name="officials_export.csv",
                            mime="text/csv"
                        )
            
            with col2:
                if st.button("Export to JSON"):
                    json_str = df.to_json(orient='records', indent=2)
                    st.download_button(
                        label="Download JSON",
                        data=json_str,
                        file_name="officials_export.json",
                        mime="application/json"
                    )
        else:
            st.info("No records found. Start by importing data.")
    
    db.close()

if __name__ == "__main__":
    render_officials_module()
