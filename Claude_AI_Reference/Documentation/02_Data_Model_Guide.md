# Complete Data Model Guide

## ⚠️ Critical Update - Version 5.1 (2025-08-10)

### Required Table for Dynamic Date Handling
**IMPORTANT**: The `dim_lastclosedperiod` table is now required for all date references in DAX measures.

**Table Structure:**
```
dim_lastclosedperiod
├── last closed period: Date field containing Yardi's current closed period
├── Purpose: Replaces TODAY() for all date calculations
└── Update frequency: Refreshes with each data sync from Yardi
```

**Implementation Note:** All v5.1 DAX measures reference this table instead of using TODAY() to ensure alignment with Yardi financial periods.

## Overview

This guide provides comprehensive instructions for building the optimized 32-table Power BI data model for Yardi BI analytics. The model follows star schema principles with specialized structures for commercial real estate analytics.

## Data Model Architecture

### Design Principles

#### 1. Hybrid Approach
- **Detailed Layer**: Amendment-based structure for accuracy
- **Summary Layer**: Pre-aggregated tables for performance
- **Balance**: Precision where needed, speed for dashboards

#### 2. Star Schema Optimization
- **Fact Tables**: Contain measures and foreign keys
- **Dimension Tables**: Contain descriptive attributes
- **Bridge Tables**: Handle many-to-many relationships
- **Control Tables**: Manage business rules and filters

#### 3. Power BI Optimization
- **Bi-directional filtering**: Only for date dimension
- **Single direction**: All other relationships
- **Explicit cardinality**: Never rely on auto-detection
- **Active relationships**: All relationships should be active

## Core Table Structure

### Dimension Tables (22 tables)

#### Property & Unit Dimensions
```
dim_property (Central Hub)
├── Primary Key: property id
├── Business Key: property code  
├── Attributes: property name, address, market
└── Relationships: Referenced by most fact tables

dim_unit
├── Primary Key: unit id
├── Foreign Key: property id → dim_property
├── Attributes: unit name, unit type, floor
└── Cardinality: Many units to one property (1:M)

dim_commcustomer / dim_commlease (Tenant Data)
├── Primary Key: tenant id
├── Foreign Key: property id → dim_property
├── Attributes: tenant code, customer id, DBA_name
└── Business Purpose: Commercial tenant information

dim_commleasetype (Lease Type Classifications)
├── Primary Key: comm lease type id
├── Attributes: comm lease type code, comm lease type desc
├── Values: Office/Industrial/Retail (Gross/Net/Fixed), Ground, Storage, Parking
└── Business Purpose: Categorizes lease structure and property type
```

#### Financial Dimensions
```
dim_account (Chart of Accounts)
├── Primary Key: account id
├── Self-Reference: parent account id → account id
├── Attributes: account code, description, report type
└── Business Logic: 4xxxx = Revenue, 5xxxx = Expenses

dim_accounttree (Account Hierarchy)
├── Primary Key: account_tree_detail_id
├── Attributes: node_description, tree_codes
└── Purpose: Financial reporting tree structure

dim_accounttreeaccountmapping (Bridge Table)
├── Composite Key: account tree detail id + account id
├── Purpose: Many-to-many account to tree mapping
└── Enables: Flexible financial reporting hierarchies

dim_book (Financial Books)
├── Primary Key: book id
├── Key Books: 46 = FPR book for NOI calculations
└── Purpose: Multiple accounting views of same data
```

#### Amendment & Lease Dimensions
```
dim_fp_amendmentsunitspropertytenant (Core Amendment Data)
├── Primary Key: amendment hmy
├── Foreign Keys: property hmy, tenant hmy
├── Key Fields: sequence, status, type, dates, square_footage
├── Business Logic: Latest sequence per property/tenant
└── Critical for: Rent roll and leasing activity calculations

dim_fp_amendmentchargeschedule (Charge Details)
├── Primary Key: record hmy
├── Foreign Key: amendment hmy → dim_fp_amendmentsunitspropertytenant
├── Attributes: charge codes, monthly amounts, effective dates
└── Cardinality: Many charge schedules to one amendment

dim_fp_chargecodetypeandgl (Charge Code Mapping)
├── Primary Key: hmy_charge_code
├── Foreign Key: hmy charged gl → dim_account
└── Purpose: Links operational charges to GL accounts
```

