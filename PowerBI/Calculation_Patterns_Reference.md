# Calculation Patterns Reference

## Overview

This document provides detailed calculation patterns converted from Tableau to Power BI DAX, organized by business function. These patterns have been validated against the original Tableau implementation and optimized for Power BI performance.

## Time Intelligence Patterns

### Last Twelve Months (LTM) Calculations

#### LTM NOI Pattern
```dax
LTM NOI = 
VAR EndDate = MAX(dim_date[date])
VAR StartDate = DATEADD(EndDate, -12, MONTH) + 1
RETURN
CALCULATE(
    SUM(fact_total[amount]),
    DATESBETWEEN(dim_date[date], StartDate, EndDate),
    dim_account[account code] >= 40000000,
    dim_account[account code] < 50000000,
    fact_total[amount type] = "Actual"
) - 
CALCULATE(
    ABS(SUM(fact_total[amount])),
    DATESBETWEEN(dim_date[date], StartDate, EndDate),
    dim_account[account code] >= 50000000,
    dim_account[account code] < 60000000,
    fact_total[amount type] = "Actual"
)
```

#### LTM Gross Rental Income
```dax
LTM Gross Rental Income = 
VAR EndDate = MAX(dim_date[date])
VAR StartDate = DATEADD(EndDate, -12, MONTH) + 1
RETURN
CALCULATE(
    SUM(fact_total[amount]) * -1,
    DATESBETWEEN(dim_date[date], StartDate, EndDate),
    dim_account[account code] >= 40000000,
    dim_account[account code] < 50000000,
    fact_total[amount type] = "Actual"
)
```

#### LTM CAPEX
```dax
LTM CAPEX = 
VAR EndDate = MAX(dim_date[date])
VAR StartDate = DATEADD(EndDate, -12, MONTH) + 1
RETURN
CALCULATE(
    SUM(fact_total[amount]),
    DATESBETWEEN(dim_date[date], StartDate, EndDate),
    dim_account[account code] IN {16005310, 16005450, 16005340, 16005360},
    fact_total[amount type] = "Actual",
    dim_book[book] = "Accrual"
)
```

### Current Quarter Calculations

#### Current QTR NOI
```dax
Current QTR NOI = 
VAR QtrStart = STARTOFQUARTER(MAX(dim_date[date]))
VAR QtrEnd = ENDOFQUARTER(MAX(dim_date[date]))
RETURN
CALCULATE(
    [Total Revenue] - [Operating Expenses],
    DATESBETWEEN(dim_date[date], QtrStart, QtrEnd),
    fact_total[amount type] = "Actual"
)
```

#### Annualized Current QTR NOI
```dax
Annualized Current QTR NOI = 
VAR AcqDate = CALCULATE(MIN(dim_fp_buildingcustomdata[acq. date]))
VAR QtrStart = STARTOFQUARTER(MAX(dim_date[date]))
VAR QtrEnd = ENDOFQUARTER(MAX(dim_date[date]))
VAR CurrentQtrNOI = [Current QTR NOI]
VAR DaysInQuarter = DATEDIFF(QtrStart, QtrEnd, DAY) + 1
VAR PossessionDays = 
    IF(
        AcqDate <= QtrStart,
        DaysInQuarter,
        DATEDIFF(AcqDate, QtrEnd, DAY) + 1
    )
RETURN
IF(
    AcqDate <= QtrStart,
    CurrentQtrNOI * 4,
    (CurrentQtrNOI / PossessionDays * DaysInQuarter) * 4
)
```

### Year-to-Date Calculations

#### YTD Revenue
```dax
YTD Revenue = 
CALCULATE(
    [Total Revenue],
    DATESYTD(dim_date[date])
)
```

#### YTD vs Prior YTD
```dax
YTD vs Prior YTD % = 
VAR CurrentYTD = [YTD Revenue]
VAR PriorYTD = CALCULATE([YTD Revenue], SAMEPERIODLASTYEAR(dim_date[date]))
RETURN
DIVIDE(CurrentYTD - PriorYTD, PriorYTD, 0) * 100
```

## Property-Level Calculations

### Tenant Count Patterns

#### Active Tenant Count
```dax
Active Tenant Count = 
VAR ReportDate = MAX(dim_date[date])
RETURN
CALCULATE(
    DISTINCTCOUNT(dim_commcustomer[customer id]),
    FILTER(
        dim_commcustomer,
        dim_commcustomer[lease from] <= ReportDate &&
        dim_commcustomer[lease to] >= ReportDate &&
        dim_commcustomer[is current] = TRUE() &&
        NOT(ISBLANK(dim_commcustomer[customer id]))
    )
) +
CALCULATE(
    DISTINCTCOUNT(dim_commcustomer[tenant id]),
    FILTER(
        dim_commcustomer,
        dim_commcustomer[lease from] <= ReportDate &&
        dim_commcustomer[lease to] >= ReportDate &&
        dim_commcustomer[is current] = TRUE() &&
        ISBLANK(dim_commcustomer[customer id]) &&
        NOT(ISBLANK(dim_commcustomer[tenant id]))
    )
)
```

