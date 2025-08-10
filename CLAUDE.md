# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a Power BI analytics solution for commercial real estate data from Yardi systems. The repository contains comprehensive documentation for implementing a 32-table data model with 122 production-ready DAX measures, achieving 95-99% accuracy against native Yardi reports.

**IMPORTANT**: This project is designed as a reference library for teams building Power BI dashboards with Claude.ai assistance. The clean, production-ready files are organized in the `Claude_AI_Reference` folder for easy upload to Claude.ai projects.

## Repository Structure

```
Yardi PowerBI/
├── Claude_AI_Reference/            # CLEAN REFERENCE FILES FOR CLAUDE.AI
│   ├── README.md                   # How to use with Claude.ai
│   ├── DAX_Measures/               # Production DAX measures
│   │   ├── Complete_DAX_Library_v4_Production.dax
│   │   ├── Top_20_Essential_Measures.dax
│   │   └── Validation_Measures.dax
│   ├── Documentation/              # Core guides (numbered for order)
│   │   ├── 01_Quick_Start_Guide.md
│   │   ├── 02_Data_Model_Guide.md
│   │   ├── 03_Data_Dictionary.md
│   │   ├── 04_Implementation_Guide.md
│   │   └── 05_Common_Issues_Solutions.md
│   ├── Dashboard_Templates/        # 4 dashboard specifications
│   ├── Reference_Guides/           # Business logic & mappings
│   └── Validation_Framework/       # Testing & accuracy guides
├── Development/                    # Development and testing tools
│   ├── Python_Scripts/            # Python validation scripts
│   ├── Test_Automation_Framework/ # Testing frameworks
│   └── Fund2_Validation_Results/  # Validation results and reports
├── Data/                          # Source data files
│   ├── Yardi_Tables/              # CSV exports from Yardi (32 tables)
│   └── Fund2_Filtered/            # Fund-specific filtered data
├── Documentation/                  # Extended documentation
│   ├── Core_Guides/               # Complete DAX libraries and guides
│   ├── Implementation/            # Implementation guides and fixes
│   └── Validation/                # Validation reports and test data
└── rent rolls/                    # Yardi rent roll exports for validation
```

## Key Commands and Tasks

### Python Validation Scripts
```bash
# Run complete rent roll workflow (filter → generate → validate)
cd Development/Python_Scripts
python run_complete_workflow.py

# Validate top 20 DAX measures accuracy
python top_20_measures_accuracy_test.py

# Validate amendment logic
python amendment_logic_validator.py

# Analyze orphaned records
python orphaned_records_analysis.py

# Validate DAX syntax
python dax_syntax_validator.py

# Generate rent roll for specific date
python generate_rent_roll_for_date.py --date "2025-06-30"

# Clean up data issues
python data_cleanup_execution.py
```

### Test Automation Framework
```bash
# Run complete test orchestration
cd Development/Test_Automation_Framework
python test_orchestrator.py --all

# Run specific test suites
python powerbi_validation_suite.py          # Data integrity validation
python accuracy_validation_enhanced.py      # Enhanced accuracy tests
python performance_test_suite.py           # Performance benchmarks
python data_quality_tests.py              # Data quality validation
python regression_testing_framework.py     # Regression testing
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

-- Validate charge schedule integration
SELECT COUNT(*) FROM dim_fp_amendmentchargeschedule
WHERE amendment_hmy NOT IN (
    SELECT hmy FROM dim_fp_amendmentsunitspropertytenant
)
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

## Key Production Files

### DAX Measures (Use v4 Production)
- **Primary**: `Documentation/Core_Guides/Complete_DAX_Library_v4_Performance_Optimized.dax`
- **Clean Reference**: `Claude_AI_Reference/DAX_Measures/Complete_DAX_Library_v4_Production.dax`
- **Top 20**: `Claude_AI_Reference/DAX_Measures/Top_20_Essential_Measures.dax`

### Critical Data Tables
- `dim_fp_amendmentsunitspropertytenant` - Core table for rent roll (must filter latest sequence)
- `dim_fp_amendmentchargeschedule` - Charge details linked to amendments
- `fact_total` - Financial transactions (revenue/expenses)
- `fact_occupancyrentarea` - Occupancy metrics by property/month

### Validation Workflows
```python
# Standard validation workflow for any DAX changes
# 1. Run syntax validation
python Development/Python_Scripts/dax_syntax_validator.py

# 2. Test amendment logic
python Development/Python_Scripts/amendment_logic_validator.py

# 3. Run accuracy tests
python Development/Python_Scripts/top_20_measures_accuracy_test.py

# 4. Full test orchestration
python Development/Test_Automation_Framework/test_orchestrator.py --all
```

## Working with Fund-Specific Data

When filtering for specific funds:
1. Use filtered data in `Data/Fund2_Filtered/` for Fund 2
2. Run `python Development/Python_Scripts/filter_fund2_data.py` to regenerate
3. Validate with `python Development/Fund2_Validation_Results/validate_fund2_accuracy.py`