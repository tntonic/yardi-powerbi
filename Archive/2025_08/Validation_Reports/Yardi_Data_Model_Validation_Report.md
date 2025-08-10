# Yardi Power BI Data Model Validation Report

**Generated:** 2025-08-09 03:21:55  
**Validator:** Yardi Power BI Data Model Integrity Specialist  
**Data Path:** `/Users/michaeltang/Documents/GitHub/BI/PBI v1.7/Data/Yardi_Tables`

## 🎯 Executive Summary

**Overall Integrity Score: 75.9/100**  
**Grade: C (Needs Improvement)**

The Yardi Power BI data model validation reveals significant structural and data integrity issues that require immediate attention before proceeding with DAX implementation and dashboard deployment.

## 📊 Key Findings

### Table Completeness (56.2/100)
- **Expected Tables:** 32
- **Found Tables:** 29 (18 matching expected schema)
- **Missing Tables:** 14 critical tables
- **Coverage:** 56.25% of expected architecture

### Data Integrity Issues
- **Orphaned Records:** 164,646 (32.52% of fact_total records)
- **Missing Rent Charges:** 735 amendments (29.75% of active amendments)
- **Duplicate Amendments:** 0 (✅ Excellent)
- **Total Data Volume:** 1,266,394 records across all tables

## ❌ Critical Issues Identified

### 1. Missing Tables (14)
| Table Type | Missing Table | Impact |
|------------|---------------|---------|
| Dimension | `dim_tenant` | **CRITICAL** - Breaks rent roll calculations |
| Dimension | `dim_assetstatus` | High - Property status tracking |
| Dimension | `dim_marketsegment` | Medium - Market analysis |
| Dimension | `dim_moveoutreasons` | Medium - Leasing activity analysis |
| Dimension | `dim_newleasereason` | Medium - Leasing activity analysis |
| Dimension | `dim_renewalreason` | Medium - Leasing activity analysis |
| Dimension | `dim_unittypelist` | Medium - Unit classification |
| Dimension | `dim_yearbuiltcategory` | Low - Property attributes |
| Fact | `fact_leasingactivity` | **CRITICAL** - Leasing metrics |
| Fact | `fact_marketrentsurvey` | High - Market analysis |
| Bridge | `bridge_propertymarkets` | Medium - Property-market mapping |
| Control | `control_active_scenario` | Low - Scenario management |
| External | `external_market_growth_projections` | Low - Forecasting |
| Reference | `ref_book_override_logic` | Medium - Book logic rules |

### 2. Orphaned Records in fact_total (CRITICAL)
- **164,646 orphaned property records (32.52%)**
- These records reference property IDs that don't exist in dim_property
- **Impact:** Causes DAX measures to return incorrect results
- **Root Cause:** Data extraction/ETL process not properly filtering inactive properties

### 3. Missing Rent Charges (HIGH)
- **735 active amendments without rent charges (29.75%)**
- Affects rent roll accuracy and completeness
- **Impact:** Under-reporting of rental income in Power BI dashboards
- **Root Cause:** Amendments created without corresponding charge schedule entries

## ✅ Positive Findings

### Amendment Integrity (100/100)
- **No duplicate latest amendments** - Excellent data quality
- **2,471 active amendments** properly sequenced
- **1,304 unique property/tenant combinations**
- Amendment sequence logic is working correctly

### Critical Table Presence (100/100)
All essential tables for basic operations are present:
- ✅ `fact_total` (506,367 records)
- ✅ `fact_occupancyrentarea` (601,319 records)  
- ✅ `dim_property` (454 records)
- ✅ `dim_fp_amendmentsunitspropertytenant` (2,472 records)
- ✅ `dim_fp_amendmentchargeschedule` (19,371 records)

## 📈 Data Volume Analysis

### Top 10 Tables by Record Count
1. **fact_occupancyrentarea:** 601,319 records (47.5%)
2. **fact_total:** 506,367 records (40.0%)
3. **dim_propertyattributes:** 30,485 records (2.4%)
4. **fact_fp_fmvm_marketunitrates:** 25,388 records (2.0%)
5. **dim_accounttreeaccountmapping:** 22,856 records (1.8%)
6. **dim_fp_amendmentchargeschedule:** 19,371 records (1.5%)
7. **dim_date:** 17,897 records (1.4%)
8. **dim_commcustomer:** 10,636 records (0.8%)
9. **dim_unit:** 9,800 records (0.8%)
10. **fact_accountsreceivable:** 5,266 records (0.4%)

### Data Quality Indicators
| Metric | Value | Status |
|--------|--------|--------|
| Amendment Status Distribution | 1,520 Activated, 951 Superseded | ✅ Good |
| Account Orphans | 0 (0%) | ✅ Perfect |
| Property Orphans | 164,646 (32.52%) | ❌ Critical |
| Charge Coverage | 70.25% | ⚠️ Needs Improvement |

