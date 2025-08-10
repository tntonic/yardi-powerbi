# Fund 2 & Fund 3 Net Absorption Validation Report

**Test Date:** 2025-08-09 22:51:00
**Test Periods:** Q1 2025 (Jan-Mar) and Q2 2025 (Apr-Jun)
**Data Source:** Yardi PowerBI Data Model

## Executive Summary

This validation tests Same-Store Net Absorption measures for Fund 2 and Fund 3 against FPR benchmarks.

## Fund 2 Results

### Q1 2025 (January 1 - March 31, 2025)

| Metric | Actual | Target | Variance | Accuracy |
|--------|--------|--------|----------|----------|
| Move-Outs (SF Expired) | 50,591 | 712,000 | -661,409 | 7.1% |
| Gross Absorption (SF Commenced) | 0 | 198,000 | -198,000 | 0.0% |
| Net Absorption | -50,591 | -514,000 | +463,409 | 9.8% |

### Q2 2025 (April 1 - June 30, 2025)

| Metric | Actual | Target | Variance | Accuracy |
|--------|--------|--------|----------|----------|
| Move-Outs (SF Expired) | 0 | 458,000 | -458,000 | 0.0% |
| Gross Absorption (SF Commenced) | 0 | 258,000 | -258,000 | 0.0% |
| Net Absorption | 0 | -200,000 | +200,000 | 0.0% |

## Fund 3 Results

### Q1 2025 (January 1 - March 31, 2025)

| Metric | Actual | Target | Variance | Accuracy |
|--------|--------|--------|----------|----------|
| Move-Outs (SF Expired) | 0 | 111,000 | -111,000 | 0.0% |
| Gross Absorption (SF Commenced) | 0 | 365,000 | -365,000 | 0.0% |
| Net Absorption | 0 | 254,000 | -254,000 | 0.0% |

### Q2 2025 (April 1 - June 30, 2025)

| Metric | Actual | Target | Variance | Accuracy |
|--------|--------|--------|----------|----------|
| Move-Outs (SF Expired) | 0 | 250,600 | -250,600 | 0.0% |
| Gross Absorption (SF Commenced) | 0 | 112,000 | -112,000 | 0.0% |
| Net Absorption | 0 | -138,600 | +138,600 | 0.0% |

## Overall Accuracy Summary

| Fund | Quarter | Move-Outs Accuracy | Gross Absorption Accuracy | Net Absorption Accuracy |
|------|---------|-------------------|---------------------------|-------------------------|
| Fund 2 | Q1 2025 | 7.1% | 0.0% | 9.8% |
| Fund 2 | Q2 2025 | 0.0% | 0.0% | 0.0% |
| Fund 3 | Q1 2025 | 0.0% | 0.0% | 0.0% |
| Fund 3 | Q2 2025 | 0.0% | 0.0% | 0.0% |

## Recommendations

1. **Data Quality**: Verify fund property assignments are correct
2. **Date Ranges**: Ensure amendment dates align with reporting periods
3. **Status Filtering**: Confirm "Activated" and "Superseded" capture all relevant records
4. **Property Filtering**: Validate same-store property criteria matches business rules

## Next Steps

1. Review property-to-fund mappings
2. Validate amendment data completeness
3. Cross-reference with source Yardi reports
4. Update DAX measures with corrected fund filtering
