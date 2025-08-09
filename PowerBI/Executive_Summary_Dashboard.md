# Executive Summary Dashboard

## Overview

The Executive Summary Dashboard provides high-level KPIs and trends for senior management and executives. This dashboard focuses on portfolio-wide performance metrics with drill-down capabilities for detailed analysis.

## Dashboard Specifications

### Page Layout (1920x1080 optimized)

```
┌─────────────────────────────────────────────────────────────┐
│                  EXECUTIVE SUMMARY                          │
│                   Portfolio Overview                        │
└─────────────────────────────────────────────────────────────┘

┌─────────────┬─────────────┬─────────────┬─────────────┬─────┐
│ Total SF    │ Occupancy % │ Monthly Rent│ NOI Margin  │ Mkt │
│ 15.2M SF    │   92.3%     │  $12.5M    │   67.2%     │Pos  │
│ +2.1% YoY   │ +1.8 pts    │ +5.2% YoY  │ +2.1 pts   │ 78  │
└─────────────┴─────────────┴─────────────┴─────────────┴─────┘

┌─────────────┬─────────────┬─────────────┬─────────────┬─────┐
│ Investment  │ Market Risk │ Portfolio   │ Rent Gap    │ Cyc │
│ Timing      │ Score       │ Health      │ Analysis    │ Pos │
│ Score: 68   │   35        │ Score: 82   │ -$2.15/SF   │Grth │
│ Hold        │ Low Risk    │ Excellent   │ Below Mkt   │     │
└─────────────┴─────────────┴─────────────┴─────────────┴─────┘

┌─────────────────────────┬───────────────────────────────────┐
│    Occupancy Trend      │        Revenue Trend              │
│    (24 Months)          │        (24 Months)                │
│    [Line Chart]         │        [Column + Line]            │
└─────────────────────────┴───────────────────────────────────┘

┌─────────────────────────┬───────────────────────────────────┐
│  Top 10 Properties      │      Property Performance        │
│  by Revenue             │      Heat Map                     │
│  [Table]                │      [Matrix Visual]              │
└─────────────────────────┴───────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   Key Alerts & Issues                       │
│ • 3 properties below 80% occupancy                         │
│ • $2.1M in leases expiring next 6 months                   │
│ • 2 properties with NOI margin below 50%                    │
└─────────────────────────────────────────────────────────────┘
```

## Visual Components

### 1. KPI Cards (Top Row)

#### Total Rentable SF Card
```dax
// Primary Measure
Total Rentable SF = [Total Rentable Area]

// Supporting Measures
Total SF YoY Change = 
VAR CurrentSF = [Total Rentable Area]
VAR PriorYearSF = 
    CALCULATE(
        [Total Rentable Area],
        SAMEPERIODLASTYEAR(dim_date[date])
    )
RETURN DIVIDE(CurrentSF - PriorYearSF, PriorYearSF, 0) * 100

// Card Configuration
Visual Type: Card
Format: 15.2M SF
Trend Indicator: YoY Change % with arrow
Color: Blue (#1F4E79)
Font: Segoe UI, Bold, 28pt
```

#### Physical Occupancy Card
```dax
// Primary Measure
Physical Occupancy % = [Physical Occupancy %]

// Supporting Measures  
Occupancy YoY Change = [Occupancy YoY Change]

// Card Configuration
Visual Type: Card
Format: 92.3%
Trend Indicator: Percentage points change with arrow
Conditional Formatting:
- Green: >90%
- Yellow: 80-90%
- Red: <80%
Font: Segoe UI, Bold, 28pt
```

#### Current Monthly Rent Card
```dax
// Primary Measure
Current Monthly Rent = [Current Monthly Rent]

// Supporting Measures
Monthly Rent YoY Growth % = 
VAR CurrentRent = [Current Monthly Rent]
VAR PriorYearRent = 
    CALCULATE(
        [Current Monthly Rent],
        SAMEPERIODLASTYEAR(dim_date[date])
    )
RETURN DIVIDE(CurrentRent - PriorYearRent, PriorYearRent, 0) * 100

// Card Configuration
Visual Type: Card
Format: $12.5M
Trend Indicator: YoY Growth % with arrow
Color: Green (#70AD47) if positive, Red (#C5504B) if negative
Font: Segoe UI, Bold, 28pt
```

