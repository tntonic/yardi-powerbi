# Yardi Power BI Data Model Integrity Validation Summary

**Date:** 2025-08-09  
**Validation Scope:** Pre-cleanup baseline assessment  
**Data Model Version:** PBI v1.7  
**Total Records Analyzed:** 1,266,394

## 🎯 Executive Summary

**Overall Integrity Score: 75.9/100 (Grade: C - Needs Improvement)**

The Yardi Power BI data model validation reveals significant structural and data integrity issues that must be resolved before DAX implementation and dashboard deployment. While core tables are present and amendment logic is sound, critical relationship integrity problems and missing data threaten reporting accuracy.

---

## 📊 Key Validation Results

### Table Inventory Assessment
- **Expected Tables:** 32 (per schema specification)
- **Found Tables:** 29 CSV files  
- **Matching Expected Schema:** 18 tables (56.25%)
- **Missing Critical Tables:** 14 tables
- **Extra/Variant Tables:** 11 tables

### Data Integrity Metrics
| Metric | Value | Status | Impact |
|--------|--------|---------|---------|
| **Orphaned fact_total Records** | 164,646 (32.52%) | ❌ Critical | Revenue/expense reporting failure |
| **Missing Amendment Charges** | 735 (29.75%) | ❌ High | Rent roll under-reporting |
| **Amendment Duplicates** | 0 (0.00%) | ✅ Perfect | Clean amendment sequencing |
| **Account Relationship Integrity** | 100% | ✅ Perfect | GL mapping intact |
| **Property Relationship Integrity** | 67.48% | ❌ Critical | Property reporting broken |

### Financial Impact Analysis
- **Total Transaction Volume:** $2.58 billion
- **Orphaned Transaction Amount:** $822 million (31.90%)
- **Compromised Records:** 164,646 fact_total entries
- **Affected Properties:** 579 unique property IDs

---

## ❌ Critical Issues Requiring Immediate Action

### 1. Massive Orphaned Records Problem (CRITICAL)
**Issue:** 32.52% of fact_total records reference non-existent properties  
**Root Cause:** ETL process including inactive/deleted properties in fact extraction  
**Financial Impact:** $822 million in orphaned transactions  
**DAX Impact:** Will cause NULL values and incorrect totals in all property-level measures

**Top Affected Properties:**
- Property ID 2828: 3,177 orphaned records
- Property ID 2829: 2,776 orphaned records  
- Property ID 1604: 2,699 orphaned records
- Property ID 3599: 2,310 orphaned records
- Property ID 1606: 2,219 orphaned records

### 2. Key Column Relationship Mismatch (CRITICAL)
**Issue:** Amendment table uses "property hmy" while property table uses "property id"  
**Root Cause:** Inconsistent key naming conventions across tables  
**Impact:** Prevents proper relationship establishment in Power BI  
**Solution Required:** Standardize primary/foreign key naming or create mapping

### 3. Missing Rent Charges (HIGH)
**Issue:** 735 active amendments (29.75%) have no associated rent charges  
**Impact:** Rent roll calculations will be incomplete and under-reported  
**Business Risk:** Financial reporting accuracy compromised

### 4. Missing Core Tables (HIGH)
**Critical Missing Tables:**
- `dim_tenant` - **BREAKS RENT ROLL COMPLETELY**
- `fact_leasingactivity` - Prevents leasing metrics
- `fact_marketrentsurvey` - Limits market analysis
- `dim_assetstatus` - Property classification incomplete

---

## ✅ Positive Findings

### Amendment Logic Integrity (Perfect Score)
- **No duplicate latest amendments** - Critical for rent roll accuracy
- **Proper sequence logic** - 1,304 unique property/tenant combinations
- **Clean status distribution** - 1,520 Activated, 951 Superseded, 1 In Process
- **Latest amendment filtering** works correctly

### Core Data Volume (Healthy)
- **fact_total:** 506,367 records - Financial data substantial
- **fact_occupancyrentarea:** 601,319 records - Occupancy tracking robust  
- **Amendment records:** 2,471 active amendments - Lease data comprehensive
- **Charge schedule:** 19,371 records - Rent charge data extensive

### Account Relationships (Perfect)
- **0% orphaned account records** - Chart of accounts mapping intact
- **Complete GL integration** - Account hierarchy preserved
- **Revenue/expense categorization** - Account type logic functional

