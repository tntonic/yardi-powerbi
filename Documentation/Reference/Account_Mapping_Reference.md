# Financial Account Mapping Reference

## Overview

This document provides the complete mapping of Yardi account codes to financial statement categories, including specific account ranges, their business purposes, and usage in calculations.

## Account Code Structure

### General Ledger Account Ranges

```
Account Range Structure:
- 8-digit numeric codes
- First 2 digits: Major category
- Digits 3-4: Sub-category
- Digits 5-6: Detail level
- Digits 7-8: Sub-detail or property-specific
```

## Revenue Accounts (40000000 - 49999999)

### Base Rental Income (40000000 - 40999999)
```
Account Range: 40000000 - 40999999
Description: Monthly base rent from tenant leases
Usage in Calculations:
- Total Revenue
- NOI calculations
- Revenue per square foot
Sign Convention: Negative values (credits) in fact_total
Display Convention: Multiply by -1 for positive display
```

### Percentage Rent (41000000 - 41999999)
```
Account Range: 41000000 - 41999999
Description: Variable rent based on tenant sales
Usage in Calculations:
- Total Revenue (included)
- Percentage rent analysis
Sign Convention: Negative values (credits)
```

### Expense Recoveries (42000000 - 42999999)
```
Account Range: 42000000 - 42999999
Description: Tenant reimbursements for operating expenses
Usage in Calculations:
- Total Revenue (included)
- Recovery ratio analysis
Sign Convention: Negative values (credits)
```

### Other Income (43000000 - 49999999)
```
Account Range: 43000000 - 49999999
Description: Parking, signage, antenna, miscellaneous income
Usage in Calculations:
- Total Revenue (included)
- Ancillary income tracking
Sign Convention: Negative values (credits)
```

## Operating Expense Accounts (50000000 - 59999999)

### Property Management (50000000 - 50999999)
```
Account Range: 50000000 - 50999999
Description: Property management fees and administrative costs
Usage in Calculations:
- Operating Expenses
- NOI calculations
Sign Convention: Positive values (debits)
```

### Utilities (51000000 - 51999999)
```
Account Range: 51000000 - 51999999
Description: Electric, gas, water, sewer expenses
Sub-categories:
- 51100000-51199999: Electric
- 51200000-51299999: Gas
- 51300000-51399999: Water/Sewer
- 51400000-51499999: Other utilities
Usage in Calculations:
- Operating Expenses
- Utility cost per SF
- Recovery calculations
Sign Convention: Positive values (debits)
```

### Repairs & Maintenance (52000000 - 52999999)
```
Account Range: 52000000 - 52999999
Description: Routine maintenance and repairs
Sub-categories:
- 52100000-52199999: HVAC
- 52200000-52299999: Electrical
- 52300000-52399999: Plumbing
- 52400000-52499999: General maintenance
Usage in Calculations:
- Operating Expenses
- R&M per SF
Sign Convention: Positive values (debits)
```

### Contracted Services (53000000 - 53999999)
```
Account Range: 53000000 - 53999999
Description: Janitorial, landscaping, security services
Sub-categories:
- 53100000-53199999: Janitorial
- 53200000-53299999: Landscaping
- 53300000-53399999: Security
Usage in Calculations:
- Operating Expenses
- Service cost analysis
Sign Convention: Positive values (debits)
```

### Insurance & Taxes (54000000 - 54999999)
```
Account Range: 54000000 - 54999999
Description: Property insurance and real estate taxes
Sub-categories:
- 54100000-54499999: Property insurance
- 54500000-54999999: Real estate taxes
Usage in Calculations:
- Operating Expenses
- Tax and insurance per SF
Sign Convention: Positive values (debits)
```

### Marketing & Leasing (55000000 - 55999999)
```
Account Range: 55000000 - 55999999
Description: Marketing and leasing expenses
Usage in Calculations:
- Operating Expenses (typically excluded from recoverable)
Sign Convention: Positive values (debits)
```

## Recoverable vs Non-Recoverable Expenses

### Recoverable Expenses (61000000 - 61999999)
```
Account Range: 61000000 - 61999999
Description: Expenses that can be recovered from tenants
Usage in Calculations:
- Total Recoverable Expenses
- Recovery rate calculations
- CAM reconciliation
Typical Categories:
- Property taxes
- Insurance
- Common area maintenance
- Utilities (if applicable)
Sign Convention: Positive values (debits)
```

### Non-Recoverable Expenses (62000000 - 62999999)
```
Account Range: 62000000 - 62999999
Description: Expenses borne by landlord
Usage in Calculations:
- Total Non-Recoverable Expenses
- NOI impact analysis
Typical Categories:
- Management fees
- Leasing commissions
- Capital reserves
- Ownership costs
Sign Convention: Positive values (debits)
```

## Capital Expenditure Accounts (16000000 Series)

### Purchase Price (16005150)
```
Account Code: 16005150
Description: Property acquisition purchase price
Usage in Calculations:
- Total acquisition cost
- Cap rate calculations
Amount Type: Cumulative Actual
Sign Convention: Positive values
```

### Land (16005200)
```
Account Code: 16005200
Description: Land component of acquisition
Usage in Calculations:
- Total acquisition cost
- FAR calculations
Amount Type: Cumulative Actual
Sign Convention: Positive values
```

### Closing Costs (16005250)
```
Account Code: 16005250
Description: Acquisition closing costs
Usage in Calculations:
- Total acquisition cost
Amount Type: Cumulative Actual
Sign Convention: Positive values
```

