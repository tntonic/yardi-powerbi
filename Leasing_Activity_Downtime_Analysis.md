# Leasing Activity Downtime Analysis Implementation Guide

## Executive Summary

This guide documents the implementation of enhanced leasing activity measures for the fact_leasingactivity table, focusing on SF-weighted rent calculations, lease spreads versus prior leases, and downtime analysis between lease periods.

## Key Features

### 1. SF-Weighted Rent Calculations
All rent calculations use area-weighted formulas to ensure accurate portfolio-level metrics:
- Formula: `SUM(Monthly Rent × SF) / SUM(SF) × 12` for annual PSF calculations
- Separate measures for New Leases, Renewals, and Expansions
- Fund-specific weighted calculations

### 2. Lease Spread Analysis
Compares current executed leases to prior leases:
- Uses "Cash Flow Type" field to distinguish current ("Proposal") vs prior ("Prior Lease")
- Calculates weighted average spread percentages
- Separate measures for New Leases vs Renewals

### 3. Downtime Analysis (New Leases Only)
Calculates vacancy periods between lease cycles:
- **Key Innovation**: Uses prior lease end date (dtEndDate) from "Prior Lease" records
- Matches to new lease start date (dtStartDate) for "New Lease" proposals
- Calculates months of downtime and associated lost rent
- Only applies to new leases (not renewals, as they typically have no gap)

## Required Data Model Setup

### 1. Table Relationships

```
fact_leasingactivity → dim_commcustomer
  From: fact_leasingactivity[Tenant Code]
  To: dim_commcustomer[tenant code]
  Type: Many-to-One (*)
  Direction: Single →

fact_leasingactivity → dim_property
  From: fact_leasingactivity[Property HMY]
  To: dim_property[property hmy]
  Type: Many-to-One (*)
  Direction: Single →

fact_leasingactivity → dim_date
  From: fact_leasingactivity[dtStartDate]
  To: dim_date[date]
  Type: Many-to-One (*)
  Direction: Single →
```

### 2. Fund Column in dim_property
The dim_property table must have a [Fund] column added via Power Query merge:
- Values: "Fund 2", "Fund 3", etc.
- This enables fund-specific filtering and analysis

## Downtime Calculation Logic

### How It Works

1. **Identify New Leases**: Filter for records where:
   - Cash Flow Type = "Proposal"
   - Proposal Type = "New Lease"
   - Deal Stage = "Executed"

2. **Find Prior Lease End Date**: For each new lease:
   - Match on Property HMY
   - Look for Cash Flow Type = "Prior Lease"
   - Find MAX(dtEndDate) where dtEndDate < New Lease Start Date

3. **Calculate Downtime**: 
   - `DATEDIFF(Prior Lease End, New Lease Start, MONTH)`
   - Returns months of vacancy between leases

4. **Calculate Lost Rent**:
   - `Downtime Months × New Monthly Rent`
   - Represents revenue opportunity cost during vacancy

### Example Scenario

```
Property: Building A (Property HMY = 12345)

Prior Lease (Cash Flow Type = "Prior Lease"):
- Tenant: ABC Corp
- End Date: 2024-06-30
- Monthly Rent: $10,000

New Lease (Cash Flow Type = "Proposal", Proposal Type = "New Lease"):
- Tenant: XYZ Inc
- Start Date: 2024-09-01
- Monthly Rent: $11,000

Downtime Calculation:
- Downtime = DATEDIFF(2024-06-30, 2024-09-01, MONTH) = 2 months
- Lost Rent = 2 months × $11,000 = $22,000
```

## Key Measures Reference

### SF-Weighted Measures
- `Executed Leases Weighted Rent PSF`: Overall portfolio weighted average
- `New Leases Weighted Rent PSF`: New leases only
- `Renewals Weighted Rent PSF`: Renewals only
- `Expansions Weighted Rent PSF`: Expansions only

### Spread Measures
- `Executed Lease Spread vs Prior %`: Overall spread percentage
- `New Lease Spread vs Prior %`: New lease spreads
- `Renewal Spread vs Prior %`: Renewal spreads

### Downtime Measures
- `Average Downtime Months (New Leases)`: Mean vacancy period
- `Median Downtime Months (New Leases)`: Median vacancy period
- `Total Downtime Months`: Sum of all vacancy periods
- `Lost Rent from Downtime`: Total revenue impact

