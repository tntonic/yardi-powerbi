# fact_leasingactivity Integration Analysis

## Executive Summary

The fact_leasingactivity table contains detailed leasing pipeline and transaction data with 2,675 records covering all stages of the leasing process from Lead to Executed deals. This analysis provides the optimal integration approach for the existing 32-table Yardi Power BI data model.

## Table Structure Analysis

### Primary Key and Core Fields
- **Primary Key**: `Deal HMY` (unique deal identifier)
- **Deal Stage**: Lead → Tour → Proposal → Negotiation → Executed / Dead Deal
- **Proposal Types**: New Lease (1,022 records), Renewal (961 records), Expansion (149 records), etc.
- **Business Workflow**: Complete leasing funnel from prospecting to execution

### Key Relationship Fields
| Field | Purpose | Data Quality |
|-------|---------|--------------|
| Deal HMY | Primary key | ✅ Unique |
| Tenant HMY | Tenant foreign key | ❌ 99.8% orphaned |
| Tenant Code | Tenant business key | ✅ 97.9% match rate |
| dtStartDate | Lease start date | ✅ Valid format |
| dtEndDate | Lease end date | ✅ Valid format |
| hCommamendment | Amendment reference | ⚠️ Needs validation |
| dArea | Square footage | ✅ Numeric |

### Financial and Metrics Fields
- **Rent Fields**: Starting Rent, Escalation Rate, Average Rent
- **Financial NPV**: Total NPV, Annual NPV, IRR, NER calculations
- **Costs**: TI Allowance, Commissions, Free Rent, Other Costs
- **Terms**: Term months, Break Even Month, Free Rent Months

## Relationship Design

### 1. Primary Tenant Relationship
```
fact_leasingactivity[Tenant Code] → dim_commcustomer[tenant code]
- Cardinality: Many-to-One (M:1)
- Cross Filter Direction: Single (fact → dim)
- Match Rate: 97.9% (505 of 516 tenant codes)
- Data Quality: 11 orphaned tenant codes (t0001675-t0001685)
```

### 2. Property Relationship (Indirect)
```
dim_commcustomer[property id] → dim_property[property id]
- Achieved via tenant relationship
- Cardinality: Many-to-One (M:1)
- Cross Filter Direction: Single (dim → dim)
- Coverage: Full property coverage via tenant linkage
```

### 3. Date Relationships
```
fact_leasingactivity[dtStartDate] → dim_date[date]
fact_leasingactivity[dtEndDate] → dim_date[date]
- Cardinality: Many-to-One (M:1)
- Cross Filter Direction: Single (fact → dim)
- Format: Standard date format compatible with Power BI
```

### 4. Amendment Relationship (Optional)
```
fact_leasingactivity[hCommamendment] → dim_fp_amendmentsunitspropertytenant[amendment hmy]
- Cardinality: Many-to-One (M:1)
- Cross Filter Direction: Single (fact → dim)
- Purpose: Link leasing deals to executed amendments
- Coverage: Partial (only for executed deals with amendments)
```

## Data Quality Issues and Solutions

### Issue 1: Orphaned Tenant References
**Problem**: 11 tenant codes in fact_leasingactivity don't exist in dim_commcustomer
**Tenant Codes**: t0001675-t0001685
**Impact**: 2.1% of leasing records (approximately 56 rows)
**Solution**: 
- Create placeholder tenant records in dim_commcustomer
- OR filter out orphaned records during data refresh
- OR leave as-is and handle in DAX with BLANK() for missing relationships

### Issue 2: Tenant HMY vs Tenant Code Mismatch
**Problem**: Tenant HMY field has 99.8% orphan rate
**Root Cause**: Different ID numbering systems between tables
**Solution**: Use Tenant Code as the relationship key instead of Tenant HMY

### Issue 3: Amendment Link Validation
**Problem**: hCommamendment field relationship needs validation
**Solution**: Validate whether hCommamendment values exist in amendment table

## Integration Strategy

### Phase 1: Basic Integration
1. **Add fact_leasingactivity to data model**
2. **Create tenant relationship**: fact_leasingactivity[Tenant Code] → dim_commcustomer[tenant code]
3. **Create date relationships**: dtStartDate and dtEndDate → dim_date
4. **Test basic functionality** with simple measures

### Phase 2: Data Quality Enhancement
1. **Handle orphaned tenant codes** (decision needed on approach)
2. **Validate amendment relationship** and create if viable
3. **Add data quality measures** to monitor orphaned records

