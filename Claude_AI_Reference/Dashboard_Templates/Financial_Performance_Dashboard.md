# Financial Performance Dashboard

## Overview

The Financial Performance Dashboard provides comprehensive financial analysis including revenue, expenses, NOI calculations, budget variance analysis, and cash flow projections. This dashboard serves financial analysts, property managers, and senior leadership.

## Dashboard Specifications

### Page Layout (1920x1080 optimized)

```
┌─────────────────────────────────────────────────────────────┐
│                FINANCIAL PERFORMANCE                        │
│                  P&L Analysis & Trends                      │
└─────────────────────────────────────────────────────────────┘

┌─────────────┬─────────────┬─────────────┬─────────────┬─────┐
│   Revenue   │ Expenses    │     NOI     │ NOI Margin  │ FPR │
│   $12.5M    │   $4.2M     │   $8.3M     │   66.4%     │     │
│  +5.2% YoY  │ +3.1% YoY   │ +6.8% YoY   │ +1.1 pts    │$8.1M│
└─────────────┴─────────────┴─────────────┴─────────────┴─────┘

┌─────────────────────────┬───────────────────────────────────┐
│     Revenue Trend       │      NOI Waterfall               │
│     vs Budget           │      (YoY Analysis)               │
│     [Combo Chart]       │      [Waterfall Chart]           │
└─────────────────────────┴───────────────────────────────────┘

┌─────────────────────────┬───────────────────────────────────┐
│   P&L by Property       │      Expense Analysis             │
│   [Matrix]              │      [Treemap/Pie]               │
└─────────────────────────┴───────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                Financial Performance Summary                │
│ Property  │ Revenue │ Expenses │ NOI    │ Margin │ vs Bgt  │
│ Prop A    │ $2.1M   │ $0.7M    │ $1.4M  │ 66.7%  │ +2.1%  │
│ Prop B    │ $1.8M   │ $0.6M    │ $1.2M  │ 66.7%  │ -1.2%  │
└─────────────────────────────────────────────────────────────┘
```

## Visual Components

### 1. Financial KPI Cards (Top Row)

#### Total Revenue Card
```dax
// Primary Measure
Total Revenue = [Total Revenue]

// Supporting Measures
Revenue YoY Growth % = [Revenue YoY Growth %]
Revenue Budget Variance % = 
VAR ActualRevenue = [Total Revenue]
VAR BudgetRevenue = 
    CALCULATE(
        SUM(fact_total[amount]),
        dim_account[account code] >= 40000000,
        dim_account[account code] < 50000000,
        fact_total[amount type] = "Budget"
    )
RETURN DIVIDE(ActualRevenue - BudgetRevenue, BudgetRevenue, 0) * 100

// Card Configuration
Visual Type: Card
Format: $12.5M
Primary Trend: YoY Growth % with arrow
Secondary Trend: Budget Variance %
Conditional Formatting:
- Green: Revenue growth >3%
- Yellow: Revenue growth 0-3%
- Red: Revenue decline
Font: Segoe UI, Bold, 28pt
```

#### Operating Expenses Card
```dax
// Primary Measure
Operating Expenses = [Operating Expenses]

// Supporting Measures
Expense YoY Growth % = 
VAR CurrentExpenses = [Operating Expenses]
VAR PriorYearExpenses = 
    CALCULATE(
        [Operating Expenses],
        SAMEPERIODLASTYEAR(dim_date[date])
    )
RETURN DIVIDE(CurrentExpenses - PriorYearExpenses, PriorYearExpenses, 0) * 100

Expense Budget Variance % = 
VAR ActualExpenses = [Operating Expenses]
VAR BudgetExpenses = 
    CALCULATE(
        ABS(SUM(fact_total[amount])),
        dim_account[account code] >= 50000000,
        dim_account[account code] < 60000000,
        fact_total[amount type] = "Budget"
    )
RETURN DIVIDE(ActualExpenses - BudgetExpenses, BudgetExpenses, 0) * 100

// Card Configuration
Visual Type: Card
Format: $4.2M
Primary Trend: YoY Growth % (Red if positive, Green if negative)
Secondary Trend: Budget Variance %
Conditional Formatting:
- Green: Expense growth <2%
- Yellow: Expense growth 2-5%
- Red: Expense growth >5%
```

