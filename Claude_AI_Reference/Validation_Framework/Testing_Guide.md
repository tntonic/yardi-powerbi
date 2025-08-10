  # Validation and Testing Guide

## Overview

This guide provides comprehensive validation and testing procedures for all DAX measures in the Yardi BI solution. Following these procedures ensures 95%+ accuracy against source systems and reliable business intelligence.

## Validation Framework

### Validation Levels

#### Level 1: Syntax and Logic Validation
- **Purpose**: Ensure measures execute without errors
- **Scope**: All measures individually
- **Timeline**: During measure creation
- **Acceptance**: 100% measures execute successfully

#### Level 2: Business Logic Validation  
- **Purpose**: Verify calculations follow business rules
- **Scope**: Core business measures
- **Timeline**: After measure groups completed
- **Acceptance**: Logic matches documented business rules

#### Level 3: Data Accuracy Validation
- **Purpose**: Compare results with source systems
- **Scope**: All measures with known benchmarks
- **Timeline**: Before dashboard deployment
- **Acceptance**: 95%+ accuracy vs source systems

#### Level 4: User Acceptance Validation
- **Purpose**: Ensure measures meet business needs
- **Scope**: Key business metrics and dashboards
- **Timeline**: Pre-production deployment
- **Acceptance**: Business user sign-off

## Automated Validation Measures

### Data Quality Monitoring Dashboard

#### Create Validation Measure Group
```dax
// === VALIDATION MEASURES ===
// These measures should be created in a separate "Validation" folder

// 1. Overall Model Health Score
Model Health Score = 
VAR DataCompleteness = [Data Completeness Score]
VAR RelationshipIntegrity = [Relationship Integrity Score]
VAR MeasureAccuracy = [Measure Accuracy Score]
VAR PerformanceScore = [Performance Score]
RETURN (DataCompleteness + RelationshipIntegrity + MeasureAccuracy + PerformanceScore) / 4

// 2. Data Completeness Score
Data Completeness Score = 
VAR PropertyCompleteness = 
    DIVIDE(
        CALCULATE(
            COUNTROWS(dim_property),
            NOT(ISBLANK(dim_property[property code])),
            NOT(ISBLANK(dim_property[property name]))
        ),
        COUNTROWS(dim_property),
        0
    )
VAR FinancialCompleteness = 
    DIVIDE(
        CALCULATE(
            COUNTROWS(fact_total),
            NOT(ISBLANK(fact_total[amount])),
            NOT(ISBLANK(fact_total[month]))
        ),
        COUNTROWS(fact_total),
        0
    )
VAR AmendmentCompleteness = 
    DIVIDE(
        CALCULATE(
            COUNTROWS(dim_fp_amendmentsunitspropertytenant),
            NOT(ISBLANK(dim_fp_amendmentsunitspropertytenant[amendment start date])),
            dim_fp_amendmentsunitspropertytenant[amendment sf] > 0
        ),
        COUNTROWS(dim_fp_amendmentsunitspropertytenant),
        0
    )
RETURN (PropertyCompleteness + FinancialCompleteness + AmendmentCompleteness) / 3 * 100

// 3. Relationship Integrity Score
Relationship Integrity Score = 
VAR TotalFactRecords = COUNTROWS(fact_total)
VAR MatchedFactRecords = 
    CALCULATE(
        COUNTROWS(fact_total),
        NOT(ISBLANK(RELATED(dim_property[property id]))),
        NOT(ISBLANK(RELATED(dim_account[account id]))),
        NOT(ISBLANK(RELATED(dim_book[book id])))
    )
VAR IntegrityRatio = DIVIDE(MatchedFactRecords, TotalFactRecords, 0)
RETURN IntegrityRatio * 100

// 4. Measure Accuracy Score (Based on validation tests)
Measure Accuracy Score = 
// Weighted average of key measure accuracy tests
VAR OccupancyAccuracy = [Occupancy Validation Score]
VAR FinancialAccuracy = [Financial Validation Score] 
VAR RentRollAccuracy = [Rent Roll Validation Score]
VAR LeasingAccuracy = [Leasing Activity Validation Score]
RETURN (OccupancyAccuracy * 0.25 + FinancialAccuracy * 0.35 + RentRollAccuracy * 0.25 + LeasingAccuracy * 0.15)
```

