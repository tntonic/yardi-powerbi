-- ============================================
-- Phase 1: Data Model Validation Scripts
-- ============================================
-- Purpose: Validate table structures, keys, and relationships
-- Target: 32 tables in Yardi BI data model
-- Author: Validation Team
-- Date: 2025-08-08
-- ============================================

-- ============================================
-- 1.1 TABLE STRUCTURE VALIDATION
-- ============================================

-- Check all required tables exist
WITH required_tables AS (
    SELECT table_name FROM (VALUES 
        -- Dimension Tables (22)
        ('dim_property'),
        ('dim_unit'),
        ('dim_account'),
        ('dim_accounttree'),
        ('dim_accounttreeaccountmapping'),
        ('dim_book'),
        ('dim_date'),
        ('dim_commcustomer'),
        ('dim_commlease'),
        ('dim_commleasetype'),
        ('dim_fp_amendmentsunitspropertytenant'),
        ('dim_fp_amendmentchargeschedule'),
        ('dim_fp_chargecodetypeandgl'),
        ('dim_fp_buildingcustomdata'),
        ('dim_moveoutreasons'),
        ('dim_newleasereason'),
        ('dim_renewalreason'),
        ('dim_tenant'),
        ('dim_unittypelist'),
        ('dim_assetstatus'),
        ('dim_marketsegment'),
        ('dim_yearbuiltcategory'),
        
        -- Fact Tables (6)
        ('fact_total'),
        ('fact_occupancyrentarea'),
        ('fact_expiringleaseunitarea'),
        ('fact_accountsreceivable'),
        ('fact_leasingactivity'),
        ('fact_marketrentsurvey'),
        
        -- Specialized Tables (4)
        ('bridge_propertymarkets'),
        ('external_market_growth_projections'),
        ('ref_book_override_logic'),
        ('control_active_scenario')
    ) AS t(table_name)
),
existing_tables AS (
    SELECT LOWER(table_name) as table_name
    FROM information_schema.tables 
    WHERE table_schema = 'dbo'
)
SELECT 
    rt.table_name,
    CASE WHEN et.table_name IS NOT NULL THEN 'EXISTS' ELSE 'MISSING' END as status
FROM required_tables rt
LEFT JOIN existing_tables et ON rt.table_name = et.table_name
ORDER BY status DESC, rt.table_name;

-- ============================================
-- 1.2 PRIMARY KEY VALIDATION
-- ============================================

-- Validate primary keys for critical tables
SELECT 
    t.table_name,
    c.column_name as primary_key,
    CASE 
        WHEN c.column_name IS NOT NULL THEN 'DEFINED'
        ELSE 'MISSING'
    END as pk_status
FROM (
    SELECT 'dim_property' as table_name, 'property id' as expected_key
    UNION ALL SELECT 'dim_unit', 'unit id'
    UNION ALL SELECT 'dim_account', 'account id'
    UNION ALL SELECT 'dim_book', 'book id'
    UNION ALL SELECT 'dim_date', 'date'
    UNION ALL SELECT 'dim_commcustomer', 'tenant id'
    UNION ALL SELECT 'dim_fp_amendmentsunitspropertytenant', 'amendment hmy'
) t
LEFT JOIN information_schema.key_column_usage c
    ON LOWER(t.table_name) = LOWER(c.table_name)
    AND c.constraint_name LIKE '%PK%'
ORDER BY pk_status DESC, t.table_name;

-- ============================================
-- 1.3 DATA TYPE VALIDATION
-- ============================================

