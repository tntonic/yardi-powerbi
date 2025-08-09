# Rent Roll Dashboard

## Overview

The Rent Roll Dashboard provides comprehensive rent roll analysis with current and future rent projections, lease expiration schedules, and tenant analysis. This dashboard replicates and enhances native Yardi rent roll functionality with real-time data and advanced analytics.

## Dashboard Specifications

### Page Layout (1920x1080 optimized)

```
┌─────────────────────────────────────────────────────────────┐
│                      RENT ROLL                              │
│               Current & Future Analysis                     │
└─────────────────────────────────────────────────────────────┘

┌─────────────┬─────────────┬─────────────┬─────────────┬─────┐
│ Current     │ Leased SF   │ Avg Rent   │ Total       │WALT │
│ Monthly     │             │    PSF      │ Tenants     │     │
│ $12.5M      │   8.4M SF   │  $28.50    │    247      │2.8Y │
│ +3.2% YoY   │ +156K SF    │ +$1.20 YoY │    +8       │     │
└─────────────┴─────────────┴─────────────┴─────────────┴─────┘

┌─────────────────────────┬───────────────────────────────────┐
│   Current Rent Roll     │      Lease Expiration            │
│   by Property           │      Waterfall (Next 24M)        │
│   [Table/Matrix]        │      [Waterfall Chart]           │
└─────────────────────────┴───────────────────────────────────┘

┌─────────────────────────┬───────────────────────────────────┐
│   Rent Analysis         │      Future Rent Roll            │
│   by Tenant Size        │      Projections                 │
│   [Scatter Plot]        │      [Line Chart]                │
└─────────────────────────┴───────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    Detailed Rent Roll                      │
│Property│Tenant │Unit │SF   │Start│End  │Rent PSF│Monthly │
│Prop A  │ABC Co │100A │5.2K │1/20 │12/25│ $32.50 │$14.1K  │
│Prop A  │XYZ Ltd│200B │8.7K │3/21 │2/26 │ $28.90 │$20.9K  │
└─────────────────────────────────────────────────────────────┘
```

## Visual Components

### 1. Rent Roll KPI Cards (Top Row)

#### Current Monthly Rent Card
```dax
// Primary Measure (From validated rent roll implementation)
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

Monthly Rent QoQ Growth % = 
VAR CurrentRent = [Current Monthly Rent]
VAR PriorQuarterRent = 
    CALCULATE(
        [Current Monthly Rent],
        DATEADD(dim_date[date], -1, QUARTER)
    )
RETURN DIVIDE(CurrentRent - PriorQuarterRent, PriorQuarterRent, 0) * 100

// Card Configuration
Visual Type: Card
Format: $12.5M
Primary Trend: YoY Growth % with arrow
Secondary Trend: QoQ Growth %
Conditional Formatting:
- Green: Growth >3%
- Yellow: Growth 0-3%
- Red: Decline
Font: Segoe UI, Bold, 28pt
```

#### Current Leased SF Card
```dax
// Primary Measure
Current Leased SF = [Current Leased SF]

// Supporting Measures
Leased SF YoY Change = 
VAR CurrentSF = [Current Leased SF]
VAR PriorYearSF = 
    CALCULATE(
        [Current Leased SF],
        SAMEPERIODLASTYEAR(dim_date[date])
    )
RETURN CurrentSF - PriorYearSF

Leased SF Growth % = 
    DIVIDE([Leased SF YoY Change], [Current Leased SF] - [Leased SF YoY Change], 0) * 100

// Card Configuration
Visual Type: Card
Format: 8.4M SF (with K/M suffix)
Primary Trend: YoY Change in SF
Secondary Trend: Growth percentage
Conditional Formatting:
- Green: SF growth
- Red: SF decline
Color: Blue (#1F4E79)
```

