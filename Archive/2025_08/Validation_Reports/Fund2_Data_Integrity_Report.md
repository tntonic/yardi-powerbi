# Fund 2 Data Integrity Validation Report

**Report Date:** August 9, 2025  
**Validation Scope:** Fund 2 Properties (32-table Yardi PowerBI Data Model)  
**Data Quality Score:** 66/100 - **POOR** - Major data integrity issues require immediate attention  

---

## Executive Summary

The comprehensive data integrity validation of Fund 2 properties has identified **critical issues** that will significantly impact rent roll accuracy and occupancy calculations. While the data model structure is sound with no orphaned records, there are **4 major issues** requiring immediate remediation before production deployment.

### Critical Success Metrics Status
| Metric | Target | Current | Status |
|--------|---------|---------|--------|
| Data Integrity Score | 95+ | 66 | ❌ FAIL |
| Orphaned Records | <1% | 0% | ✅ PASS |
| Duplicate Active Amendments | 0 | 98 combinations | ❌ FAIL |
| Invalid Amendment Statuses | 0 | 1 | ❌ FAIL |
| Missing Critical Dates | <1% | 6/7,837 (0.08%) | ✅ PASS |

---

## Data Scope Overview

### Fund 2 Data Volume
- **Properties:** 195 (171 active, 24 inactive)
- **Amendments:** 877 total (536 activated, 340 superseded, 1 invalid)
- **Active Charges:** 1,084 charges
- **Total Charges:** 7,837 charges  
- **Units:** 387 units
- **Tenants:** 417 tenants

### Data Model Integrity ✅
- **No orphaned records** found in key tables
- **100% referential integrity** between amendments and charges
- **All Fund 2 properties** properly identified (codes starting with 'x')
- **Relationship validation** passed across all 32-table architecture

---

## Critical Issues Identified

### 🚨 ISSUE #1: Duplicate Active Amendments (CRITICAL)
**Impact Level:** HIGH - Direct rent roll calculation errors

#### Problem Details
- **98 property/tenant combinations** have multiple active amendments
- **119 extra amendment records** will inflate rent roll calculations
- **Average 2.2 active amendments** per problematic combination

#### Top 10 Most Problematic Cases
| Property Code | Tenant ID | Active Amendments | Amendment Sequences |
|---------------|-----------|------------------|-------------------|
| xil1701b | t0000921 | 4 | [1, 4, 2, 3] |
| xohmost | t0000434 | 3 | [1, 2, 3] |
| xohmost | t0001072 | 3 | [0, 1, 2] |
| xnjmway5 | t0000495 | 3 | [0, 1, 2] |
| xil1600 | t0000514 | 3 | [0, 1, 2] |

#### Business Impact
- **Rent roll totals will be inflated** by counting same tenant multiple times
- **Occupancy percentages will be incorrect** due to duplicate space calculations
- **NOI calculations will be overstated** from duplicate revenue
- **Leasing activity metrics will be skewed**

#### Root Cause Analysis
This violates the core business rule that **only one amendment should be "Activated"** per property/tenant combination at any time. Multiple active amendments indicate:
1. Improper amendment lifecycle management
2. Missing business logic validation
3. Potential data entry process issues

#### Immediate Remediation Required
```sql
-- Identify all property/tenant combinations with multiple active amendments
SELECT property_hmy, tenant_hmy, COUNT(*) as active_count
FROM dim_fp_amendmentsunitspropertytenant 
WHERE amendment_status = 'Activated'
GROUP BY property_hmy, tenant_hmy
HAVING COUNT(*) > 1;

-- Fix: Change all but the latest sequence to 'Superseded'
UPDATE dim_fp_amendmentsunitspropertytenant 
SET amendment_status = 'Superseded'
WHERE amendment_status = 'Activated'
  AND amendment_sequence < (
    SELECT MAX(amendment_sequence) 
    FROM dim_fp_amendmentsunitspropertytenant t2
    WHERE t2.property_hmy = dim_fp_amendmentsunitspropertytenant.property_hmy
      AND t2.tenant_hmy = dim_fp_amendmentsunitspropertytenant.tenant_hmy
      AND t2.amendment_status = 'Activated'
  );
```

---

### 🚨 ISSUE #2: Invalid Amendment Status (CRITICAL)
**Impact Level:** MEDIUM - DAX calculation compatibility

