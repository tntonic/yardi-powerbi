-- ============================================
-- VALIDATION QUERIES FOR FUND, MARKET & REGION FILTERING
-- ============================================
-- Run these queries to validate the data model and filtering setup

-- ============================================
-- SECTION 1: DATA INTEGRITY CHECKS
-- ============================================

-- Check 1: Verify all properties have building custom data
SELECT 
    COUNT(DISTINCT p.[property id]) as total_properties,
    COUNT(DISTINCT b.[hmy property]) as properties_with_building_data,
    COUNT(DISTINCT p.[property id]) - COUNT(DISTINCT b.[hmy property]) as missing_building_data
FROM dim_property p
LEFT JOIN dim_fp_buildingcustomdata b ON p.[property id] = b.[hmy property];

-- Check 2: Find properties missing fund assignments
SELECT 
    p.[property id],
    p.[property name],
    p.[property code],
    b.fund,
    b.market,
    'Missing Fund' as issue_type
FROM dim_property p
LEFT JOIN dim_fp_buildingcustomdata b ON p.[property id] = b.[hmy property]
WHERE b.fund IS NULL OR TRIM(b.fund) = ''
ORDER BY p.[property name];

-- Check 3: Find properties missing market assignments  
SELECT 
    p.[property id],
    p.[property name],
    p.[property code],
    b.fund,
    b.market,
    'Missing Market' as issue_type
FROM dim_property p
LEFT JOIN dim_fp_buildingcustomdata b ON p.[property id] = b.[hmy property]
WHERE b.market IS NULL OR TRIM(b.market) = ''
ORDER BY p.[property name];

-- Check 4: Validate fund values are consistent
SELECT 
    fund,
    COUNT(*) as property_count,
    SUM(CASE WHEN status = 'Acquired' THEN 1 ELSE 0 END) as active_properties,
    SUM(CASE WHEN status = 'Sold' THEN 1 ELSE 0 END) as sold_properties
FROM dim_fp_buildingcustomdata
WHERE fund IS NOT NULL
GROUP BY fund
ORDER BY property_count DESC;

-- Check 5: Validate market values and distribution
SELECT 
    market,
    state,
    COUNT(*) as property_count,
    COUNT(DISTINCT fund) as funds_in_market
FROM dim_fp_buildingcustomdata
WHERE market IS NOT NULL
GROUP BY market, state
ORDER BY property_count DESC;

-- ============================================
-- SECTION 2: RELATIONSHIP VALIDATION
-- ============================================

-- Check 6: Verify one-to-one relationship integrity
WITH DuplicateCheck AS (
    SELECT 
        [hmy property],
        COUNT(*) as record_count
    FROM dim_fp_buildingcustomdata
    GROUP BY [hmy property]
    HAVING COUNT(*) > 1
)
SELECT 
    'Duplicate hmy property in building data' as issue,
    COUNT(*) as duplicate_count
FROM DuplicateCheck;

-- Check 7: Validate property to building data join
SELECT 
    'Properties' as table_name,
    COUNT(DISTINCT [property id]) as unique_keys
FROM dim_property
UNION ALL
SELECT 
    'Building Custom Data' as table_name,
    COUNT(DISTINCT [hmy property]) as unique_keys
FROM dim_fp_buildingcustomdata;

-- Check 8: Find orphaned building custom data records
SELECT 
    b.[hmy property],
    b.[property code],
    b.fund,
    b.market,
    'Orphaned Building Data' as issue_type
FROM dim_fp_buildingcustomdata b
LEFT JOIN dim_property p ON b.[hmy property] = p.[property id]
WHERE p.[property id] IS NULL;

-- ============================================
-- SECTION 3: FUND ANALYSIS VALIDATION
-- ============================================

-- Check 9: Fund portfolio composition
SELECT 
    b.fund,
    COUNT(DISTINCT p.[property id]) as property_count,
    SUM(p.[rentable area]) as total_rentable_sf,
    AVG(p.[rentable area]) as avg_property_size,
    MIN(b.[acq. date]) as earliest_acquisition,
    MAX(b.[acq. date]) as latest_acquisition
FROM dim_property p
INNER JOIN dim_fp_buildingcustomdata b ON p.[property id] = b.[hmy property]
WHERE b.fund IS NOT NULL
GROUP BY b.fund
ORDER BY total_rentable_sf DESC;

-- Check 10: Fund geographic diversification
SELECT 
    b.fund,
    b.state,
    COUNT(*) as properties_in_state,
    SUM(p.[rentable area]) as rentable_sf_in_state
