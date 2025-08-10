# PowerBI Rent Roll Accuracy Validation Report
## Comprehensive Analysis and Recommendations

**Report Date:** August 9, 2025  
**Validation Agent:** PowerBI Measure Accuracy Testing Specialist  
**Target Accuracy:** 95%+  
**Actual Accuracy:** 63.0% (FAILED - Requires Significant Improvements)

---

## Executive Summary

This comprehensive accuracy validation tested DAX rent roll measures against actual Yardi exports for Fund 2 properties across two test periods (March 31, 2025 and December 31, 2024). While the DAX logic correctly implements amendment-based calculations with 96-99% accuracy for record counts and square footage, **critical issues in the charge schedule join logic result in only 18-43% accuracy for monthly rent calculations**.

The root cause has been identified: **Latest amendment sequence selection chooses "Proposal in DM" amendments that lack rent charges**, causing $0 rent calculations for many properties.

---

## Test Results Summary

### Overall Accuracy Scores
- **March 31, 2025:** 57.2% - FAIL
- **December 31, 2024:** 68.9% - FAIL  
- **Average Accuracy:** 63.0% - SIGNIFICANTLY BELOW 95% TARGET

### Accuracy by Metric Category

| Metric Category | Mar 2025 | Dec 2024 | Status |
|-----------------|----------|----------|--------|
| Record Count | 96.6% | 99.7% | ✅ EXCELLENT |
| Property Coverage | 92.0% | 92.5% | ✅ GOOD |
| Square Feet | 99.1% | 96.8% | ✅ EXCELLENT |
| **Monthly Rent** | **18.0%** | **42.8%** | ❌ **CRITICAL FAILURE** |

---

## Root Cause Analysis

### Primary Issue: Amendment Selection Logic Flaw

**Problem:** The DAX logic correctly selects the latest amendment sequence per property/tenant combination, but many of these latest amendments are "Proposal in DM" or future amendments **without rent charges**.

**Evidence:**
- Join success rate: Only 82.1% of amendments have corresponding rent charges
- Many high-value properties show $0.00 calculated rent vs. actual rent in Yardi
- Latest amendments frequently have amendment type "Proposal in DM" with zero charges

**Examples of Affected Properties:**
- **xnj19nev:** $0 calculated vs. $192,911 actual (Latest amendment: "Proposal in DM", no charges)
- **xpa18rai:** $0 calculated vs. $180,621 actual (Latest amendment: "Proposal in DM", no charges)  
- **xil1600:** $0 calculated vs. $139,279 actual (Latest amendment: "Renewal" but charges start in future)

### Secondary Issues

1. **Charge Schedule Data Quality**
   - Active charges dataset (1,084 records) vs. All charges dataset (7,837 records)
   - Date filtering may be excluding valid charges
   - Rent charges: 250 active vs. 2,407 total

2. **Amendment Type Filtering**
   - "Superseded" amendments may still have valid rent charges
   - "Proposal in DM" amendments lack charge schedules
   - Date active filtering reduces dataset from 750 to 389 amendments

---

## Detailed Findings

### ✅ What's Working Well

1. **Data Model Relationships:** Property-tenant-amendment hierarchy correctly implemented
2. **Amendment Filtering:** Status and type filters working as designed  
3. **Date Logic:** Serial date conversion accurate, date filtering working correctly
4. **Square Footage Calculations:** 96-99% accuracy indicates solid area calculations
5. **Record Matching:** 92% property coverage shows good data alignment

### ❌ Critical Failures

1. **Rent Calculation Logic:** Selecting amendments without charges
2. **Business Logic Gap:** Not accounting for "proposals" vs. "executed" amendments
3. **Charge Schedule Join:** 18% of amendments missing rent charges
4. **Data Currency:** Using future amendments without current rent charges

---

## Specific Recommendations

### 🔧 Immediate Fixes Required

#### 1. Modify Amendment Selection Logic
**Current Logic:** Select MAX(amendment sequence) per property/tenant
```dax
// CURRENT (INCORRECT)
Latest Amendment = 
CALCULATE(
    MAX(Amendments[amendment sequence]),
    ALLEXCEPT(Amendments, Amendments[property hmy], Amendments[tenant hmy])
)
```

**Recommended Logic:** Select latest amendment WITH rent charges
```dax
// RECOMMENDED (CORRECTED)
Latest Amendment With Rent = 
VAR HasRentCharges = 
CALCULATE(
    COUNTROWS(Charges),
    Charges[charge code] = "rent",
    Charges[monthly amount] > 0
) > 0

RETURN
IF(
    HasRentCharges,
    CALCULATE(
        MAX(Amendments[amendment sequence]),
        ALLEXCEPT(Amendments, Amendments[property hmy], Amendments[tenant hmy]),
        Amendments[amendment type] <> "Proposal in DM"
    ),
    CALCULATE(
        MAX(Amendments[amendment sequence]),
        ALLEXCEPT(Amendments, Amendments[property hmy], Amendments[tenant hmy]),
        Amendments[amendment status] = "Activated"
    )
)
```

