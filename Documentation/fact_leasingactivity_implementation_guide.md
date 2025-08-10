# fact_leasingactivity Implementation Guide

## Executive Summary

This guide provides step-by-step instructions for integrating the fact_leasingactivity table into the existing 32-table Yardi Power BI data model. The integration adds comprehensive leasing pipeline analytics while preserving all existing amendment-based rent roll functionality.

## Pre-Implementation Validation ✅

### Amendment Logic Compatibility Confirmed
- **Existing Logic**: Uses `dim_fp_amendmentsunitspropertytenant` for current rent roll (latest sequence filtering)
- **New Logic**: Uses `fact_leasingactivity` for leasing pipeline and deal flow analysis
- **Result**: **No conflicts** - the tables serve complementary purposes
- **Validation**: Existing DAX measures will continue to work unchanged

### Data Quality Assessment Results
| Metric | Result | Status |
|--------|---------|--------|
| Total Records | 2,675 | ✅ Good volume |
| Tenant Code Match Rate | 97.9% (505/516) | ✅ Acceptable |
| Orphaned Records | 2.1% (11 codes) | ⚠️ Manageable |
| Date Format Compatibility | 100% | ✅ Perfect |
| Deal Stage Distribution | Balanced across pipeline | ✅ Good business logic |

## Implementation Steps

### Phase 1: Data Model Integration (30 minutes)

#### Step 1.1: Load Table into Power BI
1. Open Power BI Desktop
2. **Get Data** > **Text/CSV**
3. Select: `Data/Yardi_Tables/fact_leasingactivity.csv`
4. Click **Transform Data** to open Power Query Editor

#### Step 1.2: Apply Data Transformations
Copy and paste this complete M code into the Advanced Editor:

```m
let
    // Load source data
    Source = Csv.Document(File.Contents("[YourPath]\fact_leasingactivity.csv")),
    Headers = Table.PromoteHeaders(Source),
    
    // Data type conversions
    ConvertTypes = Table.TransformColumnTypes(Headers, {
        {"Deal HMY", Int64.Type},
        {"Tenant HMY", Int64.Type},
        {"Starting Rent", type number},
        {"Escalation Rate", type number},
        {"iTerm", Int64.Type},
        {"dArea", type number},
        {"dTotalNPV", type number},
        {"dAnnualNPV", type number},
        {"dtStartDate", type date},
        {"dtEndDate", type date},
        {"dtcreated", type datetime},
        {"dtlastmodified", type datetime}
    }),
    
    // Clean tenant codes
    CleanTenantCode = Table.ReplaceValue(ConvertTypes, "", null, Replacer.ReplaceValue, {"Tenant Code"}),
    
    // Add business logic columns
    AddDealStageOrder = Table.AddColumn(CleanTenantCode, "Deal Stage Order", 
        each if [Deal Stage] = "Lead" then 1
        else if [Deal Stage] = "Tour" then 2  
        else if [Deal Stage] = "Proposal" then 3
        else if [Deal Stage] = "Negotiation" then 4
        else if [Deal Stage] = "Executed" then 5
        else if [Deal Stage] = "Dead Deal" then 0
        else 99, Int64.Type),
    
    // Add term categorization
    AddTermCategory = Table.AddColumn(AddDealStageOrder, "Term Category",
        each if [iTerm] = null then "Unknown"
        else if [iTerm] <= 12 then "Short Term (≤12 months)"
        else if [iTerm] <= 36 then "Medium Term (13-36 months)" 
        else if [iTerm] <= 60 then "Long Term (37-60 months)"
        else "Extended Term (>60 months)", type text),
    
    // Add rent PSF calculation  
    AddRentPSF = Table.AddColumn(AddTermCategory, "Starting Rent PSF",
        each if [Starting Rent] = null or [dArea] = null or [dArea] = 0 then null
        else ([Starting Rent] * 12) / [dArea], type number),
    
    // Add data quality flag
    AddDataQualityFlag = Table.AddColumn(AddRentPSF, "Has Tenant Link",
        each [Tenant Code] <> null, type logical)
        
in
    AddDataQualityFlag
```

#### Step 1.3: Create Relationships
**In Model View, create these relationships:**