FROM dim_property p
INNER JOIN dim_fp_buildingcustomdata b ON p.[property id] = b.[hmy property]
WHERE b.fund IS NOT NULL
GROUP BY b.fund, b.state
ORDER BY b.fund, properties_in_state DESC;

-- Check 11: Fund performance metrics validation
WITH FundMetrics AS (
    SELECT 
        b.fund,
        COUNT(DISTINCT p.property_id) as property_count,
        SUM(CASE WHEN f.account_code BETWEEN 40000000 AND 49999999 THEN f.amount * -1 ELSE 0 END) as total_revenue,
        SUM(CASE WHEN f.account_code BETWEEN 50000000 AND 59999999 THEN f.amount ELSE 0 END) as total_expenses
    FROM dim_property p
    INNER JOIN dim_fp_buildingcustomdata b ON p.[property hmy] = b.hmy_property
    LEFT JOIN fact_total f ON p.property_id = f.property_id
    WHERE b.fund IS NOT NULL
    GROUP BY b.fund
)
SELECT 
    fund,
    property_count,
    total_revenue,
    total_expenses,
    (total_revenue - total_expenses) as noi,
    CASE WHEN total_revenue > 0 
         THEN ((total_revenue - total_expenses) / total_revenue) * 100 
         ELSE 0 END as noi_margin_pct
FROM FundMetrics
ORDER BY noi DESC;

-- ============================================
-- SECTION 4: MARKET ANALYSIS VALIDATION
-- ============================================

-- Check 12: Market portfolio composition
SELECT 
    b.market,
    b.state,
    COUNT(DISTINCT p.property_id) as property_count,
    COUNT(DISTINCT b.fund) as fund_count,
    SUM(p.[rentable area]) as total_rentable_sf,
    AVG(p.[year built]) as avg_year_built
FROM dim_property p
INNER JOIN dim_fp_buildingcustomdata b ON p.[property hmy] = b.hmy_property
WHERE b.market IS NOT NULL
GROUP BY b.market, b.state
ORDER BY total_rentable_sf DESC;

-- Check 13: Market occupancy validation
SELECT 
    b.market,
    AVG(o.occupied_area * 1.0 / NULLIF(o.rentable_area, 0)) * 100 as avg_occupancy_pct,
    SUM(o.occupied_area) as total_occupied_sf,
    SUM(o.rentable_area) as total_rentable_sf
FROM dim_property p
INNER JOIN dim_fp_buildingcustomdata b ON p.[property hmy] = b.hmy_property
LEFT JOIN fact_occupancyrentarea o ON p.property_id = o.property_id
WHERE b.market IS NOT NULL
    AND o.[first day of month] = (SELECT MAX([first day of month]) FROM fact_occupancyrentarea)
GROUP BY b.market
ORDER BY avg_occupancy_pct DESC;

-- Check 14: Cross-market fund presence
WITH FundMarketMatrix AS (
    SELECT 
        b.fund,
        b.market,
        COUNT(*) as property_count
    FROM dim_fp_buildingcustomdata b
    WHERE b.fund IS NOT NULL AND b.market IS NOT NULL
    GROUP BY b.fund, b.market
)
SELECT 
    fund,
    COUNT(DISTINCT market) as markets_present_in,
    STRING_AGG(market + ' (' + CAST(property_count AS VARCHAR) + ')', ', ') as market_distribution
FROM FundMarketMatrix
GROUP BY fund
ORDER BY markets_present_in DESC;

-- ============================================
-- SECTION 5: REGIONAL HIERARCHY VALIDATION
-- ============================================

-- Check 15: Regional distribution of properties
WITH RegionalMapping AS (
    SELECT 
        b.*,
        CASE 
            WHEN b.state IN ('NY','NJ','CT','MA','RI','VT','NH','ME','PA') THEN 'Northeast'
            WHEN b.state IN ('FL','GA','SC','NC','VA','WV','KY','TN','AL','MS','AR','LA') THEN 'Southeast'
            WHEN b.state IN ('OH','MI','IN','IL','WI','MN','IA','MO','ND','SD','NE','KS') THEN 'Midwest'
            WHEN b.state IN ('TX','OK','NM','AZ') THEN 'Southwest'
            WHEN b.state IN ('CA','OR','WA','NV','UT','CO','ID','MT','WY','AK','HI') THEN 'West'
            ELSE 'Other'
        END as region
    FROM dim_fp_buildingcustomdata b
)
SELECT 
    region,
    COUNT(DISTINCT fund) as fund_count,
    COUNT(DISTINCT market) as market_count,
    COUNT(*) as property_count,
    STRING_AGG(DISTINCT state, ', ') as states_in_region
FROM RegionalMapping
GROUP BY region
ORDER BY property_count DESC;

