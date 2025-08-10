# LEASING ACTIVITY DAX MEASURES VALIDATION REPORT
**Power BI Measure Accuracy Testing - Q4 2024 AM Slides Validation**

**Date:** August 10, 2025  
**Validator:** Power BI Measure Accuracy Testing Specialist  
**Target Accuracy:** 95%+  

---

## EXECUTIVE SUMMARY

The newly created Leasing Activity DAX Library (v1.0) containing 75 measures has been validated against Q4 2024 AM slide expected results. **Overall accuracy achieved: 79.9%**, which is below the required 95% threshold. Several critical issues have been identified that require immediate attention before production deployment.

### KEY FINDINGS

| Metric | Status | Details |
|--------|--------|---------|
| **Overall Accuracy** | ❌ FAIL (79.9%) | Below 95% target |
| **Data Quality** | ✅ PASS (99.8%) | Excellent data integrity |
| **Performance** | ✅ PASS (<0.001s) | Well within 3s target |
| **Fund Classification** | ❌ CRITICAL | Only 37% of deals correctly classified |

---

## DETAILED VALIDATION RESULTS

### 1. DEAL COUNTS VALIDATION

| Measure | Fund 2 | Fund 3 | Status |
|---------|--------|--------|---------|
| **New Leases** | 0 vs 4 expected | 0 vs 3 expected | ❌ CRITICAL |
| **Renewals** | 6 vs 4 expected | 7 vs 6 expected | ⚠️ MODERATE |
| **Total Deals** | 8 vs 8 expected | 9 vs 9 expected | ✅ GOOD |

**Root Cause:** Proposal Type filtering logic in DAX measures may not align with data structure.

### 2. SQUARE FOOTAGE VALIDATION

| Fund | Actual SF | Expected SF | Variance | Accuracy |
|------|-----------|-------------|----------|----------|
| **Fund 2** | 458,059 | 286,978 | +171,081 | 40.4% ❌ |
| **Fund 3** | 184,725 | 194,272 | -9,547 | 95.1% ✅ |

**Root Cause:** Fund 2 classification capturing too many deals due to backup logic.

### 3. WEIGHTED RATES VALIDATION

| Fund | Actual Rate | Expected Rate | Status |
|------|-------------|---------------|---------|
| **Fund 2** | $117,182.97 | $7.18 | ❌ CRITICAL ERROR |
| **Fund 3** | $115.92 | $9.55 | ❌ CRITICAL ERROR |

**Root Cause:** Rate calculation logic fundamentally flawed - appears to be calculating total rent instead of PSF rate.

### 4. ESCALATION RATES VALIDATION

| Fund | Actual | Expected | Accuracy |
|------|--------|----------|----------|
| **Fund 2** | 2.17% | 3.89% | 55.8% ❌ |
| **Fund 3** | 2.78% | 3.45% | 80.5% ⚠️ |

**Root Cause:** Area weighting may not be correctly implemented.

### 5. DATA QUALITY ASSESSMENT

- **Total Records:** 2,675
- **Data Quality Score:** 99.8% ✅
- **Q4 2024 Executed Deals:** 63 (reasonable)
- **Orphaned Records:** <1% (excellent)

---

## CRITICAL ISSUES IDENTIFIED

### 🔴 ISSUE 1: Fund Classification Logic
**Problem:** Only 27% of Q4 2024 deals correctly classified by fund  
**Impact:** All fund-specific measures will be inaccurate  
**Severity:** CRITICAL

**Current Logic Issues:**
- Tenant name matching fails for most records
- Backup logic assigns deals arbitrarily by size
- No integration with actual fund mapping tables

### 🔴 ISSUE 2: Weighted Average Rate Calculation
**Problem:** Rates calculated as total dollars instead of PSF  
**Impact:** All rate-based measures unusable  
**Severity:** CRITICAL

