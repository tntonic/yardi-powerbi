# Table Relationships Reference

## Overview

This document provides a comprehensive reference for all table relationships in the Yardi BI Power BI data model, including cardinality, filter direction, and business purpose for each relationship.

## Table Granularity and Relationships

### Understanding Grain in Relationships
The granularity (grain) of tables fundamentally determines how relationships function and what results they produce. Misunderstanding table grain is a primary cause of incorrect calculations and double-counting.

### Key Granularity Rules
```
1. Fact Table Grain Awareness:
   - fact_total: Property + Month + Book + Account + Amount Type
   - fact_occupancyrentarea: Property + First Day of Month + Lease Type
   - fact_expiringleaseunitarea: Property + Tenant + Unit + Lease Dates
   - fact_accountsreceivable: Property + Tenant + Invoice Date + Invoice Number

2. Dimension Table Grain:
   - dim_property: One row per property (lowest grain)
   - dim_unit: One row per rentable unit
   - dim_commcustomer: One row per tenant entity
   - dim_fp_amendmentsunitspropertytenant: Property + Tenant + Amendment Sequence

3. Relationship Impact on Aggregation:
   - One-to-Many: Dimension grain determines fact aggregation level
   - Many-to-Many: Requires bridge table to maintain proper grain
   - Bi-directional: Must consider grain from both directions
```

### Granularity Best Practices
```
Before Creating Relationships:
✓ Document the grain of both tables
✓ Verify primary/foreign key uniqueness
✓ Test for unexpected many-to-many scenarios
✓ Consider aggregation implications

Common Granularity Pitfalls:
✗ Joining tables at different time grains (daily vs monthly)
✗ Not accounting for historical records in dimensions
✗ Ignoring composite keys in fact tables
✗ Assuming one-to-one when it's actually one-to-many
```

### Amendment Granularity (Critical)
```
Amendment Table Special Considerations:
- Multiple amendments per property/tenant (sequences 0, 1, 2...)
- Include both "Activated" AND "Superseded" status
- Latest sequence logic required for current state
- Historical amendments affect relationship cardinality

Correct Pattern:
Join on amendment hmy for specific amendment
Filter for MAX(sequence) for current state only
```

## Relationship Configuration Standards

### Power BI Configuration Rules
- **Calendar Relationships**: Bi-directional filtering enabled
- **All Other Relationships**: Single direction (dimension → fact)
- **Cardinality**: Always explicitly defined (never auto-detect)
- **Active Relationships**: All relationships should be active
- **Inactive Relationships**: None (use bridge tables for complex scenarios)

## Core Hub Relationships

### dim_property (Central Hub)
The property dimension serves as the central hub for most relationships.

#### Property → Fact Relationships
```
dim_property → fact_total
├── Join: property id = property id
├── Cardinality: One to Many (1:*)
├── Filter Direction: Single (property → fact)
├── Business Purpose: Links properties to financial transactions
├── Volume: High (most voluminous relationship)
└── Grain Impact: Aggregates monthly financial data by property

dim_property → fact_occupancyrentarea
├── Join: property id = property id
├── Cardinality: One to Many (1:*)
├── Filter Direction: Single (property → fact)
├── Business Purpose: Links properties to occupancy metrics
├── Grain: Monthly snapshots per property
└── Aggregation: Enables portfolio-level occupancy rollups

dim_property → fact_accountsreceivable
├── Join: property id = property id
├── Cardinality: One to Many (1:*)
├── Filter Direction: Single (property → fact)
├── Business Purpose: Links properties to AR transactions
└── Usage: Cash flow and collection analysis

dim_property → fact_expiringleaseunitarea
├── Join: property id = property id
├── Cardinality: One to Many (1:*)
├── Filter Direction: Single (property → fact)
└── Business Purpose: Links properties to lease expiration data
```