### Specific Validation Measures

#### Occupancy Validation
```dax
// Occupancy Logic Validation
Occupancy Validation Score = 
VAR PhysicalOcc = [Physical Occupancy %]
VAR VacancyRate = [Vacancy Rate %]
VAR SumTest = ABS((PhysicalOcc + VacancyRate) - 100)
VAR LogicScore = IF(SumTest <= 1, 100, MAX(0, 100 - SumTest * 10))

VAR RangeTest = 
    IF(PhysicalOcc >= 0 && PhysicalOcc <= 105, 100, 0) // Allow 5% variance for timing
VAR RangeScore = RangeTest

VAR EconomicTest = 
    IF([Economic Occupancy %] <= [Physical Occupancy %] * 1.1, 100, 0) // Economic usually <= Physical
VAR EconomicScore = EconomicTest

RETURN (LogicScore + RangeScore + EconomicScore) / 3

// Occupancy Validation Details
Occupancy Validation Details = 
VAR PhysicalOcc = [Physical Occupancy %]
VAR EconomicOcc = [Economic Occupancy %]
VAR VacancyRate = [Vacancy Rate %]
VAR Issues = BLANK()
VAR IssueList = 
    IF(PhysicalOcc < 0 || PhysicalOcc > 105, "Physical occupancy out of range; ", "") &
    IF(ABS((PhysicalOcc + VacancyRate) - 100) > 1, "Physical + Vacancy ≠ 100%; ", "") &
    IF(EconomicOcc > PhysicalOcc * 1.1, "Economic > Physical occupancy; ", "")
RETURN 
    IF(IssueList = "", "✅ All occupancy validations passed", "❌ Issues: " & IssueList)
```

#### Financial Validation
```dax
// Financial Validation Score
Financial Validation Score = 
// Test 1: Revenue should be positive
VAR RevenueTest = IF([Total Revenue] > 0, 100, 0)

// Test 2: NOI Margin should be reasonable (20-80% for most properties)
VAR NOIMargin = [NOI Margin %]
VAR NOITest = IF(NOIMargin >= 20 && NOIMargin <= 80, 100, MAX(0, 100 - ABS(50 - NOIMargin)))

// Test 3: Revenue PSF should be reasonable ($10-$200 annually)
VAR RevenuePSF = [Revenue PSF]
VAR PSFTest = IF(RevenuePSF >= 10 && RevenuePSF <= 200, 100, 0)

// Test 4: Account codes should follow proper ranges
VAR AccountTest = 
    VAR RevenueAccounts = 
        CALCULATE(
            COUNTROWS(fact_total),
            dim_account[account code] >= 40000000,
            dim_account[account code] < 50000000,
            fact_total[amount] < 0 // Revenue should be positive
        )
    VAR ExpenseAccounts = 
        CALCULATE(
            COUNTROWS(fact_total),
            dim_account[account code] >= 50000000,
            dim_account[account code] < 60000000,
            fact_total[amount] > 0 // Expenses should be negative
        )
    VAR TotalFinancialRecords = 
        CALCULATE(
            COUNTROWS(fact_total),
            dim_account[account code] >= 40000000,
            dim_account[account code] < 60000000
        )
    VAR ErrorRecords = RevenueAccounts + ExpenseAccounts
    RETURN IF(TotalFinancialRecords = 0, 100, MAX(0, (1 - DIVIDE(ErrorRecords, TotalFinancialRecords, 0)) * 100))

RETURN (RevenueTest + NOITest + PSFTest + AccountTest) / 4

// Financial Validation Details
Financial Validation Details = 
VAR Revenue = [Total Revenue]
VAR NOIMargin = [NOI Margin %]
VAR RevenuePSF = [Revenue PSF]
VAR Issues = ""
VAR IssueList = 
    IF(Revenue <= 0, "Revenue not positive; ", "") &
    IF(NOIMargin < 20 || NOIMargin > 80, "NOI margin unusual (" & FORMAT(NOIMargin, "0.0%") & "); ", "") &
    IF(RevenuePSF < 10 || RevenuePSF > 200, "Revenue PSF unusual ($" & FORMAT(RevenuePSF, "0.00") & "); ", "")
RETURN 
    IF(IssueList = "", "✅ All financial validations passed", "❌ Issues: " & IssueList)
```