## 🚨 Impact Assessment

### High Impact Issues
1. **32.52% orphaned fact_total records** will cause:
   - Incorrect revenue/expense totals in dashboards
   - Broken property-level financial analysis
   - DAX measures returning NULL or wrong values

2. **Missing dim_tenant table** will cause:
   - Rent roll reports to fail completely
   - Tenant analysis dashboards to be non-functional
   - Leasing activity tracking to be impossible

3. **29.75% missing rent charges** will cause:
   - Under-reporting of rental income
   - Incomplete rent roll calculations
   - Inaccurate leasing metrics

### Medium Impact Issues
1. **Missing fact_leasingactivity table** will prevent:
   - New lease, renewal, and termination tracking
   - Leasing velocity analysis
   - Retention rate calculations

2. **Missing dimension tables** will limit:
   - Detailed property categorization
   - Market segment analysis  
   - Comprehensive leasing reason tracking

## 🔧 Recommended Remediation Steps

### Phase 1: Critical Fixes (Priority 1 - Immediate)
1. **Resolve orphaned fact_total records**
   ```sql
   -- Identify and remove orphaned records
   DELETE FROM fact_total 
   WHERE [property id] NOT IN (SELECT [property id] FROM dim_property);
   ```

2. **Add missing dim_tenant table**
   - Extract tenant master data from Yardi
   - Ensure proper tenant_hmy linking to amendments

3. **Populate missing rent charges**
   - Identify amendments without charges using validation script
   - Extract missing charge schedule data
   - Link charges to amendment_hmy properly

### Phase 2: Architecture Completion (Priority 2 - Short Term)
1. **Add missing fact tables**
   - `fact_leasingactivity` - Critical for leasing metrics
   - `fact_marketrentsurvey` - Important for market analysis

2. **Add missing dimension tables**
   - `dim_assetstatus`, `dim_marketsegment` - Property classification
   - `dim_moveoutreasons`, `dim_newleasereason`, `dim_renewalreason` - Leasing analysis

### Phase 3: Enhancement Tables (Priority 3 - Long Term)
1. **Add specialized tables**
   - `bridge_propertymarkets` - Property-market relationships
   - `ref_book_override_logic` - Advanced book logic
   - `external_market_growth_projections` - Forecasting support

## 📝 Validation Queries for Cleanup

### Identify Orphaned Properties
```sql
SELECT DISTINCT f.[property id] 
FROM fact_total f
LEFT JOIN dim_property p ON f.[property id] = p.[property id]
WHERE p.[property id] IS NULL
ORDER BY f.[property id];
```

### Find Amendments Without Charges
```sql
SELECT a.[amendment hmy], a.[property hmy], a.[tenant hmy], a.[amendment status]
FROM dim_fp_amendmentsunitspropertytenant a
LEFT JOIN dim_fp_amendmentchargeschedule c ON a.[amendment hmy] = c.[amendment hmy]
WHERE a.[amendment status] IN ('Activated', 'Superseded')
  AND c.[amendment hmy] IS NULL;
```

### Validate Amendment Sequences
```sql
SELECT [property hmy], [tenant hmy], 
       COUNT(*) as amendment_count,
       MAX([amendment sequence]) as latest_sequence
FROM dim_fp_amendmentsunitspropertytenant
WHERE [amendment status] IN ('Activated', 'Superseded')
GROUP BY [property hmy], [tenant hmy]
ORDER BY amendment_count DESC;
```

## ⏭️ Next Steps

### Immediate Actions Required
1. **Data Cleanup** - Address orphaned records and missing charges
2. **Missing Table Extraction** - Focus on dim_tenant and fact_leasingactivity
3. **ETL Process Review** - Ensure proper data extraction from Yardi

### Pre-DAX Implementation Checklist
- [ ] Integrity score improved to 90+ 
- [ ] Orphaned records reduced to <5%
- [ ] Missing rent charges reduced to <10%
- [ ] All critical tables present (dim_tenant, fact_leasingactivity)
- [ ] Amendment logic validated

### Monitoring and Maintenance
- [ ] Implement automated validation checks
- [ ] Schedule monthly integrity assessments  
- [ ] Create data quality alerts for new issues
- [ ] Document data refresh procedures

---

**Report Status:** Complete  
**Validation Framework:** Phase1_Data_Model_Validation.sql adapted for CSV analysis  
**Next Phase:** DAX validation and accuracy testing after data cleanup

This report provides a comprehensive baseline for the Yardi Power BI data model cleanup and improvement process. Address the critical issues identified before proceeding with DAX implementation to ensure accurate and reliable dashboard performance.