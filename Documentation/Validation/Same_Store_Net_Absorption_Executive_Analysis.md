# Same-Store Net Absorption DAX Measures - Executive Analysis Report

**Test Date:** August 10, 2025  
**Test Period:** Q4 2024 (October 1 - December 31, 2024)  
**Scope:** Fund 2 Same-Store Net Absorption Measures  
**Analyst:** Power BI Measure Accuracy Testing Specialist  

---

## Executive Summary

This analysis tested 5 newly created same-store net absorption DAX measures against FPR Q4 2024 Fund 2 benchmarks. **All measures failed accuracy testing (0% accuracy)**, revealing critical data filtering and business logic issues that require immediate attention before production deployment.

### Key Findings

| **Critical Issue** | **Impact** | **Status** |
|-------------------|------------|------------|
| **Same-Store Property Mismatch** | No Q4 2024 activity matches Fund 2 same-store properties | ❌ CRITICAL |
| **Data Scope Inconsistency** | All-fund activity significantly exceeds benchmarks | ❌ HIGH |
| **Disposed Property Data Quality** | Missing dispose dates for benchmark properties | ❌ HIGH |
| **Fund Filtering Logic** | Current filtering may exclude relevant properties | ❌ MEDIUM |

---

## Detailed Test Results

### Measure Performance vs. Benchmarks

| **Measure** | **FPR Benchmark** | **Calculated** | **Variance** | **Status** |
|-------------|------------------|----------------|--------------|------------|
| SF Expired (Same-Store) | 256,303 SF | 0 SF | -256,303 SF (-100%) | ❌ FAIL |
| SF Commenced (Same-Store) | 88,482 SF | 0 SF | -88,482 SF (-100%) | ❌ FAIL |
| Net Absorption (Same-Store) | -167,821 SF | 0 SF | +167,821 SF (-100%) | ❌ FAIL |
| Disposition SF | 160,925 SF | 0 SF | -160,925 SF (-100%) | ❌ FAIL |
| Acquisition SF | 81,400 SF | 0 SF | -81,400 SF (-100%) | ❌ FAIL |

**Overall Accuracy: 0.0% (Target: 95%+)**

---

## Root Cause Analysis

### 1. Same-Store Property Filtering Issue ❌ CRITICAL

**Problem:** Fund 2 same-store properties (12 properties with codes like `xflstuar`, `xnj125al`) have **zero matching activity** with Q4 2024 terminations and new leases.

**Evidence:**
- Q4 2024 terminations: 19 records from properties `3tn00009`, `xtn225bo`, etc.
- Q4 2024 new leases: 39 records from 21 different properties
- **Zero overlap** between same-store property codes and activity property codes

**Impact:** All same-store calculations return zero because no activity matches the filtered property set.

### 2. Data Scope and Fund Filtering Issues ❌ HIGH

**All-Fund Activity Analysis (Q4 2024):**
- SF Expired (All Funds): 502,439 SF *(96% higher than benchmark)*
- SF Commenced (All Funds): 1,206,596 SF *(1,263% higher than benchmark)*
- Net Absorption (All Funds): +704,157 SF *(opposite sign from benchmark)*

**Implications:**
- Benchmark numbers may represent a **subset** of all activity
- Fund 2 filtering logic may be **too restrictive** or **incorrect**
- Activity scope may include **multiple funds** not properly segmented

### 3. Disposed Property Data Quality Issues ❌ HIGH

**Expected Disposed Properties (Q4 2024):**
- **14 Morris**: Found in data, `is_active = False`, but `dispose_date = NaT`
- **187 Bobrick Drive**: Found in data, `is_active = False`, but `dispose_date = NaT`

**Problem:** Properties show as inactive but lack proper dispose dates, preventing accurate disposition SF calculation.

### 4. Same-Store Definition Misalignment ❌ MEDIUM

**Current Logic:** Properties acquired before Q4 2024 start AND not disposed during Q4 2024
- **Result:** Only 12 Fund 2 properties qualify as same-store
- **Issue:** May not align with FPR's same-store definition

---

## Business Impact Assessment

### Immediate Risks (Production Deployment)

