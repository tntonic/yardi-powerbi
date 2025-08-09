# Common Issues & Solutions

## Overview

This document provides comprehensive troubleshooting guidance for common issues encountered in the Yardi BI Power BI implementation, including data connection problems, performance issues, calculation errors, and dashboard display problems.

**Production Solution Status - Updated August 9, 2025:**
- ⚠️ **Current Accuracy**: 93% rent roll (Target: 95-99%), 91% leasing activity (Target: 95-98%)
- ✅ **122 Production Measures**: All measures tested and functional
- ⚠️ **Critical Data Issues**: 20.92% orphaned property records affecting accuracy
- ✅ **Performance**: Sub-10 second dashboard load times achievable after fixes

## Accuracy Validation Issues

### 1. Rent Roll Accuracy Discrepancies

#### Expected Accuracy
- **Target**: 95-99% accuracy vs native Yardi rent roll reports
- **Validated**: Production implementation achieves this target consistently

#### Common Discrepancies & Solutions

**Amendment Selection Logic**
```
Problem: Rent roll totals don't match Yardi reports
Root Cause: Incorrect amendment selection (not using latest sequence)
Solution:
1. Verify amendment selection logic uses LATEST sequence per property/tenant
2. Include both "Activated" AND "Superseded" status amendments
3. Exclude amendments where type = "Termination"
4. Check date filtering logic for current vs future leases

Validation DAX Measure:
Latest Amendment Validation = 
SUMMARIZE(
    FILTER(
        dim_fp_amendmentsunitspropertytenant,
        dim_fp_amendmentsunitspropertytenant[amendment status] IN {"Activated", "Superseded"} &&
        dim_fp_amendmentsunitspropertytenant[amendment type] <> "Termination"
    ),
    dim_fp_amendmentsunitspropertytenant[property hmy],
    dim_fp_amendmentsunitspropertytenant[tenant hmy],
    "Latest Sequence", MAX(dim_fp_amendmentsunitspropertytenant[amendment sequence])
)
```

### 2. Leasing Activity Report Discrepancies

#### Expected Accuracy
- **Target**: 95-98% accuracy vs native Yardi leasing activity reports
- **Validated**: Production implementation achieves this target consistently

#### Common Issues & Solutions

**Transaction Counting Logic**
```
Problem: Activity counts don't match Yardi reports
Root Cause: Incorrect business logic for activity types
Solution:
1. New Leases: amendment_type = "Original Lease" AND status = "Activated"
2. Renewals: amendment_type = "Renewal" OR sequence > 0 AND status = "Activated"  
3. Terminations: Use termination table with status = "Activated"
4. Verify date filtering based on amendment start/end dates

Validation DAX Measure:
Leasing Activity Summary = 
VAR PeriodStart = MIN(dim_date[date])
VAR PeriodEnd = MAX(dim_date[date])
RETURN
SUMMARIZE(
    FILTER(
        dim_fp_amendmentsunitspropertytenant,
        dim_fp_amendmentsunitspropertytenant[amendment start date] >= PeriodStart &&
        dim_fp_amendmentsunitspropertytenant[amendment start date] <= PeriodEnd
    ),
    dim_fp_amendmentsunitspropertytenant[amendment type],
    dim_fp_amendmentsunitspropertytenant[amendment status],
    "Transaction Count", COUNTROWS(dim_fp_amendmentsunitspropertytenant)
)
```

## Data Connection Issues

### 1. SQL Server Connection Failures

#### Symptoms
- Power BI Desktop cannot connect to Yardi database
- "Cannot connect to server" error messages
- Timeout errors during data refresh
- Authentication failures

#### Common Causes & Solutions

**Network Connectivity Issues**
```
Problem: Firewall blocking connection
Solution:
1. Verify server name and port (usually 1433)
2. Check firewall rules on client and server
3. Test connection using SQL Server Management Studio
4. Ensure SQL Server Browser service is running

Command to test: telnet [server_name] 1433
```

**Authentication Problems**
```
Problem: Login failed for user
Solutions:
1. Verify SQL Server authentication mode is set to mixed
2. Check user permissions on Yardi database
3. Use Windows Authentication if possible
4. Verify password hasn't expired

Required Permissions:
- db_datareader on Yardi database
- CONNECT permission
- VIEW DEFINITION permission (for schema access)
```