#### Rent Roll Validation
```dax
// Rent Roll Validation Score
Rent Roll Validation Score = 
// Test 1: Current Monthly Rent should be positive
VAR RentTest = IF([Current Monthly Rent] > 0, 100, 0)

// Test 2: Current Leased SF should be <= Total Rentable SF
VAR SFTest = 
    IF([Current Leased SF] <= [Total Rentable Area] * 1.05, 100, 0) // Allow 5% variance

// Test 3: Rent PSF should be reasonable
VAR RentPSF = [Current Rent Roll PSF]
VAR PSFTest = IF(RentPSF >= 5 && RentPSF <= 150, 100, 0)

// Test 4: Amendment logic - check for duplicate latest sequences
VAR DuplicateTest = 
    VAR AmendmentCheck = 
        ADDCOLUMNS(
            SUMMARIZE(
                dim_fp_amendmentsunitspropertytenant,
                dim_fp_amendmentsunitspropertytenant[property hmy],
                dim_fp_amendmentsunitspropertytenant[tenant hmy]
            ),
            "MaxSequence", 
            CALCULATE(MAX(dim_fp_amendmentsunitspropertytenant[amendment sequence])),
            "CountAtMaxSequence",
            CALCULATE(
                COUNTROWS(dim_fp_amendmentsunitspropertytenant),
                dim_fp_amendmentsunitspropertytenant[amendment sequence] = 
                CALCULATE(MAX(dim_fp_amendmentsunitspropertytenant[amendment sequence]))
            )
        )
    VAR ProblemsCount = 
        SUMX(
            AmendmentCheck,
            IF([CountAtMaxSequence] > 1, 1, 0)
        )
    VAR TotalPairs = COUNTROWS(AmendmentCheck)
    RETURN IF(TotalPairs = 0, 100, MAX(0, (1 - DIVIDE(ProblemsCount, TotalPairs, 0)) * 100))

RETURN (RentTest + SFTest + PSFTest + DuplicateTest) / 4

// Rent Roll Validation Details
Rent Roll Validation Details = 
VAR CurrentRent = [Current Monthly Rent]
VAR LeasedSF = [Current Leased SF]
VAR RentableSF = [Total Rentable Area]
VAR RentPSF = [Current Rent Roll PSF]
VAR Issues = ""
VAR IssueList = 
    IF(CurrentRent <= 0, "No current rent found; ", "") &
    IF(LeasedSF > RentableSF * 1.05, "Leased SF > Rentable SF; ", "") &
    IF(RentPSF < 5 || RentPSF > 150, "Rent PSF unusual ($" & FORMAT(RentPSF, "0.00") & "); ", "")
RETURN 
    IF(IssueList = "", "✅ All rent roll validations passed", "❌ Issues: " & IssueList)
```

