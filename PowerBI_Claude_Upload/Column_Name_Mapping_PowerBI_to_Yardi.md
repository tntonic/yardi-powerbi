# Column Name Mapping: PowerBI to Yardi

## Overview
This document provides a comprehensive mapping between PowerBI column references (using underscores) and actual Yardi table column names (using spaces). When implementing DAX measures or Power Query transformations, use the Yardi column names.

## Important Notes
1. **Column References in DAX**: When referencing columns with spaces in DAX, always use square brackets: `[column name]`
2. **Table References**: Table names remain with underscores as they correspond to file names
3. **Date Format**: Yardi uses Excel serial dates (e.g., 44562 = 2022-01-01)

## Table-by-Table Mapping

### dim_property
| PowerBI Reference | Yardi Column Name | Notes |
|-------------------|-------------------|-------|
| property_id | property id | Primary key |
| property_code | property code | |
| property_name | property name | |
| is_active | is active | |
| postal_address | postal address | |
| postal_city | postal city | |
| postal_state | postal state | |
| postal_zip_code | postal zip code | |
| postal_country | postal country | |
| acquire_date | acquire date | |
| dispose_date | dispose date | |
| inactive_date | inactive date | |
| is_commercial | is commercial | |
| is_international | is international | |
| property_last_closed_period | property last closed period | |
| database_id | database id | |

### fact_total
| PowerBI Reference | Yardi Column Name | Notes |
|-------------------|-------------------|-------|
| property_id | property id | Foreign key |
| book_id | book id | Foreign key |
| account_id | account id | Foreign key |
| month | month | Excel date format |
| amount_type | amount type | |
| amount | amount | |
| database_id | database id | |
| transaction_currency | transaction currency | |

### fact_occupancyrentarea
| PowerBI Reference | Yardi Column Name | Notes |
|-------------------|-------------------|-------|
| property_id | property id | Foreign key |
| lease_type_id | lease type id | |
| unit_count | unit count | |
| occupied_area | occupied area | |
| rentable_area | rentable area | |
| total_rent | total rent | |
| property_area | property area | |
| first_day_of_month | first day of month | Excel date format |
| database_id | database id | |

### dim_account
| PowerBI Reference | Yardi Column Name | Notes |
|-------------------|-------------------|-------|
| account_id | account id | Primary key |
| account | account | |
| account_code | account code | |
| account_description | account description | |
| parent_account_id | parent account id | |
| report_type | report type | |
| normal_balance | normal balance | |
| chart_id | chart id | |
| account_type | account type | |
| margin | margin | |
| advance | advance | |
| bold | bold | |
| italic | italic | |
| underline | underline | |
| database_id | database id | |

### dim_book
| PowerBI Reference | Yardi Column Name | Notes |
|-------------------|-------------------|-------|
| book_id | book id | Primary key |
| book | book | |
| database_id | database id | |

### dim_date
| PowerBI Reference | Yardi Column Name | Notes |
|-------------------|-------------------|-------|
| date | date | Primary key |
| year | year | |
| month | month | |
| month_name | month name | |
| quarter | quarter | |
| quarter_name | quarter name | |
| week_of_month | week of month | |
| day | day | |
| day_of_week | day of week | |
| day_of_year | day of year | |
| day_name | day name | |

### dim_unit
| PowerBI Reference | Yardi Column Name | Notes |
|-------------------|-------------------|-------|
| unit_id | unit id | Primary key |
| property_id | property id | Foreign key |
| unit_name | unit name | |
| unit_type | unit type | |
| excluded_unit | excluded unit | |
| floor_id | floor id | |
| floor_code | floor code | |
| floor_level_int | floor level int | |
| level | level | |
| elevator | elevator | |
| building_id | building id | |
| building_code | building code | |
| building_name | building name | |
| database_id | database id | |

### dim_commcustomer
| PowerBI Reference | Yardi Column Name | Notes |
|-------------------|-------------------|-------|
| tenant_id | tenant id | Primary key |
| property_id | property id | Foreign key |
| customer_id | customer id | |
| tenant_code | tenant code | |
| lease_type | lease type | |
| dba_name | dba name | |
| lessee_name | lessee name | |
| is_anchor_tenant | is anchor tenant | |
| naics | naics | |
| lease_from | lease from | Excel date format |
| lease_to | lease to | Excel date format |
| is_current | is current | |
| is_at_risk_tenant | is at risk tenant | |
| database_id | database id | |

