# DAX Measure Cross-Reference Guide

## Overview
This guide helps you choose the right measure for your analysis needs, particularly when deciding between standard and enhanced measures.

## Rent Calculations: Standard vs Enhanced

### When to Use Standard Measures

**Use Standard Measures When:**
- Analyzing individual properties or units
- Comparing properties of similar size
- Quick directional analysis
- Data limitations prevent weighting

**Standard Measures:**
- `Average Base Rent` - Simple average across leases
- `Pipeline Average Rent` - Unweighted pipeline average
- `Average Rent PSF` - Simple average of rent PSF values

### When to Use Enhanced (Weighted) Measures

**Use Enhanced Weighted Measures When:**
- Analyzing portfolio-level metrics
- Comparing funds or large property groups
- Executive reporting requiring accuracy
- Investment committee presentations
- Properties vary significantly in size

**Enhanced Weighted Measures:**
- `Executed Leases Weighted Rent PSF` (#21) - Portfolio accurate rent
- `New Leases Weighted Rent PSF` - Weighted new lease rent
- `Renewals Weighted Rent PSF` - Weighted renewal rent
- `Fund Executed Leases Weighted Rent PSF` (#25) - Fund-specific weighted

### Example Comparison

**Scenario**: Portfolio with two leases
- Lease A: 1,000 SF @ $50 PSF
- Lease B: 50,000 SF @ $30 PSF

**Results:**
- Simple Average: ($50 + $30) / 2 = **$40 PSF** ❌ (misleading)
- Weighted Average: (1,000×$50 + 50,000×$30) / 51,000 = **$30.39 PSF** ✅ (accurate)

## Leasing Activity: Financial vs Pipeline

### Financial Reporting Measures
**Source**: Amendment-based tables
**Purpose**: Official reporting, compliance, investor reports
**Accuracy**: 95-99% validated against Yardi

**Key Measures:**
- `New Leases Count` - From amendments table
- `Renewals Count` - From amendments table
- `Current Monthly Rent` - Latest amendment sequence
- `Current Leased SF` - From amendments

### Pipeline Analysis Measures
**Source**: fact_leasingactivity table
**Purpose**: Forward-looking analysis, sales tracking
**Accuracy**: Directional, not validated

**Key Measures:**
- `Pipeline New Leases Count` - All stages
- `Active Pipeline SF` - Pre-execution deals
- `Pipeline Value (Annual)` - Potential revenue
- `Deal Conversion Rate` - Pipeline efficiency

## Downtime Analysis: New vs Existing

### New Lease Downtime (Enhanced v5.1)
**Measure**: `Average Downtime Months (New Leases)` (#22)
**Calculation**: Prior lease end date to new lease start date
**Use Cases:**
- Vacancy period analysis
- Lost rent calculations
- Property turnover efficiency
- Market absorption timing

### Renewal Analysis
**Note**: Renewals typically have no downtime
**Alternative Metrics:**
- Early renewal timing
- Lease overlap periods
- Retention effectiveness

## Spread Calculations: Types and Usage

### Spread vs Prior Lease
**Measure**: `Executed Lease Spread vs Prior %` (#24)
**Calculation**: Weighted comparison of current vs prior rates
**Use For:**
- Rent growth achievement
- Market rent capture
- Negotiation effectiveness

### Spread vs Business Plan
**Measure**: `Average Deal Spread Over BP %`
**Benchmarks**: 
- Fund 2: $5.54 PSF
- Fund 3: $9.19 PSF
**Use For:**
- Underwriting validation
- Investment performance

### Spread vs Market
**Measure**: `Spread Over Market Rent %`
**Requires**: Market rent data table
**Use For:**
- Competitive positioning
- Pricing strategy validation

## Fund-Specific Analysis

### Dynamic Fund Filtering
**Pattern**: Measures adapt to selected fund context
**Example**: `Fund Executed Leases Weighted Rent PSF` (#25)

### Static Fund Measures
**Pattern**: Hard-coded fund filters
**Examples:**
- `Fund 2 Weighted Rent PSF`
- `Fund 3 Average Downtime Months`

### When to Use Each:
- **Dynamic**: Interactive dashboards with fund slicers
- **Static**: Fixed reports, fund-specific pages

## Migration Guide: v5.0 to v5.1 Enhanced

### Measures to Replace

| Old Measure (v5.0) | New Measure (v5.1 Enhanced) | Reason |
|-------------------|--------------------------|---------|
| `Average Rent PSF` | `Executed Leases Weighted Rent PSF` | Accuracy |
| `Pipeline Average Rent` | `New Leases Weighted Rent PSF` | SF weighting |
| `Simple Lease Spread` | `Executed Lease Spread vs Prior %` | Weighted accuracy |
| `Vacancy Days` | `Average Downtime Months (New Leases)` | Prior lease logic |
| `Portfolio Rent` | `Fund Executed Leases Weighted Rent PSF` | Fund filtering |

### Measures to Keep

These standard measures remain valid for specific use cases:
- `Physical Occupancy %` - Standard calculation sufficient
- `NOI (Net Operating Income)` - Financial reporting standard
- `Total Revenue` - GL-based, no weighting needed
- `WALT (Months)` - Already weighted by design

## Implementation Checklist

### Required Setup for Enhanced Measures
- [ ] fact_leasingactivity table loaded
- [ ] Relationship: fact_leasingactivity[Property HMY] → dim_property[id]
- [ ] Relationship: fact_leasingactivity[Tenant Code] → dim_commcustomer[tenant code]
- [ ] Relationship: fact_leasingactivity[dtStartDate] → dim_date[date]
- [ ] dim_property[Fund] column populated via Power Query

### Validation Steps
1. Compare weighted vs unweighted results
2. Verify downtime calculations with sample properties
3. Test fund filtering with known properties
4. Validate spreads against manual calculations

## Quick Decision Tree

```
Need Portfolio Metrics?
├── YES → Use Enhanced Weighted Measures
│   ├── Rent Analysis → Executed Leases Weighted Rent PSF (#21)
│   ├── Vacancy Analysis → Average Downtime Months (#22)
│   └── Fund Comparison → Fund Executed Leases Weighted Rent PSF (#25)
└── NO → Use Standard Measures
    ├── Property Level → Standard amendment-based measures
    └── Quick Analysis → Simple averages acceptable
```

## Performance Considerations

### Enhanced Measures (Iterative Calculations)
- More complex calculations
- Longer processing time for large datasets
- Consider pre-aggregating for dashboards

### Standard Measures (Direct Aggregations)
- Faster performance
- Suitable for real-time interactions
- Lower memory footprint

## Support and Questions

For additional guidance on measure selection:
1. Check measure documentation in DAX files
2. Review Business Logic Reference (05_Business_Logic_Reference.md)
3. Validate with sample data using Downtime_Validation.sql
4. Test both versions and compare results

---

**Version**: 1.0
**Created**: 2025-01-12
**Last Updated**: 2025-01-12
**Compatibility**: Yardi Power BI v5.1 Enhanced