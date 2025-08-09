# Data Dictionary

## Overview

This comprehensive data dictionary provides detailed information about all tables, columns, and data elements used in the Yardi BI Power BI solution. It serves as the authoritative reference for understanding data structures, relationships, and business meanings.

## Data Model Architecture

### Table Categories

#### Dimension Tables (dim_*)
```
Purpose: Store descriptive attributes and business entities
Characteristics:
- Relatively small size (typically <100K rows)
- Contain business keys and descriptive attributes
- Form the "one" side of one-to-many relationships
- Updated less frequently than fact tables
- Support filtering and grouping operations
```

#### Fact Tables (fact_*)
```
Purpose: Store quantitative measurements and transactions
Characteristics:
- Large size (can contain millions of rows)
- Contain foreign keys to dimension tables
- Store numeric measures and dates
- Form the "many" side of one-to-many relationships
- Updated frequently with operational data
```

#### Specialized Tables
```
Purpose: Store specific business data not fitting standard patterns
Examples:
- Bridge tables for many-to-many relationships
- Configuration and control tables
- External reference data (market rates, growth projections)
- Override and adjustment tables
```

## Dimension Tables

### 1. dim_property
**Purpose**: Master list of all properties in the portfolio
**Grain**: One row per property
**Business Key**: property id

| Column Name | Data Type | Description | Business Rules | Example Values |
|-------------|-----------|-------------|----------------|----------------|
| property id | Integer | Unique property identifier | Primary key, not null | 1001, 1002, 1003 |
| property hmy | Integer | Yardi internal property key | Foreign key to other tables | 12345, 12346 |
| property name | Text | Property display name | Not null, unique per portfolio | "Downtown Office Plaza" |
| property code | Text | Short property code | 3-10 characters, uppercase | "DOP", "WEST01" |
| postal address | Text | Primary street address | Standard address format | "123 Main Street" |
| postal address 2 | Text | Secondary address info | Optional suite/floor info | "Suite 100" |
| postal city | Text | Property city | Standard city name | "Chicago" |
| postal state | Text | Property state/province | 2-character state code | "IL", "CA", "NY" |
| postal zip code | Text | ZIP/postal code | US: 5 or 9 digits, formatted | "60601", "60601-1234" |
| postal country | Text | Country code | ISO country codes | "US", "CA" |
| property type | Text | Property classification | Office, Industrial, Retail, Mixed | "Office" |
| year built | Integer | Construction completion year | 4-digit year, > 1800 | 1985, 2010 |
| year renovated | Integer | Major renovation year | 4-digit year, optional | 2005, NULL |
| rentable area | Integer | Total rentable square feet | Positive integer, BOMA standard | 150000, 75000 |
| stories | Integer | Number of building floors | Positive integer | 10, 25 |
| parking spaces | Integer | Total parking spaces | Non-negative integer | 300, 0 |
| property manager | Text | Property manager name | Current manager | "John Smith" |
| ownership percentage | Decimal | Ownership stake in property | 0.01 to 1.00 (1% to 100%) | 1.00, 0.50 |
| is active | Boolean | Property active status | True/False | TRUE |
| acquire date | Date | Property acquisition date | Valid date | 2020-01-15 |
| dispose date | Date | Property disposition date | Valid date or NULL | NULL |
| inactive date | Date | Property inactive date | Valid date or NULL | NULL |
| is commercial | Boolean | Is commercial property | True/False | TRUE |
| is international | Boolean | Is international property | True/False | FALSE |
| property last closed period | Date | Last closed accounting period | Valid date | 6/1/25 |
| database id | Integer | Source database identifier | Not null | 1 |

**Key Relationships**:
- → fact_total (property id)
- → fact_occupancyrentarea (property id)
- → dim_unit (property id)
- → dim_fp_buildingcustomdata (property hmy)

### 2. dim_unit
**Purpose**: Individual leasable units within properties
**Grain**: One row per unit
**Business Key**: unit id