**Current DAX Issues:**
```dax
// INCORRECT - This calculates total rent, not PSF
VAR WeightedRentCalculation = 
    SUMX(
        [_BaseValidLeasingDeals],
        VAR DealArea = fact_leasingactivity[dArea]
        VAR DealRent = fact_leasingactivity[Starting Rent] * 12
        RETURN IF(DealArea > 0, (DealRent / DealArea) * DealArea, 0)
    )
```

### 🔴 ISSUE 3: Deal Type Classification
**Problem:** No "New Lease" deals found in Q4 2024  
**Impact:** New vs Renewal analysis completely wrong  
**Severity:** HIGH

### 🟡 ISSUE 4: Spread Calculations Missing
**Problem:** Spread measures use placeholder logic  
**Impact:** Key leasing performance metrics unavailable  
**Severity:** MODERATE

---

## SPECIFIC DAX FIXES REQUIRED

### 1. Fix Fund Classification Logic

**RECOMMENDED DAX:**
```dax
// Replace placeholder fund logic with actual fund mapping
Fund Classification = 
VAR PropertyFund = 
    RELATED(dim_property[Fund])
RETURN 
    IF(
        NOT ISBLANK(PropertyFund),
        PropertyFund,
        "Unknown"
    )
```

### 2. Fix Weighted Average Rate Calculation

**CORRECTED DAX:**
```dax
Weighted Average Starting Rent PSF = 
VAR ValidDeals = 
    FILTER(
        [_BaseValidLeasingDeals],
        NOT ISBLANK(fact_leasingactivity[Starting Rent]) &&
        NOT ISBLANK(fact_leasingactivity[dArea]) &&
        fact_leasingactivity[dArea] > 0
    )
VAR TotalWeightedRent = 
    SUMX(
        ValidDeals,
        fact_leasingactivity[Starting Rent] * fact_leasingactivity[dArea]
    )
VAR TotalArea = 
    SUMX(
        ValidDeals,
        fact_leasingactivity[dArea]
    )
RETURN 
    DIVIDE(TotalWeightedRent, TotalArea, 0)
```

### 3. Add Missing Spread Calculations

**NEW MEASURES NEEDED:**
```dax
Spread Over Prior Lease % = 
VAR CurrentDeals = 
    FILTER(
        [_BaseValidLeasingDeals],
        fact_leasingactivity[Cash Flow Type] = "Proposal" &&
        fact_leasingactivity[Deal Stage] = "Executed"
    )
VAR PriorDeals = 
    FILTER(
        [_BaseValidLeasingDeals],
        fact_leasingactivity[Cash Flow Type] = "Prior Lease"
    )
VAR CurrentWARate = 
    DIVIDE(
        SUMX(CurrentDeals, fact_leasingactivity[Starting Rent] * fact_leasingactivity[dArea]),
        SUMX(CurrentDeals, fact_leasingactivity[dArea])
    )
VAR PriorWARate = 
    DIVIDE(
        SUMX(PriorDeals, fact_leasingactivity[Starting Rent] * fact_leasingactivity[dArea]),
        SUMX(PriorDeals, fact_leasingactivity[dArea])
    )
RETURN 
    DIVIDE(CurrentWARate - PriorWARate, PriorWARate, 0) * 100
```

### 4. Improve Deal Type Classification

**ENHANCED LOGIC:**
```dax
New Leases Executed Count = 
CALCULATE(
    COUNTROWS([_BaseValidLeasingDeals]),
    fact_leasingactivity[Proposal Type] IN {"New Lease", "New"} ||
    (
        fact_leasingactivity[Cash Flow Type] = "Proposal" &&
        NOT CALCULATE(
            COUNTROWS(fact_leasingactivity),
            fact_leasingactivity[Cash Flow Type] = "Prior Lease",
            fact_leasingactivity[Tenant HMY] = EARLIER(fact_leasingactivity[Tenant HMY])
        ) > 0
    ),
    fact_leasingactivity[Deal Stage] = "Executed"
)
```

