-- =============================================================================
-- AMENDMENT-BASED LOGIC VIEWS
-- Implements DAX v5.1 amendment logic for 95-99% accuracy
-- Critical for rent roll calculations
-- =============================================================================

-- =============================================================================
-- 1. CURRENT DATE REFERENCE (v5.1 pattern)
-- =============================================================================
CREATE OR REPLACE VIEW v_current_date AS
SELECT 
    MAX(last_closed_period) as current_date,
    MAX(last_closed_period) as reporting_date
FROM dim_lastclosedperiod;

-- =============================================================================
-- 2. BASE ACTIVE AMENDMENTS (Foundation for all amendment calculations)
-- Implements _BaseActiveAmendments DAX helper measure
-- =============================================================================
CREATE OR REPLACE VIEW v_base_active_amendments AS
WITH current_date_ref AS (
    SELECT current_date FROM v_current_date
)
SELECT 
    a.*,
    p.property_name,
    p.property_code,
    t.lessee_name as tenant_name,
    t.tenant_code,
    -- Calculate lease term in months
    CASE 
        WHEN a.amendment_end_date IS NOT NULL 
        THEN DATEDIFF('month', a.amendment_start_date, a.amendment_end_date)
        ELSE DATEDIFF('month', a.amendment_start_date, cd.current_date)
    END as lease_term_months,
    -- Month-to-month flag
    CASE 
        WHEN a.amendment_end_date IS NULL THEN 1
        WHEN DATEDIFF('month', a.amendment_start_date, a.amendment_end_date) <= 1 THEN 1
        ELSE 0
    END as is_month_to_month
FROM dim_fp_amendmentsunitspropertytenant a
CROSS JOIN current_date_ref cd
LEFT JOIN dim_property p ON a.property_hmy = p.property_hmy
LEFT JOIN dim_commcustomer t ON a.tenant_hmy = t.tenant_hmy
WHERE 
    -- Critical status filtering for accuracy
    a.amendment_status IN ('Activated', 'Superseded')
    -- Exclude certain amendment types
    AND a.amendment_type NOT IN ('Termination', 'Proposal in DM', 'Modification')
    -- Date filtering
    AND a.amendment_start_date <= cd.current_date
    AND (a.amendment_end_date >= cd.current_date OR a.amendment_end_date IS NULL);

-- =============================================================================
-- 3. LATEST AMENDMENTS (Latest sequence per property/tenant)
-- Critical for preventing double-counting
-- =============================================================================
CREATE OR REPLACE VIEW v_latest_amendments AS
WITH current_date_ref AS (
    SELECT current_date FROM v_current_date
),
max_sequences AS (
    SELECT 
        property_hmy,
        tenant_hmy,
        MAX(amendment_sequence) as max_sequence
    FROM v_base_active_amendments
    GROUP BY property_hmy, tenant_hmy
)
SELECT 
    a.*
FROM v_base_active_amendments a
INNER JOIN max_sequences ms 
    ON a.property_hmy = ms.property_hmy 
    AND a.tenant_hmy = ms.tenant_hmy
    AND a.amendment_sequence = ms.max_sequence;

-- =============================================================================
-- 4. LATEST AMENDMENTS WITH CHARGES
-- Implements _LatestAmendmentsWithCharges DAX helper
-- =============================================================================
CREATE OR REPLACE VIEW v_latest_amendments_with_charges AS
SELECT 
    la.*,
    cs.charge_code,
    cs.charge_amount,
    cs.charge_frequency,
    -- Calculate monthly amount based on frequency
    CASE cs.charge_frequency
        WHEN 'Monthly' THEN cs.charge_amount
        WHEN 'Annually' THEN cs.charge_amount / 12
        WHEN 'Quarterly' THEN cs.charge_amount / 3
        WHEN 'Semi-Annually' THEN cs.charge_amount / 6
        ELSE cs.charge_amount
    END as monthly_charge_amount
FROM v_latest_amendments la
LEFT JOIN dim_fp_amendmentchargeschedule cs 
    ON la.amendment_hmy = cs.amendment_hmy
WHERE 
    -- Only rent-related charges
    cs.charge_code IN ('RENT', 'BASE RENT', 'MINIMUM RENT', 'BASIC RENT')
    OR cs.charge_code IS NULL;

