# Edge Case Test Execution Guide
# Comprehensive Testing Protocol for 9 Critical Rent Roll DAX Measures
# =====================================================

## Overview

This guide provides step-by-step instructions for executing comprehensive edge case testing of the updated rent roll DAX measures. The testing framework validates all possible data variations and ensures production robustness.

**Target Measures for Testing:**
1. WALT (Months)
2. Leases Expiring (Next 12 Months)
3. Expiring Lease SF (Next 12 Months)
4. New Leases Count/SF
5. Renewals Count/SF  
6. New Lease Starting Rent PSF
7. Renewal Rent Change %

## Pre-Test Setup Requirements

### 1. Test Environment Preparation

#### Power BI Environment Setup
```
Test Environment Specifications:
- Power BI Desktop: Latest version
- Available RAM: Minimum 8GB (16GB recommended)
- Test Workspace: Dedicated workspace for edge case testing
- Backup: Current production model backed up
```

#### Test Data Loading
```powershell
# Load all edge case test datasets
Copy-Item "edge_case_amendments.csv" -Destination "PowerBI_TestData/"
Copy-Item "edge_case_properties.csv" -Destination "PowerBI_TestData/"
Copy-Item "edge_case_tenants.csv" -Destination "PowerBI_TestData/"
Copy-Item "edge_case_charge_schedules.csv" -Destination "PowerBI_TestData/"
Copy-Item "date_boundary_test_scenarios.csv" -Destination "PowerBI_TestData/"
Copy-Item "financial_calculation_test_scenarios.csv" -Destination "PowerBI_TestData/"
```

### 2. Baseline Performance Measurement

#### Performance Baseline Setup
```dax
// Create baseline performance measures for comparison
Baseline_Performance_Current_Rent = 
VAR StartTime = NOW()
VAR Result = [Current Monthly Rent]
VAR EndTime = NOW()
VAR ExecutionTimeSeconds = DATEDIFF(StartTime, EndTime, SECOND)
RETURN 
    "Baseline: " & FORMAT(Result, "$#,##0") & 
    " | Time: " & ExecutionTimeSeconds & "s"

Baseline_Performance_WALT = 
VAR StartTime = NOW()
VAR Result = [WALT (Months)]
VAR EndTime = NOW()
VAR ExecutionTimeSeconds = DATEDIFF(StartTime, EndTime, SECOND)
RETURN 
    "Baseline WALT: " & FORMAT(Result, "0.0") & " months" &
    " | Time: " & ExecutionTimeSeconds & "s"
```

## Test Execution Phases

### Phase 1: Amendment Sequence Logic Testing

#### Test 1.1: Multiple Amendment Sequence Validation
```
Objective: Verify MAX(sequence) logic selects latest amendments correctly
Test Data: edge_case_amendments.csv (rows 1001-1007)
Expected Results: validation_expected_results.csv (Multiple_Amendments scenarios)

Execution Steps:
1. Load test data into Power BI model
2. Create test visual filtering to PROP001, TEN001
3. Execute DAX validation measures:
   - [Amendment_Sequence_Test_PROP001]
4. Verify result: "Sequence: 3 | Rent: $6,000 | SF: 2,500"
5. Document any deviations

Pass/Fail Criteria:
✅ PASS: Only sequence 3 selected, rent = $6,000, SF = 2,500
❌ FAIL: Wrong sequence selected or incorrect aggregation
```

#### Test 1.2: Amendment Sequence Gap Handling
```
Objective: Verify MAX() function handles sequence gaps correctly
Test Data: PROP002, TEN002 (sequences 1 and 5)
Expected: Sequence 5 selected ($3,200 rent)

Execution:
1. Execute [Amendment_Gap_Test_PROP002]
2. Verify "Gap Test - Sequence: 5 | Rent: $3,200"
3. Confirm no errors with missing sequences 2-4
```

#### Test 1.3: Duplicate Sequence Handling
```
Objective: Test behavior with duplicate sequence numbers
Test Data: PROP003, TEN003 (two records with sequence 2)
Expected: Both records processed gracefully

Execution:
1. Filter to PROP003, TEN003
2. Verify total rent and SF aggregation
3. Ensure no calculation errors or duplications
```