#### Net Operating Income Card
```dax
// Primary Measure
NOI = [NOI (Net Operating Income)]

// Supporting Measures
NOI YoY Growth % = 
VAR CurrentNOI = [NOI (Net Operating Income)]
VAR PriorYearNOI = 
    CALCULATE(
        [NOI (Net Operating Income)],
        SAMEPERIODLASTYEAR(dim_date[date])
    )
RETURN DIVIDE(CurrentNOI - PriorYearNOI, PriorYearNOI, 0) * 100

NOI Budget Variance % = 
VAR ActualNOI = [NOI (Net Operating Income)]
VAR BudgetNOI = 
    VAR BudgetRevenue = 
        CALCULATE(
            SUM(fact_total[amount]),
            dim_account[account code] >= 40000000,
            dim_account[account code] < 50000000,
            fact_total[amount type] = "Budget"
        )
    VAR BudgetExpenses = 
        CALCULATE(
            ABS(SUM(fact_total[amount])),
            dim_account[account code] >= 50000000,
            dim_account[account code] < 60000000,
            fact_total[amount type] = "Budget"
        )
    RETURN BudgetRevenue - BudgetExpenses
RETURN DIVIDE(ActualNOI - BudgetNOI, BudgetNOI, 0) * 100

// Card Configuration
Visual Type: Card
Format: $8.3M
Primary Trend: YoY Growth % with arrow
Secondary Trend: Budget Variance %
Conditional Formatting:
- Green: NOI growth >5%
- Yellow: NOI growth 0-5%
- Red: NOI decline
```

#### NOI Margin Card
```dax
// Primary Measure
NOI Margin % = [NOI Margin %]

// Supporting Measures
NOI Margin YoY Change = [NOI Margin YoY Change]
NOI Margin Budget Variance = 
VAR ActualMargin = [NOI Margin %]
VAR BudgetMargin = 
    VAR BudgetRevenue = [Budget Revenue Total]
    VAR BudgetExpenses = [Budget Expense Total]
    RETURN DIVIDE(BudgetRevenue - BudgetExpenses, BudgetRevenue, 0) * 100
RETURN ActualMargin - BudgetMargin

// Card Configuration
Visual Type: Card
Format: 66.4%
Primary Trend: Percentage points change YoY
Secondary Trend: Budget variance in points
Conditional Formatting:
- Green: Margin >65%
- Yellow: Margin 55-65%
- Red: Margin <55%
```

#### FPR NOI Card
```dax
// Primary Measure
FPR NOI = [FPR NOI]

// Supporting Measures
FPR vs Traditional NOI Variance = [NOI Timing Difference]
FPR NOI YoY Growth % = 
VAR CurrentFPR = [FPR NOI]
VAR PriorYearFPR = 
    CALCULATE(
        [FPR NOI],
        SAMEPERIODLASTYEAR(dim_date[date])
    )
RETURN DIVIDE(CurrentFPR - PriorYearFPR, PriorYearFPR, 0) * 100

// Card Configuration
Visual Type: Card
Format: $8.1M
Primary Trend: YoY Growth %
Secondary: Variance vs Traditional NOI
Color: Orange (#FFC000) to distinguish from traditional NOI
Tooltip: "FPR NOI uses balance sheet movements (Book 46)"
```

### 2. Revenue Analysis Chart