#### Average Rent PSF Card
```dax
// Primary Measure
Current Rent Roll PSF = [Current Rent Roll PSF]

// Supporting Measures
Rent PSF YoY Change = 
VAR CurrentPSF = [Current Rent Roll PSF]
VAR PriorYearPSF = 
    CALCULATE(
        [Current Rent Roll PSF],
        SAMEPERIODLASTYEAR(dim_date[date])
    )
RETURN CurrentPSF - PriorYearPSF

Market Rate Comparison = 
VAR ActualPSF = [Current Rent Roll PSF]
VAR MarketPSF = 
    CALCULATE(
        AVERAGE(fact_fp_fmvm_marketunitrates[unitmlarentnew]),
        RELATED(dim_unit[unit hmy]) = fact_fp_fmvm_marketunitrates[unit hmy]
    )
RETURN ActualPSF - MarketPSF

// Card Configuration
Visual Type: Card
Format: $28.50
Primary Trend: YoY Change in dollars
Secondary: vs Market Rate (+ above, - below)
Conditional Formatting:
- Green: Above market rate
- Yellow: At market rate
- Red: Below market rate
```

#### Total Active Tenants Card
```dax
// Primary Measure
Active Tenant Count = 
VAR CurrentDate = TODAY()
RETURN
CALCULATE(
    DISTINCTCOUNT(dim_fp_amendmentsunitspropertytenant[tenant hmy]),
    FILTER(
        dim_fp_amendmentsunitspropertytenant,
        dim_fp_amendmentsunitspropertytenant[amendment status] IN {"Activated", "Superseded"} &&
        dim_fp_amendmentsunitspropertytenant[amendment type] <> "Termination" &&
        dim_fp_amendmentsunitspropertytenant[amendment start date] <= CurrentDate &&
        (dim_fp_amendmentsunitspropertytenant[amendment end date] >= CurrentDate || 
         ISBLANK(dim_fp_amendmentsunitspropertytenant[amendment end date]))
    ),
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
)

// Supporting Measures
Tenant Count YoY Change = 
VAR CurrentCount = [Active Tenant Count]
VAR PriorYearCount = 
    CALCULATE(
        [Active Tenant Count],
        SAMEPERIODLASTYEAR(dim_date[date])
    )
RETURN CurrentCount - PriorYearCount

// Card Configuration
Visual Type: Card
Format: 247
Primary Trend: YoY Change with +/- indicator
Conditional Formatting:
- Green: Tenant growth
- Red: Tenant decline
Color: Orange (#FFC000)
```

#### WALT (Weighted Average Lease Term) Card
```dax
// Primary Measure
WALT Years = [WALT Years]

// Supporting Measures
WALT Change YoY = 
VAR CurrentWALT = [WALT Years]
VAR PriorYearWALT = 
    CALCULATE(
        [WALT Years],
        SAMEPERIODLASTYEAR(dim_date[date])
    )
RETURN CurrentWALT - PriorYearWALT

WALT Risk Level = 
VAR WALTYears = [WALT Years]
RETURN 
    SWITCH(
        TRUE(),
        WALTYears > 5, "Low Risk",
        WALTYears > 3, "Medium Risk",
        WALTYears > 2, "High Risk",
        "Critical"
    )

// Card Configuration
Visual Type: Card
Format: 2.8Y
Primary Trend: YoY Change in years
Secondary: Risk level indicator
Conditional Formatting:
- Green: WALT >4 years
- Yellow: WALT 2-4 years
- Red: WALT <2 years
```

### 2. Current Rent Roll by Property