| Column Name | Data Type | Description | Business Rules | Example Values |
|-------------|-----------|-------------|----------------|----------------|
| unit id | Integer | Unique unit identifier | Primary key, not null | 5001, 5002 |
| unit hmy | Integer | Yardi internal unit key | Foreign key to other tables | 98765, 98766 |
| property id | Integer | Parent property | Foreign key to dim_property | 1001 |
| unit name | Text | Unit designation | Building + Unit format | "Building A - Suite 101" |
| unit code | Text | Short unit code | Alphanumeric, unique per property | "A101", "B205" |
| floor level int | Integer | Floor number | Positive integer, ground = 1 | 1, 15, 25 |
| unit type | Text | Space classification | Office, Warehouse, Retail, etc. | "Office" |
| rentable area | Integer | Unit rentable square feet | Positive integer | 2500, 10000 |
| usable area | Integer | Unit usable square feet | <= rentable area | 2250, 9500 |
| load factor | Decimal | Rentable/Usable ratio | >= 1.0, typically 1.1-1.3 | 1.15, 1.25 |
| window line | Boolean | Has exterior windows | True/False | TRUE, FALSE |
| corner unit | Boolean | Corner location | True/False | TRUE, FALSE |
| handicap accessible | Boolean | ADA compliant | True/False | TRUE, FALSE |
| hvac type | Text | Climate control system | Central, Individual, None | "Central" |
| base year | Integer | Expense stop year | 4-digit year | 2020, 2024 |
| market rent psf | Decimal | Current market rent | Dollars per SF annually | 32.50, 28.75 |
| excluded unit | Boolean | Excluded from metrics | True/False | FALSE |
| floor id | Integer | Floor identifier | Internal ID | 27, 28 |
| floor code | Text | Floor code | Alphanumeric code | "3", "4" |
| level | Text | Level designation | Floor level text | "Ground", "Mezzanine" |
| elevator | Text | Elevator access | Yes/No | "Yes", "No" |
| building id | Integer | Building identifier | Foreign key | 91, 92 |
| building code | Text | Building code | Short building identifier | "building 1", "building 2" |
| building name | Text | Building name | Full building name | "858 Lenola - 1" |
| database id | Integer | Source database identifier | Not null | 1 |

**Key Relationships**:
- dim_property → dim_unit (property id)
- → dim_fp_amendmentsunitspropertytenant (unit hmy)
- → fact_fp_fmvm_marketunitrates (unit hmy)

### 3. dim_commcustomer
**Purpose**: Commercial tenants and customers
**Grain**: One row per tenant entity
**Business Key**: tenant id

| Column Name | Data Type | Description | Business Rules | Example Values |
|-------------|-----------|-------------|----------------|----------------|
| tenant id | Integer | Unique tenant identifier | Primary key, not null | 2001, 2002 |
| property id | Integer | Property where tenant is located | Foreign key to dim_property | 1001 |
| customer id | Integer | Customer identifier | Not null | 54321, 54322 |
| tenant code | Text | Short tenant code | Alphanumeric, unique | "ABC01", "XYZ02" |
| lease type | Text | Type of lease | NNN, Full Service, Modified | "NNN" |
| dba name | Text | Doing business as name | Trade name if different | "ABC Consulting" |
| lessee name | Text | Legal entity name | Official business name | "ABC Corporation" |
| is anchor tenant | Boolean | Is anchor tenant | True/False | TRUE, FALSE |
| naics | Text | NAICS industry code | 2-6 digit industry code | "541211" |
| lease from | Date | Lease start date | Excel date format | 44562 |
| lease to | Date | Lease end date | Excel date format | 45292 |
| is current | Boolean | Is currently active | True/False | TRUE |
| is at risk tenant | Boolean | At risk of leaving | True/False | FALSE |
| database id | Integer | Source database identifier | Not null | 1 |

**Key Relationships**:
- dim_property → dim_commcustomer (property id)
- → dim_fp_amendmentsunitspropertytenant (tenant id)
- → dim_fp_naicstotenantmap (tenant id)

### 4. dim_account
**Purpose**: Chart of accounts for financial reporting
**Grain**: One row per account
**Business Key**: account id

