-- fact_leasingactivity Data Transformation and Integration Code
-- Purpose: Clean and prepare fact_leasingactivity for Power BI integration
-- Author: Claude AI Data Architect
-- Date: 2025-08-10

-- =============================================================================
-- POWER QUERY M CODE (For Power BI Desktop)
-- =============================================================================

/*
// Complete Power Query M transformation for fact_leasingactivity
let
    // Step 1: Load source data
    Source = Csv.Document(File.Contents("[YourPath]\fact_leasingactivity.csv")),
    Headers = Table.PromoteHeaders(Source),
    
    // Step 2: Data type conversions
    ConvertTypes = Table.TransformColumnTypes(Headers, {
        {"Deal HMY", Int64.Type},
        {"Tenant HMY", Int64.Type},
        {"Starting Rent", type number},
        {"Escalation Rate", type number},
        {"iTerm", Int64.Type},
        {"dArea", type number},
        {"dTotalNPV", type number},
        {"dAnnualNPV", type number},
        {"dTotalRent", type number},
        {"dTIAllowance", type number},
        {"dCommissionInside", type number},
        {"dCommissionOutside", type number},
        {"dFreeRent", type number},
        {"dAverageRent", type number},
        {"dNER", type number},
        {"dIRR", type number},
        {"dtStartDate", type date},
        {"dtEndDate", type date},
        {"dtcreated", type datetime},
        {"dtlastmodified", type datetime}
    }),
    
    // Step 3: Clean tenant codes (remove empty strings, set to null)
    CleanTenantCode = Table.ReplaceValue(ConvertTypes, "", null, Replacer.ReplaceValue, {"Tenant Code"}),
    
    // Step 4: Add business logic columns
    AddDealStageOrder = Table.AddColumn(CleanTenantCode, "Deal Stage Order", 
        each if [Deal Stage] = "Lead" then 1
        else if [Deal Stage] = "Tour" then 2  
        else if [Deal Stage] = "Proposal" then 3
        else if [Deal Stage] = "Negotiation" then 4
        else if [Deal Stage] = "Executed" then 5
        else if [Deal Stage] = "Dead Deal" then 0
        else 99, Int64.Type),
    
    // Step 5: Add lease term categorization
    AddTermCategory = Table.AddColumn(AddDealStageOrder, "Term Category",
        each if [iTerm] = null then "Unknown"
        else if [iTerm] <= 12 then "Short Term (≤12 months)"
        else if [iTerm] <= 36 then "Medium Term (13-36 months)" 
        else if [iTerm] <= 60 then "Long Term (37-60 months)"
        else "Extended Term (>60 months)", type text),
    
    // Step 6: Add deal size categorization based on area
    AddSizeCategory = Table.AddColumn(AddTermCategory, "Deal Size Category",
        each if [dArea] = null then "Unknown"
        else if [dArea] <= 5000 then "Small (≤5K SF)"
        else if [dArea] <= 15000 then "Medium (5K-15K SF)"
        else if [dArea] <= 50000 then "Large (15K-50K SF)"
        else "Extra Large (>50K SF)", type text),
    
    // Step 7: Add annualized rent calculation
    AddAnnualizedRent = Table.AddColumn(AddSizeCategory, "Annualized Starting Rent",
        each if [Starting Rent] = null or [dArea] = null or [dArea] = 0 then null
        else ([Starting Rent] * 12), type number),
    
    // Step 8: Add rent per square foot calculation  
    AddRentPSF = Table.AddColumn(AddAnnualizedRent, "Starting Rent PSF",
        each if [Annualized Starting Rent] = null or [dArea] = null or [dArea] = 0 then null
        else [Annualized Starting Rent] / [dArea], type number),
    
    // Step 9: Add deal timeline calculations
    AddDealDuration = Table.AddColumn(AddRentPSF, "Deal Duration Days",
        each if [dtStartDate] = null or [dtEndDate] = null then null
        else Duration.Days([dtEndDate] - [dtStartDate]), Int64.Type),
    
    // Step 10: Add data quality flags
    AddDataQualityFlags = Table.AddColumn(AddDealDuration, "Has Tenant Link",
        each [Tenant Code] <> null, type logical),
    
    AddOrphanFlag = Table.AddColumn(AddDataQualityFlags, "Is Orphaned Tenant",
        each [Tenant Code] <> null and 
             List.Contains({"t0001675", "t0001676", "t0001677", "t0001678", "t0001679", 
                           "t0001680", "t0001681", "t0001682", "t0001683", "t0001684", "t0001685"}, 
                          [Tenant Code]), type logical),
    
    // Step 11: Add fiscal year calculations (assuming fiscal year starts July 1)
    AddFiscalYear = Table.AddColumn(AddOrphanFlag, "Start Fiscal Year",
        each if [dtStartDate] = null then null
        else if Date.Month([dtStartDate]) >= 7 then Date.Year([dtStartDate]) + 1
        else Date.Year([dtStartDate]), Int64.Type),
    
    // Step 12: Final column reordering for usability
    ReorderColumns = Table.ReorderColumns(AddFiscalYear, {
        "Deal HMY", "Deal Stage", "Deal Stage Order", "Proposal Type", 
        "Tenant Code", "Tenant HMY", "Has Tenant Link", "Is Orphaned Tenant",
        "dtStartDate", "dtEndDate", "Start Fiscal Year", "Deal Duration Days",
        "iTerm", "Term Category", "dArea", "Deal Size Category",
        "Starting Rent", "Annualized Starting Rent", "Starting Rent PSF",
        "Escalation Rate", "dAverageRent", "dTotalRent", "dTotalNPV", "dAnnualNPV",
        "dNER", "dIRR", "dTIAllowance", "dCommissionInside", "dCommissionOutside",
        "dFreeRent", "Cash Flow Type", "iCashFlowType", "hCommamendment"
    })
    
in
    ReorderColumns
*/

