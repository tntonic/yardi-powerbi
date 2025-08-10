#!/usr/bin/env python3
"""
Executive Summary Dashboard Component
High-level portfolio KPIs and performance indicators
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date

def render_executive_summary(dashboard, date_range, selected_properties, fund_filter, book_filter):
    """Render the Executive Summary dashboard"""
    
    # Build property filter for SQL
    if selected_properties:
        property_codes = [prop.split(" - ")[0] for prop in selected_properties]
        quoted_codes = [f"'{code}'" for code in property_codes]
        property_filter = f"\"property code\" IN ({', '.join(quoted_codes)})"
    else:
        property_filter = "1=1"
    
    # Build date filter
    if len(date_range) == 2:
        start_date, end_date = date_range
        # Convert dates to Excel serial format for database comparison
        # Excel serial date is days since January 1, 1900
        start_serial = (start_date - date(1900, 1, 1)).days + 2  # +2 for Excel's leap year bug
        end_serial = (end_date - date(1900, 1, 1)).days + 2  # +2 for Excel's leap year bug
        date_filter = f"month BETWEEN {start_serial} AND {end_serial}"
    else:
        date_filter = "1=1"
    
    # Build book filter
    book_where = ""
    if book_filter == "Book 46 (FPR)":
        book_where = "AND ft.\"book id\" = 46"
    elif book_filter == "Book 1 (Standard)":
        book_where = "AND ft.\"book id\" = 1"
    
    # Portfolio KPIs Section
    st.header("📊 Portfolio Key Performance Indicators")
    
    # Get portfolio-level metrics using actual database schema
    portfolio_query = f"""
    SELECT 
        COUNT(DISTINCT ft."property id") as property_count,
        SUM(CASE WHEN ft."amount type" = 'Revenue' THEN ft.amount ELSE 0 END) as total_revenue,
        SUM(CASE WHEN ft."amount type" = 'NOI' THEN ft.amount ELSE 0 END) as total_noi,
        COUNT(DISTINCT dp."property code") as active_properties
    FROM fact_total ft
    LEFT JOIN dim_property dp ON ft."property id" = dp."property id"
    WHERE {property_filter}
    AND {date_filter}
    {book_where}
    """
    
    portfolio_df = dashboard.get_data(portfolio_query)
    
    if not portfolio_df.empty:
        metrics = portfolio_df.iloc[0]
        
        # Display KPIs in columns
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                "🏢 Properties",
                f"{int(metrics['property_count'])}"
            )
            st.metric(
                "📊 Active Properties",
                f"{int(metrics['active_properties'])}"
            )
        
        with col2:
            st.metric(
                "💰 Total Revenue",
                dashboard.format_currency(metrics['total_revenue'] or 0)
            )
        
        with col3:
            st.metric(
                "💵 Portfolio NOI",
                dashboard.format_currency(metrics['total_noi'] or 0)
            )
        
        with col4:
            noi_margin = ((metrics['total_noi'] or 0) / (metrics['total_revenue'] or 1)) * 100 if metrics['total_revenue'] else 0
            st.metric(
                "📈 NOI Margin",
                dashboard.format_percentage(noi_margin)
            )
        
        with col5:
            st.metric(
                "📊 Portfolio Status",
                "Active" if metrics['active_properties'] > 0 else "Inactive"
            )
    
    st.markdown("---")
    
    # Charts Section
    col_left, col_right = st.columns(2)
    
    with col_left:
        # Revenue by Property Chart
        st.subheader("💰 Revenue by Property")
        
        revenue_query = f"""
        SELECT 
            dp."property name" as property_name,
            SUM(CASE WHEN ft."amount type" = 'Revenue' THEN ft.amount ELSE 0 END) as total_revenue
        FROM fact_total ft
        LEFT JOIN dim_property dp ON ft."property id" = dp."property id"
        WHERE {property_filter}
        AND {date_filter}
        {book_where}
        GROUP BY dp."property name"
        ORDER BY total_revenue DESC
        LIMIT 10
        """
        
        revenue_df = dashboard.get_data(revenue_query)
        
        if not revenue_df.empty:
            fig_revenue = px.bar(
                revenue_df, 
                x='property_name', 
                y='total_revenue',
                title="Top 10 Properties by Revenue",
                labels={'total_revenue': 'Revenue ($)', 'property_name': 'Property'},
                color='total_revenue',
                color_continuous_scale='Blues'
            )
            fig_revenue.update_layout(height=400, xaxis_tickangle=-45)
            st.plotly_chart(fig_revenue, use_container_width=True)
        else:
            st.info("No revenue data available")
    
    with col_right:
        # NOI by Property Chart
        st.subheader("💵 NOI by Property")
        
        noi_query = f"""
        SELECT 
            dp."property name" as property_name,
            SUM(CASE WHEN ft."amount type" = 'NOI' THEN ft.amount ELSE 0 END) as total_noi
        FROM fact_total ft
        LEFT JOIN dim_property dp ON ft."property id" = dp."property id"
        WHERE {property_filter}
        AND {date_filter}
        {book_where}
        GROUP BY dp."property name"
        ORDER BY total_noi DESC
        LIMIT 10
        """
        
        noi_df = dashboard.get_data(noi_query)
        
        if not noi_df.empty:
            fig_noi = px.bar(
                noi_df, 
                x='property_name', 
                y='total_noi',
                title="Top 10 Properties by NOI",
                labels={'total_noi': 'NOI ($)', 'property_name': 'Property'},
                color='total_noi',
                color_continuous_scale='Greens'
            )
            fig_noi.update_layout(height=400, xaxis_tickangle=-45)
            st.plotly_chart(fig_noi, use_container_width=True)
        else:
            st.info("No NOI data available")
        
    st.markdown("---")
    
    # Summary Section
    st.subheader("📋 Portfolio Summary")
    
    # Get basic property information
    property_summary_query = f"""
    SELECT 
        dp."property code" as property_code,
        dp."property name" as property_name,
        dp."postal city" as city,
        dp."postal state" as state,
        COUNT(DISTINCT ft."book id") as book_count
    FROM dim_property dp
    LEFT JOIN fact_total ft ON dp."property id" = ft."property id"
    WHERE {property_filter}
    AND {date_filter}
    {book_where}
    GROUP BY dp."property code", dp."property name", dp."postal city", dp."postal state"
    ORDER BY dp."property name"
    """
    
    property_df = dashboard.get_data(property_summary_query)
    
    if not property_df.empty:
        st.dataframe(
            property_df,
            column_config={
                "property_code": "Property Code",
                "property_name": "Property Name", 
                "city": "City",
                "state": "State",
                "book_count": "Books"
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("No property data available for the selected filters")
    
    # Summary insights
    st.subheader("💡 Key Insights")
    
    if not portfolio_df.empty:
        insights = []
        metrics = portfolio_df.iloc[0]
        
        # Revenue insights
        if metrics['total_revenue'] and metrics['total_revenue'] > 0:
            insights.append("✅ **Portfolio generating revenue** - Active revenue streams detected")
        
        # NOI insights
        if metrics['total_noi'] and metrics['total_noi'] > 0:
            noi_margin = (metrics['total_noi'] / metrics['total_revenue']) * 100 if metrics['total_revenue'] else 0
            if noi_margin >= 50:
                insights.append("✅ **Excellent profitability** - Portfolio NOI margin above 50%")
            elif noi_margin < 30:
                insights.append("⚠️ **Margin improvement opportunity** - Portfolio NOI margin below 30%")
        
        # Property count insights
        if metrics['active_properties'] and metrics['active_properties'] > 0:
            insights.append(f"✅ **Active portfolio** - {metrics['active_properties']} properties with data")
        
        if insights:
            for insight in insights:
                st.markdown(insight)
        else:
            st.markdown("📊 Portfolio metrics are within normal ranges")
    else:
        st.info("Unable to generate insights - no data available for selected filters")