### Solar Panels (16005260)
```
Account Code: 16005260
Description: Solar panel installations
Usage in Calculations:
- Total acquisition cost
- Sustainability tracking
Amount Type: Cumulative Actual
Sign Convention: Positive values
```

### Tenant Improvements (16005310)
```
Account Code: 16005310
Description: Tenant improvement costs
Usage in Calculations:
- Total CAPEX
- TI per SF analysis
- Leasing cost tracking
Amount Type: Actual
Sign Convention: Positive values
```

### Capital Expenses (16005340)
```
Account Code: 16005340
Description: General capital expenditures
Usage in Calculations:
- Total CAPEX
- Capital reserve analysis
Amount Type: Actual
Sign Convention: Positive values
```

### Construction Management Fees (16005360)
```
Account Code: 16005360
Description: Construction management costs
Usage in Calculations:
- Total CAPEX
- Project cost tracking
Amount Type: Actual
Sign Convention: Positive values
```

### Leasing Commissions (16005450)
```
Account Code: 16005450
Description: Broker and leasing commissions
Usage in Calculations:
- Total leasing costs
- Cost per lease analysis
Amount Type: Actual
Sign Convention: Positive values
```

## Excluded Accounts

### Depreciation (64006000)
```
Account Code: 64006000
Description: Depreciation expense
Exclusion Reason: Non-cash expense excluded from NOI
```

### Corporate Overhead (64001100 - 64001600)
```
Account Range: 64001100 - 64001600
Description: Corporate level expenses
Exclusion Reason: Not property-level operating expenses
```

## Book-Specific Account Usage

### Accrual Book
```
Book Name: Accrual
Purpose: GAAP-based financial reporting
Account Usage:
- All revenue accounts (40000000-49999999)
- All expense accounts (50000000-62999999)
- Capital accounts for cumulative totals
```

### Business Plan Books
```
Book Names: Business Plan, Business Plan 2024, etc.
Purpose: Forecasting and budgeting
Account Usage:
- Same account structure as Accrual
- Used for forward-looking projections
- Source for Year 1 NOI calculations
```

### Budget Books
```
Book Names: BA-2024, Budget-Accrual
Purpose: Annual budget tracking
Account Usage:
- Forecasted CAPEX items
- Future period projections
```

### FPR Book (Book ID 46)
```
Book Name: FPR (Financial Planning & Reporting)
Purpose: Cash-basis NOI calculations
Special Accounts:
- 646: Special FPR adjustments
- 648: FPR timing differences
- 825: FPR reconciliation items
- 950, 953, 957: FPR-specific accounts
- 1111-1114: FPR balance sheet movements
- 1120, 1123: Additional FPR items
```

## DAX Implementation Examples

### Total Revenue Calculation
```dax
Total Revenue = 
CALCULATE(
    SUM(fact_total[amount]) * -1,
    dim_account[account code] >= 40000000,
    dim_account[account code] <= 49999999,
    fact_total[amount type] = "Actual",
    dim_book[book] = "Accrual"
)
```

### Operating Expenses Calculation
```dax
Operating Expenses = 
CALCULATE(
    ABS(SUM(fact_total[amount])),
    dim_account[account code] >= 50000000,
    dim_account[account code] <= 59999999,
    NOT(dim_account[account code] IN {64001100, 64001101, 64001102, 64001103, 64001104, 64001105, 64001106, 64001600}),
    dim_account[account code] <> 64006000,
    fact_total[amount type] = "Actual",
    dim_book[book] = "Accrual"
)
```

### Total CAPEX Calculation
```dax
Total CAPEX = 
CALCULATE(
    SUM(fact_total[amount]),
    dim_account[account code] IN {16005310, 16005340, 16005360, 16005450},
    fact_total[amount type] = "Actual"
)
```

## Validation Queries

### Verify Revenue Accounts
```sql
SELECT 
    account_code,
    account_name,
    COUNT(*) as transaction_count,
    SUM(amount) as total_amount
FROM fact_total f
JOIN dim_account a ON f.account_id = a.account_id
WHERE a.account_code >= 40000000 
  AND a.account_code <= 49999999
GROUP BY account_code, account_name
ORDER BY account_code;
```

### Check Sign Conventions
```sql
-- Revenue should be negative (credits)
SELECT 
    'Revenue' as category,
    COUNT(CASE WHEN amount > 0 THEN 1 END) as positive_count,
    COUNT(CASE WHEN amount < 0 THEN 1 END) as negative_count
FROM fact_total f
JOIN dim_account a ON f.account_id = a.account_id
WHERE a.account_code BETWEEN 40000000 AND 49999999

UNION ALL

-- Expenses should be positive (debits)
SELECT 
    'Expenses' as category,
    COUNT(CASE WHEN amount > 0 THEN 1 END) as positive_count,
    COUNT(CASE WHEN amount < 0 THEN 1 END) as negative_count
FROM fact_total f
JOIN dim_account a ON f.account_id = a.account_id
WHERE a.account_code BETWEEN 50000000 AND 59999999;
```

## Important Notes

1. **Sign Conventions**: Revenue accounts typically store negative values (credits) in the database and need to be multiplied by -1 for display
2. **Amount Types**: Different amount types (Actual, Budget, Cumulative Actual) serve different purposes
3. **Book Selection**: Always filter by appropriate book for the analysis being performed
4. **Exclusions**: Remember to exclude depreciation and corporate overhead from NOI calculations
5. **Property-Level**: All operating accounts should be at the property level for accurate NOI