#### NOI Margin Card
```dax
// Primary Measure
NOI Margin % = [NOI Margin %]

// Supporting Measures
NOI Margin YoY Change = 
VAR CurrentMargin = [NOI Margin %]
VAR PriorYearMargin = 
    CALCULATE(
        [NOI Margin %],
        SAMEPERIODLASTYEAR(dim_date[date])
    )
RETURN CurrentMargin - PriorYearMargin

// Card Configuration
Visual Type: Card
Format: 67.2%
Trend Indicator: Percentage points change
Conditional Formatting:
- Green: >60%
- Yellow: 50-60%
- Red: <50%
Font: Segoe UI, Bold, 28pt
```

#### Market Position Card
```dax
// Primary Measure
Market Position Score = [Competitive Position Score]

// Supporting Measures
Market Position Rating = 
SWITCH(
    TRUE(),
    [Competitive Position Score] > 75, "Excellent",
    [Competitive Position Score] > 60, "Above Market",
    [Competitive Position Score] > 45, "Market Level",
    "Below Market"
)

Position vs Peers = 
VAR PortfolioScore = [Competitive Position Score]
VAR PeerAverage = 65 // Industry benchmark
RETURN PortfolioScore - PeerAverage

// Card Configuration
Visual Type: Card
Format: 78
Trend Indicator: Position rating
Secondary: vs peers comparison
Conditional Formatting:
- Green: Score >70
- Yellow: Score 50-70
- Red: Score <50
Color: Blue (#1F4E79)
```

### 2. Strategic Intelligence KPI Cards (Second Row)

#### Investment Timing Card
```dax
// Primary Measure
Investment Timing Score = [Investment Timing Score]

// Supporting Measures
Investment Recommendation = [Investment Recommendation]

Timing Confidence = 
VAR Score = [Investment Timing Score]
VAR RiskScore = [Market Risk Score]
RETURN
    SWITCH(
        TRUE(),
        Score > 80 && RiskScore < 40, "High",
        Score > 60 && RiskScore < 60, "Medium",
        Score > 40, "Low",
        "Avoid"
    )

// Card Configuration
Visual Type: Card
Format: 68
Primary Trend: Investment recommendation
Secondary: Timing confidence level
Conditional Formatting:
- Green: Strong Buy/Buy (Score >70)
- Yellow: Hold (Score 40-70)
- Red: Sell/Strong Sell (Score <40)
Color: Purple (#7030A0)
```

#### Market Risk Card
```dax
// Primary Measure
Market Risk Score = [Market Risk Score]

// Supporting Measures
Risk Level Assessment = 
SWITCH(
    TRUE(),
    [Market Risk Score] < 30, "Low Risk",
    [Market Risk Score] < 50, "Moderate Risk",
    [Market Risk Score] < 70, "High Risk",
    "Critical Risk"
)

Risk Trend = 
VAR CurrentRisk = [Market Risk Score]
VAR PriorRisk = 
    CALCULATE([Market Risk Score], DATEADD(dim_date[date], -3, MONTH))
RETURN
    IF(CurrentRisk > PriorRisk + 5, "↗ Increasing",
       IF(CurrentRisk < PriorRisk - 5, "↘ Decreasing", "→ Stable"))

// Card Configuration
Visual Type: Card
Format: 35
Primary Trend: Risk level assessment
Secondary: Risk trend indicator
Conditional Formatting:
- Green: Low risk (<30)
- Yellow: Moderate risk (30-50)
- Orange: High risk (50-70)
- Red: Critical risk (>70)
```

#### Portfolio Health Card
```dax
// Primary Measure
Portfolio Health Score = [Portfolio Health Score]

// Supporting Measures
Health Rating = 
SWITCH(
    TRUE(),
    [Portfolio Health Score] > 80, "Excellent",
    [Portfolio Health Score] > 65, "Good",
    [Portfolio Health Score] > 50, "Fair",
    "Needs Attention"
)

Health Components = 
VAR OccHealth = IF([Physical Occupancy %] >= 90, "✓", "×")
VAR NOIHealth = IF([NOI Margin %] >= 60, "✓", "×")
VAR RetHealth = IF([Retention Rate %] >= 75, "✓", "×")
RETURN "Occ:" & OccHealth & " NOI:" & NOIHealth & " Ret:" & RetHealth

// Card Configuration
Visual Type: Card
Format: 82
Primary Trend: Health rating
Secondary: Component indicators
Conditional Formatting:
- Green: Score >75 (Excellent/Good)
- Yellow: Score 50-75 (Fair)
- Red: Score <50 (Needs Attention)
```