#### Problem Details
- **1 amendment** with invalid status "In Process"
- **Valid statuses:** Activated, Superseded, Cancelled, Pending
- **Property:** xga4225, Tenant: t0000778, Type: "Proposal in DM"

#### Business Impact
- DAX measures filtering on valid statuses will exclude this record
- Rent roll calculations may be incomplete
- Status inconsistency affects reporting accuracy

#### Immediate Remediation
```sql
-- Review and fix invalid status
SELECT * FROM dim_fp_amendmentsunitspropertytenant 
WHERE amendment_status NOT IN ('Activated', 'Superseded', 'Cancelled', 'Pending');

-- Likely fix: Change 'In Process' to 'Pending' or 'Activated' based on business rules
UPDATE dim_fp_amendmentsunitspropertytenant 
SET amendment_status = 'Pending'  -- or 'Activated' based on review
WHERE amendment_status = 'In Process';
```

---

### ⚠️ ISSUE #3: Missing Charge Dates (MINOR)
**Impact Level:** LOW - Minimal impact on rent roll

#### Problem Details
- **6 charges** missing "to date" values (out of 7,837 total)
- **0 charges** missing "from date" values  
- **Date format:** Excel serial numbers (e.g., 44228 = specific date)

#### Business Impact
- Charges without end dates may be included indefinitely in calculations
- Minor impact on time-based rent calculations

#### Remediation
Review the 6 charges with missing end dates and populate appropriate values based on lease terms.

---

### ⚠️ ISSUE #4: Amendments Without Rent Charges (WARNING)
**Impact Level:** MEDIUM - Potential rent roll incompleteness

#### Problem Details
- **634 amendments** (72%) have no associated rent charges
- **243 amendments** (28%) have rent charges totaling $5.2M monthly
- This may be intentional for certain amendment types

#### Analysis Required
Determine if amendments without rent charges are:
1. **Intentional:** Non-rent amendments (expense recovery, parking, etc.)
2. **Missing data:** Rent charges not properly linked
3. **Incomplete setup:** Amendments pending charge schedule creation

#### Validation Query
```sql
-- Identify amendment types without rent charges
SELECT a.amendment_type, COUNT(*) as count_without_rent
FROM dim_fp_amendmentsunitspropertytenant a
LEFT JOIN dim_fp_amendmentchargeschedule c ON a.amendment_hmy = c.amendment_hmy 
  AND c.charge_code_desc LIKE '%Rent%'
WHERE c.amendment_hmy IS NULL
GROUP BY a.amendment_type
ORDER BY count_without_rent DESC;
```

---

## Relationship Validation Results ✅

### Table Relationship Integrity
All critical relationships validated successfully:

#### Property Relationships
- **195 Fund 2 properties** properly identified (100% start with 'x')
- **0 orphaned amendments** - all reference valid properties
- **Property-to-amendment links:** 100% integrity

#### Amendment-to-Charges Relationships  
- **0 orphaned charges** - all reference valid amendments
- **1,084 active charges** properly linked to amendments
- **7,837 total charges** with valid amendment references

#### Data Quality Summary by Table
| Table | Records | Columns | Missing Data Issues | Duplicate Records |
|-------|---------|---------|-------------------|-------------------|
| Properties | 195 | 16 | 4 columns | 0 |
| Amendments | 877 | 22 | 7 columns | 0 |
| Active Charges | 1,084 | 39 | 4 columns | 0 |
| Units | 387 | 14 | 8 columns | 0 |
| Tenants | 417 | 2 | 0 columns | 0 |

---

## Business Rule Validation

### Amendment-Based Rent Roll Logic
The validation confirmed critical business rules for rent roll accuracy:

#### ✅ Passed Validations
- Amendment sequence logic structure intact
- Property/tenant combination tracking works
- Charge schedule linking functional
- Date conversion format identified (Excel serial)

#### ❌ Failed Validations  
- **Multiple active amendments per property/tenant** (98 violations)
- **Incomplete rent charge coverage** (634/877 = 72% without rent)

### Calendar Relationship Status
- **Bi-directional Calendar relationships:** Not validated in this scope
- **Time intelligence compatibility:** Requires separate validation
- **Date filtering integrity:** Affected by Excel serial date format

---

## Impact on Rent Roll Calculations

