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
│   ├── DAX_Measures/               # Production DAX measures (v5.1)
│   │   ├── 01_Core_Financial_Rent_Roll_Measures_v5.0.dax
│   │   ├── 02_Leasing_Activity_Pipeline_Measures_v5.0.dax
│   │   ├── 03_Credit_Risk_Tenant_Analysis_Measures_v5.0.dax
│   │   ├── 04_Net_Absorption_Fund_Analysis_Measures_v5.0.dax
│   │   ├── 05_Performance_Validation_Measures_v5.0.dax
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

// Current date from Yardi closed period (v5.1+ pattern)
VAR CurrentDate = CALCULATE(
    MAX(dim_lastclosedperiod[last closed period]),
    ALL(dim_lastclosedperiod)
)
```

### Date Handling Pattern (v5.1+)
**IMPORTANT**: As of v5.1, all DAX measures use the Yardi closed period date instead of TODAY():
- **Pattern**: Reference `dim_lastclosedperiod[last closed period]` for the current date
- **Benefits**: Ensures consistency with Yardi financial reporting periods
- **Updates**: Automatically when data is refreshed from Yardi
- **Current Value**: Dynamically reads from the table (e.g., "2025-07-01")

```dax
// OLD PATTERN (v5.0 and earlier)
VAR CurrentDate = TODAY()

// NEW PATTERN (v5.1+)
VAR CurrentDate = CALCULATE(
    MAX(dim_lastclosedperiod[last closed period]),
    ALL(dim_lastclosedperiod)
)
```

## Top 25 Most-Used DAX Measures

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
21. `Average Tenant Credit Score` - Average credit score across tenants
22. `Revenue at Risk %` - Percentage of revenue from at-risk tenants
23. `Enhanced Tenant Risk Flag` - Combined Yardi + credit score risk assessment
24. `Credit Score Coverage %` - Percentage of tenants with credit scores
25. `Portfolio Credit Risk Score` - Credit risk on 0-100 scale

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
- Net absorption accuracy: 95-99% vs FPR benchmarks (Fund 2 target: -167,821 SF)
- Credit risk coverage: 70%+ tenants with credit scores
- Dashboard performance: <10 second load times
- All 217+ DAX measures execute without errors

## Key Production Files

### DAX Measures (v5.1 - Dynamic Date Handling)
- **Core Financial**: `Claude_AI_Reference/DAX_Measures/01_Core_Financial_Rent_Roll_Measures_v5.0.dax` (42 measures)
- **Leasing Activity**: `Claude_AI_Reference/DAX_Measures/02_Leasing_Activity_Pipeline_Measures_v5.0.dax` (85 measures)
- **Credit Risk**: `Claude_AI_Reference/DAX_Measures/03_Credit_Risk_Tenant_Analysis_Measures_v5.0.dax` (30 measures)  
- **Net Absorption**: `Claude_AI_Reference/DAX_Measures/04_Net_Absorption_Fund_Analysis_Measures_v5.0.dax` (35 measures)
- **Performance**: `Claude_AI_Reference/DAX_Measures/05_Performance_Validation_Measures_v5.0.dax` (25 measures)
- **Quick Reference**: `Claude_AI_Reference/DAX_Measures/Top_20_Essential_Measures.dax`
- **Historical (Archived)**: `Archive/DAX_Versions_Historical/` (v4.1 and earlier)

### Critical Data Tables
- `dim_lastclosedperiod` - **v5.1**: Yardi closed period date for all date references (replaces TODAY())
- `dim_fp_amendmentsunitspropertytenant` - Core table for rent roll (must filter latest sequence)
- `dim_fp_amendmentchargeschedule` - Charge details linked to amendments  
- `dim_fp_terminationtomoveoutreas` - Termination details for net absorption analysis
- `fact_total` - Financial transactions (revenue/expenses)
- `fact_occupancyrentarea` - Occupancy metrics by property/month
- `fact_leasingactivity` - Pipeline and deal flow management (separate from financial reporting)
- `dim_fp_customercreditscorecustomdata` - Credit scores and company information (191 records)
- `dim_fp_customertoparentmap` - Parent company mapping for corporate structures (1000 records)
- `fact_fp_fmvm_marketunitrates` - Market unit rates for benchmarking

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

# 5. Extract new tenants with credit scores
python Development/Python_Scripts/extract_new_tenants_fund2_fund3.py
```

## Working with Fund-Specific Data

When filtering for specific funds:
1. Use filtered data in `Data/Fund2_Filtered/` for Fund 2
2. Run `python Development/Python_Scripts/filter_fund2_data.py` to regenerate
3. Validate with `python Development/Fund2_Validation_Results/validate_fund2_accuracy.py`

## Customer Code Mapping Logic

### Table Relationships for Customer Identity

The customer identification system uses a three-table architecture to provide business-friendly codes and company information:

```
dim_commcustomer (Primary Tenant Table)
├── tenant_id: Unique tenant identifier in system
├── customer_id: Links to credit and parent tables (JOIN KEY)
├── tenant_code: Technical code (t0000xxx format)
└── lessee_name: Legal company name

dim_fp_customercreditscorecustomdata (Credit & Company Data)
├── hmyperson_customer: = customer_id from dim_commcustomer (JOIN)
├── customer code: Business code (c0000xxx format)
├── customer name: Company display name
└── credit score: Risk assessment (0-10 scale)

dim_fp_customertoparentmap (Corporate Structure)
├── customer hmy: = customer_id from dim_commcustomer (JOIN)
├── customer code: Business code (c0000xxx format)
├── customer name: Company display name
└── parent customer hmy: Link to parent company
```

### Customer Code Lookup Priority

When retrieving customer codes and names, follow this priority:

1. **Primary Source**: `dim_fp_customercreditscorecustomdata`
   - Check using customer_id = hmyperson_customer
   - Returns customer code and enhanced company name
   
2. **Secondary Source**: `dim_fp_customertoparentmap`
   - Check using customer_id = customer hmy
   - Returns customer code if not in credit table
   
3. **Fallback**: `dim_commcustomer`
   - Use lessee_name when no match in other tables
   - Always available for all tenants

### DAX Pattern for Customer Lookups

```dax
Customer Code Lookup = 
VAR CustomerID = SELECTEDVALUE(dim_commcustomer[customer id])
VAR CreditCode = LOOKUPVALUE(
    dim_fp_customercreditscorecustomdata[customer code],
    dim_fp_customercreditscorecustomdata[hmyperson_customer], CustomerID
)
VAR ParentCode = LOOKUPVALUE(
    dim_fp_customertoparentmap[customer code],
    dim_fp_customertoparentmap[customer hmy], CustomerID
)
RETURN COALESCE(CreditCode, ParentCode)
```

### Key Points

- Customer codes (c0000xxx format) are business-friendly identifiers
- Codes are consistent when present in both credit and parent tables
- Not all customers have codes - subset based on credit assessment
- Use customer_id as the primary join key for all lookups
- Parent company relationships enable consolidated risk assessment

## Credit Score and Risk Analysis

### New Data Tables for Credit Analysis

#### dim_fp_customercreditscorecustomdata
Contains credit scores and comprehensive company information:
- **hmyperson_customer**: Customer ID reference (matches dim_commcustomer.customer_id)
- **customer name**: Company name
- **credit score**: Numeric credit score (typical range 0-10)
- **date**: Credit score date
- **company location**: Company address
- **annual revenue**: Company annual revenue
- **primary industry**: Industry classification
- **ownership**: Ownership structure (e.g., Private, Public, PE-backed)

#### dim_fp_customertoparentmap
Maps customer entities to parent companies for corporate structures:
- **customer hmy**: Child customer ID
- **parent customer hmy**: Parent customer ID
- **customer code**: Customer reference code
- **customer name**: Customer/entity name

### Credit Risk Analysis Workflows
```sql
-- Find tenants with credit scores
SELECT t.tenant_id, c.customer_name, cs.credit_score, cs.date
FROM dim_commcustomer c
JOIN dim_fp_customercreditscorecustomdata cs 
    ON c.customer_id = cs.hmyperson_customer
JOIN fact_amendmentsunitspropertytenant t 
    ON c.customer_id = t.customer_id

-- Find parent company relationships
SELECT child.customer_name as Child_Company,
       parent.customer_name as Parent_Company,
       cs.credit_score as Parent_Credit_Score
FROM dim_fp_customertoparentmap pm
JOIN dim_fp_customercreditscorecustomdata child_cs 
    ON pm.customer_hmy = child_cs.hmyperson_customer
JOIN dim_fp_customercreditscorecustomdata cs 
    ON pm.parent_customer_hmy = cs.hmyperson_customer
```

### Credit Score DAX Patterns
```dax
// Average portfolio credit score
Portfolio Credit Score = 
AVERAGEX(
    FILTER(
        dim_fp_customercreditscorecustomdata,
        dim_fp_customercreditscorecustomdata[credit score] <> BLANK()
    ),
    dim_fp_customercreditscorecustomdata[credit score]
)

// Credit risk categorization
Credit Risk Category = 
SWITCH(
    TRUE(),
    dim_fp_customercreditscorecustomdata[credit score] >= 8, "Low Risk",
    dim_fp_customercreditscorecustomdata[credit score] >= 6, "Medium Risk", 
    dim_fp_customercreditscorecustomdata[credit score] >= 4, "High Risk",
    "Very High Risk"
)
```

## New in v5.0: Enhanced Analytics Features

### Net Absorption (Same-Store FPR Methodology)
**Purpose**: Measures net change in occupied space using Financial Planning & Reporting methodology.

**Key Components**:
- **SF Commenced**: New leases starting in period (from `dim_fp_amendmentsunitspropertytenant`)
- **SF Expired**: Lease terminations in period (from `dim_fp_terminationtomoveoutreas`) 
- **Net Absorption**: SF Commenced - SF Expired

