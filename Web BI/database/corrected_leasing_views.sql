-- =============================================================================
-- CORRECTED LEASING ACTIVITY VIEWS
-- Fixed column names to match actual database structure
-- =============================================================================

-- =============================================================================
-- 1. LEASING ACTIVITY SUMMARY
-- =============================================================================
CREATE OR REPLACE VIEW v_leasing_activity_summary AS
SELECT 
    la."property id",
    DATE_TRUNC('month', CAST(la."lease start date" AS DATE)) as activity_month,
    p."property name",
    p."property code",
    
    -- New Leases
    COUNT(CASE WHEN la."lease type" = 'New' THEN 1 END) as new_leases_count,
    SUM(CASE WHEN la."lease type" = 'New' THEN la."leased area" ELSE 0 END) as new_leases_sf,
    SUM(CASE WHEN la."lease type" = 'New' THEN la."annual rent" ELSE 0 END) as new_leases_rent,
    
    -- Renewals
    COUNT(CASE WHEN la."lease type" = 'Renewal' THEN 1 END) as renewals_count,
    SUM(CASE WHEN la."lease type" = 'Renewal' THEN la."leased area" ELSE 0 END) as renewals_sf,
    SUM(CASE WHEN la."lease type" = 'Renewal' THEN la."annual rent" ELSE 0 END) as renewals_rent,
    
    -- Terminations
    COUNT(CASE WHEN la."lease type" = 'Termination' THEN 1 END) as terminations_count,
    SUM(CASE WHEN la."lease type" = 'Termination' THEN la."leased area" ELSE 0 END) as terminations_sf,
    SUM(CASE WHEN la."lease type" = 'Termination' THEN la."annual rent" ELSE 0 END) as terminations_rent,
    
    -- Net Leasing Activity
    (COUNT(CASE WHEN la."lease type" IN ('New', 'Renewal') THEN 1 END) - 
     COUNT(CASE WHEN la."lease type" = 'Termination' THEN 1 END)) as net_activity_count,
    
    (SUM(CASE WHEN la."lease type" IN ('New', 'Renewal') THEN la."leased area" ELSE 0 END) - 
     SUM(CASE WHEN la."lease type" = 'Termination' THEN la."leased area" ELSE 0 END)) as net_activity_sf,
     
    -- Calculate retention rate (avoid division by zero)
    CASE 
        WHEN (COUNT(CASE WHEN la."lease type" = 'Renewal' THEN 1 END) + 
              COUNT(CASE WHEN la."lease type" = 'Termination' THEN 1 END)) > 0
        THEN COUNT(CASE WHEN la."lease type" = 'Renewal' THEN 1 END) * 100.0 / 
             (COUNT(CASE WHEN la."lease type" = 'Renewal' THEN 1 END) + 
              COUNT(CASE WHEN la."lease type" = 'Termination' THEN 1 END))
        ELSE 0
    END as retention_rate

FROM fact_leasingactivity la
LEFT JOIN dim_property p ON la."property id" = p."property id"
GROUP BY 
    la."property id", 
    DATE_TRUNC('month', CAST(la."lease start date" AS DATE)), 
    p."property name", 
    p."property code";

-- =============================================================================
-- 2. LEASING ACTIVITY BY PROPERTY (Aggregated)
-- =============================================================================
CREATE OR REPLACE VIEW v_leasing_activity_by_property AS
SELECT 
    p."property code",
    p."property name",
    
    -- Total counts
    COUNT(CASE WHEN la."lease type" = 'New' THEN 1 END) as total_new_leases,
    COUNT(CASE WHEN la."lease type" = 'Renewal' THEN 1 END) as total_renewals,
    COUNT(CASE WHEN la."lease type" = 'Termination' THEN 1 END) as total_terminations,
    
    -- Total SF
    SUM(CASE WHEN la."lease type" = 'New' THEN la."leased area" ELSE 0 END) as total_new_sf,
    SUM(CASE WHEN la."lease type" = 'Renewal' THEN la."leased area" ELSE 0 END) as total_renewal_sf,
    SUM(CASE WHEN la."lease type" = 'Termination' THEN la."leased area" ELSE 0 END) as total_termination_sf,
    
    -- Net activity
    (SUM(CASE WHEN la."lease type" IN ('New', 'Renewal') THEN la."leased area" ELSE 0 END) - 
     SUM(CASE WHEN la."lease type" = 'Termination' THEN la."leased area" ELSE 0 END)) as net_activity_sf,
    
    -- Retention rate
    CASE 
        WHEN (COUNT(CASE WHEN la."lease type" = 'Renewal' THEN 1 END) + 
              COUNT(CASE WHEN la."lease type" = 'Termination' THEN 1 END)) > 0
        THEN COUNT(CASE WHEN la."lease type" = 'Renewal' THEN 1 END) * 100.0 / 
             (COUNT(CASE WHEN la."lease type" = 'Renewal' THEN 1 END) + 
              COUNT(CASE WHEN la."lease type" = 'Termination' THEN 1 END))
        ELSE 0
    END as retention_rate_pct,
    
    -- Average deal size
    AVG(CASE WHEN la."lease type" IN ('New', 'Renewal') THEN la."leased area" END) as avg_deal_size_sf,
    
    -- Pipeline metrics
    COUNT(CASE WHEN la."pipeline stage" = 'Negotiation' THEN 1 END) as deals_in_negotiation,
    COUNT(CASE WHEN la."pipeline stage" = 'Executed' THEN 1 END) as deals_executed

FROM fact_leasingactivity la
LEFT JOIN dim_property p ON la."property id" = p."property id"
GROUP BY p."property code", p."property name";