### Accuracy Impact Assessment
The identified issues will have the following impacts on rent roll calculations:

#### Rent Roll Inflation (CRITICAL)
- **119 duplicate amendment records** will inflate rent totals
- **Multiple active amendments** cause same tenant to be counted multiple times
- **Estimated accuracy impact:** -15% to -25% from actual

#### Completeness Impact (MEDIUM)
- **634 amendments without rent charges** may indicate missing rent data
- If these should have rent charges, rent roll will be understated
- **Estimated completeness impact:** Unknown until business rule clarification

#### Technical Implementation Impact
- **DAX measures** filtering on amendment status will work correctly after fixes
- **Latest amendment sequence logic** will function properly after duplicate resolution
- **Time intelligence** may need adjustment for Excel serial date format

---

## Remediation Action Plan

### 🚨 PRIORITY 1: IMMEDIATE CRITICAL FIXES (24-48 hours)

#### Action 1.1: Fix Duplicate Active Amendments
```sql
-- Step 1: Identify all duplicates
CREATE TEMP TABLE duplicate_amendments AS
SELECT property_hmy, tenant_hmy, 
       MAX(amendment_sequence) as latest_sequence
FROM dim_fp_amendmentsunitspropertytenant 
WHERE amendment_status = 'Activated'
GROUP BY property_hmy, tenant_hmy
HAVING COUNT(*) > 1;

-- Step 2: Change older sequences to Superseded
UPDATE dim_fp_amendmentsunitspropertytenant 
SET amendment_status = 'Superseded',
    amendment_status_code = 2  -- Superseded status code
WHERE amendment_status = 'Activated'
  AND (property_hmy, tenant_hmy, amendment_sequence) IN (
    SELECT d.property_hmy, d.tenant_hmy, a.amendment_sequence
    FROM duplicate_amendments d
    JOIN dim_fp_amendmentsunitspropertytenant a 
      ON d.property_hmy = a.property_hmy 
      AND d.tenant_hmy = a.tenant_hmy
    WHERE a.amendment_sequence < d.latest_sequence
      AND a.amendment_status = 'Activated'
  );

-- Step 3: Validation check
SELECT COUNT(*) as remaining_duplicates
FROM (
  SELECT property_hmy, tenant_hmy, COUNT(*) as cnt
  FROM dim_fp_amendmentsunitspropertytenant 
  WHERE amendment_status = 'Activated'
  GROUP BY property_hmy, tenant_hmy
  HAVING COUNT(*) > 1
) x;
-- Should return 0
```

#### Action 1.2: Fix Invalid Amendment Status
```sql
-- Review the invalid status amendment
SELECT * FROM dim_fp_amendmentsunitspropertytenant 
WHERE amendment_status = 'In Process';

-- Fix based on business review (likely 'Pending' or 'Activated')
UPDATE dim_fp_amendmentsunitspropertytenant 
SET amendment_status = 'Pending',    -- Confirm with business
    amendment_status_code = 3        -- Pending status code
WHERE amendment_status = 'In Process';
```

### ⚠️ PRIORITY 2: DATA QUALITY IMPROVEMENTS (1-2 weeks)

#### Action 2.1: Investigate Amendments Without Rent
```sql
-- Analysis query to understand amendment types without rent
SELECT 
    a.amendment_type,
    a.amendment_status,
    COUNT(*) as amendments_without_rent,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM dim_fp_amendmentsunitspropertytenant), 2) as percentage
FROM dim_fp_amendmentsunitspropertytenant a
LEFT JOIN (
    SELECT DISTINCT amendment_hmy 
    FROM dim_fp_amendmentchargeschedule 
    WHERE charge_code_desc ILIKE '%rent%'
) c ON a.amendment_hmy = c.amendment_hmy
WHERE c.amendment_hmy IS NULL
GROUP BY a.amendment_type, a.amendment_status
ORDER BY amendments_without_rent DESC;
```

#### Action 2.2: Fix Missing Charge Dates
```sql
-- Identify charges with missing to_date
SELECT property_code, amendment_hmy, charge_code_desc, from_date, to_date, amount
FROM dim_fp_amendmentchargeschedule 
WHERE to_date IS NULL;

-- Business review required to populate proper end dates
```

### 📊 PRIORITY 3: PREVENTIVE CONTROLS (2-4 weeks)