**Connection String Issues**
```
Correct Format:
Server=[YardiServer];Database=[YardiDB];Trusted_Connection=yes;

For SQL Authentication:
Server=[YardiServer];Database=[YardiDB];User ID=[username];Password=[password];

Common Mistakes:
- Missing server instance name
- Incorrect database name
- Wrong port specification
```

#### Resolution Steps
1. **Test Basic Connectivity**
   ```sql
   // DAX measure to verify data connection
   Data Connection Check = 
   VAR RecordCount = COUNTROWS(fact_total)
   VAR PropertyCount = DISTINCTCOUNT(dim_property[property id])
   RETURN "Records: " & FORMAT(RecordCount, "#,##0") & " | Properties: " & FORMAT(PropertyCount, "#,##0")
   ```

2. **Verify Table Access**
   ```sql
   // DAX measures to verify table access
   Table Access Check = 
   VAR PropertyRows = COUNTROWS(dim_property)
   VAR FactTotalRows = COUNTROWS(fact_total)
   VAR AmendmentRows = COUNTROWS(dim_fp_amendmentsunitspropertytenant)
   RETURN "Properties: " & FORMAT(PropertyRows, "#,##0") & 
          " | Financials: " & FORMAT(FactTotalRows, "#,##0") & 
          " | Amendments: " & FORMAT(AmendmentRows, "#,##0")
   ```

3. **Check Data Gateway Configuration**
   - Ensure On-premises Data Gateway is installed and running
   - Verify gateway service account has database permissions
   - Test gateway connection in Power BI Service

### 2. Data Refresh Failures

#### Symptoms
- Scheduled refresh fails in Power BI Service
- "Data source error" messages
- Partial data loading
- Inconsistent refresh timing

#### Common Causes & Solutions

**Gateway Configuration Issues**
```
Problem: Gateway not configured or offline
Solutions:
1. Check gateway status in Power BI Admin Portal
2. Restart gateway service on server
3. Update gateway to latest version
4. Verify gateway clustering (if applicable)

Gateway Service Check:
Services.msc → "On-premises data gateway service"
Status should be "Running"
```

**Memory and Timeout Issues**
```
Problem: Refresh timeout or memory errors
Solutions:
1. Increase gateway machine memory (minimum 8GB)
2. Adjust timeout settings in Power BI Service
3. Implement incremental refresh for large tables
4. Split large queries into smaller batches

Incremental Refresh Setup:
1. Define date/time parameters in Power Query
2. Configure incremental refresh policy
3. Set historical and refresh periods appropriately
```

**Data Source Permissions**
```
Problem: Service account lacks permissions
Solutions:
1. Use dedicated service account for gateway
2. Grant minimum required database permissions
3. Avoid using personal accounts
4. Configure proper authentication method

Required Service Account Rights:
- "Log on as a service" 
- Read access to Yardi database
- Network permissions to reach SQL Server
```

#### Resolution Steps
1. **Check Gateway Health**
   ```powershell
   # PowerShell commands to check gateway
   Get-Service -Name "PBIEgwService"
   Get-EventLog -LogName Application -Source "On-premises data gateway"
   ```

2. **Monitor Refresh Performance**
   ```
   Power BI Service → Dataset → Refresh History
   - Review error messages
   - Check duration trends
   - Identify problematic tables
   ```

3. **Optimize Refresh Strategy**
   ```
   Large Tables (>1M rows): Enable incremental refresh
   Medium Tables (100K-1M): Refresh daily
   Small Tables (<100K): Refresh hourly
   Lookup Tables: Refresh weekly
   ```

## Performance Issues

### 3. Slow Dashboard Loading

#### Symptoms
- Dashboards take >10 seconds to load
- Visuals timeout during rendering
- Page navigation is sluggish
- Browser becomes unresponsive

#### Common Causes & Solutions

**Data Model Size Issues**
```
Problem: Model too large for efficient processing
Solutions:
1. Remove unused columns and tables
2. Implement proper data types
3. Create aggregation tables
4. Use DirectQuery for very large datasets

Data Model Optimization:
- Text columns: Use categorical data types
- Dates: Use proper date/time types
- Numbers: Use smallest appropriate numeric type
- Remove blank rows and columns
```

