#!/usr/bin/env python3
"""
Rent Roll Analysis Dashboard Component
Simplified version using actual database schema
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

def render_rent_roll_analysis(dashboard, date_range, selected_properties, fund_filter):
    """Render the Rent Roll Analysis dashboard"""
    
    # Build property filter for SQL
    if selected_properties:
        property_codes = [prop.split(" - ")[0] for prop in selected_properties]
        quoted_codes = [f"'{code}'" for code in property_codes]
        property_filter = f"\"property code\" IN ({', '.join(quoted_codes)})"
    else:
        property_filter = "1=1"
    
    st.header("🏠 Financial Data Analysis")
    st.markdown("*Analysis of property financial data from Yardi system*")
    
    # Summary KPIs
    st.subheader("📊 Financial Summary")
    
    # Simple summary using actual database schema
    summary_query = f"""
    SELECT 
        COUNT(DISTINCT ft."property id") as total_properties,
        COUNT(DISTINCT dp."property code") as properties_with_data,
        SUM(CASE WHEN ft."amount type" = 'Revenue' THEN ft.amount ELSE 0 END) as total_revenue,
        SUM(CASE WHEN ft."amount type" = 'NOI' THEN ft.amount ELSE 0 END) as total_noi,
        COUNT(DISTINCT ft."book id") as total_books
    FROM fact_total ft
    LEFT JOIN dim_property dp ON ft."property id" = dp."property id"
    WHERE {property_filter}
    AND ft.amount > 0
    """
    
    summary_df = dashboard.get_data(summary_query)
    
    if not summary_df.empty:
        metrics = summary_df.iloc[0]
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "🏢 Total Properties",
                f"{int(metrics['total_properties'])}"
            )
            st.metric(
                "📊 Properties with Data",
                f"{int(metrics['properties_with_data'])}"
            )
        
        with col2:
            st.metric(
                "💰 Total Revenue",
                dashboard.format_currency(metrics['total_revenue'] or 0)
            )
        
        with col3:
            st.metric(
                "💵 Total NOI",
                dashboard.format_currency(metrics['total_noi'] or 0)
            )
        
        with col4:
            noi_margin = ((metrics['total_noi'] or 0) / (metrics['total_revenue'] or 1)) * 100 if metrics['total_revenue'] else 0
            st.metric(
                "📈 NOI Margin",
                dashboard.format_percentage(noi_margin)
            )
    
    st.markdown("---")
    
    # Charts Section
    col_left, col_right = st.columns(2)
    
    with col_left:
        # Revenue by Property Chart
        st.subheader("💰 Revenue by Property")
        
        revenue_query = f"""
        SELECT 
            dp."property code" as property_code,
            dp."property name" as property_name,
            SUM(CASE WHEN ft."amount type" = 'Revenue' THEN ft.amount ELSE 0 END) as total_revenue
        FROM fact_total ft
        LEFT JOIN dim_property dp ON ft."property id" = dp."property id"
        WHERE {property_filter}
        AND ft.amount > 0
        GROUP BY dp."property code", dp."property name"
        ORDER BY total_revenue DESC
        LIMIT 10
        """
        
        revenue_df = dashboard.get_data(revenue_query)
        
        if not revenue_df.empty:
            fig_revenue = px.bar(
                revenue_df, 
                x='property_code', 
                y='total_revenue',
                title="Top 10 Properties by Revenue",
                labels={'total_revenue': 'Revenue ($)', 'property_code': 'Property'},
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
            dp."property code" as property_code,
            dp."property name" as property_name,
            SUM(CASE WHEN ft."amount type" = 'NOI' THEN ft.amount ELSE 0 END) as total_noi
        FROM fact_total ft
        LEFT JOIN dim_property dp ON ft."property id" = dp."property id"
        WHERE {property_filter}
        AND ft.amount > 0
        GROUP BY dp."property code", dp."property name"
        ORDER BY total_noi DESC
        LIMIT 10
        """
        
        noi_df = dashboard.get_data(noi_query)
        
        if not noi_df.empty:
            fig_noi = px.bar(
                noi_df, 
                x='property_code', 
                y='total_noi',
                title="Top 10 Properties by NOI",
                labels={'total_noi': 'NOI ($)', 'property_code': 'Property'},
                color='total_noi',
                color_continuous_scale='Greens'
            )
            fig_noi.update_layout(height=400, xaxis_tickangle=-45)
            st.plotly_chart(fig_noi, use_container_width=True)
        else:
            st.info("No NOI data available")
    
    st.markdown("---")
    
    # Property Details Section
    st.subheader("📋 Property Details")
    
    # Get detailed property information
    property_details_query = f"""
    SELECT 
        dp."property code" as property_code,
        dp."property name" as property_name,
        dp."postal city" as city,
        dp."postal state" as state,
        dp."postal zip code" as zip_code,
        COUNT(DISTINCT ft."book id") as book_count,
        SUM(CASE WHEN ft."amount type" = 'Revenue' THEN ft.amount ELSE 0 END) as total_revenue,
        SUM(CASE WHEN ft."amount type" = 'NOI' THEN ft.amount ELSE 0 END) as total_noi
    FROM dim_property dp
    LEFT JOIN fact_total ft ON dp."property id" = ft."property id"
    WHERE {property_filter}
    GROUP BY dp."property code", dp."property name", dp."postal city", dp."postal state", dp."postal zip code"
    ORDER BY total_revenue DESC
    """
    
    property_df = dashboard.get_data(property_details_query)
    
    if not property_df.empty:
        # Calculate NOI margin
        property_df['noi_margin'] = (property_df['total_noi'] / property_df['total_revenue'] * 100).fillna(0)
        
        st.dataframe(
            property_df,
            column_config={
                "property_code": "Property Code",
                "property_name": "Property Name", 
                "city": "City",
                "state": "State",
                "zip_code": "ZIP Code",
                "book_count": "Books",
                "total_revenue": st.column_config.NumberColumn(
                    "Total Revenue",
                    format="$%.0f"
                ),
                "total_noi": st.column_config.NumberColumn(
                    "Total NOI",
                    format="$%.0f"
                ),
                "noi_margin": st.column_config.NumberColumn(
                    "NOI Margin %",
                    format="%.1f%%"
                )
            },
            hide_index=True,
            use_container_width=True
        )
        
        # Export functionality
        if st.button("📊 Export Property Details to CSV"):
            csv = property_df.to_csv(index=False)
            st.download_button(
                label="💾 Download CSV",
                data=csv,
                file_name=f"property_details_{datetime.now().strftime('%Y%m%d')}.csv",
                mime='text/csv'
            )
    else:
        st.info("No property data available for the selected filters")
    
    st.markdown("---")
    
    # Summary insights
    st.subheader("💡 Key Insights")
    
    if not summary_df.empty:
        insights = []
        metrics = summary_df.iloc[0]
        
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
        if metrics['properties_with_data'] and metrics['properties_with_data'] > 0:
            insights.append(f"✅ **Active portfolio** - {metrics['properties_with_data']} properties with data")
        
        if insights:
            for insight in insights:
                st.markdown(insight)
        else:
            st.markdown("📊 Portfolio metrics are within normal ranges")
    else:
        st.info("Unable to generate insights - no data available for selected filters")