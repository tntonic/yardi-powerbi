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

# Page configuration
st.set_page_config(
    page_title="Yardi PowerBI Dashboard",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .reportview-container {
        background: #f0f2f6
    }
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .stMetric > label {
        font-size: 16px !important;
        font-weight: 600 !important;
        color: #262730 !important;
    }
    .stMetric > div {
        font-size: 28px !important;
        font-weight: 700 !important;
    }
    .dashboard-header {
        background: linear-gradient(90deg, #1f77b4 0%, #17a2b8 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .kpi-container {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    .sidebar-content {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

class YardiDashboard:
    def __init__(self):
        self.conn = None
        self.db_path = Path(__file__).parent / "database" / "yardi.duckdb"
        self.initialize_connection()
        
    def initialize_connection(self):
        """Initialize database connection with error handling"""
        try:
            if not self.db_path.exists():
                st.error(f"""
                Database not found at {self.db_path}
                
                Please run the database initialization script first:
                ```bash
                cd database
                python init_db.py
                ```
                """)
                st.stop()
                
            self.conn = duckdb.connect(str(self.db_path), read_only=True)
            # Test connection
            self.conn.execute("SELECT 1").fetchone()
            
        except Exception as e:
            st.error(f"Database connection failed: {str(e)}")
            st.stop()
    
    def get_data(self, query: str) -> pd.DataFrame:
        """Execute query and return DataFrame with error handling"""
        try:
            return self.conn.execute(query).df()
        except Exception as e:
            st.error(f"Query failed: {str(e)}")
            return pd.DataFrame()
    
    def get_property_list(self) -> list:
        """Get list of properties for filtering"""
        query = "SELECT DISTINCT \"property code\", \"property name\" FROM dim_property ORDER BY \"property code\""
        df = self.get_data(query)
        return [f"{row['property code']} - {row['property name']}" for _, row in df.iterrows()]
    
    def get_date_range(self) -> tuple:
        """Get available date range from data"""
        query = "SELECT MIN(month) as min_date, MAX(month) as max_date FROM fact_total"
        df = self.get_data(query)
        if not df.empty:
            # Convert Excel serial dates to date objects
            min_serial = df.iloc[0]['min_date']
            max_serial = df.iloc[0]['max_date']
            
            if min_serial and max_serial:
                # Convert Excel serial date to Python date
                # Excel serial date is days since January 1, 1900
                # Python date starts from January 1, 1900
                min_date = date(1900, 1, 1) + timedelta(days=int(min_serial) - 2)  # -2 for Excel's leap year bug
                max_date = date(1900, 1, 1) + timedelta(days=int(max_serial) - 2)  # -2 for Excel's leap year bug
                return min_date, max_date
        
        # Fallback to current date range
        return date.today() - timedelta(days=365), date.today()
    
    def render_sidebar(self):
        """Render sidebar with filters and navigation"""
        st.sidebar.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
        
        # Dashboard navigation
        st.sidebar.header("📊 Dashboard Navigation")
        dashboard_choice = st.sidebar.selectbox(
            "Select Dashboard",
            ["Executive Summary", "Rent Roll Analysis", "Leasing Activity", "Financial Performance", "Credit Risk Analysis"]
        )
        
        # Date range filter
        st.sidebar.header("📅 Date Filters")
        min_date, max_date = self.get_date_range()
        
        date_range = st.sidebar.date_input(
            "Select Date Range",
            value=(max_date - timedelta(days=365), max_date),
            min_value=min_date,
            max_value=max_date
        )
        
        # Property filter
        st.sidebar.header("🏢 Property Filters")
        properties = self.get_property_list()
        
        if properties:
            selected_properties = st.sidebar.multiselect(
                "Select Properties",
                properties,
                default=properties[:5] if len(properties) > 5 else properties
            )
        else:
            selected_properties = []
        
        # Fund filter
        st.sidebar.header("💼 Fund Filters")
        fund_filter = st.sidebar.selectbox(
            "Select Fund",
            ["All Funds", "Fund 1", "Fund 2", "Fund 3"]
        )
        
        # Book filter for financial data
        st.sidebar.header("📚 Book Filters")
        book_filter = st.sidebar.selectbox(
            "Select Book",
            ["All Books", "Book 46 (FPR)", "Book 1 (Standard)"]
        )
        
        st.sidebar.markdown('</div>', unsafe_allow_html=True)
        
        return dashboard_choice, date_range, selected_properties, fund_filter, book_filter
    
    def render_header(self, dashboard_name: str):
        """Render dashboard header"""
        st.markdown(f"""
        <div class="dashboard-header">
            <h1>🏢 Yardi PowerBI Dashboard</h1>
            <h2>{dashboard_name}</h2>
            <p>Real-time commercial real estate analytics • Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        """, unsafe_allow_html=True)
    
    def format_currency(self, value):
        """Format currency values"""
        if pd.isna(value) or value == 0:
            return "$0"
        elif abs(value) >= 1e6:
            return f"${value/1e6:.1f}M"
        elif abs(value) >= 1e3:
            return f"${value/1e3:.0f}K"
        else:
            return f"${value:,.0f}"
    
    def format_percentage(self, value):
        """Format percentage values"""
        if pd.isna(value):
            return "0.0%"
        return f"{value:.1f}%"
    
    def format_area(self, value):
        """Format square footage values"""
        if pd.isna(value) or value == 0:
            return "0 SF"
        elif abs(value) >= 1e6:
            return f"{value/1e6:.1f}M SF"
        elif abs(value) >= 1e3:
            return f"{value/1e3:.0f}K SF"
        else:
            return f"{value:,.0f} SF"

# Initialize dashboard
if 'dashboard' not in st.session_state:
    st.session_state.dashboard = YardiDashboard()

dashboard = st.session_state.dashboard

# Render sidebar and get filters
dashboard_choice, date_range, selected_properties, fund_filter, book_filter = dashboard.render_sidebar()

# Render header
dashboard.render_header(dashboard_choice)

# Load dashboard components based on selection
if dashboard_choice == "Executive Summary":
    from components.executive_summary import render_executive_summary
    render_executive_summary(dashboard, date_range, selected_properties, fund_filter, book_filter)

elif dashboard_choice == "Rent Roll Analysis":
    from components.rent_roll import render_rent_roll_analysis
    render_rent_roll_analysis(dashboard, date_range, selected_properties, fund_filter)

elif dashboard_choice == "Leasing Activity":
    from components.leasing_activity import render_leasing_activity
    render_leasing_activity(dashboard, date_range, selected_properties, fund_filter)

elif dashboard_choice == "Financial Performance":
    from components.financial_metrics import render_financial_performance
    render_financial_performance(dashboard, date_range, selected_properties, fund_filter, book_filter)

elif dashboard_choice == "Credit Risk Analysis":
    from components.credit_risk import render_credit_risk_analysis
    render_credit_risk_analysis(dashboard, date_range, selected_properties, fund_filter)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>🏢 Yardi PowerBI Dashboard • Built with Streamlit & DuckDB • 
    <a href="https://github.com/your-username/yardi-powerbi" target="_blank">View Source Code</a></p>
</div>
""", unsafe_allow_html=True)