### Fund-Specific Measures
- `Fund 2 Weighted Rent PSF`: Fund 2 specific weighted rent
- `Fund 2 Average Downtime Months`: Fund 2 vacancy analysis
- `Fund 2 Lease Spread vs Prior %`: Fund 2 spread analysis
- Similar measures for Fund 3

## Implementation Steps

### Step 1: Import DAX Measures
1. Open Power BI Desktop
2. Navigate to Model View
3. Copy measures from `Enhanced_Leasing_Activity_Measures.dax`
4. Create a new measure table called "Leasing Activity Enhanced"
5. Paste measures into the table

### Step 2: Verify Relationships
1. Check all three relationships are active
2. Ensure single-direction filtering
3. Test relationship integrity with sample queries

### Step 3: Validate Calculations
1. Create test visuals:
   - Table with Property, Prior Lease End, New Lease Start, Downtime Months
   - Verify downtime calculations match manual calculations
2. Check weighted rent calculations:
   - Compare simple average vs weighted average
   - Weighted should reflect larger leases more heavily

### Step 4: Create Dashboards

#### Leasing Performance Dashboard
- KPI: Executed Leases Weighted Rent PSF
- KPI: Average Downtime Months
- Line Chart: Monthly trend of weighted rents by lease type
- Bar Chart: Spread vs Prior by Property

#### Fund Comparison Dashboard
- Matrix: Fund 2 vs Fund 3 metrics
- Columns: Weighted Rent PSF, Average Downtime, Spread %
- Filter: Date range selector

## Validation Queries

### Check Data Coverage
```dax
New Leases with Downtime Data % = 
// Shows what percentage of new leases have prior lease data for downtime calc
// Target: >70% for meaningful analysis
```

### Verify Fund Filtering
```dax
Fund 2 Executed Leases Count vs Fund 3 Executed Leases Count
// Should show distinct counts when dim_property[Fund] is properly populated
```

### Data Quality Check
```dax
Leasing Data Quality %
// Should be >95% if relationships are properly configured
```

## Common Issues & Solutions

### Issue: Downtime shows as blank
**Cause**: No prior lease found for the property
**Solution**: This is expected for properties with first-time leases. Use COALESCE to handle nulls if needed.

### Issue: Negative downtime values
**Cause**: New lease starts before prior lease ends (overlap)
**Solution**: Filter added in measures to exclude negative values (overlaps handled separately)

### Issue: Fund measures return zero
**Cause**: Missing Fund column in dim_property or incorrect values
**Solution**: Verify Power Query merge added Fund column with correct values ("Fund 2", "Fund 3")

### Issue: Weighted rent seems incorrect
**Cause**: Missing or zero dArea values
**Solution**: Measures include filters for dArea > 0 to exclude invalid records

## Performance Considerations

- Downtime calculations use iterative logic (ADDCOLUMNS + CALCULATE)
- For large datasets (>100K records), consider:
  - Pre-calculating downtime in Power Query
  - Creating a summary table for property-level metrics
  - Using aggregation tables for fund-level rollups

## Business Value

### Leasing Team Benefits
- Accurate tracking of market rent achievement (weighted by deal size)
- Clear visibility into lease-up velocity and downtime patterns
- Fund-specific performance comparison

### Asset Management Benefits
- Revenue leakage identification through downtime analysis
- Lease spread tracking for portfolio mark-to-market
- Predictive metrics for vacancy exposure

### Executive Reporting
- Single source of truth for leasing KPIs
- Automated fund-level performance summaries
- Trend analysis with proper area-weighting

## Next Steps

1. **Extend Analysis**:
   - Add free rent period tracking
   - Include TI/LC amortization in effective rents
   - Create cohort analysis by lease vintage

2. **Automate Reporting**:
   - Schedule daily data refreshes
   - Set up alerts for extended downtime
   - Create Power Automate flows for stakeholder updates

3. **Enhance Predictions**:
   - Use historical downtime for vacancy assumptions
   - Build renewal probability models
   - Forecast weighted rent growth by fund

## Support & Maintenance

- **Measure Updates**: Review quarterly for business rule changes
- **Data Quality**: Monitor Leasing Data Quality % weekly
- **Performance**: Check query times monthly, optimize as needed
- **Documentation**: Update this guide with new patterns discovered

---

**Version**: 1.0
**Created**: 2025-01-12
**Last Updated**: 2025-01-12
**Author**: Enhanced Leasing Analytics Team