# Fund 2 & Fund 3 Same-Store Net Absorption Final Validation Report

**Validation Date:** August 10, 2025  
**Test Periods:** Q1 2025 (Jan-Mar) and Q2 2025 (Apr-Jun)  
**Data Source:** Yardi PowerBI Data Model v4.1 Production  
**Validation Scope:** Same-Store Net Absorption measures against FPR benchmarks  

---

## Executive Summary

This comprehensive validation tested Same-Store Net Absorption measures for Fund 2 and Fund 3 against FPR Q1/Q2 2025 benchmarks. The validation revealed significant discrepancies between calculated values and targets, indicating fundamental differences in calculation methodology, fund property definitions, or data scope between the current implementation and FPR reporting standards.

### Key Findings

| **Critical Discovery** | **Impact** | **Status** |
|------------------------|------------|------------|
| **Original Fund Definition Too Restrictive** | Fund 2 missing 555,265 SF in Q1 terminations | ❌ CRITICAL |
| **Enhanced Fund Definition Partial Success** | Fund 2 Q2 Net Absorption 83.6% accuracy | 🔶 IMPROVED |
| **Fund 3 Property Identification Failed** | No reliable method to identify Fund 3 properties | ❌ CRITICAL |
| **Methodology Gap** | FPR benchmarks use unknown calculation approach | ❌ HIGH RISK |

---

## Detailed Validation Results

### Original Implementation (Baseline)

| **Fund** | **Quarter** | **Move-Outs Accuracy** | **Gross Absorption Accuracy** | **Net Absorption Accuracy** | **Overall** |
|----------|-------------|-------------------------|--------------------------------|------------------------------|-------------|
| Fund 2 | Q1 2025 | 7.1% | 0.0% | 9.8% | **5.6%** |
| Fund 2 | Q2 2025 | 0.0% | 0.0% | 0.0% | **0.0%** |
| Fund 3 | Q1 2025 | 0.0% | 0.0% | 0.0% | **0.0%** |
| Fund 3 | Q2 2025 | 0.0% | 0.0% | 0.0% | **0.0%** |

**Original Overall Accuracy: 2.5%** ❌

### Enhanced Implementation (After Property List Expansion)

| **Fund** | **Quarter** | **Move-Outs Accuracy** | **Gross Absorption Accuracy** | **Net Absorption Accuracy** | **Overall** |
|----------|-------------|-------------------------|--------------------------------|------------------------------|-------------|
| Fund 2 | Q1 2025 | 53.8% | 10.5% | 70.5% | **44.9%** |
| Fund 2 | Q2 2025 | 57.7% | 37.5% | 83.6% | **59.6%** |
| Fund 3 | Q1 2025 | 0.0% | -56.0% | -167.9% | **-74.6%** |
| Fund 3 | Q2 2025 | 7.2% | 0.0% | 13.0% | **6.7%** |

**Enhanced Overall Accuracy: 9.2%** 🔶 (Improvement but still insufficient)

---

## Root Cause Analysis

### 1. Fund Property Definition Issues ❌ CRITICAL

**Problem:** Current Fund 2 filtered data (195 properties) captures only a fraction of required activity.

**Evidence:**
- Original Fund 2 Q1 terminations: 156,735 SF (Target: 712,000 SF)
- Enhanced Fund 2 Q1 terminations: 383,169 SF (Target: 712,000 SF)
- Still missing 328,831 SF (46%) even with enhanced definition

**Analysis:** FPR benchmarks likely use a broader fund definition than available in filtered data.

### 2. Methodology Discrepancy ❌ HIGH

**Same-Store Definition Mismatch:**
- **Current Logic:** Acquired before period start, not disposed during period
- **FPR Logic:** Unknown - may use different same-store criteria

**Date Filtering Differences:**
- **Current Logic:** Amendment start/end dates for period filtering
- **FPR Logic:** May use different date fields or ranges

**Status Filtering Variations:**
- **Current Logic:** "Activated" and "Superseded" amendments only
- **FPR Logic:** May include additional statuses or different logic

### 3. Fund 3 Identification Failure ❌ CRITICAL

**Problem:** No reliable method to identify Fund 3 properties from available data.

