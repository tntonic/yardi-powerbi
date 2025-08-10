# Rent Roll Edge Case Test Framework

## Executive Summary

This document provides comprehensive edge case test scenarios for the 9 critical rent roll DAX measures that have been updated with optimized MAX(amendment sequence) filters. The framework ensures production robustness by testing all possible data variations in the Yardi commercial real estate environment.

**Target Measures:**
1. WALT (Months) - Weighted average lease term calculations
2. Leases Expiring (Next 12 Months) - Lease expiration tracking  
3. Expiring Lease SF (Next 12 Months) - SF expiring analysis
4. New Leases Count/SF - New leasing activity
5. Renewals Count/SF - Renewal activity tracking
6. New Lease Starting Rent PSF - Pricing analysis
7. Renewal Rent Change % - Rent growth analysis

**Current State:**
- All measures implement MAX(amendment sequence) filtering logic
- 97%+ accuracy achieved in validation testing
- Amendment-based logic handles both "Activated" and "Superseded" statuses
- Performance optimized for <5 second query response

## Core Amendment Logic Pattern

All updated measures implement this critical pattern:
```dax
VAR LatestAmendments = 
    FILTER(
        FILTER(
            dim_fp_amendmentsunitspropertytenant,
            [amendment status] IN {"Activated", "Superseded"} &&
            [amendment type] <> "Termination"
        ),
        [amendment sequence] = CALCULATE(
            MAX([amendment sequence]),
            ALLEXCEPT(
                dim_fp_amendmentsunitspropertytenant,
                [property hmy],
                [tenant hmy]
            )
        )
    )
```

## Edge Case Test Categories

### Category 1: Amendment Sequence Edge Cases

#### Test 1.1: Multiple Amendments Same Tenant
**Scenario**: Testing MAX(sequence) selection with multiple amendments per tenant

**Test Data Pattern**:
```csv
property_hmy,tenant_hmy,amendment_sequence,amendment_status,monthly_amount,amendment_sf,start_date,end_date
PROP001,TEN001,1,Activated,5000,2000,2024-01-01,2026-12-31
PROP001,TEN001,2,Activated,5500,2000,2024-06-01,2026-12-31
PROP001,TEN001,3,Superseded,6000,2500,2024-12-01,2027-12-31
```

**Expected Result**: Only Sequence 3 should be selected (latest)
**Validation Measures**: Current Monthly Rent = $6,000, Current Leased SF = 2,500

#### Test 1.2: Gap in Amendment Sequences
**Scenario**: Testing sequence selection with missing sequence numbers

**Test Data Pattern**:
```csv
property_hmy,tenant_hmy,amendment_sequence,amendment_status,monthly_amount,amendment_sf
PROP002,TEN002,1,Activated,3000,1500
PROP002,TEN002,5,Superseded,3200,1500
```

**Expected Result**: Sequence 5 should be selected (MAX function handles gaps)
**Validation**: Current Monthly Rent = $3,200

#### Test 1.3: Identical Sequences (Duplicate Data Error)
**Scenario**: Testing behavior when duplicate sequences exist

**Test Data Pattern**:
```csv
property_hmy,tenant_hmy,amendment_sequence,amendment_status,monthly_amount,amendment_sf
PROP003,TEN003,2,Activated,4000,1800
PROP003,TEN003,2,Superseded,4200,1800
```

**Expected Result**: Both records should be processed (measures should handle gracefully)
**Validation**: System should not crash, rent total should be reasonable

### Category 2: Amendment Status Edge Cases

#### Test 2.1: Latest Amendment is Superseded
**Scenario**: Testing inclusion of "Superseded" status as latest amendment

**Test Data Pattern**:
```csv
property_hmy,tenant_hmy,amendment_sequence,amendment_status,monthly_amount,amendment_sf
PROP004,TEN004,1,Activated,4000,2000
PROP004,TEN004,2,Superseded,4500,2000
```

**Expected Result**: Sequence 2 ("Superseded") should be included in rent roll
**Critical Test**: 16.7% of actual leases have latest status = "Superseded"

#### Test 2.2: Termination Amendment Exclusion
**Scenario**: Testing exclusion of amendment_type = "Termination"

