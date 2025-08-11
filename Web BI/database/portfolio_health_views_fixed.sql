-- =============================================================================
-- PORTFOLIO HEALTH & STRATEGIC KPI VIEWS
-- Implements DAX v5.1 strategic intelligence measures
-- Critical for executive dashboards
-- 
-- FIXES APPLIED:
-- - All column names use quoted format ("property id" instead of "property id")
-- - DuckDB-compatible date functions (DATE_DIFF instead of DATEDIFF)
-- - Added missing v_rent_roll_with_credit view 
-- - Date handling for fact_total using DATE '1900-01-01' + INTERVAL (month - 2) DAY
-- - Fixed all date intervals to use DuckDB syntax
-- =============================================================================

-- =============================================================================
-- MISSING RENT ROLL WITH CREDIT VIEW
-- Required dependency for portfolio health calculations
-- =============================================================================
CREATE OR REPLACE VIEW v_rent_roll_with_credit AS
WITH latest_amendments AS (
    SELECT 
        a.*,
        p."property code",
        p."property name",
        t."lessee name" as tenant_name,
        t."tenant code",
        -- Get latest sequence per property/tenant
        ROW_NUMBER() OVER (
            PARTITION BY a."property hmy", a."tenant hmy" 
            ORDER BY a."amendment sequence" DESC
        ) as rn
    FROM dim_fp_amendmentsunitspropertytenant a
    LEFT JOIN dim_property p ON a."property hmy" = p."property id"
    LEFT JOIN dim_commcustomer t ON a."tenant hmy" = t."tenant hmy"
    WHERE a."amendment status" IN ('Activated', 'Superseded')
),
credit_enhanced AS (
    SELECT 
        la.*,
        cs."credit score",
        cs."customer name" as customer_display_name,
        CASE 
            WHEN cs."credit score" IS NULL THEN 'No Score'
            WHEN cs."credit score" >= 8 THEN 'Low Risk'
            WHEN cs."credit score" >= 6 THEN 'Medium Risk'
            WHEN cs."credit score" >= 4 THEN 'High Risk'
            ELSE 'Very High Risk'
        END as credit_risk_category
    FROM latest_amendments la
    LEFT JOIN dim_fp_customercreditscorecustomdata cs 
        ON la."tenant hmy" = cs."hmyperson customer"
    WHERE la.rn = 1  -- Latest amendment only
)
SELECT 
    *,
    COALESCE("amendment monthly amount", 0) as current_monthly_rent,
    CASE 
        WHEN "amendment area" > 0 
        THEN (COALESCE("amendment monthly amount", 0) * 12) / "amendment area"
        ELSE 0 
    END as current_rent_psf,
    "amendment area" as "leased area"
FROM credit_enhanced;

