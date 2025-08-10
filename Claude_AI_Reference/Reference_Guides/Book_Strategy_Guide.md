# Book Strategy Documentation

## Overview

The Yardi system uses different "books" to represent various accounting perspectives and reporting requirements. Understanding the book strategy is critical for accurate financial analysis and reporting.

## Book Architecture

### What is a Book?
A "book" in Yardi represents a specific accounting perspective or version of the financial data. The same transaction can be recorded differently across books based on accounting methods, timing, or reporting requirements.

## Standard Books

### 1. Accrual Book (Book ID: 1)
```
Purpose: Standard GAAP accrual-based accounting
Usage: Primary financial reporting, NOI calculations
Key Characteristics:
- Revenue recognized when earned
- Expenses recognized when incurred
- Matches revenues with expenses
- Used for financial statements

DAX Usage:
fact_total[book_id] = 1 OR dim_book[book] = "Accrual"

Common Calculations:
- Traditional NOI
- Financial statements
- Period comparisons
```

### 2. Cash Book (Book ID: 2)
```
Purpose: Cash-basis accounting
Usage: Cash flow analysis, collection tracking
Key Characteristics:
- Revenue recognized when received
- Expenses recognized when paid
- Focus on actual cash movements
- Used for cash management

DAX Usage:
fact_total[book_id] = 2 OR dim_book[book] = "Cash"

Common Calculations:
- Cash flow statements
- Collection analysis
- Payment timing
```

### 3. FPR Book (Book ID: 46) - Critical
```
Purpose: Financial Planning & Reporting specialized view
Usage: Enhanced NOI calculations with balance sheet movements
Key Characteristics:
- Hybrid approach between cash and accrual
- Includes balance sheet account movements
- More accurate property-level performance
- Used by institutional investors

Special Account Codes:
- 646: FPR adjustments
- 648: Timing differences
- 825: Reconciliation items
- 950, 953, 957: FPR-specific accounts
- 1111-1114: Balance sheet movements
- 1120, 1123: Additional FPR items

DAX Usage:
fact_total[book_id] = 46

Common Calculations:
- FPR NOI
- Cash-adjusted NOI
- True property performance
```

### 4. Budget Books
```
Purpose: Annual budget tracking and variance analysis
Common Names:
- "Budget-Accrual"
- "BA-2024" (Budget Accrual 2024)
- "Budget 2024"

Usage: Budget vs actual analysis
Key Characteristics:
- Contains approved budget amounts
- Updated annually or quarterly
- Used for variance reporting
- May include forecast updates

DAX Pattern:
dim_book[book] CONTAINS "Budget" OR 
dim_book[book] LIKE "BA-%"

Common Calculations:
- Budget variance
- YTD budget vs actual
- Forecast accuracy
```

### 5. Business Plan Books
```
Purpose: Strategic planning and forecasting
Common Names:
- "Business Plan"
- "Business Plan 2024"
- "BP-Original"

Usage: Long-term planning, acquisition underwriting
Key Characteristics:
- Multi-year projections
- Acquisition assumptions
- Used for Year 1 NOI calculations
- Updated periodically

DAX Pattern:
dim_book[book] CONTAINS "Business Plan"

Common Calculations:
- Year 1 NOI projections
- Acquisition cap rates
- Hold period analysis
```

### 6. Forecast Books
```
Purpose: Rolling forecasts and projections
Common Names:
- "Forecast"
- "Q1 Forecast 2024"
- "Rolling Forecast"

Usage: Updated projections based on actual performance
Key Characteristics:
- More frequent updates than budget
- Remainder of year projections
- Used for revised guidance

DAX Pattern:
dim_book[book] CONTAINS "Forecast"
```

## Book Selection Strategy

### Hierarchical Approach
```dax
// Book selection priority for financial analysis
Selected Book Value = 
VAR ActualValue = 
    CALCULATE(
        SUM(fact_total[amount]),
        dim_book[book] = "Accrual",
        fact_total[amount_type] = "Actual"
    )
VAR BudgetValue = 
    CALCULATE(
        SUM(fact_total[amount]),
        dim_book[book] CONTAINS "Budget",
        fact_total[amount_type] = "Budget"
    )
VAR ForecastValue = 
    CALCULATE(
        SUM(fact_total[amount]),
        dim_book[book] CONTAINS "Forecast",
        fact_total[amount_type] = "Forecast"
    )
RETURN
    COALESCE(ActualValue, ForecastValue, BudgetValue)
```

### Multi-Book Analysis
```dax
// Comparing across books
Book Comparison = 
SUMMARIZE(
    fact_total,
    dim_book[book],
    dim_date[year_month],
    "Amount", SUM(fact_total[amount])
)
```

## Book-Specific Calculations

### Traditional NOI (Accrual Book)
```dax
Traditional NOI = 
CALCULATE(
    [Total Revenue] - [Operating Expenses],
    dim_book[book] = "Accrual",
    fact_total[amount_type] = "Actual"
)
```

### FPR NOI (Book 46)
```dax
FPR NOI = 
CALCULATE(
    SUM(fact_total[amount]),
    dim_book[book_id] = 46
)
// OR if using unified fact table
FPR NOI Alternative = 
CALCULATE(
    SUM(fact_total[amount]),
    dim_book[book_id] = 46,
    dim_account[account_code] IN {646, 648, 825, 950, 953, 957, 1111, 1112, 1113, 1114, 1120, 1123}
)
```