### Phase 2: Amendment Status Logic Testing

#### Test 2.1: Superseded Status Inclusion
```
Objective: Verify "Superseded" status included in current rent roll
Test Data: PROP004, TEN004
Expected: Latest amendment (sequence 2, Superseded status) selected

Execution Steps:
1. Execute [Superseded_Status_Test_PROP004]
2. Verify result: "Status: Superseded | Rent: $4,500"
3. Confirm Superseded amendments appear in current rent roll

Critical Validation:
- Superseded amendments must be included (not excluded)
- This tests the IN {"Activated", "Superseded"} logic
```

#### Test 2.2: Termination Amendment Exclusion
```
Objective: Verify Termination amendments properly excluded
Test Data: PROP005, TEN005
Expected: Termination amendment (sequence 2) excluded

Execution:
1. Execute [Termination_Exclusion_Test_PROP005]  
2. Verify "Total: 2 | Included: 1 | Rent: $5,000"
3. Confirm termination amendments don't appear in rent roll
```

#### Test 2.3: Draft Status Exclusion
```
Objective: Verify Draft status amendments excluded
Test Data: PROP006, TEN006
Expected: Only Activated amendment (sequence 1) included

Execution:
1. Execute [Draft_Status_Test_PROP006]
2. Verify "Sequence: 1 (Draft excluded) | Rent: $5,000"
3. Confirm Draft amendments properly filtered out
```

### Phase 3: Date Boundary Testing

#### Test 3.1: Report Date Boundary Validation
```
Test Date Context: 2025-06-30 (simulated report date)
Objective: Verify date-based filtering accuracy

Test Cases:
A. Null End Date (Month-to-Month):
   - Execute [Null_End_Date_Test_PROP007]
   - Expected: "Included: Yes | Rent: $3,000 (NULL end date = MTM)"

B. Future Start Date:
   - Execute [Future_Start_Test_PROP008]
   - Expected: "Included: No (Future start date)"

C. Recently Expired:
   - Execute [Expired_Lease_Test_PROP009]  
   - Expected: "Included: No (Expired 2025-06-29)"

D. Expiring Today:
   - Execute [Expiring_Today_Test_PROP010]
   - Expected: "Current: Yes | Expiring List: Yes | Rent: $3,600"
```

#### Test 3.2: 12-Month Expiring List Validation
```
Objective: Test "Leases Expiring (Next 12 Months)" accuracy
Test Data: date_boundary_test_scenarios.csv

Key Test Cases:
- Expires_11_Months: Should be in expiring list
- Expires_12_Months: Should be in expiring list (boundary)
- Expires_13_Months: Should NOT be in expiring list
- Expires_365_Days: Should be in expiring list
- Expires_366_Days: Should NOT be in expiring list

Validation Query:
Filter leases expiring between 2025-06-30 and 2026-06-30
Verify boundary conditions handled correctly
```

#### Test 3.3: WALT Calculation Date Logic
```
Objective: Test WALT date calculations with edge cases
Test Focus: 
- Very short leases (1 day, 1 week, 1 month)
- Very long leases (10, 20, 50 years)
- Null end dates (month-to-month)

Execution:
1. Load date_boundary_test_scenarios.csv
2. Execute [WALT_Calculation_Test]
3. Verify weighted calculations handle extreme terms
4. Check null end date handling (should use high value or exclude)
```

### Phase 4: Financial Calculation Testing

#### Test 4.1: Zero and Negative Amount Handling
```
Objective: Test financial edge cases without calculation errors
Test Data: financial_calculation_test_scenarios.csv

Test Cases:
A. Zero Rent: Execute [Zero_Rent_Test_PROP011]
   Expected: "Rent: $0 | SF: 1,000 | PSF: $0.00"

B. Negative Rent: Execute [Negative_Rent_Test_PROP012]  
   Expected: "Base: $4,500 | Credit: $-500 | Net: $4,000"

C. Division by Zero: Execute [Zero_SF_Test_PROP013A]
   Expected: "Rent: $5,000 | SF: 0 | PSF: $0.00 (no error)"

Critical Validation:
- No #ERROR values in results
- Graceful handling of division by zero
- Negative amounts calculated correctly
```

