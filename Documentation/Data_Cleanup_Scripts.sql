-- =====================================================================
-- Data Cleanup Scripts for PowerBI Rent Roll Database Improvements
-- =====================================================================
-- Version: 1.0
-- Date: August 2025
-- Purpose: Resolve duplicate amendments, data integrity issues, and
--          prepare database for optimized PowerBI calculations
-- 
-- CRITICAL: Run these scripts in ORDER and verify results after each step
-- BACKUP: Always create backups before executing cleanup procedures
-- =====================================================================

-- =====================================================================
-- SECTION 1: PRE-EXECUTION SAFETY CHECKS AND BACKUPS
-- =====================================================================

-- Create backup timestamp
DO $$
BEGIN
    RAISE NOTICE 'Starting Data Cleanup - Timestamp: %', NOW();
    RAISE NOTICE 'Creating safety backups before cleanup execution...';
END $$;

-- Backup critical tables before any modifications
CREATE TABLE dim_fp_amendmentsunitspropertytenant_backup_20250809 AS
SELECT * FROM dim_fp_amendmentsunitspropertytenant;

CREATE TABLE dim_fp_amendmentchargeschedule_backup_20250809 AS
SELECT * FROM dim_fp_amendmentchargeschedule;

-- Verify backup integrity
DO $$
DECLARE
    original_count INTEGER;
    backup_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO original_count FROM dim_fp_amendmentsunitspropertytenant;
    SELECT COUNT(*) INTO backup_count FROM dim_fp_amendmentsunitspropertytenant_backup_20250809;
    
    IF original_count != backup_count THEN
        RAISE EXCEPTION 'BACKUP FAILED: Amendment table backup count mismatch';
    END IF;
    
    RAISE NOTICE 'Backup verification successful: % amendment records backed up', backup_count;
END $$;

-- =====================================================================
-- SECTION 2: DATA QUALITY ASSESSMENT BEFORE CLEANUP
-- =====================================================================

-- Assessment Report: Current state analysis
CREATE TEMP VIEW v_pre_cleanup_assessment AS
SELECT 
    'Duplicate Active Amendments' as issue_type,
    COUNT(*) as issue_count,
    'Property/Tenant combinations with multiple active amendments' as description
FROM (
    SELECT property_hmy, tenant_hmy, COUNT(*) as active_count
    FROM dim_fp_amendmentsunitspropertytenant 
    WHERE amendment_status = 'Activated'
    GROUP BY property_hmy, tenant_hmy
    HAVING COUNT(*) > 1
) duplicates

UNION ALL

SELECT 
    'Amendments Missing Rent Charges' as issue_type,
    COUNT(*) as issue_count,
    'Active amendments with SF > 0 but no rent charges' as description
FROM dim_fp_amendmentsunitspropertytenant a
LEFT JOIN (
    SELECT DISTINCT amendment_hmy 
    FROM dim_fp_amendmentchargeschedule 
    WHERE charge_code = 'rent'
) c ON a.amendment_hmy = c.amendment_hmy
WHERE a.amendment_status = 'Activated' 
AND a.amendment_sf > 0 
AND c.amendment_hmy IS NULL

UNION ALL

SELECT 
    'Invalid Date Sequences' as issue_type,
    COUNT(*) as issue_count,
    'Amendments with end date before start date' as description
FROM dim_fp_amendmentsunitspropertytenant 
WHERE amendment_end_date IS NOT NULL 
AND amendment_end_date < amendment_start_date

UNION ALL

SELECT 
    'Orphaned Charge Schedules' as issue_type,
    COUNT(*) as issue_count,
    'Charge schedules without corresponding amendments' as description
FROM dim_fp_amendmentchargeschedule c
LEFT JOIN dim_fp_amendmentsunitspropertytenant a ON c.amendment_hmy = a.amendment_hmy
WHERE a.amendment_hmy IS NULL;

-- Display pre-cleanup assessment
SELECT 
    issue_type,
    issue_count,
    description,
    CASE 
        WHEN issue_count = 0 THEN 'OK'
        WHEN issue_count > 0 AND issue_type LIKE '%Duplicate%' THEN 'CRITICAL'
        WHEN issue_count > 0 AND issue_type LIKE '%Missing%' THEN 'HIGH'
        ELSE 'MEDIUM'
    END as severity