#### Property → Dimension Relationships
```
dim_property → dim_unit
├── Join: property id = property id
├── Cardinality: One to Many (1:*)
├── Filter Direction: Single (property → unit)
├── Business Purpose: Property contains multiple units
└── Hierarchy: Portfolio → Property → Building → Unit

dim_property → dim_commcustomer
├── Join: property id = property id
├── Cardinality: One to Many (1:*)
├── Filter Direction: Single (property → customer)
├── Business Purpose: Property can have multiple tenants
└── Note: May be many-to-many in reality (tenants across properties)

dim_property → dim_fp_amendmentsunitspropertytenant
├── Join: property_hmy = property_hmy
├── Cardinality: One to Many (1:*)
├── Filter Direction: Single (property → amendment)
├── Business Purpose: Property has multiple lease amendments
└── Critical: Core relationship for rent roll calculations

dim_property → dim_fp_buildingcustomdata
├── Join: hmy_property = hmy_property
├── Cardinality: One to One (1:1)
├── Filter Direction: Single (property → building data)
├── Business Purpose: Extended property attributes
└── Contains: Market, status, acquisition data
```

## Date Dimension Relationships (Bi-directional)

### dim_date ↔ Fact Tables
All date relationships use bi-directional filtering to enable time intelligence.

```
dim_date ↔ fact_total
├── Join: date = month
├── Cardinality: One to Many (1:*)
├── Filter Direction: Both (bi-directional)
├── Business Purpose: Time intelligence for financial data
└── Functions: YoY, QoQ, rolling periods, time comparisons

dim_date ↔ fact_occupancyrentarea
├── Join: date = first_day_of_month
├── Cardinality: One to Many (1:*)
├── Filter Direction: Both (bi-directional)
├── Business Purpose: Time intelligence for occupancy trends
└── Grain: Monthly snapshots

dim_date ↔ fact_accountsreceivable
├── Join: date = invoice_date
├── Cardinality: One to Many (1:*)
├── Filter Direction: Both (bi-directional)
├── Business Purpose: AR aging and collection time analysis
└── Usage: Payment trend analysis

dim_date ↔ fact_expiringleaseunitarea
├── Join: date = lease_from_date (primary)
├── Additional: date = lease_to_date (secondary)
├── Cardinality: One to Many (1:*)
├── Filter Direction: Both (bi-directional)
└── Business Purpose: Lease term and expiration analysis
```

## Financial Dimension Relationships

### Account Structure Relationships
```
dim_account → fact_total
├── Join: account_id = account_id
├── Cardinality: One to Many (1:*)
├── Filter Direction: Single (account → fact)
├── Business Purpose: Links GL accounts to transactions
└── Account Codes: 4xxxx=Revenue, 5xxxx=Expenses, 6xxxx=Other

dim_account → dim_account (Self-Reference)
├── Join: parent_account_id = account_id
├── Cardinality: Many to One (*:1)
├── Filter Direction: Single (parent → child)
├── Business Purpose: Account hierarchy for rollups
└── Usage: Financial statement groupings
```

### Account Tree Relationships (Many-to-Many)
```
dim_account ↔ dim_accounttreeaccountmapping ↔ dim_accounttree

Bridge Implementation:
dim_account → dim_accounttreeaccountmapping
├── Join: account_id = account_id
├── Cardinality: One to Many (1:*)
└── Purpose: Account can appear in multiple tree positions

dim_accounttree → dim_accounttreeaccountmapping
├── Join: account_tree_detail_id = account_tree_detail_id
├── Cardinality: One to Many (1:*)
└── Purpose: Tree node can contain multiple accounts

Business Purpose:
- Flexible financial reporting hierarchies
- Same account in multiple report sections
- Dynamic financial statement generation
```

### Book Relationships
```
dim_book → fact_total
├── Join: book_id = book_id
├── Cardinality: One to Many (1:*)
├── Filter Direction: Single (book → fact)
├── Business Purpose: Multiple accounting views of same data
└── Key Books: 1=Cash, 2=Accrual, 46=FPR

// Note: For FPR book (book_id = 46) calculations, filter fact_total table
```

## Amendment & Lease Relationships

### Core Amendment Chain
```
dim_fp_amendmentsunitspropertytenant → dim_fp_amendmentchargeschedule
├── Join: amendment hmy = amendment hmy
├── Cardinality: One to Many (1:*)
├── Filter Direction: Single (amendment → charges)
├── Business Purpose: Amendment has multiple charge lines
├── Critical for: Rent roll calculations
├── Grain: Multiple charges per amendment (rent, CAM, tax, etc.)
└── CRITICAL: Must filter for latest sequence to avoid duplicates

dim_fp_amendmentsunitspropertytenant → dim_fp_terminationtomoveoutreas
├── Join: amendment hmy = amendment hmy
├── Cardinality: One to Many (1:*)
├── Filter Direction: Single (amendment → termination)
├── Business Purpose: Links terminations to move-out reasons
└── Usage: Retention analysis and churn prevention
```