---

## 📈 Detailed Findings by Validation Area

### 1. Table Completeness Analysis (56.2/100)
**Missing Tables Impact Assessment:**

| Missing Table | Type | Priority | Impact on Reporting |
|---------------|------|----------|-------------------|
| `dim_tenant` | Dimension | CRITICAL | Rent roll fails completely |
| `fact_leasingactivity` | Fact | CRITICAL | No leasing metrics possible |
| `dim_assetstatus` | Dimension | HIGH | Property status tracking lost |
| `fact_marketrentsurvey` | Fact | HIGH | Market analysis limited |
| `dim_moveoutreasons` | Dimension | MEDIUM | Termination analysis incomplete |
| `dim_newleasereason` | Dimension | MEDIUM | New lease tracking limited |
| `dim_renewalreason` | Dimension | MEDIUM | Renewal analysis incomplete |

### 2. Relationship Integrity Analysis (67.5/100)
**Property Relationships:**
- Valid records: 341,721 (67.48%)
- Orphaned records: 164,646 (32.52%)
- Unique orphaned property IDs: 579

**Account Relationships:**
- Valid records: 506,367 (100%)
- Orphaned records: 0 (0%)

### 3. Amendment Integrity Analysis (100/100)
**Status Distribution:**
- Activated: 1,520 amendments (61.5%)
- Superseded: 951 amendments (38.5%)  
- In Process: 1 amendment (0.04%)

**Sequence Validation:**
- Unique property/tenant combinations: 1,304
- Duplicate latest sequences: 0
- Amendment logic: ✅ PERFECT

### 4. Charge Coverage Analysis (70.3/100)
**Coverage Metrics:**
- Amendments with charges: 1,736 (70.25%)
- Amendments without charges: 735 (29.75%)
- Charge records available: 19,371

---

## 🔧 Prioritized Remediation Plan

### Phase 1: Emergency Fixes (Week 1)
1. **Resolve Orphaned Records**
   ```sql
   DELETE FROM fact_total 
   WHERE [property id] NOT IN (SELECT [property id] FROM dim_property);
   ```
   Expected removal: 164,646 records

2. **Standardize Key Relationships**
   - Map property_hmy to property_id across tables
   - Create relationship bridge table if needed
   - Validate all foreign key relationships

3. **Extract Missing dim_tenant Table**
   - Critical for rent roll functionality
   - Must include tenant_hmy mapping to amendments

### Phase 2: Core Completeness (Week 2-3)
1. **Add Critical Fact Tables**
   - Extract `fact_leasingactivity` from Yardi
   - Add `fact_marketrentsurvey` for market analysis
   
2. **Complete Dimension Tables**
   - Add `dim_assetstatus` for property classification
   - Extract reason code dimensions for leasing analysis

3. **Populate Missing Charges**
   - Investigate 735 amendments without charges
   - Extract missing charge schedule data
   - Implement charge creation validation

### Phase 3: Enhancement & Monitoring (Week 4+)
1. **Add Specialized Tables**
   - Bridge tables for complex relationships
   - Reference tables for business logic
   - External data for market projections

2. **Implement Data Quality Controls**
   - Automated orphan record detection
   - Referential integrity constraints
   - Regular validation reporting

---

## 📝 SQL Validation Queries

### Critical Issues Detection
```sql
-- 1. Find all orphaned fact_total records
SELECT COUNT(*) as orphaned_count,
       SUM([amount]) as orphaned_amount
FROM fact_total f
LEFT JOIN dim_property p ON f.[property id] = p.[property id]  
WHERE p.[property id] IS NULL;

-- 2. Identify amendments without charges
SELECT COUNT(*) as missing_charges_count
FROM dim_fp_amendmentsunitspropertytenant a
LEFT JOIN dim_fp_amendmentchargeschedule c ON a.[amendment hmy] = c.[amendment hmy]
WHERE a.[amendment status] IN ('Activated', 'Superseded')
  AND c.[amendment hmy] IS NULL;

-- 3. Check for duplicate latest amendments  
SELECT [property hmy], [tenant hmy], COUNT(*) as duplicate_count
FROM (
    SELECT [property hmy], [tenant hmy], [amendment sequence],
           ROW_NUMBER() OVER (PARTITION BY [property hmy], [tenant hmy] 
                              ORDER BY [amendment sequence] DESC) as rn
    FROM dim_fp_amendmentsunitspropertytenant
    WHERE [amendment status] IN ('Activated', 'Superseded')
) latest
WHERE rn = 1
GROUP BY [property hmy], [tenant hmy]
HAVING COUNT(*) > 1;
```