**Inefficient DAX Measures**
```
Problem: Complex calculations causing delays
Solutions:
1. Use variables to avoid recalculation
2. Avoid CALCULATE() in iterating functions
3. Use SUMMARIZECOLUMNS instead of SUMMARIZE
4. Pre-calculate complex measures in Power Query

Example Optimization:
BEFORE:
CALCULATE(SUM(Table[Column]), FILTER(Table, Table[Date] > TODAY()))

AFTER:
VAR FilteredTable = FILTER(Table, Table[Date] > TODAY())
RETURN SUMX(FilteredTable, Table[Column])
```

**Visual Overload**
```
Problem: Too many visuals on single page
Solutions:
1. Limit to 10-12 visuals per page
2. Use bookmarks for multiple views
3. Implement drill-through instead of detailed tables
4. Consider paginated reports for detailed data

Best Practices:
- Use slicers sparingly (max 5 per page)
- Avoid complex custom visuals
- Limit data points in charts (max 1000)
- Use TOP N filtering for large categories
```

#### Resolution Steps
1. **Performance Analyzer**
   ```
   View → Performance Analyzer
   1. Start recording
   2. Refresh all visuals
   3. Analyze duration for each visual
   4. Identify bottlenecks
   ```

2. **DAX Studio Analysis**
   ```sql
   -- Check model size and efficiency
   SELECT * FROM $SYSTEM.DISCOVER_OBJECT_MEMORY_USAGE
   ORDER BY [OBJECT_MEMORY_NONSHRINKABLE] DESC
   
   -- Analyze query performance
   SELECT * FROM $SYSTEM.DISCOVER_QUERY_STATS
   ORDER BY [Query_Duration] DESC
   ```

3. **Model Optimization**
   ```
   File → Options → Data Load
   - Disable auto date/time
   - Reduce relationship cardinality where possible
   - Use single direction filtering (except for dates)
   ```

### 4. Memory and Capacity Issues

#### Symptoms
- "Insufficient memory" errors
- Dataset refresh failures
- Browser crashes during interaction
- Power BI Service capacity warnings

#### Common Causes & Solutions

**Dataset Size Limits**
```
Power BI Pro: 1 GB limit per dataset
Power BI Premium: 10 GB (Gen2) limit per dataset

Solutions:
1. Implement data archiving strategy
2. Use DirectQuery for historical data
3. Create separate datasets for different time periods
4. Use incremental refresh with data compression
```

**Memory-Intensive Calculations**
```
Problem: Complex DAX measures consuming too much memory
Solutions:
1. Avoid calculated columns in large tables
2. Use measures instead of calculated columns
3. Pre-aggregate data in SQL Server
4. Implement star schema design properly

Memory-Efficient Patterns:
- Use SUMMARIZECOLUMNS for aggregations
- Avoid ALL() functions in large tables
- Use KEEPFILTERS() to maintain filter context
- Pre-filter data in Power Query
```

#### Resolution Steps
1. **Monitor Capacity Metrics**
   ```
   Power BI Premium Metrics App:
   - Dataset memory usage
   - CPU utilization
   - Query duration trends
   - Eviction patterns
   ```

2. **Optimize Data Types**
   ```
   Power Query → Column Tools → Data Type
   - Integer instead of Decimal for whole numbers
   - Text instead of Any for string data
   - Date instead of DateTime (if time not needed)
   - Boolean instead of Text for Yes/No values
   ```

## Calculation Errors

### 5. Incorrect Rent Roll Calculations

#### Symptoms
- Rent roll totals don't match Yardi reports
- Missing tenants in current rent roll
- Duplicate or incorrect rent amounts
- Future leases appearing in current rent roll

#### Common Causes & Solutions

**Amendment Logic Errors**
```
Problem: Incorrect amendment filtering
Solution: Use validated amendment logic

Correct Logic:
1. Include "Activated" AND "Superseded" statuses
2. Exclude "Termination" types
3. Use LATEST sequence per property/tenant
4. Apply proper date filtering

Common Mistakes:
- Only including "Activated" amendments
- Not handling "Superseded" status correctly
- Using MIN instead of MAX for sequence
- Incorrect date comparisons
```

