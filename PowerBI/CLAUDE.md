# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a Power BI analytics solution for commercial real estate data from Yardi systems. The repository contains comprehensive documentation for implementing a 32-table data model with 122 production-ready DAX measures, achieving 95-99% accuracy against native Yardi reports.

## Yardi Data Model YAML Integration

The solution is based on the Yardi semantic data model defined in `Yardi Data Model_MT.lsdl.yaml`. This YAML file contains:
- **50+ entity definitions** with semantic terms and synonyms
- **Column-level bindings** mapping logical names to physical table/column names
- **Business terminology** for improved data discovery

### Key YAML to PowerBI Table Mappings
- YAML: `fact_occupancy_rent_area` → PowerBI: `fact_occupancyrentarea`
- YAML: `fact_total` → PowerBI: `fact_total`
- YAML: `dim_property` → PowerBI: `dim_property`
- YAML: `dim_comm_customer` → PowerBI: `dim_commcustomer`

**Note**: Critical amendment tables (e.g., `dim_fp_amendmentsunitspropertytenant`) are PowerBI-specific enhancements not present in the base YAML schema.

## How to Use This Project with Claude

### Initial Setup Questions to Ask Claude:

```
"Review the Complete_Data_Model_Guide.md and explain the core table relationships for the rent roll calculation"

"Show me the top 20 DAX measures from Complete_DAX_Library_Production_Ready.dax that I should implement first"

"Based on the Quick_Start_Checklist.md, what are the critical validation steps for Phase 1?"
```

### Building the Data Model:

```
"Using the Table_Relationships_Reference.md, create a script to validate all table relationships in Power BI"

"Generate Power Query M code to clean and transform the dim_property table based on the data model requirements"

"What are the specific cardinality settings needed for the amendment tables according to the data model guide?"
```

### Implementing DAX Measures:

```
"Extract all occupancy-related measures from Complete_DAX_Library_Production_Ready.dax and explain their calculation logic"

"Create a custom DAX measure for [specific requirement] that follows the patterns in the DAX library"

"Validate my rent roll calculation against the business logic in Rent_Roll_Implementation.md"
```

### Working with the Yardi Data Model YAML:

```
"Show me the YAML entity definition for fact_occupancy_rent_area and explain how it maps to PowerBI"

"What semantic terms are available for the dim_property entity in the YAML file?"

"Compare the YAML table bindings with the PowerBI data model and identify any gaps"

"Generate a mapping between YAML entity names and PowerBI table names for all fact tables"
```

## Top 20 Most-Used DAX Measures

### Core Financial Measures
1. `Total Revenue` - Revenue from 4xxxx accounts (multiply by -1)
2. `Operating Expenses` - Expenses from 5xxxx accounts
3. `NOI (Net Operating Income)` - Revenue minus operating expenses
4. `FPR NOI` - Book 46 enhanced NOI calculation
5. `NOI Margin %` - NOI as percentage of revenue

### Occupancy Measures  
6. `Physical Occupancy %` - Occupied area ÷ rentable area × 100
7. `Economic Occupancy %` - Actual rent ÷ potential rent × 100
8. `Vacancy Rate %` - (Rentable - Occupied) ÷ Rentable × 100
9. `Total Rentable Area` - Sum of rentable square footage
10. `Average Rent PSF` - Annual rent per square foot

### Rent Roll Measures
11. `Current Monthly Rent` - Latest amendment-based monthly rent
12. `Current Rent Roll PSF` - Current monthly rent × 12 ÷ leased SF
13. `Current Leased SF` - Currently leased square footage from amendments
14. `WALT (Months)` - Weighted average lease term

### Leasing Activity Measures
15. `New Leases Count` - Count of new leases in period
16. `Renewals Count` - Count of lease renewals in period  
17. `Terminations Count` - Count of lease terminations in period
18. `Net Leasing Activity SF` - (New + Renewals) - Terminations
19. `Retention Rate %` - Renewals ÷ (Renewals + Terminations) × 100

### Performance Measures
20. `Portfolio Health Score` - Composite performance indicator (0-100)

## Common Filter Patterns

### Date Filtering
```dax
// Current month filter
dim_date[date] = EOMONTH(TODAY(), 0)

// Year-to-date filter  
DATESYTD(dim_date[date])

// Last 12 months filter
DATESINPERIOD(dim_date[date], MAX(dim_date[date]), -12, MONTH)
```

### Amendment Filtering (Critical for Rent Roll)
```dax
// Latest amendments only
FILTER(
    ALL(dim_fp_amendmentsunitspropertytenant),
    dim_fp_amendmentsunitspropertytenant[amendment sequence] = 
    CALCULATE(
        MAX(dim_fp_amendmentsunitspropertytenant[amendment sequence]),
        ALLEXCEPT(
            dim_fp_amendmentsunitspropertytenant,
            dim_fp_amendmentsunitspropertytenant[property hmy],
            dim_fp_amendmentsunitspropertytenant[tenant hmy]
        )
    )
)

// Active amendments only
dim_fp_amendmentsunitspropertytenant[amendment status] IN {"Activated", "Superseded"}
```

### Book Filtering
```dax
// Accrual book (standard accounting)
fact_total[book_id] = 1 OR dim_book[book] = "Accrual"

// FPR book (enhanced NOI)
fact_total[book_id] = 46

// Budget vs Actual
fact_total[amount_type] = "Actual"  // For actuals
dim_book[book] CONTAINS "Budget"     // For budget data
```

## Key Architecture