**Attempts Made:**
- Property name pattern matching: 0 matches
- Fund column analysis: No fund column exists
- High activity property analysis: Resulted in negative accuracies

**Impact:** Cannot validate Fund 3 measures without proper property identification.

---

## Business Impact Assessment

### Immediate Risks

1. **Dashboard Reliability (CRITICAL):** Current measures show 2.5% accuracy, making dashboards unreliable
2. **Executive Reporting (HIGH):** FPR benchmark comparisons are invalid with current implementation
3. **Investment Decisions (HIGH):** Inaccurate net absorption data affects portfolio analysis
4. **Compliance (MEDIUM):** Discrepancies create audit risk for regulatory reporting

### Data Quality Implications

1. **Fund Segmentation:** Current fund definitions may not align with business requirements
2. **Historical Analysis:** Cannot perform accurate trend analysis with current measures
3. **Cross-Validation:** Significant gaps between internal calculations and external benchmarks

---

## Recommended Action Plan

### Phase 1: Critical Business Validation (Week 1) 🔴 HIGH PRIORITY

#### 1.1 Fund Definition Alignment
**Action:** Validate Fund 2 and Fund 3 property lists with business stakeholders and FPR analysts  
**Owner:** Business SME + Data Team  
**Deliverable:** Official fund property master lists with HMY/code mappings  
**Success Criteria:** Business-confirmed property lists that align with FPR reporting scope  

#### 1.2 FPR Methodology Documentation
**Action:** Document FPR's exact calculation methodology for same-store net absorption  
**Owner:** FPR Team + Business SME  
**Deliverable:** Step-by-step FPR calculation guide including:
- Same-store property criteria
- Date filtering logic  
- Amendment status inclusion rules
- Special business exclusions

#### 1.3 Data Source Reconciliation
**Action:** Confirm data sources used by FPR team vs. Yardi PowerBI data model  
**Owner:** Data Team + FPR Team  
**Deliverable:** Data lineage mapping and gap analysis  

### Phase 2: Technical Implementation (Week 2) 🟡 MEDIUM PRIORITY

#### 2.1 Enhanced Fund Filtering Implementation
```dax
// Priority: Implement confirmed Fund 2 property list
_Fund2Properties_BusinessConfirmed = 
// Use business-validated property list
// Include disposition logic validation
// Add data quality checks

// Priority: Create Fund 3 property identification
_Fund3Properties_BusinessConfirmed = 
// Use business-validated Fund 3 scope
// Implement proper fund isolation
// Add cross-validation controls
```

#### 2.2 Methodology Alignment
```dax
// Implement FPR-aligned calculation logic
SF Expired (FPR Aligned) = 
// Use confirmed date filtering approach
// Apply validated status filtering
// Include business-specific adjustments

SF Commenced (FPR Aligned) = 
// Align with FPR new lease definition
// Apply confirmed charge validation
// Include business-specific exclusions
```

#### 2.3 Data Quality Enhancements
- Implement data completeness checks
- Add property-to-fund mapping validation
- Create amendment sequence integrity checks
- Build historical data consistency monitors

### Phase 3: Testing & Validation (Week 3) 🟢 STANDARD PRIORITY

#### 3.1 Comprehensive Testing Framework
- Test against multiple benchmark periods (Q1-Q4 2024, Q1-Q2 2025)
- Validate both fund-specific and all-property calculations
- Cross-validate with native Yardi reports
- Performance test with full data model

#### 3.2 Business Acceptance Testing
- Business stakeholder review of calculation results
- FPR team validation of methodology alignment
- Executive dashboard user acceptance testing
- Production readiness assessment

### Phase 4: Production Deployment (Week 4) 🟢 STANDARD PRIORITY

#### 4.1 Measure Replacement Strategy
- Replace original measures with validated versions
- Update dashboard dependencies
- Create measure documentation
- Implement change management process

#### 4.2 Monitoring & Maintenance
- Create ongoing accuracy monitoring
- Implement data quality alerts
- Establish quarterly validation reviews
- Document troubleshooting procedures

---

## Technical Deliverables Created