### Budget Variance
```dax
Budget Variance = 
VAR Actual = 
    CALCULATE(
        SUM(fact_total[amount]),
        dim_book[book] = "Accrual",
        fact_total[amount_type] = "Actual"
    )
VAR Budget = 
    CALCULATE(
        SUM(fact_total[amount]),
        dim_book[book] CONTAINS "Budget",
        fact_total[amount_type] = "Budget"
    )
RETURN
    Actual - Budget
```

### Business Plan Metrics
```dax
// Acquisition In-Place NOI from Business Plan
Acquisition NOI BP = 
VAR AcqDate = CALCULATE(MIN(dim_fp_buildingcustomdata[acq. date]))
VAR FirstFullMonth = EOMONTH(AcqDate, 1)
RETURN
CALCULATE(
    [Total Revenue] - [Operating Expenses],
    dim_book[book] CONTAINS "Business Plan",
    dim_date[date] = FirstFullMonth
) * 12

// Year 1 NOI from Business Plan
Year 1 NOI BP = 
VAR AcqDate = CALCULATE(MIN(dim_fp_buildingcustomdata[acq. date]))
VAR Year1End = DATEADD(AcqDate, 12, MONTH)
RETURN
CALCULATE(
    [Total Revenue] - [Operating Expenses],
    dim_book[book] CONTAINS "Business Plan",
    DATESBETWEEN(dim_date[date], AcqDate, Year1End)
)
```

## Amount Type Interactions

### Amount Types by Book
```
Accrual Book:
- Actual: Historical transactions
- Budget: Not typically used
- Cumulative Actual: Running totals for capital accounts

Budget Books:
- Actual: Budget amounts (confusingly)
- Budget: Alternative budget scenarios
- Forecast: Mid-year updates

FPR Book:
- Actual: Adjusted actual amounts
- Various: Depends on specific FPR methodology
```

### Filtering Strategy
```dax
// Proper amount type filtering by book
Filtered Amount = 
SWITCH(
    SELECTEDVALUE(dim_book[book]),
    "Accrual", 
        CALCULATE(
            SUM(fact_total[amount]),
            fact_total[amount_type] = "Actual"
        ),
    "Budget", 
        CALCULATE(
            SUM(fact_total[amount]),
            fact_total[amount_type] IN {"Budget", "Actual"}
        ),
    SUM(fact_total[amount])
)
```

## Common Book Scenarios

### Scenario 1: Monthly Reporting Package
```
Books Required:
1. Accrual - Actual results
2. Budget - Current year budget
3. Forecast - Latest forecast
4. Prior Year Accrual - YoY comparison

Output:
- Actual vs Budget variance
- Actual vs Forecast variance  
- YoY comparison
- FPR NOI reconciliation
```

### Scenario 2: Acquisition Analysis
```
Books Required:
1. Business Plan - Original underwriting
2. Accrual - Actual performance
3. FPR - True economic performance

Output:
- Actual vs underwriting
- Investment performance metrics
- Cap rate achievement
```

### Scenario 3: Year-End Planning
```
Books Required:
1. Current Year Budget
2. Current Year Forecast
3. Next Year Budget
4. Business Plan

Output:
- Current year projection
- Next year budget
- Long-term plan alignment
```

## Book Validation

### Data Quality Checks
```sql
-- Verify book coverage
SELECT 
    b.book,
    b.book_id,
    COUNT(DISTINCT f.property_id) as properties,
    COUNT(DISTINCT f.month) as months,
    SUM(CASE WHEN f.amount_type = 'Actual' THEN 1 ELSE 0 END) as actual_records,
    SUM(CASE WHEN f.amount_type = 'Budget' THEN 1 ELSE 0 END) as budget_records
FROM fact_total f
JOIN dim_book b ON f.book_id = b.book_id
GROUP BY b.book, b.book_id
ORDER BY b.book_id;

-- Check FPR book special accounts
SELECT 
    a.account_code,
    a.account_name,
    COUNT(*) as transaction_count,
    SUM(f.amount) as total_amount
FROM fact_total f
JOIN dim_account a ON f.account_id = a.account_id
JOIN dim_book b ON f.book_id = b.book_id
WHERE b.book_id = 46
  AND a.account_code IN (646, 648, 825, 950, 953, 957, 1111, 1112, 1113, 1114, 1120, 1123)
GROUP BY a.account_code, a.account_name;
```

### Book Reconciliation
```dax
// Reconcile Traditional vs FPR NOI
NOI Reconciliation = 
VAR TraditionalNOI = [Traditional NOI]
VAR FPRNOI = [FPR NOI]
VAR Difference = FPRNOI - TraditionalNOI
VAR DifferencePercent = DIVIDE(Difference, TraditionalNOI, 0) * 100
RETURN
    "Traditional: " & FORMAT(TraditionalNOI, "$#,##0") & 
    " | FPR: " & FORMAT(FPRNOI, "$#,##0") & 
    " | Diff: " & FORMAT(Difference, "$#,##0") & 
    " (" & FORMAT(DifferencePercent, "0.0%") & ")"
```

## Best Practices

### 1. Always Specify Book
Never assume a default book - always explicitly filter

### 2. Understand Amount Types
Different books use amount_type differently

### 3. Document Book Usage
Clearly document which book is used in each measure

### 4. Validate Book Data
Regularly verify data completeness across books

### 5. Handle Missing Books
Use COALESCE patterns for fallback logic

### 6. Consider Performance
Book 46 may have its own optimized fact table

## Implementation Notes

### Power BI Setup
1. Create book parameter for user selection
2. Set default book based on report purpose
3. Show book selection in report header
4. Use tooltips to explain book differences

### User Training Points
1. Explain why different books show different values
2. Document which book to use for which purpose
3. Provide reconciliation reports between books
4. Train on FPR vs Traditional NOI differences