#### Number of Buildings (Adjusted)
```dax
Number of Buildings Adjusted = 
VAR PropertyType = SELECTEDVALUE(dim_fp_buildingcustomdata[sector - property type detail])
VAR BuildingCount = 
    CALCULATE(
        DISTINCTCOUNT(dim_fp_buildingcustomdata[building id])
    )
RETURN
IF(
    PropertyType = "Land Parcel",
    0,
    BuildingCount
)
```

### Occupancy Calculations

#### Acquisition Occupancy
```dax
Acquisition Occupancy = 
VAR AcqDate = CALCULATE(MIN(dim_fp_buildingcustomdata[acq. date]))
VAR AcqMonthEnd = EOMONTH(AcqDate, 0)
RETURN
CALCULATE(
    DIVIDE(
        SUM(fact_occupancyrentarea[occupied area]),
        SUM(fact_occupancyrentarea[rentable area]),
        0
    ),
    dim_date[date] = AcqMonthEnd
)
```

#### Current Occupancy
```dax
Current Occupancy = 
VAR ReportDate = MAX(dim_date[date])
RETURN
CALCULATE(
    DIVIDE(
        SUM(fact_occupancyrentarea[occupied area]),
        SUM(fact_occupancyrentarea[rentable area]),
        0
    ),
    dim_date[date] = EOMONTH(ReportDate, 0)
)
```

### Weighted Average Calculations

#### Current WA Base Rent
```dax
Current WA Base Rent = 
VAR ReportDate = MAX(dim_date[date])
RETURN
CALCULATE(
    DIVIDE(
        SUM(fact_occupancyrentarea[total rent]),
        SUM(fact_occupancyrentarea[rentable area]),
        0
    ) * 12,
    dim_date[date] = EOMONTH(ReportDate, 0)
)
```

#### WA Base Rent at Acquisition
```dax
WA Base Rent at Acquisition = 
VAR AcqDate = CALCULATE(MIN(dim_fp_buildingcustomdata[acq. date]))
VAR AcqMonthEnd = EOMONTH(AcqDate, 0)
VAR BaseRent = 
    CALCULATE(
        DIVIDE(
            SUM(fact_occupancyrentarea[total rent]),
            SUM(fact_occupancyrentarea[rentable area]),
            0
        ) * 12,
        dim_date[date] = AcqMonthEnd
    )
RETURN
IF(BaseRent < 0, 0, BaseRent)
```

## CAPEX and Investment Calculations

### Total CAPEX Components

#### Total Tenant Improvements
```dax
Total TI = 
VAR AcqDate = CALCULATE(MIN(dim_fp_buildingcustomdata[acq. date]))
VAR ReportDate = MAX(dim_date[date])
VAR ExitDate = 
    IF(
        SELECTEDVALUE(dim_fp_buildingcustomdata[status]) = "Sold",
        CALCULATE(MAX(dim_fp_buildingcustomdata[disposition date])),
        CALCULATE(MAX(predicted_exit_override[projected exit date]))
    )
VAR ActualTI = 
    CALCULATE(
        SUM(fact_total[amount]),
        dim_account[account code] = 16005310,
        fact_total[amount type] = "Actual",
        dim_book[book] = "Accrual",
        DATESBETWEEN(dim_date[date], AcqDate, ReportDate)
    )
VAR ForecastedTI = 
    CALCULATE(
        SUM(fact_total[amount]),
        dim_account[account code] = 16005310,
        fact_total[amount type] = "Actual",
        dim_book[book] IN {"BA-2024", "Budget-Accrual"},
        DATESBETWEEN(dim_date[date], ReportDate + 1, ExitDate)
    )
RETURN
ActualTI + ForecastedTI
```