1. **Primary Tenant Relationship** (Required)
   - From: `fact_leasingactivity[Tenant Code]`
   - To: `dim_commcustomer[tenant code]`
   - Cardinality: Many-to-One (*)
   - Cross Filter Direction: Single →
   - Active: ✅ Yes

2. **Start Date Relationship** (Required)
   - From: `fact_leasingactivity[dtStartDate]`
   - To: `dim_date[date]`
   - Cardinality: Many-to-One (*)
   - Cross Filter Direction: Single →
   - Active: ✅ Yes

3. **End Date Relationship** (Optional)
   - From: `fact_leasingactivity[dtEndDate]`
   - To: `dim_date[date]`
   - Cardinality: Many-to-One (*)
   - Cross Filter Direction: Single →
   - Active: ❌ No (activate in measures when needed)

### Phase 2: Data Quality Measures (15 minutes)

Add these DAX measures to monitor data quality:

```dax
// Data Quality Monitoring
Leasing Data Quality % = 
VAR TotalRecords = COUNTROWS(fact_leasingactivity)
VAR ValidRecords = 
    CALCULATE(
        COUNTROWS(fact_leasingactivity),
        NOT ISBLANK(RELATED(dim_commcustomer[tenant id]))
    )
RETURN
    DIVIDE(ValidRecords, TotalRecords, 0) * 100

Orphaned Leasing Records = 
CALCULATE(
    COUNTROWS(fact_leasingactivity),
    ISBLANK(RELATED(dim_commcustomer[tenant id]))
)

Total Leasing Deals = 
CALCULATE(
    COUNTROWS(fact_leasingactivity),
    NOT ISBLANK(RELATED(dim_commcustomer[tenant id]))
)
```

### Phase 3: Core Leasing Measures (20 minutes)

Add these essential leasing pipeline measures:

```dax
// Pipeline Analytics
Active Deals Count = 
CALCULATE(
    COUNTROWS(fact_leasingactivity),
    fact_leasingactivity[Deal Stage] IN {"Lead", "Tour", "Proposal", "Negotiation"},
    NOT ISBLANK(RELATED(dim_commcustomer[tenant id]))
)

Executed Deals Count = 
CALCULATE(
    COUNTROWS(fact_leasingactivity),
    fact_leasingactivity[Deal Stage] = "Executed",
    NOT ISBLANK(RELATED(dim_commcustomer[tenant id]))
)

Pipeline Square Footage = 
CALCULATE(
    SUM(fact_leasingactivity[dArea]),
    fact_leasingactivity[Deal Stage] IN {"Lead", "Tour", "Proposal", "Negotiation"},
    NOT ISBLANK(RELATED(dim_commcustomer[tenant id]))
)

Deal Conversion Rate = 
VAR ProposalCount = 
    CALCULATE(
        COUNTROWS(fact_leasingactivity),
        fact_leasingactivity[Deal Stage] = "Proposal",
        NOT ISBLANK(RELATED(dim_commcustomer[tenant id]))
    )
VAR ExecutedCount = 
    CALCULATE(
        COUNTROWS(fact_leasingactivity),
        fact_leasingactivity[Deal Stage] = "Executed",
        NOT ISBLANK(RELATED(dim_commcustomer[tenant id]))
    )
RETURN
    DIVIDE(ExecutedCount, ProposalCount, 0)

Average Deal Size SF = 
CALCULATE(
    AVERAGE(fact_leasingactivity[dArea]),
    NOT ISBLANK(RELATED(dim_commcustomer[tenant id]))
)

Pipeline Value (Annual Rent) = 
CALCULATE(
    SUM(fact_leasingactivity[Starting Rent]) * 12,
    fact_leasingactivity[Deal Stage] IN {"Lead", "Tour", "Proposal", "Negotiation"},
    NOT ISBLANK(RELATED(dim_commcustomer[tenant id]))
)
```

### Phase 4: Testing and Validation (15 minutes)

#### Test 1: Basic Filtering
1. Create a simple table visual with:
   - Rows: `fact_leasingactivity[Deal Stage]`
   - Values: `Total Leasing Deals`
2. **Expected Result**: 5 deal stages with reasonable counts