#### 2. Improve Charge Schedule Join Logic
- Use **all charges dataset** with proper date filtering instead of "active" subset
- Implement fallback to previous amendment if latest has no charges
- Add validation for $0 rent amounts with business rule exceptions

#### 3. Add Amendment Type Business Rules
```dax
// Exclude proposals and include only executed amendments
ValidAmendmentTypes = 
Amendments[amendment type] IN {
    "Original Lease",
    "Renewal", 
    "Expansion",
    "Assignment",
    "Holdover"
}
```

### 🔍 Validation Improvements

#### 1. Data Quality Checks
- Alert when calculated rent = $0 for occupied properties
- Validate charge schedule completeness for active amendments  
- Cross-reference amendment types with charge availability

#### 2. Enhanced Testing Framework
- Test with current date (TODAY()) instead of historical dates
- Include accuracy thresholds by property type and size
- Add property-level variance analysis

#### 3. Business Logic Validation
- Confirm with business users: Should "Superseded" amendments have rent?
- Verify: Are "Proposal in DM" amendments valid for rent roll?
- Establish: What's the correct fallback logic for missing charges?

---

## Implementation Priority

### Phase 1: Critical Fixes (Immediate - Week 1)
1. ✅ **Amendment selection logic** - Use latest amendment WITH rent charges
2. ✅ **Charge dataset** - Switch from "active" to "all" with date filtering  
3. ✅ **Amendment type filtering** - Exclude "Proposal in DM" types

### Phase 2: Enhanced Logic (Week 2)
1. ✅ **Fallback logic** - Use previous amendment if latest has no charges
2. ✅ **Data validation** - Add $0 rent alerts and business rule checks
3. ✅ **Testing improvements** - Comprehensive property-level validation

### Phase 3: Production Readiness (Week 3-4)
1. ✅ **Performance optimization** - Ensure <10 second dashboard load times
2. ✅ **Comprehensive testing** - Validate against all Yardi exports
3. ✅ **Documentation updates** - Refresh DAX library with corrected measures

---

## Expected Accuracy Improvement

Based on root cause analysis, implementing the recommended fixes should achieve:

| Fix Implementation | Expected Accuracy |
|-------------------|-------------------|
| Current State | 63.0% |
| Amendment Logic Fix | 85-90% |
| + Charge Dataset Fix | 90-95% |
| + Business Rules | **95-98%** ✅ |

---

## Technical Implementation Notes

### DAX Measure Updates Required

1. **Current Monthly Rent Measure**
2. **Current Leased SF Measure** 
3. **Current Rent Roll PSF Measure**
4. **Amendment-based filtering patterns**

### Data Model Considerations
- Relationship between amendments and charges is sound
- Date filtering logic works correctly
- Consider adding calculated column for "Amendment Has Charges" flag

### Testing Protocol
- Re-run accuracy tests after each fix implementation
- Validate against multiple date periods
- Include edge cases (terminated leases, holdovers, expansions)

---

## Conclusion

The PowerBI rent roll implementation demonstrates **excellent technical architecture** with accurate data relationships, date logic, and square footage calculations. However, a **fundamental business logic flaw** in amendment selection prevents achieving the 95% accuracy target.

**The core issue is correctable** through improved amendment selection logic that prioritizes amendments with active rent charges over those without. Implementation of the recommended fixes should bring accuracy from 63% to 95%+.

**Recommendation:** Proceed with Phase 1 critical fixes immediately, as the foundation is solid and the solution path is clear.

---

## Appendix: Test Data Details

### Test Coverage
- **Properties Tested:** 195 Fund 2 properties
- **Common Properties:** 160-161 per test date
- **Amendment Records:** 877 total, 307-309 after filtering
- **Charge Records:** 7,837 total, 1,084 active

### Accuracy by Property Size
- **Properties >90% accuracy:** 61-39 out of 160-161
- **Properties <50% accuracy:** ~100 properties (mostly $0 rent)
- **Perfect matches (100%):** Properties with executed amendments and active charges

### Data Quality Metrics
- Amendment filtering retention: 44.4%
- Charge schedule join success: 82.1%  
- Date serial conversion accuracy: 100%
- Property code extraction: 100%

---

**Report Prepared By:** PowerBI Measure Accuracy Testing Agent  
**Next Review:** Upon implementation of Phase 1 fixes  
**File Location:** `/Users/michaeltang/Documents/GitHub/BI/PBI v1.7/Final_PowerBI_Rent_Roll_Accuracy_Validation_Report.md`