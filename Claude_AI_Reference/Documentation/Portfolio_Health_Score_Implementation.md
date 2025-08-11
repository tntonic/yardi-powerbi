# Portfolio Health Score Implementation Guide

## Quick Fix for Dashboard Error

The dashboard is looking for a table called `v_portfolio_health_score` with specific columns. Here's how to implement it:

## Option 1: Create as Calculated Table (Recommended)

1. Open your Power BI file
2. Go to **Modeling** tab → **New Table**
3. Copy the entire `v_portfolio_health_score` calculated table code from:
   ```
   Claude_AI_Reference/DAX_Measures/Portfolio_Health_Score_Comprehensive.dax
   ```
4. Paste the code and press Enter
5. The table will be created with all required columns

## Option 2: Create Individual Measures

If you prefer measures instead of a calculated table:

1. Create these measures in your model:
   - `Portfolio Health Score Enhanced`
   - `Occupancy Points`
   - `Financial Points`
   - `Credit Points`
   - `Leasing Points`
   - `Portfolio Health Category`

2. All measure code is in:
   ```
   Claude_AI_Reference/DAX_Measures/Portfolio_Health_Score_Comprehensive.dax
   ```

## Required Columns for Dashboard

The dashboard expects these columns:
- `portfolio_health_score` (INTEGER) - Overall score 0-100
- `health_category` (STRING) - Excellent/Good/Fair/Needs Attention/Critical
- `occupancy_points` (INTEGER) - Occupancy component (0-25)
- `financial_points` (INTEGER) - Financial component (0-25)
- `credit_points` (INTEGER) - Credit risk component (0-25)
- `leasing_points` (INTEGER) - Leasing activity component (0-25)

## Scoring Breakdown

Each component contributes 25 points to the total 100-point score:

### Occupancy Points (0-25)
- 95%+ occupancy = 25 points
- 90-94% = 20 points
- 85-89% = 15 points
- 80-84% = 10 points
- 75-79% = 5 points
- <75% = 0 points

### Financial Points (0-25)
- 70%+ NOI margin = 25 points
- 60-69% = 20 points
- 50-59% = 15 points
- 40-49% = 10 points
- 30-39% = 5 points
- <30% = 0 points

### Credit Points (0-25)
Based on average credit score AND at-risk tenant percentage:
- Score 8+ with <5% at-risk = 25 points
- Score 7+ with <10% at-risk = 20 points
- Score 6+ with <15% at-risk = 15 points
- Score 5+ with <20% at-risk = 10 points
- Score 4+ = 5 points
- <4 = 0 points

### Leasing Points (0-25)
Based on leasing velocity (new leases + renewals):
- 80%+ velocity = 25 points
- 60-79% = 20 points
- 40-59% = 15 points
- 20-39% = 10 points
- 10-19% = 5 points
- <10% = 0 points

## Health Categories

Total scores map to categories:
- **90-100**: Excellent
- **75-89**: Good
- **60-74**: Fair
- **40-59**: Needs Attention
- **0-39**: Critical

## Prerequisites

Ensure these tables exist in your model:
- `dim_lastclosedperiod` - For current date reference
- `fact_occupancyrentarea` - For occupancy metrics
- `fact_total` - For financial metrics
- `dim_fp_customercreditscorecustomdata` - For credit scores
- `dim_fp_amendmentsunitspropertytenant` - For leasing activity
- `dim_chartofaccounts` - For account filtering
- `dim_property` - For property filtering

## Troubleshooting

If the calculated table doesn't work:
1. Check all required tables exist
2. Verify column names match exactly
3. Ensure relationships are properly configured
4. Check for any missing measures referenced

## Alternative SQL View (If Needed)

If your dashboard requires a SQL view instead of DAX:
```sql
CREATE VIEW v_portfolio_health_score AS
SELECT 
    75 as portfolio_health_score,
    'Good' as health_category,
    20 as occupancy_points,
    20 as financial_points,
    20 as credit_points,
    15 as leasing_points
```
This creates a static view for testing. Replace with actual calculations once confirmed working.

## Validation

After implementation:
1. Refresh your data model
2. Check the calculated table has data
3. Verify the dashboard loads without errors
4. Validate scores match business expectations