-- =============================================================================
-- 1. PORTFOLIO HEALTH SCORE (0-100 composite score)
-- Based on multiple performance factors
-- =============================================================================
CREATE OR REPLACE VIEW v_portfolio_health_score AS
WITH occupancy_score AS (
    SELECT 
        AVG(physical_occupancy_pct) as avg_occupancy,
        -- Score based on occupancy (max 25 points)
        CASE 
            WHEN AVG(physical_occupancy_pct) >= 95 THEN 25
            WHEN AVG(physical_occupancy_pct) >= 90 THEN 20
            WHEN AVG(physical_occupancy_pct) >= 85 THEN 15
            WHEN AVG(physical_occupancy_pct) >= 80 THEN 10
            ELSE 5
        END as occupancy_points
    FROM v_occupancy_metrics
),
financial_score AS (
    SELECT 
        SUM(amount * -1) as total_revenue,
        SUM(CASE WHEN "account code" LIKE '5%' THEN amount ELSE 0 END) as total_expenses,
        -- Calculate NOI margin
        CASE 
            WHEN SUM(amount * -1) > 0
            THEN ((SUM(amount * -1) - SUM(CASE WHEN "account code" LIKE '5%' THEN amount ELSE 0 END)) / SUM(amount * -1)) * 100
            ELSE 0
        END as noi_margin,
        -- Score based on NOI margin (max 25 points)
        CASE 
            WHEN ((SUM(amount * -1) - SUM(CASE WHEN "account code" LIKE '5%' THEN amount ELSE 0 END)) / NULLIF(SUM(amount * -1), 0)) >= 0.70 THEN 25
            WHEN ((SUM(amount * -1) - SUM(CASE WHEN "account code" LIKE '5%' THEN amount ELSE 0 END)) / NULLIF(SUM(amount * -1), 0)) >= 0.65 THEN 20
            WHEN ((SUM(amount * -1) - SUM(CASE WHEN "account code" LIKE '5%' THEN amount ELSE 0 END)) / NULLIF(SUM(amount * -1), 0)) >= 0.60 THEN 15
            WHEN ((SUM(amount * -1) - SUM(CASE WHEN "account code" LIKE '5%' THEN amount ELSE 0 END)) / NULLIF(SUM(amount * -1), 0)) >= 0.55 THEN 10
            ELSE 5
        END as financial_points
    FROM fact_total
    WHERE ("account code" LIKE '4%' OR "account code" LIKE '5%')
      -- Example of date handling from month column: DATE '1900-01-01' + INTERVAL (month - 2) DAY
      AND (DATE '1900-01-01' + INTERVAL (month - 2) DAY) >= (CURRENT_DATE - INTERVAL '12 MONTH')
),
"credit score" AS (
    SELECT 
        AVG(CASE WHEN "credit score" IS NOT NULL THEN "credit score" ELSE 5 END) as avg_credit_score,
        COUNT(CASE WHEN "credit score" >= 7 THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0) as pct_low_risk,
        -- Score based on credit risk (max 25 points)
        CASE 
            WHEN AVG(CASE WHEN "credit score" IS NOT NULL THEN "credit score" ELSE 5 END) >= 7 THEN 25
            WHEN AVG(CASE WHEN "credit score" IS NOT NULL THEN "credit score" ELSE 5 END) >= 6 THEN 20
            WHEN AVG(CASE WHEN "credit score" IS NOT NULL THEN "credit score" ELSE 5 END) >= 5 THEN 15
            WHEN AVG(CASE WHEN "credit score" IS NOT NULL THEN "credit score" ELSE 5 END) >= 4 THEN 10
            ELSE 5
        END as credit_points
    FROM v_rent_roll_with_credit
    WHERE current_monthly_rent > 0
),
leasing_score AS (
    SELECT 
        COUNT(CASE WHEN "lease type" = 'New' THEN 1 END) as new_leases,
        COUNT(CASE WHEN "lease type" = 'Renewal' THEN 1 END) as renewals,
        COUNT(CASE WHEN "lease type" = 'Termination' THEN 1 END) as terminations,
        -- Calculate retention rate
        CASE 
            WHEN (COUNT(CASE WHEN "lease type" = 'Renewal' THEN 1 END) + COUNT(CASE WHEN "lease type" = 'Termination' THEN 1 END)) > 0
            THEN COUNT(CASE WHEN "lease type" = 'Renewal' THEN 1 END) * 100.0 / 
                 (COUNT(CASE WHEN "lease type" = 'Renewal' THEN 1 END) + COUNT(CASE WHEN "lease type" = 'Termination' THEN 1 END))
            ELSE 0
        END as retention_rate,
        -- Score based on retention (max 25 points)
        CASE 
            WHEN COUNT(CASE WHEN "lease type" = 'Renewal' THEN 1 END) * 100.0 / 
                 NULLIF(COUNT(CASE WHEN "lease type" = 'Renewal' THEN 1 END) + COUNT(CASE WHEN "lease type" = 'Termination' THEN 1 END), 0) >= 80 THEN 25
            WHEN COUNT(CASE WHEN "lease type" = 'Renewal' THEN 1 END) * 100.0 / 
                 NULLIF(COUNT(CASE WHEN "lease type" = 'Renewal' THEN 1 END) + COUNT(CASE WHEN "lease type" = 'Termination' THEN 1 END), 0) >= 70 THEN 20
            WHEN COUNT(CASE WHEN "lease type" = 'Renewal' THEN 1 END) * 100.0 / 
                 NULLIF(COUNT(CASE WHEN "lease type" = 'Renewal' THEN 1 END) + COUNT(CASE WHEN "lease type" = 'Termination' THEN 1 END), 0) >= 60 THEN 15
            WHEN COUNT(CASE WHEN "lease type" = 'Renewal' THEN 1 END) * 100.0 / 
                 NULLIF(COUNT(CASE WHEN "lease type" = 'Renewal' THEN 1 END) + COUNT(CASE WHEN "lease type" = 'Termination' THEN 1 END), 0) >= 50 THEN 10
            ELSE 5
        END as leasing_points
    FROM fact_leasingactivity
    WHERE "lease start date" >= (CURRENT_DATE - INTERVAL '12 MONTH')
)
SELECT 
    os.occupancy_points + fs.financial_points + cs.credit_points + ls.leasing_points as portfolio_health_score,
    -- Component scores
    os.occupancy_points,
    fs.financial_points,
    cs.credit_points,
    ls.leasing_points,
    -- Supporting metrics
    os.avg_occupancy,
    fs.noi_margin,
    cs.avg_credit_score,
    ls.retention_rate,
    -- Health category
    CASE 
        WHEN os.occupancy_points + fs.financial_points + cs.credit_points + ls.leasing_points >= 80 THEN 'Excellent'
        WHEN os.occupancy_points + fs.financial_points + cs.credit_points + ls.leasing_points >= 65 THEN 'Good'
        WHEN os.occupancy_points + fs.financial_points + cs.credit_points + ls.leasing_points >= 50 THEN 'Fair'
        ELSE 'Needs Attention'
    END as health_category