#### Test 2: Property Relationship (via Tenant)
1. Add `dim_property[property name]` to the table
2. **Expected Result**: Property names should appear for most deals

#### Test 3: Date Filtering
1. Add a date slicer connected to `dim_date[date]`
2. Filter to current year
3. **Expected Result**: Measures should update correctly

#### Test 4: Data Quality Check
1. Create a card visual with `Leasing Data Quality %`
2. **Expected Result**: Should show ~98% (97.9% tenant match rate)

## Business Value and Use Cases

### Dashboard Applications
1. **Leasing Pipeline Dashboard**
   - Deal stages funnel visualization
   - Conversion rates by property/tenant type
   - Pipeline value and timing forecasts

2. **Leasing Activity Analysis**
   - New lease vs renewal analysis
   - Deal size distribution by property
   - Seasonal leasing patterns

3. **Property Performance Comparison**
   - Leasing velocity by property
   - Average deal terms and pricing
   - Time to close analysis

### Complementary to Existing Model
- **Amendment Tables**: Current occupancy and rent roll (actual)
- **Leasing Activity Table**: Pipeline and future deals (forecast)
- **Combined Power**: Complete leasing lifecycle visibility

## Data Refresh Configuration

### Refresh Frequency
- **Recommended**: Daily (same as existing tables)
- **Minimum**: Weekly for meaningful pipeline changes

### Dependencies
- Must refresh **after** `dim_commcustomer` to maintain relationships
- No impact on existing table refresh order

## Troubleshooting Guide

### Issue: High Orphaned Records Count
**Cause**: New tenant codes not yet in `dim_commcustomer`
**Solution**: 
```dax
// Filter out orphaned records in measures
Valid Leasing Deals = 
CALCULATE(
    COUNTROWS(fact_leasingactivity),
    NOT ISBLANK(RELATED(dim_commcustomer[tenant id]))
)
```

### Issue: Date Relationships Not Working
**Cause**: Date format compatibility
**Solution**: Check Power Query date conversion in Step 1.2

### Issue: Measures Show Blank
**Cause**: Inactive relationships or missing filters
**Solution**: Verify relationship directions and add proper filters

## Performance Considerations

### Table Size Impact
- **fact_leasingactivity**: 2,675 rows (small)
- **Performance Impact**: Minimal - table is lightweight
- **Optimization**: Pre-aggregated columns added in Power Query

### Query Performance
- **New Relationships**: Single-direction only (optimal)
- **Measure Performance**: Fast due to small table size
- **Memory Usage**: Negligible increase

## Security and Access Control

### Row-Level Security (RLS)
If existing model uses property-based RLS:
```dax
// Add to existing property RLS rule
[property id] IN (
    SELECTCOLUMNS(
        FILTER(
            fact_leasingactivity,
            RELATED(dim_commcustomer[property id]) = [property id]
        ),
        "PropertyID", RELATED(dim_commcustomer[property id])
    )
)
```

## Deployment Checklist

- [ ] **Phase 1**: Table loaded and relationships created
- [ ] **Phase 2**: Data quality measures implemented  
- [ ] **Phase 3**: Core leasing measures added
- [ ] **Phase 4**: Testing completed successfully
- [ ] **Refresh Schedule**: Updated to include new table
- [ ] **Documentation**: Updated data dictionary
- [ ] **User Training**: Key stakeholders notified of new capabilities
- [ ] **Monitoring**: Data quality measures added to admin dashboard

## Success Metrics

### Technical Success
- [ ] 97%+ data quality score maintained
- [ ] All relationships working correctly
- [ ] No impact on existing amendment logic
- [ ] Dashboard load times < 10 seconds

### Business Success
- [ ] Leasing team can track pipeline effectively
- [ ] Property managers have deal visibility
- [ ] Executive dashboards show leasing KPIs
- [ ] Forecasting accuracy improved with pipeline data

## Contact and Support

For implementation questions:
- **Technical Issues**: Reference this guide and existing documentation
- **Business Logic**: Validate against Yardi native reports
- **Performance**: Monitor using built-in data quality measures

---

**Implementation Time Estimate**: 80 minutes total
**Complexity Level**: Medium (requires relationship management)
**Risk Level**: Low (no existing functionality affected)
**Business Impact**: High (significant new analytical capabilities)