| Column Name | Data Type | Description | Business Rules | Example Values |
|-------------|-----------|-------------|----------------|----------------|
| account id | Integer | Unique account identifier | Primary key, not null | 3001, 3002 |
| account code | Integer | Numeric account code | 5-8 digit code, structured (see ranges below) | 40100000, 50200000 |
| account | Text | Account display name | Descriptive name | "Base Rent Income" |
| account description | Text | Detailed description | Full account purpose | "Monthly base rental income" |
| account type | Text | Account classification | Revenue, Expense, Asset, etc. | "Revenue" |
| report type | Text | Report classification | Balance Sheet, Income Statement | "Income Statement" |
| parent account id | Integer | Parent account ID | For hierarchical grouping | 40000 |
| normal balance | Text | Normal balance side | Debit, Credit | "Credit" |
| chart id | Integer | Chart of accounts ID | Chart identifier | 1 |
| margin | Integer | Display margin | For report formatting | 0 |
| advance | Integer | Display advance | For report formatting | 0 |
| bold | Boolean | Bold formatting | For report display | TRUE, FALSE |
| italic | Boolean | Italic formatting | For report display | TRUE, FALSE |
| underline | Boolean | Underline formatting | For report display | TRUE, FALSE |
| database id | Integer | Source database identifier | Not null | 1 |

**Account Code Ranges**:
```
Revenue Accounts (40000000 - 49999999):
- 40000000-40999999: Base Rental Income
- 41000000-41999999: Percentage Rent
- 42000000-42999999: Expense Recoveries
- 43000000-49999999: Other Income (Parking, Signage, etc.)

Operating Expense Accounts (50000000 - 59999999):
- 50000000-50999999: Property Management
- 51000000-51999999: Utilities
  - 51100000-51199999: Electric
  - 51200000-51299999: Gas
  - 51300000-51399999: Water/Sewer
  - 51400000-51499999: Other utilities
- 52000000-52999999: Repairs & Maintenance
  - 52100000-52199999: HVAC
  - 52200000-52299999: Electrical
  - 52300000-52399999: Plumbing
  - 52400000-52499999: General maintenance
- 53000000-53999999: Contracted Services
  - 53100000-53199999: Janitorial
  - 53200000-53299999: Landscaping
  - 53300000-53399999: Security
- 54000000-54999999: Insurance & Taxes
  - 54100000-54499999: Property insurance
  - 54500000-54999999: Real estate taxes
- 55000000-55999999: Marketing & Leasing

Recovery Categorization:
- 61000000-61999999: Recoverable Expenses
- 62000000-62999999: Non-Recoverable Expenses

Capital Accounts (16000000 Series):
- 16005150: Purchase Price
- 16005200: Land
- 16005250: Closing Costs
- 16005260: Solar Panels
- 16005310: Tenant Improvements
- 16005340: Capital Expenses
- 16005360: Construction Management Fees
- 16005450: Leasing Commissions

Excluded from NOI:
- 64006000: Depreciation
- 64001100-64001600: Corporate Overhead
```

**Sign Convention**:
- Revenue accounts: Stored as negative (credits), multiply by -1 for display
- Expense accounts: Stored as positive (debits)

**Key Relationships**:
- → fact_total (account id)
- → dim_accounttreeaccountmapping (account id)

### 5. dim_date
**Purpose**: Calendar dimension for time-based analysis
**Grain**: One row per date
**Business Key**: date

| Column Name | Data Type | Description | Business Rules | Example Values |
|-------------|-----------|-------------|----------------|----------------|
| date | Date | Calendar date | Primary key, continuous | 2024-01-15 |
| year | Integer | Calendar year | 4-digit year | 2024 |
| quarter | Integer | Calendar quarter | 1, 2, 3, 4 | 1 |
| month | Integer | Calendar month | 1-12 | 1 |
| day | Integer | Day of month | 1-31 | 15 |
| month name | Text | Month name | Full month name | "January" |
| quarter name | Text | Quarter name | Quarter format | "Q1" |
| week of month | Integer | Week of month | 1-5 | 1 |
| day of week | Integer | Day of week | 0=Sunday, 6=Saturday | 0 |
| day of year | Integer | Day of year | 1-366 | 15 |
| day name | Text | Day name | Full day name | "Monday" |
| fiscal_month | Integer | Fiscal month | 1-12 for fiscal periods | 5 |
| is_weekend | Boolean | Weekend indicator | Saturday/Sunday = True | FALSE |
| is_holiday | Boolean | Holiday indicator | US federal holidays | FALSE |
| is_business_day | Boolean | Business day indicator | Excludes weekends/holidays | TRUE |
| days_in_month | Integer | Month length | 28-31 days | 31 |
| week_of_year | Integer | ISO week number | 1-53 | 3 |

