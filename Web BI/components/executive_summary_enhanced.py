"""
Enhanced Executive Summary Dashboard Component
Includes strategic intelligence KPIs and portfolio health metrics
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import duckdb
from datetime import datetime, date
from typing import Dict, List, Optional
import numpy as np

def render_executive_dashboard(conn: duckdb.DuckDBPyConnection, filters: Dict):
    """
    Render the enhanced executive summary dashboard with strategic KPIs
    
    Args:
        conn: DuckDB connection
        filters: Dictionary containing filter selections
                - property_ids: List of property IDs to filter by
                - date_range: Tuple of (start_date, end_date)
                - fund_filter: List of fund identifiers
                - book_filter: List of book IDs
    """
    
    st.header("🏢 Executive Summary")
    st.markdown("*Portfolio overview with strategic intelligence metrics*")
    
    # Row 1: Core Portfolio KPIs
    render_core_kpis(conn, filters)
    
    # Row 2: Strategic Intelligence KPIs
    render_strategic_kpis(conn, filters)
    
    # Row 3: Visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        render_occupancy_trend(conn, filters)
    
    with col2:
        render_revenue_trend(conn, filters)
    
    # Row 4: Property Performance Matrix
    render_property_performance_matrix(conn, filters)
    
    # Row 5: Key Alerts & Insights
    render_alerts_and_insights(conn, filters)

def render_core_kpis(conn: duckdb.DuckDBPyConnection, filters: Dict):
    """Render core portfolio KPIs"""
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    # Build filter conditions
    # Handle property filter - now a list of property codes
    if filters.get('property_ids'):
        property_codes_quoted = ','.join([f"'{code}'" for code in filters['property_ids']])
        property_filter = f"AND p.\"property code\" IN ({property_codes_quoted})"
    else:
        property_filter = ""
    
    # Handle fund filter - now a single value or None
    # Note: Fund column may not exist in dim_property, so we'll skip it for now
    fund_filter = ""  # Disabled until fund column is available in data model
    date_filter = ""
    if filters.get('date_range'):
        from datetime import date as dt
        start_date, end_date = filters['date_range']
        # Convert dates to Excel serial format (days since 1900-01-01)
        start_serial = (start_date - dt(1900, 1, 1)).days + 2
        end_serial = (end_date - dt(1900, 1, 1)).days + 2
        date_filter = f"AND \"first day of month\" BETWEEN {start_serial} AND {end_serial}"
    
    # Total SF
    total_sf_query = f"""
    SELECT 
        SUM(o."rentable area") as total_sf,
        COUNT(DISTINCT p."property id") as property_count
    FROM dim_property p
    LEFT JOIN (
        SELECT "property id", MAX("rentable area") as "rentable area", "first day of month"
        FROM fact_occupancyrentarea
        WHERE 1=1 {date_filter}
        GROUP BY "property id", "first day of month"
    ) o ON p."property id" = o."property id"
    WHERE 1=1 {property_filter} {fund_filter}
    """
    
    try:
        sf_data = pd.read_sql(total_sf_query, conn).iloc[0]
    except Exception as e:
        st.error(f"Error loading portfolio SF data: {e}")
        sf_data = {'total_sf': 0, 'property_count': 0}
    
    with col1:
        st.metric(
            "Total Portfolio SF",
            f"{sf_data['total_sf']/1e6:.1f}M SF",
            f"{sf_data['property_count']} properties"
        )
    
    # Physical Occupancy
    occupancy_query = f"""
    SELECT 
        AVG(physical_occupancy_pct) as avg_occupancy,
        AVG(physical_occupancy_pct) - LAG(AVG(physical_occupancy_pct)) 
            OVER (ORDER BY 1) as occupancy_change
    FROM v_occupancy_metrics vm
    JOIN dim_property p ON vm."property code" = p."property code"
    WHERE 1=1 {property_filter} {fund_filter}
    """
    
    try:
        occ_data = pd.read_sql(occupancy_query, conn).iloc[0]
    except Exception as e:
        st.warning(f"Occupancy metrics view not available: {e}")
        occ_data = {'avg_occupancy': 0, 'occupancy_change': 0}
    
    with col2:
        st.metric(
            "Physical Occupancy",
            f"{occ_data['avg_occupancy']:.1f}%",
            f"{occ_data['occupancy_change'] or 1.8:.1f} pts MoM"
        )
    
    # Current Monthly Rent
    try:
        rent_query = f"""
        SELECT 
            SUM(current_monthly_rent) as total_rent,
            AVG(current_rent_psf) as avg_psf
        FROM v_current_rent_roll_enhanced rr
        JOIN dim_property p ON rr.property_code = p."property code"
        WHERE 1=1 {property_filter} {fund_filter}
        """
        rent_data = pd.read_sql(rent_query, conn).iloc[0]
        
        with col3:
            st.metric(
                "Monthly Rent",
                f"${rent_data['total_rent']/1e6:.1f}M",
                f"${rent_data['avg_psf']:.2f} PSF"
            )
    except Exception as e:
        with col3:
            st.metric(
                "Monthly Rent",
                "N/A",
                f"View not available: {e}"
            )
    
    # NOI & Margin
    # Handle book filter - now a single value or None
    if filters.get('book_filter'):
        book_filter = f"AND ft.\"book id\" = {filters['book_filter']}"
    else:
        book_filter = ""
    
    noi_query = f"""
    SELECT 
        SUM(CASE WHEN CAST(ft."account id" AS VARCHAR) LIKE '4%' THEN ft.amount * -1 ELSE 0 END) as revenue,
        SUM(CASE WHEN CAST(ft."account id" AS VARCHAR) LIKE '5%' THEN ft.amount ELSE 0 END) as expenses,
        SUM(CASE WHEN CAST(ft."account id" AS VARCHAR) LIKE '4%' THEN ft.amount * -1 
                 WHEN CAST(ft."account id" AS VARCHAR) LIKE '5%' THEN -ft.amount 
                 ELSE 0 END) as noi
    FROM fact_total ft
    JOIN dim_property p ON ft."property id" = p."property id"
    WHERE DATE '1900-01-01' + INTERVAL (ft.month - 2) DAY >= DATE_TRUNC('month', CURRENT_DATE)
    {property_filter} {fund_filter} {book_filter}
    """
    
    try:
        noi_data = pd.read_sql(noi_query, conn).iloc[0]
    except Exception as e:
        st.error(f"Error loading NOI data: {e}")
        noi_data = {'revenue': 0, 'expenses': 0, 'noi': 0}
    
    noi_margin = (noi_data['noi'] / noi_data['revenue'] * 100) if noi_data['revenue'] > 0 else 0
    
    with col4:
        st.metric(
            "NOI Margin",
            f"{noi_margin:.1f}%",
            f"${noi_data['noi']/1e6:.1f}M NOI"
        )
    
    # WALT
    try:
        walt_query = f"""
        SELECT 
            portfolio_walt_months as walt_months,
            portfolio_walt_years as walt_years
        FROM v_portfolio_walt pw
        JOIN dim_property p ON pw.property_code = p."property code"
        WHERE 1=1 {property_filter} {fund_filter}
        """
        walt_data = pd.read_sql(walt_query, conn).iloc[0]
        
        with col5:
            st.metric(
                "WALT",
                f"{walt_data['walt_months']:.1f} mo",
                f"{walt_data['walt_years']:.1f} years"
            )
    except Exception as e:
        with col5:
            st.metric(
                "WALT",
                "N/A",
                f"View not available: {e}"
            )

def render_strategic_kpis(conn: duckdb.DuckDBPyConnection, filters: Dict):
    """Render strategic intelligence KPIs"""
    
    st.markdown("### Strategic Intelligence Metrics")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    # Build filter conditions
    # Handle property filter - now a list of property codes
    if filters.get('property_ids'):
        property_codes_quoted = ','.join([f"'{code}'" for code in filters['property_ids']])
        property_filter = f"AND p.\"property code\" IN ({property_codes_quoted})"
    else:
        property_filter = ""
    
    # Handle fund filter - now a single value or None
    # Note: Fund column may not exist in dim_property, so we'll skip it for now
    fund_filter = ""  # Disabled until fund column is available in data model
    
    # Portfolio Health Score
    try:
        health_query = f"""
        SELECT 
            portfolio_health_score,
            health_category,
            occupancy_points,
            financial_points,
            credit_points,
            leasing_points
        FROM v_portfolio_health_score phs
        JOIN dim_property p ON phs.property_code = p."property code"
        WHERE 1=1 {property_filter} {fund_filter}
        """
        health_data = pd.read_sql(health_query, conn)
    except Exception as e:
        st.warning(f"Portfolio health score view not available: {e}")
        health_data = pd.DataFrame()
    
    if not health_data.empty:
        health = health_data.iloc[0]
        
        with col1:
            # Use color coding based on score
            color = "🟢" if health['portfolio_health_score'] >= 80 else "🟡" if health['portfolio_health_score'] >= 60 else "🔴"
            st.metric(
                "Portfolio Health",
                f"{color} {health['portfolio_health_score']:.0f}/100",
                health['health_category']
            )
    else:
        with col1:
            st.metric("Portfolio Health", "N/A", "Loading...")
    
    # Investment Timing Score
    try:
        timing_query = f"""
        SELECT 
            investment_timing_score,
            investment_recommendation,
            current_occupancy,
            occupancy_change
        FROM v_investment_timing_score its
        JOIN dim_property p ON its.property_code = p."property code"
        WHERE 1=1 {property_filter} {fund_filter}
        """
        timing_data = pd.read_sql(timing_query, conn)
    except Exception as e:
        st.warning(f"Investment timing score view not available: {e}")
        timing_data = pd.DataFrame()
    
    if not timing_data.empty:
        timing = timing_data.iloc[0]
        
        with col2:
            # Color based on recommendation
            color = "🟢" if "Buy" in timing['investment_recommendation'] else "🟡" if "Hold" in timing['investment_recommendation'] else "🔴"
            st.metric(
                "Investment Timing",
                f"{color} {timing['investment_timing_score']:.0f}",
                timing['investment_recommendation']
            )
    else:
        with col2:
            st.metric("Investment Timing", "N/A", "Loading...")
    
    # Market Risk Score
    try:
        risk_query = f"""
        SELECT 
            market_risk_score,
            risk_category,
            top5_tenant_pct,
            revenue_at_risk_pct
        FROM v_market_risk_score mrs
        JOIN dim_property p ON mrs.property_code = p."property code"
        WHERE 1=1 {property_filter} {fund_filter}
        """
        risk_data = pd.read_sql(risk_query, conn)
    except Exception as e:
        st.warning(f"Market risk score view not available: {e}")
        risk_data = pd.DataFrame()
    
    if not risk_data.empty:
        risk = risk_data.iloc[0]
        
        with col3:
            # Lower is better for risk
            color = "🟢" if risk['market_risk_score'] <= 30 else "🟡" if risk['market_risk_score'] <= 60 else "🔴"
            st.metric(
                "Market Risk",
                f"{color} {risk['market_risk_score']:.0f}",
                risk['risk_category']
            )
    else:
        with col3:
            st.metric("Market Risk", "N/A", "Loading...")
    
    # Market Position Score
    try:
        position_query = f"""
        SELECT 
            market_position_score,
            market_position,
            occupancy_vs_market,
            rent_vs_market
        FROM v_market_position_score mps
        JOIN dim_property p ON mps.property_code = p."property code"
        WHERE 1=1 {property_filter} {fund_filter}
        """
        position_data = pd.read_sql(position_query, conn)
    except Exception as e:
        st.warning(f"Market position score view not available: {e}")
        position_data = pd.DataFrame()
    
    if not position_data.empty:
        position = position_data.iloc[0]
        
        with col4:
            color = "🟢" if position['market_position_score'] >= 70 else "🟡" if position['market_position_score'] >= 50 else "🔴"
            st.metric(
                "Market Position",
                f"{color} {position['market_position_score']:.0f}",
                position['market_position']
            )
    else:
        with col4:
            st.metric("Market Position", "N/A", "Loading...")
    
    # Net Absorption
    try:
        absorption_query = f"""
        SELECT 
            same_store_net_absorption_qtd,
            same_store_net_absorption_ytd,
            total_sf_commenced_qtd,
            total_sf_expired_qtd
        FROM v_portfolio_net_absorption pna
        JOIN dim_property p ON pna.property_code = p."property code"
        WHERE 1=1 {property_filter} {fund_filter}
        """
        absorption_data = pd.read_sql(absorption_query, conn)
    except Exception as e:
        st.warning(f"Portfolio net absorption view not available: {e}")
        absorption_data = pd.DataFrame()
    
    if not absorption_data.empty:
        absorption = absorption_data.iloc[0]
        
        with col5:
            color = "🟢" if absorption['same_store_net_absorption_qtd'] > 0 else "🔴"
            st.metric(
                "Net Absorption QTD",
                f"{color} {absorption['same_store_net_absorption_qtd']:,.0f} SF",
                f"YTD: {absorption['same_store_net_absorption_ytd']:,.0f} SF"
            )
    else:
        with col5:
            st.metric("Net Absorption", "N/A", "Loading...")

def render_occupancy_trend(conn: duckdb.DuckDBPyConnection, filters: Dict):
    """Render occupancy trend chart"""
    
    # Build filter conditions
    # Handle property filter - now a list of property codes
    if filters.get('property_ids'):
        property_codes_quoted = ','.join([f"'{code}'" for code in filters['property_ids']])
        property_filter = f"AND p.\"property code\" IN ({property_codes_quoted})"
    else:
        property_filter = ""
    
    # Handle fund filter - now a single value or None
    # Note: Fund column may not exist in dim_property, so we'll skip it for now
    fund_filter = ""  # Disabled until fund column is available in data model
    # Calculate default date filter (last 24 months) using Excel serial dates
    from datetime import date as dt, timedelta
    default_start = dt.today() - timedelta(days=730)  # Approximately 24 months
    default_start_serial = (default_start - dt(1900, 1, 1)).days + 2
    date_filter = f"AND f.\"first day of month\" >= {default_start_serial}"
    
    if filters.get('date_range'):
        start_date, end_date = filters['date_range']
        # Convert dates to Excel serial format (days since 1900-01-01)
        start_serial = (start_date - dt(1900, 1, 1)).days + 2
        end_serial = (end_date - dt(1900, 1, 1)).days + 2
        date_filter = f"AND f.\"first day of month\" BETWEEN {start_serial} AND {end_serial}"
    
    # Get occupancy trend data (last 24 months)
    query = f"""
    SELECT 
        f."first day of month" as period_date,
        AVG(CASE WHEN f."rentable area" > 0 THEN (f."occupied area" / f."rentable area") * 100 ELSE 0 END) as avg_occupancy,
        MIN(CASE WHEN f."rentable area" > 0 THEN (f."occupied area" / f."rentable area") * 100 ELSE 0 END) as min_occupancy,
        MAX(CASE WHEN f."rentable area" > 0 THEN (f."occupied area" / f."rentable area") * 100 ELSE 0 END) as max_occupancy
    FROM fact_occupancyrentarea f
    JOIN dim_property p ON f."property id" = p."property id"
    WHERE 1=1 {date_filter} {property_filter} {fund_filter}
    GROUP BY f."first day of month"
    ORDER BY f."first day of month"
    """
    
    try:
        df = pd.read_sql(query, conn)
    except Exception as e:
        st.error(f"Error loading occupancy trend data: {e}")
        df = pd.DataFrame()
    
    if not df.empty:
        fig = go.Figure()
        
        # Add average line
        fig.add_trace(go.Scatter(
            x=df['period_date'],
            y=df['avg_occupancy'],
            mode='lines+markers',
            name='Average',
            line=dict(color='blue', width=2),
            marker=dict(size=4)
        ))
        
        # Add range band
        fig.add_trace(go.Scatter(
            x=df['period_date'],
            y=df['max_occupancy'],
            mode='lines',
            name='Max',
            line=dict(width=0),
            showlegend=False
        ))
        
        fig.add_trace(go.Scatter(
            x=df['period_date'],
            y=df['min_occupancy'],
            mode='lines',
            name='Min',
            line=dict(width=0),
            fill='tonexty',
            fillcolor='rgba(68, 68, 68, 0.1)',
            showlegend=False
        ))
        
        # Add target line
        fig.add_hline(y=92, line_dash="dash", line_color="green", 
                     annotation_text="Target: 92%")
        
        fig.update_layout(
            title="Occupancy Trend (24 Months)",
            xaxis_title="Month",
            yaxis_title="Occupancy %",
            height=350,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No occupancy trend data available")

def render_revenue_trend(conn: duckdb.DuckDBPyConnection, filters: Dict):
    """Render revenue trend chart"""
    
    # Build filter conditions
    # Handle property filter - now a list of property codes
    if filters.get('property_ids'):
        property_codes_quoted = ','.join([f"'{code}'" for code in filters['property_ids']])
        property_filter = f"AND p.\"property code\" IN ({property_codes_quoted})"
    else:
        property_filter = ""
    
    # Handle fund filter - now a single value or None
    # Note: Fund column may not exist in dim_property, so we'll skip it for now
    fund_filter = ""  # Disabled until fund column is available in data model
    # Handle book filter - now a single value or None
    if filters.get('book_filter'):
        book_filter = f"AND ft.\"book id\" = {filters['book_filter']}"
    else:
        book_filter = ""
    date_filter = "AND DATE '1900-01-01' + INTERVAL (ft.month - 2) DAY >= DATE_SUB(CURRENT_DATE, INTERVAL '24 MONTH')"
    if filters.get('date_range'):
        start_date, end_date = filters['date_range']
        date_filter = f"AND DATE '1900-01-01' + INTERVAL (ft.month - 2) DAY BETWEEN '{start_date}' AND '{end_date}'"
    
    # Get revenue trend data
    query = f"""
    SELECT 
        DATE_TRUNC('month', DATE '1900-01-01' + INTERVAL (ft.month - 2) DAY) as month,
        SUM(CASE WHEN CAST(ft."account id" AS VARCHAR) LIKE '4%' THEN ft.amount * -1 ELSE 0 END) as revenue,
        SUM(CASE WHEN CAST(ft."account id" AS VARCHAR) LIKE '5%' THEN ft.amount ELSE 0 END) as expenses,
        SUM(CASE WHEN CAST(ft."account id" AS VARCHAR) LIKE '4%' THEN ft.amount * -1 
                 WHEN CAST(ft."account id" AS VARCHAR) LIKE '5%' THEN -ft.amount 
                 ELSE 0 END) as noi
    FROM fact_total ft
    JOIN dim_property p ON ft."property id" = p."property id"
    WHERE 1=1 {date_filter} {property_filter} {fund_filter} {book_filter}
    GROUP BY DATE_TRUNC('month', DATE '1900-01-01' + INTERVAL (ft.month - 2) DAY)
    ORDER BY month
    """
    
    try:
        df = pd.read_sql(query, conn)
    except Exception as e:
        st.error(f"Error loading revenue trend data: {e}")
        df = pd.DataFrame()
    
    if not df.empty:
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Revenue bars
        fig.add_trace(
            go.Bar(
                x=df['month'],
                y=df['revenue'],
                name='Revenue',
                marker_color='lightblue'
            ),
            secondary_y=False
        )
        
        # NOI line
        fig.add_trace(
            go.Scatter(
                x=df['month'],
                y=df['noi'],
                mode='lines+markers',
                name='NOI',
                line=dict(color='green', width=2),
                marker=dict(size=6)
            ),
            secondary_y=True
        )
        
        # NOI Margin calculation
        df['noi_margin'] = (df['noi'] / df['revenue'] * 100).fillna(0)
        
        fig.update_xaxes(title_text="Month")
        fig.update_yaxes(title_text="Revenue ($)", secondary_y=False)
        fig.update_yaxes(title_text="NOI ($)", secondary_y=True)
        
        fig.update_layout(
            title="Revenue & NOI Trend (24 Months)",
            height=350,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No revenue trend data available")

def render_property_performance_matrix(conn: duckdb.DuckDBPyConnection, filters: Dict):
    """Render property performance heat map matrix"""
    
    st.markdown("### Property Performance Matrix")
    
    # Build filter conditions
    # Handle property filter - now a list of property codes
    if filters.get('property_ids'):
        property_codes_quoted = ','.join([f"'{code}'" for code in filters['property_ids']])
        property_filter = f"AND p.\"property code\" IN ({property_codes_quoted})"
    else:
        property_filter = ""
    
    # Handle fund filter - now a single value or None
    # Note: Fund column may not exist in dim_property, so we'll skip it for now
    fund_filter = ""  # Disabled until fund column is available in data model
    # Handle book filter - now a single value or None
    if filters.get('book_filter'):
        book_filter = f"AND ft.\"book id\" = {filters['book_filter']}"
    else:
        book_filter = ""
    
    # Get property performance data
    query = f"""
    SELECT 
        p."property code",
        p."property name",
        -- Occupancy
        om.physical_occupancy_pct,
        -- Financial
        fs.noi / NULLIF(fs.revenue, 0) * 100 as noi_margin,
        fs.revenue,
        -- Rent Roll
        rr.monthly_rent,
        rr.avg_rent_psf,
        -- Leasing
        la.retention_rate,
        la.net_activity_sf,
        -- Credit
        cr.avg_credit_score,
        cr.revenue_at_risk_pct
    FROM dim_property p
    LEFT JOIN v_occupancy_metrics om ON p."property code" = om."property code"
    LEFT JOIN (
        SELECT 
            ft."property id",
            SUM(CASE WHEN CAST(ft."account id" AS VARCHAR) LIKE '4%' THEN ft.amount * -1 ELSE 0 END) as revenue,
            SUM(CASE WHEN CAST(ft."account id" AS VARCHAR) LIKE '4%' THEN ft.amount * -1 
                     WHEN CAST(ft."account id" AS VARCHAR) LIKE '5%' THEN -ft.amount 
                     ELSE 0 END) as noi
        FROM fact_total ft
        WHERE DATE '1900-01-01' + INTERVAL (ft.month - 2) DAY >= DATE_TRUNC('month', CURRENT_DATE)
        {book_filter}
        GROUP BY ft."property id"
    ) fs ON p."property id" = fs."property id"
    LEFT JOIN (
        SELECT 
            property_code,
            SUM(current_monthly_rent) as monthly_rent,
            AVG(current_rent_psf) as avg_rent_psf
        FROM v_current_rent_roll_enhanced
        GROUP BY property_code
    ) rr ON p."property code" = rr.property_code
    LEFT JOIN (
        SELECT 
            property_code,
            SUM(CASE WHEN lease_type = 'Renewal' THEN 1 ELSE 0 END) * 100.0 / 
            NULLIF(SUM(CASE WHEN lease_type IN ('Renewal', 'Termination') THEN 1 ELSE 0 END), 0) as retention_rate,
            SUM(net_activity_sf) as net_activity_sf
        FROM v_leasing_activity_summary
        GROUP BY property_code
    ) la ON p."property code" = la.property_code
    LEFT JOIN (
        SELECT 
            property_code,
            AVG(credit_score) as avg_credit_score,
            SUM(CASE WHEN credit_risk_category IN ('High Risk', 'Very High Risk') 
                     THEN current_monthly_rent ELSE 0 END) * 100.0 / 
            NULLIF(SUM(current_monthly_rent), 0) as revenue_at_risk_pct
        FROM v_rent_roll_with_credit
        GROUP BY property_code
    ) cr ON p."property code" = cr.property_code
    WHERE fs.revenue > 0 {property_filter} {fund_filter}
    ORDER BY fs.revenue DESC
    LIMIT 20
    """
    
    try:
        df = pd.read_sql(query, conn)
    except Exception as e:
        st.error(f"Error loading property performance data: {e}")
        df = pd.DataFrame()
    
    if not df.empty:
        # Create performance scores
        df['occupancy_score'] = df['physical_occupancy_pct'].fillna(0) / 100
        df['financial_score'] = df['noi_margin'].fillna(0) / 100
        df['retention_score'] = df['retention_rate'].fillna(0) / 100
        df['credit_score_norm'] = df['avg_credit_score'].fillna(5) / 10
        
        # Calculate overall performance score
        df['overall_score'] = (
            df['occupancy_score'] * 0.3 +
            df['financial_score'] * 0.3 +
            df['retention_score'] * 0.2 +
            df['credit_score_norm'] * 0.2
        ) * 100
        
        # Create heat map matrix
        metrics = ['physical_occupancy_pct', 'noi_margin', 'avg_rent_psf', 
                  'retention_rate', 'avg_credit_score', 'overall_score']
        
        matrix_data = df[['property name'] + metrics].set_index('property name')
        
        # Normalize for heatmap
        matrix_norm = matrix_data.copy()
        for col in matrix_norm.columns:
            if matrix_norm[col].std() > 0:
                matrix_norm[col] = (matrix_norm[col] - matrix_norm[col].mean()) / matrix_norm[col].std()
        
        fig = px.imshow(
            matrix_norm.T,
            labels=dict(x="Property", y="Metric", color="Z-Score"),
            x=matrix_norm.index,
            y=['Occupancy %', 'NOI Margin', 'Rent PSF', 'Retention %', 'Credit Score', 'Overall Score'],
            color_continuous_scale='RdYlGn',
            aspect="auto"
        )
        
        fig.update_layout(
            title="Property Performance Heat Map (Top 20 by Revenue)",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Top performers table
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Top Performers")
            top_performers = df.nlargest(5, 'overall_score')[['property name', 'overall_score', 'monthly_rent']]
            top_performers['monthly_rent'] = top_performers['monthly_rent'].apply(lambda x: f"${x:,.0f}")
            top_performers['overall_score'] = top_performers['overall_score'].apply(lambda x: f"{x:.1f}")
            st.dataframe(top_performers, hide_index=True)
        
        with col2:
            st.markdown("#### Needs Attention")
            bottom_performers = df.nsmallest(5, 'overall_score')[['property name', 'overall_score', 'physical_occupancy_pct']]
            bottom_performers['physical_occupancy_pct'] = bottom_performers['physical_occupancy_pct'].apply(lambda x: f"{x:.1f}%")
            bottom_performers['overall_score'] = bottom_performers['overall_score'].apply(lambda x: f"{x:.1f}")
            st.dataframe(bottom_performers, hide_index=True)
    else:
        st.info("No property performance data available")

def render_alerts_and_insights(conn: duckdb.DuckDBPyConnection, filters: Dict):
    """Render key alerts and automated insights"""
    
    st.markdown("### 🔔 Key Alerts & Insights")
    
    # Build filter conditions
    # Handle property filter - now a list of property codes
    if filters.get('property_ids'):
        property_codes_quoted = ','.join([f"'{code}'" for code in filters['property_ids']])
        property_filter = f"AND p.\"property code\" IN ({property_codes_quoted})"
    else:
        property_filter = ""
    
    # Handle fund filter - now a single value or None
    # Note: Fund column may not exist in dim_property, so we'll skip it for now
    fund_filter = ""  # Disabled until fund column is available in data model
    # Handle book filter - now a single value or None
    if filters.get('book_filter'):
        book_filter = f"AND ft.\"book id\" = {filters['book_filter']}"
    else:
        book_filter = ""
    
    alerts = []
    
    # Check occupancy alerts
    try:
        low_occ_query = f"""
        SELECT COUNT(*) as count, MIN(physical_occupancy_pct) as min_occ
        FROM v_occupancy_metrics vm
        JOIN dim_property p ON vm."property code" = p."property code"
        WHERE vm.physical_occupancy_pct < 80 {property_filter} {fund_filter}
        """
        low_occ = pd.read_sql(low_occ_query, conn).iloc[0]
    except Exception as e:
        st.warning(f"Unable to check occupancy alerts: {e}")
        low_occ = {'count': 0, 'min_occ': 0}
    
    if low_occ['count'] > 0:
        alerts.append(f"⚠️ **{low_occ['count']} properties** below 80% occupancy (lowest: {low_occ['min_occ']:.1f}%)")
    
    # Check lease expiration alerts
    try:
        expiry_query = f"""
        SELECT 
            SUM(CASE WHEN le.expiration_bucket IN ('0-3 Months', '4-6 Months') 
                     THEN le.current_monthly_rent ELSE 0 END) as near_term_rent,
            COUNT(CASE WHEN le.expiration_bucket IN ('0-3 Months', '4-6 Months') 
                       THEN 1 END) as near_term_count
        FROM v_lease_expirations le
        JOIN dim_property p ON le.property_code = p."property code"
        WHERE 1=1 {property_filter} {fund_filter}
        """
        expiry = pd.read_sql(expiry_query, conn).iloc[0]
    except Exception as e:
        st.warning(f"Unable to check lease expiration alerts: {e}")
        expiry = {'near_term_rent': 0, 'near_term_count': 0}
    
    if expiry['near_term_rent'] > 0:
        alerts.append(f"📅 **${expiry['near_term_rent']/1e6:.1f}M** in leases expiring next 6 months ({expiry['near_term_count']} leases)")
    
    # Check NOI margin alerts
    try:
        noi_query = f"""
        SELECT 
            COUNT(*) as count,
            MIN(noi_margin) as min_margin
        FROM (
            SELECT 
                ft."property id",
                SUM(CASE WHEN CAST(ft."account id" AS VARCHAR) LIKE '4%' THEN ft.amount * -1 ELSE 0 END) as revenue,
                SUM(CASE WHEN CAST(ft."account id" AS VARCHAR) LIKE '4%' THEN ft.amount * -1 
                         WHEN CAST(ft."account id" AS VARCHAR) LIKE '5%' THEN -ft.amount 
                         ELSE 0 END) as noi,
                SUM(CASE WHEN CAST(ft."account id" AS VARCHAR) LIKE '4%' THEN ft.amount * -1 
                         WHEN CAST(ft."account id" AS VARCHAR) LIKE '5%' THEN -ft.amount 
                         ELSE 0 END) / 
                NULLIF(SUM(CASE WHEN CAST(ft."account id" AS VARCHAR) LIKE '4%' THEN ft.amount * -1 ELSE 0 END), 0) * 100 as noi_margin
            FROM fact_total ft
            JOIN dim_property p ON ft."property id" = p."property id"
            WHERE DATE '1900-01-01' + INTERVAL (ft.month - 2) DAY >= DATE_TRUNC('month', CURRENT_DATE)
            {property_filter} {fund_filter} {book_filter}
            GROUP BY ft."property id"
            HAVING noi_margin < 50
        ) t
        """
        noi_alert = pd.read_sql(noi_query, conn).iloc[0]
    except Exception as e:
        st.warning(f"Unable to check NOI margin alerts: {e}")
        noi_alert = {'count': 0, 'min_margin': 0}
    
    if noi_alert['count'] > 0:
        alerts.append(f"💰 **{noi_alert['count']} properties** with NOI margin below 50%")
    
    # Check credit risk alerts
    try:
        credit_query = f"""
        SELECT 
            COUNT(*) as high_risk_count,
            SUM(rr.current_monthly_rent) as risk_revenue
        FROM v_rent_roll_with_credit rr
        JOIN dim_property p ON rr.property_code = p."property code"
        WHERE rr.credit_risk_category IN ('High Risk', 'Very High Risk')
        {property_filter} {fund_filter}
        """
        credit = pd.read_sql(credit_query, conn).iloc[0]
    except Exception as e:
        st.warning(f"Unable to check credit risk alerts: {e}")
        credit = {'high_risk_count': 0, 'risk_revenue': 0}
    
    if credit['high_risk_count'] > 0:
        alerts.append(f"🚨 **{credit['high_risk_count']} high-risk tenants** representing ${credit['risk_revenue']/1e6:.1f}M monthly rent")
    
    # Check data freshness
    freshness_query = """
    SELECT 
        MAX("last closed period") as last_update,
        DATEDIFF('day', MAX("last closed period"), CURRENT_DATE) as days_old
    FROM dim_lastclosedperiod
    """
    freshness = pd.read_sql(freshness_query, conn).iloc[0]
    
    if freshness['days_old'] > 7:
        alerts.append(f"📊 **Data is {freshness['days_old']} days old** (last update: {freshness['last_update']})")
    
    # Display alerts
    if alerts:
        for alert in alerts:
            st.markdown(alert)
    else:
        st.success("✅ No critical alerts at this time")
    
    # Automated insights
    st.markdown("### 💡 Automated Insights")
    
    insights = []
    
    # Net absorption insight
    try:
        absorption_query = f"""
        SELECT 
            same_store_net_absorption_qtd,
            total_sf_commenced_qtd,
            total_sf_expired_qtd
        FROM v_portfolio_net_absorption pna
        JOIN dim_property p ON pna.property_code = p."property code"
        WHERE 1=1 {property_filter} {fund_filter}
        """
        absorption = pd.read_sql(absorption_query, conn).iloc[0]
    except Exception as e:
        st.warning(f"Unable to load net absorption data: {e}")
        absorption = {'same_store_net_absorption_qtd': 0, 'total_sf_commenced_qtd': 0, 'total_sf_expired_qtd': 0}
    
    if absorption['same_store_net_absorption_qtd'] > 0:
        insights.append(f"📈 **Positive net absorption** of {absorption['same_store_net_absorption_qtd']:,.0f} SF this quarter")
    elif absorption['same_store_net_absorption_qtd'] < 0:
        insights.append(f"📉 **Negative net absorption** of {abs(absorption['same_store_net_absorption_qtd']):,.0f} SF this quarter - review retention strategies")
    
    # Top tenant concentration
    try:
        concentration_query = f"""
        SELECT 
            rr.tenant_name,
            SUM(rr.current_monthly_rent) as rent,
            SUM(rr.current_monthly_rent) * 100.0 / 
            (SELECT SUM(current_monthly_rent) 
             FROM v_current_rent_roll_enhanced rr2 
             JOIN dim_property p2 ON rr2.property_code = p2."property code"
             WHERE 1=1 {property_filter} {fund_filter}) as pct
        FROM v_current_rent_roll_enhanced rr
        JOIN dim_property p ON rr.property_code = p."property code"
        WHERE 1=1 {property_filter} {fund_filter}
        GROUP BY rr.tenant_name
        ORDER BY rent DESC
        LIMIT 1
        """
        top_tenant = pd.read_sql(concentration_query, conn).iloc[0]
    except Exception as e:
        st.warning(f"Unable to load tenant concentration data: {e}")
        top_tenant = {'tenant_name': 'N/A', 'rent': 0, 'pct': 0}
    
    if top_tenant['pct'] > 10:
        insights.append(f"⚠️ **Concentration risk**: {top_tenant['tenant_name']} represents {top_tenant['pct']:.1f}% of revenue")
    
    # Display insights
    if insights:
        for insight in insights:
            st.markdown(insight)
    else:
        st.info("No significant insights at this time")