#### Property Rent Roll Matrix
```dax
// Matrix Measures
Property Monthly Rent = [Current Monthly Rent]
Property Leased SF = [Current Leased SF]
Property Rent PSF = [Current Rent Roll PSF]
Property Tenant Count = [Active Tenant Count]
Property WALT = [WALT Years]
Property Occupancy = [Physical Occupancy %]

// Performance Indicators
Rent Collection % = 
VAR TotalRent = [Current Monthly Rent]
VAR CollectedRent = 
    TotalRent - CALCULATE(
        SUM(fact_accountsreceivable[amount]),
        fact_accountsreceivable[aging days] <= 30
    )
RETURN DIVIDE(CollectedRent, TotalRent, 0) * 100

Market Position = 
VAR PropertyPSF = [Current Rent Roll PSF]
VAR MarketAvgPSF = 
    CALCULATE(
        AVERAGE([Current Rent Roll PSF]),
        ALLEXCEPT(dim_property, dim_fp_buildingcustomdata[market])
    )
RETURN 
    SWITCH(
        TRUE(),
        PropertyPSF > MarketAvgPSF * 1.1, "Premium",
        PropertyPSF > MarketAvgPSF * 0.9, "Market",
        "Below Market"
    )

// Matrix Configuration
Visual Type: Matrix
Rows: dim_property[property name]
Columns: Rent roll metrics
Values:
- Monthly Rent ($M format)
- Leased SF (Number with K/M suffix)
- Rent PSF ($0.00 format)
- Tenant Count (Whole number)
- WALT (0.0Y format)
- Occupancy % (Percentage)
- Market Position (Text)

Conditional Formatting:
- Rent PSF: Color scale based on market position
- WALT: Green >3Y, Yellow 2-3Y, Red <2Y
- Occupancy: Green >90%, Yellow 80-90%, Red <80%
Subtotals: Portfolio totals enabled
Sorting: By Monthly Rent (Descending)
```

### 3. Lease Expiration Waterfall

#### Next 24 Months Expiration Analysis
```dax
// Expiration Measures by Quarter
Current Rent Base = [Current Monthly Rent]

Q1 Expirations = 
VAR CurrentDate = TODAY()
VAR Q1EndDate = EOMONTH(CurrentDate, 3)
RETURN
CALCULATE(
    SUM(dim_fp_amendmentchargeschedule[monthly amount]),
    FILTER(
        dim_fp_amendmentsunitspropertytenant,
        dim_fp_amendmentsunitspropertytenant[amendment status] IN {"Activated", "Superseded"} &&
        dim_fp_amendmentsunitspropertytenant[amendment type] <> "Termination" &&
        dim_fp_amendmentsunitspropertytenant[amendment end date] > CurrentDate &&
        dim_fp_amendmentsunitspropertytenant[amendment end date] <= Q1EndDate
    )
)

Q2 Expirations = 
VAR Q1EndDate = EOMONTH(TODAY(), 3)
VAR Q2EndDate = EOMONTH(TODAY(), 6)
RETURN
CALCULATE(
    SUM(dim_fp_amendmentchargeschedule[monthly amount]),
    FILTER(
        dim_fp_amendmentsunitspropertytenant,
        dim_fp_amendmentsunitspropertytenant[amendment status] IN {"Activated", "Superseded"} &&
        dim_fp_amendmentsunitspropertytenant[amendment type] <> "Termination" &&
        dim_fp_amendmentsunitspropertytenant[amendment end date] > Q1EndDate &&
        dim_fp_amendmentsunitspropertytenant[amendment end date] <= Q2EndDate
    )
)

// Similar measures for Q3, Q4, and beyond...

Expected Renewals = 
// Apply retention rate to expirations
VAR ExpiringRent = [Q1 Expirations] + [Q2 Expirations] // + other quarters
VAR RetentionRate = [Retention Rate %] / 100
RETURN ExpiringRent * RetentionRate

Expected New Rent = 
// Estimate new leasing to replace non-renewals
VAR NonRenewals = ([Q1 Expirations] + [Q2 Expirations]) - [Expected Renewals]
VAR NewLeasingRate = 0.75 // Assume 75% of space re-leased
RETURN NonRenewals * NewLeasingRate

Projected Rent 24M = 
[Current Rent Base] - [Q1 Expirations] - [Q2 Expirations] + 
[Expected Renewals] + [Expected New Rent]

// Waterfall Configuration
Visual Type: Waterfall Chart
Categories:
1. "Current Rent" (Starting point - Current Monthly Rent)
2. "Q1 Expirations" (Negative - Q1 Expirations)
3. "Q2 Expirations" (Negative - Q2 Expirations) 
4. "Q3 Expirations" (Negative - Q3 Expirations)
5. "Q4 Expirations" (Negative - Q4 Expirations)
6. "Expected Renewals" (Positive - Expected Renewals)
7. "New Leasing" (Positive - Expected New Rent)
8. "Projected Rent" (Ending point - Projected Rent 24M)

Colors:
- Starting/Ending: Blue (#1F4E79)
- Expirations: Red (#C5504B)
- Renewals/New: Green (#70AD47)
Data Labels: Currency format with percentages of total
```

