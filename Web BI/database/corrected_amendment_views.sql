-- =============================================================================
-- CORRECTED AMENDMENT-BASED LOGIC VIEWS
-- Fixed column names to match actual database structure
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
-- =============================================================================
CREATE OR REPLACE VIEW v_base_active_amendments AS
WITH current_date_ref AS (
    SELECT current_date FROM v_current_date
)
SELECT 
    a.*,
    p."property name",
    p."property code" as prop_code,
    t."lessee name" as tenant_name,
    t."tenant code",
    -- Calculate lease term in months
    CASE 
        WHEN a."amendment end date" IS NOT NULL AND a."amendment end date" != ''
        THEN DATEDIFF('month', 
            CAST(a."amendment start date" AS DATE), 
            CAST(a."amendment end date" AS DATE))
        ELSE DATEDIFF('month', 
            CAST(a."amendment start date" AS DATE), 
            CAST(cd.current_date AS DATE))
    END as lease_term_months,
    -- Month-to-month flag
    CASE 
        WHEN a."amendment end date" IS NULL OR a."amendment end date" = '' THEN 1
        WHEN DATEDIFF('month', 
            CAST(a."amendment start date" AS DATE), 
            CAST(a."amendment end date" AS DATE)) <= 1 THEN 1
        ELSE 0
    END as is_month_to_month
FROM dim_fp_amendmentsunitspropertytenant a
CROSS JOIN current_date_ref cd
LEFT JOIN dim_property p ON a."property hmy" = p."property id"
LEFT JOIN dim_commcustomer t ON a."tenant hmy" = t."tenant id"
WHERE 
    -- Critical status filtering for accuracy
    a."amendment status" IN ('Activated', 'Superseded')
    -- Exclude certain amendment types
    AND a."amendment type" NOT IN ('Termination', 'Proposal in DM', 'Modification')
    -- Date filtering
    AND CAST(a."amendment start date" AS DATE) <= CAST(cd.current_date AS DATE)
    AND (a."amendment end date" = '' 
         OR a."amendment end date" IS NULL 
         OR CAST(a."amendment end date" AS DATE) >= CAST(cd.current_date AS DATE));

-- =============================================================================
-- 3. LATEST AMENDMENTS (Latest sequence per property/tenant)
-- =============================================================================
CREATE OR REPLACE VIEW v_latest_amendments AS
WITH max_sequences AS (
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
        ELSE COALESCE(cs."charge amount", 0)
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
-- =============================================================================
CREATE OR REPLACE VIEW v_current_rent_roll_enhanced AS
SELECT 
    "property hmy",
    prop_code as "property code",
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
    "units under amendment" as "unit number",
    COALESCE("amendment sf", 0) as "leased area",
    -- Aggregate monthly charges
    SUM(COALESCE(monthly_charge_amount, 0)) as current_monthly_rent,
    -- Calculate annual rent
    SUM(COALESCE(monthly_charge_amount, 0)) * 12 as current_annual_rent,
    -- Calculate PSF if area available
    CASE 
        WHEN COALESCE("amendment sf", 0) > 0 
        THEN (SUM(COALESCE(monthly_charge_amount, 0)) * 12) / "amendment sf"
        ELSE 0
    END as current_rent_psf
FROM v_latest_amendments_with_charges
GROUP BY 
    "property hmy", prop_code, "property name",
    "tenant hmy", "tenant code", tenant_name,
    "amendment hmy", "amendment sequence", "amendment type",
    "amendment status", "amendment start date", "amendment end date",
    lease_term_months, is_month_to_month,
    "units under amendment", "amendment sf";

-- =============================================================================
-- 6. OCCUPANCY CALCULATIONS (Amendment-based)
-- Note: dim_property doesn't have rentable area, using placeholder
-- =============================================================================
CREATE OR REPLACE VIEW v_occupancy_metrics AS
WITH property_totals AS (
    SELECT 
        "property id" as "property hmy",
        "property code",
        "property name",
        100000 as total_rentable_area  -- Placeholder - no rentable area in dim_property
    FROM dim_property
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
-- 7. RENT ROLL WITH CREDIT (Enhanced with credit scores)
-- =============================================================================
CREATE OR REPLACE VIEW v_rent_roll_with_credit AS
SELECT 
    rr.*,
    -- Credit Score Integration
    cs."credit score",
    cs."annual revenue",
    cs."primary industry",
    cs.ownership,
    -- Customer Code (use tenant code as fallback)
    COALESCE(cs."customer code", pm."customer code", rr."tenant code") as "customer code",
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
LEFT JOIN dim_commcustomer t ON rr."tenant hmy" = t."tenant id"
LEFT JOIN dim_fp_customercreditscorecustomdata cs 
    ON t."customer id" = cs."hmyperson customer"
LEFT JOIN dim_fp_customertoparentmap pm 
    ON t."customer id" = pm."customer hmy"
LEFT JOIN dim_fp_customercreditscorecustomdata parent_cs 
    ON pm."parent customer hmy" = parent_cs."hmyperson customer";