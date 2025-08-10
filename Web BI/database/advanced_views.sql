-- Advanced SQL Views for Yardi Dashboard
-- Replicates complex DAX logic and calculations

-- =============================================================================
-- LEASING ACTIVITY VIEWS
-- =============================================================================

-- Leasing activity aggregations
CREATE OR REPLACE VIEW v_leasing_activity_summary AS
SELECT 
    la.property_id,
    DATE_TRUNC('month', la.lease_start_date) as activity_month,
    p.property_name,
    p.property_code,
    
    -- New Leases
    COUNT(CASE WHEN la.lease_type = 'New' THEN 1 END) as new_leases_count,
    SUM(CASE WHEN la.lease_type = 'New' THEN la.leased_area ELSE 0 END) as new_leases_sf,
    SUM(CASE WHEN la.lease_type = 'New' THEN la.annual_rent ELSE 0 END) as new_leases_rent,
    
    -- Renewals
    COUNT(CASE WHEN la.lease_type = 'Renewal' THEN 1 END) as renewals_count,
    SUM(CASE WHEN la.lease_type = 'Renewal' THEN la.leased_area ELSE 0 END) as renewals_sf,
    SUM(CASE WHEN la.lease_type = 'Renewal' THEN la.annual_rent ELSE 0 END) as renewals_rent,
    
    -- Terminations
    COUNT(CASE WHEN la.lease_type = 'Termination' THEN 1 END) as terminations_count,
    SUM(CASE WHEN la.lease_type = 'Termination' THEN la.leased_area ELSE 0 END) as terminations_sf,
    SUM(CASE WHEN la.lease_type = 'Termination' THEN la.annual_rent ELSE 0 END) as terminations_rent,
    
    -- Net Leasing Activity
    (COUNT(CASE WHEN la.lease_type IN ('New', 'Renewal') THEN 1 END) - 
     COUNT(CASE WHEN la.lease_type = 'Termination' THEN 1 END)) as net_activity_count,
    
    (SUM(CASE WHEN la.lease_type IN ('New', 'Renewal') THEN la.leased_area ELSE 0 END) - 
     SUM(CASE WHEN la.lease_type = 'Termination' THEN la.leased_area ELSE 0 END)) as net_activity_sf

FROM fact_leasingactivity la
LEFT JOIN dim_property p ON la.property_id = p.property_id
GROUP BY la.property_id, DATE_TRUNC('month', la.lease_start_date), p.property_name, p.property_code;

-- =============================================================================
-- RENT ROLL ENHANCEMENT VIEWS
-- =============================================================================

-- Enhanced rent roll with PSF calculations and risk metrics
CREATE OR REPLACE VIEW v_rent_roll_enhanced AS
SELECT 
    rr.*,
    -- PSF Calculations
    CASE 
        WHEN rr.leased_area > 0 AND rr.monthly_amount > 0
        THEN (rr.monthly_amount * 12) / rr.leased_area 
        ELSE 0 
    END as annual_rent_psf,
    
    -- Credit Score Integration
    cs.credit_score,
    cs.annual_revenue,
    cs.primary_industry,
    cs.ownership,
    
    -- Credit Risk Category
    CASE 
        WHEN cs.credit_score >= 8 THEN 'Low Risk'
        WHEN cs.credit_score >= 6 THEN 'Medium Risk'
        WHEN cs.credit_score >= 4 THEN 'High Risk'
        ELSE 'Very High Risk'
    END as credit_risk_category,
    
    -- Parent Company Info
    pm.parent_customer_hmy,
    parent_cs.customer_name as parent_company_name,
    parent_cs.credit_score as parent_credit_score

FROM v_current_rent_roll rr
LEFT JOIN dim_fp_customercreditscorecustomdata cs 
    ON rr.tenant_hmy = cs.hmyperson_customer
LEFT JOIN dim_fp_customertoparentmap pm 
    ON rr.tenant_hmy = pm.customer_hmy
LEFT JOIN dim_fp_customercreditscorecustomdata parent_cs 
    ON pm.parent_customer_hmy = parent_cs.hmyperson_customer;

-- =============================================================================
-- WALT (WEIGHTED AVERAGE LEASE TERM) CALCULATION
-- =============================================================================

CREATE OR REPLACE VIEW v_walt_calculation AS
SELECT 
    property_code,
    property_name,
    -- WALT in months
    CASE 
        WHEN SUM(monthly_amount) > 0
        THEN SUM(lease_term_months * monthly_amount) / SUM(monthly_amount)
        ELSE 0
    END as walt_months,
    
    -- Supporting metrics
    COUNT(*) as total_leases,
    SUM(monthly_amount) as total_monthly_rent,
    AVG(lease_term_months) as avg_lease_term,
    MIN(lease_term_months) as min_lease_term,
    MAX(lease_term_months) as max_lease_term