#### Enhanced Analytics Dimensions
```
dim_fp_naics (Industry Classification)
├── Primary Key: naics code
├── Attributes: naics_description, naics_level
└── Purpose: Industry diversification analysis

dim_fp_naicstotenantmap (Industry Bridge)
├── Composite Key: naics code + tenant hmy
├── Purpose: Maps tenants to industry classifications
└── Enables: Industry concentration and risk analysis

dim_fp_moveoutreasonreflist (Termination Reasons)
├── Primary Key: hmy
├── Attributes: move_out_reason, reason_category
└── Categories: Voluntary/Involuntary termination tracking

dim_fp_terminationtomoveoutreas (Termination Bridge)
├── Composite Key: amendment hmy + moveout reason hmy
├── Purpose: Links terminations to specific reasons
└── Enables: Retention analysis and churn prevention
```

#### Customer Identity and Credit Risk Data Model
```
dim_fp_customercreditscorecustomdata (Credit & Company Data)
├── Primary Key: hmy_creditscore
├── Join Key: hmyperson_customer → dim_commcustomer.customer_id
├── Business Key: customer code (c0000xxx format)
├── Attributes: customer name, credit score (0-10), company info
├── Purpose: Credit risk assessment and company intelligence
└── Coverage: Subset of customers with credit assessments

dim_fp_customertoparentmap (Corporate Structure)
├── Primary Key: Composite (customer hmy + parent customer hmy)
├── Join Key: customer hmy → dim_commcustomer.customer_id
├── Business Key: customer code (c0000xxx format)
├── Attributes: customer name, parent relationships
├── Purpose: Corporate hierarchy and parent company mapping
└── Usage: Aggregate risk at parent company level

Customer Data Flow:
dim_commcustomer (tenant_id, customer_id, tenant_code, lessee_name)
    ├──→ dim_fp_customercreditscorecustomdata (via customer_id = hmyperson_customer)
    │    └── Returns: customer code, customer name, credit score
    └──→ dim_fp_customertoparentmap (via customer_id = customer hmy)
         └── Returns: customer code, customer name, parent company

Lookup Priority Logic:
1. Check dim_fp_customercreditscorecustomdata first (primary source)
2. If not found, check dim_fp_customertoparentmap (secondary source)
3. If neither, use dim_commcustomer.lessee_name (fallback)
4. Customer codes are consistent when present in both tables
```

### Fact Tables (7 tables)

#### Core Financial Facts
```
fact_total (Primary Financial Data)
├── Composite Key: property id + book id + account id + month
├── Measures: amount (by amount type: Actual, Budget, Cumulative)
├── Grain: Monthly transactions by property, book, and account
├── Volume: Highest transaction volume table
└── Note: Filter by book_id = 46 for FPR NOI calculations
```

#### Operational Facts
```
fact_occupancyrentarea (Occupancy Metrics)
├── Composite Key: property id + lease type id + first day of month
├── Measures: unit_count, occupied area, rentable area, total rent
├── Grain: Monthly occupancy snapshots by property and lease type
└── Critical for: Physical/Economic occupancy calculations

fact_accountsreceivable (AR Tracking)
├── Composite Key: property id + tenant id + invoice date + amount
├── Measures: amount, aging_days
├── Purpose: Cash flow forecasting and collection analysis
└── Enables: AR aging and collection efficiency metrics

fact_expiringleaseunitarea (Lease Expirations)
├── Composite Key: property id + unit id + tenant id + lease from date
├── Measures: property_area, expiring_area
├── Purpose: Lease expiration planning and renewal forecasting
└── Supports: WALT calculations and expiration waterfalls
```