#### Revenue vs Budget Trend
```dax
// Chart Measures
Total Revenue = [Total Revenue]
Budget Revenue = 
    CALCULATE(
        SUM(fact_total[amount]),
        dim_account[account code] >= 40000000,
        dim_account[account code] < 50000000,
        fact_total[amount type] = "Budget"
    )
Revenue Variance % = 
    DIVIDE([Total Revenue] - [Budget Revenue], [Budget Revenue], 0) * 100

Cumulative Revenue = 
    CALCULATE(
        [Total Revenue],
        DATESYTD(dim_date[date])
    )
Cumulative Budget Revenue = 
    CALCULATE(
        [Budget Revenue],
        DATESYTD(dim_date[date])
    )

// Chart Configuration
Visual Type: Combo Chart (Column + Line)
X-Axis: dim_date[date] (Month hierarchy)
Y-Axis 1 (Columns): Total Revenue, Budget Revenue
Y-Axis 2 (Line): Revenue Variance %
Date Range: Current fiscal year
Colors:
- Actual Revenue: Blue (#1F4E79)
- Budget Revenue: Light Blue (#B3D1FF)
- Variance Line: Green/Red based on positive/negative
Data Labels: Enabled for variance line
Secondary Y-Axis Range: -10% to +10%
```

### 3. NOI Waterfall Analysis

#### Year-over-Year NOI Bridge
```dax
// Waterfall Components
Prior Year NOI = 
    CALCULATE(
        [NOI (Net Operating Income)],
        SAMEPERIODLASTYEAR(dim_date[date])
    )

Revenue Impact = 
VAR CurrentRevenue = [Total Revenue]
VAR PriorRevenue = 
    CALCULATE([Total Revenue], SAMEPERIODLASTYEAR(dim_date[date]))
RETURN CurrentRevenue - PriorRevenue

Expense Impact = 
VAR CurrentExpenses = [Operating Expenses]
VAR PriorExpenses = 
    CALCULATE([Operating Expenses], SAMEPERIODLASTYEAR(dim_date[date]))
RETURN PriorExpenses - CurrentExpenses // Positive = expense reduction

Same Store Revenue Impact = 
    CALCULATE(
        [Revenue Impact],
        [Same Store Properties]
    )

Acquisition Revenue Impact = 
VAR TotalImpact = [Revenue Impact]
VAR SameStoreImpact = [Same Store Revenue Impact]
RETURN TotalImpact - SameStoreImpact

// Waterfall Configuration
Visual Type: Waterfall Chart
Categories: 
1. "Prior Year NOI" (Starting point)
2. "Same-Store Revenue" (Revenue Impact)
3. "Acquisition Revenue" (Acquisition Impact)
4. "Expense Management" (Expense Impact)
5. "Current NOI" (Ending point)

Colors:
- Starting/Ending: Blue (#1F4E79)
- Positive changes: Green (#70AD47)
- Negative changes: Red (#C5504B)
Data Labels: Currency format with +/- indicators
```

### 4. Property P&L Matrix

#### Financial Performance by Property
```dax
// Matrix Measures
Property Revenue = [Total Revenue]
Property Expenses = [Operating Expenses]
Property NOI = [NOI (Net Operating Income)]
Property NOI Margin = [NOI Margin %]
Property Budget Variance = [NOI Budget Variance %]

Revenue PSF = [Revenue PSF]
Expense PSF = DIVIDE([Operating Expenses], [Total Rentable Area], 0)
NOI PSF = DIVIDE([NOI (Net Operating Income)], [Total Rentable Area], 0)

// Matrix Configuration
Visual Type: Matrix
Rows: dim_property[property name]
Columns: Financial metrics
Values: 
- Revenue ($M format)
- Expenses ($M format)  
- NOI ($M format)
- NOI Margin (% format)
- Budget Var (% format with +/-)

Conditional Formatting:
- NOI Margin: Green >65%, Yellow 55-65%, Red <55%
- Budget Variance: Green >0%, Red <0%
Subtotals: Enabled for portfolio totals
Sorting: By NOI (Descending)
```

### 5. Expense Analysis