**Key Relationships**:
- ↔ fact_total (month) - Bi-directional
- ↔ fact_occupancyrentarea (first day of month) - Bi-directional

## Fact Tables

### 6. dim_book
**Purpose**: Accounting book perspectives for financial reporting
**Grain**: One row per accounting book
**Business Key**: book id

| Column Name | Data Type | Description | Business Rules | Example Values |
|-------------|-----------|-------------|----------------|----------------|
| book id | Integer | Unique book identifier | Primary key, not null | 1, 2, 46 |
| book | Text | Book display name | Descriptive name | "Accrual", "Cash", "FPR" |
| database id | Integer | Source database identifier | Not null | 1 |

**Standard Books**:
```
Book ID 1: Accrual Book
- Purpose: Standard GAAP financial reporting
- Usage: Primary NOI calculations, financial statements

Book ID 2: Cash Book  
- Purpose: Cash-basis accounting
- Usage: Cash flow analysis, collection tracking

Book ID 46: FPR Book (Financial Planning & Reporting)
- Purpose: Enhanced NOI with balance sheet movements
- Special Accounts: 646, 648, 825, 950, 953, 957, 1111-1114, 1120, 1123
- Usage: Institutional investor reporting

Budget Books (Various IDs):
- Names: "BA-2024", "Budget-Accrual", "Budget 2024"
- Purpose: Annual budget tracking and variance analysis

Business Plan Books (Various IDs):
- Names: "Business Plan", "Business Plan 2024", "BP-Original"
- Purpose: Multi-year projections, acquisition underwriting
```

**Key Relationships**:
- → fact_total (book id)

### 7. fact_total
**Purpose**: All financial transactions across the portfolio
**Grain**: One row per account, property, book, period combination
**Update Frequency**: Monthly

| Column Name | Data Type | Description | Business Rules | Example Values |
|-------------|-----------|-------------|----------------|----------------|
| property id | Integer | Property identifier | Foreign key to dim_property | 1001 |
| book id | Integer | Book identifier | Foreign key to dim_book | 1 |
| account id | Integer | Account identifier | Foreign key to dim_account | 3001 |
| month | Date | Accounting period | First day of month, Excel format | 44562 |
| amount type | Text | Transaction type | Actual, Budget, Cumulative Actual | "Actual" |
| amount | Decimal | Transaction amount | Positive or negative, 2 decimals | 125000.00, -25000.00 |
| database id | Integer | Source database identifier | Not null | 1 |
| transaction currency | Text | Currency code | ISO currency code | "USD" |

**Key Relationships**:
- dim_property → fact_total (property id)
- dim_account → fact_total (account id)  
- dim_book → fact_total (book id)
- dim_date ↔ fact_total (month)

### 8. fact_occupancyrentarea
**Purpose**: Monthly property occupancy and rent metrics
**Grain**: One row per property per month
**Update Frequency**: Monthly

| Column Name | Data Type | Description | Business Rules | Example Values |
|-------------|-----------|-------------|----------------|----------------|
| property id | Integer | Property identifier | Foreign key to dim_property | 1001 |
| lease type id | Integer | Lease type identifier | Type of lease | 1 |
| unit count | Integer | Number of units | Count of units | 25 |
| occupied area | Integer | Occupied SF | 0 <= occupied <= rentable | 135000 |
| rentable area | Integer | Total rentable SF | Must be > 0 | 150000 |
| total rent | Decimal | Monthly rent total | Sum of all tenant rents | 350000.00 |
| property area | Integer | Total property area | Total SF | 150000 |
| first day of month | Date | Month being measured | First day, Excel format | 44562 |
| database id | Integer | Source database identifier | Not null | 1 |

**Key Relationships**:
- dim_property → fact_occupancyrentarea (property id)
- dim_date ↔ fact_occupancyrentarea (first day of month)

## Specialized Yardi Tables

### 9. dim_fp_amendmentsunitspropertytenant
**Purpose**: Core lease amendment data linking properties, units, and tenants
**Grain**: One row per amendment
**Business Key**: amendment_hmy