---

## VALIDATION TEST SCENARIOS

### Test Scenario 1: Q4 2024 Fund 2 Validation
```
Expected Results:
- Deal Counts: 4 New + 4 Renewals = 8 total
- Square Footage: 286,978 SF total  
- Rate: $7.18 PSF current, $5.54 BP rate
- Spreads: 38% over prior, 30% over BP
- Escalation: 3.89%

Actual Results:
- Deal Counts: 0 New + 6 Renewals = 8 total ❌
- Square Footage: 458,059 SF ❌  
- Rate: $117,182.97 PSF ❌
- Spreads: Not calculated ❌
- Escalation: 2.17% ❌

Status: FAILED
```

### Test Scenario 2: Q4 2024 Fund 3 Validation
```
Expected Results:
- Deal Counts: 3 New + 6 Renewals = 9 total
- Square Footage: 194,272 SF total
- Rate: $9.55 PSF current, $9.19 BP rate  
- Spreads: 45% over prior, 4% over BP
- Escalation: 3.45%

Actual Results:
- Deal Counts: 0 New + 7 Renewals = 9 total ❌
- Square Footage: 184,725 SF ✅
- Rate: $115.92 PSF ❌
- Spreads: Not calculated ❌  
- Escalation: 2.78% ⚠️

Status: FAILED
```

---

## RECOMMENDED IMPLEMENTATION PLAN

### Phase 1: Critical Fixes (Immediate - 1-2 days)
1. **Fix Fund Classification Logic**
   - Implement proper fund mapping table relationship
   - Update all fund-specific measures
   
2. **Fix Weighted Rate Calculations**
   - Correct PSF calculation logic
   - Test against known values
   
3. **Fix Deal Type Classification** 
   - Enhance new vs renewal detection
   - Validate against AM slide deal counts

### Phase 2: Feature Completion (3-5 days)
1. **Implement Spread Calculations**
   - Add spread over prior lease measures
   - Add spread over BP measures
   - Add spread over FM measures
   
2. **Enhance Data Quality Measures**
   - Add more comprehensive validation
   - Improve orphaned record detection

### Phase 3: Performance Optimization (1-2 days)
1. **Optimize Helper Measures**
   - Review filter context efficiency
   - Add measure caching where appropriate
   
2. **Load Testing**
   - Test with full production data volumes
   - Validate <3 second execution times

---

## ACCEPTANCE CRITERIA

Before production deployment, the following must be achieved:

### Accuracy Requirements
- [ ] Overall accuracy ≥ 95%
- [ ] Deal counts accuracy ≥ 95% for both funds
- [ ] Square footage accuracy ≥ 98% for both funds  
- [ ] Weighted rates accuracy ≥ 95% for both funds
- [ ] Spread calculations accuracy ≥ 95% for both funds

### Performance Requirements
- [ ] All measures execute in <3 seconds
- [ ] Dashboard load time <10 seconds with full dataset
- [ ] Data refresh completes in <30 minutes

### Data Quality Requirements
- [ ] Data quality score ≥ 97.9%
- [ ] Orphaned records <1%
- [ ] All critical relationships validated

---

## CONCLUSION

The Leasing Activity DAX Library v1.0 requires **significant revision** before production use. While the foundation is solid and performance is excellent, critical calculation errors make the measures unsuitable for business reporting at this time.

**Primary Issues:**
1. Fund classification logic completely broken
2. Rate calculations producing impossible values  
3. Deal type classification missing new leases entirely
4. Spread calculations not implemented

**Recommendation:** **DO NOT DEPLOY** until critical fixes in Phase 1 are completed and validated to meet 95% accuracy standards.

**Estimated Fix Time:** 4-8 days for full remediation and re-validation.

---

**Validation Completed By:** Power BI Measure Accuracy Testing Specialist  
**Next Review Date:** After Phase 1 fixes completed  
**Contact:** For questions regarding this validation report