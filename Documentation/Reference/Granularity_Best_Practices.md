# Table Granularity Specifications

## Overview

This document defines the granularity (grain) of each table in the Yardi BI data model, essential for accurate aggregations and preventing double-counting in calculations.

## Understanding Granularity

### Granularity Definitions
- **Lowest Granularity (Finest Detail)**: The most detailed level at which data is stored
- **Highest Granularity (Coarsest Aggregation)**: The most summarized level
- **Natural Grain**: The inherent level of detail that makes business sense

## Fact Table Granularity

### fact_total
```
Grain: Property + Month + Book + Account + Amount Type
Primary Key: Composite of above fields
Row Represents: A single financial transaction or journal entry

Granularity Levels:
- Lowest: Individual GL line items by property/month/book/account
- Natural: Monthly financial activity by property and account
- Highest: Total portfolio financial summary

Volume Indicators:
- Rows per property per month: 100-500 typically
- Total rows: Millions for multi-year history

Aggregation Rules:
- Sum amounts within same account range for totals
- Filter by amount_type = 'Actual' for realized transactions
- Filter by book for specific reporting views
```

### fact_occupancyrentarea
```
Grain: Property + First Day of Month + Lease Type
Primary Key: Composite of above fields
Row Represents: Monthly occupancy snapshot for a property/lease type

Granularity Levels:
- Lowest: Property + Month + Lease Type combination
- Natural: Monthly property occupancy metrics
- Highest: Portfolio occupancy summary

Volume Indicators:
- Rows per property: 12 per year (monthly snapshots)
- Multiplied by lease types if segmented

Aggregation Rules:
- Latest month for current metrics
- Average for period trends
- Sum areas across properties for portfolio totals
```

### fact_expiringleaseunitarea
```
Grain: Property + Tenant + Unit + Lease Dates
Primary Key: Composite of above fields
Row Represents: A specific unit lease with expiration details

Granularity Levels:
- Lowest: Individual unit leases
- Natural: Tenant leases by property
- Highest: Portfolio lease expiration summary

Volume Indicators:
- Rows per property: Equal to number of active leases
- Changes with lease activity

Aggregation Rules:
- Sum expiring_area for total expiring square footage
- Count distinct tenants for tenant counts
- Filter by date ranges for expiration analysis
```

### fact_accountsreceivable
```
Grain: Property + Tenant + Invoice Date + Invoice Number
Primary Key: Composite of above fields
Row Represents: Individual AR invoice or payment

Granularity Levels:
- Lowest: Individual invoice line items
- Natural: Tenant AR balances by property
- Highest: Portfolio AR summary

Aggregation Rules:
- Sum amounts for total AR
- Age by invoice_date for aging buckets
- Group by tenant for collection analysis
```

### fact_fp_fmvm_marketunitrates
```
Grain: Property + Unit + Profile Date
Primary Key: Composite of above fields
Row Represents: Market rate assessment for a specific unit

Granularity Levels:
- Lowest: Unit-level market rates
- Natural: Property average market rates
- Highest: Portfolio market position

Aggregation Rules:
- Average rates weighted by unit area
- Latest profile date for current market rates
- Compare with actual rents for gap analysis
```

## Dimension Table Granularity

### dim_property
```
Grain: One row per property
Primary Key: property_id
Natural Key: property_code
Row Represents: A single real estate property

Cardinality: Low (typically 10s to 100s of properties)
Relationships: One-to-many with most fact tables
```

### dim_unit
```
Grain: One row per rentable unit
Primary Key: unit_id
Natural Key: property_id + unit_code
Row Represents: A single rentable space within a property

Cardinality: Medium (100s to 1000s of units)
Relationships: Many-to-one with dim_property
```

### dim_commcustomer / dim_commlease
```
Grain: One row per tenant/customer
Primary Key: customer_id or tenant_id
Row Represents: A commercial tenant entity

Cardinality: Medium (100s to 1000s of tenants)
Special Considerations:
- May have multiple leases per tenant
- Historical and current tenants included
```

### dim_account
```
Grain: One row per GL account
Primary Key: account_id
Natural Key: account_code
Row Represents: A single chart of accounts entry

Cardinality: Medium (100s of accounts)
Hierarchy: Self-referencing parent-child structure
```

### dim_book
```
Grain: One row per accounting book
Primary Key: book_id
Row Represents: An accounting perspective (Accrual, Cash, Budget, etc.)

Cardinality: Very Low (typically <10 books)
Critical Books:
- Book 1: Standard Accrual
- Book 46: FPR (Financial Planning & Reporting)
- Budget books: Annual budgets
```

### dim_date
```
Grain: One row per calendar date
Primary Key: date
Row Represents: A single calendar day

Cardinality: Medium (365 days × number of years)
Special Attributes: Fiscal periods, quarters, holidays
```

## Amendment Table Granularity (Critical)

### dim_fp_amendmentsunitspropertytenant
```
Grain: Property + Tenant + Amendment Sequence
Primary Key: amendment_hmy
Row Represents: A specific lease amendment version

Granularity Levels:
- Lowest: Individual amendments including historical versions
- Natural: Latest amendment per property/tenant
- Highest: Current rent roll

Critical Business Rules:
- Multiple amendments per tenant (sequence 0, 1, 2, etc.)
- Include both "Activated" AND "Superseded" status
- Latest sequence determines current lease terms
- Historical amendments retained for audit trail

Aggregation Rules:
- Filter for MAX(sequence) per property/tenant for current
- Include Superseded status in latest sequence logic
- Exclude Termination type for active leases
```

