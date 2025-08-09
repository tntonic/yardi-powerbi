# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a Power BI analytics solution for commercial real estate data from Yardi systems. The repository contains comprehensive documentation for implementing a 32-table data model with 122 production-ready DAX measures, achieving 95-99% accuracy against native Yardi reports.

## Repository Structure

```
PBI v1.6/
├── PowerBI/                        # Main documentation directory
│   ├── Complete_DAX_Library_Production_Ready.dax  # All 122 DAX measures
│   ├── Complete_Data_Model_Guide.md               # 32-table architecture
│   ├── Quick_Start_Checklist.md                   # Implementation timeline
│   ├── Validation_and_Testing_Guide.md            # Testing procedures
│   └── [Multiple dashboard templates and guides]
├── Yardi Tables/                   # CSV data files for testing
│   ├── fact_*                      # Fact tables (transactions, totals, etc.)
│   └── dim_*                       # Dimension tables (properties, accounts, etc.)
└── README.md                       # Project overview
```

## Key Commands and Tasks

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

## High-Level Architecture

### Data Model Structure
- **32 optimized tables** following star schema principles
- **Hybrid approach**: Amendment-based detail layer + pre-aggregated summary tables
- **Key fact tables**: 
  - `fact_total` - Financial transactions (revenue, expenses, NOI)
  - `fact_occupancyrentarea` - Occupancy metrics by property/month
  - `dim_fp_amendmentsunitspropertytenant` - Lease amendments (critical for rent roll)
- **Critical relationships**: All single-direction except Calendar table (bi-directional)

### Amendment-Based Rent Roll Logic
The most critical innovation is the amendment-based approach for rent roll calculations:
- Uses `dim_fp_amendmentsunitspropertytenant` table
- Filters by **latest sequence** per property/tenant combination
- Includes **Activated + Superseded** statuses only
- Achieves **95-99% accuracy** vs native Yardi reports

### Financial Calculations
- **Traditional NOI**: Revenue (4xxxx accounts × -1) - Expenses (5xxxx accounts)
- **FPR Book NOI**: Uses book_id = 46 for enhanced property-level analysis
- **Note**: Revenue accounts in GL are stored as negative values

### Common Filter Patterns
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

## Top 20 Most-Used DAX Measures

1. `Total Revenue` - Revenue from 4xxxx accounts (multiply by -1)
2. `Operating Expenses` - Expenses from 5xxxx accounts
3. `NOI (Net Operating Income)` - Revenue minus operating expenses
4. `Physical Occupancy %` - Occupied area ÷ rentable area × 100
5. `Economic Occupancy %` - Actual rent ÷ potential rent × 100
6. `Current Monthly Rent` - Latest amendment-based monthly rent
7. `Current Rent Roll PSF` - Current monthly rent × 12 ÷ leased SF
8. `Current Leased SF` - Currently leased square footage from amendments
9. `WALT (Months)` - Weighted average lease term
10. `New Leases Count` - Count of new leases in period
11. `Renewals Count` - Count of lease renewals in period
12. `Terminations Count` - Count of lease terminations in period
13. `Net Leasing Activity SF` - (New + Renewals) - Terminations
14. `Retention Rate %` - Renewals ÷ (Renewals + Terminations) × 100
15. `FPR NOI` - Book 46 enhanced NOI calculation
16. `NOI Margin %` - NOI as percentage of revenue
17. `Vacancy Rate %` - (Rentable - Occupied) ÷ Rentable × 100
18. `Total Rentable Area` - Sum of rentable square footage
19. `Average Rent PSF` - Annual rent per square foot
20. `Portfolio Health Score` - Composite performance indicator (0-100)

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

## Critical Implementation Notes

1. **Amendment-based calculations** are essential for accuracy - always filter to latest sequence
2. **Revenue sign convention**: GL stores revenue as negative, multiply by -1 for reporting
3. **Status filtering**: Include both "Activated" AND "Superseded" for rent roll
4. **Relationship directions**: Keep single-direction except Calendar table
5. **Date conversions**: Excel serial dates need proper conversion in Power Query

## Validation Requirements

Before deployment, ensure:
- Rent roll accuracy: 95-99% vs Yardi native reports
- Leasing activity accuracy: 95-98% vs source systems
- Financial measures: 98%+ accuracy vs GL data
- Dashboard performance: <10 second load times
- All 122 DAX measures execute without errors