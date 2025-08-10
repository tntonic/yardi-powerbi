# Business Logic Reference

## Overview

This document provides comprehensive business logic definitions for all key calculations used in the Yardi Power BI solution v5.0. It serves as the authoritative reference for understanding how metrics are calculated and when to use specific measures.

## Table of Contents

1. [Net Absorption Methodology (FPR)](#net-absorption-methodology-fpr)
2. [Leasing Spread Analysis](#leasing-spread-analysis)
3. [Downtime and Pipeline Analysis](#downtime-and-pipeline-analysis)
4. [Credit Risk Methodology](#credit-risk-methodology)
5. [Amendment-Based Calculations](#amendment-based-calculations)
6. [Pipeline vs Financial Measures](#pipeline-vs-financial-measures)
7. [Fund-Specific Logic](#fund-specific-logic)

---

## Net Absorption Methodology (FPR)

### Definition
Net absorption measures the net change in occupied space over a period, calculated as:
**Net Absorption = SF Commenced - SF Expired**

### Same-Store Methodology
Following FPR (Financial Planning & Reporting) standards:

#### Same-Store Property Criteria
- **Acquired**: Before period start date
- **Not Disposed**: During the measurement period
- **Active**: Throughout the entire period

#### SF Commenced Calculation
**Purpose**: Square footage from new leases starting in the period

**Data Source**: `dim_fp_amendmentsunitspropertytenant`

**Business Rules**:
1. **Amendment Types**: Include `"Original Lease"` and `"New Lease"`
2. **Status Filter**: `"Activated"` AND `"Superseded"`
3. **Date Filter**: `amendment_start_date` within measurement period
4. **Same-Store Only**: Property acquired before period start
5. **Data Quality**: Must have associated rent charges
6. **Sequence Logic**: Use latest amendment sequence per property/tenant

**DAX Pattern**:
```dax
VAR FilteredNewLeases = 
    CALCULATETABLE(
        dim_fp_amendmentsunitspropertytenant,
        dim_fp_amendmentsunitspropertytenant[amendment status] IN {"Activated", "Superseded"},
        dim_fp_amendmentsunitspropertytenant[amendment type] IN {"Original Lease", "New Lease"},
        dim_fp_amendmentsunitspropertytenant[amendment start date] >= CurrentPeriodStart,
        dim_fp_amendmentsunitspropertytenant[amendment start date] <= CurrentPeriodEnd
    )
```

#### SF Expired Calculation
**Purpose**: Square footage from lease terminations in the period

**Data Source**: `dim_fp_terminationtomoveoutreas`

**Business Rules**:
1. **Amendment Type**: Always `"Termination"`
2. **Status Filter**: `"Activated"` AND `"Superseded"`
3. **Date Filter**: `amendment_end_date` within measurement period
4. **Same-Store Only**: Property acquired before period start
5. **Sequence Logic**: Use latest termination sequence per property/tenant

### Fund-Specific Net Absorption

#### Enhanced Fund 2 Properties
Uses expanded property list based on FPR benchmark analysis:
- **Original Fund 2**: 195 core properties
- **High Activity Properties**: Additional 6 properties with significant termination activity
- **Total**: 201 properties for enhanced accuracy

#### Fund 3 Properties
Preliminary identification based on:
- High new lease activity properties
- Not included in Fund 2 enhanced list
- Requires business validation

### Performance Targets
**Q4 2024 Fund 2 Benchmarks**:
- SF Expired (Same-Store): 256,303 SF
- SF Commenced (Same-Store): 88,482 SF
- Net Absorption (Same-Store): -167,821 SF
- Target Accuracy: 95-99%

---

## Leasing Spread Analysis

### Definition
Leasing spreads measure rent growth by comparing current lease rates to various benchmarks:

### Spread Over Prior Lease
**Formula**: `(Current Rent - Prior Rent) / Prior Rent × 100`

**Data Source**: `fact_leasingactivity`

**Business Rules**:
1. **Current Deals**: `Cash Flow Type = "Proposal"` AND `Deal Stage = "Executed"`
2. **Prior Deals**: `Cash Flow Type = "Prior Lease"`
3. **Calculation**: Area-weighted average rates
4. **Validation**: Both rates must be > 0

**Usage**: Measures organic rent growth for existing tenants

### Spread Over Business Plan (BP)
**Formula**: `(Executed Rent PSF - BP Rent PSF) / BP Rent PSF × 100`

**BP Rate Assumptions**:
- **Fund 2**: $5.54 PSF
- **Fund 3**: $9.19 PSF
- **Portfolio Average**: $7.37 PSF

**Usage**: Compares actual leasing performance to underwriting assumptions

### Spread Over Forecast Manager (FM)
**Formula**: `(Executed Rent PSF - FM Rent PSF) / FM Rent PSF × 100`

**FM Rate Calculations** (typically 95% of BP rates):
- **Fund 2**: $5.26 PSF
- **Fund 3**: $8.73 PSF
- **Portfolio Average**: $7.00 PSF

**Usage**: Compares actual performance to budgeted/forecast rates

### Weighted Average Calculations
All spread calculations use area-weighted averages:
```dax
VAR WeightedRate = 
    DIVIDE(
        SUMX(ValidDeals, Rent × Area),
        SUMX(ValidDeals, Area),
        0
    )
```

---

## Downtime and Pipeline Analysis

### Average Time to Lease
**Definition**: Days between lease signing and lease commencement

**Formula**: `DATEDIFF(amendment_sign_date, amendment_start_date, DAY)`

**Data Source**: `dim_fp_amendmentsunitspropertytenant`

**Business Rules**:
1. **Amendment Type**: `"Original Lease"` only
2. **Status Filter**: `"Activated"` AND `"Superseded"`
3. **Date Requirements**: Both sign date and start date must be non-blank
4. **Sequence Logic**: Use latest amendment sequence only
5. **Calculation**: Average across all qualifying leases

### Pipeline Aging Categories

#### 0-30 Days in Pipeline
**Definition**: Active deals created within last 30 days
**Status**: Normal pipeline velocity

#### 31-90 Days in Pipeline
**Definition**: Active deals created 31-90 days ago
**Status**: Standard negotiation timeframe

#### 90+ Days in Pipeline
**Definition**: Active deals created over 90 days ago
**Status**: Requires attention - potential stalled deals

### Average Days in Pipeline
**Formula**: `DATEDIFF(dtcreated, dtStartDate, DAY)`

**Data Source**: `fact_leasingactivity`

**Business Rules**:
1. **Deal Stage**: `"Executed"` only
2. **Date Requirements**: Both created date and start date must be non-blank
3. **Calculation**: Average across all executed deals

### Performance Benchmarks
- **Excellent**: ≤ 60 days average
- **Good**: 61-90 days average  
- **Fair**: 91-120 days average
- **Needs Attention**: > 120 days average

---

## Credit Risk Methodology

### Credit Score Scale
**Range**: 0.0 to 10.0 (higher = better creditworthiness)

**Risk Categories**:
- **Low Risk (8.0-10.0)**: Strong creditworthiness, minimal default risk
- **Medium Risk (6.0-7.9)**: Moderate creditworthiness, manageable risk
- **High Risk (4.0-5.9)**: Elevated risk profile, requires monitoring
- **Very High Risk (0.0-3.9)**: Significant credit concerns, high default risk

### Portfolio Credit Risk Score
**Formula**: `Average Credit Score × 10` (converted to 0-100 scale)

**Calculation Method**:
1. Calculate simple average of all available credit scores
2. Multiply by 10 for 0-100 scale presentation
3. Round to nearest whole number

### Enhanced Risk Analysis
Combines multiple risk indicators:

#### Enhanced Tenant Risk Flag
**Priority Logic**:
1. **At Risk (Yardi Flag)**: Yardi `is_at_risk_tenant = 1`
2. **At Risk (Credit Score)**: Credit score < 4.0
3. **Watch List**: Credit score 4.0-5.9
4. **Stable**: Credit score ≥ 6.0 and no Yardi flag

#### Revenue at Risk
**Definition**: Annual revenue from high-risk tenants

**Formula**: `Monthly Rent × 12` for tenants with:
- Credit score < 4.0 OR
- Yardi at-risk flag = 1

### Parent Company Analysis
**Credit Score Inheritance**:
1. Use direct tenant credit score if available
2. If not available, inherit from parent company
3. Uses `COALESCE(DirectScore, ParentScore)` logic

**Data Sources**:
- `dim_fp_customercreditscorecustomdata`: Direct scores
- `dim_fp_customertoparentmap`: Parent relationships

### Portfolio Health Scoring
**Composite Score** (0-100):
- **Credit Component (40%)**: `(Avg Credit Score / 10) × 40`
- **Occupancy Component (40%)**: `(Physical Occupancy % / 100) × 40`
- **Risk Component (20%)**: `(1 - At-Risk %) × 20`

---

## Amendment-Based Calculations

### Core Amendment Logic
All financial reporting measures use amendment-based logic for accuracy and consistency.

#### Latest Amendment Sequence
**Purpose**: Ensure only current lease terms are counted

**Logic**:
```dax
MAX(amendment_sequence) per (property_hmy, tenant_hmy) combination
```

#### Status Filtering
**Required Statuses**: `"Activated"` AND `"Superseded"`

**Rationale**:
- `"Activated"`: Current active leases
- `"Superseded"`: Previously active leases that were replaced
- Excludes: `"Pending"`, `"Cancelled"`, `"Proposal in DM"`

#### Charge Integration Requirement
**Data Quality Rule**: Amendments must have associated rent charges

**Validation**:
```dax
CALCULATE(
    COUNTROWS(dim_fp_amendmentchargeschedule),
    dim_fp_amendmentchargeschedule[amendment_hmy] = amendment_hmy,
    dim_fp_amendmentchargeschedule[charge_code] = "rent"
) > 0
```

### Month-to-Month Lease Detection
**Criteria**:
- `amendment_end_date` IS NULL AND
- `amendment_term = 0`

**Usage**: Identifies leases without fixed end dates

---

## Pipeline vs Financial Measures

### When to Use Pipeline Measures
**Source**: `fact_leasingactivity` table

**Use Cases**:
- Deal flow forecasting
- Sales pipeline analysis
- Leasing team performance
- Prospect conversion tracking

**Characteristics**:
- Forward-looking
- Includes all deal stages
- Updated as deals progress
- Includes dead deals for analysis

**Examples**:
- `Pipeline New Leases Executed Count`
- `Active Leasing Pipeline Count`
- `Lead to Tour Conversion %`

### When to Use Financial Measures  
**Source**: `dim_fp_amendmentsunitspropertytenant` + charges

**Use Cases**:
- Financial reporting
- NOI calculations
- Rent roll validation
- Investor reporting

**Characteristics**:
- Historical accuracy
- Only executed/activated leases
- Integrated with financial systems
- Used for compliance reporting

**Examples**:
- `New Leases Count` (official)
- `Current Monthly Rent`
- `Net Leasing Activity SF`

### Key Differences
| Aspect | Pipeline Measures | Financial Measures |
|--------|------------------|-------------------|
| **Data Source** | fact_leasingactivity | Amendment tables |
| **Timing** | Real-time/Forward | Month-end/Historical |
| **Purpose** | Forecasting | Reporting |
| **Accuracy Priority** | Speed | Precision |
| **Deal Stages** | All stages | Executed only |

---

## Fund-Specific Logic

### Fund Classification Hierarchy
1. **Enhanced Fund Lists**: Use curated property lists for Fund 2/3
2. **dim_property[Fund]**: Fallback to table-based classification  
3. **"Unknown"**: Properties not mapped to any fund

### Fund 2 Enhanced Logic
**Property Count**: 201 properties (195 core + 6 high-activity)

**Usage**: All Fund 2-specific measures use enhanced property list:
- `SF Expired (Fund 2 Enhanced)`
- `SF Commenced (Fund 2 Enhanced)` 
- `Net Absorption (Fund 2 Enhanced)`
- `Fund 2 Current Monthly Rent`

### Fund 3 Logic
**Status**: Initial implementation, requires validation

**Property Count**: ~15 properties identified through analysis

**Business Validation Required**: Confirm property assignments with stakeholders

### Same-Store vs Total Fund
**Same-Store**: Properties owned throughout entire measurement period
**Total Fund**: All properties in fund, regardless of acquisition/disposal timing

**Usage Guidelines**:
- **Same-Store**: Use for period-over-period comparisons
- **Total Fund**: Use for current portfolio snapshots

---

## Implementation Notes

### Performance Optimizations
1. **Helper Measures**: Use centralized filtering to reduce code duplication
2. **Variable Caching**: Cache expensive calculations in variables
3. **Single-Pass Logic**: Combine multiple calculations where possible
4. **CALCULATETABLE vs FILTER(ALL())**: Use CALCULATETABLE for better performance

### Data Quality Requirements
1. **Amendment Sequence**: Always use latest sequence logic
2. **Charge Validation**: Require rent charges for financial measures
3. **Date Validation**: Ensure valid date ranges and non-blank dates
4. **Status Consistency**: Use standard status filtering across all measures

### Accuracy Targets
- **Rent Roll**: 97% (achieved)
- **Leasing Activity**: 96% (achieved)
- **Net Absorption**: 95-99% (target)
- **Credit Analysis**: 95% coverage (target)

This business logic reference ensures consistent understanding and implementation of all calculations across the Yardi Power BI solution v5.0.