FROM v_pre_cleanup_assessment
ORDER BY 
    CASE 
        WHEN issue_type LIKE '%Duplicate%' THEN 1
        WHEN issue_type LIKE '%Missing%' THEN 2
        WHEN issue_type LIKE '%Invalid%' THEN 3
        ELSE 4
    END;

-- =====================================================================
-- SECTION 3: DUPLICATE AMENDMENT RESOLUTION
-- =====================================================================

-- Step 3.1: Identify and log duplicate active amendments
DO $$
DECLARE
    duplicate_count INTEGER;
BEGIN
    -- Create temporary table to track duplicates for audit
    DROP TABLE IF EXISTS temp_duplicate_amendments_log;
    
    CREATE TEMP TABLE temp_duplicate_amendments_log AS
    SELECT 
        property_hmy,
        tenant_hmy,
        amendment_hmy,
        amendment_sequence,
        amendment_status,
        amendment_start_date,
        amendment_end_date,
        ROW_NUMBER() OVER (
            PARTITION BY property_hmy, tenant_hmy 
            ORDER BY amendment_sequence DESC, amendment_hmy DESC
        ) as keep_rank,
        'DUPLICATE_ACTIVE' as cleanup_reason
    FROM dim_fp_amendmentsunitspropertytenant 
    WHERE amendment_status = 'Activated'
    AND (property_hmy, tenant_hmy) IN (
        SELECT property_hmy, tenant_hmy
        FROM dim_fp_amendmentsunitspropertytenant 
        WHERE amendment_status = 'Activated'
        GROUP BY property_hmy, tenant_hmy
        HAVING COUNT(*) > 1
    );
    
    SELECT COUNT(*) INTO duplicate_count 
    FROM temp_duplicate_amendments_log 
    WHERE keep_rank > 1;
    
    RAISE NOTICE 'Found % duplicate active amendments to be superseded', duplicate_count;
END $$;

-- Step 3.2: Execute duplicate amendment cleanup
WITH amendments_to_supersede AS (
    SELECT amendment_hmy
    FROM temp_duplicate_amendments_log
    WHERE keep_rank > 1  -- Keep only the highest sequence, supersede others
)
UPDATE dim_fp_amendmentsunitspropertytenant 
SET 
    amendment_status = 'Superseded',
    amendment_status_code = 2,
    -- Add audit trail in notes
    amendment_notes = COALESCE(amendment_notes || ' | ', '') || 
                     'Auto-superseded on ' || CURRENT_DATE || ' due to duplicate active status'
WHERE amendment_hmy IN (SELECT amendment_hmy FROM amendments_to_supersede);

-- Step 3.3: Verification of duplicate cleanup
DO $$
DECLARE
    remaining_duplicates INTEGER;
BEGIN
    SELECT COUNT(*) INTO remaining_duplicates
    FROM (
        SELECT property_hmy, tenant_hmy, COUNT(*) as active_count
        FROM dim_fp_amendmentsunitspropertytenant 
        WHERE amendment_status = 'Activated'
        GROUP BY property_hmy, tenant_hmy
        HAVING COUNT(*) > 1
    ) x;
    
    IF remaining_duplicates > 0 THEN
        RAISE EXCEPTION 'CLEANUP FAILED: Still % duplicate active amendments remain', remaining_duplicates;
    ELSE
        RAISE NOTICE 'SUCCESS: All duplicate active amendments resolved';
    END IF;
END $$;

-- =====================================================================
-- SECTION 4: MISSING CHARGE SCHEDULE RESOLUTION
-- =====================================================================

-- Step 4.1: Analyze amendments missing charge schedules
CREATE TEMP VIEW v_amendments_missing_charges AS
SELECT 
    a.amendment_hmy,
    a.property_hmy,
    a.property_code,
    a.tenant_hmy,
    a.tenant_id,
    a.amendment_status,
    a.amendment_sf,
    a.amendment_start_date,
    a.amendment_end_date,
    COALESCE(c.charge_count, 0) as existing_charges,
    -- Business logic to determine if charge is expected
    CASE 
        WHEN a.amendment_sf > 0 AND a.amendment_status = 'Activated' THEN 'RENT_EXPECTED'
        WHEN a.amendment_sf > 0 AND a.amendment_status = 'Superseded' THEN 'HISTORICAL_RENT'
        WHEN a.amendment_sf = 0 AND a.amendment_type_code = 4 THEN 'TERMINATION_OK'
        WHEN a.amendment_sf = 0 AND a.amendment_type_code = 5 THEN 'HOLDOVER_REVIEW'
        ELSE 'REVIEW_REQUIRED'
    END as charge_expectation,
    -- Estimated rent based on property averages (for business review)
    ROUND(a.amendment_sf * prop_avg.avg_rent_psf / 12, 2) as estimated_monthly_rent