FROM occupancy_score os, financial_score fs, "credit score" cs, leasing_score ls;

-- =============================================================================
-- 2. INVESTMENT TIMING SCORE (0-100)
-- Market cycle positioning indicator
-- =============================================================================
CREATE OR REPLACE VIEW v_investment_timing_score AS
WITH market_metrics AS (
    -- Calculate year-over-year metrics
    SELECT 
        -- Current metrics
        AVG(CASE WHEN "period date" >= (CURRENT_DATE - INTERVAL '1 MONTH') 
                 THEN "occupancy percent" END) as current_occupancy,
        AVG(CASE WHEN "period date" >= (CURRENT_DATE - INTERVAL '13 MONTH')
                  AND "period date" < (CURRENT_DATE - INTERVAL '12 MONTH')
                 THEN "occupancy percent" END) as prior_year_occupancy,
        -- Calculate growth rates
        (AVG(CASE WHEN "period date" >= (CURRENT_DATE - INTERVAL '1 MONTH') 
                  THEN "occupancy percent" END) - 
         AVG(CASE WHEN "period date" >= (CURRENT_DATE - INTERVAL '13 MONTH')
                   AND "period date" < (CURRENT_DATE - INTERVAL '12 MONTH')
                  THEN "occupancy percent" END)) as occupancy_change
    FROM fact_occupancyrentarea
),
rent_growth AS (
    SELECT 
        AVG(current_rent_psf) as current_avg_rent,
        -- Calculate rent growth (simplified - would need historical data)
        5.0 as rent_growth_rate -- Placeholder
    FROM v_current_rent_roll_enhanced
    WHERE current_monthly_rent > 0
),
absorption_metrics AS (
    SELECT 
        total_net_absorption_ytd,
        same_store_net_absorption_ytd,
        CASE 
            WHEN same_store_net_absorption_ytd > 0 THEN 1
            ELSE -1
        END as absorption_direction
    FROM v_portfolio_net_absorption
)
SELECT 
    -- Calculate investment timing score
    CASE 
        -- Strong Buy (80-100): High occupancy growth, positive absorption, moderate rent growth
        WHEN mm.occupancy_change > 2 AND am.absorption_direction = 1 AND rg.rent_growth_rate < 10 THEN 85
        -- Buy (60-79): Stable occupancy, positive absorption
        WHEN mm.occupancy_change >= 0 AND am.absorption_direction = 1 THEN 70
        -- Hold (40-59): Flat metrics
        WHEN ABS(mm.occupancy_change) < 1 THEN 50
        -- Sell (20-39): Declining occupancy, negative absorption
        WHEN mm.occupancy_change < -1 AND am.absorption_direction = -1 THEN 30
        -- Strong Sell (0-19): Significant decline
        WHEN mm.occupancy_change < -3 AND am.absorption_direction = -1 THEN 15
        ELSE 50
    END as investment_timing_score,
    -- Supporting metrics
    mm.current_occupancy,
    mm.occupancy_change,
    rg.rent_growth_rate,
    am.same_store_net_absorption_ytd,
    -- Investment recommendation
    CASE 
        WHEN mm.occupancy_change > 2 AND am.absorption_direction = 1 THEN 'Strong Buy'
        WHEN mm.occupancy_change >= 0 AND am.absorption_direction = 1 THEN 'Buy'
        WHEN ABS(mm.occupancy_change) < 1 THEN 'Hold'
        WHEN mm.occupancy_change < -1 AND am.absorption_direction = -1 THEN 'Sell'
        WHEN mm.occupancy_change < -3 AND am.absorption_direction = -1 THEN 'Strong Sell'
        ELSE 'Hold'
    END as investment_recommendation
