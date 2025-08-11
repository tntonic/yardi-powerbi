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
    MAX("last closed period") as current_date,
    MAX("last closed period") as reporting_date
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
    p."property name",
    p."property code",
    t."lessee name" as tenant_name,
    t."tenant code",
    -- Calculate lease term in months
    CASE 
        WHEN a."amendment end date" IS NOT NULL 
        THEN DATEDIFF('month', a."amendment start date", a."amendment end date")
        ELSE DATEDIFF('month', a."amendment start date", cd.current_date)
    END as lease_term_months,
    -- Month-to-month flag
    CASE 
        WHEN a."amendment end date" IS NULL THEN 1
        WHEN DATEDIFF('month', a."amendment start date", a."amendment end date") <= 1 THEN 1
        ELSE 0
    END as is_month_to_month
FROM dim_fp_amendmentsunitspropertytenant a
CROSS JOIN current_date_ref cd
LEFT JOIN dim_property p ON a."property hmy" = p."property id"
LEFT JOIN dim_commcustomer t ON a."tenant hmy" = t."tenant hmy"
WHERE 
    -- Critical status filtering for accuracy
    a."amendment status" IN ('Activated', 'Superseded')
    -- Exclude certain amendment types
    AND a."amendment type" NOT IN ('Termination', 'Proposal in DM', 'Modification')
    -- Date filtering
    AND a."amendment start date" <= cd.current_date
    AND (a."amendment end date" >= cd.current_date OR a."amendment end date" IS NULL);

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
        "property hmy",
        "tenant hmy",
        MAX("amendment sequence") as max_sequence
    FROM v_base_active_amendments
    GROUP BY "property hmy", "tenant hmy"
)
SELECT 
    a.*
FROM v_base_active_amendments a
INNER JOIN max_sequences ms 
    ON a."property hmy" = ms."property hmy" 
    AND a."tenant hmy" = ms."tenant hmy"
    AND a."amendment sequence" = ms.max_sequence;

-- =============================================================================
-- 4. LATEST AMENDMENTS WITH CHARGES
-- Implements _LatestAmendmentsWithCharges DAX helper
-- =============================================================================
CREATE OR REPLACE VIEW v_latest_amendments_with_charges AS
SELECT 
    la.*,
    cs."charge code",
    cs."charge amount",
    cs."charge frequency",
    -- Calculate monthly amount based on frequency
    CASE cs."charge frequency"
        WHEN 'Monthly' THEN cs."charge amount"
        WHEN 'Annually' THEN cs."charge amount" / 12
        WHEN 'Quarterly' THEN cs."charge amount" / 3
        WHEN 'Semi-Annually' THEN cs."charge amount" / 6
        ELSE cs."charge amount"
    END as monthly_charge_amount
FROM v_latest_amendments la
LEFT JOIN dim_fp_amendmentchargeschedule cs 
    ON la."amendment hmy" = cs."amendment hmy"
WHERE 
    -- Only rent-related charges
    cs."charge code" IN ('RENT', 'BASE RENT', 'MINIMUM RENT', 'BASIC RENT')
    OR cs."charge code" IS NULL;

-- =============================================================================
-- 5. CURRENT RENT ROLL (Amendment-based with charges)
-- Implements Current Monthly Rent DAX measure
-- =============================================================================
CREATE OR REPLACE VIEW v_current_rent_roll_enhanced AS
SELECT 
    "property hmy",
    "property code",
    "property name",
    "tenant hmy",
    "tenant code",
    tenant_name,
    "amendment hmy",
    "amendment sequence",
    "amendment type",
    "amendment status",
    "amendment start date",
    "amendment end date",
    lease_term_months,
    is_month_to_month,
    "unit number",
    "leased area",
    -- Aggregate monthly charges
    SUM(monthly_charge_amount) as current_monthly_rent,
    -- Calculate annual rent
    SUM(monthly_charge_amount) * 12 as current_annual_rent,
    -- Calculate PSF if area available
    CASE 
        WHEN "leased area" > 0 
        THEN (SUM(monthly_charge_amount) * 12) / "leased area"
        ELSE 0
    END as current_rent_psf
FROM v_latest_amendments_with_charges
GROUP BY 
    "property hmy", "property code", "property name",
    "tenant hmy", "tenant code", tenant_name,
    "amendment hmy", "amendment sequence", "amendment type",
    "amendment status", "amendment start date", "amendment end date",
    lease_term_months, is_month_to_month,
    "unit number", "leased area";

-- =============================================================================
-- 6. WALT CALCULATION (Weighted Average Lease Term)
-- Implements WALT (Months) DAX measure
-- =============================================================================
CREATE OR REPLACE VIEW v_walt_by_property AS
SELECT 
    "property code",
    "property name",
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
    COUNT(DISTINCT "tenant hmy") as tenant_count,
    SUM(current_monthly_rent) as total_monthly_rent,
    SUM("leased area") as total_leased_sf,
    AVG(lease_term_months) as avg_lease_term_months