FROM dim_fp_amendmentsunitspropertytenant a
LEFT JOIN (
    SELECT 
        amendment_hmy,
        COUNT(*) as charge_count,
        SUM(CASE WHEN charge_code = 'rent' THEN 1 ELSE 0 END) as rent_charge_count
    FROM dim_fp_amendmentchargeschedule 
    GROUP BY amendment_hmy
) c ON a.amendment_hmy = c.amendment_hmy
LEFT JOIN (
    -- Property-level average rent PSF for estimation
    SELECT 
        a.property_hmy,
        AVG(cs.monthly_amount * 12.0 / NULLIF(a.amendment_sf, 0)) as avg_rent_psf
    FROM dim_fp_amendmentsunitspropertytenant a
    INNER JOIN dim_fp_amendmentchargeschedule cs ON a.amendment_hmy = cs.amendment_hmy
    WHERE cs.charge_code = 'rent' 
    AND a.amendment_sf > 0
    AND cs.monthly_amount > 0
    GROUP BY a.property_hmy
) prop_avg ON a.property_hmy = prop_avg.property_hmy
WHERE COALESCE(c.charge_count, 0) = 0;

-- Step 4.2: Generate business review report for missing charges
CREATE TEMP TABLE missing_charges_business_review AS
SELECT 
    charge_expectation,
    COUNT(*) as amendment_count,
    SUM(amendment_sf) as total_sf_affected,
    SUM(estimated_monthly_rent) as estimated_monthly_impact,
    STRING_AGG(DISTINCT property_code, ', ' ORDER BY property_code) as properties_affected
FROM v_amendments_missing_charges
GROUP BY charge_expectation
ORDER BY 
    CASE charge_expectation
        WHEN 'RENT_EXPECTED' THEN 1
        WHEN 'HISTORICAL_RENT' THEN 2
        WHEN 'REVIEW_REQUIRED' THEN 3
        WHEN 'HOLDOVER_REVIEW' THEN 4
        ELSE 5
    END;

-- Display missing charges analysis
SELECT 
    charge_expectation,
    amendment_count,
    ROUND(total_sf_affected, 0) as total_sf,
    ROUND(estimated_monthly_impact, 0) as est_monthly_rent,
    CASE 
        WHEN charge_expectation = 'RENT_EXPECTED' THEN 'CRITICAL - Active leases missing rent'
        WHEN charge_expectation = 'HISTORICAL_RENT' THEN 'HIGH - Historical data gaps'
        WHEN charge_expectation = 'TERMINATION_OK' THEN 'OK - Terminations expected to have no rent'
        ELSE 'REVIEW - Business logic validation needed'
    END as business_impact
FROM missing_charges_business_review;

-- Step 4.3: Create placeholder charges for critical missing rent (BUSINESS APPROVAL REQUIRED)
-- Note: This script creates $0 placeholder charges that require manual update with actual rates
/*
WARNING: The following INSERT statement creates placeholder charge records.
These placeholders are marked with $0 monthly amounts and require business 
review to populate with actual rent values.

BUSINESS ACTION REQUIRED:
1. Review the missing_charges_business_review table above
2. Obtain actual rent amounts for amendments marked as 'RENT_EXPECTED'
3. Update the placeholder records with correct rent amounts
4. Validate that all active amendments have appropriate charges

-- UNCOMMENT ONLY AFTER BUSINESS APPROVAL:

INSERT INTO dim_fp_amendmentchargeschedule (
    property_hmy, amendment_hmy, tenant_hmy, charge_code_hmy, charge_code, 
    charge_code_desc, amount_period_code, amount_period_desc, 
    from_date, to_date, amount, monthly_amount, contracted_area, 
    notes, dtcreated, dtlastmodified
)
SELECT 
    a.property_hmy,
    a.amendment_hmy,
    a.tenant_hmy,
    30, -- Standard rent charge code HMY
    'rent',
    'Rent - Base',
    2, -- Monthly period code
    'Monthly',
    a.amendment_start_date,
    a.amendment_end_date,
    0, -- PLACEHOLDER: Requires business review for actual amount
    0, -- PLACEHOLDER: Requires business review for actual amount
    a.amendment_sf,
    'SYSTEM GENERATED: Placeholder charge created during data cleanup. REQUIRES BUSINESS REVIEW FOR ACTUAL RENT AMOUNT.',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
FROM v_amendments_missing_charges a
WHERE a.charge_expectation = 'RENT_EXPECTED';

*/