#### Market & Analysis Facts
```
fact_fp_fmvm_marketunitrates (Market Rates)
├── Primary Key: Combination of property, unit, and profile identifiers
├── Measures: unitmlarentnew, profilemlarentfinal, unitarea
├── Purpose: Market vs actual rent gap analysis
└── Enables: Pricing optimization and benchmarking
```

### Specialized Tables (5 tables)

#### Control & Override Tables
```
dim_lastclosedperiod (Control Table)
├── Single Row Table: Contains last closed accounting period
├── Purpose: Global filter for financial reporting
└── Usage: Filter all financial data to closed periods only

acq_costs_override (Acquisition Data)
├── Primary Key: hmy_property
├── Attributes: purchase_price, total_acq_cost, closing_costs
├── Purpose: Property acquisition cost analysis
└── Supplements: Building custom data for investment analysis

dim_propertyattributes (Flexible Metadata)
├── Composite Key: property id + attribute name
├── Structure: Key-value pairs for property characteristics
├── Purpose: Extended property metadata without schema changes
└── Flexibility: Add new property attributes without model changes
```

#### Extended Property Data
```
dim_fp_buildingcustomdata (Extended Property Info)
├── Primary Key: hmy_property
├── Key Fields: market, status, acq date, disposition date
├── Property Status: "Acquired" = owned, "Sold" = disposed
└── Critical for: Same-store analysis and portfolio tracking

dim_fp_unitscustomdata (Unit Technical Data)
├── Primary Key: hmy_unit
├── Attributes: office percentage, lighting type, electrical capacity
└── Purpose: Unit-level technical specifications
```

## Relationship Configuration

### Power BI Relationship Setup

#### Calendar Relationships (Bi-directional)
```
dim_date ↔ fact_total (month)
dim_date ↔ fact_occupancyrentarea (first day of month)
dim_date ↔ fact_accountsreceivable (invoice date)
dim_date ↔ fact_expiringleaseunitarea (lease from date)

Configuration:
- Cross Filter Direction: Both
- Cardinality: One to Many (1:*)
- Make Relationship Active: Yes
```

#### Core Dimension Relationships (Single Direction)
```
dim_property → fact_total (property_id)
dim_property → fact_occupancyrentarea (property_id)
dim_property → fact_accountsreceivable (property_id)
dim_property → dim_unit (property_id)
dim_property → dim_commcustomer (property_id)

Configuration:
- Cross Filter Direction: Single (dimension → fact)
- Cardinality: One to Many (1:*)
- Make Relationship Active: Yes
```

#### Financial Relationships
```
dim_account → fact_total (account_id)
dim_book → fact_total (book_id)

Account Tree Relationships:
dim_account ↔ dim_accounttreeaccountmapping (account_id)
dim_accounttree ↔ dim_accounttreeaccountmapping (account_tree_detail_id)

Configuration:
- Bridge table handles many-to-many relationships
- All relationships remain active
```

#### Amendment Relationships Chain
```
dim_fp_amendmentsunitspropertytenant → dim_fp_amendmentchargeschedule (amendment hmy)
dim_fp_amendmentsunitspropertytenant → dim_fp_terminationtomoveoutreas (amendment hmy)
dim_fp_amendmentsunitspropertytenant ↔ dim_fp_unitto_amendmentmapping (amendment hmy)

Property Chain:
dim_property → dim_fp_amendmentsunitspropertytenant (property hmy)
dim_commcustomer → dim_fp_amendmentsunitspropertytenant (tenant hmy)
```

#### Customer Identity Relationships
```
dim_commcustomer → dim_fp_customercreditscorecustomdata (customer_id = hmyperson_customer)
dim_commcustomer → dim_fp_customertoparentmap (customer_id = customer hmy)
dim_fp_customertoparentmap → dim_fp_customercreditscorecustomdata (parent customer hmy = hmyperson_customer)

Configuration:
- Cross Filter Direction: Single (dim_commcustomer → credit/parent tables)
- Cardinality: One to Zero-or-One (1:0..1)
- Make Relationship Active: Yes
- Note: Not all customers have credit scores or parent mappings
```

### Relationship Validation

