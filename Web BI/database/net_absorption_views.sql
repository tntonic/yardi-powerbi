-- =============================================================================
-- NET ABSORPTION VIEWS (FPR METHODOLOGY)
-- Implements DAX v5.1 net absorption calculations
-- Same-store methodology for accurate market analysis
-- =============================================================================

-- =============================================================================
-- 1. SAME-STORE PROPERTY IDENTIFICATION
-- Properties owned throughout the measurement period
-- =============================================================================
CREATE OR REPLACE VIEW v_same_store_properties AS
WITH current_date_ref AS (
    SELECT current_date FROM v_current_date
)
SELECT 
    p.property_hmy,
    p.property_code,
    p.property_name,
    p.acquisition_date,
    p.disposition_date,
    -- Same-store flag for different periods
    CASE 
        WHEN p.acquisition_date <= DATE_SUB(cd.current_date, INTERVAL '3 MONTH')
             AND (p.disposition_date IS NULL OR p.disposition_date > cd.current_date)
        THEN 1 ELSE 0
    END as is_same_store_qtd,
    CASE 
        WHEN p.acquisition_date <= DATE_SUB(cd.current_date, INTERVAL '1 YEAR')
             AND (p.disposition_date IS NULL OR p.disposition_date > cd.current_date)
        THEN 1 ELSE 0
    END as is_same_store_ytd
FROM dim_property p
CROSS JOIN current_date_ref cd;

-- =============================================================================
-- 2. SF COMMENCED (New leases starting in period)
-- From dim_fp_amendmentsunitspropertytenant
-- =============================================================================
CREATE OR REPLACE VIEW v_sf_commenced AS
WITH current_date_ref AS (
    SELECT current_date FROM v_current_date
),
max_sequences AS (
    SELECT 
        property_hmy,
        tenant_hmy,
        MAX(amendment_sequence) as max_sequence
    FROM dim_fp_amendmentsunitspropertytenant
    WHERE amendment_status IN ('Activated', 'Superseded')
    GROUP BY property_hmy, tenant_hmy
)
SELECT 
    a.property_hmy,
    p.property_code,
    p.property_name,
    DATE_TRUNC('month', a.amendment_start_date) as commence_month,
    DATE_TRUNC('quarter', a.amendment_start_date) as commence_quarter,
    EXTRACT(YEAR FROM a.amendment_start_date) as commence_year,
    a.tenant_hmy,
    a.lessee_name,
    a.amendment_type,
    a.leased_area as sf_commenced,
    -- Period indicators
    CASE 
        WHEN a.amendment_start_date >= DATE_SUB(cd.current_date, INTERVAL '1 MONTH')
        THEN a.leased_area ELSE 0
    END as sf_commenced_mtd,
    CASE 
        WHEN a.amendment_start_date >= DATE_TRUNC('quarter', cd.current_date)
        THEN a.leased_area ELSE 0
    END as sf_commenced_qtd,
    CASE 
        WHEN a.amendment_start_date >= DATE_TRUNC('year', cd.current_date)
        THEN a.leased_area ELSE 0
    END as sf_commenced_ytd
FROM dim_fp_amendmentsunitspropertytenant a
INNER JOIN max_sequences ms 
    ON a.property_hmy = ms.property_hmy 
    AND a.tenant_hmy = ms.tenant_hmy
    AND a.amendment_sequence = ms.max_sequence
LEFT JOIN dim_property p ON a.property_hmy = p.property_hmy
CROSS JOIN current_date_ref cd
WHERE 
    a.amendment_status IN ('Activated', 'Superseded')
    AND a.amendment_type IN ('Original Lease', 'New Lease')
    -- Must have associated rent charges for data quality
    AND EXISTS (
        SELECT 1 FROM dim_fp_amendmentchargeschedule cs
        WHERE cs.amendment_hmy = a.amendment_hmy
        AND cs.charge_code IN ('RENT', 'BASE RENT', 'MINIMUM RENT')
    );