### 4. Rent Analysis by Tenant Size

#### Rent PSF vs Square Footage Analysis
```dax
// Scatter Plot Measures (Tenant Level)
Tenant Monthly Rent = 
CALCULATE(
    SUM(dim_fp_amendmentchargeschedule[monthly amount]),
    FILTER(
        dim_fp_amendmentsunitspropertytenant,
        dim_fp_amendmentsunitspropertytenant[amendment status] IN {"Activated", "Superseded"} &&
        dim_fp_amendmentsunitspropertytenant[amendment type] <> "Termination"
    )
)

Tenant SF = 
CALCULATE(
    SUM(dim_fp_amendmentsunitspropertytenant[amendment sf]),
    FILTER(
        dim_fp_amendmentsunitspropertytenant,
        dim_fp_amendmentsunitspropertytenant[amendment status] IN {"Activated", "Superseded"} &&
        dim_fp_amendmentsunitspropertytenant[amendment type] <> "Termination"
    )
)

Tenant Rent PSF = DIVIDE([Tenant Monthly Rent] * 12, [Tenant SF], 0)

Tenant Size Category = 
VAR TenantSF = [Tenant SF]
RETURN 
    SWITCH(
        TRUE(),
        TenantSF >= 100000, "Large (100K+ SF)",
        TenantSF >= 50000, "Medium (50-100K SF)",
        TenantSF >= 25000, "Small (25-50K SF)",
        "Very Small (<25K SF)"
    )

// Scatter Plot Configuration
Visual Type: Scatter Chart
X-Axis: Tenant SF (Logarithmic scale)
Y-Axis: Tenant Rent PSF
Size: Tenant Monthly Rent
Color: Tenant Size Category
Legend: Tenant Size Category
Tooltip: Include tenant name, property, lease expiration
Trend Line: Enabled (power law curve)
```

### 5. Future Rent Roll Projections

#### Multi-Year Rent Growth Analysis
```dax
// Projection Measures
Year 1 Projected Rent = 
VAR CurrentRent = [Current Monthly Rent]
VAR MarketGrowthRate = 0.03 // 3% annual growth
VAR RetentionAssumption = [Retention Rate %] / 100
VAR RenewalGrowthRate = 0.025 // 2.5% renewal increases
RETURN CurrentRent * (1 + (MarketGrowthRate * RetentionAssumption) + (RenewalGrowthRate * (1 - RetentionAssumption)))

Year 2 Projected Rent = [Year 1 Projected Rent] * 1.03
Year 3 Projected Rent = [Year 2 Projected Rent] * 1.03
Year 4 Projected Rent = [Year 3 Projected Rent] * 1.03
Year 5 Projected Rent = [Year 4 Projected Rent] * 1.03

// Market Rate Projections (Using MRG data if available)
Market Rate Growth Factor = 
VAR PropertyMarket = RELATED(dim_fp_buildingcustomdata[market])
VAR GrowthRate = 
    SWITCH(
        PropertyMarket,
        "Northern NJ/New York", 0.035,
        "Chicago", 0.028,
        "Philadelphia", 0.025,
        0.03 // Default
    )
RETURN GrowthRate

Projected Market Rent PSF Year 1 = 
VAR CurrentMarketRate = AVERAGE(fact_fp_fmvm_marketunitrates[unitmlarentnew])
VAR GrowthFactor = [Market Rate Growth Factor]
RETURN CurrentMarketRate * (1 + GrowthFactor)

// Line Chart Configuration
Visual Type: Line Chart
X-Axis: Years (Current, Year 1, Year 2, Year 3, Year 4, Year 5)
Y-Axis: Monthly Rent ($M)
Series:
- Projected Portfolio Rent (Blue line)
- Market Rate Equivalent (Orange dashed line)
- Conservative Scenario (90% of projection, Gray line)
- Optimistic Scenario (110% of projection, Green line)

Data Labels: Enabled for latest 2 years
Markers: Enabled for all series
Y-Axis Format: Currency in millions
```