### Unit-Amendment Bridge (Many-to-Many)
```
dim_unit ↔ dim_fp_unitto_amendmentmapping ↔ dim_fp_amendmentsunitspropertytenant

Bridge Implementation:
dim_unit → dim_fp_unitto_amendmentmapping
├── Join: unit_hmy = unit_hmy
├── Cardinality: One to Many (1:*)
└── Purpose: Unit can be in multiple amendments over time

dim_fp_amendmentsunitspropertytenant → dim_fp_unitto_amendmentmapping
├── Join: amendment hmy = amendment hmy
├── Cardinality: One to Many (1:*)
└── Purpose: Amendment can contain multiple units

Business Purpose:
- Tracks which units are affected by each amendment
- Handles multi-unit lease amendments
- Enables unit-level lease analysis
```

### Tenant Relationships
```
dim_commcustomer → dim_fp_amendmentsunitspropertytenant
├── Join: tenant_hmy = tenant_hmy
├── Cardinality: One to Many (1:*)
├── Filter Direction: Single (customer → amendment)
├── Business Purpose: Tenant can have multiple amendments
└── Usage: Tenant lease history and rent roll

dim_commcustomer → fact_accountsreceivable
├── Join: tenant_id = tenant_id
├── Cardinality: One to Many (1:*)
├── Filter Direction: Single (customer → AR)
├── Business Purpose: Tenant AR and collection tracking
└── Usage: Cash flow and collection analysis
```

## Enhanced Analytics Relationships

### Industry Classification (Many-to-Many)
```
dim_fp_naics ↔ dim_fp_naicstotenantmap ↔ dim_commcustomer

Bridge Implementation:
dim_fp_naics → dim_fp_naicstotenantmap
├── Join: naics_code = naics_code
├── Cardinality: One to Many (1:*)
└── Purpose: Industry code can apply to multiple tenants

dim_commcustomer → dim_fp_naicstotenantmap
├── Join: tenant_hmy = tenant_hmy
├── Cardinality: One to Many (1:*)
└── Purpose: Tenant can have multiple industry classifications

Business Purpose:
- Industry diversification analysis
- Risk assessment by industry concentration
- Peer benchmarking and market analysis
```

### Termination Analysis
```
dim_fp_moveoutreasonreflist → dim_fp_terminationtomoveoutreas
├── Join: hmy = moveout_reason_hmy
├── Cardinality: One to Many (1:*)
├── Filter Direction: Single (reason → termination)
├── Business Purpose: Standardized termination reason tracking
├── Categories: Voluntary vs Involuntary terminations
└── Usage: Retention strategy development
```

### Market Rate Analysis
```
dim_property → fact_fp_fmvm_marketunitrates
├── Join: property_hmy = property_hmy
├── Cardinality: One to Many (1:*)
├── Filter Direction: Single (property → market rates)
├── Business Purpose: Property market rate benchmarking
└── Usage: Pricing optimization and gap analysis

dim_unit → fact_fp_fmvm_marketunitrates
├── Join: unit_hmy = unit_hmy
├── Cardinality: One to Many (1:*)
├── Filter Direction: Single (unit → market rates)
├── Business Purpose: Unit-level market rate data
└── Usage: Unit-specific pricing strategies
```

## Specialized Table Relationships

### Control Table Relationships
```
dim_lastclosedperiod (Single Row Global Filter)
├── No explicit relationships (used in measure logic)
├── Purpose: Global filter for financial reporting
├── Usage: Ensures all financial data filtered to closed periods
└── Implementation: Used in DAX measures, not as relationship

dim_propertyattributes → dim_property
├── Join: property id = property id
├── Cardinality: Many to One (*:1)
├── Filter Direction: Single (attributes → property)
├── Business Purpose: Flexible property metadata storage
└── Structure: Key-value pairs for extended attributes
```

### Acquisition and Investment Analysis
```
acq_costs_override → dim_property
├── Join: hmy_property = hmy_property
├── Cardinality: One to One (1:1)
├── Filter Direction: Single (costs → property)
├── Business Purpose: Property acquisition cost override data
└── Usage: Investment analysis and ROI calculations

dim_fp_buildingcustomdata → dim_property
├── Join: hmy_property = hmy_property
├── Cardinality: One to One (1:1)
├── Filter Direction: Single (building data → property)
├── Key Fields: status, acq_date, disposition_date, market
└── Critical for: Same-store analysis, portfolio tracking
```