-- =============================================================================
-- 3. SF EXPIRED (Lease terminations in period)
-- From dim_fp_terminationtomoveoutreas
-- =============================================================================
CREATE OR REPLACE VIEW v_sf_expired AS
WITH current_date_ref AS (
    SELECT current_date FROM v_current_date
),
max_terminations AS (
    SELECT 
        property_hmy,
        tenant_hmy,
        MAX(amendment_sequence) as max_sequence
    FROM dim_fp_terminationtomoveoutreas
    WHERE amendment_status IN ('Activated', 'Superseded')
    GROUP BY property_hmy, tenant_hmy
)
SELECT 
    t.property_hmy,
    p.property_code,
    p.property_name,
    DATE_TRUNC('month', t.amendment_end_date) as expire_month,
    DATE_TRUNC('quarter', t.amendment_end_date) as expire_quarter,
    EXTRACT(YEAR FROM t.amendment_end_date) as expire_year,
    t.tenant_hmy,
    t.lessee_name,
    t.amendment_type,
    t.leased_area as sf_expired,
    t.move_out_reason,
    -- Period indicators
    CASE 
        WHEN t.amendment_end_date >= DATE_SUB(cd.current_date, INTERVAL '1 MONTH')
             AND t.amendment_end_date <= cd.current_date
        THEN t.leased_area ELSE 0
    END as sf_expired_mtd,
    CASE 
        WHEN t.amendment_end_date >= DATE_TRUNC('quarter', cd.current_date)
             AND t.amendment_end_date <= cd.current_date
        THEN t.leased_area ELSE 0
    END as sf_expired_qtd,
    CASE 
        WHEN t.amendment_end_date >= DATE_TRUNC('year', cd.current_date)
             AND t.amendment_end_date <= cd.current_date
        THEN t.leased_area ELSE 0
    END as sf_expired_ytd
FROM dim_fp_terminationtomoveoutreas t
INNER JOIN max_terminations mt 
    ON t.property_hmy = mt.property_hmy 
    AND t.tenant_hmy = mt.tenant_hmy
    AND t.amendment_sequence = mt.max_sequence
LEFT JOIN dim_property p ON t.property_hmy = p.property_hmy
CROSS JOIN current_date_ref cd
WHERE 
    t.amendment_status IN ('Activated', 'Superseded')
    AND t.amendment_type = 'Termination';

-- =============================================================================
-- 4. NET ABSORPTION BY PROPERTY (Same-Store)
-- SF Commenced - SF Expired
-- =============================================================================
CREATE OR REPLACE VIEW v_net_absorption_by_property AS
WITH property_commenced AS (
    SELECT 
        property_hmy,
        property_code,
        property_name,
        SUM(sf_commenced_mtd) as sf_commenced_mtd,
        SUM(sf_commenced_qtd) as sf_commenced_qtd,
        SUM(sf_commenced_ytd) as sf_commenced_ytd
    FROM v_sf_commenced
    GROUP BY property_hmy, property_code, property_name
),
property_expired AS (
    SELECT 
        property_hmy,
        SUM(sf_expired_mtd) as sf_expired_mtd,
        SUM(sf_expired_qtd) as sf_expired_qtd,
        SUM(sf_expired_ytd) as sf_expired_ytd
    FROM v_sf_expired
    GROUP BY property_hmy
)
SELECT 
    pc.property_code,
    pc.property_name,
    ss.is_same_store_qtd,
    ss.is_same_store_ytd,
    -- SF Commenced
    COALESCE(pc.sf_commenced_mtd, 0) as sf_commenced_mtd,
    COALESCE(pc.sf_commenced_qtd, 0) as sf_commenced_qtd,
    COALESCE(pc.sf_commenced_ytd, 0) as sf_commenced_ytd,
    -- SF Expired
    COALESCE(pe.sf_expired_mtd, 0) as sf_expired_mtd,
    COALESCE(pe.sf_expired_qtd, 0) as sf_expired_qtd,
    COALESCE(pe.sf_expired_ytd, 0) as sf_expired_ytd,
    -- Net Absorption
    COALESCE(pc.sf_commenced_mtd, 0) - COALESCE(pe.sf_expired_mtd, 0) as net_absorption_mtd,
    COALESCE(pc.sf_commenced_qtd, 0) - COALESCE(pe.sf_expired_qtd, 0) as net_absorption_qtd,
    COALESCE(pc.sf_commenced_ytd, 0) - COALESCE(pe.sf_expired_ytd, 0) as net_absorption_ytd,
    -- Same-Store Net Absorption
    CASE 
        WHEN ss.is_same_store_qtd = 1
        THEN COALESCE(pc.sf_commenced_qtd, 0) - COALESCE(pe.sf_expired_qtd, 0)
        ELSE 0
    END as net_absorption_same_store_qtd,
    CASE 
        WHEN ss.is_same_store_ytd = 1
        THEN COALESCE(pc.sf_commenced_ytd, 0) - COALESCE(pe.sf_expired_ytd, 0)
        ELSE 0
    END as net_absorption_same_store_ytd