#### Critical Relationship Tests
```sql
-- Test property relationships
SELECT 
    COUNT(*) as total_facts,
    COUNT(p.property_id) as matched_properties,
    COUNT(*) - COUNT(p.property_id) as orphaned_records
FROM fact_total f
LEFT JOIN dim_property p ON f.property_id = p.property_id

-- Test amendment relationships
SELECT 
    COUNT(*) as total_amendments,
    COUNT(c.amendment hmy) as amendments_with_charges
FROM dim_fp_amendmentsunitspropertytenant a
LEFT JOIN dim_fp_amendmentchargeschedule c ON a.amendment hmy = c.amendment hmy

-- Test date relationships
SELECT 
    MIN(month) as earliest_date,
    MAX(month) as latest_date,
    COUNT(DISTINCT month) as unique_dates
FROM fact_total
```

## Performance Optimization

### Data Model Optimizations

#### Column Store Optimization
```dax
// Remove unnecessary columns
// Keep only required columns in each table
// Use calculated columns sparingly

// Optimize data types
Amendment Sequence = INT(dim_fp_amendmentsunitspropertytenant[amendment sequence])
Monthly Amount = CURRENCY(dim_fp_amendmentchargeschedule[monthly amount])
```

#### Relationship Optimization
```
Single Direction Filtering:
- Reduces model complexity
- Improves query performance
- Prevents circular dependencies

Bi-directional Only for Calendar:
- Enables time intelligence functions
- Required for period-over-period calculations
- Should not be used elsewhere
```

### Summary Table Strategy

#### Monthly Occupancy Summary
```sql
-- Create in Power Query or SQL
SELECT 
    EOMONTH(first day of month) as period date,
    property_id,
    SUM(occupied area) as occupied sf,
    SUM(rentable area) as rentable sf,
    SUM(total rent) as total rent
FROM fact_occupancyrentarea
GROUP BY EOMONTH(first day of month), property_id
```

#### Current Rent Roll Snapshot
```sql
-- Pre-calculated current rent roll
WITH LatestAmendments AS (
    SELECT 
        property hmy,
        tenant hmy,
        MAX(amendment sequence) as latest sequence
    FROM dim_fp_amendmentsunitspropertytenant
    WHERE amendment status IN ('Activated', 'Superseded')
    AND amendment type <> 'Termination'
    GROUP BY property hmy, tenant hmy
)
SELECT 
    a.*,
    c.monthly_amount,
    c.charge_code
FROM dim_fp_amendmentsunitspropertytenant a
INNER JOIN LatestAmendments l ON 
    a.property hmy = l.property hmy AND
    a.tenant hmy = l.tenant hmy AND
    a.amendment sequence = l.latest sequence
INNER JOIN dim_fp_amendmentchargeschedule c ON a.amendment hmy = c.amendment hmy
WHERE GETDATE() BETWEEN a.amendment_start_date AND ISNULL(a.amendment_end_date, '2099-12-31')
```

### Incremental Refresh Configuration

#### Setup Parameters
```powerquery
// Add these parameters in Power Query
RangeStart = #datetime(2020, 1, 1, 0, 0, 0) meta [IsParameterQuery=true, Type="DateTime"]
RangeEnd = #datetime(2025, 12, 31, 23, 59, 59) meta [IsParameterQuery=true, Type="DateTime"]

// Apply to fact tables
= Table.SelectRows(fact_total, each [month] >= RangeStart and [month] < RangeEnd)
```

#### Refresh Policy
```
Historical Data: Keep 3 years, don't refresh
Recent Data: Refresh last 3 months daily
Archive Data: Annual snapshots for historical reporting
```

## Data Quality Framework

### Validation Measures