FROM v_current_rent_roll
WHERE charge_code = 'rent' 
  AND monthly_amount > 0
  AND lease_term_months > 0
GROUP BY property_code, property_name;

-- =============================================================================
-- NOI MARGIN AND FINANCIAL RATIOS
-- =============================================================================

CREATE OR REPLACE VIEW v_financial_ratios AS
SELECT 
    fs.*,
    -- NOI Margin
    CASE 
        WHEN fs.revenue > 0 
        THEN (fs.noi / fs.revenue) * 100 
        ELSE 0 
    END as noi_margin_pct,
    
    -- Operating Expense Ratio
    CASE 
        WHEN fs.revenue > 0 
        THEN (fs.operating_expenses / fs.revenue) * 100 
        ELSE 0 
    END as opex_ratio_pct,
    
    -- Revenue PSF (need to join with occupancy for area)
    om.rentable_area,
    CASE 
        WHEN om.rentable_area > 0 
        THEN fs.revenue / om.rentable_area 
        ELSE 0 
    END as revenue_psf,
    
    -- NOI PSF
    CASE 
        WHEN om.rentable_area > 0 
        THEN fs.noi / om.rentable_area 
        ELSE 0 
    END as noi_psf

FROM v_financial_summary fs
LEFT JOIN (
    SELECT 
        property_id,
        period,
        AVG(rentable_area) as rentable_area
    FROM fact_occupancyrentarea
    GROUP BY property_id, period
) om ON fs.property_id = om.property_id AND fs.period = om.period;

-- =============================================================================
-- PORTFOLIO HEALTH SCORE CALCULATION
-- =============================================================================

CREATE OR REPLACE VIEW v_portfolio_health_score AS
WITH property_metrics AS (
    SELECT 
        p.property_id,
        p.property_name,
        p.property_code,
        
        -- Occupancy Score (0-30 points)
        CASE 
            WHEN om.physical_occupancy_pct >= 95 THEN 30
            WHEN om.physical_occupancy_pct >= 90 THEN 25
            WHEN om.physical_occupancy_pct >= 85 THEN 20
            WHEN om.physical_occupancy_pct >= 80 THEN 15
            ELSE 10
        END as occupancy_score,
        
        -- NOI Margin Score (0-25 points)
        CASE 
            WHEN fr.noi_margin_pct >= 60 THEN 25
            WHEN fr.noi_margin_pct >= 50 THEN 20
            WHEN fr.noi_margin_pct >= 40 THEN 15
            WHEN fr.noi_margin_pct >= 30 THEN 10
            ELSE 5
        END as noi_score,
        
        -- Leasing Activity Score (0-20 points)
        CASE 
            WHEN las.net_activity_sf >= 0 THEN 20
            WHEN las.net_activity_sf >= -5000 THEN 15
            WHEN las.net_activity_sf >= -10000 THEN 10
            ELSE 5
        END as leasing_score,
        
        -- Credit Risk Score (0-15 points)
        CASE 
            WHEN AVG(CASE 
                WHEN rre.credit_score >= 8 THEN 15
                WHEN rre.credit_score >= 6 THEN 12
                WHEN rre.credit_score >= 4 THEN 8
                ELSE 4
            END) IS NOT NULL THEN AVG(CASE 
                WHEN rre.credit_score >= 8 THEN 15
                WHEN rre.credit_score >= 6 THEN 12
                WHEN rre.credit_score >= 4 THEN 8
                ELSE 4
            END)
            ELSE 10  -- Default for properties without credit data
        END as credit_score,
        
        -- WALT Score (0-10 points)
        CASE 
            WHEN w.walt_months >= 60 THEN 10
            WHEN w.walt_months >= 48 THEN 8
            WHEN w.walt_months >= 36 THEN 6
            WHEN w.walt_months >= 24 THEN 4
            ELSE 2
        END as walt_score,
        
        -- Raw metrics for display
        om.physical_occupancy_pct,
        fr.noi_margin_pct,
        las.net_activity_sf,
        w.walt_months

    FROM dim_property p
    LEFT JOIN v_occupancy_metrics om ON p.property_id = om.property_id
    LEFT JOIN v_financial_ratios fr ON p.property_id = fr.property_id
    LEFT JOIN v_leasing_activity_summary las ON p.property_id = las.property_id
    LEFT JOIN v_walt_calculation w ON p.property_code = w.property_code
    LEFT JOIN v_rent_roll_enhanced rre ON p.property_code = rre.property_code
    
    -- Use most recent data
    WHERE om.period = (SELECT MAX(period) FROM fact_occupancyrentarea WHERE property_id = p.property_id)
    OR om.period IS NULL
    
    GROUP BY p.property_id, p.property_name, p.property_code, 
             om.physical_occupancy_pct, fr.noi_margin_pct, 
             las.net_activity_sf, w.walt_months
)

