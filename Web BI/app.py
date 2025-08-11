#!/usr/bin/env python3
"""
Yardi PowerBI Web Dashboard
Main Streamlit Application

Interactive web-based dashboard for commercial real estate analytics
Built on DuckDB for high-performance OLAP queries
"""

import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, date, timedelta
import os
from pathlib import Path
import yaml
import time
from functools import lru_cache

# Page configuration with improved settings
st.set_page_config(
    page_title="Yardi PowerBI Dashboard",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/your-username/yardi-powerbi',
        'Report a bug': "https://github.com/your-username/yardi-powerbi/issues",
        'About': "# Yardi PowerBI Dashboard\n\nInteractive commercial real estate analytics platform."
    }
)

# Enhanced CSS for better styling and responsiveness
st.markdown("""
<style>
    /* Main container improvements */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 1400px;
    }
    
    /* Enhanced metrics styling */
    .stMetric > label {
        font-size: 14px !important;
        font-weight: 600 !important;
        color: #262730 !important;
        margin-bottom: 0.5rem !important;
    }
    .stMetric > div {
        font-size: 24px !important;
        font-weight: 700 !important;
        color: #1f77b4 !important;
    }
    .stMetric > div[data-testid="metric-container"] {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
    }
    
    /* Enhanced header styling */
    .dashboard-header {
        background: linear-gradient(135deg, #1f77b4 0%, #17a2b8 50%, #20c997 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .dashboard-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
    }
    .dashboard-header h2 {
        margin: 0.5rem 0;
        font-size: 1.5rem;
        font-weight: 500;
        opacity: 0.9;
    }
    .dashboard-header p {
        margin: 0;
        opacity: 0.8;
        font-size: 0.9rem;
    }
    
    /* Enhanced sidebar styling */
    .sidebar-content {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border: 1px solid #e9ecef;
    }
    .sidebar-content h3 {
        color: #1f77b4;
        font-size: 1.1rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #e9ecef;
        padding-bottom: 0.5rem;
    }
    
    /* Enhanced chart containers */
    .chart-container {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border: 1px solid #e9ecef;
        margin-bottom: 1rem;
    }
    
    /* Loading spinner improvements */
    .stSpinner > div {
        border-color: #1f77b4 !important;
    }
    
    /* Data table improvements */
    .dataframe {
        font-size: 0.9rem !important;
    }
    .dataframe th {
        background-color: #f8f9fa !important;
        font-weight: 600 !important;
    }
    
    /* Responsive improvements */
    @media (max-width: 768px) {
        .dashboard-header h1 {
            font-size: 2rem;
        }
        .dashboard-header h2 {
            font-size: 1.2rem;
        }
        .stMetric > div {
            font-size: 20px !important;
        }
    }
    
    /* Custom success/error message styling */
    .success-message {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        border: 1px solid #c3e6cb;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        color: #155724;
    }
    .error-message {
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
        border: 1px solid #f5c6cb;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        color: #721c24;
    }
    .warning-message {
        background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
        border: 1px solid #ffeaa7;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        color: #856404;
    }
</style>
""", unsafe_allow_html=True)