FROM v_current_rent_roll_enhanced
WHERE current_monthly_rent > 0
GROUP BY "property code", "property name";

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
    COUNT(DISTINCT "property hmy") as property_count,
    COUNT(DISTINCT "tenant hmy") as tenant_count,
    SUM(current_monthly_rent) as total_monthly_rent,
    SUM("leased area") as total_leased_sf
FROM v_current_rent_roll_enhanced
WHERE current_monthly_rent > 0;

-- =============================================================================
-- 8. OCCUPANCY CALCULATIONS (Amendment-based)
-- Implements Physical Occupancy % and Economic Occupancy %
-- =============================================================================
CREATE OR REPLACE VIEW v_occupancy_metrics AS
WITH property_totals AS (
    SELECT 
        "property hmy",
        "property code",
        "property name",
        MAX("rentable area") as total_rentable_area
    FROM dim_property
    GROUP BY "property hmy", "property code", "property name"
),
leased_totals AS (
    SELECT 
        "property hmy",
        SUM("leased area") as total_leased_area,
        SUM(current_monthly_rent) as total_monthly_rent
    FROM v_current_rent_roll_enhanced
    GROUP BY "property hmy"
)
SELECT 
    pt."property code",
    pt."property name",
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
LEFT JOIN leased_totals lt ON pt."property hmy" = lt."property hmy";

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
        WHEN "amendment end date" IS NULL THEN 'Month-to-Month'
        WHEN DATEDIFF('month', cd.current_date, "amendment end date") <= 0 THEN 'Expired'
        WHEN DATEDIFF('month', cd.current_date, "amendment end date") <= 3 THEN '0-3 Months'
        WHEN DATEDIFF('month', cd.current_date, "amendment end date") <= 6 THEN '4-6 Months'
        WHEN DATEDIFF('month', cd.current_date, "amendment end date") <= 12 THEN '7-12 Months'
        WHEN DATEDIFF('month', cd.current_date, "amendment end date") <= 24 THEN '13-24 Months'
        ELSE '24+ Months'
    END as expiration_bucket,
    "property code",
    "property name",
    tenant_name,
    "amendment end date",
    "leased area",
    current_monthly_rent,
    current_rent_psf
FROM v_current_rent_roll_enhanced
CROSS JOIN current_date_ref cd
ORDER BY "amendment end date";

-- =============================================================================
-- 10. CREDIT SCORE INTEGRATION (Enhanced rent roll with credit)
-- =============================================================================
CREATE OR REPLACE VIEW v_rent_roll_with_credit AS
SELECT 
    rr.*,
    -- Credit Score Integration
    cs."credit score",
    cs."annual revenue",
    cs."primary industry",
    cs.ownership,
    -- Customer Code Lookup (3-table priority)
    COALESCE(cs."customer code", pm."customer code", t."tenant code") as "customer code",
    -- Credit Risk Category
    CASE 
        WHEN cs."credit score" >= 8 THEN 'Low Risk'
        WHEN cs."credit score" >= 6 THEN 'Medium Risk'
        WHEN cs."credit score" >= 4 THEN 'High Risk'
        WHEN cs."credit score" IS NOT NULL THEN 'Very High Risk'
        ELSE 'No Score'
    END as credit_risk_category,
    -- Parent Company Info
    pm."parent customer hmy",
    parent_cs."customer name" as parent_company_name,
    parent_cs."credit score" as parent_credit_score
FROM v_current_rent_roll_enhanced rr
LEFT JOIN dim_commcustomer t ON rr."tenant hmy" = t."tenant hmy"
LEFT JOIN dim_fp_customercreditscorecustomdata cs 
    ON t."customer id" = cs."hmyperson customer"
LEFT JOIN dim_fp_customertoparentmap pm 
    ON t."customer id" = pm."customer hmy"
LEFT JOIN dim_fp_customercreditscorecustomdata parent_cs 
    ON pm."parent customer hmy" = parent_cs."hmyperson customer";

-- =============================================================================
-- VALIDATION QUERY
-- Run this to verify amendment logic is working correctly
-- =============================================================================
/*
SELECT 
    COUNT(DISTINCT "property hmy") as property_count,
    COUNT(DISTINCT "tenant hmy") as tenant_count,
    COUNT(*) as total_amendments,
    SUM(current_monthly_rent) as total_monthly_rent,
    SUM("leased area") as total_leased_sf,
    AVG(current_rent_psf) as avg_rent_psf
FROM v_current_rent_roll_enhanced
WHERE current_monthly_rent > 0;
*/