FROM market_metrics mm, rent_growth rg, absorption_metrics am;

-- =============================================================================
-- 3. MARKET RISK SCORE (0-100, lower is better)
-- Measures portfolio exposure to market risks
-- =============================================================================
CREATE OR REPLACE VIEW v_market_risk_score AS
WITH concentration_risk AS (
    -- Tenant concentration risk
    SELECT 
        MAX(current_monthly_rent) * 100.0 / NULLIF(SUM(current_monthly_rent), 0) as top_tenant_pct,
        -- Top 5 tenants concentration
        (SELECT SUM(rent_pct) FROM (
            SELECT current_monthly_rent * 100.0 / NULLIF(SUM(current_monthly_rent) OVER (), 0) as rent_pct
            FROM v_current_rent_roll_enhanced
            WHERE current_monthly_rent > 0
            ORDER BY current_monthly_rent DESC
            LIMIT 5
        ) t) as top5_tenant_pct
    FROM v_current_rent_roll_enhanced
    WHERE current_monthly_rent > 0
),
lease_expiry_risk AS (
    -- Lease expiration concentration
    SELECT 
        SUM(CASE WHEN expiration_bucket IN ('0-3 Months', '4-6 Months') 
                 THEN current_monthly_rent ELSE 0 END) * 100.0 / 
        NULLIF(SUM(current_monthly_rent), 0) as near_term_expiry_pct,
        COUNT(CASE WHEN expiration_bucket = 'Month-to-Month' THEN 1 END) * 100.0 / 
        NULLIF(COUNT(*), 0) as mtm_lease_pct
    FROM v_lease_expirations
),
credit_risk AS (
    -- Credit quality risk
    SELECT 
        COUNT(CASE WHEN credit_risk_category IN ('High Risk', 'Very High Risk') THEN 1 END) * 100.0 / 
        NULLIF(COUNT(*), 0) as high_risk_tenant_pct,
        SUM(CASE WHEN credit_risk_category IN ('High Risk', 'Very High Risk') 
                 THEN current_monthly_rent ELSE 0 END) * 100.0 / 
        NULLIF(SUM(current_monthly_rent), 0) as revenue_at_risk_pct
    FROM v_rent_roll_with_credit
    WHERE current_monthly_rent > 0
),
market_volatility AS (
    -- Market volatility indicators
    SELECT 
        STDDEV("occupancy percent") as occupancy_volatility,
        -- Normalize to 0-25 scale
        LEAST(STDDEV("occupancy percent") * 2, 25) as volatility_points
    FROM fact_occupancyrentarea
    WHERE "period date" >= (CURRENT_DATE - INTERVAL '12 MONTH')
)
SELECT 
    -- Calculate market risk score (0-100, lower is better)
    LEAST(
        -- Concentration risk (0-25 points)
        CASE 
            WHEN cr.top5_tenant_pct > 50 THEN 25
            WHEN cr.top5_tenant_pct > 40 THEN 20
            WHEN cr.top5_tenant_pct > 30 THEN 15
            WHEN cr.top5_tenant_pct > 20 THEN 10
            ELSE 5
        END +
        -- Lease expiry risk (0-25 points)
        CASE 
            WHEN ler.near_term_expiry_pct > 30 THEN 25
            WHEN ler.near_term_expiry_pct > 20 THEN 20
            WHEN ler.near_term_expiry_pct > 15 THEN 15
            WHEN ler.near_term_expiry_pct > 10 THEN 10
            ELSE 5
        END +
        -- Credit risk (0-25 points)
        CASE 
            WHEN crd.revenue_at_risk_pct > 20 THEN 25
            WHEN crd.revenue_at_risk_pct > 15 THEN 20
            WHEN crd.revenue_at_risk_pct > 10 THEN 15
            WHEN crd.revenue_at_risk_pct > 5 THEN 10
            ELSE 5
        END +
        -- Market volatility (0-25 points)
        mv.volatility_points,
        100
    ) as market_risk_score,
    -- Component scores
    cr.top5_tenant_pct,
    ler.near_term_expiry_pct,
    crd.revenue_at_risk_pct,
    mv.occupancy_volatility,
    -- Risk category
    CASE 
        WHEN (CASE WHEN cr.top5_tenant_pct > 50 THEN 25 ELSE 5 END +
              CASE WHEN ler.near_term_expiry_pct > 30 THEN 25 ELSE 5 END +
              CASE WHEN crd.revenue_at_risk_pct > 20 THEN 25 ELSE 5 END +
              mv.volatility_points) <= 30 THEN 'Low Risk'
        WHEN (CASE WHEN cr.top5_tenant_pct > 50 THEN 25 ELSE 5 END +
              CASE WHEN ler.near_term_expiry_pct > 30 THEN 25 ELSE 5 END +
              CASE WHEN crd.revenue_at_risk_pct > 20 THEN 25 ELSE 5 END +
              mv.volatility_points) <= 50 THEN 'Medium Risk'
        WHEN (CASE WHEN cr.top5_tenant_pct > 50 THEN 25 ELSE 5 END +
              CASE WHEN ler.near_term_expiry_pct > 30 THEN 25 ELSE 5 END +
              CASE WHEN crd.revenue_at_risk_pct > 20 THEN 25 ELSE 5 END +
              mv.volatility_points) <= 70 THEN 'High Risk'
        ELSE 'Very High Risk'
    END as risk_category