#### Expense Category Breakdown
```dax
// Expense Categories
Utilities Expense = 
    CALCULATE(
        [Operating Expenses],
        FILTER(
            dim_account,
            SEARCH("UTILIT", UPPER(dim_account[description]), 1, 0) > 0 ||
            SEARCH("ELECTRIC", UPPER(dim_account[description]), 1, 0) > 0 ||
            SEARCH("GAS", UPPER(dim_account[description]), 1, 0) > 0
        )
    )

Maintenance Expense = 
    CALCULATE(
        [Operating Expenses],
        FILTER(
            dim_account,
            SEARCH("MAINT", UPPER(dim_account[description]), 1, 0) > 0 ||
            SEARCH("REPAIR", UPPER(dim_account[description]), 1, 0) > 0
        )
    )

Insurance Expense = 
    CALCULATE(
        [Operating Expenses],
        FILTER(
            dim_account,
            SEARCH("INSUR", UPPER(dim_account[description]), 1, 0) > 0
        )
    )

Property Tax = 
    CALCULATE(
        [Operating Expenses],
        FILTER(
            dim_account,
            SEARCH("TAX", UPPER(dim_account[description]), 1, 0) > 0 &&
            SEARCH("PROPERTY", UPPER(dim_account[description]), 1, 0) > 0
        )
    )

Management Fee = 
    CALCULATE(
        [Operating Expenses],
        FILTER(
            dim_account,
            SEARCH("MANAGEMENT", UPPER(dim_account[description]), 1, 0) > 0 ||
            SEARCH("ADMIN", UPPER(dim_account[description]), 1, 0) > 0
        )
    )

Other Expenses = 
    [Operating Expenses] - [Utilities Expense] - [Maintenance Expense] - 
    [Insurance Expense] - [Property Tax] - [Management Fee]

// Treemap Configuration
Visual Type: Treemap
Categories: Expense category names
Values: Expense amounts
Colors: Gradient from light to dark blue
Data Labels: Category name and amount
Tooltip: Include percentage of total expenses
```

### 6. Financial Performance Summary Table

#### Comprehensive Property Analysis
```dax
// Summary Table Measures
Property Count = 1 // For property-level context
Total SF = [Total Rentable Area]
Occupancy = [Physical Occupancy %]
Revenue = [Total Revenue]
Expenses = [Operating Expenses]
NOI = [NOI (Net Operating Income)]
NOI Margin = [NOI Margin %]
Budget Variance = [NOI Budget Variance %]
Revenue PSF = [Revenue PSF]
Expense PSF = DIVIDE([Operating Expenses], [Total Rentable Area], 0)

// Performance Rankings
Revenue Rank = 
    RANKX(
        ALL(dim_property[property name]),
        [Total Revenue],
        ,
        DESC
    )

NOI Margin Rank = 
    RANKX(
        ALL(dim_property[property name]),
        [NOI Margin %],
        ,
        DESC
    )

// Table Configuration
Visual Type: Table
Columns:
1. Property Name
2. Total SF (Number with K suffix)
3. Occupancy % (Percentage)
4. Revenue ($M format)
5. Expenses ($M format)
6. NOI ($M format)
7. Margin % (Percentage)
8. vs Budget (Percentage with +/-)
9. Revenue PSF ($0.00)
10. Rank (Revenue ranking)

Conditional Formatting:
- Occupancy: Green >90%, Yellow 80-90%, Red <80%
- NOI Margin: Green >65%, Yellow 55-65%, Red <55%
- Budget Variance: Green >0%, Red <0%
Sorting: By NOI (Descending)
Totals Row: Enabled with portfolio aggregates
```

## Advanced Analytics Features

### 1. Variance Analysis
```dax
// Detailed Variance Components
Revenue Variance Detail = 
VAR ActualRev = [Total Revenue]
VAR BudgetRev = [Budget Revenue]
VAR Variance = ActualRev - BudgetRev
VAR VariancePct = DIVIDE(Variance, BudgetRev, 0) * 100
RETURN 
    "Actual: " & FORMAT(ActualRev, "$#,##0K") & 
    " | Budget: " & FORMAT(BudgetRev, "$#,##0K") & 
    " | Variance: " & FORMAT(Variance, "$#,##0K") & 
    " (" & FORMAT(VariancePct, "+0.0%;-0.0%") & ")"

// Expense Variance by Category
Expense Variance Analysis = 
CONCATENATEX(
    ADDCOLUMNS(
        VALUES(dim_account[account description]),
        "ActualExp", [Operating Expenses],
        "BudgetExp", [Budget Expense],
        "Variance", [Operating Expenses] - [Budget Expense]
    ),
    dim_account[account description] & ": " & FORMAT([Variance], "+$#,##0;-$#,##0"),
    "; "
)
```