FROM property_commenced pc
LEFT JOIN property_expired pe ON pc.property_hmy = pe.property_hmy
LEFT JOIN v_same_store_properties ss ON pc.property_hmy = ss.property_hmy;

-- =============================================================================
-- 5. PORTFOLIO NET ABSORPTION (Aggregated)
-- =============================================================================
CREATE OR REPLACE VIEW v_portfolio_net_absorption AS
SELECT 
    -- All Properties
    SUM(sf_commenced_mtd) as total_sf_commenced_mtd,
    SUM(sf_commenced_qtd) as total_sf_commenced_qtd,
    SUM(sf_commenced_ytd) as total_sf_commenced_ytd,
    SUM(sf_expired_mtd) as total_sf_expired_mtd,
    SUM(sf_expired_qtd) as total_sf_expired_qtd,
    SUM(sf_expired_ytd) as total_sf_expired_ytd,
    SUM(net_absorption_mtd) as total_net_absorption_mtd,
    SUM(net_absorption_qtd) as total_net_absorption_qtd,
    SUM(net_absorption_ytd) as total_net_absorption_ytd,
    -- Same-Store Only
    SUM(net_absorption_same_store_qtd) as same_store_net_absorption_qtd,
    SUM(net_absorption_same_store_ytd) as same_store_net_absorption_ytd,
    -- Property counts
    COUNT(DISTINCT property_code) as total_properties,
    SUM(is_same_store_qtd) as same_store_properties_qtd,
    SUM(is_same_store_ytd) as same_store_properties_ytd
FROM v_net_absorption_by_property;

-- =============================================================================
-- 6. FUND 2 ENHANCED PROPERTIES (201 properties)
-- Based on FPR benchmark analysis
-- =============================================================================
CREATE OR REPLACE VIEW v_fund2_enhanced_properties AS
-- This would be populated from the actual Fund 2 property list
-- For now, creating structure for implementation
SELECT 
    property_hmy,
    property_code,
    property_name,
    'Fund 2' as fund_name,
    1 as is_fund2_enhanced
FROM dim_property
WHERE 
    -- Placeholder: actual Fund 2 property filter would go here
    -- This should match the 201 properties identified in FPR analysis
    property_code IN (
        -- Core Fund 2 properties (195)
        -- Plus 6 high-activity properties
        SELECT property_code FROM dim_property WHERE book_id = 2
    );

-- =============================================================================
-- 7. FUND 2 NET ABSORPTION
-- Implements Fund 2 Enhanced Net Absorption measures
-- =============================================================================
CREATE OR REPLACE VIEW v_fund2_net_absorption AS
SELECT 
    'Fund 2' as fund_name,
    -- SF Commenced
    SUM(CASE WHEN f2.is_fund2_enhanced = 1 THEN na.sf_commenced_qtd ELSE 0 END) as fund2_sf_commenced_qtd,
    SUM(CASE WHEN f2.is_fund2_enhanced = 1 THEN na.sf_commenced_ytd ELSE 0 END) as fund2_sf_commenced_ytd,
    -- SF Expired
    SUM(CASE WHEN f2.is_fund2_enhanced = 1 THEN na.sf_expired_qtd ELSE 0 END) as fund2_sf_expired_qtd,
    SUM(CASE WHEN f2.is_fund2_enhanced = 1 THEN na.sf_expired_ytd ELSE 0 END) as fund2_sf_expired_ytd,
    -- Net Absorption
    SUM(CASE WHEN f2.is_fund2_enhanced = 1 THEN na.net_absorption_qtd ELSE 0 END) as fund2_net_absorption_qtd,
    SUM(CASE WHEN f2.is_fund2_enhanced = 1 THEN na.net_absorption_ytd ELSE 0 END) as fund2_net_absorption_ytd,
    -- Same-Store Net Absorption
    SUM(CASE WHEN f2.is_fund2_enhanced = 1 THEN na.net_absorption_same_store_qtd ELSE 0 END) as fund2_net_absorption_ss_qtd,
    SUM(CASE WHEN f2.is_fund2_enhanced = 1 THEN na.net_absorption_same_store_ytd ELSE 0 END) as fund2_net_absorption_ss_ytd,
    -- Property count
    COUNT(DISTINCT CASE WHEN f2.is_fund2_enhanced = 1 THEN na.property_code END) as fund2_property_count