#### Leasing Activity Validation
```dax
// Leasing Activity Validation Score
Leasing Activity Validation Score = 
// Test 1: Net Activity Math Check
VAR NetActivity = [Net Leasing Activity SF]
VAR CalculatedNet = [New Leases SF] + [Renewals SF] - [Terminations SF]
VAR NetTest = IF(ABS(NetActivity - CalculatedNet) < 1000, 100, 0)

// Test 2: Activity counts should be reasonable
VAR NewCount = [New Leases Count]
VAR RenewalCount = [Renewals Count]
VAR TermCount = [Terminations Count]
VAR CountTest = 
    IF(NewCount >= 0 && RenewalCount >= 0 && TermCount >= 0, 100, 0)

// Test 3: SF amounts should be reasonable
VAR NewSF = [New Leases SF]
VAR RenewalSF = [Renewals SF]
VAR TermSF = [Terminations SF]
VAR SFTest = 
    IF(NewSF >= 0 && RenewalSF >= 0 && TermSF >= 0, 100, 0)

// Test 4: Retention Rate should be reasonable (0-100%)
VAR RetentionRate = [Retention Rate %]
VAR RetentionTest = 
    IF(RetentionRate >= 0 && RetentionRate <= 100, 100, 0)

RETURN (NetTest + CountTest + SFTest + RetentionTest) / 4

// Leasing Activity Validation Details
Leasing Activity Validation Details = 
VAR NetActivity = [Net Leasing Activity SF]
VAR CalculatedNet = [New Leases SF] + [Renewals SF] - [Terminations SF]
VAR RetentionRate = [Retention Rate %]
VAR Issues = ""
VAR IssueList = 
    IF(ABS(NetActivity - CalculatedNet) >= 1000, 
       "Net activity calculation error (" & FORMAT(NetActivity - CalculatedNet, "#,##0") & " SF); ", "") &
    IF([New Leases Count] < 0 || [Renewals Count] < 0 || [Terminations Count] < 0, 
       "Negative activity counts; ", "") &
    IF(RetentionRate < 0 || RetentionRate > 100, 
       "Retention rate out of range (" & FORMAT(RetentionRate, "0.0%") & "); ", "")
RETURN 
    IF(IssueList = "", "✅ All leasing activity validations passed", "❌ Issues: " & IssueList)
```

## Manual Testing Procedures

### Cross-System Validation

#### Step 1: Prepare Reference Data Using DAX
```dax
// DAX Measures for Cross-System Validation
// 1. Revenue Totals by Property

Property Financial Summary = 
// Creates a summary table of revenue, expenses, and NOI by property
// Use this in a table visual with property code for validation
ADDCOLUMNS(
    VALUES(dim_property[property code]),
    "Revenue Total", [Total Revenue],
    "Expense Total", [Operating Expenses],
    "NOI", [NOI (Net Operating Income)]
)

// Alternative: Create as calculated table for export
Property Financial Validation Table = 
CALCULATETABLE(
    ADDCOLUMNS(
        VALUES(dim_property[property code]),
        "Revenue Total", 
        CALCULATE(
            SUM(fact_total[amount]) * -1,
            dim_account[account code] >= 40000000,
            dim_account[account code] < 50000000,
            fact_total[month] = DATE(2024, 12, 1)
        ),
        "Expense Total",
        CALCULATE(
            ABS(SUM(fact_total[amount])),
            dim_account[account code] >= 50000000,
            dim_account[account code] < 60000000,
            fact_total[month] = DATE(2024, 12, 1)
        )
    ),
    fact_total[month] = DATE(2024, 12, 1)
)

// 2. Current Rent Roll Snapshot

Rent Roll Validation Summary = 
// Summary of current rent roll by property
// Use in table visual or export for comparison
SUMMARIZE(
    dim_property,
    dim_property[property code],
    "Tenant Count", [Current Tenant Count],
    "Monthly Rent", [Current Monthly Rent],
    "Leased SF", [Current Leased SF]
)

// SQL Query results can be replaced with these DAX measures
// Export results from Power BI for comparison with Yardi native reports
```

#### Step 2: Power BI Validation Dashboard
Create a dedicated validation dashboard with these visuals:

```
┌─────────────────┬─────────────────┬─────────────────┐
│ Model Health    │ Data Complete   │ Relationship    │
│ Score: [95.2%]  │ Score: [97.8%]  │ Integrity: [99%]│
└─────────────────┴─────────────────┴─────────────────┘

┌─────────────────┬─────────────────┬─────────────────┐
│ Occupancy       │ Financial       │ Rent Roll       │
│ Valid: [98.5%]  │ Valid: [96.2%]  │ Valid: [94.8%]  │
└─────────────────┴─────────────────┴─────────────────┘

┌───────────────────────────────────────────────────────┐
│              Validation Issue Details                 │
│ Property | Issue Type | Description | Severity       │
│ PROP001  | Occupancy  | >100% occ   | Medium        │
│ PROP002  | Financial  | Neg revenue | High          │
└───────────────────────────────────────────────────────┘
```

### User Acceptance Testing Protocol

#### Test Scenarios

**Scenario 1: Executive Summary Dashboard**
```
Test Steps:
1. Open Executive Summary dashboard
2. Select current month date filter
3. Verify key metrics display correctly:
   - Physical Occupancy %: Expected 85-95%
   - Total Revenue: Expected $2-5M per month
   - NOI Margin %: Expected 50-70%
   - Current Monthly Rent: Expected $1-3M

Acceptance Criteria:
✅ All metrics display within expected ranges
✅ Values make business sense vs prior month
✅ Dashboard loads in <10 seconds
✅ Drill-down functionality works correctly
```

**Scenario 2: Rent Roll Analysis**
```
Test Steps:
1. Open rent roll dashboard  
2. Filter to specific property
3. Verify rent roll details:
   - Tenant list matches known tenants
   - Monthly rent amounts are reasonable
   - Square footage totals are correct
   - PSF rates align with market expectations

Acceptance Criteria:
✅ Rent roll totals within 5% of Yardi native report
✅ All active tenants appear in list
✅ No duplicate tenant entries
✅ PSF rates within market range ($15-$50)
```

**Scenario 3: Leasing Activity Report**
```
Test Steps:
1. Open leasing activity dashboard
2. Select last quarter date range
3. Review activity metrics:
   - New leases executed
   - Renewals completed  
   - Terminations processed
   - Net absorption calculation

Acceptance Criteria:
✅ Activity counts match known deals
✅ Net absorption = New + Renewals - Terms
✅ Retention rate is reasonable (60-80%)
✅ Activity aligns with business expectations
```

### Performance Testing

#### Response Time Benchmarks
```dax
// Create Performance Monitoring Measures
Dashboard Load Time = 
// This would be measured through usage metrics
"Target: <10 seconds for standard dashboards"

Query Response Time = 
// Monitor through Performance Analyzer
"Target: <5 seconds for typical interactions"

Data Refresh Duration = 
// Monitor through refresh history
"Target: <30 minutes for full refresh"
```

#### Load Testing Protocol
1. **Single User Testing**: Test all dashboards with single user
2. **Concurrent User Testing**: Test with 5-10 concurrent users
3. **Peak Load Testing**: Test during maximum expected usage
4. **Large Dataset Testing**: Test with full historical data loaded

## Issue Tracking and Resolution

### Issue Classification

#### Critical Issues (Fix Immediately)
- **Data Accuracy <90%**: Measures significantly different from source
- **Dashboard Failures**: Visuals not loading or showing errors
- **Performance Issues**: >15 second load times
- **Calculation Errors**: Measures returning obviously wrong values

#### High Priority Issues (Fix within 24 hours)
- **Data Accuracy 90-95%**: Minor variances from source systems
- **Missing Data**: Some properties or periods not appearing
- **Formula Logic**: Measures not following business rules correctly
- **User Experience**: Navigation or filtering issues