#### Data Completeness Checks
```dax
// Property Data Completeness
Property Data Completeness = 
VAR TotalProperties = COUNTROWS(dim_property)
VAR CompleteProperties = 
    CALCULATE(
        COUNTROWS(dim_property),
        NOT(ISBLANK(dim_property[property name])),
        NOT(ISBLANK(dim_property[property code])),
        dim_property[is active] = TRUE
    )
RETURN DIVIDE(CompleteProperties, TotalProperties, 0)

// Amendment Data Quality
Amendment Data Quality = 
VAR TotalAmendments = COUNTROWS(dim_fp_amendmentsunitspropertytenant)
VAR QualityAmendments = 
    CALCULATE(
        COUNTROWS(dim_fp_amendmentsunitspropertytenant),
        NOT(ISBLANK(dim_fp_amendmentsunitspropertytenant[amendment start date])),
        dim_fp_amendmentsunitspropertytenant[amendment sf] > 0,
        dim_fp_amendmentsunitspropertytenant[amendment sequence] >= 0
    )
RETURN DIVIDE(QualityAmendments, TotalAmendments, 0)
```

#### Relationship Integrity
```dax
// Orphaned Records Check
Orphaned Financial Records = 
VAR TotalRecords = COUNTROWS(fact_total)
VAR MatchedRecords = 
    CALCULATE(
        COUNTROWS(fact_total),
        NOT(ISBLANK(RELATED(dim_property[property id]))),
        NOT(ISBLANK(RELATED(dim_account[account id])))
    )
RETURN TotalRecords - MatchedRecords
```

### Data Model Health Monitoring

#### Key Health Metrics
```dax
// Model Size Monitor
Model Size GB = 
VAR ModelSize = INFO.MEMORYBYTES()
RETURN DIVIDE(ModelSize, 1024*1024*1024, 0)

// Relationship Health
Active Relationships = 
COUNTROWS(
    FILTER(
        INFO.RELATIONSHIPS(),
        [IsActive] = TRUE
    )
)

// Query Performance Monitor  
Average Query Time = 
// Implement through usage metrics API
// Monitor dashboard load times
// Track slow-performing measures
```

## Implementation Steps

### Step 1: Table Import and Preparation
1. Import all 32 required tables using bulk selection
2. Apply data type transformations in Power Query
3. Clean and standardize text fields
4. Configure date field conversions
5. Apply data quality filters

### Step 2: Relationship Creation
1. Start with dim_property as central hub
2. Create all property-related relationships first
3. Add financial dimension relationships
4. Configure amendment relationship chain
5. Set up bridge table relationships last

### Step 3: Cardinality and Direction Configuration
1. Set all relationships to explicit cardinality
2. Configure single direction for all except calendar
3. Enable bi-directional filtering for date relationships only
4. Verify no circular dependencies exist
5. Test relationship functionality

### Step 4: Performance Testing
1. Load sample data and test query performance
2. Monitor memory usage during refresh
3. Test dashboard responsiveness
4. Validate relationship query folding
5. Optimize slow-performing elements

### Step 5: Data Validation
1. Run relationship integrity checks
2. Validate data completeness scores
3. Test business logic with known results
4. Compare key metrics with source systems
5. Document any data quality issues

## Troubleshooting Guide

### Common Model Issues

#### Issue: Circular Dependencies
**Cause**: Bi-directional relationships creating loops
**Solution**: 
- Review all bi-directional relationships
- Keep bi-directional only for calendar table
- Use calculated columns or measures instead

#### Issue: Poor Query Performance
**Cause**: Complex relationships or large cardinality
**Solution**:
- Implement summary tables for common queries
- Use single direction filtering
- Consider composite models for very large datasets

#### Issue: Incorrect Totals
**Cause**: Many-to-many relationships not handled properly
**Solution**:
- Use bridge tables for many-to-many scenarios
- Implement proper DAX measure logic
- Validate relationship cardinality settings

#### Issue: Memory Errors
**Cause**: Data model too large for available memory
**Solution**:
- Implement incremental refresh
- Create summary tables for historical data
- Remove unnecessary columns and tables

## YAML to PowerBI Table Mappings

The data model is based on the Yardi semantic data model defined in `Yardi Data Model_MT.lsdl.yaml`. This section provides the mapping between YAML entity names and PowerBI table names.

### Naming Convention Rules