**Date Handling Issues**
```
Problem: Excel date format causing errors
Solution: Proper date conversion in Power Query

Correct Transformation:
= Table.TransformColumns(Source,{
    {"amendment start date", each Date.From(Number.From(_) + #date(1899,12,30))},
    {"amendment end date", each Date.From(Number.From(_) + #date(1899,12,30))}
})

Validation DAX Measure:
Date Conversion Check = 
VAR SampleExcelDate = 44926  // Example: January 1, 2023
VAR ConvertedDate = DATE(1899, 12, 30) + SampleExcelDate
VAR ExpectedDate = DATE(2023, 1, 1)
RETURN
IF(
    ConvertedDate = ExpectedDate,
    "✅ Date conversion correct",
    "❌ Date conversion error: " & FORMAT(ConvertedDate, "yyyy-mm-dd")
)
```

**Charge Schedule Mismatches**
```
Problem: Amendments without corresponding charges
Solution: Implement proper relationship and error handling

Diagnostic DAX Measure:
Amendments Without Charges = 
VAR AmendmentsWithCharges = 
    SUMMARIZE(
        dim_fp_amendmentchargeschedule,
        dim_fp_amendmentchargeschedule[amendment hmy]
    )
VAR AllActiveAmendments = 
    CALCULATETABLE(
        SUMMARIZE(
            dim_fp_amendmentsunitspropertytenant,
            dim_fp_amendmentsunitspropertytenant[amendment hmy]
        ),
        dim_fp_amendmentsunitspropertytenant[amendment status] IN {"Activated", "Superseded"},
        dim_fp_amendmentsunitspropertytenant[amendment type] <> "Termination"
    )
RETURN
COUNTROWS(EXCEPT(AllActiveAmendments, AmendmentsWithCharges))
```

#### Resolution Steps
1. **Validate Amendment Base**
   ```dax
   // Create validation measure
   Amendment Validation = 
   VAR TotalAmendments = COUNTROWS(dim_fp_amendmentsunitspropertytenant)
   VAR ValidAmendments = 
       COUNTROWS(
           FILTER(
               dim_fp_amendmentsunitspropertytenant,
               NOT(ISBLANK(dim_fp_amendmentsunitspropertytenant[amendment sequence])) &&
               NOT(ISBLANK(dim_fp_amendmentsunitspropertytenant[amendment start date]))
           )
       )
   RETURN DIVIDE(ValidAmendments, TotalAmendments, 0) * 100
   ```

2. **Cross-Reference with Yardi**
   ```sql
   // DAX measures to match Power BI results
   Current Rent Roll Validation = 
   VAR CurrentDate = TODAY()
   VAR TenantCount = 
       CALCULATE(
           DISTINCTCOUNT(dim_fp_amendmentsunitspropertytenant[tenant hmy]),
           dim_fp_amendmentsunitspropertytenant[amendment status] IN {"Activated", "Superseded"},
           dim_fp_amendmentsunitspropertytenant[amendment type] <> "Termination",
           dim_fp_amendmentsunitspropertytenant[amendment start date] <= CurrentDate,
           dim_fp_amendmentsunitspropertytenant[amendment end date] >= CurrentDate || 
               ISBLANK(dim_fp_amendmentsunitspropertytenant[amendment end date]),
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
   VAR TotalRent = [Current Monthly Rent]
   RETURN
   "Tenant Count: " & FORMAT(TenantCount, "#,##0") & 
   " | Monthly Rent: " & FORMAT(TotalRent, "$#,##0")
   ```

### 6. Financial Calculation Discrepancies

#### Symptoms
- NOI calculations don't match GL reports
- Revenue totals incorrect
- Missing expense categories
- Wrong account classifications

#### Common Causes & Solutions

**Account Mapping Issues**
```
Problem: Incorrect account code ranges
Solution: Verify account classification logic

Standard Account Ranges:
Revenue: 40000-49999
Operating Expenses: 50000-59999 (excluding specific accounts)
Capital Expenses: Usually 64001100-64001600
Excluded Accounts: 64006000 (typically depreciation)

Validation DAX Measures:
// 1. Create calculated column in dim_account table
Account Classification = 
SWITCH(
    TRUE(),
    dim_account[account code] >= 40000000 && dim_account[account code] < 50000000, "Revenue",
    dim_account[account code] >= 50000000 && dim_account[account code] < 60000000, "Operating Expense",
    "Other"
)

// 2. Summary measure for validation
Account Summary Validation = 
VAR DateThreshold = DATE(2024, 1, 1)
RETURN
SUMMARIZECOLUMNS(
    dim_account[account code],
    dim_account[account description],
    dim_account[Account Classification],
    FILTER(fact_total, fact_total[month] >= DateThreshold),
    "Total Amount", SUM(fact_total[amount])
)
```