-- Check critical column data types
WITH expected_columns AS (
    SELECT table_name, column_name, data_type FROM (VALUES
        -- dim_property critical columns
        ('dim_property', 'property id', 'int'),
        ('dim_property', 'property code', 'varchar'),
        ('dim_property', 'property name', 'varchar'),
        ('dim_property', 'is active', 'bit'),
        ('dim_property', 'acquire date', 'datetime'),
        
        -- fact_total critical columns
        ('fact_total', 'property id', 'int'),
        ('fact_total', 'book id', 'int'),
        ('fact_total', 'account id', 'int'),
        ('fact_total', 'month', 'datetime'),
        ('fact_total', 'amount', 'decimal'),
        
        -- Amendment table critical columns
        ('dim_fp_amendmentsunitspropertytenant', 'amendment hmy', 'int'),
        ('dim_fp_amendmentsunitspropertytenant', 'property hmy', 'int'),
        ('dim_fp_amendmentsunitspropertytenant', 'tenant hmy', 'int'),
        ('dim_fp_amendmentsunitspropertytenant', 'amendment sequence', 'int'),
        ('dim_fp_amendmentsunitspropertytenant', 'amendment status', 'varchar')
    ) AS t(table_name, column_name, data_type)
)
SELECT 
    e.table_name,
    e.column_name,
    e.data_type as expected_type,
    c.data_type as actual_type,
    CASE 
        WHEN c.data_type LIKE '%' + e.data_type + '%' THEN 'MATCH'
        ELSE 'MISMATCH'
    END as validation_status
FROM expected_columns e
LEFT JOIN information_schema.columns c
    ON LOWER(e.table_name) = LOWER(c.table_name)
    AND LOWER(e.column_name) = LOWER(c.column_name)
ORDER BY validation_status DESC, e.table_name, e.column_name;

-- ============================================
-- 1.4 RELATIONSHIP INTEGRITY TESTING
-- ============================================