1. **Underscore Removal**: YAML uses underscores, PowerBI typically removes them
   - Example: `fact_occupancy_rent_area` → `fact_occupancyrentarea`

2. **Case Preservation**: Both systems maintain the same case pattern
   - Fact tables: lowercase (e.g., `fact_total`)
   - Dimension tables: lowercase with dim prefix (e.g., `dim_property`)

### Core Table Mappings

#### Fact Tables
| YAML Entity Name | PowerBI Table Name | Description |
|------------------|-------------------|-------------|
| `fact_total` | `fact_total` | Financial transactions and GL data |
| `fact_occupancy_rent_area` | `fact_occupancyrentarea` | Monthly occupancy snapshots |
| `fact_accounts_receivable` | `fact_accountsreceivable` | AR aging and collections |
| `fact_expiring_lease_unit_area` | `fact_expiringleaseunitarea` | Lease expiration tracking |

#### Core Dimension Tables
| YAML Entity Name | PowerBI Table Name | Description |
|------------------|-------------------|-------------|
| `dim_property` | `dim_property` | Property master data |
| `dim_account` | `dim_account` | Chart of accounts |
| `dim_date` | `dim_date` | Date dimension |
| `dim_book` | `dim_book` | Accounting books |
| `dim_unit` | `dim_unit` | Unit/space information |
| `dim_comm_customer` | `dim_commcustomer` | Customer/tenant data |
| `dim_comm_lease` | `dim_commlease` | Lease header information |
| `dim_comm_lease_type` | `dim_commleasetype` | Lease type classifications |

#### Account Hierarchy Tables
| YAML Entity Name | PowerBI Table Name | Description |
|------------------|-------------------|-------------|
| `dim_account_tree` | `dim_accounttree` | Account hierarchy structure |
| `dim_account_tree_account_mapping` | `dim_accounttreeaccountmapping` | Account to tree mapping |

### PowerBI-Specific Tables (Not in YAML)

These critical tables exist in the PowerBI implementation but are not defined in the base YAML schema:

#### Amendment Tables (Critical for Rent Roll)
- `dim_fp_amendmentsunitspropertytenant` - Core amendment/lease data
- `dim_fp_amendmentchargeschedule` - Charge schedules
- `dim_fp_terminationtomoveoutreas` - Termination reasons
- `dim_fp_unitto_amendmentmapping` - Unit to amendment mapping

#### Summary Tables
- `acq_costs_override` - Acquisition cost overrides

### Using the Mapping

#### For Data Model Implementation
```sql
-- YAML entity name
SELECT * FROM fact_occupancy_rent_area

-- Translates to PowerBI table
SELECT * FROM fact_occupancyrentarea
```

#### For Semantic Search
When searching for tables in the YAML file, use the entity terms and synonyms:
```bash
# Find occupancy-related entities
grep -i "occupancy" "Yardi Data Model_MT.lsdl.yaml"

# Extract semantic terms for an entity
grep -A15 "fact_occupancy_rent_area:" "Yardi Data Model_MT.lsdl.yaml" | grep "Terms:" -A10
```

### Important Notes

1. **Amendment Tables**: The most critical tables for rent roll accuracy (`dim_fp_amendmentsunitspropertytenant` and related) are PowerBI-specific enhancements not in the YAML.

2. **Book-Specific Filtering**: For book-specific analysis (e.g., FPR book 46), filter the fact_total table by book_id rather than creating separate tables.

3. **Summary Tables**: Pre-aggregated tables are performance optimizations added in PowerBI.

4. **Semantic Terms**: The YAML file includes business synonyms and terms for each entity that can help with data discovery and understanding.

## Next Steps

After completing the data model setup:

1. **Validate Relationships**: Test all table joins work correctly
2. **Import DAX Measures**: Begin implementing the 115 production measures
3. **Performance Tuning**: Optimize for your specific data volumes
4. **Create Dashboards**: Start building dashboard templates
5. **User Testing**: Validate model with business users

The data model provides the foundation for all analytics and reporting. Ensure it's solid before proceeding to measure implementation.