-- Check 16: Validate market-to-region mapping consistency
WITH MarketRegions AS (
    SELECT 
        market,
        state,
        COUNT(*) as property_count,
        CASE 
            WHEN state IN ('NY','NJ','CT','MA','RI','VT','NH','ME','PA') THEN 'Northeast'
            WHEN state IN ('FL','GA','SC','NC','VA','WV','KY','TN','AL','MS','AR','LA') THEN 'Southeast'
            WHEN state IN ('OH','MI','IN','IL','WI','MN','IA','MO','ND','SD','NE','KS') THEN 'Midwest'
            WHEN state IN ('TX','OK','NM','AZ') THEN 'Southwest'
            WHEN state IN ('CA','OR','WA','NV','UT','CO','ID','MT','WY','AK','HI') THEN 'West'
            ELSE 'Other'
        END as region
    FROM dim_fp_buildingcustomdata
    WHERE market IS NOT NULL
    GROUP BY market, state
)
SELECT 
    market,
    state,
    region,
    property_count,
    'Check if market spans multiple regions' as validation_note
FROM MarketRegions
ORDER BY market, state;

-- ============================================
-- SECTION 6: FILTER COMBINATION TESTING
-- ============================================

-- Check 17: Test fund + market filter combination
DECLARE @TestFund VARCHAR(100) = 'FRG IX';  -- Replace with actual fund
DECLARE @TestMarket VARCHAR(100) = 'Houston';  -- Replace with actual market

SELECT 
    p.[property id],
    p.[property name],
    b.fund,
    b.market,
    b.status,
    p.[rentable area]
FROM dim_property p
INNER JOIN dim_fp_buildingcustomdata b ON p.[property id] = b.[hmy property]
WHERE b.fund = @TestFund 
    AND b.market = @TestMarket
ORDER BY p.[property name];

-- Check 18: Validate filter result counts
WITH FilterCombinations AS (
    SELECT 
        b.fund,
        b.market,
        COUNT(*) as property_count,
        SUM(p.[rentable area]) as total_sf
    FROM dim_property p
    INNER JOIN dim_fp_buildingcustomdata b ON p.[property hmy] = b.hmy_property
    WHERE b.fund IS NOT NULL AND b.market IS NOT NULL
    GROUP BY b.fund, b.market
)
SELECT 
    fund,
    market,
    property_count,
    total_sf,
    'Validate these counts match Power BI' as validation_instruction
FROM FilterCombinations
ORDER BY fund, market;

-- ============================================
-- SECTION 7: PERFORMANCE TESTING QUERIES
-- ============================================

-- Check 19: Index recommendation query
SELECT 
    'Consider index on dim_fp_buildingcustomdata(hmy_property)' as recommendation
UNION ALL
SELECT 'Consider index on dim_fp_buildingcustomdata(fund)' 
UNION ALL
SELECT 'Consider index on dim_fp_buildingcustomdata(market)'
UNION ALL
SELECT 'Consider index on dim_property([property hmy])';

-- Check 20: Summary statistics for validation
SELECT 
    'Total Properties' as metric,
    COUNT(*) as count
FROM dim_property
UNION ALL
SELECT 
    'Properties with Fund Data' as metric,
    COUNT(*) as count
FROM dim_fp_buildingcustomdata
WHERE fund IS NOT NULL
UNION ALL
SELECT 
    'Properties with Market Data' as metric,
    COUNT(*) as count
FROM dim_fp_buildingcustomdata
WHERE market IS NOT NULL
UNION ALL
SELECT 
    'Active Properties' as metric,
    COUNT(*) as count
FROM dim_fp_buildingcustomdata
WHERE status = 'Acquired'
UNION ALL
SELECT 
    'Unique Funds' as metric,
    COUNT(DISTINCT fund) as count
FROM dim_fp_buildingcustomdata
WHERE fund IS NOT NULL
UNION ALL
SELECT 
    'Unique Markets' as metric,
    COUNT(DISTINCT market) as count
FROM dim_fp_buildingcustomdata
WHERE market IS NOT NULL;

-- ============================================
-- VALIDATION CHECKLIST
-- ============================================
/*
Run these queries and verify:
1. [ ] All properties have corresponding building custom data
2. [ ] No duplicate hmy_property values in building data
3. [ ] Fund values are consistent and properly formatted
4. [ ] Market values are consistent and properly formatted  
5. [ ] Regional classifications are correct
6. [ ] Filter combinations return expected results
7. [ ] Counts match between SQL and Power BI
8. [ ] No orphaned records in either direction
9. [ ] Performance is acceptable for large datasets
10. [ ] All critical fields have non-null values where expected
*/