| Column Name | Data Type | Description | Business Rules | Example Values |
|-------------|-----------|-------------|----------------|----------------|
| amendment_hmy | Integer | Unique amendment ID | Primary key, not null | 789123 |
| property_hmy | Integer | Property reference | Foreign key to property | 12345 |
| unit_hmy | Integer | Unit reference | Foreign key to unit | 98765 |
| tenant_hmy | Integer | Tenant reference | Foreign key to tenant | 54321 |
| amendment_sequence | Integer | Amendment order | 0 = original, 1+ = amendments | 0, 1, 2 |
| amendment_type | Text | Type of amendment | Original Lease, Renewal, etc. | "Original Lease" |
| amendment_status | Text | Current status | Activated, Superseded, Pending | "Activated" |
| amendment_start_date | Date | Effective start date | Must be valid date | 2023-01-01 |
| amendment_end_date | Date | Lease expiration | NULL for month-to-month | 2025-12-31 |
| amendment_sf | Integer | Square feet under lease | Must be > 0 | 5000 |
| base_rent | Decimal | Monthly base rent | Must be >= 0 | 12500.00 |
| rent_psf | Decimal | Annual rent per SF | base_rent * 12 / amendment_sf | 30.00 |
| security_deposit | Decimal | Deposit amount | >= 0 | 25000.00 |
| lease_type | Text | Lease classification | Full Service, NNN, Modified | "NNN" |
| lease_term_months | Integer | Original term length | > 0 for fixed terms | 36 |
| renewal_options | Integer | Number of renewal options | >= 0 | 2 |
| percentage_rent_rate | Decimal | Percentage rent % | 0-100 if applicable | 5.0 |
| expense_stop | Decimal | Base year expenses | PSF amount | 8.50 |
| parking_spaces | Integer | Included parking | >= 0 | 10 |

**Key Relationships**:
- dim_property ← dim_fp_amendmentsunitspropertytenant (property_hmy)
- dim_unit ← dim_fp_amendmentsunitspropertytenant (unit_hmy)
- dim_commcustomer ← dim_fp_amendmentsunitspropertytenant (tenant_hmy)
- → dim_fp_amendmentchargeschedule (amendment_hmy)

### 10. dim_fp_amendmentchargeschedule
**Purpose**: Detailed rent and charge schedules for lease amendments
**Grain**: One row per charge period per amendment
**Business Key**: Combination of amendment_hmy + from_date + charge_type

| Column Name | Data Type | Description | Business Rules | Example Values |
|-------------|-----------|-------------|----------------|----------------|
| amendment_hmy | Integer | Parent amendment | Foreign key to amendments | 789123 |
| charge_type | Text | Type of charge | Base Rent, CAM, Tax, etc. | "Base Rent" |
| from_date | Date | Charge start date | Must be valid date | 2023-01-01 |
| to_date | Date | Charge end date | NULL for ongoing | 2023-12-31 |
| monthly_amount | Decimal | Monthly charge amount | Can be positive/negative | 12500.00 |
| annual_amount | Decimal | Annual charge amount | monthly_amount * 12 | 150000.00 |
| psf_amount | Decimal | Per SF amount | annual_amount / SF | 30.00 |
| escalation_rate | Decimal | Annual increase % | 0-100 | 3.0 |
| escalation_type | Text | Escalation method | Fixed, CPI, Compounding | "Fixed" |
| billing_frequency | Text | Billing schedule | Monthly, Quarterly, Annual | "Monthly" |
| billing_in_advance | Boolean | Advance billing | True/False | TRUE |
| prorate_partial | Boolean | Prorate partial months | True/False | TRUE |
| is_recoverable | Boolean | Recoverable from tenant | True/False | FALSE |
| gl_account | Text | General ledger account | For revenue recognition | "4010-001" |

**Key Relationships**:
- dim_fp_amendmentsunitspropertytenant → dim_fp_amendmentchargeschedule (amendment_hmy)

### 11. dim_fp_buildingcustomdata
**Purpose**: Property-specific custom attributes and status information
**Grain**: One row per property
**Business Key**: hmy_property

