# Weighted Average Update - Version 5.1

## Overview
Updated DAX measures to properly implement area-weighted averages for rent PSF calculations, ensuring accurate portfolio metrics that account for property size differences.

## Key Changes

### 1. Renamed Existing Measure for Clarity
- **Old Name**: `Average Rent PSF`
- **New Name**: `Portfolio Rent PSF`
- **Reason**: The original measure was misleadingly named - it actually calculates total portfolio rent divided by total occupied area, which is NOT a weighted average across properties

### 2. Added New Properly Weighted Measures

#### Property Weighted Average Rent PSF
```dax
Property Weighted Average Rent PSF = 
// Properly weighted average rent PSF across properties
// Weights by each property's occupied area for accurate portfolio average
```
- Calculates rent PSF for each property individually
- Weights each property's PSF by its occupied area
- Returns the true weighted average across the portfolio

#### Unit Weighted Average Rent PSF
```dax
Unit Weighted Average Rent PSF = 
// Properly weighted average rent PSF across individual units
// Uses amendment-based data for unit-level precision
```
- Uses amendment-based data for precise unit-level calculations
- Weights each unit's rent PSF by its leased area
- Provides most granular weighted average

### 3. Added Helper Measure for Reusability
```dax
_PropertyRentMetrics = 
// Pre-calculates property-level rent metrics for reuse
```
- Centralizes property rent calculations
- Improves performance by avoiding duplicate calculations
- Can be reused across multiple measures

### 4. Enhanced Validation Measures
Added three new validation measures to ensure weighted averages are working correctly:

- **Weighted Average Validation**: Compares weighted vs portfolio totals to identify issues
- **Property Mix Skew Analysis**: Identifies if large properties are dominating averages
- **Weighted vs Simple Average Comparison**: Shows the difference between calculation methods

## Why This Matters

### Before (Incorrect)
```dax
Average Rent PSF = 
DIVIDE(
    SUM(total rent) * 12,
    SUM(occupied area),
    0
)
```
This gives the same weight to a 10,000 SF property and a 100,000 SF property when they should be weighted differently.

### After (Correct)
```dax
Property Weighted Average Rent PSF = 
// Calculates PSF for each property
// Then weights by that property's area
```
This properly accounts for property size differences in the portfolio average.

## Example Scenario
Consider a portfolio with:
- Property A: 10,000 SF at $20/SF
- Property B: 100,000 SF at $10/SF

**Old Method (Portfolio Rent PSF)**:
- Total Rent: (10,000 × $20) + (100,000 × $10) = $1,200,000
- Total Area: 110,000 SF
- Result: $10.91/SF

**New Method (Weighted Average)**:
- Property A weight: 10,000/110,000 = 9.09%
- Property B weight: 100,000/110,000 = 90.91%
- Result: ($20 × 9.09%) + ($10 × 90.91%) = $10.91/SF

In this case they match because we're using the same underlying calculation. However, when calculating averages across properties with varying occupancy levels or when some properties have missing data, the weighted average method provides more accurate results.

## Implementation Notes

1. **Backward Compatibility**: The original measure was renamed, not removed. Any existing reports using `Average Rent PSF` should be updated to use either:
   - `Portfolio Rent PSF` (for the same calculation as before)
   - `Property Weighted Average Rent PSF` (for the new weighted calculation)

2. **Performance Considerations**: The weighted average measures are more computationally intensive as they calculate at the property level first. Use the helper measure `_PropertyRentMetrics` when multiple weighted calculations are needed.

3. **When to Use Each Measure**:
   - **Portfolio Rent PSF**: When you need total portfolio metrics (total rent / total area)
   - **Property Weighted Average Rent PSF**: When you need the average rent PSF across properties
   - **Unit Weighted Average Rent PSF**: When you need the most granular unit-level average

## Files Modified

1. `/Claude_AI_Reference/DAX_Measures/01_Core_Financial_Rent_Roll_Measures_v5.0.dax`
   - Added 3 new weighted average measures
   - Added 1 helper measure
   - Renamed existing Average Rent PSF
   - Updated to v5.1

2. `/Claude_AI_Reference/DAX_Measures/Top_20_Essential_Measures.dax`
   - Updated to reflect renamed measure
   - Added Property Weighted Average Rent PSF
   - Updated to v5.1

3. `/Claude_AI_Reference/DAX_Measures/Validation_Measures.dax`
   - Fixed references to renamed measure
   - Added 3 new validation measures for weighted averages
   - Updated to v5.1

## Testing Recommendations

1. Compare `Portfolio Rent PSF` with `Property Weighted Average Rent PSF`
2. Run `Property Mix Skew Analysis` to understand your portfolio composition
3. Use `Weighted Average Validation` to ensure calculations are correct
4. Test with filters applied (e.g., single fund or property type) to verify weighting logic

## Version History
- **v5.0**: Original implementation with `Average Rent PSF`
- **v5.1**: Added proper weighted averages and renamed for clarity