## Relationship Validation

### Integrity Checks

#### Orphaned Records Detection
```sql
-- Check for orphaned financial records
SELECT 
    'fact_total' as table_name,
    COUNT(*) as total_records,
    COUNT(p.property id) as matched_records,
    COUNT(*) - COUNT(p.property id) as orphaned_records
FROM fact_total f
LEFT JOIN dim_property p ON f.property id = p.property id

-- Check amendment-charge relationship integrity
SELECT 
    'amendment_charges' as relationship,
    COUNT(DISTINCT a.amendment_hmy) as total_amendments,
    COUNT(DISTINCT c.amendment_hmy) as amendments_with_charges,
    COUNT(DISTINCT a.amendment_hmy) - COUNT(DISTINCT c.amendment_hmy) as amendments_without_charges
FROM dim_fp_amendmentsunitspropertytenant a
LEFT JOIN dim_fp_amendmentchargeschedule c ON a.amendment hmy = c.amendment hmy
```

#### Cardinality Validation
```sql
-- Check for unexpected many-to-many relationships
SELECT 
    property_id,
    COUNT(*) as property_count
FROM dim_property
GROUP BY property_id
HAVING COUNT(*) > 1

-- Validate unit-property relationship
SELECT 
    p.property_code,
    COUNT(u.unit_id) as unit_count,
    COUNT(DISTINCT u.unit_id) as distinct_units
FROM dim_property p
LEFT JOIN dim_unit u ON p.property_id = u.property_id
GROUP BY p.property_code
HAVING COUNT(u.unit_id) <> COUNT(DISTINCT u.unit_id)
```

## Performance Considerations

### Relationship Performance Impact

#### High-Performance Relationships
- **Single Direction**: Faster query execution
- **One-to-Many**: Optimal for Power BI engine
- **Explicit Cardinality**: Prevents engine guessing

#### Performance Optimization
```
Recommended:
✅ Single direction filtering (except calendar)
✅ Explicit cardinality settings
✅ Active relationships only
✅ Minimal bi-directional relationships

Avoid:
❌ Circular dependencies
❌ Excessive bi-directional relationships  
❌ Many-to-many without bridge tables
❌ Inactive relationships as workarounds
```

### Query Folding Impact
```sql
-- Relationships that support query folding
Property → Fact relationships: ✅ Excellent folding
Date → Fact relationships: ✅ Good folding with proper joins
Bridge table relationships: ⚠️ May break folding

-- Optimize for query folding
Use native database joins where possible
Minimize Power Query transformations
Keep relationships simple and direct
```

## Troubleshooting Guide

### Common Relationship Issues

#### Issue: Totals Don't Match
**Cause**: Many-to-many relationship not handled properly
**Solution**: Implement bridge table or adjust DAX measures

#### Issue: Circular Dependencies
**Cause**: Bi-directional relationships creating loops
**Solution**: Review filter directions, keep bi-directional for calendar only

#### Issue: Poor Performance
**Cause**: Complex relationship chains or incorrect cardinality
**Solution**: Simplify relationships, use summary tables

#### Issue: Missing Data in Visuals
**Cause**: Incorrect filter direction or inactive relationships
**Solution**: Check relationship direction and activation status

## Implementation Best Practices

### Step-by-Step Relationship Creation
1. **Start with Property Hub**: Create all property-related relationships first
2. **Add Date Relationships**: Configure bi-directional date relationships
3. **Financial Relationships**: Set up account and book relationships
4. **Amendment Chain**: Create amendment-related relationships
5. **Bridge Tables**: Implement many-to-many relationships last
6. **Validation**: Test all relationships with sample queries

### Relationship Testing Checklist
- [ ] All relationships have explicit cardinality
- [ ] Filter directions are correctly configured
- [ ] No circular dependencies exist
- [ ] Bridge tables handle many-to-many scenarios
- [ ] Orphaned records are minimized
- [ ] Query performance is acceptable

This relationship reference provides the foundation for building accurate and performant Power BI models. Refer to this document when creating or troubleshooting table relationships.