| Column Name | Data Type | Description | Business Rules | Example Values |
|-------------|-----------|-------------|----------------|----------------|
| hmy_property | Integer | Property reference | Foreign key to property | 12345 |
| status | Text | Property status | Acquired, Sold, Development | "Acquired" |
| acq_date | Date | Acquisition date | Excel date format | 2020-03-15 |
| disposition_date | Date | Sale date | Excel date format, NULL if owned | NULL |
| disposition_price | Decimal | Sale price | > 0 if sold | NULL |
| market | Text | Market classification | Geographic market name | "Chicago" |
| submarket | Text | Submarket detail | More specific location | "Downtown Loop" |
| property_class | Text | Building class | Class A, B, C | "Class A" |
| construction_type | Text | Building construction | Steel, Concrete, etc. | "Steel Frame" |
| hvac_system | Text | Climate control | Central, VAV, etc. | "VAV" |
| elevator_count | Integer | Number of elevators | >= 0 | 4 |
| leed_rating | Text | LEED certification | Gold, Silver, Certified | "Gold" |
| energy_star_score | Integer | Energy Star rating | 1-100 | 85 |
| management_company | Text | Property manager | Management company name | "ABC Property Mgmt" |
| leasing_company | Text | Leasing agent | Leasing company name | "XYZ Leasing" |
| property_website | Text | Property website URL | Valid URL format | "www.property.com" |

**Key Relationships**:
- dim_property ← dim_fp_buildingcustomdata (hmy_property)

## Reference and Control Tables

### 12. dim_lastclosedperiod
**Purpose**: Control table indicating last closed accounting period
**Grain**: Single row (control table)

| Column Name | Data Type | Description | Business Rules | Example Values |
|-------------|-----------|-------------|----------------|----------------|
| last_closed_date | Date | Last closed period end | End of accounting period | 2024-01-31 |
| fiscal_year | Integer | Fiscal year | Current fiscal year | 2024 |
| fiscal_period | Integer | Fiscal period | 1-12 | 1 |
| is_year_end | Boolean | Year-end close indicator | True/False | FALSE |
| close_date | DateTime | When period was closed | Audit timestamp | 2024-02-05 08:30:00 |
| closed_by | Text | User who closed period | Audit trail | "jsmith" |

### 13. dim_fp_naics
**Purpose**: NAICS industry classification codes
**Grain**: One row per NAICS code

| Column Name | Data Type | Description | Business Rules | Example Values |
|-------------|-----------|-------------|----------------|----------------|
| naics_code | Text | NAICS classification code | 2-6 digit code | "541211" |
| naics_description | Text | Industry description | Official NAICS description | "Offices of Certified Public Accountants" |
| naics_level | Integer | Code hierarchy level | 2, 3, 4, 5, or 6 digit | 6 |
| parent_code | Text | Parent NAICS code | Higher level classification | "5412" |
| is_active | Boolean | Active code indicator | True/False | TRUE |

### 14. 'MRG (1Q25)'
**Purpose**: Market rent growth projections by market (2025-2035)
**Grain**: One row per market

| Column Name | Data Type | Description | Business Rules | Example Values |
|-------------|-----------|-------------|----------------|----------------|
| Market | Text | Market name | LMS naming convention | "Northern NJ" |
| 2025 | Text | 2025 growth rate | Percentage with % symbol | "3.5%" |
| 2026 | Text | 2026 growth rate | Percentage with % symbol | "3.2%" |
| 2027 | Text | 2027 growth rate | Percentage with % symbol | "2.9%" |
| 2028 | Text | 2028 growth rate | Percentage with % symbol | "2.8%" |
| 2029 | Text | 2029 growth rate | Percentage with % symbol | "2.7%" |
| 2030 | Text | 2030 growth rate | Percentage with % symbol | "2.6%" |
| 2031 | Text | 2031 growth rate | Percentage with % symbol | "2.5%" |
| 2032 | Text | 2032 growth rate | Percentage with % symbol | "2.4%" |
| 2033 | Text | 2033 growth rate | Percentage with % symbol | "2.3%" |
| 2034 | Text | 2034 growth rate | Percentage with % symbol | "2.2%" |
| 2035 | Text | 2035 growth rate | Percentage with % symbol | "2.1%" |

### 15. dim_market_data
**Purpose**: Market benchmark data for occupancy, size, and competitive positioning
**Grain**: One row per market
**Business Key**: market_name