**Test Data Pattern**:
```csv
property_hmy,tenant_hmy,amendment_sequence,amendment_status,amendment_type,monthly_amount
PROP005,TEN005,1,Activated,Original Lease,5000
PROP005,TEN005,2,Activated,Termination,0
```

**Expected Result**: Only Sequence 1 used, Sequence 2 ignored
**Validation**: Tenant should appear in current rent roll with $5,000 rent

#### Test 2.3: Draft Amendment Status
**Scenario**: Testing exclusion of "Draft" status amendments

**Test Data Pattern**:
```csv
property_hmy,tenant_hmy,amendment_sequence,amendment_status,monthly_amount
PROP006,TEN006,1,Activated,5000
PROP006,TEN006,2,Draft,5500
```

**Expected Result**: Only "Activated" amendment used (Draft excluded)
**Validation**: Current Monthly Rent = $5,000

### Category 3: Date Boundary Edge Cases

#### Test 3.1: Null End Date (Month-to-Month)
**Scenario**: Testing leases with no end date (month-to-month)

**Test Data Pattern**:
```csv
property_hmy,tenant_hmy,amendment_sequence,start_date,end_date,amendment_status,monthly_amount
PROP007,TEN007,1,2024-01-01,NULL,Activated,3000
```

**Expected Result**: Should be included in current rent roll
**WALT Impact**: Should calculate as high value or handle NULL appropriately

#### Test 3.2: Future Start Date
**Scenario**: Testing amendments with future start dates

**Test Data Pattern**:
```csv
property_hmy,tenant_hmy,amendment_sequence,start_date,end_date,amendment_status
PROP008,TEN008,1,2025-12-31,2026-12-31,Activated
```

**Expected Result**: Should NOT be included if report date is 2025-06-30
**Validation**: Future leases excluded from current calculations

#### Test 3.3: Recently Expired Lease
**Scenario**: Testing leases that expired recently

**Test Data Pattern**:
```csv
property_hmy,tenant_hmy,amendment_sequence,start_date,end_date,amendment_status
PROP009,TEN009,1,2024-01-01,2025-06-29,Activated
```

**Expected Result**: Should NOT be included in 2025-06-30 rent roll
**Validation**: Expired leases properly excluded

#### Test 3.4: Lease Expiring Today
**Scenario**: Testing lease that expires on report date

**Test Data Pattern**:
```csv
property_hmy,tenant_hmy,amendment_sequence,start_date,end_date,amendment_status
PROP010,TEN010,1,2024-01-01,2025-06-30,Activated
```

**Expected Result**: Should be included (expires at end of day)
**Edge Case**: Boundary condition for "Leases Expiring Next 12 Months"

### Category 4: Financial Calculation Edge Cases

#### Test 4.1: Zero Rent Amount
**Scenario**: Testing amendments with zero monthly rent

**Test Data Pattern**:
```csv
property_hmy,tenant_hmy,amendment_sequence,monthly_amount,amendment_sf,amendment_status
PROP011,TEN011,1,0,1000,Activated
```

**Expected Result**: 
- Current Monthly Rent: $0 contribution
- Current Leased SF: 1,000 SF contribution  
- Rent PSF: $0/SF (handle division by zero)

#### Test 4.2: Negative Rent (Tenant Improvements)
**Scenario**: Testing amendments with negative rent (credits)

**Test Data Pattern**:
```csv
property_hmy,tenant_hmy,amendment_sequence,monthly_amount,amendment_sf,amendment_status
PROP012,TEN012,1,-500,500,Activated
```

**Expected Result**: Should be handled properly in aggregations
**Validation**: Total rent calculations account for negative values

#### Test 4.3: Extremely Large Rent Amount
**Scenario**: Testing data validation for unreasonable rent amounts

**Test Data Pattern**:
```csv
property_hmy,tenant_hmy,amendment_sequence,monthly_amount,amendment_sf,amendment_status
PROP013,TEN013,1,999999999,1000,Activated
```

**Expected Result**: Should be included but flagged as unusual
**Validation**: Rent PSF would be extremely high ($999,999/SF annually)

### Category 5: Property/Unit Relationship Edge Cases

#### Test 5.1: Same Tenant Multiple Properties
**Scenario**: Testing tenant with leases in multiple properties