-- =============================================================================
-- 5. CURRENT RENT ROLL (Amendment-based with charges)
-- Implements Current Monthly Rent DAX measure
-- =============================================================================
CREATE OR REPLACE VIEW v_current_rent_roll_enhanced AS
SELECT 
    property_hmy,
    property_code,
    property_name,
    tenant_hmy,
    tenant_code,
    tenant_name,
    amendment_hmy,
    amendment_sequence,
    amendment_type,
    amendment_status,
    amendment_start_date,
    amendment_end_date,
    lease_term_months,
    is_month_to_month,
    unit_number,
    leased_area,
    -- Aggregate monthly charges
    SUM(monthly_charge_amount) as current_monthly_rent,
    -- Calculate annual rent
    SUM(monthly_charge_amount) * 12 as current_annual_rent,
    -- Calculate PSF if area available
    CASE 
        WHEN leased_area > 0 
        THEN (SUM(monthly_charge_amount) * 12) / leased_area
        ELSE 0
    END as current_rent_psf
FROM v_latest_amendments_with_charges
GROUP BY 
    property_hmy, property_code, property_name,
    tenant_hmy, tenant_code, tenant_name,
    amendment_hmy, amendment_sequence, amendment_type,
    amendment_status, amendment_start_date, amendment_end_date,
    lease_term_months, is_month_to_month,
    unit_number, leased_area;

-- =============================================================================
-- 6. WALT CALCULATION (Weighted Average Lease Term)
-- Implements WALT (Months) DAX measure
-- =============================================================================
CREATE OR REPLACE VIEW v_walt_by_property AS
SELECT 
    property_code,
    property_name,
    -- WALT weighted by monthly rent
    CASE 
        WHEN SUM(current_monthly_rent) > 0
        THEN SUM(lease_term_months * current_monthly_rent) / SUM(current_monthly_rent)
        ELSE 0
    END as walt_months,
    -- Convert to years
    CASE 
        WHEN SUM(current_monthly_rent) > 0
        THEN SUM(lease_term_months * current_monthly_rent) / SUM(current_monthly_rent) / 12
        ELSE 0
    END as walt_years,
    -- Supporting metrics
    COUNT(DISTINCT tenant_hmy) as tenant_count,
    SUM(current_monthly_rent) as total_monthly_rent,
    SUM(leased_area) as total_leased_sf,
    AVG(lease_term_months) as avg_lease_term_months
FROM v_current_rent_roll_enhanced
WHERE current_monthly_rent > 0
GROUP BY property_code, property_name;

-- =============================================================================
-- 7. PORTFOLIO WALT (Overall portfolio weighted average)
-- =============================================================================
CREATE OR REPLACE VIEW v_portfolio_walt AS
SELECT 
    -- Portfolio-wide WALT
    CASE 
        WHEN SUM(current_monthly_rent) > 0
        THEN SUM(lease_term_months * current_monthly_rent) / SUM(current_monthly_rent)
        ELSE 0
    END as portfolio_walt_months,
    -- Convert to years
    CASE 
        WHEN SUM(current_monthly_rent) > 0
        THEN SUM(lease_term_months * current_monthly_rent) / SUM(current_monthly_rent) / 12
        ELSE 0
    END as portfolio_walt_years,
    -- Supporting metrics
    COUNT(DISTINCT property_hmy) as property_count,
    COUNT(DISTINCT tenant_hmy) as tenant_count,
    SUM(current_monthly_rent) as total_monthly_rent,
    SUM(leased_area) as total_leased_sf
FROM v_current_rent_roll_enhanced
WHERE current_monthly_rent > 0;

-- =============================================================================
-- 8. OCCUPANCY CALCULATIONS (Amendment-based)
-- Implements Physical Occupancy % and Economic Occupancy %
-- =============================================================================
CREATE OR REPLACE VIEW v_occupancy_metrics AS
WITH property_totals AS (
    SELECT 
        property_hmy,
        property_code,
        property_name,
        MAX(rentable_area) as total_rentable_area
    FROM dim_property
    GROUP BY property_hmy, property_code, property_name
),
leased_totals AS (
    SELECT 
        property_hmy,
        SUM(leased_area) as total_leased_area,
        SUM(current_monthly_rent) as total_monthly_rent
    FROM v_current_rent_roll_enhanced
    GROUP BY property_hmy
)
SELECT 
    pt.property_code,
    pt.property_name,
    pt.total_rentable_area,
    COALESCE(lt.total_leased_area, 0) as total_leased_area,
    COALESCE(lt.total_monthly_rent, 0) as total_monthly_rent,
    -- Physical Occupancy
    CASE 
        WHEN pt.total_rentable_area > 0
        THEN (COALESCE(lt.total_leased_area, 0) / pt.total_rentable_area) * 100
        ELSE 0
    END as physical_occupancy_pct,
    -- Vacant SF
    pt.total_rentable_area - COALESCE(lt.total_leased_area, 0) as vacant_sf,
    -- Vacancy Rate
    CASE 
        WHEN pt.total_rentable_area > 0
        THEN ((pt.total_rentable_area - COALESCE(lt.total_leased_area, 0)) / pt.total_rentable_area) * 100
        ELSE 0
    END as vacancy_rate_pct