-- =============================================================================
-- SQL VALIDATION QUERIES (For data quality checks)
-- =============================================================================

-- Query 1: Validate tenant code relationships
WITH orphaned_tenants AS (
    SELECT DISTINCT la.[Tenant Code]
    FROM fact_leasingactivity la
    LEFT JOIN dim_commcustomer dc ON la.[Tenant Code] = dc.[tenant code]
    WHERE la.[Tenant Code] IS NOT NULL 
    AND dc.[tenant code] IS NULL
)
SELECT 
    COUNT(*) as orphaned_tenant_codes_count,
    (SELECT COUNT(DISTINCT [Tenant Code]) FROM fact_leasingactivity WHERE [Tenant Code] IS NOT NULL) as total_tenant_codes,
    CAST(COUNT(*) * 100.0 / (SELECT COUNT(DISTINCT [Tenant Code]) FROM fact_leasingactivity WHERE [Tenant Code] IS NOT NULL) AS DECIMAL(5,2)) as orphan_percentage
FROM orphaned_tenants;

-- Query 2: Deal stage distribution analysis
SELECT 
    [Deal Stage],
    COUNT(*) as deal_count,
    CAST(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER() AS DECIMAL(5,2)) as percentage,
    AVG([Starting Rent]) as avg_starting_rent,
    AVG([dArea]) as avg_area_sf,
    AVG([iTerm]) as avg_term_months
FROM fact_leasingactivity
WHERE [Tenant Code] IS NOT NULL  -- Exclude orphaned records
GROUP BY [Deal Stage]
ORDER BY 
    CASE [Deal Stage]
        WHEN 'Lead' THEN 1
        WHEN 'Tour' THEN 2
        WHEN 'Proposal' THEN 3
        WHEN 'Negotiation' THEN 4
        WHEN 'Executed' THEN 5
        WHEN 'Dead Deal' THEN 6
        ELSE 7
    END;

-- Query 3: Proposal type analysis
SELECT 
    [Proposal Type],
    COUNT(*) as deal_count,
    COUNT(CASE WHEN [Deal Stage] = 'Executed' THEN 1 END) as executed_count,
    CAST(COUNT(CASE WHEN [Deal Stage] = 'Executed' THEN 1 END) * 100.0 / COUNT(*) AS DECIMAL(5,2)) as execution_rate,
    AVG([Starting Rent]) as avg_starting_rent,
    SUM([dArea]) as total_area_sf
FROM fact_leasingactivity
WHERE [Tenant Code] IS NOT NULL
GROUP BY [Proposal Type]
ORDER BY deal_count DESC;

-- Query 4: Date range and completeness check
SELECT 
    MIN([dtStartDate]) as earliest_start_date,
    MAX([dtStartDate]) as latest_start_date,
    MIN([dtEndDate]) as earliest_end_date,
    MAX([dtEndDate]) as latest_end_date,
    COUNT(*) as total_records,
    COUNT([dtStartDate]) as records_with_start_date,
    COUNT([dtEndDate]) as records_with_end_date,
    COUNT([Tenant Code]) as records_with_tenant_code