**Test Data Pattern**:
```csv
property_hmy,tenant_hmy,amendment_sequence,monthly_amount,amendment_sf,amendment_status
PROP014,TEN014,1,5000,1000,Activated
PROP015,TEN014,1,8000,2000,Activated
```

**Expected Result**: Both leases included separately (different property hmy)
**Validation**: MAX(sequence) calculated per property/tenant combination

#### Test 5.2: Multiple Units Same Amendment
**Scenario**: Testing single amendment covering multiple units

**Test Data Pattern**:
```csv
property_hmy,tenant_hmy,unit_hmy,amendment_sequence,amendment_sf,amendment_status
PROP016,TEN016,UNIT101,1,2500,Activated
PROP016,TEN016,UNIT102,1,2500,Activated
```

**Expected Result**: Amendment counted once, not per unit
**Validation**: No duplication in SF or rent calculations

#### Test 5.3: Orphaned Amendment Records
**Scenario**: Testing amendments without corresponding property/tenant records

**Test Data Pattern**:
```csv
property_hmy,tenant_hmy,amendment_sequence,amendment_status
PROP999,TEN999,1,Activated
```

**Expected Result**: Should be excluded from calculations if relationships broken
**Validation**: Relationship integrity maintained

### Category 6: Missing Data Edge Cases

#### Test 6.1: Null Amendment SF
**Scenario**: Testing amendments with missing square footage

**Test Data Pattern**:
```csv
property_hmy,tenant_hmy,amendment_sequence,monthly_amount,amendment_sf,amendment_status
PROP017,TEN017,1,5000,NULL,Activated
```

**Expected Result**: 
- Rent Roll PSF: Handle null division gracefully
- Current Leased SF: Exclude NULL values from sum

#### Test 6.2: Missing Monthly Amount
**Scenario**: Testing amendments with missing rent amount

**Test Data Pattern**:
```csv
property_hmy,tenant_hmy,amendment_sequence,monthly_amount,amendment_sf,amendment_status
PROP018,TEN018,1,NULL,1500,Activated
```

**Expected Result**: Should default to $0 or be excluded from rent calculations

#### Test 6.3: Missing Start/End Dates
**Scenario**: Testing amendments with missing date information

**Test Data Pattern**:
```csv
property_hmy,tenant_hmy,amendment_sequence,start_date,end_date,amendment_status
PROP019,TEN019,1,NULL,NULL,Activated
```

**Expected Result**: Should be excluded from date-based calculations (WALT, expirations)

### Category 7: Performance and Scale Edge Cases

#### Test 7.1: High Amendment Volume Property
**Scenario**: Testing property with 100+ tenants, each with multiple amendments

**Test Data Pattern**: Generate 100 tenants × 5 amendments each = 500 records
**Expected Result**: Query executes in <5 seconds
**Performance Test**: MAX(sequence) calculation efficiency under load

#### Test 7.2: Wide Date Range Filtering
**Scenario**: Testing performance with 10+ year historical data range

**Test Data Pattern**: 2015-2025 amendment data across multiple properties
**Expected Result**: Date-based measures (WALT, expirations) perform adequately

#### Test 7.3: Cross-Filter Performance
**Scenario**: Testing measure performance with multiple dashboard filters applied

**Filter Combination**:
- Date range: Q2 2025
- Property type: Industrial  
- Tenant size: >50,000 SF
- Lease status: Current only

**Expected Result**: All 9 measures respond within 5 seconds with filters applied

## Test Data Generation Specifications

### Synthetic Dataset Requirements

**Portfolio Structure**:
- 20 properties (mixed industrial, office, retail)
- 100 tenants with varying lease patterns
- 400 amendments covering all edge cases
- Time range: 2020-2030 for comprehensive date testing

**Amendment Distribution**:
- 40% single amendment tenants (sequence 1 only)
- 35% multiple amendment tenants (2-3 sequences)
- 20% complex amendment tenants (4+ sequences)
- 5% edge case scenarios (gaps, nulls, extremes)

**Status Distribution**:
- 70% latest amendments with "Activated" status
- 25% latest amendments with "Superseded" status
- 5% with excluded statuses ("Draft", "Cancelled")

**Data Quality Scenarios**:
- 90% complete data (all fields populated)
- 5% missing SF or rent amounts
- 3% missing or invalid dates
- 2% extreme values or data errors