#### Test 4.2: Rent PSF Calculation Consistency
```
Objective: Verify PSF calculations consistent across measures
Formula Validation:
- Annual PSF = (Monthly Rent × 12) ÷ Square Footage
- Monthly PSF = Monthly Rent ÷ Square Footage
- Rent Roll PSF = Current Monthly Rent × 12 ÷ Current Leased SF

Test Execution:
1. Filter to financial test scenarios
2. Compare PSF calculations across different measures
3. Verify rounding and precision consistency
4. Check extreme value handling (very high/low PSF)
```

#### Test 4.3: Complex Charge Structure Testing
```
Objective: Test multi-component rent calculations
Test Cases:
- Base rent only
- Base + CAM charges  
- Base + CAM + Insurance + Taxes (full service)
- Percentage rent calculations
- Tenant improvement credits

Validation:
- All charge components aggregate correctly
- Net effective rent calculated properly
- Credits applied in correct direction
```

### Phase 5: Leasing Activity Testing

#### Test 5.1: Activity Type Classification
```
Objective: Test leasing activity measures accuracy
Activity Period: 2024-06-01 to 2024-12-31

Test Cases:
A. New Leases: Execute [New_Leases_Activity_Test]
   Expected: "New Leases: 1 | SF: 2,000 | Starting PSF: $48.00"

B. Renewals: Execute [Renewals_Activity_Test]
   Expected: "Renewals: 2 | SF: [calculated] | Sample Rent Change: 5.6%"

Validation Points:
- Activity counts match filtered amendments
- Square footage aggregations correct
- Starting rent PSF calculated accurately  
- Rent change percentages calculated correctly
```

#### Test 5.2: Rent Change Calculation Testing
```
Objective: Verify renewal rent change calculations
Test Process:
1. Compare new amendment rent vs. prior amendment rent
2. Calculate percentage change: (New - Prior) / Prior × 100
3. Validate both increases and decreases handled correctly
4. Test edge cases (zero prior rent, negative changes)

Test Data: PROP023, TEN023
- Prior rent: $9,000/month  
- New rent: $9,500/month
- Expected change: +5.6%
```

### Phase 6: Performance and Scalability Testing

#### Test 6.1: Single Measure Performance Testing
```
Objective: Validate individual measure performance
Performance Targets:
- Execution time: <5 seconds
- Memory usage: Reasonable scaling
- No timeout errors

Test Process:
1. Load performance test dataset (1,000 amendments)
2. Execute each of the 9 measures individually
3. Record execution times using baseline performance measures
4. Progressively increase data volume (10K, 100K amendments)
5. Document performance degradation curve

Expected Results:
Measure | 1K | 10K | 100K | Pass/Fail
Current Monthly Rent | <2s | <3s | <5s | ✅
WALT (Months) | <3s | <4s | <6s | ✅
[Continue for all measures]
```

#### Test 6.2: Dashboard Integration Testing
```
Objective: Test measures in realistic dashboard environment
Test Setup:
1. Create dashboard with all 9 measures
2. Add property, tenant, and date filters
3. Include cross-filtering between visuals

Performance Test:
1. Dashboard initial load time: <10 seconds
2. Filter application response: <5 seconds  
3. Cross-filter interactions: <3 seconds
4. Simultaneous user load testing (if applicable)
```

#### Test 6.3: Large Dataset Stress Testing
```
Objective: Test measures with enterprise-scale data
Test Datasets:
- Small: 1,000 amendments
- Medium: 10,000 amendments  
- Large: 100,000 amendments
- Extreme: 1,000,000 amendments

Execution:
1. Generate or load large test datasets
2. Execute full measure battery
3. Monitor system resources (CPU, memory)
4. Document breaking points and degradation patterns
5. Verify accuracy maintained at scale
```

## Test Result Documentation

### Test Execution Tracking Sheet