| Column Name | Data Type | Description | Business Rules | Example Values |
|-------------|-----------|-------------|----------------|----------------|
| market_name | Text | Market name | Matches dim_fp_buildingcustomdata[market] | "Northern NJ/New York" |
| market_occupancy_benchmark | Decimal | Market average occupancy % | 0-100 range | 91.2 |
| market_size_sf | Integer | Total market square footage | Estimated market size | 50000000 |
| market_score | Integer | Overall market score | 0-100 scale | 100 |
| location_advantage_score | Integer | Premium location scoring | 0-20 scale | 20 |

**Usage Notes**:
- Replaces hard-coded market data in DAX measures
- Updated quarterly with market reports
- Default row provided for unmapped markets
- Join on market_name to dim_fp_buildingcustomdata[market]

## Data Type Standards and Formats

### Numeric Data Types
```
Integer: Whole numbers (IDs, counts, years)
- Range: -2,147,483,648 to 2,147,483,647
- Use for: Keys, counts, years, square footage

Decimal: Monetary and precise numeric values
- Precision: 18 digits, 2 decimal places typical
- Use for: Currency, percentages, rates, PSF amounts

Float: Approximate numeric values (rare usage)
- Use for: Calculated ratios, statistical measures
```

### Text Data Types
```
Text: Variable length strings
- Use for: Names, descriptions, codes, addresses
- Max length varies by column (typically 50-255 characters)

Fixed Length: Specific character requirements
- Use for: State codes (2 char), postal codes (5-10 char)
```

### Date Data Types
```
Date: Calendar dates without time
- Format: YYYY-MM-DD
- Use for: Transaction dates, lease dates, period dates

DateTime: Date and time combined
- Format: YYYY-MM-DD HH:MM:SS
- Use for: Audit timestamps, precise transaction timing

Excel Date: Numeric date format from Excel/Yardi
- Requires conversion: Date.From(Number.From(_) + #date(1899,12,30))
- Common in Yardi data exports
```

### Boolean Data Types
```
Boolean: True/False values
- Values: TRUE, FALSE, NULL
- Use for: Status flags, indicators, yes/no fields
```

## Data Quality Standards

### Completeness Requirements
```
Critical Fields (Must not be NULL):
- All primary and foreign keys
- Required business attributes (property names, tenant names)
- Financial amounts (can be zero but not null)
- Effective dates for time-sensitive records

Optional Fields (May be NULL):
- Secondary attributes (phone numbers, email addresses)
- End dates for ongoing relationships
- Future-dated or planned information
```

### Data Validation Rules
```
Referential Integrity:
- All foreign keys must reference valid parent records
- Orphaned records not permitted in production
- Cascade updates/deletes handled appropriately

Business Logic Validation:
- Dates: Start dates <= End dates
- Amounts: Reasonable ranges for each data type
- Percentages: 0-100 range unless otherwise specified
- Square Footage: Positive values, reasonable for property type
```

### Data Refresh Patterns
```
Real-time: Not applicable for this solution
Daily: Occupancy data, tenant changes
Weekly: Market data updates, benchmarking information
Monthly: Financial data, rent rolls, major property changes
Quarterly: Budget data, strategic metrics
Annually: Market projections, static reference data
```

## Usage Guidelines

### Query Performance Optimization
```
Indexing Strategy:
- Primary keys automatically indexed
- Foreign keys should be indexed
- Date columns used in filters should be indexed
- Composite indexes for multi-column filters

Query Best Practices:
- Filter on indexed columns when possible
- Use appropriate data types in joins
- Limit result sets with WHERE clauses
- Avoid functions in WHERE clauses that prevent index usage
```

### Data Security Classification
```
Public: General property information, market data
Internal: Detailed financial data, tenant information
Restricted: Strategic plans, acquisition targets
Confidential: Individual salary data, legal matters

Access Controls:
- Role-based access to sensitive data
- Row-level security for multi-tenant scenarios
- Audit logging for sensitive data access
- Regular access reviews and certifications
```

This comprehensive data dictionary serves as the authoritative reference for all data elements in the Yardi BI Power BI solution, ensuring consistent understanding and proper usage of data across all development and analysis activities.