FROM concentration_risk cr, lease_expiry_risk ler, credit_risk crd, market_volatility mv;

-- =============================================================================
-- 4. OVERALL SYSTEM HEALTH (Data quality and system performance)
-- =============================================================================
CREATE OR REPLACE VIEW v_overall_system_health AS
WITH data_completeness AS (
    SELECT 
        -- Check for missing critical data
        COUNT(CASE WHEN current_monthly_rent IS NULL OR current_monthly_rent = 0 THEN 1 END) * 100.0 / 
        NULLIF(COUNT(*), 0) as pct_missing_rent,
        COUNT(CASE WHEN "leased area" IS NULL OR "leased area" = 0 THEN 1 END) * 100.0 / 
        NULLIF(COUNT(*), 0) as pct_missing_area
    FROM v_current_rent_roll_enhanced
),
data_freshness AS (
    SELECT 
        MAX("last closed period") as last_update,
        DATE_DIFF('day', MAX("last closed period"), CURRENT_DATE) as days_since_update
    FROM dim_lastclosedperiod
),
orphaned_records AS (
    SELECT 
        COUNT(*) as orphaned_count
    FROM fact_total f
    LEFT JOIN dim_property p ON f."property id" = p."property id"
    WHERE p."property id" IS NULL
)
SELECT 
    -- Calculate overall system health (0-100)
    GREATEST(
        100 - 
        -- Deduct for missing data
        (dc.pct_missing_rent * 2) -
        (dc.pct_missing_area * 2) -
        -- Deduct for stale data
        CASE 
            WHEN df.days_since_update > 30 THEN 20
            WHEN df.days_since_update > 14 THEN 10
            WHEN df.days_since_update > 7 THEN 5
            ELSE 0
        END -
        -- Deduct for orphaned records
        CASE 
            WHEN o.orphaned_count > 100 THEN 20
            WHEN o.orphaned_count > 50 THEN 10
            WHEN o.orphaned_count > 10 THEN 5
            ELSE 0
        END,
        0
    ) as overall_system_health,
    -- Supporting metrics
    dc.pct_missing_rent,
    dc.pct_missing_area,
    df.last_update,
    df.days_since_update,
    o.orphaned_count,
    -- Health status
    CASE 
        WHEN GREATEST(100 - (dc.pct_missing_rent * 2) - (dc.pct_missing_area * 2) - 
             CASE WHEN df.days_since_update > 30 THEN 20 ELSE 0 END -
             CASE WHEN o.orphaned_count > 100 THEN 20 ELSE 0 END, 0) >= 90 THEN 'Excellent'
        WHEN GREATEST(100 - (dc.pct_missing_rent * 2) - (dc.pct_missing_area * 2) - 
             CASE WHEN df.days_since_update > 30 THEN 20 ELSE 0 END -
             CASE WHEN o.orphaned_count > 100 THEN 20 ELSE 0 END, 0) >= 75 THEN 'Good'
        WHEN GREATEST(100 - (dc.pct_missing_rent * 2) - (dc.pct_missing_area * 2) - 
             CASE WHEN df.days_since_update > 30 THEN 20 ELSE 0 END -
             CASE WHEN o.orphaned_count > 100 THEN 20 ELSE 0 END, 0) >= 60 THEN 'Fair'
        ELSE 'Needs Attention'
    END as health_status