FROM v_net_absorption_by_property na
LEFT JOIN v_fund2_enhanced_properties f2 ON na.property_code = f2.property_code;

-- =============================================================================
-- 8. NET ABSORPTION TREND ANALYSIS
-- Monthly trend for charts
-- =============================================================================
CREATE OR REPLACE VIEW v_net_absorption_trend AS
WITH monthly_commenced AS (
    SELECT 
        DATE_TRUNC('month', amendment_start_date) as activity_month,
        SUM(leased_area) as sf_commenced
    FROM dim_fp_amendmentsunitspropertytenant
    WHERE 
        amendment_status IN ('Activated', 'Superseded')
        AND amendment_type IN ('Original Lease', 'New Lease')
        AND amendment_start_date >= DATE_SUB(CURRENT_DATE, INTERVAL '24 MONTH')
    GROUP BY DATE_TRUNC('month', amendment_start_date)
),
monthly_expired AS (
    SELECT 
        DATE_TRUNC('month', amendment_end_date) as activity_month,
        SUM(leased_area) as sf_expired
    FROM dim_fp_terminationtomoveoutreas
    WHERE 
        amendment_status IN ('Activated', 'Superseded')
        AND amendment_type = 'Termination'
        AND amendment_end_date >= DATE_SUB(CURRENT_DATE, INTERVAL '24 MONTH')
    GROUP BY DATE_TRUNC('month', amendment_end_date)
)
SELECT 
    COALESCE(mc.activity_month, me.activity_month) as month,
    COALESCE(mc.sf_commenced, 0) as sf_commenced,
    COALESCE(me.sf_expired, 0) as sf_expired,
    COALESCE(mc.sf_commenced, 0) - COALESCE(me.sf_expired, 0) as net_absorption
FROM monthly_commenced mc
FULL OUTER JOIN monthly_expired me ON mc.activity_month = me.activity_month
ORDER BY month;

-- =============================================================================
-- 9. TERMINATION REASON ANALYSIS
-- For understanding why tenants are leaving
-- =============================================================================
CREATE OR REPLACE VIEW v_termination_reasons AS
SELECT 
    move_out_reason,
    COUNT(*) as termination_count,
    SUM(leased_area) as total_sf_expired,
    AVG(leased_area) as avg_sf_per_termination,
    -- Percentage of total terminations
    COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () as pct_of_terminations,
    -- Percentage of total SF
    SUM(leased_area) * 100.0 / SUM(SUM(leased_area)) OVER () as pct_of_sf
FROM dim_fp_terminationtomoveoutreas
WHERE 
    amendment_status IN ('Activated', 'Superseded')
    AND amendment_type = 'Termination'
    AND amendment_end_date >= DATE_SUB(CURRENT_DATE, INTERVAL '12 MONTH')
GROUP BY move_out_reason
ORDER BY total_sf_expired DESC;

-- =============================================================================
-- VALIDATION QUERIES
-- =============================================================================
/*
-- Q4 2024 Fund 2 Benchmark Targets:
-- SF Expired (Same-Store): 256,303 SF
-- SF Commenced (Same-Store): 88,482 SF
-- Net Absorption (Same-Store): -167,821 SF

SELECT 
    fund2_sf_commenced_qtd,
    fund2_sf_expired_qtd,
    fund2_net_absorption_qtd,
    fund2_net_absorption_ss_qtd,
    fund2_property_count
FROM v_fund2_net_absorption;
*/