class YardiDashboard:
    def __init__(self):
        self.conn = None
        self.db_path = Path(__file__).parent / "database" / "yardi.duckdb"
        self.initialize_connection()
        
    def initialize_connection(self):
        """Initialize database connection with enhanced error handling"""
        try:
            if not self.db_path.exists():
                st.error(f"🚨 Database Not Found at: {self.db_path}")
                st.info("""
                To fix this:
                1. Navigate to the database directory: `cd database`
                2. Run the initialization script: `python init_db.py`
                3. Ensure CSV files are available in the Data/Yardi_Tables directory
                """)
                st.stop()
                
            self.conn = duckdb.connect(str(self.db_path), read_only=True)
            # Test connection with timeout
            self.conn.execute("SELECT 1").fetchone()
            
            # Show success message
            st.success("✅ Database connection established successfully!")
            
        except Exception as e:
            st.error(f"🚨 Database Connection Failed: {str(e)}")
            st.info("""
            Possible solutions:
            • Check if the database file exists and is accessible
            • Ensure you have read permissions for the database file
            • Try restarting the application
            """)
            st.stop()
    
    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def get_data(_self, query: str) -> pd.DataFrame:
        """Execute query and return DataFrame with enhanced error handling and caching"""
        try:
            start_time = time.time()
            df = _self.conn.execute(query).df()
            execution_time = time.time() - start_time
            
            # Log slow queries
            if execution_time > 2.0:
                st.warning(f"⚠️ Slow query detected ({execution_time:.2f}s). Consider optimizing.")
            
            return df
            
        except Exception as e:
            st.error(f"🚨 Query Execution Failed: {str(e)}")
            if len(query) > 200:
                st.code(f"Query: {query[:200]}...", language="sql")
            else:
                st.code(f"Query: {query}", language="sql")
            return pd.DataFrame()
    
    @st.cache_data(ttl=600)  # Cache for 10 minutes
    def get_property_list(_self) -> list:
        """Get list of properties for filtering with caching"""
        try:
            query = """
            SELECT DISTINCT 
                "property code", 
                "property name",
                "postal city",
                "postal state"
            FROM dim_property 
            WHERE "property code" IS NOT NULL 
            AND "property name" IS NOT NULL
            ORDER BY "property code"
            """
            df = _self.get_data(query)
            return [f"{row['property code']} - {row['property name']} ({row['postal city']}, {row['postal state']})" 
                   for _, row in df.iterrows()]
        except Exception as e:
            st.error(f"Failed to load property list: {str(e)}")
            return []
    
    @st.cache_data(ttl=600)  # Cache for 10 minutes
    def get_date_range(_self) -> tuple:
        """Get available date range from data with enhanced error handling"""
        try:
            query = "SELECT MIN(month) as min_date, MAX(month) as max_date FROM fact_total WHERE month IS NOT NULL"
            df = _self.get_data(query)
            
            if not df.empty and df.iloc[0]['min_date'] and df.iloc[0]['max_date']:
                # Convert Excel serial dates to date objects
                min_serial = df.iloc[0]['min_date']
                max_serial = df.iloc[0]['max_date']
                
                # Convert Excel serial date to Python date
                min_date = date(1900, 1, 1) + timedelta(days=int(min_serial) - 2)
                max_date = date(1900, 1, 1) + timedelta(days=int(max_serial) - 2)
                return min_date, max_date
            
        except Exception as e:
            st.warning(f"Could not determine date range from data: {str(e)}")
        
        # Fallback to current date range
        return date.today() - timedelta(days=365), date.today()
    
    def render_sidebar(self):
        """Render enhanced sidebar with filters and navigation"""
        st.sidebar.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
        
        # Dashboard navigation with icons
        st.sidebar.header("📊 Dashboard Navigation")
        dashboard_choice = st.sidebar.selectbox(
            "Select Dashboard",
            ["Executive Summary", "Rent Roll Analysis", "Leasing Activity", "Financial Performance", "Credit Risk Analysis"],
            help="Choose the dashboard view you want to explore"
        )
        
        # Date range filter with validation
        st.sidebar.header("📅 Date Filters")
        min_date, max_date = self.get_date_range()
        
        # Validate date range
        if min_date >= max_date:
            st.sidebar.error("⚠️ Invalid date range in database")
            date_range = (max_date - timedelta(days=365), max_date)
        else:
            date_range = st.sidebar.date_input(
                "Select Date Range",
                value=(max_date - timedelta(days=365), max_date),
                min_value=min_date,
                max_value=max_date,
                help="Select the date range for your analysis"
            )
        
        # Property filter with search
        st.sidebar.header("🏢 Property Filters")
        properties = self.get_property_list()
        
        if properties:
            # Add search functionality
            search_term = st.sidebar.text_input(
                "🔍 Search Properties",
                placeholder="Type to filter properties...",
                help="Type property name or code to filter the list"
            )
            
            # Filter properties based on search
            if search_term:
                filtered_properties = [p for p in properties if search_term.lower() in p.lower()]
            else:
                filtered_properties = properties
            
            selected_properties = st.sidebar.multiselect(
                "Select Properties",
                filtered_properties,
                default=filtered_properties[:5] if len(filtered_properties) > 5 else filtered_properties,
                help="Select one or more properties to analyze"
            )
        else:
            selected_properties = []
            st.sidebar.warning("⚠️ No properties available")
        
        # Fund filter
        st.sidebar.header("💼 Fund Filters")
        fund_filter = st.sidebar.selectbox(
            "Select Fund",
            ["All Funds", "Fund 1", "Fund 2", "Fund 3"],
            help="Filter data by specific fund"
        )
        
        # Book filter for financial data
        st.sidebar.header("📚 Book Filters")
        book_filter = st.sidebar.selectbox(
            "Select Book",
            ["All Books", "Book 46 (FPR)", "Book 1 (Standard)"],
            help="Filter financial data by accounting book"
        )
        
        # Quick actions
        st.sidebar.header("⚡ Quick Actions")
        if st.sidebar.button("🔄 Refresh Data", help="Refresh cached data"):
            st.cache_data.clear()
            st.rerun()
        
        if st.sidebar.button("📊 Export Current View", help="Export current dashboard data"):
            st.info("📊 Export functionality coming soon!")
        
        st.sidebar.markdown('</div>', unsafe_allow_html=True)
        
        return dashboard_choice, date_range, selected_properties, fund_filter, book_filter
    
    def render_header(self, dashboard_name: str):
        """Render enhanced dashboard header"""
        st.markdown(f"""
        <div class="dashboard-header">
            <h1>🏢 Yardi PowerBI Dashboard</h1>
            <h2>{dashboard_name}</h2>
            <p>📊 Real-time commercial real estate analytics • 🕒 Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        """, unsafe_allow_html=True)
    
    def format_currency(self, value):
        """Format currency values with enhanced handling"""
        if pd.isna(value) or value == 0:
            return "$0"
        elif abs(value) >= 1e9:
            return f"${value/1e9:.2f}B"
        elif abs(value) >= 1e6:
            return f"${value/1e6:.1f}M"
        elif abs(value) >= 1e3:
            return f"${value/1e3:.0f}K"
        else:
            return f"${value:,.0f}"
    
    def format_percentage(self, value):
        """Format percentage values with enhanced handling"""
        if pd.isna(value):
            return "0.0%"
        return f"{value:.1f}%"
    
    def format_area(self, value):
        """Format square footage values with enhanced handling"""
        if pd.isna(value) or value == 0:
            return "0 SF"
        elif abs(value) >= 1e6:
            return f"{value/1e6:.1f}M SF"
        elif abs(value) >= 1e3:
            return f"{value/1e3:.0f}K SF"
        else:
            return f"{value:,.0f} SF"