SELECT 
    *,
    -- Total Health Score (0-100)
    COALESCE(occupancy_score, 15) + 
    COALESCE(noi_score, 12) + 
    COALESCE(leasing_score, 10) + 
    COALESCE(credit_score, 10) + 
    COALESCE(walt_score, 5) as total_health_score,
    
    -- Health Category
    CASE 
        WHEN (COALESCE(occupancy_score, 15) + COALESCE(noi_score, 12) + 
              COALESCE(leasing_score, 10) + COALESCE(credit_score, 10) + 
              COALESCE(walt_score, 5)) >= 80 THEN 'Excellent'
        WHEN (COALESCE(occupancy_score, 15) + COALESCE(noi_score, 12) + 
              COALESCE(leasing_score, 10) + COALESCE(credit_score, 10) + 
              COALESCE(walt_score, 5)) >= 65 THEN 'Good'
        WHEN (COALESCE(occupancy_score, 15) + COALESCE(noi_score, 12) + 
              COALESCE(leasing_score, 10) + COALESCE(credit_score, 10) + 
              COALESCE(walt_score, 5)) >= 50 THEN 'Fair'
        ELSE 'Poor'
    END as health_category

FROM property_metrics;

-- =============================================================================
-- TIME SERIES VIEWS FOR TRENDING
-- =============================================================================

-- Monthly NOI trends
CREATE OR REPLACE VIEW v_noi_trends AS
SELECT 
    property_id,
    property_name,
    property_code,
    period,
    noi,
    revenue,
    operating_expenses,
    noi_margin_pct,
    -- Month-over-month change
    LAG(noi) OVER (PARTITION BY property_id ORDER BY period) as prev_month_noi,
    noi - LAG(noi) OVER (PARTITION BY property_id ORDER BY period) as noi_change_mom,
    -- Year-over-year change
    LAG(noi, 12) OVER (PARTITION BY property_id ORDER BY period) as prev_year_noi,
    noi - LAG(noi, 12) OVER (PARTITION BY property_id ORDER BY period) as noi_change_yoy
FROM v_financial_ratios
ORDER BY property_id, period;

-- Occupancy trends
CREATE OR REPLACE VIEW v_occupancy_trends AS
SELECT 
    property_id,
    property_name,
    property_code,
    period,
    physical_occupancy_pct,
    economic_occupancy_pct,
    vacancy_rate_pct,
    -- Month-over-month change
    LAG(physical_occupancy_pct) OVER (PARTITION BY property_id ORDER BY period) as prev_month_occupancy,
    physical_occupancy_pct - LAG(physical_occupancy_pct) OVER (PARTITION BY property_id ORDER BY period) as occupancy_change_mom,
    -- Year-over-year change
    LAG(physical_occupancy_pct, 12) OVER (PARTITION BY property_id ORDER BY period) as prev_year_occupancy,
    physical_occupancy_pct - LAG(physical_occupancy_pct, 12) OVER (PARTITION BY property_id ORDER BY period) as occupancy_change_yoy
FROM v_occupancy_metrics
ORDER BY property_id, period;

-- =============================================================================
-- EXECUTIVE SUMMARY VIEWS
-- =============================================================================

-- Portfolio-level KPIs
CREATE OR REPLACE VIEW v_portfolio_kpis AS
SELECT 
    'Portfolio Total' as metric_scope,
    -- Occupancy Metrics
    AVG(physical_occupancy_pct) as avg_physical_occupancy,
    AVG(economic_occupancy_pct) as avg_economic_occupancy,
    AVG(vacancy_rate_pct) as avg_vacancy_rate,
    
    -- Financial Metrics
    SUM(revenue) as total_revenue,
    SUM(operating_expenses) as total_operating_expenses,
    SUM(noi) as total_noi,
    AVG(noi_margin_pct) as avg_noi_margin,
    
    -- Property Count
    COUNT(DISTINCT property_id) as property_count,
    
    -- Area Metrics
    SUM(rentable_area) as total_rentable_area,
    AVG(revenue_psf) as avg_revenue_psf,
    AVG(noi_psf) as avg_noi_psf,
    
    -- Health Score
    AVG(total_health_score) as avg_health_score

FROM v_financial_ratios fr
JOIN v_portfolio_health_score phs ON fr.property_id = phs.property_id
WHERE fr.period = (SELECT MAX(period) FROM v_financial_ratios);