### Phase 3: Advanced Analytics
1. **Create leasing funnel measures** (conversion rates by stage)
2. **Develop pipeline analytics** (deals by stage, size, type)
3. **Build forecasting measures** (projected lease execution)

## Power BI Implementation

### Relationship Configuration
```sql
-- Primary tenant relationship (M:1)
fact_leasingactivity[Tenant Code] → dim_commcustomer[tenant code]
Cardinality: Many-to-One
Cross Filter: Single Direction (Left to Right)
Active: Yes

-- Date relationships (M:1)
fact_leasingactivity[dtStartDate] → dim_date[date]
fact_leasingactivity[dtEndDate] → dim_date[date]
Cardinality: Many-to-One
Cross Filter: Single Direction (Left to Right)
Active: Yes (both can be active for different purposes)
```

### Data Transformation Requirements
```m
// Power Query M code for fact_leasingactivity cleanup
let
    Source = Csv.Document(File.Contents("fact_leasingactivity.csv")),
    Headers = Table.PromoteHeaders(Source),
    
    // Clean tenant codes - remove empty strings
    CleanTenantCode = Table.ReplaceValue(Headers, "", null, Replacer.ReplaceValue, {"Tenant Code"}),
    
    // Convert dates to proper Date type
    ConvertDates = Table.TransformColumnTypes(CleanTenantCode, {
        {"dtStartDate", type date},
        {"dtEndDate", type date},
        {"dtcreated", type datetime},
        {"dtlastmodified", type datetime}
    }),
    
    // Convert numeric fields
    ConvertNumeric = Table.TransformColumnTypes(ConvertDates, {
        {"Deal HMY", Int64.Type},
        {"Tenant HMY", Int64.Type},
        {"Starting Rent", type number},
        {"Escalation Rate", type number},
        {"dArea", type number},
        {"iTerm", Int64.Type}
    }),
    
    // Add helpful calculated columns
    AddCalculatedColumns = Table.AddColumn(ConvertNumeric, "Deal Stage Order", 
        each if [Deal Stage] = "Lead" then 1
        else if [Deal Stage] = "Tour" then 2  
        else if [Deal Stage] = "Proposal" then 3
        else if [Deal Stage] = "Negotiation" then 4
        else if [Deal Stage] = "Executed" then 5
        else if [Deal Stage] = "Dead Deal" then 0
        else 9),
        
    // Add lease term category
    AddTermCategory = Table.AddColumn(AddCalculatedColumns, "Term Category",
        each if [iTerm] = null then "Unknown"
        else if [iTerm] <= 12 then "Short Term (≤12 months)"
        else if [iTerm] <= 36 then "Medium Term (13-36 months)" 
        else if [iTerm] <= 60 then "Long Term (37-60 months)"
        else "Extended Term (>60 months)")
        
in
    AddTermCategory
```

## Compatibility with Existing Model

### Amendment-Based Logic Preservation
The fact_leasingactivity integration will **complement** (not replace) the existing amendment-based rent roll logic:

- **Amendment Table**: Continue using for current rent roll, occupancy, and financial reporting
- **Leasing Activity Table**: Use for pipeline analysis, deal flow, and forward-looking metrics
- **Relationship**: Both tables can connect via hCommamendment for executed deals

### Key DAX Considerations
```dax
// Ensure proper filter context for leasing measures
Leasing Deals Count = 
CALCULATE(
    COUNTROWS(fact_leasingactivity),
    fact_leasingactivity[Tenant Code] <> BLANK()  // Exclude orphaned records
)

// Deal conversion rate
Proposal to Executed Rate = 
DIVIDE(
    CALCULATE(COUNTROWS(fact_leasingactivity), fact_leasingactivity[Deal Stage] = "Executed"),
    CALCULATE(COUNTROWS(fact_leasingactivity), fact_leasingactivity[Deal Stage] = "Proposal")
)
```

## Recommended Next Steps

1. **Immediate**: Implement basic tenant and date relationships
2. **Short-term**: Validate amendment relationship and handle data quality issues  
3. **Medium-term**: Develop leasing-specific DAX measures and dashboard components
4. **Long-term**: Consider adding this table to the automated validation framework

## Risk Assessment

- **Low Risk**: Basic tenant and date relationships (high confidence)
- **Medium Risk**: Amendment relationship validation needed
- **Low Risk**: Data quality issues are manageable (2.1% orphan rate)
- **No Risk**: Integration won't conflict with existing amendment-based logic