#### Rent Gap Analysis Card
```dax
// Primary Measure
Rent Gap Analysis = [Market Rent Gap PSF]

// Supporting Measures
Gap Opportunity = 
VAR GapPSF = [Market Rent Gap PSF]
VAR LeasedSF = [Current Leased SF]
VAR AnnualOpportunity = ABS(GapPSF) * LeasedSF
RETURN 
    IF(GapPSF < 0, 
        "Opportunity: " & FORMAT(AnnualOpportunity, "$#,##0K"), 
        "Premium: " & FORMAT(AnnualOpportunity, "$#,##0K")
    )

Gap vs Market = 
SWITCH(
    TRUE(),
    [Market Rent Gap PSF] > 2, "Above Market",
    [Market Rent Gap PSF] > -2, "At Market", 
    "Below Market"
)

// Card Configuration
Visual Type: Card
Format: -$2.15/SF
Primary Trend: Gap vs market assessment
Secondary: Opportunity/premium value
Conditional Formatting:
- Green: Positive gap (above market)
- Yellow: Small gap (±$2/SF)
- Red: Large negative gap (>$2 below)
```

#### Market Cycle Position Card
```dax
// Primary Measure
Market Cycle Position = [Market Cycle Position]

// Supporting Measures
Cycle Stage Description = 
VAR Position = [Market Cycle Position]
RETURN
SWITCH(
    Position,
    "Trough", "Bottom - Opportunity",
    "Growth", "Rising - Good Timing",
    "Expansion", "Strong - Hold",
    "Peak", "Top - Caution",
    "Contraction", "Declining - Defensive",
    "Mixed"
)

Cycle Momentum = 
VAR OccTrend = [Physical Occupancy %] - 
    CALCULATE([Physical Occupancy %], DATEADD(dim_date[date], -6, MONTH))
VAR RentTrend = [Average Rent PSF] - 
    CALCULATE([Average Rent PSF], DATEADD(dim_date[date], -6, MONTH))
RETURN
    IF(OccTrend > 0 && RentTrend > 0, "Accelerating",
       IF(OccTrend < 0 && RentTrend < 0, "Decelerating", "Mixed"))

// Card Configuration
Visual Type: Card
Format: Growth
Primary Trend: Cycle stage description
Secondary: Momentum indicator
Conditional Formatting:
- Green: Trough/Growth (opportunity)
- Yellow: Expansion (hold)
- Red: Peak/Contraction (caution)
Color: Orange (#FFC000)
```

### 2. Trend Analysis Charts

#### Occupancy Trend Chart
```dax
// Measures for Chart
Physical Occupancy % = [Physical Occupancy %]
Economic Occupancy % = [Economic Occupancy %]
Target Occupancy = 95 // Static line

// Chart Configuration
Visual Type: Line Chart
X-Axis: dim_date[date] (Month hierarchy)
Y-Axis: Occupancy measures
Date Range: Last 24 months
Colors: 
- Physical: Blue (#5B9BD5)
- Economic: Orange (#FFC000)
- Target: Red dashed line
Y-Axis Range: 70% - 100%
Data Labels: Enabled for latest 3 months
```

#### Revenue Trend Chart
```dax
// Measures for Chart
Total Revenue = [Total Revenue]
Operating Expenses = [Operating Expenses] 
NOI = [NOI (Net Operating Income)]
Revenue Budget = [Revenue Budget] // If budget data available

// Chart Configuration
Visual Type: Combo Chart (Column + Line)
X-Axis: dim_date[date] (Month hierarchy)
Y-Axis 1 (Columns): Revenue, Expenses (in thousands)
Y-Axis 2 (Line): NOI Margin %
Date Range: Last 24 months
Colors:
- Revenue: Blue (#1F4E79)
- Expenses: Red (#C5504B)
- NOI Margin: Green line (#70AD47)
Data Labels: Enabled for columns
```