**Period and Book Filtering**
```
Problem: Wrong accounting period or book selection
Solutions:
1. Use dim_lastclosedperiod for period filtering
2. Verify book selection (usually book_id = 1 for standard GL)
3. Check for FPR book analysis (book_id = 46)

Correct Period Filter:
VAR LastClosedDate = 
    CALCULATE(
        MAX(dim_lastclosedperiod[last closed date]),
        ALL(dim_lastclosedperiod)
    )
VAR CurrentDate = MAX(dim_date[date])
RETURN CurrentDate <= LastClosedDate
```

#### Resolution Steps
1. **Account Analysis**
   ```dax
   // Create account validation table
   Account Classification Check = 
   ADDCOLUMNS(
       VALUES(dim_account[account code]),
       "Account Description", RELATED(dim_account[account description]),
       "Current Year Amount", 
           CALCULATE(
               SUM(fact_total[amount]),
               YEAR(dim_date[date]) = YEAR(TODAY())
           ),
       "Classification",
           SWITCH(
               TRUE(),
               dim_account[account code] >= 40000000 && dim_account[account code] < 50000000, "Revenue",
               dim_account[account code] >= 50000000 && dim_account[account code] < 60000000, "Operating Expense",
               "Other"
           )
   )
   ```

2. **GL Reconciliation**
   ```
   Steps:
   1. Export Power BI financial summary
   2. Compare with Yardi GL reports for same period
   3. Identify variances >1%
   4. Drill down to account level differences
   5. Verify account mapping and period selection
   ```

## Dashboard Display Issues

### 7. Visual Rendering Problems

#### Symptoms
- Charts displaying incorrectly
- Missing data points
- Formatting issues
- Tooltips not working

#### Common Causes & Solutions

**Data Type Mismatches**
```
Problem: Wrong data types causing display issues
Solutions:
1. Ensure numeric columns are properly typed
2. Convert text numbers to numeric
3. Handle null values appropriately
4. Use proper date formats

Power Query Fixes:
- Number.From() for numeric conversion
- Date.From() for date conversion  
- Text.From() for text conversion
- Replace null values with appropriate defaults
```

**Filter Context Issues**
```
Problem: Visuals showing unexpected results due to filters
Solutions:
1. Check slicer interactions
2. Verify drill-through filters
3. Use ALL() or ALLSELECTED() appropriately
4. Clear filters to test base data

DAX Pattern for Filter Debugging:
Debug Measure = 
VAR CurrentFilters = FILTERS(dim_property)
RETURN 
IF(
    ISEMPTY(CurrentFilters),
    "No filters applied",
    "Filters active: " & CONCATENATEX(CurrentFilters, dim_property[property name], ", ")
)
```

#### Resolution Steps
1. **Visual Diagnostics**
   ```
   Steps:
   1. Right-click visual → "See data"
   2. Check for missing values or unexpected data
   3. Verify filter pane settings
   4. Test with simple measures first
   5. Add complexity gradually
   ```

2. **Clear Cache and Refresh**
   ```
   Power BI Desktop:
   File → Options → Data Load → Clear Cache
   
   Power BI Service:
   Dataset → Settings → Scheduled Refresh → Refresh Now
   ```

### 8. Mobile Display Issues

#### Symptoms
- Dashboard not responsive on mobile
- Text too small to read
- Touch targets too small
- Charts not optimized for mobile

#### Common Causes & Solutions

**Layout Issues**
```
Problem: Desktop layout not mobile-friendly
Solutions:
1. Create separate mobile layout
2. Use mobile-optimized visual types
3. Increase text sizes
4. Simplify complex visuals

Mobile Best Practices:
- Minimum 14pt font size
- 44px minimum touch targets
- Maximum 4 visuals per mobile page
- Use portrait orientation layouts
```