#### Total Leasing Commissions
```dax
Total LC = 
VAR AcqDate = CALCULATE(MIN(dim_fp_buildingcustomdata[acq. date]))
VAR ReportDate = MAX(dim_date[date])
VAR ExitDate = 
    IF(
        SELECTEDVALUE(dim_fp_buildingcustomdata[status]) = "Sold",
        CALCULATE(MAX(dim_fp_buildingcustomdata[disposition date])),
        CALCULATE(MAX(predicted_exit_override[projected exit date]))
    )
VAR ActualLC = 
    CALCULATE(
        SUM(fact_total[amount]),
        dim_account[account code] = 16005450,
        fact_total[amount type] = "Actual",
        dim_book[book] = "Accrual",
        DATESBETWEEN(dim_date[date], AcqDate, ReportDate)
    )
VAR ForecastedLC = 
    CALCULATE(
        SUM(fact_total[amount]),
        dim_account[account code] = 16005450,
        fact_total[amount type] = "Actual",
        dim_book[book] IN {"BA-2024", "Budget-Accrual"},
        DATESBETWEEN(dim_date[date], ReportDate + 1, ExitDate)
    )
RETURN
ActualLC + ForecastedLC
```

#### Total Capital Expenses
```dax
Total CapEx = 
VAR AcqDate = CALCULATE(MIN(dim_fp_buildingcustomdata[acq. date]))
VAR ReportDate = MAX(dim_date[date])
VAR ExitDate = 
    IF(
        SELECTEDVALUE(dim_fp_buildingcustomdata[status]) = "Sold",
        CALCULATE(MAX(dim_fp_buildingcustomdata[disposition date])),
        CALCULATE(MAX(predicted_exit_override[projected exit date]))
    )
VAR ActualCapEx = 
    CALCULATE(
        SUM(fact_total[amount]),
        dim_account[account code] IN {16005340, 16005360},
        fact_total[amount type] = "Actual",
        dim_book[book] = "Accrual",
        DATESBETWEEN(dim_date[date], AcqDate, ReportDate)
    )
VAR ForecastedCapEx = 
    CALCULATE(
        SUM(fact_total[amount]),
        dim_account[account code] IN {16005340, 16005360},
        fact_total[amount type] = "Actual",
        dim_book[book] IN {"BA-2024", "Budget-Accrual"},
        DATESBETWEEN(dim_date[date], ReportDate + 1, ExitDate)
    )
RETURN
ActualCapEx + ForecastedCapEx
```

### Investment Metrics

#### Purchase Price (Flexible)
```dax
Purchase Price CF = 
VAR OverridePrice = CALCULATE(MAX(acq_costs_override[purchase price]))
VAR GLPrice = 
    CALCULATE(
        SUM(fact_total[amount]),
        dim_account[account code] IN {16005150, 16005200},
        fact_total[amount type] = "Cumulative Actual",
        dim_book[book] = "Accrual"
    )
VAR Status = SELECTEDVALUE(dim_fp_buildingcustomdata[status])
VAR DispositionDate = CALCULATE(MAX(dim_fp_buildingcustomdata[disposition date]))
VAR DispositionPrice = 
    IF(
        Status = "Sold",
        CALCULATE(
            SUM(fact_total[amount]),
            dim_account[account code] IN {16005150, 16005200},
            fact_total[amount type] = "Cumulative Actual",
            dim_book[book] = "Accrual",
            dim_date[date] >= DATEADD(DispositionDate, -2, MONTH),
            dim_date[date] < DispositionDate
        ),
        BLANK()
    )
RETURN
COALESCE(OverridePrice, DispositionPrice, GLPrice)
```

#### Total Acquisition Cost
```dax
Total Acquisition Cost CF = 
VAR OverrideCost = CALCULATE(MAX(acq_costs_override[total acq. cost]))
VAR GLCost = 
    CALCULATE(
        SUM(fact_total[amount]),
        dim_account[account code] IN {16005150, 16005200, 16005250, 16005260},
        fact_total[amount type] = "Cumulative Actual",
        dim_book[book] = "Accrual"
    )
RETURN
COALESCE(OverrideCost, GLCost)
```

#### Acquisition In Place NOI
```dax
Acquisition In Place NOI CF = 
VAR BusinessPlanOverride = CALCULATE(MAX(business_plan_book_override[acquisition in place noi]))
VAR AcqDate = CALCULATE(MIN(dim_fp_buildingcustomdata[acq. date]))
VAR FirstFullMonth = EOMONTH(AcqDate, 1)
VAR FirstMonthNOI = 
    CALCULATE(
        [NOI (Net Operating Income)],
        dim_date[date] = FirstFullMonth,
        dim_book[book] CONTAINSSTRING "Business Plan"
    )
RETURN
IF(
    NOT(ISBLANK(BusinessPlanOverride)) && BusinessPlanOverride <> 0,
    BusinessPlanOverride,
    IF(
        NOT(ISBLANK(FirstMonthNOI)),
        FirstMonthNOI * 12,
        0
    )
)
```