### dim_fp_amendmentchargeschedule
```
Grain: Amendment + Charge Type + Effective Date Range
Primary Key: Composite key
Row Represents: Rent and charge details for an amendment period

Granularity Levels:
- Lowest: Individual charge lines by date range
- Natural: Monthly charges per amendment
- Highest: Total rent roll

Aggregation Rules:
- Sum monthly_amount for total rent
- Filter by date range for point-in-time rent
- Join to amendments for tenant attribution
```

## Bridge Table Granularity

### dim_accounttreeaccountmapping
```
Grain: Account + Tree Node combination
Primary Key: account_id + account_tree_detail_id
Purpose: Many-to-many relationship resolver

Usage:
- Enables flexible financial reporting hierarchies
- Same account can appear in multiple report sections
```

### dim_fp_naicstotenantmap
```
Grain: NAICS Code + Tenant combination
Primary Key: naics_code + tenant_hmy
Purpose: Industry classification bridge

Usage:
- Enables industry diversification analysis
- Tenant can have multiple industry classifications
```

### dim_fp_unitto_amendmentmapping
```
Grain: Unit + Amendment combination
Primary Key: unit_hmy + amendment_hmy
Purpose: Multi-unit lease tracking

Usage:
- Tracks which units are in each amendment
- Handles multi-unit leases
```

## Aggregation Best Practices

### Property Level Aggregations
```dax
// Always aggregate at property level first for performance
Property Summary = 
SUMMARIZE(
    fact_total,
    dim_property[property_id],
    dim_property[property_name],
    "Total Revenue", [Total Revenue],
    "Total Expenses", [Operating Expenses],
    "NOI", [NOI (Net Operating Income)]
)
```

### Time-Based Aggregations
```dax
// Be explicit about time grain
Monthly Summary = 
SUMMARIZE(
    fact_total,
    dim_date[year],
    dim_date[month],
    "Monthly Total", SUM(fact_total[amount])
)
```

### Avoiding Double-Counting
```dax
// Use DISTINCTCOUNT for unique counts across grains
Unique Tenant Count = 
DISTINCTCOUNT(dim_fp_amendmentsunitspropertytenant[tenant_hmy])

// Not SUM of counts which would double-count
```

### Handling Different Grains
```dax
// When mixing different grain tables, use appropriate aggregation
Combined Metric = 
VAR MonthlyFinancials = 
    CALCULATE(
        [Total Revenue],
        fact_total[month] = MAX(dim_date[date])
    )
VAR CurrentOccupancy = 
    CALCULATE(
        [Physical Occupancy %],
        fact_occupancyrentarea[first_day_of_month] = EOMONTH(MAX(dim_date[date]), 0)
    )
RETURN
    MonthlyFinancials * CurrentOccupancy
```

## Common Granularity Pitfalls

### 1. Amendment Sequence Confusion
```
Problem: Not filtering for latest sequence causes duplicate tenants
Solution: Always use MAX(sequence) per property/tenant
```

### 2. Time Period Misalignment
```
Problem: Mixing different time grains (daily vs monthly)
Solution: Standardize to common grain (usually monthly)
```

### 3. Book Aggregation
```
Problem: Summing across all books inflates totals
Solution: Filter to specific book before aggregation
```

### 4. Status Filtering
```
Problem: Only including "Activated" misses valid "Superseded" records
Solution: Include both statuses in amendment queries
```

## Validation Queries

### Check Granularity
```sql
-- Verify fact_total grain
SELECT 
    property_id,
    month,
    book_id,
    account_id,
    amount_type,
    COUNT(*) as row_count
FROM fact_total
GROUP BY 
    property_id,
    month,
    book_id,
    account_id,
    amount_type
HAVING COUNT(*) > 1;  -- Should return no rows if grain is correct

-- Verify amendment grain
SELECT 
    property_hmy,
    tenant_hmy,
    amendment_sequence,
    COUNT(*) as amendment_count
FROM dim_fp_amendmentsunitspropertytenant
WHERE amendment_status IN ('Activated', 'Superseded')
GROUP BY 
    property_hmy,
    tenant_hmy,
    amendment_sequence
HAVING COUNT(*) > 1;  -- Should return no rows if grain is correct
```

### Monitor Row Counts
```sql
-- Table row count summary
SELECT 
    'fact_total' as table_name,
    COUNT(*) as row_count,
    COUNT(DISTINCT property_id) as unique_properties,
    COUNT(DISTINCT month) as unique_months
FROM fact_total
UNION ALL
SELECT 
    'fact_occupancyrentarea',
    COUNT(*),
    COUNT(DISTINCT property_id),
    COUNT(DISTINCT first_day_of_month)
FROM fact_occupancyrentarea
UNION ALL
SELECT 
    'dim_fp_amendmentsunitspropertytenant',
    COUNT(*),
    COUNT(DISTINCT property_hmy),
    COUNT(DISTINCT tenant_hmy)
FROM dim_fp_amendmentsunitspropertytenant;
```

## Performance Impact of Grain

### Storage Optimization
- Lower grain = more rows = more storage
- Consider summary tables for frequently accessed aggregations
- Partition large fact tables by date

### Query Performance
- Filter early in the query to reduce row processing
- Use the appropriate grain level for the analysis
- Create aggregated tables for dashboard performance

### Incremental Refresh Strategy
- Monthly grain allows monthly refresh windows
- Daily grain requires more frequent updates
- Balance freshness needs with processing resources