**Visual Selection Issues**
```
Problem: Complex visuals don't work well on mobile
Solutions:
1. Use simple bar/column charts instead of complex visuals
2. Replace tables with card visuals
3. Use gauge charts for single metrics
4. Avoid scatter plots and complex matrices

Mobile-Friendly Visuals:
✓ Cards and KPI visuals
✓ Simple bar charts
✓ Line charts (single series)
✓ Donut charts (max 5 segments)
✗ Complex matrices
✗ Scatter plots with many points
✗ Multi-axis charts
✗ Custom visuals
```

#### Resolution Steps
1. **Mobile Layout Creation**
   ```
   View → Mobile Layout
   1. Drag visuals from desktop view
   2. Resize for mobile screen
   3. Test on actual mobile device
   4. Optimize touch interactions
   ```

2. **Mobile Testing**
   ```
   Testing Checklist:
   - Test on iOS and Android
   - Verify both portrait and landscape
   - Check touch responsiveness
   - Validate text readability
   - Test filtering and navigation
   ```

## Emergency Procedures

### 9. Critical System Failures

#### Power BI Service Outages
```
Immediate Actions:
1. Check Power BI Service Status page
2. Notify affected users
3. Implement backup reporting procedures
4. Document impact and duration

Communication Template:
"Power BI services are currently unavailable due to [reason]. 
We estimate restoration by [time]. 
Alternative reports are available at [location]."
```

#### Data Gateway Failures
```
Emergency Response:
1. Restart gateway service
2. Check server health and resources
3. Switch to backup gateway (if configured)
4. Contact IT support for server issues

Gateway Failover:
1. Install secondary gateway
2. Configure gateway cluster
3. Test automatic failover
4. Document failover procedures
```

#### Widespread Calculation Errors
```
Crisis Response:
1. Immediately disable affected dashboards
2. Identify root cause of calculation errors
3. Restore from known good backup
4. Validate all calculations before republishing

Validation Checklist:
- Run validation queries against source data
- Compare key metrics with previous period
- Test with multiple date ranges
- Verify with business stakeholders
```

### 10. Escalation Procedures

#### Internal Escalation
```
Level 1: Self-service troubleshooting (30 minutes)
Level 2: Team lead/senior developer (2 hours)
Level 3: IT Support/Database team (4 hours)
Level 4: Vendor support (24 hours)

Contact Information:
- Power BI Support: [support contact]
- Database Admin: [DBA contact]
- Business Stakeholders: [business contact]
```

#### External Support
```
Microsoft Power BI Support:
- Premier Support: Dedicated support engineer
- Professional Support: Standard support tickets
- Community Support: Power BI Community forums

Information to Gather:
- Error messages (screenshots)
- Steps to reproduce
- Impact on business operations
- System configuration details
```

## Prevention and Monitoring

### 11. Proactive Monitoring

#### Performance Monitoring
```
Daily Checks:
- Dashboard load times (<10 seconds)
- Data refresh success rates (>95%)
- User activity and adoption metrics
- System resource utilization

Weekly Reviews:
- Data quality metrics
- Calculation accuracy validation
- User feedback and issues
- Capacity planning assessment
```

#### Automated Alerts
```
Power Automate Integration:
1. Data refresh failure alerts
2. Performance degradation warnings
3. Data quality threshold alerts
4. User access issues

Alert Configuration:
- Immediate: Critical system failures
- Hourly: Performance issues
- Daily: Data quality reports
- Weekly: Usage and adoption metrics
```

### 12. Best Practices for Issue Prevention

#### Development Standards
```
Code Quality:
- Use consistent naming conventions
- Document complex DAX measures
- Test with sample data before production
- Implement error handling in measures

Deployment Process:
- Staged deployment (Dev → Test → Prod)
- User acceptance testing
- Performance validation
- Rollback procedures
```

#### Documentation Requirements
```
Required Documentation:
- Data source connections and credentials
- Business logic and calculation methods
- Known issues and workarounds
- User training materials
- Support procedures and contacts

Update Schedule:
- Monthly: Performance metrics
- Quarterly: Full documentation review
- Annually: Complete system audit
```

## NEW CRITICAL ISSUES - August 2025 Validation

