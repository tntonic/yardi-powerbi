#!/usr/bin/env python3
"""
Credit Risk Analysis Dashboard Component
Tenant credit scores, risk assessment, and portfolio risk analysis
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def render_credit_risk_analysis(dashboard, date_range, selected_properties, fund_filter):
    """Render the Credit Risk Analysis dashboard"""
    
    # Build property filter for SQL
    if selected_properties:
        property_codes = [prop.split(" - ")[0] for prop in selected_properties]
        property_filter = f"property_code IN ({', '.join([f\"'{code}'\" for code in property_codes])})"
    else:
        property_filter = "1=1"
    
    st.header("⚠️ Credit Risk Analysis Dashboard")
    st.markdown("*Comprehensive tenant credit scoring and portfolio risk assessment*")
    
    # Credit Risk KPIs
    st.subheader("📊 Credit Risk Overview")
    
    credit_summary_query = f"""
    SELECT 
        COUNT(DISTINCT tenant_hmy) as total_tenants,
        COUNT(DISTINCT CASE WHEN credit_score IS NOT NULL THEN tenant_hmy END) as tenants_with_scores,
        AVG(credit_score) as avg_credit_score,
        SUM(CASE WHEN credit_score IS NOT NULL THEN CAST(monthly_amount AS DECIMAL(15,2)) ELSE 0 END) as rent_with_scores,
        SUM(CAST(monthly_amount AS DECIMAL(15,2))) as total_rent,
        COUNT(CASE WHEN credit_score < 4 THEN 1 END) as very_high_risk_count,
        COUNT(CASE WHEN credit_score >= 4 AND credit_score < 6 THEN 1 END) as high_risk_count,
        COUNT(CASE WHEN credit_score >= 6 AND credit_score < 8 THEN 1 END) as medium_risk_count,
        COUNT(CASE WHEN credit_score >= 8 THEN 1 END) as low_risk_count
    FROM v_rent_roll_enhanced
    WHERE {property_filter}
    AND charge_code = 'rent'
    AND monthly_amount > 0
    """
    
    summary_df = dashboard.get_data(credit_summary_query)
    
    if not summary_df.empty:
        metrics = summary_df.iloc[0]
        
        # Calculate derived metrics
        coverage_pct = (metrics['tenants_with_scores'] / metrics['total_tenants'] * 100) if metrics['total_tenants'] > 0 else 0
        rent_coverage_pct = (metrics['rent_with_scores'] / metrics['total_rent'] * 100) if metrics['total_rent'] > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "👥 Total Tenants",
                f"{int(metrics['total_tenants'])}"
            )
            st.metric(
                "📊 Credit Coverage",
                f"{coverage_pct:.1f}%",
                delta=f"{coverage_pct - 70:.1f}pp vs 70% target"
            )
        
        with col2:
            st.metric(
                "⭐ Avg Credit Score",
                f"{metrics['avg_credit_score']:.1f}/10" if metrics['avg_credit_score'] else "N/A",
                delta=f"{(metrics['avg_credit_score'] or 0) - 6:.1f} vs 6.0 target" if metrics['avg_credit_score'] else None
            )
            st.metric(
                "💰 Rent Coverage",
                f"{rent_coverage_pct:.1f}%"
            )
        
        with col3:
            st.metric(
                "🟢 Low Risk",
                f"{int(metrics['low_risk_count'])}",
                delta=f"{(metrics['low_risk_count'] / metrics['total_tenants'] * 100):.1f}% of portfolio" if metrics['total_tenants'] > 0 else None
            )
        
        with col4:
            st.metric(
                "🔴 High + Very High Risk",
                f"{int(metrics['high_risk_count'] + metrics['very_high_risk_count'])}",
                delta=f"{((metrics['high_risk_count'] + metrics['very_high_risk_count']) / metrics['total_tenants'] * 100):.1f}% of portfolio" if metrics['total_tenants'] > 0 else None
            )
    
    st.markdown("---")
    
    # Risk distribution charts
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("🎯 Credit Risk Distribution")
        
        risk_distribution_query = f"""
        SELECT 
            credit_risk_category,
            COUNT(*) as tenant_count,
            SUM(CAST(monthly_amount AS DECIMAL(15,2))) as monthly_rent,
            AVG(credit_score) as avg_score
        FROM v_rent_roll_enhanced
        WHERE {property_filter}
        AND charge_code = 'rent'
        AND monthly_amount > 0
        AND credit_risk_category IS NOT NULL
        GROUP BY credit_risk_category
        ORDER BY 
            CASE credit_risk_category
                WHEN 'Low Risk' THEN 1
                WHEN 'Medium Risk' THEN 2
                WHEN 'High Risk' THEN 3
                WHEN 'Very High Risk' THEN 4
                ELSE 5
            END
        """
        
        risk_df = dashboard.get_data(risk_distribution_query)
        
        if not risk_df.empty:
            # Create donut chart
            fig_risk = px.pie(
                risk_df,
                values='monthly_rent',
                names='credit_risk_category',
                title='Monthly Rent by Risk Category',
                color_discrete_map={
                    'Low Risk': '#2ca02c',
                    'Medium Risk': '#1f77b4',
                    'High Risk': '#ff7f0e',
                    'Very High Risk': '#d62728'
                },
                hole=0.4
            )
            
            fig_risk.update_traces(
                textposition='inside', 
                textinfo='percent+label',
                hovertemplate='<b>%{label}</b><br>Rent: $%{value:,.0f}<br>Percentage: %{percent}<extra></extra>'
            )
            
            fig_risk.update_layout(height=400)
            st.plotly_chart(fig_risk, use_container_width=True)
        else:
            st.info("No credit risk data available")
    
    with col_right:
        st.subheader("📈 Credit Score Distribution")
        
        score_distribution_query = f"""
        SELECT 
            credit_score,
            COUNT(*) as tenant_count,
            SUM(CAST(monthly_amount AS DECIMAL(15,2))) as monthly_rent
        FROM v_rent_roll_enhanced
        WHERE {property_filter}
        AND charge_code = 'rent'
        AND monthly_amount > 0
        AND credit_score IS NOT NULL
        GROUP BY credit_score
        ORDER BY credit_score
        """
        
        score_df = dashboard.get_data(score_distribution_query)
        
        if not score_df.empty:
            fig_score = px.histogram(
                score_df,
                x='credit_score',
                y='tenant_count',
                title='Tenant Count by Credit Score',
                nbins=10,
                color_discrete_sequence=['#1f77b4']
            )
            
            # Add risk zone backgrounds
            fig_score.add_vrect(x0=0, x1=4, fillcolor="red", opacity=0.1, line_width=0)
            fig_score.add_vrect(x0=4, x1=6, fillcolor="orange", opacity=0.1, line_width=0)
            fig_score.add_vrect(x0=6, x1=8, fillcolor="yellow", opacity=0.1, line_width=0)
            fig_score.add_vrect(x0=8, x1=10, fillcolor="green", opacity=0.1, line_width=0)
            
            # Add mean line
            mean_score = score_df['credit_score'].mean()
            fig_score.add_vline(
                x=mean_score,
                line_dash="dash",
                line_color="red",
                annotation_text=f"Mean: {mean_score:.1f}"
            )
            
            fig_score.update_layout(
                xaxis_title="Credit Score",
                yaxis_title="Number of Tenants",
                xaxis=dict(range=[0, 10]),
                height=400
            )
            
            st.plotly_chart(fig_score, use_container_width=True)
        else:
            st.info("No credit score distribution data available")
    
    st.markdown("---")
    
    # Portfolio risk metrics
    st.subheader("📊 Portfolio Risk Metrics")
    
    col_risk1, col_risk2 = st.columns(2)
    
    with col_risk1:
        st.markdown("**🏢 Risk by Property**")
        
        property_risk_query = f"""
        SELECT 
            property_code,
            property_name,
            COUNT(*) as tenant_count,
            AVG(credit_score) as avg_credit_score,
            SUM(CAST(monthly_amount AS DECIMAL(15,2))) as monthly_rent,
            COUNT(CASE WHEN credit_score < 5 THEN 1 END) as high_risk_tenants,
            SUM(CASE WHEN credit_score < 5 THEN CAST(monthly_amount AS DECIMAL(15,2)) ELSE 0 END) as high_risk_rent
        FROM v_rent_roll_enhanced
        WHERE {property_filter}
        AND charge_code = 'rent'
        AND monthly_amount > 0
        AND credit_score IS NOT NULL
        GROUP BY property_code, property_name
        ORDER BY avg_credit_score ASC
        """
        
        prop_risk_df = dashboard.get_data(property_risk_query)
        
        if not prop_risk_df.empty:
            # Calculate risk percentage
            prop_risk_df['high_risk_pct'] = (prop_risk_df['high_risk_rent'] / prop_risk_df['monthly_rent'] * 100).fillna(0)
            
            fig_prop_risk = px.scatter(
                prop_risk_df,
                x='avg_credit_score',
                y='high_risk_pct',
                size='monthly_rent',
                hover_name='property_name',
                hover_data={
                    'property_code': True,
                    'tenant_count': True,
                    'high_risk_tenants': True
                },
                title='Property Risk Profile (Bubble Size = Monthly Rent)',
                color='high_risk_pct',
                color_continuous_scale='Reds'
            )
            
            # Add risk quadrant lines
            fig_prop_risk.add_hline(y=20, line_dash="dot", line_color="gray", annotation_text="20% High Risk Threshold")
            fig_prop_risk.add_vline(x=6, line_dash="dot", line_color="gray", annotation_text="Score 6.0 Threshold")
            
            fig_prop_risk.update_layout(
                xaxis_title="Average Credit Score",
                yaxis_title="% Rent from High Risk Tenants",
                height=400
            )
            
            st.plotly_chart(fig_prop_risk, use_container_width=True)
        else:
            st.info("No property risk data available")
    
    with col_risk2:
        st.markdown("**🏭 Risk by Industry**")
        
        industry_risk_query = f"""
        SELECT 
            COALESCE(primary_industry, 'Unknown') as industry,
            COUNT(*) as tenant_count,
            AVG(credit_score) as avg_credit_score,
            SUM(CAST(monthly_amount AS DECIMAL(15,2))) as monthly_rent,
            COUNT(CASE WHEN credit_score < 5 THEN 1 END) as high_risk_count
        FROM v_rent_roll_enhanced
        WHERE {property_filter}
        AND charge_code = 'rent'
        AND monthly_amount > 0
        GROUP BY COALESCE(primary_industry, 'Unknown')
        HAVING COUNT(*) >= 3
        ORDER BY monthly_rent DESC
        LIMIT 10
        """
        
        industry_df = dashboard.get_data(industry_risk_query)
        
        if not industry_df.empty:
            # Calculate risk rate by industry
            industry_df['high_risk_rate'] = (industry_df['high_risk_count'] / industry_df['tenant_count'] * 100).fillna(0)
            
            fig_industry = px.bar(
                industry_df,
                x='industry',
                y='high_risk_rate',
                title='High Risk Rate by Industry (%)',
                hover_data=['tenant_count', 'avg_credit_score', 'monthly_rent'],
                color='high_risk_rate',
                color_continuous_scale='Reds'
            )
            
            fig_industry.update_layout(
                xaxis_title="Industry",
                yaxis_title="High Risk Rate (%)",
                xaxis_tickangle=-45,
                height=400
            )
            
            st.plotly_chart(fig_industry, use_container_width=True)
        else:
            st.info("No industry risk data available")
    
    st.markdown("---")
    
    # High-risk tenant details
    st.subheader("🚨 High-Risk Tenant Analysis")
    
    # Risk threshold selector
    col_threshold, col_export = st.columns([3, 1])
    
    with col_threshold:
        risk_threshold = st.slider(
            "Credit Score Threshold (below = high risk)",
            min_value=1.0,
            max_value=8.0,
            value=5.0,
            step=0.5
        )
    
    high_risk_query = f"""
    SELECT 
        property_code,
        property_name,
        tenant_name,
        credit_score,
        credit_risk_category,
        CAST(monthly_amount AS DECIMAL(15,2)) as monthly_rent,
        CAST(leased_area AS DECIMAL(15,2)) as leased_sf,
        annual_revenue,
        primary_industry,
        parent_company_name,
        lease_term_months
    FROM v_rent_roll_enhanced
    WHERE {property_filter}
    AND charge_code = 'rent'
    AND monthly_amount > 0
    AND credit_score < {risk_threshold}
    ORDER BY monthly_rent DESC
    """
    
    high_risk_df = dashboard.get_data(high_risk_query)
    
    if not high_risk_df.empty:
        # Summary of high-risk exposure
        total_high_risk_rent = high_risk_df['monthly_rent'].sum()
        high_risk_tenant_count = len(high_risk_df)
        
        st.markdown(f"""
        **📊 High-Risk Portfolio Exposure (Score < {risk_threshold}):**
        - **{high_risk_tenant_count}** tenants at risk
        - **{dashboard.format_currency(total_high_risk_rent)}** monthly rent at risk
        - **{dashboard.format_currency(total_high_risk_rent * 12)}** annual rent at risk
        """)
        
        # Format for display
        display_df = high_risk_df.copy()
        display_df['Monthly Rent'] = display_df['monthly_rent'].apply(dashboard.format_currency)
        display_df['Annual Rent'] = (display_df['monthly_rent'] * 12).apply(dashboard.format_currency)
        display_df['Leased SF'] = display_df['leased_sf'].apply(lambda x: dashboard.format_area(x) if pd.notna(x) else 'N/A')
        display_df['Credit Score'] = display_df['credit_score'].apply(lambda x: f"{x:.1f}")
        display_df['Annual Revenue'] = display_df['annual_revenue'].apply(lambda x: dashboard.format_currency(x) if pd.notna(x) else 'N/A')
        display_df['Lease Term'] = display_df['lease_term_months'].apply(lambda x: f"{x:.0f} mos" if pd.notna(x) else 'N/A')
        
        table_df = display_df[[\n            'property_code', 'property_name', 'tenant_name', 'Credit Score', 'credit_risk_category',\n            'Monthly Rent', 'Annual Rent', 'Leased SF', 'Lease Term', 'primary_industry', 'parent_company_name'\n        ]].rename(columns={\n            'property_code': 'Property',\n            'property_name': 'Property Name',\n            'tenant_name': 'Tenant',\n            'credit_risk_category': 'Risk Category',\n            'primary_industry': 'Industry',\n            'parent_company_name': 'Parent Company'\n        })
        
        # Color code by risk level
        def color_risk_category(val):\n            if val == 'Very High Risk':\n                return 'background-color: #f8d7da; color: #721c24'\n            elif val == 'High Risk':\n                return 'background-color: #fff3cd; color: #856404'\n            return ''\n        \n        styled_df = table_df.style.applymap(color_risk_category, subset=['Risk Category'])\n        \n        st.dataframe(\n            styled_df,\n            use_container_width=True,\n            height=500\n        )
        
        # Export functionality
        with col_export:
            if st.button("📊 Export High-Risk List"):
                csv = table_df.to_csv(index=False)
                st.download_button(
                    label="💾 Download CSV",
                    data=csv,
                    file_name=f"high_risk_tenants_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime='text/csv'
                )
    else:
        st.success(f"✅ No tenants found with credit scores below {risk_threshold}")
    
    st.markdown("---")
    
    # Risk insights
    st.subheader("💡 Credit Risk Insights")
    
    if not summary_df.empty:
        insights = []
        metrics = summary_df.iloc[0]
        
        # Coverage insights
        coverage_pct = (metrics['tenants_with_scores'] / metrics['total_tenants'] * 100) if metrics['total_tenants'] > 0 else 0
        if coverage_pct >= 80:
            insights.append(f"✅ **Excellent credit coverage** - {coverage_pct:.1f}% of tenants have credit scores")
        elif coverage_pct < 50:
            insights.append(f"⚠️ **Low credit coverage** - Only {coverage_pct:.1f}% of tenants have credit scores")
        
        # Risk concentration insights
        high_risk_pct = ((metrics['high_risk_count'] + metrics['very_high_risk_count']) / metrics['total_tenants'] * 100) if metrics['total_tenants'] > 0 else 0
        if high_risk_pct <= 10:
            insights.append(f"✅ **Low risk portfolio** - Only {high_risk_pct:.1f}% are high/very high risk")
        elif high_risk_pct >= 25:
            insights.append(f"🚨 **High risk concentration** - {high_risk_pct:.1f}% are high/very high risk tenants")
        
        # Average score insights
        if metrics['avg_credit_score']:
            if metrics['avg_credit_score'] >= 7:
                insights.append(f"✅ **Strong tenant quality** - Average credit score of {metrics['avg_credit_score']:.1f}")
            elif metrics['avg_credit_score'] < 5:
                insights.append(f"⚠️ **Credit quality concern** - Average credit score of {metrics['avg_credit_score']:.1f}")
        
        if insights:
            for insight in insights:
                st.markdown(insight)
        else:
            st.markdown("📊 Credit risk metrics are within acceptable ranges")
    else:
        st.info("Unable to generate insights - no credit data available for selected filters")
    
    # Credit score methodology
    with st.expander("ℹ️ Credit Scoring Methodology"):
        st.markdown("""
        **Credit Score Scale (0-10):**
        - **8-10**: Low Risk - Excellent credit profile
        - **6-8**: Medium Risk - Good credit profile
        - **4-6**: High Risk - Fair credit profile, monitor closely
        - **0-4**: Very High Risk - Poor credit profile, requires attention
        
        **Risk Categories:**
        - Based on comprehensive analysis including payment history, financial strength, and industry stability
        - Integrated with parent company relationships for enhanced accuracy
        - Updated regularly based on latest financial data
        """)