# Rent Roll Generation from Yardi Tables - Project Summary

## Project Overview

Successfully created a complete, reproducible process to generate rent rolls from raw Yardi data tables, achieving **95.8% accuracy** compared to native Yardi exports. This project focused on Fund 2 properties as of June 30, 2025.

## Key Accomplishments

### 1. Data Pipeline Created
- **Filtered Fund 2 Data**: Extracted 877 amendment records, 1,084 active charges, 195 properties
- **Date Conversion Logic**: Handled mixed date formats (MM/DD/YYYY vs Excel serial)
- **Optimized for Performance**: Created filtered datasets to avoid context overload

### 2. Business Logic Validated
- **Critical Discovery**: Must include both "Activated" AND "Superseded" amendment statuses
- **Amendment Selection**: Always use MAX(sequence) per property/tenant combination
- **Charge Integration**: Filter charges to those active on report date

### 3. Python Implementation
Created three key scripts:
- `filter_fund2_data.py` - Extracts and filters Fund 2 data
- `generate_rent_roll_from_yardi.py` - Applies business logic to generate rent roll
- `validate_rent_roll.py` - Compares output with Yardi export

### 4. Validation Results

| Metric | Accuracy |
|--------|----------|
| Record Count | 95.7% |
| Monthly Rent Total | 95.6% |
| Annual Rent Total | 95.6% |
| Square Footage | 97.2% |
| **Overall Weighted** | **95.8%** |

## File Structure Created

```
PBI v1.7/
├── python scripts/
│   ├── filter_fund2_data.py                # Data extraction and filtering
│   ├── generate_rent_roll_from_yardi.py    # Rent roll generation (June 30)
│   ├── generate_rent_roll_for_date.py      # Flexible date rent roll generator
│   ├── validate_rent_roll.py               # Validation against Yardi export
│   ├── clean_rent_roll.py                  # Original Yardi export cleaner
│   └── run_complete_workflow.py            # Complete workflow runner
├── Data/
│   └── Fund2_Filtered/                     # Filtered Fund 2 data files
│       ├── dim_fp_amendmentsunitspropertytenant_fund2.csv
│       ├── dim_fp_amendmentchargeschedule_fund2_active.csv
│       ├── dim_property_fund2.csv
│       └── dim_unit_fund2.csv
├── Generated_Rent_Rolls/                   # Output rent rolls
│   ├── fund2_rent_roll_generated_063025.csv
│   └── fund2_rent_roll_generated_063025.xlsx
├── Documentation/
│   ├── Implementation/
│   │   └── Rent_Roll_Logic_Complete.md     # Complete logic with column naming
│   └── Validation/
│       ├── Validation_Progress.md          # Validation status
│       └── IMPLEMENTATION_IMPROVEMENTS.md  # Column naming discoveries
└── Archive/                                # Archived analyses
    └── June1_Analysis/                     # June 1, 2025 comparison files
```

## Key Insights for PowerBI Implementation

### 1. Critical Column Naming Discovery

**IMPORTANT**: Yardi tables use spaces in column names, not underscores:
- Use `[amendment status]` not `[amendment_status]`
- Use `[property hmy]` not `[property_hmy]`
- Use `[tenant id]` not `[tenant_id]`
- Use `[from date]` not `[from_date]`

### 2. DAX Measure Corrections Needed

The existing DAX measures should be updated to:
- Include "Superseded" status in addition to "Activated"
- Always filter to MAX(amendment_sequence) per property/tenant
- Properly filter charge schedules by date
- Use correct column names with spaces

### 3. Recommended DAX Pattern

```dax
Current Monthly Rent = 
VAR CurrentDate = TODAY()
VAR ValidAmendments = 
    FILTER(
        dim_fp_amendmentsunitspropertytenant,
        dim_fp_amendmentsunitspropertytenant[amendment status] IN {"Activated", "Superseded"} &&
        dim_fp_amendmentsunitspropertytenant[amendment type] <> "Termination"
    )
VAR LatestAmendments = 
    FILTER(
        ValidAmendments,
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
RETURN
CALCULATE(
    SUM(dim_fp_amendmentchargeschedule[monthly amount]),
    LatestAmendments,
    dim_fp_amendmentchargeschedule[charge code] = "rent",
    dim_fp_amendmentchargeschedule[from date] <= CurrentDate,
    dim_fp_amendmentchargeschedule[to date] >= CurrentDate
)
```

**Note**: Column names use spaces, not underscores!

## Areas for Future Enhancement

1. **Vacant Unit Handling**
   - Current logic only shows occupied units
   - Could add vacant units from dim_unit table

2. **Additional Charges**
   - Currently only includes base rent
   - Could add CAM, insurance, tax charges

3. **Performance Optimization**
   - Consider creating materialized views
   - Implement incremental refresh strategy

4. **Extended Validation**
   - Test with other funds (Fund 3, etc.)
   - Validate historical periods

## How to Use This Work

### To Generate a Rent Roll:
```bash
# 1. Filter the data
python3 "python scripts/filter_fund2_data.py"

# 2. Generate the rent roll
python3 "python scripts/generate_rent_roll_from_yardi.py"

# 3. Validate the results
python3 "python scripts/validate_rent_roll.py"
```

### To Run Complete Workflow:
```bash
python3 "python scripts/run_complete_workflow.py"
```

## Conclusion

This project successfully:
1. ✅ Reproduced Yardi rent rolls with 95.8% accuracy
2. ✅ Documented the complete logic flow
3. ✅ Created reusable Python scripts for validation
4. ✅ Identified critical business rules (Superseded status, sequence logic)
5. ✅ Provided clear implementation guidance for PowerBI

The validated logic can now be confidently used to:
- Update PowerBI DAX measures for improved accuracy
- Train team members on rent roll generation
- Validate future PowerBI implementations
- Document the Yardi data model comprehensively