### 2. Predictive Analytics
```dax
// Revenue Forecast (Simple Linear Trend)
Revenue Forecast = 
VAR CurrentDate = CALCULATE(
    MAX(dim_lastclosedperiod[last closed period]),
    ALL(dim_lastclosedperiod)
)
VAR HistoricalRevenue = 
    CALCULATETABLE(
        VALUES(dim_date[date]),
        dim_date[date] >= EDATE(CurrentDate, -12),
        dim_date[date] <= CurrentDate
    )
VAR TrendSlope = 
    // Calculate trend using statistical functions
    LINEST([Total Revenue], MONTH(dim_date[date]))
VAR ForecastMonths = DATEDIFF(CurrentDate, MAX(dim_date[date]), MONTH)
RETURN [Total Revenue] + (TrendSlope * ForecastMonths)

// NOI Projection
NOI Projection 12M = 
VAR CurrentNOI = [NOI (Net Operating Income)]
VAR NOIGrowthRate = [NOI YoY Growth %] / 100
VAR ProjectedNOI = CurrentNOI * POWER(1 + NOIGrowthRate, 1)
RETURN ProjectedNOI
```

## Interactive Features

### 1. Advanced Filtering
```
Date Filter: Fiscal year, quarter, month selection
Property Filter: Multi-select with market grouping
Account Filter: Revenue/Expense category selection
Budget Comparison: Toggle actual vs budget vs variance
Comparison Period: YoY, QoQ, sequential month options
```

### 2. Drill-Through Capabilities
```
From: Any property in matrix or table
To: Property Detail Financial Analysis
Filters Passed: Property, Date Range, Account Categories
Actions Available:
- View detailed P&L
- Analyze expense trends
- Review budget vs actual by month
- Compare to peer properties
```

### 3. Export Functionality
```
Financial Summary Export: 
- Excel format with formatted P&L
- Budget variance analysis
- Property ranking tables
- Expense category breakdowns

PDF Reports:
- Executive summary format
- Monthly financial package
- Budget variance reporting
- Property performance scorecards
```

## Performance Optimization

### 1. Calculation Optimization
```dax
// Use summary tables for complex aggregations
Financial Summary = 
SUMMARIZECOLUMNS(
    dim_property[property name],
    dim_date[Year Month],
    "Revenue", [Total Revenue],
    "Expenses", [Operating Expenses],
    "NOI", [NOI (Net Operating Income)],
    "Budget Revenue", [Budget Revenue],
    "Budget Expenses", [Budget Expense]
)
```

### 2. Visual Performance
```
Matrix Limits: Top 20 properties by default
Table Pagination: 25 rows per page
Chart Data Points: Maximum 24 months
Conditional Formatting: Limited to essential metrics
```

## Implementation Checklist

### Data Preparation
- [ ] Budget data imported and validated
- [ ] Account categorization verified
- [ ] FPR book data (Book 46) available
- [ ] Historical data for trend analysis (24+ months)

### Visual Development
- [ ] KPI cards with conditional formatting
- [ ] Revenue vs budget combo chart
- [ ] NOI waterfall analysis
- [ ] Property P&L matrix
- [ ] Expense breakdown treemap/pie
- [ ] Financial summary table

### Advanced Features
- [ ] Variance analysis calculations
- [ ] Predictive analytics measures
- [ ] Drill-through to property details
- [ ] Export functionality tested
- [ ] Performance optimization applied

### User Experience
- [ ] Responsive design for tablet/mobile
- [ ] Intuitive navigation and filtering
- [ ] Help tooltips for complex metrics
- [ ] Loading performance under 10 seconds
- [ ] User training materials prepared

This Financial Performance Dashboard provides comprehensive financial analysis capabilities while maintaining strong performance and user experience.