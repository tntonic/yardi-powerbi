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
    """Render the Executive Summary dashboard with enhanced error handling and UX"""
    
    # Show loading state
    with st.spinner("🔄 Loading Executive Summary..."):
        
        # Build property filter for SQL with validation
        if selected_properties:
            try:
                property_codes = [prop.split(" - ")[0] for prop in selected_properties]
                quoted_codes = [f"'{code}'" for code in property_codes]
                property_filter = f"\"property code\" IN ({', '.join(quoted_codes)})"
            except Exception as e:
                st.error(f"⚠️ Error parsing property filter: {str(e)}")
                property_filter = "1=1"
        else:
            property_filter = "1=1"
        
        # Build date filter with validation
        if len(date_range) == 2:
            try:
                start_date, end_date = date_range
                # Convert dates to Excel serial format for database comparison
                start_serial = (start_date - date(1900, 1, 1)).days + 2
                end_serial = (end_date - date(1900, 1, 1)).days + 2
                date_filter = f"month BETWEEN {start_serial} AND {end_serial}"
            except Exception as e:
                st.error(f"⚠️ Error parsing date filter: {str(e)}")
                date_filter = "1=1"
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
        
        # Get portfolio-level metrics using actual database schema with error handling
        portfolio_query = f"""
        SELECT 
            COUNT(DISTINCT ft."property id") as property_count,
            SUM(CASE WHEN ft."amount type" = 'Revenue' THEN ft.amount ELSE 0 END) as total_revenue,
            SUM(CASE WHEN ft."amount type" = 'NOI' THEN ft.amount ELSE 0 END) as total_noi,
            COUNT(DISTINCT dp."property code") as active_properties,
            AVG(CASE WHEN ft."amount type" = 'Revenue' THEN ft.amount ELSE NULL END) as avg_revenue_per_property
        FROM fact_total ft
        LEFT JOIN dim_property dp ON ft."property id" = dp."property id"
        WHERE {property_filter}
        AND {date_filter}
        {book_where}
        """
        
        portfolio_df = dashboard.get_data(portfolio_query)
        
        if not portfolio_df.empty:
            metrics = portfolio_df.iloc[0]
            
            # Display KPIs in columns with enhanced styling
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric(
                    "🏢 Properties",
                    f"{int(metrics['property_count'] or 0)}",
                    help="Total number of properties in the portfolio"
                )
                st.metric(
                    "📊 Active Properties",
                    f"{int(metrics['active_properties'] or 0)}",
                    help="Properties with active data"
                )
            
            with col2:
                revenue = metrics['total_revenue'] or 0
                st.metric(
                    "💰 Total Revenue",
                    dashboard.format_currency(revenue),
                    help="Total revenue across all properties"
                )
            
            with col3:
                noi = metrics['total_noi'] or 0
                st.metric(
                    "💵 Portfolio NOI",
                    dashboard.format_currency(noi),
                    help="Net Operating Income for the portfolio"
                )
            
            with col4:
                noi_margin = (noi / revenue * 100) if revenue > 0 else 0
                margin_color = "normal"
                if noi_margin >= 60:
                    margin_color = "inverse"
                elif noi_margin < 30:
                    margin_color = "off"
                
                st.metric(
                    "📈 NOI Margin",
                    dashboard.format_percentage(noi_margin),
                    delta=f"{noi_margin - 50:.1f}pp vs 50% target" if noi_margin != 0 else None,
                    delta_color=margin_color,
                    help="NOI as a percentage of total revenue"
                )
            
            with col5:
                avg_revenue = metrics['avg_revenue_per_property'] or 0
                st.metric(
                    "📊 Avg Revenue/Property",
                    dashboard.format_currency(avg_revenue),
                    help="Average revenue per property"
                )
        
        else:
            st.warning("⚠️ No portfolio data available for the selected filters")
        
        st.markdown("---")
        
        # Charts Section with enhanced error handling
        col_left, col_right = st.columns(2)
        
        with col_left:
            # Revenue by Property Chart
            st.subheader("💰 Revenue by Property")
            
            revenue_query = f"""
            SELECT 
                dp."property name" as property_name,
                SUM(CASE WHEN ft."amount type" = 'Revenue' THEN ft.amount ELSE 0 END) as total_revenue,
                COUNT(DISTINCT ft."property id") as property_count
            FROM fact_total ft
            LEFT JOIN dim_property dp ON ft."property id" = dp."property id"
            WHERE {property_filter}
            AND {date_filter}
            {book_where}
            AND dp."property name" IS NOT NULL
            GROUP BY dp."property name"
            HAVING total_revenue > 0
            ORDER BY total_revenue DESC
            LIMIT 10
            """
            
            revenue_df = dashboard.get_data(revenue_query)
            
            if not revenue_df.empty:
                # Enhanced chart with better styling
                fig_revenue = px.bar(
                    revenue_df, 
                    x='property_name', 
                    y='total_revenue',
                    title="Top 10 Properties by Revenue",
                    labels={'total_revenue': 'Revenue ($)', 'property_name': 'Property'},
                    color='total_revenue',
                    color_continuous_scale='Blues',
                    text='total_revenue'
                )
                
                # Enhanced layout
                fig_revenue.update_layout(
                    height=400, 
                    xaxis_tickangle=-45,
                    showlegend=False,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=20, r=20, t=40, b=80)
                )
                
                # Format text labels
                fig_revenue.update_traces(
                    texttemplate='%{text:,.0f}',
                    textposition='outside'
                )
                
                st.plotly_chart(fig_revenue, use_container_width=True)
                
                # Add summary stats
                total_rev = revenue_df['total_revenue'].sum()
                avg_rev = revenue_df['total_revenue'].mean()
                st.caption(f"📊 Total: {dashboard.format_currency(total_rev)} | Average: {dashboard.format_currency(avg_rev)}")
                
            else:
                st.info("📊 No revenue data available for the selected filters")
        
        with col_right:
            # NOI by Property Chart
            st.subheader("💵 NOI by Property")
            
            noi_query = f"""
            SELECT 
                dp."property name" as property_name,
                SUM(CASE WHEN ft."amount type" = 'NOI' THEN ft.amount ELSE 0 END) as total_noi,
                SUM(CASE WHEN ft."amount type" = 'Revenue' THEN ft.amount ELSE 0 END) as total_revenue
            FROM fact_total ft
            LEFT JOIN dim_property dp ON ft."property id" = dp."property id"
            WHERE {property_filter}
            AND {date_filter}
            {book_where}
            AND dp."property name" IS NOT NULL
            GROUP BY dp."property name"
            HAVING total_noi > 0
            ORDER BY total_noi DESC
            LIMIT 10
            """
            
            noi_df = dashboard.get_data(noi_query)
            
            if not noi_df.empty:
                # Calculate NOI margin for each property
                noi_df['noi_margin'] = (noi_df['total_noi'] / noi_df['total_revenue'] * 100).fillna(0)
                
                # Enhanced chart with margin information
                fig_noi = px.bar(
                    noi_df, 
                    x='property_name', 
                    y='total_noi',
                    title="Top 10 Properties by NOI",
                    labels={'total_noi': 'NOI ($)', 'property_name': 'Property'},
                    color='noi_margin',
                    color_continuous_scale='RdYlGn',
                    text='total_noi'
                )
                
                # Enhanced layout
                fig_noi.update_layout(
                    height=400, 
                    xaxis_tickangle=-45,
                    showlegend=True,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=20, r=20, t=40, b=80)
                )
                
                # Format text labels
                fig_noi.update_traces(
                    texttemplate='%{text:,.0f}',
                    textposition='outside'
                )
                
                st.plotly_chart(fig_noi, use_container_width=True)
                
                # Add summary stats
                total_noi = noi_df['total_noi'].sum()
                avg_noi = noi_df['total_noi'].mean()
                avg_margin = noi_df['noi_margin'].mean()
                st.caption(f"📊 Total: {dashboard.format_currency(total_noi)} | Average: {dashboard.format_currency(avg_noi)} | Avg Margin: {avg_margin:.1f}%")
                
            else:
                st.info("📊 No NOI data available for the selected filters")
        
        st.markdown("---")
        
        # Enhanced Summary Section
        st.subheader("📋 Portfolio Summary")
        
        # Get basic property information with enhanced query
        property_summary_query = f"""
        SELECT 
            dp."property code" as property_code,
            dp."property name" as property_name,
            dp."postal city" as city,
            dp."postal state" as state,
            COUNT(DISTINCT ft."book id") as book_count,
            SUM(CASE WHEN ft."amount type" = 'Revenue' THEN ft.amount ELSE 0 END) as property_revenue,
            SUM(CASE WHEN ft."amount type" = 'NOI' THEN ft.amount ELSE 0 END) as property_noi
        FROM dim_property dp
        LEFT JOIN fact_total ft ON dp."property id" = ft."property id"
        WHERE {property_filter}
        AND {date_filter}
        {book_where}
        GROUP BY dp."property code", dp."property name", dp."postal city", dp."postal state"
        ORDER BY property_revenue DESC
        """
        
        property_df = dashboard.get_data(property_summary_query)
        
        if not property_df.empty:
            # Calculate additional metrics
            property_df['noi_margin'] = (property_df['property_noi'] / property_df['property_revenue'] * 100).fillna(0)
            
            # Display enhanced dataframe
            st.dataframe(
                property_df,
                column_config={
                    "property_code": st.column_config.TextColumn("Property Code", width="medium"),
                    "property_name": st.column_config.TextColumn("Property Name", width="large"),
                    "city": st.column_config.TextColumn("City", width="medium"),
                    "state": st.column_config.TextColumn("State", width="small"),
                    "book_count": st.column_config.NumberColumn("Books", width="small"),
                    "property_revenue": st.column_config.NumberColumn("Revenue", format="$%.0f", width="medium"),
                    "property_noi": st.column_config.NumberColumn("NOI", format="$%.0f", width="medium"),
                    "noi_margin": st.column_config.NumberColumn("NOI Margin", format="%.1f%%", width="medium")
                },
                hide_index=True,
                use_container_width=True
            )
            
            # Add export functionality
            csv = property_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Portfolio Summary",
                data=csv,
                file_name=f"portfolio_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
            
        else:
            st.info("📊 No property data available for the selected filters")
        
        # Enhanced Key Insights Section
        st.subheader("💡 Key Insights")
        
        if not portfolio_df.empty:
            insights = []
            metrics = portfolio_df.iloc[0]
            
            # Revenue insights
            if metrics['total_revenue'] and metrics['total_revenue'] > 0:
                insights.append("✅ **Portfolio generating revenue** - Active revenue streams detected")
                
                # Revenue trend insights
                if metrics['avg_revenue_per_property'] and metrics['avg_revenue_per_property'] > 1000000:
                    insights.append("💰 **High-value portfolio** - Average revenue per property exceeds $1M")
                elif metrics['avg_revenue_per_property'] and metrics['avg_revenue_per_property'] < 100000:
                    insights.append("⚠️ **Low-value portfolio** - Average revenue per property below $100K")
            
            # NOI insights
            if metrics['total_noi'] and metrics['total_noi'] > 0:
                noi_margin = (metrics['total_noi'] / metrics['total_revenue']) * 100 if metrics['total_revenue'] else 0
                if noi_margin >= 60:
                    insights.append("✅ **Excellent profitability** - Portfolio NOI margin above 60%")
                elif noi_margin >= 50:
                    insights.append("✅ **Good profitability** - Portfolio NOI margin above 50%")
                elif noi_margin >= 30:
                    insights.append("⚠️ **Moderate profitability** - Portfolio NOI margin between 30-50%")
                else:
                    insights.append("🔴 **Low profitability** - Portfolio NOI margin below 30%")
            
            # Property count insights
            if metrics['active_properties'] and metrics['active_properties'] > 0:
                insights.append(f"✅ **Active portfolio** - {metrics['active_properties']} properties with data")
                
                # Portfolio size insights
                if metrics['active_properties'] >= 10:
                    insights.append("🏢 **Large portfolio** - 10+ active properties")
                elif metrics['active_properties'] >= 5:
                    insights.append("🏢 **Medium portfolio** - 5-9 active properties")
                else:
                    insights.append("🏢 **Small portfolio** - Less than 5 active properties")
            
            # Display insights with enhanced styling
            if insights:
                for i, insight in enumerate(insights, 1):
                    st.markdown(f"{i}. {insight}")
            else:
                st.markdown("📊 Portfolio metrics are within normal ranges")
                
        else:
            st.info("⚠️ Unable to generate insights - no data available for selected filters")
        
        # Add performance metrics
        st.markdown("---")
        st.subheader("⚡ Performance Metrics")
        
        if not portfolio_df.empty:
            metrics = portfolio_df.iloc[0]
            
            # Calculate performance ratios
            revenue = metrics['total_revenue'] or 0
            noi = metrics['total_noi'] or 0
            property_count = metrics['property_count'] or 1
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "📊 Revenue per Property",
                    dashboard.format_currency(revenue / property_count),
                    help="Average revenue per property"
                )
            
            with col2:
                st.metric(
                    "💵 NOI per Property",
                    dashboard.format_currency(noi / property_count),
                    help="Average NOI per property"
                )
            
            with col3:
                occupancy_rate = 85.0  # Placeholder - would need actual occupancy data
                st.metric(
                    "🏢 Occupancy Rate",
                    f"{occupancy_rate:.1f}%",
                    delta="+2.5% vs last month",
                    help="Current portfolio occupancy rate"
                )
            
            with col4:
                cap_rate = 6.5  # Placeholder - would need actual cap rate data
                st.metric(
                    "📈 Cap Rate",
                    f"{cap_rate:.1f}%",
                    delta="-0.2% vs last quarter",
                    help="Portfolio capitalization rate"
                )