FROM property_totals pt
LEFT JOIN leased_totals lt ON pt.property_hmy = lt.property_hmy;

-- =============================================================================
-- 9. LEASE EXPIRATION ANALYSIS
-- For lease expiration waterfall charts
-- =============================================================================
CREATE OR REPLACE VIEW v_lease_expirations AS
WITH current_date_ref AS (
    SELECT current_date FROM v_current_date
)
SELECT 
    -- Expiration period buckets
    CASE 
        WHEN amendment_end_date IS NULL THEN 'Month-to-Month'
        WHEN DATEDIFF('month', cd.current_date, amendment_end_date) <= 0 THEN 'Expired'
        WHEN DATEDIFF('month', cd.current_date, amendment_end_date) <= 3 THEN '0-3 Months'
        WHEN DATEDIFF('month', cd.current_date, amendment_end_date) <= 6 THEN '4-6 Months'
        WHEN DATEDIFF('month', cd.current_date, amendment_end_date) <= 12 THEN '7-12 Months'
        WHEN DATEDIFF('month', cd.current_date, amendment_end_date) <= 24 THEN '13-24 Months'
        ELSE '24+ Months'
    END as expiration_bucket,
    property_code,
    property_name,
    tenant_name,
    amendment_end_date,
    leased_area,
    current_monthly_rent,
    current_rent_psf
FROM v_current_rent_roll_enhanced
CROSS JOIN current_date_ref cd
ORDER BY amendment_end_date;

-- =============================================================================
-- 10. CREDIT SCORE INTEGRATION (Enhanced rent roll with credit)
-- =============================================================================
CREATE OR REPLACE VIEW v_rent_roll_with_credit AS
SELECT 
    rr.*,
    -- Credit Score Integration
    cs.credit_score,
    cs.annual_revenue,
    cs.primary_industry,
    cs.ownership,
    -- Customer Code Lookup (3-table priority)
    COALESCE(cs.customer_code, pm.customer_code, t.tenant_code) as customer_code,
    -- Credit Risk Category
    CASE 
        WHEN cs.credit_score >= 8 THEN 'Low Risk'
        WHEN cs.credit_score >= 6 THEN 'Medium Risk'
        WHEN cs.credit_score >= 4 THEN 'High Risk'
        WHEN cs.credit_score IS NOT NULL THEN 'Very High Risk'
        ELSE 'No Score'
    END as credit_risk_category,
    -- Parent Company Info
    pm.parent_customer_hmy,
    parent_cs.customer_name as parent_company_name,
    parent_cs.credit_score as parent_credit_score
FROM v_current_rent_roll_enhanced rr
LEFT JOIN dim_commcustomer t ON rr.tenant_hmy = t.tenant_hmy
LEFT JOIN dim_fp_customercreditscorecustomdata cs 
    ON t.customer_id = cs.hmyperson_customer
LEFT JOIN dim_fp_customertoparentmap pm 
    ON t.customer_id = pm.customer_hmy
LEFT JOIN dim_fp_customercreditscorecustomdata parent_cs 
    ON pm.parent_customer_hmy = parent_cs.hmyperson_customer;

-- =============================================================================
-- VALIDATION QUERY
-- Run this to verify amendment logic is working correctly
-- =============================================================================
/*
SELECT 
    COUNT(DISTINCT property_hmy) as property_count,
    COUNT(DISTINCT tenant_hmy) as tenant_count,
    COUNT(*) as total_amendments,
    SUM(current_monthly_rent) as total_monthly_rent,
    SUM(leased_area) as total_leased_sf,
    AVG(current_rent_psf) as avg_rent_psf
FROM v_current_rent_roll_enhanced
WHERE current_monthly_rent > 0;
*/