### 3. Property Performance Analysis

#### Top 10 Properties Table
```dax
// Table Measures
Property Rank = [Property Performance Rank]
Monthly Revenue = [Total Revenue]
Occupancy = [Physical Occupancy %]
NOI Margin = [NOI Margin %]
Leased SF = [Current Leased SF]

// Table Configuration
Visual Type: Table
Columns:
1. Property Name (dim_property[property name])
2. Monthly Revenue (Currency format)
3. Occupancy % (Percentage format)
4. NOI Margin % (Percentage format)  
5. Leased SF (Number format with K suffix)

Sorting: By Monthly Revenue (Descending)
Row Limit: Top 10
Conditional Formatting:
- Occupancy: Green >90%, Yellow 80-90%, Red <80%
- NOI Margin: Green >60%, Yellow 50-60%, Red <50%
```

#### Property Performance Heat Map
```dax
// Heat Map Measures
Property Performance Score = [Property Performance Score]
Occupancy Performance = 
    SWITCH(
        TRUE(),
        [Physical Occupancy %] >= 95, "Excellent",
        [Physical Occupancy %] >= 90, "Good",
        [Physical Occupancy %] >= 80, "Fair",
        "Needs Attention"
    )

Revenue Performance = 
    VAR RevenuePSF = [Revenue PSF]
    VAR PortfolioAvgPSF = 
        CALCULATE(
            [Revenue PSF],
            REMOVEFILTERS(dim_property)
        )
    RETURN
        SWITCH(
            TRUE(),
            RevenuePSF >= PortfolioAvgPSF * 1.1, "Above Average",
            RevenuePSF >= PortfolioAvgPSF * 0.9, "Average",
            "Below Average"
        )

// Heat Map Configuration
Visual Type: Matrix
Rows: dim_property[property name]
Columns: Performance Categories
Values: Property Performance Score
Conditional Formatting:
- Green: Score >80
- Yellow: Score 60-80
- Red: Score <60
Cell Size: Auto-fit
```

### 4. Key Alerts Section

#### Alert Generation Logic
```dax
// Low Occupancy Alert
Low Occupancy Properties = 
CONCATENATEX(
    FILTER(
        ADDCOLUMNS(
            VALUES(dim_property[property name]),
            "Occupancy", [Physical Occupancy %]
        ),
        [Occupancy] < 80
    ),
    dim_property[property name] & " (" & FORMAT([Occupancy], "0.0%") & ")",
    ", "
)

// Expiring Leases Alert
Expiring Leases Next 6M = 
VAR ExpiringRent = [Expiring Lease SF (Next 6 Months)] * [Average Rent PSF] / 12
RETURN 
    IF(
        ExpiringRent > 1000000,
        FORMAT(ExpiringRent, "$#,##0.0M") & " in leases expiring next 6 months",
        BLANK()
    )

// Low NOI Margin Alert
Low NOI Properties = 
CONCATENATEX(
    FILTER(
        ADDCOLUMNS(
            VALUES(dim_property[property name]),
            "NOIMargin", [NOI Margin %]
        ),
        [NOIMargin] < 50
    ),
    dim_property[property name] & " (" & FORMAT([NOIMargin], "0.0%") & ")",
    ", "
)

// Combined Alert Display
Key Alerts = 
VAR LowOccAlert = [Low Occupancy Properties]
VAR ExpiringAlert = [Expiring Leases Next 6M]
VAR LowNOIAlert = [Low NOI Properties]
VAR AlertList = 
    IF(NOT ISBLANK(LowOccAlert), "• " & COUNTROWS(FILTER(...)) & " properties below 80% occupancy" & UNICHAR(10), "") &
    IF(NOT ISBLANK(ExpiringAlert), "• " & ExpiringAlert & UNICHAR(10), "") &
    IF(NOT ISBLANK(LowNOIAlert), "• " & COUNTROWS(FILTER(...)) & " properties with NOI margin below 50%" & UNICHAR(10), "")
RETURN 
    IF(AlertList = "", "✅ No critical alerts", AlertList)
```

## Interactive Features