### 13. Orphaned Property Records (HIGHEST PRIORITY)

#### Symptoms
- Financial totals significantly lower than expected
- Missing properties in reports
- Fact_total records not matching dimension tables
- 20.92% of financial records affected

#### Root Cause
- Dimension table (dim_property) missing entries for properties in fact_total
- Data synchronization issue between source systems
- Incomplete property master data import

#### Resolution Steps
1. **Immediate Fix**
   ```sql
   -- Identify orphaned records
   SELECT DISTINCT f.[property id], COUNT(*) as orphaned_count
   FROM fact_total f
   LEFT JOIN dim_property p ON f.[property id] = p.[property id]
   WHERE p.[property id] IS NULL
   GROUP BY f.[property id]
   ORDER BY orphaned_count DESC
   ```

2. **Recovery Process**
   - Export list of missing property IDs
   - Query Yardi source for missing property data
   - Import missing property records to dim_property
   - Validate relationships after import

3. **Prevention**
   - Implement referential integrity checks in ETL
   - Add data quality gates before refresh
   - Create orphaned record alert measures

### 14. Multiple Active Amendments Issue

#### Symptoms
- Duplicate tenants in rent roll
- Inflated rent calculations
- 180 property/tenant combinations affected (13.8%)

#### Root Cause
- Missing or incorrect latest amendment selection logic
- Multiple amendments with same sequence number
- Status filtering not properly applied

#### Resolution Steps
1. **Add Validation Measure**
   ```dax
   Multiple Active Amendments Check = 
   VAR ProblematicCombos = 
   SUMMARIZE(
       FILTER(
           dim_fp_amendmentsunitspropertytenant,
           dim_fp_amendmentsunitspropertytenant[amendment status] IN {"Activated", "Superseded"}
       ),
       dim_fp_amendmentsunitspropertytenant[property hmy],
       dim_fp_amendmentsunitspropertytenant[tenant hmy],
       "Amendment Count", 
       CALCULATE(
           COUNTROWS(dim_fp_amendmentsunitspropertytenant),
           dim_fp_amendmentsunitspropertytenant[amendment sequence] = 
           MAX(dim_fp_amendmentsunitspropertytenant[amendment sequence])
       )
   )
   RETURN COUNTROWS(FILTER(ProblematicCombos, [Amendment Count] > 1))
   ```

2. **Fix Amendment Logic**
   - Ensure ONLY latest sequence is selected
   - Add tie-breaker logic for same sequence numbers
   - Consider amendment date as secondary sort

### 15. Missing Tables from Expected Schema

#### Symptoms
- 29 of 32 expected tables found
- Some advanced features not working
- Missing dimension tables for specific analyses

#### Identified Missing Tables
- dim_moveoutreasons
- dim_newleasereason
- fact_leasingactivity (possibly)

#### Resolution Steps
1. **Verify Table Requirements**
   - Check if tables are truly needed
   - Review feature dependencies
   - Assess impact on dashboards

2. **Recovery Options**
   - Request missing tables from Yardi export
   - Create placeholder tables if non-critical
   - Update documentation with actual table list

### 16. Revenue Sign Convention Inconsistency

#### Symptoms
- 8% of revenue records stored as positive (should be negative)
- Revenue calculations showing incorrect totals
- NOI calculations affected

#### Resolution Steps
1. **Add Data Quality Check**
   ```dax
   Revenue Sign Check = 
   VAR PositiveRevenue = 
   CALCULATE(
       COUNTROWS(fact_total),
       dim_account[account code] >= 40000000,
       dim_account[account code] < 50000000,
       fact_total[amount] > 0
   )
   VAR TotalRevenue = 
   CALCULATE(
       COUNTROWS(fact_total),
       dim_account[account code] >= 40000000,
       dim_account[account code] < 50000000
   )
   RETURN DIVIDE(PositiveRevenue, TotalRevenue, 0) * 100
   ```

2. **Correction Logic**
   - Update ETL to ensure consistent sign convention
   - Add transformation in Power Query if needed
   - Document exceptions for special cases

This comprehensive troubleshooting guide provides systematic approaches to identifying, resolving, and preventing common issues in the Yardi BI Power BI implementation. The August 2025 validation identified critical data quality issues that must be resolved to achieve target accuracy levels.