**Business Rules**:
- Same-store properties only (acquired before period start, not disposed during)
- Include both "Activated" AND "Superseded" statuses
- Use latest amendment sequence logic to prevent double-counting
- Validate with rent charges for data quality

**Fund 2 Enhanced Filtering**:
- 201 total properties (195 core + 6 high-activity additions)
- Based on FPR benchmark analysis for improved accuracy
- Target: Q4 2024 = -167,821 SF net absorption

### Leasing Spreads Analysis
**Purpose**: Measures rent growth across different benchmarks.

**Types of Spreads**:
1. **Spread Over Prior Lease**: Current vs previous lease rate for renewals
2. **Spread Over Business Plan**: Actual vs underwriting assumptions (Fund 2: $5.54 PSF, Fund 3: $9.19 PSF)
3. **Spread Over Forecast Manager**: Actual vs budgeted rates (~95% of BP rates)

**Data Source**: `fact_leasingactivity` with area-weighted calculations

### Downtime & Pipeline Analysis  
**Purpose**: Tracks deal velocity and pipeline health.

**Key Metrics**:
- **Average Time to Lease**: Days between lease signing and commencement
- **Pipeline Aging**: 0-30, 31-90, 90+ day categories
- **Average Days in Pipeline**: Creation to execution timeframe

**Performance Benchmarks**:
- Excellent: ≤ 60 days
- Good: 61-90 days  
- Fair: 91-120 days
- Needs Attention: > 120 days

### Credit Risk Methodology
**Purpose**: Portfolio credit risk assessment and tenant analysis.

**Credit Score Scale** (0-10):
- **8.0-10.0**: Low Risk
- **6.0-7.9**: Medium Risk
- **4.0-5.9**: High Risk  
- **0.0-3.9**: Very High Risk

**Enhanced Risk Logic**:
1. Yardi `is_at_risk_tenant` flag (priority)
2. Credit score < 4.0 (high risk)
3. Credit score 4.0-5.9 (watch list)
4. Parent company score inheritance via `dim_fp_customertoparentmap`

**Portfolio Metrics**:
- Revenue at Risk %: Annual revenue from high-risk tenants
- Credit Coverage %: Percentage of tenants with credit scores  
- Portfolio Health Score: Composite 0-100 score

### Pipeline vs Financial Measures
**Important Distinction**:

**Pipeline Measures** (`fact_leasingactivity`):
- Forward-looking deal analysis
- All deal stages (Lead → Executed)
- Sales team performance tracking
- Examples: `Pipeline New Leases Executed Count`, `Active Leasing Pipeline Count`

**Financial Measures** (amendment-based):
- Historical accuracy for reporting
- Only executed/activated leases
- NOI and rent roll validation
- Examples: `New Leases Count`, `Current Monthly Rent`

**When to Use**:
- **Pipeline**: Forecasting, sales analysis, deal flow
- **Financial**: Official reporting, compliance, investor reports

### Enhanced Fund Analysis
**Fund 2 Enhanced Properties**:
- Uses curated property list (201 properties)
- Includes high-activity properties from FPR analysis
- All Fund 2 measures use enhanced filtering

**Fund 3 Properties**:
- Initial identification (~15 properties)
- Based on new lease activity analysis
- Requires business validation

### Data Quality & Performance Monitoring
**Comprehensive Validation Framework**:
- Real-time data quality scoring
- Performance monitoring measures
- Alert systems for critical issues
- Executive health dashboards

**Key Health Indicators**:
- Overall System Health (0-100)
- Dashboard Readiness Score
- Critical Data Alerts
- Performance Status

## v5.0 Implementation Workflow

### 1. Data Model Updates
```sql
-- Verify new table relationships
-- Check fact_leasingactivity integration
-- Validate credit score table joins
-- Test termination table connections
```

### 2. Measure Implementation
```
-- Import measures by functional area:
1. Core Financial (Start here - 42 measures)
2. Leasing Activity (Pipeline analysis - 85 measures)  
3. Credit Risk (Risk assessment - 30 measures)
4. Net Absorption (FPR methodology - 35 measures)
5. Performance (Monitoring - 25 measures)
```

### 3. Validation Testing
```python
# Run comprehensive validation
python Development/Test_Automation_Framework/test_orchestrator.py --all

# Test net absorption accuracy
python Development/Python_Scripts/net_absorption_validator.py

# Validate credit risk measures
python Development/Python_Scripts/credit_risk_validator.py
```

### 4. Business Logic Reference
Refer to `Claude_AI_Reference/Documentation/05_Business_Logic_Reference.md` for detailed calculation methodologies and business rules.

---

**Version 5.1 Status**: Production Ready - Dynamic Date Handling
**Total Measures**: 217+ across 5 functional areas
**Key Update**: All measures now use dim_lastclosedperiod for date reference (replacing TODAY())
**Features**: Net absorption, leasing spreads, credit risk, downtime analysis
**Accuracy Targets**: 95-99% across all measure categories