-- Test for orphaned records in fact_total
SELECT 
    'fact_total -> dim_property' as relationship,
    COUNT(*) as total_records,
    COUNT(DISTINCT f.[property id]) as distinct_properties,
    SUM(CASE WHEN p.[property id] IS NULL THEN 1 ELSE 0 END) as orphaned_records,
    CAST(SUM(CASE WHEN p.[property id] IS NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS DECIMAL(5,2)) as orphaned_pct
FROM fact_total f
LEFT JOIN dim_property p ON f.[property id] = p.[property id];

-- Test for orphaned records in fact_total (accounts)
SELECT 
    'fact_total -> dim_account' as relationship,
    COUNT(*) as total_records,
    COUNT(DISTINCT f.[account id]) as distinct_accounts,
    SUM(CASE WHEN a.[account id] IS NULL THEN 1 ELSE 0 END) as orphaned_records,
    CAST(SUM(CASE WHEN a.[account id] IS NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS DECIMAL(5,2)) as orphaned_pct
FROM fact_total f
LEFT JOIN dim_account a ON f.[account id] = a.[account id];

-- Test for orphaned records in fact_total (books)
SELECT 
    'fact_total -> dim_book' as relationship,
    COUNT(*) as total_records,
    COUNT(DISTINCT f.[book id]) as distinct_books,
    SUM(CASE WHEN b.[book id] IS NULL THEN 1 ELSE 0 END) as orphaned_records,
    CAST(SUM(CASE WHEN b.[book id] IS NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS DECIMAL(5,2)) as orphaned_pct
FROM fact_total f
LEFT JOIN dim_book b ON f.[book id] = b.[book id];

-- Test amendment relationships
SELECT 
    'amendments -> dim_property' as relationship,
    COUNT(*) as total_amendments,
    COUNT(DISTINCT a.[property hmy]) as distinct_properties,
    SUM(CASE WHEN p.[property hmy] IS NULL THEN 1 ELSE 0 END) as orphaned_records,
    CAST(SUM(CASE WHEN p.[property hmy] IS NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS DECIMAL(5,2)) as orphaned_pct
FROM dim_fp_amendmentsunitspropertytenant a
LEFT JOIN dim_property p ON a.[property hmy] = p.[property hmy];

-- ============================================
-- 1.5 AMENDMENT TABLE VALIDATION
-- ============================================

-- Validate amendment sequences and statuses
SELECT 
    [amendment status],
    COUNT(*) as record_count,
    COUNT(DISTINCT [property hmy]) as property_count,
    COUNT(DISTINCT [tenant hmy]) as tenant_count,
    MIN([amendment sequence]) as min_sequence,
    MAX([amendment sequence]) as max_sequence,
    AVG(CAST([amendment sequence] AS FLOAT)) as avg_sequence
FROM dim_fp_amendmentsunitspropertytenant
GROUP BY [amendment status]
ORDER BY record_count DESC;

-- Check for duplicate latest amendments
WITH latest_amendments AS (
    SELECT 
        [property hmy],
        [tenant hmy],
        MAX([amendment sequence]) as max_sequence,
        COUNT(*) as amendment_count
    FROM dim_fp_amendmentsunitspropertytenant
    WHERE [amendment status] IN ('Activated', 'Superseded')
    GROUP BY [property hmy], [tenant hmy]
    HAVING COUNT(*) > 1
)
SELECT 
    COUNT(*) as duplicate_latest_count,
    COUNT(DISTINCT [property hmy]) as affected_properties,
    COUNT(DISTINCT [tenant hmy]) as affected_tenants
FROM latest_amendments;

-- ============================================
-- 1.6 TABLE GRANULARITY VALIDATION
-- ============================================

-- Validate fact_total granularity
SELECT 
    'fact_total' as table_name,
    COUNT(*) as total_records,
    COUNT(DISTINCT CONCAT([property id], '|', [book id], '|', [account id], '|', FORMAT([month], 'yyyy-MM'), '|', [amount type])) as unique_combinations,
    CASE 
        WHEN COUNT(*) = COUNT(DISTINCT CONCAT([property id], '|', [book id], '|', [account id], '|', FORMAT([month], 'yyyy-MM'), '|', [amount type]))
        THEN 'CORRECT GRAIN'
        ELSE 'DUPLICATE RECORDS'
    END as grain_status
FROM fact_total;

-- Validate fact_occupancyrentarea granularity
SELECT 
    'fact_occupancyrentarea' as table_name,
    COUNT(*) as total_records,
    COUNT(DISTINCT CONCAT([property id], '|', FORMAT([first day of month], 'yyyy-MM'), '|', ISNULL(CAST([lease type id] AS VARCHAR), 'NULL'))) as unique_combinations,
    CASE 
        WHEN COUNT(*) = COUNT(DISTINCT CONCAT([property id], '|', FORMAT([first day of month], 'yyyy-MM'), '|', ISNULL(CAST([lease type id] AS VARCHAR), 'NULL')))
        THEN 'CORRECT GRAIN'
        ELSE 'DUPLICATE RECORDS'
    END as grain_status
FROM fact_occupancyrentarea;

-- ============================================
-- 1.7 DATE DIMENSION VALIDATION
-- ============================================

-- Validate date dimension coverage
SELECT 
    MIN([date]) as earliest_date,
    MAX([date]) as latest_date,
    COUNT(DISTINCT [date]) as total_days,
    COUNT(DISTINCT [year]) as year_count,
    COUNT(DISTINCT CONCAT([year], '-', [month])) as month_count,
    CASE 
        WHEN MIN([date]) <= '2020-01-01' AND MAX([date]) >= '2025-12-31' THEN 'ADEQUATE COVERAGE'
        ELSE 'INSUFFICIENT COVERAGE'
    END as coverage_status
FROM dim_date;

-- ============================================
-- 1.8 SUMMARY VALIDATION REPORT
-- ============================================

-- Create summary validation results
WITH validation_summary AS (
    SELECT 'Table Count' as check_type, 
           CAST(COUNT(*) AS VARCHAR) as result,
           CASE WHEN COUNT(*) = 32 THEN 'PASS' ELSE 'FAIL' END as status
    FROM information_schema.tables 
    WHERE table_schema = 'dbo' 
    AND table_name LIKE 'dim_%' OR table_name LIKE 'fact_%'
    
    UNION ALL
    
    SELECT 'Orphaned Records', 
           CAST(SUM(orphaned_count) AS VARCHAR) as result,
           CASE WHEN SUM(orphaned_count) = 0 THEN 'PASS' ELSE 'FAIL' END as status
    FROM (
        SELECT COUNT(*) as orphaned_count 
        FROM fact_total f
        LEFT JOIN dim_property p ON f.[property id] = p.[property id]
        WHERE p.[property id] IS NULL
    ) o
)
SELECT 
    check_type,
    result,
    status,
    CASE 
        WHEN status = 'PASS' THEN '✅'
        ELSE '❌'
    END as indicator
FROM validation_summary
ORDER BY status DESC, check_type;