```
Test_ID | Test_Category | Test_Description | Expected_Result | Actual_Result | Pass/Fail | Notes
T1.1    | Amendment_Seq | Multiple amendments MAX logic | Seq 3 selected | Seq 3 selected | ✅ PASS | Correct
T1.2    | Amendment_Seq | Sequence gap handling | Seq 5 selected | Seq 5 selected | ✅ PASS | Correct  
T2.1    | Status_Logic  | Superseded inclusion | Included | Included | ✅ PASS | Correct
T2.2    | Status_Logic  | Termination exclusion | Excluded | Excluded | ✅ PASS | Correct
T3.1    | Date_Boundary | Null end date MTM | Included | Included | ✅ PASS | Correct
T3.2    | Date_Boundary | Future start exclusion | Excluded | Excluded | ✅ PASS | Correct
[Continue for all test cases...]
```

### Performance Benchmark Tracking

```
Measure_Name | Baseline | 1K_Records | 10K_Records | 100K_Records | Performance_Grade
Current Monthly Rent | 1.2s | 1.5s | 2.8s | 4.2s | A (Good)
WALT (Months) | 2.1s | 2.5s | 4.1s | 7.8s | B (Acceptable)
Leases Expiring | 1.8s | 2.1s | 3.5s | 6.1s | A (Good)
[Continue for all measures...]
```

### Issue Tracking and Resolution

#### Critical Issues (Must Fix Before Production)
```
Issue_ID: C001
Description: Amendment sequence selection incorrect with duplicate sequences
Measure_Affected: All rent roll measures
Impact: High - Could result in wrong rent totals
Status: Open
Priority: Critical
Resolution_Target: Immediate
```

#### Performance Issues (Optimization Needed)
```
Issue_ID: P001  
Description: WALT calculation >10 seconds with 100K+ amendments
Measure_Affected: WALT (Months)
Impact: Medium - Acceptable for batch processing, slow for interactive
Status: Under Review
Priority: Medium
Resolution_Target: Next release
```

## Success Criteria and Sign-off

### Functional Success Criteria
- ✅ All 9 measures execute without errors across all edge cases
- ✅ Amendment sequence logic (MAX) works correctly in all scenarios
- ✅ Status filtering includes "Activated" and "Superseded", excludes others
- ✅ Date boundary conditions handled accurately (current vs. expired)
- ✅ Financial calculations handle zero, null, and negative values gracefully
- ✅ Leasing activity measures classify and calculate correctly
- ✅ WALT calculations weighted properly across all lease terms

### Performance Success Criteria  
- ✅ Single measure execution: <5 seconds up to 100K amendments
- ✅ Dashboard loading: <10 seconds with standard filters
- ✅ Interactive filtering: <5 seconds response time
- ✅ Memory usage: Scales linearly without memory leaks
- ✅ Concurrent users: Graceful performance degradation

### Business Logic Success Criteria
- ✅ Rent roll accuracy: 97%+ vs. expected results
- ✅ Date calculations: 100% accuracy for boundary conditions
- ✅ Financial precision: Consistent PSF calculations across measures
- ✅ Leasing activity: Accurate classification and aggregation
- ✅ Edge cases: No errors, graceful handling of unusual data

### Production Readiness Checklist
- [ ] All functional tests passed
- [ ] All performance benchmarks met
- [ ] All edge cases handled gracefully  
- [ ] Documentation updated with test results
- [ ] Business users trained on new measure behavior
- [ ] Monitoring and alerting configured for production
- [ ] Rollback plan prepared for production deployment

## Post-Test Activities

### Test Result Analysis
1. Compile comprehensive test result summary
2. Identify any patterns in failures or performance issues
3. Prioritize issues by business impact and technical complexity
4. Create detailed issue resolution plan

### Production Deployment Preparation
1. Package validated DAX measures for production deployment
2. Update production documentation with test-validated behavior
3. Create user communication about any behavior changes
4. Prepare production monitoring for new measures

### Continuous Testing Integration
1. Archive test datasets for future regression testing
2. Create automated test scripts where possible
3. Establish periodic re-testing schedule (quarterly/annually)
4. Document lessons learned for future measure development

This comprehensive test execution guide ensures thorough validation of all edge cases before production deployment, maintaining the high accuracy and performance standards required for business-critical rent roll analysis.