### 6. Detailed Rent Roll Table

#### Comprehensive Tenant Listing
```dax
// Table Measures (Tenant Level)
Tenant Name = RELATED(dim_commcustomer[tenant name])
Property Name = RELATED(dim_property[property name])
Unit Number = RELATED(dim_unit[unit name])
Lease SF = [Tenant SF]
Lease Start = 
CALCULATE(
    MIN(dim_fp_amendmentsunitspropertytenant[amendment start date]),
    dim_fp_amendmentsunitspropertytenant[amendment status] IN {"Activated", "Superseded"}
)
Lease End = 
CALCULATE(
    MAX(dim_fp_amendmentsunitspropertytenant[amendment end date]),
    dim_fp_amendmentsunitspropertytenant[amendment status] IN {"Activated", "Superseded"}
)
Monthly Rent = [Tenant Monthly Rent]
Annual Rent PSF = [Tenant Rent PSF]

Lease Status = 
VAR CurrentDate = TODAY()
VAR EndDate = [Lease End]
VAR MonthsToExpiry = DATEDIFF(CurrentDate, EndDate, MONTH)
RETURN 
    SWITCH(
        TRUE(),
        ISBLANK(EndDate), "Month-to-Month",
        MonthsToExpiry <= 6, "Expiring Soon",
        MonthsToExpiry <= 12, "Expiring <1Y",
        MonthsToExpiry <= 24, "Expiring 1-2Y",
        "Long Term"
    )

Industry = RELATED(dim_fp_naics[naics description])

Rent Growth Potential = 
VAR ActualPSF = [Tenant Rent PSF]
VAR MarketPSF = 
    CALCULATE(
        AVERAGE(fact_fp_fmvm_marketunitrates[unitmlarentnew]),
        RELATED(dim_unit[unit hmy]) = fact_fp_fmvm_marketunitrates[unit hmy]
    )
VAR GapPct = DIVIDE(MarketPSF - ActualPSF, ActualPSF, 0) * 100
RETURN 
    SWITCH(
        TRUE(),
        GapPct > 15, "High (>15%)",
        GapPct > 5, "Medium (5-15%)",
        GapPct > -5, "Limited (<5%)",
        "Above Market"
    )

// Table Configuration
Visual Type: Table
Columns:
1. Property Name
2. Tenant Name  
3. Unit Number
4. Lease SF (Number with K suffix)
5. Lease Start (Date format)
6. Lease End (Date format)
7. Monthly Rent (Currency)
8. Annual PSF (Currency)
9. Lease Status (Text with conditional formatting)
10. Industry (Text)
11. Growth Potential (Text with conditional formatting)

Conditional Formatting:
- Lease Status: Red for "Expiring Soon", Yellow for "Expiring <1Y"
- Growth Potential: Green for "High", Yellow for "Medium", Red for "Above Market"
- Monthly Rent: Data bars for relative comparison

Sorting: By Monthly Rent (Descending)
Filtering: Show active leases only
Pagination: 25 rows per page
Export: Enable Excel export with formatting
```

## Advanced Analytics Features

### 1. Lease Renewal Probability Modeling
```dax
// Renewal Probability Score
Tenant Renewal Probability % = 
VAR TenantQuality = [Tenant Quality Score] // From advanced calculations
VAR RentGap = [Market Rent Gap %]
VAR LeaseTermRemaining = 
    DATEDIFF(TODAY(), [Lease End], MONTH)
VAR IndustryStability = 
    SWITCH(
        [Industry],
        "Educational Services", 85,
        "Health Care and Social Assistance", 80,
        "Professional, Scientific, and Technical Services", 75,
        "Finance and Insurance", 75,
        50 // Default
    )
VAR BaseRenewalRate = 
    SWITCH(
        TRUE(),
        TenantQuality >= 80, 85,
        TenantQuality >= 60, 70,
        TenantQuality >= 40, 55,
        35
    )
VAR RentGapAdjustment = 
    SWITCH(
        TRUE(),
        RentGap > 20, -20,
        RentGap > 10, -10,
        RentGap > -10, 0,
        10
    )
RETURN MIN(95, MAX(5, BaseRenewalRate + RentGapAdjustment + IndustryStability * 0.2))
```