FROM data_completeness dc, data_freshness df, orphaned_records o;

-- =============================================================================
-- 5. DASHBOARD READINESS SCORE
-- Indicates if data is ready for dashboard consumption
-- =============================================================================
CREATE OR REPLACE VIEW v_dashboard_readiness_score AS
WITH critical_tables AS (
    SELECT 
        (SELECT COUNT(*) FROM dim_property) as property_count,
        (SELECT COUNT(*) FROM dim_commcustomer) as customer_count,
        (SELECT COUNT(*) FROM dim_fp_amendmentsunitspropertytenant) as amendment_count,
        (SELECT COUNT(*) FROM fact_total) as transaction_count,
        (SELECT COUNT(*) FROM fact_occupancyrentarea) as occupancy_count
),
view_checks AS (
    SELECT 
        (SELECT COUNT(*) FROM v_current_rent_roll_enhanced) as rent_roll_count,
        (SELECT COUNT(*) FROM v_occupancy_metrics) as occupancy_metrics_count,
        (SELECT portfolio_walt_months FROM v_portfolio_walt) as walt_check
)
SELECT 
    -- Calculate readiness score (0-100)
    CASE 
        WHEN ct.property_count > 0 
         AND ct.customer_count > 0
         AND ct.amendment_count > 0
         AND ct.transaction_count > 0
         AND ct.occupancy_count > 0
         AND vc.rent_roll_count > 0
         AND vc.occupancy_metrics_count > 0
        THEN 100
        WHEN ct.property_count > 0 
         AND ct.customer_count > 0
         AND ct.amendment_count > 0
        THEN 75
        WHEN ct.property_count > 0
        THEN 50
        ELSE 0
    END as dashboard_readiness_score,
    -- Table counts
    ct.property_count,
    ct.customer_count,
    ct.amendment_count,
    ct.transaction_count,
    ct.occupancy_count,
    -- View status
    vc.rent_roll_count,
    vc.occupancy_metrics_count,
    -- Readiness status
    CASE 
        WHEN ct.property_count > 0 
         AND ct.customer_count > 0
         AND ct.amendment_count > 0
         AND ct.transaction_count > 0
         AND ct.occupancy_count > 0
         AND vc.rent_roll_count > 0
        THEN 'Ready'
        WHEN ct.property_count > 0 
         AND ct.customer_count > 0
         AND ct.amendment_count > 0
        THEN 'Partially Ready'
        ELSE 'Not Ready'
    END as readiness_status