#### Year 1 NOI
```dax
Year 1 NOI = 
VAR BusinessPlanOverride = CALCULATE(MAX(business_plan_book_override[year 1 noi]))
VAR AcqDate = CALCULATE(MIN(dim_fp_buildingcustomdata[acq. date]))
VAR Year1EndDate = DATEADD(AcqDate, 12, MONTH)
VAR CalculatedYear1NOI = 
    CALCULATE(
        [NOI (Net Operating Income)],
        DATESBETWEEN(dim_date[date], AcqDate, Year1EndDate),
        dim_book[book] CONTAINSSTRING "Business Plan"
    )
RETURN
IF(
    NOT(ISBLANK(BusinessPlanOverride)) && BusinessPlanOverride <> 0,
    BusinessPlanOverride,
    CalculatedYear1NOI
)
```

### Return Metrics

#### Acquisition Cap Rate
```dax
Acquisition Cap Rate = 
DIVIDE([Acquisition In Place NOI CF], [Purchase Price CF], 0)
```

#### Year 1 Cap Rate
```dax
Year 1 Cap Rate = 
DIVIDE([Year 1 NOI], [Purchase Price CF], 0)
```

#### Current In-Place Yield on Cost
```dax
Current In-Place YOC = 
VAR CurrentQtrNOI = [Current QTR NOI] * 4
VAR TotalCost = [Current Total Cost]
RETURN
DIVIDE(CurrentQtrNOI, TotalCost, 0)
```

## WALT (Weighted Average Lease Term) Calculation

### Current WALT
```dax
Current WALT Years = 
VAR ReportDate = MAX(dim_date[date])
VAR WALTCalc = 
    SUMX(
        FILTER(
            fact_expiringleaseunitarea,
            fact_expiringleaseunitarea[lease from date] <= ReportDate &&
            fact_expiringleaseunitarea[lease to date] > ReportDate
        ),
        fact_expiringleaseunitarea[expiring area] * 
        DIVIDE(
            DATEDIFF(ReportDate, fact_expiringleaseunitarea[lease to date], DAY),
            365,
            0
        )
    )
VAR TotalArea = 
    CALCULATE(
        SUM(fact_expiringleaseunitarea[expiring area]),
        fact_expiringleaseunitarea[lease from date] <= ReportDate,
        fact_expiringleaseunitarea[lease to date] > ReportDate
    )
RETURN
DIVIDE(WALTCalc, TotalArea, 0)
```

## Special Calculations

### FAR (Floor Area Ratio)
```dax
FAR = 
VAR TotalSF = [Size (SF)]
VAR LandAcres = CALCULATE(MAX(dim_fp_buildingcustomdata[land(acres)]))
VAR LandSF = LandAcres * 43560
RETURN
DIVIDE(TotalSF, LandSF, 0)
```

### Projected vs Actual Exit Date
```dax
Projected/Actual Exit Date = 
VAR Status = SELECTEDVALUE(dim_fp_buildingcustomdata[status])
VAR DispositionDate = CALCULATE(MAX(dim_fp_buildingcustomdata[disposition date]))
VAR ProjectedDate = CALCULATE(MAX(predicted_exit_override[projected exit date]))
RETURN
IF(
    Status = "Sold",
    DispositionDate,
    ProjectedDate
)
```

### Fund Name Derivation
```dax
Fund Name = 
VAR StandardizedName = CALCULATE(MAX(predicted_exit_override[fund standardized name]))
VAR Vehicle = SELECTEDVALUE(dim_property[vehicle])
RETURN
IF(
    ISBLANK(StandardizedName),
    Vehicle,
    StandardizedName
)
```

### Asset Investment Style
```dax
Asset Investment Style = 
VAR Vehicle = SELECTEDVALUE(dim_property[vehicle])
RETURN
SWITCH(
    TRUE(),
    Vehicle = "ISLB", "Core",
    Vehicle IN {"FRG IX", "FRG X", "FUND 3 (FRG XI)"}, "Value-Add",
    "Other"
)
```

## Performance Optimization Notes

### Variable Usage
- Always use variables for complex calculations to avoid recalculation
- Store date ranges in variables for time intelligence
- Cache SELECTEDVALUE results when used multiple times

### Filter Context
- Apply most restrictive filters first
- Use CALCULATETABLE for complex filter combinations
- Avoid using ALL() unless necessary

### Time Intelligence
- Ensure dim_date is marked as Date table
- Use built-in time intelligence functions where possible
- Pre-calculate period boundaries in variables

### Aggregation Strategy
- Create summary tables for frequently accessed aggregations
- Use SUMMARIZECOLUMNS for complex grouping operations
- Consider incremental refresh for large fact tables