#### Control 3.1: Data Validation Rules
Implement database constraints:
```sql
-- Prevent multiple active amendments per property/tenant
CREATE UNIQUE INDEX idx_unique_active_amendments 
ON dim_fp_amendmentsunitspropertytenant (property_hmy, tenant_hmy)
WHERE amendment_status = 'Activated';

-- Valid status constraint
ALTER TABLE dim_fp_amendmentsunitspropertytenant 
ADD CONSTRAINT chk_valid_amendment_status 
CHECK (amendment_status IN ('Activated', 'Superseded', 'Cancelled', 'Pending'));

-- Date range validation
ALTER TABLE dim_fp_amendmentchargeschedule 
ADD CONSTRAINT chk_valid_date_range 
CHECK (from_date <= to_date);
```

#### Control 3.2: Ongoing Monitoring
```sql
-- Weekly data integrity check queries
-- Check 1: Duplicate active amendments
SELECT COUNT(*) as duplicate_combinations
FROM (
    SELECT property_hmy, tenant_hmy
    FROM dim_fp_amendmentsunitspropertytenant 
    WHERE amendment_status = 'Activated'
    GROUP BY property_hmy, tenant_hmy
    HAVING COUNT(*) > 1
) x;

-- Check 2: Invalid statuses
SELECT amendment_status, COUNT(*)
FROM dim_fp_amendmentsunitspropertytenant
WHERE amendment_status NOT IN ('Activated', 'Superseded', 'Cancelled', 'Pending')
GROUP BY amendment_status;

-- Check 3: Date integrity
SELECT COUNT(*) as invalid_date_ranges
FROM dim_fp_amendmentchargeschedule 
WHERE from_date > to_date;
```

---

## Post-Remediation Validation Plan

### Validation Checklist
After implementing fixes, validate the following:

#### ✅ Data Integrity Validation
- [ ] **Zero duplicate active amendments** per property/tenant combination
- [ ] **All amendment statuses valid** (Activated, Superseded, Cancelled, Pending)
- [ ] **Date ranges valid** (from_date ≤ to_date)
- [ ] **Rent roll totals match** expected business values
- [ ] **DAX measures execute** without errors

#### ✅ Rent Roll Accuracy Testing
- [ ] **Generate test rent roll** for specific date (e.g., 6/30/2025)
- [ ] **Compare with Yardi native report** (target 95-99% accuracy)
- [ ] **Validate occupancy calculations** show realistic percentages
- [ ] **Confirm amendment sequence logic** returns latest amendments only

#### ✅ Performance Validation
- [ ] **Dashboard load times** < 10 seconds
- [ ] **Data refresh times** < 30 minutes
- [ ] **Query response times** < 5 seconds for user interactions

---

## Expected Outcomes

### After Full Remediation
- **Data Integrity Score:** 95+ (vs current 66)
- **Rent Roll Accuracy:** 95-99% vs Yardi native reports
- **Duplicate Active Amendments:** 0 (vs current 98)
- **Invalid Amendment Statuses:** 0 (vs current 1)
- **Ready for Production Deployment**

### Business Value Recovery
- **Accurate rent roll calculations** for financial reporting
- **Correct occupancy metrics** for portfolio management
- **Reliable leasing activity data** for operational decisions
- **Trustworthy PowerBI dashboards** for executive reporting

---

## Conclusion and Next Steps

The Fund 2 data integrity validation has identified critical issues that **must be resolved** before production deployment. While the underlying data model architecture is sound, the **duplicate active amendments** represent a significant threat to rent roll accuracy.

### Immediate Actions Required
1. **Execute Priority 1 fixes** within 24-48 hours
2. **Re-run validation** to confirm issue resolution
3. **Test rent roll calculations** against known good data
4. **Implement preventive controls** to avoid future issues

### Success Criteria
The Fund 2 data will be considered **production-ready** when:
- Data Integrity Score ≥ 95
- Zero duplicate active amendments
- Rent roll accuracy ≥ 95% vs Yardi native reports
- All DAX measures execute without errors

**Current Status: NOT READY for production**  
**Estimated Time to Production Ready: 1-2 weeks** (after implementing fixes)

---

*Report generated by Yardi PowerBI Data Integrity Validator*  
*For questions or clarification, review the detailed analysis scripts in the project directory.*