FROM critical_tables ct, view_checks vc;

-- =============================================================================
-- 6. MARKET POSITION SCORE
-- Competitive positioning indicator
-- =============================================================================
CREATE OR REPLACE VIEW v_market_position_score AS
WITH portfolio_metrics AS (
    SELECT 
        AVG(physical_occupancy_pct) as portfolio_occupancy,
        AVG(current_rent_psf) as portfolio_avg_rent
    FROM v_occupancy_metrics om
    LEFT JOIN v_current_rent_roll_enhanced rr ON om."property code" = rr."property code"
    WHERE rr.current_monthly_rent > 0
),
market_benchmark AS (
    -- In production, this would come from market data
    -- Using placeholder values for market averages
    SELECT 
        90.0 as market_avg_occupancy,
        25.0 as market_avg_rent
)
SELECT 
    -- Calculate market position score (0-100)
    CASE 
        -- Above market in both metrics
        WHEN pm.portfolio_occupancy > mb.market_avg_occupancy 
         AND pm.portfolio_avg_rent > mb.market_avg_rent THEN 85
        -- Above market in occupancy
        WHEN pm.portfolio_occupancy > mb.market_avg_occupancy THEN 70
        -- Above market in rent
        WHEN pm.portfolio_avg_rent > mb.market_avg_rent THEN 65
        -- At market
        WHEN ABS(pm.portfolio_occupancy - mb.market_avg_occupancy) < 2
         AND ABS(pm.portfolio_avg_rent - mb.market_avg_rent) < 2 THEN 50
        -- Below market
        ELSE 35
    END as market_position_score,
    -- Metrics
    pm.portfolio_occupancy,
    mb.market_avg_occupancy,
    pm.portfolio_occupancy - mb.market_avg_occupancy as occupancy_vs_market,
    pm.portfolio_avg_rent,
    mb.market_avg_rent,
    pm.portfolio_avg_rent - mb.market_avg_rent as rent_vs_market,
    -- Position category
    CASE 
        WHEN pm.portfolio_occupancy > mb.market_avg_occupancy 
         AND pm.portfolio_avg_rent > mb.market_avg_rent THEN 'Market Leader'
        WHEN pm.portfolio_occupancy > mb.market_avg_occupancy 
          OR pm.portfolio_avg_rent > mb.market_avg_rent THEN 'Above Market'
        WHEN ABS(pm.portfolio_occupancy - mb.market_avg_occupancy) < 2
         AND ABS(pm.portfolio_avg_rent - mb.market_avg_rent) < 2 THEN 'At Market'
        ELSE 'Below Market'
    END as market_position
FROM portfolio_metrics pm, market_benchmark mb;

-- =============================================================================
-- VALIDATION QUERIES
-- =============================================================================
/*
-- Check all strategic KPIs
SELECT 
    (SELECT portfolio_health_score FROM v_portfolio_health_score) as portfolio_health,
    (SELECT investment_timing_score FROM v_investment_timing_score) as investment_timing,
    (SELECT market_risk_score FROM v_market_risk_score) as market_risk,
    (SELECT overall_system_health FROM v_overall_system_health) as system_health,
    (SELECT dashboard_readiness_score FROM v_dashboard_readiness_score) as dashboard_readiness,
    (SELECT market_position_score FROM v_market_position_score) as market_position;
*/