-- =====================================================================
-- SECTION 5: DATA INTEGRITY FIXES
-- =====================================================================

-- Step 5.1: Fix invalid date sequences
UPDATE dim_fp_amendmentsunitspropertytenant 
SET amendment_end_date = NULL,
    amendment_notes = COALESCE(amendment_notes || ' | ', '') || 
                     'End date cleared on ' || CURRENT_DATE || ' due to invalid date sequence'
WHERE amendment_end_date IS NOT NULL 
AND amendment_end_date < amendment_start_date;

-- Step 5.2: Clean up orphaned charge schedules
-- Log orphaned charges before deletion
CREATE TEMP TABLE orphaned_charges_log AS
SELECT 
    c.*,
    'ORPHANED_AMENDMENT' as cleanup_reason,
    CURRENT_TIMESTAMP as cleanup_timestamp
FROM dim_fp_amendmentchargeschedule c
LEFT JOIN dim_fp_amendmentsunitspropertytenant a ON c.amendment_hmy = a.amendment_hmy
WHERE a.amendment_hmy IS NULL;

-- Delete orphaned charge schedules
DELETE FROM dim_fp_amendmentchargeschedule 
WHERE amendment_hmy IN (
    SELECT c.amendment_hmy 
    FROM dim_fp_amendmentchargeschedule c
    LEFT JOIN dim_fp_amendmentsunitspropertytenant a ON c.amendment_hmy = a.amendment_hmy
    WHERE a.amendment_hmy IS NULL
);

-- =====================================================================
-- SECTION 6: POST-CLEANUP VALIDATION AND REPORTING
-- =====================================================================

-- Step 6.1: Post-cleanup data quality assessment
CREATE TEMP VIEW v_post_cleanup_assessment AS
SELECT 
    'Duplicate Active Amendments' as issue_type,
    COUNT(*) as issue_count,
    'RESOLVED' as status
FROM (
    SELECT property_hmy, tenant_hmy, COUNT(*) as active_count
    FROM dim_fp_amendmentsunitspropertytenant 
    WHERE amendment_status = 'Activated'
    GROUP BY property_hmy, tenant_hmy
    HAVING COUNT(*) > 1
) duplicates

UNION ALL

SELECT 
    'Invalid Date Sequences' as issue_type,
    COUNT(*) as issue_count,
    'RESOLVED' as status
FROM dim_fp_amendmentsunitspropertytenant 
WHERE amendment_end_date IS NOT NULL 
AND amendment_end_date < amendment_start_date

UNION ALL

SELECT 
    'Orphaned Charge Schedules' as issue_type,
    COUNT(*) as issue_count,
    'RESOLVED' as status
FROM dim_fp_amendmentchargeschedule c
LEFT JOIN dim_fp_amendmentsunitspropertytenant a ON c.amendment_hmy = a.amendment_hmy
WHERE a.amendment_hmy IS NULL

UNION ALL

SELECT 
    'Amendments Still Missing Charges' as issue_type,
    COUNT(*) as issue_count,
    'REQUIRES_BUSINESS_REVIEW' as status
FROM dim_fp_amendmentsunitspropertytenant a
LEFT JOIN (
    SELECT DISTINCT amendment_hmy 
    FROM dim_fp_amendmentchargeschedule 
    WHERE charge_code = 'rent'
) c ON a.amendment_hmy = c.amendment_hmy
WHERE a.amendment_status = 'Activated' 
AND a.amendment_sf > 0 
AND c.amendment_hmy IS NULL;

-- Step 6.2: Generate cleanup summary report
DO $$
DECLARE
    amendments_superseded INTEGER;
    charges_orphaned INTEGER;
    dates_fixed INTEGER;