#### Medium Priority Issues (Fix within 1 week)
- **Data Accuracy 95-98%**: Small variances from source systems
- **Formatting Issues**: Number formats, labels, or colors incorrect
- **Performance Optimization**: Load times 10-15 seconds
- **Enhancement Requests**: Additional features or calculations

### Issue Resolution Process

#### Step 1: Issue Documentation
```
Issue Template:
- Issue ID: [Unique identifier]
- Date Reported: [Date/Time]
- Reporter: [Name and role]
- Severity: [Critical/High/Medium/Low]
- Dashboard/Measure: [Specific location]
- Description: [Detailed description]
- Expected Result: [What should happen]
- Actual Result: [What actually happens]
- Steps to Reproduce: [How to recreate issue]
- Screenshots: [Visual evidence]
```

#### Step 2: Root Cause Analysis
1. **Data Source Investigation**: Check if issue originates in source data
2. **Transformation Analysis**: Review Power Query transformations
3. **Relationship Validation**: Verify table relationships are correct
4. **Measure Logic Review**: Analyze DAX code for logical errors
5. **Performance Analysis**: Check for performance-related causes

#### Step 3: Resolution Implementation
1. **Fix Development**: Implement corrective measures
2. **Testing**: Validate fix resolves issue without creating new problems
3. **Documentation**: Update documentation with changes made
4. **Deployment**: Apply fix to production environment
5. **Verification**: Confirm issue is resolved in production

### Continuous Monitoring

#### Automated Monitoring Setup
```dax
// Create Monitoring Measures for Daily Checks
Daily Health Check = 
VAR TodayScore = [Model Health Score]
VAR YesterdayScore = 
    CALCULATE(
        [Model Health Score],
        DATEADD(dim_date[date], -1, DAY)
    )
VAR ScoreChange = TodayScore - YesterdayScore
RETURN 
    IF(
        TodayScore >= 95,
        "✅ System Healthy (" & FORMAT(TodayScore, "0.0%") & ")",
        IF(
            TodayScore >= 90,
            "⚠️ Minor Issues (" & FORMAT(TodayScore, "0.0%") & ")",
            "🔴 Critical Issues (" & FORMAT(TodayScore, "0.0%") & ")"
        )
    )

// Alert Conditions
Alert Required = 
VAR HealthScore = [Model Health Score]
VAR DataFreshness = DATEDIFF(MAX(fact_total[month]), TODAY(), DAY)
VAR CriticalErrors = [Critical Error Count]
RETURN
    HealthScore < 90 || DataFreshness > 31 || CriticalErrors > 10

// Trending Issues
Issue Trend = 
VAR Current = [Critical Error Count]
VAR Prior = 
    CALCULATE(
        [Critical Error Count],
        DATEADD(dim_date[date], -7, DAY)
    )
RETURN
    IF(
        Current > Prior * 1.2,
        "📈 Issues Increasing",
        IF(
            Current < Prior * 0.8,
            "📉 Issues Decreasing",
            "➡️ Issues Stable"
        )
    )
```

## Validation Checklist

### Pre-Production Validation
- [ ] All 77 measures execute without errors
- [ ] Validation dashboard shows >95% overall health score
- [ ] Cross-system validation completed for key measures
- [ ] Performance benchmarks met (<10 sec dashboard load)
- [ ] User acceptance testing completed successfully
- [ ] Business sign-off obtained from key stakeholders

### Production Monitoring
- [ ] Daily automated validation checks configured
- [ ] Alert thresholds set for critical issues
- [ ] Monthly comprehensive validation schedule established
- [ ] Issue tracking system implemented
- [ ] Performance monitoring dashboards created

### Ongoing Improvement
- [ ] Quarterly validation procedure reviews
- [ ] Annual accuracy benchmark updates
- [ ] User feedback integration process
- [ ] Continuous improvement project pipeline
- [ ] Knowledge transfer and documentation updates

This comprehensive validation and testing framework ensures reliable, accurate data for business decision-making throughout the lifecycle of your Power BI solution.