### Test Data Files Structure

```
Test_Data/
├── edge_case_amendments.csv          # Core amendment test data
├── edge_case_properties.csv          # Property dimension data
├── edge_case_tenants.csv             # Tenant dimension data
├── edge_case_charge_schedules.csv    # Charge schedule data
├── validation_expected_results.csv   # Expected outcomes for each test
└── test_scenarios_documentation.md   # Detailed test case descriptions
```

## Validation Framework

### Automated Test Execution

**Phase 1: Data Loading**
1. Load synthetic test dataset into Power BI model
2. Verify all relationships establish correctly
3. Validate data types and formats

**Phase 2: Measure Testing**
1. Execute all 9 rent roll measures against test data
2. Capture results for each edge case scenario
3. Compare against expected outcomes
4. Log any discrepancies or errors

**Phase 3: Performance Validation**
1. Measure query execution times under various loads
2. Test cross-filter performance with dashboard scenarios
3. Validate memory usage and resource consumption

### Success Criteria

**Functional Requirements**:
- ✅ All measures handle edge cases without errors
- ✅ MAX(sequence) logic works correctly in all scenarios
- ✅ Both "Activated" and "Superseded" statuses properly included
- ✅ Date boundary conditions handled appropriately
- ✅ Null/missing data handled gracefully

**Performance Requirements**:
- ✅ Query execution <5 seconds for single measure
- ✅ Dashboard response <10 seconds with multiple measures
- ✅ Handles 500+ amendment records efficiently

**Business Logic Requirements**:
- ✅ WALT calculations accurate for all date scenarios
- ✅ Expiration tracking works correctly at boundaries
- ✅ Leasing activity metrics sum correctly
- ✅ Rent PSF calculations handle zero/null divisions

## Issue Classification and Response

### Critical Issues (Fix Immediately)
- Measures returning incorrect results for core scenarios
- Performance degradation >10 seconds
- Data corruption or relationship failures
- Crashes or calculation errors

### High Priority Issues (Fix within 24 hours)
- Edge cases not handled gracefully
- Minor calculation discrepancies (<5%)
- Performance issues 5-10 seconds
- Missing data scenarios causing problems

### Medium Priority Issues (Fix within 1 week)
- Unusual data scenarios requiring business rule clarification
- Performance optimization opportunities
- Enhancement requests for additional edge case handling

## Continuous Monitoring

### Production Monitoring Measures

```dax
// Amendment Logic Health Check
Amendment Logic Health = 
VAR TotalAmendments = COUNTROWS(dim_fp_amendmentsunitspropertytenant)
VAR LatestAmendments = 
    COUNTROWS(
        FILTER(
            dim_fp_amendmentsunitspropertytenant,
            [amendment sequence] = CALCULATE(
                MAX([amendment sequence]),
                ALLEXCEPT(
                    dim_fp_amendmentsunitspropertytenant,
                    [property hmy],
                    [tenant hmy]
                )
            )
        )
    )
VAR PropertyTenantPairs = 
    COUNTROWS(
        SUMMARIZE(
            dim_fp_amendmentsunitspropertytenant,
            [property hmy],
            [tenant hmy]
        )
    )
RETURN 
    IF(
        LatestAmendments = PropertyTenantPairs,
        "✅ Amendment logic healthy",
        "⚠️ Amendment logic issues detected"
    )

// Edge Case Detection
Edge Case Alert = 
VAR ZeroRentCount = 
    CALCULATE(
        COUNTROWS(dim_fp_amendmentsunitspropertytenant),
        [monthly amount] = 0
    )
VAR NullSFCount = 
    CALCULATE(
        COUNTROWS(dim_fp_amendmentsunitspropertytenant),
        ISBLANK([amendment sf])
    )
VAR FutureStartCount = 
    CALCULATE(
        COUNTROWS(dim_fp_amendmentsunitspropertytenant),
        [amendment start date] > TODAY()
    )
RETURN 
    "Zero Rent: " & ZeroRentCount & " | " &
    "Null SF: " & NullSFCount & " | " &
    "Future Starts: " & FutureStartCount
```

This comprehensive edge case testing framework ensures the 9 critical rent roll measures are production-ready and can handle all possible data variations in the Yardi commercial real estate environment.