### Data Quality Monitoring
```sql
-- Monthly data quality scorecard
WITH quality_metrics AS (
    SELECT 
        'Table Completeness' as metric,
        COUNT(*) as actual_value,
        32 as target_value,
        CAST(COUNT(*) * 100.0 / 32 AS DECIMAL(5,2)) as score
    FROM information_schema.tables
    WHERE table_name LIKE 'dim_%' OR table_name LIKE 'fact_%'
    
    UNION ALL
    
    SELECT 
        'Property Orphans %' as metric,
        COUNT(*) as actual_value,
        0 as target_value,
        CASE WHEN COUNT(*) = 0 THEN 100.0 ELSE 0.0 END as score
    FROM fact_total f
    LEFT JOIN dim_property p ON f.[property id] = p.[property id]
    WHERE p.[property id] IS NULL
    
    UNION ALL
    
    SELECT
        'Amendment Charges %' as metric,
        COUNT(*) as actual_value,
        0 as target_value,
        100.0 - (COUNT(*) * 100.0 / (SELECT COUNT(*) FROM dim_fp_amendmentsunitspropertytenant WHERE [amendment status] IN ('Activated', 'Superseded'))) as score
    FROM dim_fp_amendmentsunitspropertytenant a
    LEFT JOIN dim_fp_amendmentchargeschedule c ON a.[amendment hmy] = c.[amendment hmy]
    WHERE a.[amendment status] IN ('Activated', 'Superseded')
      AND c.[amendment hmy] IS NULL
)
SELECT 
    metric,
    actual_value,
    target_value,
    score,
    CASE 
        WHEN score >= 95 THEN '✅ Excellent'
        WHEN score >= 85 THEN '✅ Good'  
        WHEN score >= 70 THEN '⚠️ Fair'
        ELSE '❌ Poor'
    END as grade
FROM quality_metrics;
```

---

## 🎯 Success Criteria for Cleanup

### Target Metrics (Pre-DAX Implementation)
- **Overall Integrity Score:** 90+ (up from 75.9)
- **Orphaned Records:** <5% (down from 32.52%)
- **Missing Charges:** <10% (down from 29.75%)
- **Table Completeness:** 90% (up from 56.25%)
- **Critical Tables:** 100% present

### Validation Gates
1. **Gate 1:** Orphaned records eliminated
2. **Gate 2:** dim_tenant and fact_leasingactivity tables added  
3. **Gate 3:** Amendment-charge coverage >90%
4. **Gate 4:** All relationship integrity >95%
5. **Gate 5:** Automated quality monitoring implemented

### Business Impact Targets
- **Rent Roll Accuracy:** 95%+ vs Yardi native
- **Financial Reporting Accuracy:** 98%+ vs GL
- **Dashboard Load Time:** <10 seconds
- **Data Refresh Time:** <30 minutes

---

## 📋 Next Phase Recommendations

### Immediate Actions (Next 48 Hours)
1. **Stakeholder Communication:** Brief leadership on critical findings
2. **ETL Process Review:** Investigate orphaned record root cause
3. **Data Extraction Planning:** Prioritize missing critical tables
4. **Resource Allocation:** Assign data engineering support

### Short-term Objectives (Next 2 Weeks)  
1. **Complete remediation Phase 1 and 2**
2. **Re-run validation to confirm improvements**
3. **Begin Phase 2 DAX validation preparation**
4. **Establish ongoing data quality monitoring**

### Long-term Strategy (Next Quarter)
1. **Implement comprehensive data governance**
2. **Automate validation and monitoring processes**  
3. **Establish data refresh SLAs and monitoring**
4. **Create user training and documentation**

---

**Validation Status:** COMPLETE  
**Next Step:** Execute Phase 1 remediation plan  
**Critical Path:** Orphaned record cleanup → Missing table extraction → DAX validation

This baseline assessment provides the foundation for systematic data model cleanup and ensures reliable Power BI dashboard deployment.