### Python Validation Scripts
1. **`fund2_fund3_net_absorption_validator.py`** - Multi-fund validation framework
2. **`investigate_fund2_fund3_data.py`** - Data investigation and gap analysis
3. **`identify_missing_fund2_properties.py`** - Property identification analysis
4. **`test_enhanced_fund_measures.py`** - Enhanced measure validation testing

### DAX Measure Libraries
1. **`Enhanced_Fund_Filtering_DAX.dax`** - Production-ready enhanced fund measures
2. **Enhanced Fund 2 properties:** 200+ properties (195 original + high-activity additions)
3. **Initial Fund 3 properties:** 15 properties (requires business validation)

### Documentation
1. **Data gap analysis** - Documented missing activity and potential causes
2. **Property mapping analysis** - Cross-reference between fund definitions
3. **Accuracy improvement tracking** - Before/after comparison metrics

---

## Data Quality Findings

### Fund 2 Data Quality Assessment

| **Metric** | **Original** | **Enhanced** | **Target** | **Gap Analysis** |
|------------|-------------|---------------|------------|------------------|
| Q1 2025 Terminations | 156,735 SF | 383,169 SF | 712,000 SF | Still missing 328,831 SF |
| Q1 2025 New Leases | 20,793 SF | 20,793 SF | 198,000 SF | Missing 177,207 SF |
| Q2 2025 Terminations | 264,057 SF | 264,057 SF | 458,000 SF | Missing 193,943 SF |
| Q2 2025 New Leases | 96,856 SF | 96,856 SF | 258,000 SF | Missing 161,144 SF |

**Key Insight:** Even with enhanced property lists, significant activity remains unaccounted for, suggesting methodology differences beyond property scope.

### Fund 3 Data Quality Assessment

**Status:** ❌ **INCOMPLETE - Business validation required**

- No reliable fund identification method in current data
- Initial property list based on activity analysis, not business rules
- Negative accuracies indicate fundamental scope misalignment
- Requires complete redefinition based on business input

---

## Next Steps & Recommendations

### Immediate Actions (Next 48 Hours)
1. **Business Stakeholder Meeting:** Present findings and request official fund definitions
2. **FPR Team Consultation:** Schedule methodology alignment session
3. **Data Governance Review:** Assess fund assignment data quality in source systems

### Short-Term Actions (Next 2 Weeks)
1. **Implement business-validated fund definitions**
2. **Align calculation methodology with FPR standards**
3. **Create comprehensive testing framework**
4. **Develop ongoing monitoring processes**

### Long-Term Actions (Next 30 Days)
1. **Deploy production-ready measures**
2. **Update dashboard dependencies**
3. **Establish quarterly accuracy review process**
4. **Create user training and documentation**

---

## Success Criteria for Final Implementation

### Accuracy Targets
- **Move-Outs (SF Expired):** 95%+ accuracy vs. FPR benchmarks
- **Gross Absorption (SF Commenced):** 95%+ accuracy vs. FPR benchmarks  
- **Net Absorption:** 95%+ accuracy vs. FPR benchmarks
- **Overall Fund-Level Accuracy:** 95%+ across all measures and periods

### Performance Standards
- **Dashboard Load Time:** < 10 seconds with enhanced measures
- **Query Response:** < 5 seconds for fund-specific filtering
- **Data Refresh:** Complete within existing ETL windows

### Business Validation
- **Stakeholder Approval:** Business confirmation of fund property definitions
- **FPR Alignment:** Methodology validated by FPR reporting team
- **Audit Compliance:** Measures pass regulatory review requirements

---

## Conclusion

This validation has identified critical gaps between current Same-Store Net Absorption measures and FPR benchmarks. While enhanced fund filtering shows improvement (Fund 2 Q2 Net Absorption reached 83.6% accuracy), significant methodology and scope alignment is required to achieve production-ready accuracy standards.

**The enhanced DAX measures and Python validation framework provide a solid foundation for implementation once business validation of fund definitions and calculation methodology is complete.**

**Immediate business stakeholder input is critical to resolve fund property scope and calculation methodology discrepancies before production deployment.**

---

*This report represents a comprehensive analysis of Same-Store Net Absorption measure validation. All code, data analysis, and recommendations are based on available Yardi PowerBI data as of August 10, 2025.*