### Data Model Structure
- **32 optimized tables** following star schema principles
- **Hybrid approach**: Amendment-based detail layer + pre-aggregated summary tables
- **Key fact tables**: `fact_total` (financials), `fact_occupancyrentarea` (occupancy), `dim_fp_amendmentsunitspropertytenant` (amendments/leases)
- **Critical relationships**: All single-direction except Calendar table (bi-directional)

### Core Components
- **Data Model**: `Complete_Data_Model_Guide.md` - Complete 32-table architecture documentation
- **DAX Measures**: `Complete_DAX_Library_Production_Ready.dax` - All 122 production-ready measures
- **Dashboard Templates**: 8 production-ready dashboard designs (Executive Summary, Financial Performance, etc.)
- **Implementation Guides**: Step-by-step deployment instructions
- **Reference Guides**: Account mapping, calculation patterns, granularity best practices, book strategy

## Development Commands

### Power BI Development
```bash
# No traditional build/test commands - this is a Power BI solution
# Key development activities:

# 1. Import data model using Power Query
# 2. Apply DAX measures from Complete_DAX_Library_Production_Ready.dax
# 3. Validate accuracy against Yardi reports (95%+ target)
# 4. Test dashboard performance (<10 second load time)
```

### Data Validation SQL
```sql
-- Validate amendment-based rent roll accuracy
SELECT COUNT(*) FROM dim_fp_amendmentsunitspropertytenant 
WHERE status IN ('Activated', 'Superseded')

-- Check for orphaned records
SELECT COUNT(*) FROM fact_total f
LEFT JOIN dim_property p ON f.property_id = p.property_id
WHERE p.property_id IS NULL
```

### YAML-Based Model Validation
```bash
# Extract entity names from YAML for validation
grep -E "^  \w+:" "Yardi Data Model_MT.lsdl.yaml" | cut -d: -f1 | tr -d ' '

# Verify table bindings match PowerBI implementation
grep -A2 "Binding:" "Yardi Data Model_MT.lsdl.yaml" | grep "Table:"

# Check semantic terms for a specific entity
grep -A20 "fact_occupancy_rent_area:" "Yardi Data Model_MT.lsdl.yaml"
```

## Critical Business Logic

### Rent Roll Calculation
- Uses **amendment-based approach** from `dim_fp_amendmentsunitspropertytenant`
- Filters by **latest sequence** per property/tenant combination
- Includes **Activated + Superseded** statuses only
- Achieves **95-99% accuracy** vs native Yardi reports

### Leasing Activity Tracking
- **New Leases**: Type = 'New Lease', moveout_date IS NULL
- **Renewals**: Type = 'Renewal', within date period
- **Terminations**: moveout_date within period, mapped to move-out reasons
- Enhanced with **velocity metrics** and **retention analysis**

### Financial Calculations
- **Traditional NOI**: Revenue (4xxxx accounts) - Expenses (5xxxx accounts)
- **FPR Book NOI**: Uses book_id = 46 for enhanced property-level analysis
- **Occupancy**: Physical (leased SF / total SF) and Economic (actual rent / potential rent)

## Key Files to Review

### Core Implementation Files
1. **Data Model**: `Complete_Data_Model_Guide.md` - Complete table structure and relationships
2. **DAX Library**: `Complete_DAX_Library_Production_Ready.dax` - All 122 measures with comments
3. **Implementation**: `Quick_Start_Checklist.md` - Step-by-step deployment checklist
4. **Validation**: `Validation_and_Testing_Guide.md` - Accuracy testing procedures

### Essential Reference Guides  
5. **Account Mapping**: `Account_Mapping_Reference.md` - Complete GL account structure and usage
6. **Calculation Patterns**: `Calculation_Patterns_Reference.md` - DAX patterns converted from Tableau
7. **Data Granularity**: `Granularity_Best_Practices.md` - Table grain specifications and aggregation rules
8. **Book Strategy**: `Book_Strategy_Guide.md` - Understanding Yardi accounting books (Accrual, FPR, Budget)
9. **Business Logic**: `Business_Logic_Reference.md` - Detailed calculation explanations

## Performance Standards

- **Dashboard Load**: < 10 seconds
- **Data Refresh**: < 30 minutes for full model
- **Query Response**: < 5 seconds for interactions
- **Accuracy Targets**: 95-99% for rent roll, 95-98% for leasing activity

## Common Troubleshooting

### Rent Roll Issues
- **Problem**: Rent roll totals don't match Yardi
- **Check**: Are you including both "Activated" AND "Superseded" status?
- **Fix**: Use `IN {"Activated", "Superseded"}` not just `= "Activated"`

### Revenue Sign Issues  
- **Problem**: Revenue shows as negative
- **Check**: Revenue accounts (4xxxx) are stored as negative in GL
- **Fix**: Multiply by -1: `SUM(fact_total[amount]) * -1`

### Amendment Duplicates
- **Problem**: Duplicate tenants in rent roll
- **Check**: Are you filtering to latest amendment sequence?
- **Fix**: Use MAX(sequence) filter per property/tenant combination

### Performance Issues
- **Problem**: Dashboard loads >10 seconds
- **Check**: Are you using proper relationship directions?
- **Fix**: Ensure single-direction relationships except for Calendar table

## Important Notes

- This is a **documentation-only repository** - no executable code
- All DAX measures are **production-tested** with real Yardi data
- Focus on **amendment-based calculations** for maximum accuracy
- Follow **star schema principles** when extending the model
- Maintain **single-direction relationships** except for Calendar table