# Initialize dashboard with session state
if 'dashboard' not in st.session_state:
    st.session_state.dashboard = YardiDashboard()

dashboard = st.session_state.dashboard

# Render sidebar and get filters
dashboard_choice, date_range, selected_properties, fund_filter, book_filter = dashboard.render_sidebar()

# Render header
dashboard.render_header(dashboard_choice)

# Load dashboard components based on selection with error handling
try:
    if dashboard_choice == "Executive Summary":
        # Use enhanced executive summary with strategic KPIs
        from components.executive_summary_enhanced import render_executive_dashboard
        
        # Extract property codes from the selected properties
        property_codes = []
        if selected_properties:
            for prop in selected_properties:
                # Extract the property code (part before the dash)
                if ' - ' in prop:
                    property_codes.append(prop.split(' - ')[0])
                else:
                    property_codes.append(prop)
        
        # Parse fund filter to extract actual fund identifier
        fund_value = None
        if fund_filter == "Fund 1":
            fund_value = "1"
        elif fund_filter == "Fund 2":
            fund_value = "2"
        elif fund_filter == "Fund 3":
            fund_value = "3"
        # "All Funds" means no filter
        
        # Parse book filter to extract actual book ID
        book_value = None
        if book_filter == "Book 46 (FPR)":
            book_value = "46"
        elif book_filter == "Book 1 (Standard)":
            book_value = "1"
        # "All Books" means no filter
        
        filters = {
            'property_ids': property_codes,
            'date_range': date_range,
            'fund_filter': fund_value,
            'book_filter': book_value
        }
        render_executive_dashboard(dashboard.conn, filters)

    elif dashboard_choice == "Rent Roll Analysis":
        # Use true rent roll with amendment-based logic
        from components.rent_roll_true import render_rent_roll_dashboard
        
        # Extract property codes (reuse logic from above)
        property_codes = []
        if selected_properties:
            for prop in selected_properties:
                if ' - ' in prop:
                    property_codes.append(prop.split(' - ')[0])
                else:
                    property_codes.append(prop)
        
        # Parse fund filter (reuse logic from above)
        fund_value = None
        if fund_filter == "Fund 1":
            fund_value = "1"
        elif fund_filter == "Fund 2":
            fund_value = "2"
        elif fund_filter == "Fund 3":
            fund_value = "3"
        
        filters = {
            'property_ids': property_codes,
            'date_range': date_range,
            'fund_filter': fund_value
        }
        render_rent_roll_dashboard(dashboard.conn, filters)

    elif dashboard_choice == "Leasing Activity":
        from components.leasing_activity import render_leasing_activity
        
        # Extract property codes for consistency
        property_codes = []
        if selected_properties:
            for prop in selected_properties:
                if ' - ' in prop:
                    property_codes.append(prop.split(' - ')[0])
                else:
                    property_codes.append(prop)
        
        # Parse fund filter
        fund_value = None
        if fund_filter == "Fund 1":
            fund_value = "1"
        elif fund_filter == "Fund 2":
            fund_value = "2"
        elif fund_filter == "Fund 3":
            fund_value = "3"
        
        render_leasing_activity(dashboard, date_range, property_codes, fund_value)

    elif dashboard_choice == "Financial Performance":
        from components.financial_metrics import render_financial_performance
        
        # Extract property codes
        property_codes = []
        if selected_properties:
            for prop in selected_properties:
                if ' - ' in prop:
                    property_codes.append(prop.split(' - ')[0])
                else:
                    property_codes.append(prop)
        
        # Parse fund filter
        fund_value = None
        if fund_filter == "Fund 1":
            fund_value = "1"
        elif fund_filter == "Fund 2":
            fund_value = "2"
        elif fund_filter == "Fund 3":
            fund_value = "3"
        
        # Parse book filter
        book_value = None
        if book_filter == "Book 46 (FPR)":
            book_value = "46"
        elif book_filter == "Book 1 (Standard)":
            book_value = "1"
        
        render_financial_performance(dashboard, date_range, property_codes, fund_value, book_value)

    elif dashboard_choice == "Credit Risk Analysis":
        from components.credit_risk import render_credit_risk_analysis
        
        # Extract property codes
        property_codes = []
        if selected_properties:
            for prop in selected_properties:
                if ' - ' in prop:
                    property_codes.append(prop.split(' - ')[0])
                else:
                    property_codes.append(prop)
        
        # Parse fund filter
        fund_value = None
        if fund_filter == "Fund 1":
            fund_value = "1"
        elif fund_filter == "Fund 2":
            fund_value = "2"
        elif fund_filter == "Fund 3":
            fund_value = "3"
        
        render_credit_risk_analysis(dashboard, date_range, property_codes, fund_value)

except ImportError as e:
    st.error(f"🚨 Component Import Error: Failed to load dashboard component: {str(e)}. Please ensure all component files are present in the components directory.")
except Exception as e:
    st.error(f"🚨 Dashboard Error: An error occurred while rendering the dashboard: {str(e)}. Please try refreshing the page or contact support if the issue persists.")

# Enhanced footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem; background: #f8f9fa; border-radius: 8px; margin-top: 2rem;">
    <p>🏢 <strong>Yardi PowerBI Dashboard</strong> • Built with Streamlit & DuckDB • 
    <a href="https://github.com/your-username/yardi-powerbi" target="_blank">View Source Code</a> • 
    <a href="mailto:support@example.com">Contact Support</a></p>
    <p style="font-size: 0.8rem; margin-top: 0.5rem;">© 2024 Commercial Real Estate Analytics Platform</p>
</div>
""", unsafe_allow_html=True)