### 1. Date Filtering
```
Filter Type: Date Slicer (Between style)
Default Selection: Current Month
Quick Selections: MTD, QTD, YTD, Last Month, Last Quarter
Position: Top right corner
Style: Dropdown with calendar
```

### 2. Property Filtering
```
Filter Type: Multi-select dropdown
Default: All properties selected
Hierarchy: Market → Property (if multiple markets)
Position: Top left corner
Style: Search-enabled dropdown
```

### 3. Drill-Through Actions
```
From: Any property in table or heat map
To: Property Detail Dashboard
Filters Passed: Property, Date Range
Button: "View Property Details"
```

### 4. Cross-Filtering Behavior
```
KPI Cards: Filter all other visuals when clicked
Trend Charts: Cross-highlight related visuals
Property Table: Filter heat map and alerts
Heat Map: Filter property table
```

## Performance Optimization

### 1. Data Model Optimizations
```dax
// Use aggregated measures for better performance
Portfolio Summary = 
SUMMARIZECOLUMNS(
    dim_date[Year Month],
    dim_property[Market],
    "Total Revenue", [Total Revenue],
    "Total Occupancy", [Physical Occupancy %],
    "NOI Margin", [NOI Margin %]
)
```

### 2. Visual Optimizations
```
Row Limits: 
- Property table: Top 10 only
- Heat map: Current properties only
- Trend charts: Last 24 months maximum

Refresh Strategy:
- KPI cards: Real-time
- Charts: Daily refresh
- Alerts: Every 4 hours
```

## Mobile Responsiveness

### Phone Layout (414x896)
```
┌───────────────────────────┐
│    EXECUTIVE SUMMARY      │
├─────────────┬─────────────┤
│ Total SF    │ Occupancy % │
│ 15.2M       │   92.3%     │
├─────────────┼─────────────┤
│ Monthly Rent│ NOI Margin  │
│ $12.5M      │   67.2%     │
├─────────────────────────┤
│   Occupancy Trend       │
│   (12 Months)           │
│   [Simplified Chart]    │
├───────────────────────────┤
│   Top 5 Properties      │
│   [Simplified Table]    │
├───────────────────────────┤
│   Key Alerts            │
│   [Text Summary]        │
└───────────────────────────┘
```

### Tablet Layout (768x1024)
```
┌─────────────────────────────────────┐
│         EXECUTIVE SUMMARY           │
├─────────┬─────────┬─────────┬───────┤
│Total SF │Occupancy│ Monthly │ NOI   │
│15.2M SF │ 92.3%   │ $12.5M  │67.2%  │
├─────────────────┬─────────────────┤
│ Occupancy Trend │ Revenue Trend   │
│ [Chart]         │ [Chart]         │
├─────────────────┼─────────────────┤
│ Top Properties  │ Performance     │
│ [Table]         │ [Heat Map]      │
├─────────────────────────────────────┤
│         Key Alerts                  │
└─────────────────────────────────────┘
```

## Implementation Checklist

### Pre-Implementation
- [ ] Data model relationships verified
- [ ] All required measures created and tested
- [ ] Sample data available for testing
- [ ] Performance benchmarks established

### Dashboard Creation
- [ ] Page layout configured (1920x1080)
- [ ] KPI cards created with conditional formatting
- [ ] Trend charts configured with proper scales
- [ ] Property table with top 10 filter applied
- [ ] Heat map matrix created with performance scores
- [ ] Alert logic implemented and tested

### Interactive Features
- [ ] Date slicer configured with quick selections
- [ ] Property filter dropdown created
- [ ] Drill-through actions to property details
- [ ] Cross-filtering behavior verified
- [ ] Mobile layouts optimized

### Testing & Validation
- [ ] All visuals load within 10 seconds
- [ ] KPI values match validation benchmarks
- [ ] Trend analysis shows expected patterns
- [ ] Property rankings verified against source data
- [ ] Alert logic triggers appropriately
- [ ] Mobile responsiveness tested on devices

### Deployment
- [ ] Dashboard published to workspace
- [ ] User permissions configured
- [ ] Scheduled refresh enabled
- [ ] Usage metrics tracking enabled
- [ ] User training materials prepared

This Executive Summary Dashboard provides senior management with critical portfolio insights while maintaining fast performance and mobile accessibility.