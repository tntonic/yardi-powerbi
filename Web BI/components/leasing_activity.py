#!/usr/bin/env python3
"""
Leasing Activity Dashboard Component
Leasing metrics, trends, and activity analysis
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def render_leasing_activity(dashboard, date_range, selected_properties, fund_filter):
    """Render the Leasing Activity dashboard"""
    
    # Build property filter for SQL
    if selected_properties:
        property_codes = [prop.split(" - ")[0] for prop in selected_properties]
        property_filter = f"property_id IN (SELECT property_id FROM dim_property WHERE property_code IN ({', '.join([f\"'{code}'\" for code in property_codes])}))"
    else:
        property_filter = "1=1"
    
    # Build date filter
    if len(date_range) == 2:
        start_date, end_date = date_range
        date_filter = f"lease_start_date BETWEEN '{start_date}' AND '{end_date}'"
    else:
        date_filter = "1=1"
    
    st.header("🏃 Leasing Activity Analysis")
    st.markdown("*Track new leases, renewals, terminations, and net absorption*")
    
    # Leasing Activity KPIs
    st.subheader("📊 Activity Summary")
    
    activity_summary_query = f"""
    SELECT 
        COUNT(CASE WHEN lease_type = 'New' THEN 1 END) as new_leases,
        COUNT(CASE WHEN lease_type = 'Renewal' THEN 1 END) as renewals,
        COUNT(CASE WHEN lease_type = 'Termination' THEN 1 END) as terminations,
        SUM(CASE WHEN lease_type = 'New' THEN leased_area ELSE 0 END) as new_leases_sf,
        SUM(CASE WHEN lease_type = 'Renewal' THEN leased_area ELSE 0 END) as renewals_sf,
        SUM(CASE WHEN lease_type = 'Termination' THEN leased_area ELSE 0 END) as terminations_sf,
        SUM(CASE WHEN lease_type = 'New' THEN annual_rent ELSE 0 END) as new_rent,
        SUM(CASE WHEN lease_type = 'Renewal' THEN annual_rent ELSE 0 END) as renewal_rent,
        SUM(CASE WHEN lease_type = 'Termination' THEN annual_rent ELSE 0 END) as terminated_rent
    FROM fact_leasingactivity
    WHERE {property_filter}
    AND {date_filter}
    """
    
    activity_df = dashboard.get_data(activity_summary_query)
    
    if not activity_df.empty:
        metrics = activity_df.iloc[0]
        
        # Calculate net metrics
        net_leases = metrics['new_leases'] + metrics['renewals'] - metrics['terminations']
        net_sf = metrics['new_leases_sf'] + metrics['renewals_sf'] - metrics['terminations_sf']
        net_rent = metrics['new_rent'] + metrics['renewal_rent'] - metrics['terminated_rent']
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                "🆕 New Leases",
                f"{int(metrics['new_leases'])}",
                delta=dashboard.format_area(metrics['new_leases_sf'])
            )
        
        with col2:
            st.metric(
                "🔄 Renewals", 
                f"{int(metrics['renewals'])}",
                delta=dashboard.format_area(metrics['renewals_sf'])
            )
        
        with col3:
            st.metric(
                "❌ Terminations",
                f"{int(metrics['terminations'])}",
                delta=dashboard.format_area(metrics['terminations_sf'])
            )
        
        with col4:
            st.metric(
                "📊 Net Activity",
                f"{net_leases:+d} leases",
                delta=f"{net_sf:+,.0f} SF" if net_sf != 0 else "0 SF"
            )
        
        with col5:
            retention_rate = (metrics['renewals'] / (metrics['renewals'] + metrics['terminations']) * 100) if (metrics['renewals'] + metrics['terminations']) > 0 else 0
            st.metric(
                "🎯 Retention Rate",
                f"{retention_rate:.1f}%",
                delta=f"{retention_rate - 75:.1f}pp vs Target"
            )
    
    st.markdown("---")
    
    # Activity trends and charts
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("📈 Monthly Activity Trends")
        
        monthly_trends_query = f"""
        SELECT 
            DATE_TRUNC('month', lease_start_date) as month,
            COUNT(CASE WHEN lease_type = 'New' THEN 1 END) as new_leases,
            COUNT(CASE WHEN lease_type = 'Renewal' THEN 1 END) as renewals,
            COUNT(CASE WHEN lease_type = 'Termination' THEN 1 END) as terminations,
            SUM(CASE WHEN lease_type IN ('New', 'Renewal') THEN leased_area ELSE 0 END) as positive_sf,
            SUM(CASE WHEN lease_type = 'Termination' THEN leased_area ELSE 0 END) as negative_sf
        FROM fact_leasingactivity
        WHERE {property_filter}
        AND lease_start_date >= CURRENT_DATE - INTERVAL '12 months'
        GROUP BY DATE_TRUNC('month', lease_start_date)
        ORDER BY month
        """
        
        trends_df = dashboard.get_data(monthly_trends_query)
        
        if not trends_df.empty and len(trends_df) > 1:
            fig_trends = go.Figure()
            
            # Net SF activity
            net_activity_sf = trends_df['positive_sf'] - trends_df['negative_sf']
            fig_trends.add_trace(go.Scatter(
                x=trends_df['month'],
                y=net_activity_sf,
                mode='lines+markers',
                name='Net SF Activity',
                line=dict(color='#1f77b4', width=3),
                fill='tonexty' if (net_activity_sf >= 0).all() else None
            ))
            
            # Add zero line
            fig_trends.add_hline(y=0, line_dash="dash", line_color="gray")
            
            fig_trends.update_layout(
                title="Net Leasing Activity (SF)",
                xaxis_title="Month",
                yaxis_title="Square Feet",
                yaxis_tickformat=',.0f',
                height=400
            )
            
            st.plotly_chart(fig_trends, use_container_width=True)
        else:
            st.info("Insufficient data for trends chart")
    
    with col_right:
        st.subheader("🏢 Activity by Property")
        
        property_activity_query = f"""
        SELECT 
            p.property_code,
            p.property_name,
            COUNT(CASE WHEN la.lease_type = 'New' THEN 1 END) as new_leases,
            COUNT(CASE WHEN la.lease_type = 'Renewal' THEN 1 END) as renewals,
            COUNT(CASE WHEN la.lease_type = 'Termination' THEN 1 END) as terminations,
            SUM(CASE WHEN la.lease_type IN ('New', 'Renewal') THEN la.leased_area 
                WHEN la.lease_type = 'Termination' THEN -la.leased_area 
                ELSE 0 END) as net_activity_sf
        FROM fact_leasingactivity la
        LEFT JOIN dim_property p ON la.property_id = p.property_id
        WHERE {property_filter}
        AND {date_filter}
        GROUP BY p.property_code, p.property_name
        HAVING COUNT(*) > 0
        ORDER BY net_activity_sf DESC
        """
        
        property_df = dashboard.get_data(property_activity_query)
        
        if not property_df.empty:
            fig_property = px.bar(
                property_df,
                x='property_code',
                y='net_activity_sf',
                title='Net Activity by Property (SF)',
                hover_data=['property_name', 'new_leases', 'renewals', 'terminations'],
                color='net_activity_sf',
                color_continuous_scale='RdYlGn'
            )
            
            fig_property.update_layout(
                xaxis_title="Property Code",
                yaxis_title="Net Square Feet",
                yaxis_tickformat=',.0f',
                height=400
            )
            
            st.plotly_chart(fig_property, use_container_width=True)
        else:
            st.info("No property activity data available")
    
    st.markdown("---")
    
    # Detailed activity table
    st.subheader("📋 Detailed Activity Log")
    
    # Filters for activity table
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        activity_type_filter = st.selectbox(
            "Activity Type",
            ["All", "New", "Renewal", "Termination"]
        )
    
    with col_f2:
        min_area_filter = st.number_input("Min Area (SF)", value=0, step=1000)
    
    with col_f3:
        sort_by = st.selectbox(
            "Sort By",
            ["Date (Newest)", "Date (Oldest)", "Area (Largest)", "Rent (Highest)"]
        )
    
    # Build detailed query
    activity_filters = [property_filter, date_filter]
    
    if activity_type_filter != "All":
        activity_filters.append(f"lease_type = '{activity_type_filter}'")
    
    if min_area_filter > 0:
        activity_filters.append(f"leased_area >= {min_area_filter}")
    
    # Sort order
    if sort_by == "Date (Newest)":
        sort_order = "lease_start_date DESC"
    elif sort_by == "Date (Oldest)":
        sort_order = "lease_start_date ASC"
    elif sort_by == "Area (Largest)":
        sort_order = "leased_area DESC"
    else:  # Rent (Highest)
        sort_order = "annual_rent DESC"
    
    activity_where = " AND ".join(activity_filters)
    
    detailed_activity_query = f"""
    SELECT 
        la.lease_start_date,
        p.property_code,
        p.property_name,
        la.tenant_name,
        la.lease_type,
        la.leased_area,
        la.annual_rent,
        CASE 
            WHEN la.leased_area > 0 
            THEN la.annual_rent / la.leased_area 
            ELSE NULL 
        END as rent_psf,
        la.lease_term_months
    FROM fact_leasingactivity la
    LEFT JOIN dim_property p ON la.property_id = p.property_id
    WHERE {activity_where}
    ORDER BY {sort_order}
    LIMIT 200
    """
    
    detailed_df = dashboard.get_data(detailed_activity_query)
    
    if not detailed_df.empty:
        # Format for display
        display_df = detailed_df.copy()
        display_df['Date'] = pd.to_datetime(display_df['lease_start_date']).dt.strftime('%Y-%m-%d')
        display_df['Area'] = display_df['leased_area'].apply(lambda x: dashboard.format_area(x) if pd.notna(x) else 'N/A')
        display_df['Annual Rent'] = display_df['annual_rent'].apply(lambda x: dashboard.format_currency(x) if pd.notna(x) else 'N/A')
        display_df['Rent PSF'] = display_df['rent_psf'].apply(lambda x: f"${x:.2f}" if pd.notna(x) else 'N/A')
        display_df['Term'] = display_df['lease_term_months'].apply(lambda x: f"{x:.0f} mos" if pd.notna(x) else 'N/A')
        
        # Activity type color coding
        def color_activity_type(val):
            if val == 'New':
                return 'background-color: #d4edda; color: #155724'
            elif val == 'Renewal':
                return 'background-color: #d1ecf1; color: #0c5460'
            elif val == 'Termination':
                return 'background-color: #f8d7da; color: #721c24'
            return ''
        
        table_df = display_df[[
            'Date', 'property_code', 'property_name', 'tenant_name', 'lease_type',
            'Area', 'Annual Rent', 'Rent PSF', 'Term'
        ]].rename(columns={
            'property_code': 'Property',
            'property_name': 'Property Name',
            'tenant_name': 'Tenant',
            'lease_type': 'Type'
        })
        
        styled_df = table_df.style.applymap(color_activity_type, subset=['Type'])
        
        st.dataframe(
            styled_df,
            use_container_width=True,
            height=500
        )
        
        # Export functionality
        if st.button("📊 Export Activity Log to CSV"):
            csv = table_df.to_csv(index=False)
            st.download_button(
                label="💾 Download CSV",
                data=csv,
                file_name=f"leasing_activity_{datetime.now().strftime('%Y%m%d')}.csv",
                mime='text/csv'
            )
    else:
        st.info("No activity data found for the selected filters")
    
    st.markdown("---")
    
    # Insights section
    st.subheader("💡 Leasing Insights")
    
    if not activity_df.empty:
        insights = []
        metrics = activity_df.iloc[0]
        
        # Activity level insights
        total_activity = metrics['new_leases'] + metrics['renewals'] + metrics['terminations']
        if total_activity > 20:
            insights.append("✅ **High activity period** - Significant leasing volume")
        elif total_activity < 5:
            insights.append("📊 **Low activity period** - Consider marketing initiatives")
        
        # Net absorption insights
        net_sf = metrics['new_leases_sf'] + metrics['renewals_sf'] - metrics['terminations_sf']
        if net_sf > 10000:
            insights.append(f"🚀 **Positive net absorption** - Growing {dashboard.format_area(net_sf)}")
        elif net_sf < -10000:
            insights.append(f"⚠️ **Negative net absorption** - Contracting {dashboard.format_area(abs(net_sf))}")
        
        # Retention insights
        if (metrics['renewals'] + metrics['terminations']) > 0:
            retention_rate = metrics['renewals'] / (metrics['renewals'] + metrics['terminations']) * 100
            if retention_rate >= 80:
                insights.append(f"💚 **Strong retention** - {retention_rate:.1f}% tenant retention rate")
            elif retention_rate < 60:
                insights.append(f"📉 **Retention concern** - {retention_rate:.1f}% retention below industry average")
        
        if insights:
            for insight in insights:
                st.markdown(insight)
        else:
            st.markdown("📊 Activity levels are within normal ranges")
    else:
        st.info("Unable to generate insights - no activity data available for selected filters")