### 2. Portfolio Risk Analysis
```dax
// Concentration Risk Analysis
Top 10 Tenant Concentration = 
VAR TotalRent = [Current Monthly Rent]
VAR Top10Rent = 
    CALCULATE(
        [Current Monthly Rent],
        TOPN(10, VALUES(dim_commcustomer[tenant name]), [Tenant Monthly Rent])
    )
RETURN DIVIDE(Top10Rent, TotalRent, 0) * 100

Industry Concentration Risk = 
VAR TopIndustryRent = 
    CALCULATE(
        [Current Monthly Rent],
        TOPN(1, VALUES(dim_fp_naics[naics description]), [Current Monthly Rent])
    )
VAR TotalRent = [Current Monthly Rent]
RETURN DIVIDE(TopIndustryRent, TotalRent, 0) * 100

// Credit Risk Assessment
Portfolio Credit Score = 
VAR WeightedScore = 
    SUMX(
        VALUES(dim_commcustomer[tenant name]),
        [Tenant Monthly Rent] * [Tenant Quality Score]
    )
VAR TotalRent = [Current Monthly Rent]
RETURN DIVIDE(WeightedScore, TotalRent, 0)
```

## Interactive Features

### 1. Dynamic Filtering
```
Date Selection: Current, Future projections, Historical comparison
Property Filter: Multi-select with market grouping
Tenant Filter: Size categories, industries, lease status
Rent Range: PSF range sliders
Expiration Period: Next 6/12/24 months
```

### 2. Drill-Through Actions
```
From: Any tenant or property row
To: Detailed Lease Analysis Page
Filters: Tenant, Property, Lease details
Actions:
- View lease amendment history
- Analyze payment history
- Review market comparisons
- Renewal probability assessment
```

### 3. Export Capabilities
```
Rent Roll Export:
- Current rent roll in Excel format
- Lease expiration schedule
- Tenant contact information
- Market analysis summary

Management Reports:
- Executive rent roll summary
- Lease expiration report
- Renewal pipeline analysis
- Risk assessment summary
```

## Mobile Optimization

### Phone Layout (414x896)
```
┌─────────────────────────┐
│      RENT ROLL          │
├───────────┬─────────────┤
│Current    │ Leased SF   │
│$12.5M     │ 8.4M SF     │
├───────────┼─────────────┤
│Avg PSF    │ Tenants     │
│$28.50     │ 247         │
├─────────────────────────┤
│   Rent by Property      │
│   [Simplified Table]    │
├─────────────────────────┤
│   Expiring Leases       │
│   [Chart]               │
└─────────────────────────┘
```

## Implementation Checklist

### Data Requirements
- [ ] Amendment data with latest sequence logic
- [ ] Charge schedule data with effective dates
- [ ] Market rate benchmarking data
- [ ] Tenant industry classifications
- [ ] Historical rent roll for trend analysis

### Dashboard Development
- [ ] KPI cards with rent roll metrics
- [ ] Property rent roll matrix
- [ ] Lease expiration waterfall
- [ ] Tenant size analysis scatter plot
- [ ] Future rent projections
- [ ] Detailed tenant table

### Advanced Features
- [ ] Renewal probability modeling
- [ ] Portfolio risk analysis
- [ ] Market comparison analytics
- [ ] Export functionality
- [ ] Mobile responsive design

### Testing & Validation
- [ ] Rent roll accuracy vs Yardi (95%+ target)
- [ ] Amendment logic validation
- [ ] Performance optimization (<10 sec load)
- [ ] User acceptance testing
- [ ] Training materials prepared

This Rent Roll Dashboard provides comprehensive rent roll analysis with predictive capabilities while maintaining the accuracy and detail required for effective lease management and strategic planning.