BEGIN
    -- Count actions taken
    SELECT COUNT(*) INTO amendments_superseded 
    FROM dim_fp_amendmentsunitspropertytenant 
    WHERE amendment_notes LIKE '%Auto-superseded%';
    
    SELECT COUNT(*) INTO charges_orphaned 
    FROM orphaned_charges_log;
    
    SELECT COUNT(*) INTO dates_fixed
    FROM dim_fp_amendmentsunitspropertytenant 
    WHERE amendment_notes LIKE '%End date cleared%';
    
    -- Summary report
    RAISE NOTICE '';
    RAISE NOTICE '========== DATA CLEANUP SUMMARY REPORT ==========';
    RAISE NOTICE 'Cleanup completed at: %', NOW();
    RAISE NOTICE '';
    RAISE NOTICE 'ACTIONS TAKEN:';
    RAISE NOTICE '  - Amendments superseded (duplicates): %', amendments_superseded;
    RAISE NOTICE '  - Invalid dates fixed: %', dates_fixed;
    RAISE NOTICE '  - Orphaned charges removed: %', charges_orphaned;
    RAISE NOTICE '';
    RAISE NOTICE 'BUSINESS REVIEW REQUIRED:';
    RAISE NOTICE '  - Check missing_charges_business_review table';
    RAISE NOTICE '  - Populate placeholder charge amounts if created';
    RAISE NOTICE '  - Validate active amendments have appropriate charges';
    RAISE NOTICE '';
    RAISE NOTICE 'NEXT STEPS:';
    RAISE NOTICE '  1. Run Schema_Enhancement_DDL.sql for performance improvements';
    RAISE NOTICE '  2. Implement data validation framework';
    RAISE NOTICE '  3. Update PowerBI measures with latest amendment logic';
    RAISE NOTICE '================================================';
END $$;

-- Display final validation results
SELECT 
    issue_type,
    issue_count,
    status,
    CASE 
        WHEN issue_count = 0 AND status = 'RESOLVED' THEN 'SUCCESS'
        WHEN status = 'REQUIRES_BUSINESS_REVIEW' THEN 'ACTION_NEEDED'
        ELSE 'CHECK_REQUIRED'
    END as result
FROM v_post_cleanup_assessment
ORDER BY 
    CASE status
        WHEN 'REQUIRES_BUSINESS_REVIEW' THEN 1
        WHEN 'RESOLVED' THEN 2
        ELSE 3
    END;

-- =====================================================================
-- SECTION 7: ROLLBACK PROCEDURES (IN CASE OF EMERGENCY)
-- =====================================================================

/*
EMERGENCY ROLLBACK INSTRUCTIONS:

If issues are discovered after cleanup execution, use these commands to restore:

-- Step 1: Restore amendment table from backup
DROP TABLE IF EXISTS dim_fp_amendmentsunitspropertytenant_rollback_temp;
ALTER TABLE dim_fp_amendmentsunitspropertytenant RENAME TO dim_fp_amendmentsunitspropertytenant_rollback_temp;
ALTER TABLE dim_fp_amendmentsunitspropertytenant_backup_20250809 RENAME TO dim_fp_amendmentsunitspropertytenant;

-- Step 2: Restore charge schedule table from backup
DROP TABLE IF EXISTS dim_fp_amendmentchargeschedule_rollback_temp;
ALTER TABLE dim_fp_amendmentchargeschedule RENAME TO dim_fp_amendmentchargeschedule_rollback_temp;
ALTER TABLE dim_fp_amendmentchargeschedule_backup_20250809 RENAME TO dim_fp_amendmentchargeschedule;

-- Step 3: Verify rollback success
SELECT COUNT(*) as amendment_count FROM dim_fp_amendmentsunitspropertytenant;
SELECT COUNT(*) as charge_count FROM dim_fp_amendmentchargeschedule;

IMPORTANT: After rollback, investigate the cause of issues before re-attempting cleanup.
Contact the database administrator if rollback is required.
*/

-- =====================================================================
-- END OF DATA CLEANUP SCRIPTS
-- =====================================================================

-- Final checkpoint
DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '*** DATA CLEANUP SCRIPTS COMPLETED SUCCESSFULLY ***';
    RAISE NOTICE 'Review the output above for any business actions required.';
    RAISE NOTICE 'Proceed to Schema Enhancement DDL for performance improvements.';
    RAISE NOTICE '';
END $$;