FROM fact_leasingactivity;

-- Query 5: Financial metrics analysis
SELECT 
    [Deal Stage],
    [Proposal Type],
    COUNT(*) as deal_count,
    AVG([Starting Rent]) as avg_starting_rent,
    AVG([dTotalNPV]) as avg_total_npv,
    AVG([dNER]) as avg_ner,
    AVG([dIRR]) as avg_irr,
    SUM([dTIAllowance]) as total_ti_allowance,
    SUM([dCommissionInside] + [dCommissionOutside]) as total_commissions
FROM fact_leasingactivity
WHERE [Tenant Code] IS NOT NULL
  AND [Starting Rent] > 0
GROUP BY [Deal Stage], [Proposal Type]
ORDER BY [Deal Stage], deal_count DESC;

-- =============================================================================
-- POWER BI RELATIONSHIP DEFINITIONS
-- =============================================================================

/*
Create these relationships in Power BI Model view:

1. PRIMARY TENANT RELATIONSHIP
   From: fact_leasingactivity[Tenant Code]
   To: dim_commcustomer[tenant code]
   Cardinality: Many-to-One (*)
   Cross Filter Direction: Single (Left to Right)
   Active: Yes
   
2. START DATE RELATIONSHIP  
   From: fact_leasingactivity[dtStartDate]
   To: dim_date[date]
   Cardinality: Many-to-One (*)
   Cross Filter Direction: Single (Left to Right) 
   Active: Yes
   
3. END DATE RELATIONSHIP
   From: fact_leasingactivity[dtEndDate] 
   To: dim_date[date]
   Cardinality: Many-to-One (*)
   Cross Filter Direction: Single (Left to Right)
   Active: No (set inactive, activate in specific measures as needed)
   
4. AMENDMENT RELATIONSHIP (Optional - validate first)
   From: fact_leasingactivity[hCommamendment]
   To: dim_fp_amendmentsunitspropertytenant[amendment hmy]
   Cardinality: Many-to-One (*)
   Cross Filter Direction: Single (Left to Right)
   Active: Yes (if validation confirms relationship exists)
*/

-- =============================================================================
-- DATA QUALITY MONITORING MEASURES (DAX)
-- =============================================================================

/*
Create these measures in Power BI for ongoing data quality monitoring:

-- Orphaned Records Count
Orphaned Leasing Records = 
CALCULATE(
    COUNTROWS(fact_leasingactivity),
    ISBLANK(RELATED(dim_commcustomer[tenant id]))
)

-- Data Quality Score
Leasing Data Quality % = 
VAR TotalRecords = COUNTROWS(fact_leasingactivity)
VAR ValidRecords = 
    CALCULATE(
        COUNTROWS(fact_leasingactivity),
        NOT ISBLANK(RELATED(dim_commcustomer[tenant id]))
    )
RETURN
    DIVIDE(ValidRecords, TotalRecords, 0) * 100

-- Active Deals Count
Active Leasing Deals = 
CALCULATE(
    COUNTROWS(fact_leasingactivity),
    fact_leasingactivity[Deal Stage] IN {"Lead", "Tour", "Proposal", "Negotiation"}
)

-- Executed Deals This Year
Executed Deals YTD = 
CALCULATE(
    COUNTROWS(fact_leasingactivity),
    fact_leasingactivity[Deal Stage] = "Executed",
    DATESYTD(dim_date[date])
)
*/

-- =============================================================================
-- DEPLOYMENT CHECKLIST
-- =============================================================================

/*
1. ✅ Load fact_leasingactivity.csv into Power BI
2. ✅ Apply Power Query M transformations above
3. ✅ Create tenant relationship: fact_leasingactivity[Tenant Code] → dim_commcustomer[tenant code]
4. ✅ Create start date relationship: fact_leasingactivity[dtStartDate] → dim_date[date]
5. ⚠️ Validate amendment relationship before creating
6. ✅ Set end date relationship as inactive (for specific measure use)
7. ✅ Test basic filtering and measures
8. ✅ Add data quality monitoring measures
9. ✅ Update data refresh schedule to include new table
10. ✅ Document new table in data dictionary
*/