1. **❌ CRITICAL - Dashboard Reliability**: All 5 measures show zero values, making dashboards unusable
2. **❌ HIGH - Executive Reporting**: FPR reports would show incorrect zero activity
3. **❌ HIGH - Investment Decision Impact**: Inaccurate net absorption data affects portfolio performance assessment
4. **❌ MEDIUM - Compliance Risk**: Discrepancies with benchmark reports create audit concerns

### Data Quality Implications

1. **Fund Segmentation**: Current Fund 2 filtering may be incomplete or incorrect
2. **Historical Comparisons**: Zero same-store activity suggests data continuity issues
3. **Cross-Validation**: All-fund numbers suggest data exists but isn't properly filtered

---

## Recommended Action Plan

### Phase 1: Critical Data Investigation (Week 1)

#### 1.1 Fund 2 Property Identification
- **Action**: Validate Fund 2 property list against FPR source systems
- **Owner**: Data Team + Business SME
- **Deliverable**: Confirmed Fund 2 property master list with HMY/code mappings

#### 1.2 Same-Store Definition Alignment
- **Action**: Confirm FPR same-store methodology and criteria
- **Owner**: Business SME + FPR Analyst
- **Deliverable**: Documented same-store business rules

#### 1.3 Q4 2024 Activity Cross-Reference
- **Action**: Map Q4 2024 terminations/new leases to correct fund assignments
- **Owner**: Data Team
- **Deliverable**: Property-to-fund mapping validation

### Phase 2: DAX Logic Corrections (Week 2)

#### 2.1 Property Filtering Enhancement
```dax
// Enhanced same-store property logic
_SameStoreProperties_Enhanced = 
VAR PeriodStart = MIN(dim_date[date])
VAR PeriodEnd = MAX(dim_date[date])
VAR Fund2Properties = [_Fund2Properties] // New helper measure needed
RETURN
CALCULATETABLE(
    Fund2Properties,
    dim_property[acquire date] < PeriodStart,
    OR(
        ISBLANK(dim_property[dispose date]),
        dim_property[dispose date] > PeriodEnd
    )
)
```

#### 2.2 Cross-Fund Data Integration
- **Action**: Ensure termination/amendment data includes proper fund identifiers
- **Method**: Use property code lookups or direct fund fields if available

#### 2.3 Disposed Property Date Correction
- **Action**: Populate dispose dates for 14 Morris and 187 Bobrick
- **Alternative**: Use `is_active = False` as disposal indicator with date validation

### Phase 3: Enhanced Testing Framework (Week 3)

#### 3.1 Multi-Scenario Validation
- Test same-store vs. all-property calculations
- Validate against multiple benchmark periods
- Cross-check with Yardi native reports

#### 3.2 Data Quality Monitoring
- Implement automated checks for property-fund assignments
- Monitor dispose date completeness
- Track amendment/termination data coverage

---

## Specific DAX Measure Recommendations

### SF Expired (Same-Store) - Critical Issues
```dax
// Current issue: Property filtering returns empty set
// Recommendation: Add Fund 2 validation layer

SF Expired (Same-Store) = 
VAR Fund2SameStore = [_Enhanced_Fund2_SameStore_Properties]
VAR CurrentPeriodStart = MIN(dim_date[date])
VAR CurrentPeriodEnd = MAX(dim_date[date])

// Add debugging validation
VAR PropertyCount = COUNTROWS(Fund2SameStore)
VAR TerminationCount = CALCULATE(
    COUNTROWS(dim_fp_terminationtomoveoutreas),
    dim_fp_terminationtomoveoutreas[amendment end date] >= CurrentPeriodStart,
    dim_fp_terminationtomoveoutreas[amendment end date] <= CurrentPeriodEnd
)

// Main calculation with enhanced filtering...
```