### dim_commleasetype
| PowerBI Reference | Yardi Column Name | Notes |
|-------------------|-------------------|-------|
| comm_lease_type_id | comm lease type id | Primary key |
| comm_lease_type_code | comm lease type code | |
| comm_lease_type_desc | comm lease type desc | |
| database_id | database id | |

### dim_fp_amendmentsunitspropertytenant
| PowerBI Reference | Yardi Column Name | Notes |
|-------------------|-------------------|-------|
| amendment_hmy | amendment hmy | Primary key |
| property_hmy | property hmy | Foreign key |
| property_code | property code | |
| tenant_hmy | tenant hmy | Foreign key |
| tenant_id | tenant id | |
| amendment_status_code | amendment status code | |
| amendment_status | amendment status | |
| amendment_type_code | amendment type code | |
| amendment_type | amendment type | |
| amendment_sequence | amendment sequence | |
| units_under_amendment | units under amendment | |
| hmy_units_under_amendment | hmy units under amendment | |
| amendment_sf | amendment sf | |
| amendment_term | amendment term | |
| amendment_start_date | amendment start date | Excel date format |
| amendment_end_date | amendment end date | Excel date format |
| amendment_sign_date | amendment sign date | Excel date format |
| amendment_description | amendment description | |
| amendment_notes | amendment notes | |
| holdover_percent | holdover % | Note the % symbol |

### dim_fp_amendmentchargeschedule
| PowerBI Reference | Yardi Column Name | Notes |
|-------------------|-------------------|-------|
| record_hmy | record hmy | Primary key |
| property_hmy | property hmy | Foreign key |
| property_code | property code | |
| amendment_hmy | amendment hmy | Foreign key |
| tenant_hmy | tenant hmy | Foreign key |
| lease_code | lease code | |
| charge_code_hmy | charge code hmy | |
| charge_code | charge code | |
| charge_code_desc | charge code desc | |
| amount_period_code | amount period code | |
| amount_period_desc | amount period desc | |
| from_date | from date | Excel date format |
| to_date | to date | Excel date format |
| amount | amount | |
| monthly_amount | monthly amount | |
| contracted_area | contracted area | |
| notes | notes | |
| management_fee_percent | management fee % | Note the % symbol |

### fact_accountsreceivable
| PowerBI Reference | Yardi Column Name | Notes |
|-------------------|-------------------|-------|
| property_id | property id | Foreign key |
| tenant_id | tenant id | Foreign key |
| customer_id | customer id | |
| total_owed | total owed | |
| days_0_30 | 0 to 30 | Note the different format |
| days_31_60 | 31 to 60 | Note the different format |
| days_61_90 | 61 to 90 | Note the different format |
| over_ninety_owed | over ninety owed | |
| first_day_of_month | first day of month | Excel date format |
| database_id | database id | |

### fact_expiringleaseunitarea
| PowerBI Reference | Yardi Column Name | Notes |
|-------------------|-------------------|-------|
| property_id | property id | Foreign key |
| property_area | property area | |
| unit_id | unit id | Foreign key |
| tenant_id | tenant id | Foreign key |
| lease_from_date | lease from date | Excel date format |
| lease_to_date | lease to date | Excel date format |
| expiring_area | expiring area | |
| database_id | database id | |

## Special Cases and Notes

1. **Date Columns**: All date columns use Excel serial date format. Use DAX date conversion functions when needed.

2. **Percentage Columns**: Some columns include the % symbol in their names (e.g., `holdover %`, `management fee %`). These require special handling in DAX.

3. **Aging Buckets**: In fact_accountsreceivable, the aging buckets use different naming:
   - PowerBI: `days_0_30`, `days_31_60`, etc.
   - Yardi: `0 to 30`, `31 to 60`, etc.

4. **Key Suffixes**: PowerBI documentation often uses `_hmy` suffix, while Yardi uses ` hmy` (with space).

## DAX Formula Updates Required

When updating DAX formulas:

1. Replace all underscores with spaces in column names
2. Add square brackets around all column references
3. Update table references if needed (though table names generally match file names)

Example transformation:
```dax
// Old (PowerBI documentation)
SUM(fact_total[amount])

// New (Yardi-compatible)
SUM(fact_total[amount])
```

For columns with spaces:
```dax
// Old (PowerBI documentation)
SUM(fact_occupancyrentarea[occupied_area])

// New (Yardi-compatible)
SUM(fact_occupancyrentarea[occupied area])
```