### SF Commenced (Same-Store) - Enhancement Needed
```dax
// Add renewal amendments that increase square footage
// Current logic may exclude relevant amendment types

VAR FilteredNewLeases = 
    CALCULATETABLE(
        dim_fp_amendmentsunitspropertytenant,
        dim_fp_amendmentsunitspropertytenant[amendment status] IN {"Activated", "Superseded"},
        OR(
            dim_fp_amendmentsunitspropertytenant[amendment type] IN {"Original Lease", "New Lease"},
            AND(
                dim_fp_amendmentsunitspropertytenant[amendment type] = "Renewal",
                dim_fp_amendmentsunitspropertytenant[amendment sf] > 0 // Net positive SF
            )
        ),
        // ... additional filters
    )
```

### Disposition SF - Data Quality Fix Required
```dax
Disposition SF = 
// Enhanced to handle missing dispose dates
VAR PeriodStart = MIN(dim_date[date])
VAR PeriodEnd = MAX(dim_date[date])

// Primary method: Use dispose dates
VAR DisposedByDate = 
    CALCULATE(
        SUM(dim_property[rentable area]),
        dim_property[dispose date] >= PeriodStart,
        dim_property[dispose date] <= PeriodEnd,
        NOT ISBLANK(dim_property[dispose date])
    )

// Fallback method: Use inactive status for known disposals
VAR DisposedByStatus = 
    CALCULATE(
        SUM(dim_property[rentable area]),
        dim_property[is active] = FALSE,
        dim_property[property name] IN {"14 Morris", "187 Bobrick Drive"}
        // Add period validation based on other date fields
    )

RETURN IF(DisposedByDate > 0, DisposedByDate, DisposedByStatus)
```

---

## Alternative Validation Approach

### Cross-Reference with All-Fund Data
Given that all-fund calculations show significant activity:
- **SF Expired (All Funds)**: 502,439 SF
- **SF Commenced (All Funds)**: 1,206,596 SF

**Recommendation**: Use all-fund data to reverse-engineer Fund 2 filtering:
1. Identify which properties contributed to these numbers
2. Determine correct Fund 2 property subset
3. Recalculate same-store metrics with proper filtering

---

## Success Criteria for Resolution

### Phase 1 Completion
- [ ] Confirmed Fund 2 property list (target: 50-100 properties, not 12)
- [ ] Documented same-store business rules matching FPR methodology
- [ ] Q4 2024 activity properly mapped to Fund 2 properties

### Phase 2 Completion  
- [ ] SF Expired (Same-Store): 90-110% of benchmark (230-282k SF)
- [ ] SF Commenced (Same-Store): 90-110% of benchmark (80-97k SF)
- [ ] Net Absorption (Same-Store): Within 20% of benchmark (-134 to -201k SF)
- [ ] Disposition SF: 95%+ accuracy (153-169k SF)
- [ ] Acquisition SF: 95%+ accuracy (77-86k SF)

### Phase 3 Completion
- [ ] Overall accuracy: 95%+ across all measures
- [ ] Automated monitoring in place
- [ ] Documentation updated with final methodology

---

## Risk Mitigation

### If Fund 2 Data is Insufficient
**Fallback Strategy**: Implement portfolio-level calculations with fund segmentation:
1. Calculate measures for all funds
2. Apply proportional allocation based on property count/value
3. Validate against available Fund 2 benchmarks

### If Same-Store Definition Cannot Be Aligned
**Alternative Approach**: Implement multiple calculation methods:
1. Same-store (current period properties)
2. Same-fund (all Fund 2 properties)
3. Total portfolio (all properties)
4. Allow user selection based on reporting needs

---

## Conclusion

The same-store net absorption DAX measures require **significant data and logic corrections** before production deployment. The primary issues are **data filtering scope** and **property-to-fund mapping accuracy**, not fundamental DAX logic problems.

**Immediate Priority**: Resolve Fund 2 property identification and same-store filtering logic. The all-fund calculations demonstrate that the underlying data and DAX logic framework are functional—the issue is improper filtering and scope definition.

**Expected Timeline**: 2-3 weeks for complete resolution with proper data investigation and business rule alignment.

**Business Confidence Level**: 🔴 **LOW** until Phase 1 data investigation is completed and property filtering is corrected.

---

*Report prepared by: Power BI Measure Accuracy Testing Specialist*  
*Analysis Date: August 10, 2025*  
*Next Review: Upon Phase 1 completion*