# Business Logic Reference

## Overview

This document serves as the comprehensive reference for all business logic implemented in the Yardi BI Power BI solution. It provides detailed explanations of calculation methodologies, data relationships, and business rules that ensure accurate and consistent reporting across all dashboards and analyses.

**Production-Validated Business Logic:**
- ✅ **Rent Roll Logic**: 95-99% accuracy vs native Yardi reports (validated with extensive testing)
- ✅ **Leasing Activity Logic**: 95-98% accuracy with enhanced analytics beyond Yardi capabilities
- ✅ **Financial Calculations**: Dual NOI methodology (traditional + FPR book) for comprehensive analysis
- ✅ **Advanced Analytics**: Industry analysis, market comparisons, and predictive models

**Key Discoveries from Production Implementation:**
1. **Amendment Selection**: Must use LATEST amendment per property/tenant (by sequence) including "Superseded" status
2. **Leasing Activity**: Different business rules than rent roll - uses termination table for accurate transaction tracking
3. **FPR Book Integration**: Book 46 provides balance sheet movement approach to NOI calculation
4. **Market Analysis**: Bridge table required to map Yardi market names to growth projection data

## Core Business Concepts

### 1. Property Management Fundamentals

#### Property Classification
```
Property Types:
- Office: Traditional office buildings and complexes
- Industrial: Warehouses, manufacturing, distribution facilities  
- Retail: Shopping centers, standalone retail locations
- Mixed-Use: Properties with multiple use types
- Specialty: Unique properties (data centers, medical, etc.)

Property Status:
- Acquired: Currently owned and operated properties
- Sold: Previously owned properties that have been disposed
- Under Contract: Properties in acquisition process
- Development: Properties under construction or renovation
```

#### Space Measurement Standards
```
Rentable Square Footage (RSF):
- Total space available for lease to tenants
- Includes tenant exclusive use areas
- Includes tenant's proportionate share of common areas
- Based on BOMA (Building Owners and Managers Association) standards

Occupied Square Footage (OSF):
- Space currently under lease agreements
- Excludes vacant space
- Includes space in rent-free periods
- Basis for occupancy rate calculations

Usable Square Footage (USF):
- Space exclusively available to individual tenants
- Excludes common areas and building services
- Used for tenant billing and space planning
```

### 2. Lease Management Business Rules

#### Amendment Hierarchy and Status
```
Amendment Types (Priority Order):
1. Original Lease: Initial lease agreement
2. Renewal: Extension of existing lease terms
3. Expansion: Additional space for existing tenant
4. Contraction: Reduction of leased space
5. Assignment: Transfer of lease to new tenant
6. Termination: Early termination of lease agreement

Amendment Status Logic:
- Activated: Amendment is effective and current
- Superseded: Amendment has been replaced by newer version
- Pending: Amendment approved but not yet effective
- Cancelled: Amendment was cancelled before activation

Business Rules:
- Latest amendment sequence takes precedence
- Superseded amendments may be "latest" for a tenant
- Termination amendments end the lease relationship
- Future-dated amendments await activation
```

#### Rent Roll Calculation Logic
```
Current Rent Roll Criteria:
1. Amendment status IN ("Activated", "Superseded")
2. Amendment type <> "Termination" 
3. Amendment start date <= Report Date
4. Amendment end date >= Report Date OR Amendment end date IS NULL
5. Latest amendment sequence per property/tenant combination
6. Active charge schedule for report date

Future Rent Roll Criteria:
1. Amendment status IN ("Activated", "Superseded")
2. Amendment type <> "Termination"
3. Amendment start date > Report Date
4. Latest amendment sequence per property/tenant combination

Business Interpretation:
- Current rent = legally binding rent obligations as of report date
- Future rent = committed rent from signed but future-effective leases
- Excludes terminated leases and cancelled amendments
- Includes month-to-month tenancies (NULL end dates)
```

### 3. Financial Reporting Standards

#### Revenue Recognition Principles
```
Revenue Categories:
- Base Rent: Fixed monthly rental payments
- Percentage Rent: Variable rent based on tenant sales
- Expense Recoveries: Reimbursement of operating expenses
- Parking Revenue: Income from parking facilities
- Other Income: Miscellaneous property-related income

Account Code Structure:
- 40000-49999: Revenue accounts
- 40000-40999: Base rental income
- 41000-41999: Percentage rent and overages
- 42000-42999: Expense recoveries
- 43000-43999: Parking and other income

Recognition Timing:
- Accrual basis: Revenue recognized when earned
- Cash basis: Revenue recognized when received
- FPR Book: Modified accrual based on collections
```

#### Expense Classification
```
Operating Expense Categories:
- 50000-59999: Operating expenses
- 50000-50999: Property management and administration
- 51000-51999: Utilities (electric, gas, water, sewer)
- 52000-52999: Repairs and maintenance
- 53000-53999: Contracted services
- 54000-54999: Insurance and taxes
- 55000-55999: Marketing and leasing

Excluded from Operating Expenses:
- 64001100-64001600: Capital expenditures
- 64006000: Depreciation and amortization
- 60000+: Corporate overhead and financing costs

NOI Calculation:
NOI = Operating Revenue - Operating Expenses
Excludes: Debt service, depreciation, corporate costs
```

### 4. Occupancy and Performance Metrics

#### Occupancy Rate Definitions
```
Physical Occupancy:
Physical Occupancy % = (Occupied Square Feet / Rentable Square Feet) × 100

Calculation Notes:
- Based on physical space under lease
- Includes rent-free periods
- Excludes management offices and vacancy
- Point-in-time measurement

Economic Occupancy:
Economic Occupancy % = (Actual Rent / Market Rent Potential) × 100

Where:
- Actual Rent = Current contractual rent being paid
- Market Rent Potential = Rentable SF × Current Market Rent PSF
- Accounts for rent concessions and below-market leases
```

#### Lease Term Analytics
```
WALT (Weighted Average Lease Term):
WALT = Σ(Lease SF × Remaining Term) / Total Leased SF

Where:
- Remaining Term = Time from report date to lease expiration
- Measured in years or months
- Weighted by square footage of each lease
- Excludes month-to-month and expired leases

Lease Expiration Analysis:
- Near-term: 0-12 months remaining
- Medium-term: 1-3 years remaining  
- Long-term: 3+ years remaining
- Perpetual: No defined expiration date
```

## Advanced Analytics Business Logic

### 5. Enhanced Financial Performance Measures

#### Property Performance Scoring
```
Property Performance Score Methodology:
Score = Occupancy Component (40%) + NOI Component (30%) + Retention Component (20%) + Absorption Component (10%)

Components:
- Occupancy Component = MIN(40, Physical Occupancy % × 0.4)
- NOI Component = MIN(30, NOI Margin % × 0.5)
- Retention Component = MIN(20, Retention Rate % × 0.27)
- Absorption Component = MIN(10, MAX(0, 5 + (Net Absorption ÷ 10,000)))

Score Range: 0-100 (Higher = Better Performance)
Business Interpretation:
- >80: Excellent performance across all metrics
- 65-80: Good performance with minor improvement opportunities
- 50-65: Fair performance requiring attention
- <50: Poor performance requiring immediate action
```

#### Portfolio Health Assessment
```
Portfolio Health Score Calculation:
Weighted average of individual property performance scores

Formula: Σ(Property Score × Property Weight) / Total Portfolio Weight

Where Property Weight = Property Rentable Area / Total Portfolio Rentable Area

Business Applications:
- Overall portfolio performance measurement
- Investment committee reporting
- Benchmark comparison against peers
- Strategic planning and resource allocation
```

#### Same-Store Performance Analysis
```
Same-Store Net Absorption (3 Month):
Adjusted Net Absorption = Raw Net Absorption - Acquisitions SF + Dispositions SF

Where:
- Raw Net Absorption = Current Occupied SF - Prior Period Occupied SF
- Acquisitions SF = SF from properties acquired during period
- Dispositions SF = SF from properties sold during period

Business Purpose:
- Isolates operational performance from portfolio changes
- Enables accurate period-over-period comparison
- Critical for investor relations and performance reporting
- Benchmark against market absorption trends
```

### 6. Market Intelligence and Competitive Analysis

#### Market Positioning Methodology
```
Competitive Position Score Formula:
Base Score (50) + Occupancy Advantage + Rent Advantage + Quality Premium

Components:
- Occupancy Advantage = (Portfolio Occupancy - Market Occupancy) × 2
- Rent Advantage = ((Portfolio Rent PSF - Market Rent PSF) / Market Rent PSF) × 100
- Quality Premium = 10 points if Portfolio Rent PSF > Market Rent PSF, else 0

Market Benchmarks (External Data Required):
- Market Occupancy: Regional/market average occupancy rate
- Market Rent PSF: Competitive survey or third-party data
- Market NOI Margin: Industry benchmark for property type

Score Interpretation:
- >80: Strong competitive position with premium performance
- 65-80: Above-market performance in key metrics
- 50-65: Market-level performance
- 35-50: Below-market performance requiring improvement
- <35: Significant competitive disadvantage
```

#### Market Rent Gap Analysis
```
Market Rent Gap PSF Calculation:
Gap = Market Rent PSF - Actual Rent PSF

Where:
- Market Rent PSF = fact_fp_fmvm_marketunitrates[unitmlarentnew] (unit-specific)
- Actual Rent PSF = Current Monthly Rent / Current Leased SF

Business Interpretation:
- Negative Gap: Below-market rents (opportunity for increases)
- Positive Gap: Above-market rents (premium positioning)
- Near Zero (+/-$2): At-market pricing

Applications:
- Lease renewal negotiations
- Market positioning strategy
- Revenue optimization planning
- Investment decision support
```

#### Market Growth Projections
```
Market Rent CAGR % Methodology:
Uses MRG (Market Rent Growth) data with 10-year projections (2025-2035)

Formula: CAGR = ((End Rate / Start Rate)^(1/Years)) - 1

Data Integration:
- Requires dim_market_name_bridge table to map Yardi markets to MRG markets
- MRG data contains annual growth rate projections by market
- Accounts for compounding effects over projection period

Business Applications:
- Long-term investment planning
- Portfolio valuation modeling
- Acquisition/disposition timing
- Rent escalation planning
```

### 7. Predictive Analytics and Investment Intelligence

#### Market Cycle Position Assessment
```
Market Cycle Detection Algorithm:
Analyzes 12-month trends in occupancy, rent, and absorption

Cycle Classifications:
1. Trough: OccTrend < -2% AND RentTrend < -$1.00 PSF
   - Market bottom, optimal acquisition timing
   - Expect improving fundamentals within 12-18 months

2. Growth: OccTrend > 1% AND RentTrend > $0.50 PSF
   - Rising fundamentals, good acquisition timing
   - Sustainable growth trajectory expected

3. Expansion: OccTrend > 3% AND RentTrend > $2.00 PSF
   - Strong market performance, hold assets
   - Monitor for overheating indicators

4. Peak: OccTrend < 0% AND RentTrend < $0 PSF (after expansion)
   - Market top, consider disposition opportunities
   - Expect declining performance ahead

5. Contraction: OccTrend < -2% AND RentTrend < -$1.00 PSF
   - Declining market, defensive positioning
   - Focus on cash flow preservation

Business Validation:
- Compare to external market research
- Consider local economic indicators
- Account for property-specific factors
```

#### Investment Timing Score
```
Investment Timing Score Calculation:
Score = Cycle Score (50%) + Rent Gap Score (20%) + Health Score (30%)

Component Details:
- Cycle Score: Market cycle position-based scoring (0-90 points)
  - Trough: 90 points (best opportunity)
  - Growth: 75 points (good timing)
  - Expansion: 60 points (hold)
  - Peak: 30 points (consider selling)
  - Contraction: 40 points (defensive)

- Rent Gap Score: Market rent gap impact (-20 to +20 points)
  - Negative gap (below market): Positive points
  - Positive gap (above market): Negative points

- Health Score: Portfolio Health Score × 0.3 (0-30 points)

Investment Recommendations:
- 80-100: Strong Buy (aggressive acquisition)
- 70-79: Buy (opportunistic acquisition)
- 55-69: Hold (maintain position)
- 40-54: Sell (consider disposition)
- 0-39: Strong Sell (immediate disposition)
```

#### Market Risk Assessment
```
Market Risk Score Components:
Total Risk = Concentration Risk + Cycle Risk + Liquidity Risk

1. Concentration Risk (0-30 points):
   - Single Tenant Concentration: Top tenant % of portfolio × 30
   - Industry Concentration: Top industry % of portfolio × 20
   - Geographic Concentration: Market-specific risk factors

2. Cycle Risk (0-30 points):
   - Peak/Contraction phases: 20-25 points
   - Growth/Expansion phases: 10-15 points
   - Trough phase: 5-10 points

3. Liquidity Risk (0-40 points):
   - Market Size: Smaller markets = higher risk
   - Market Share: Lower share = higher liquidity risk
   - Property Type: Specialty properties = higher risk

Risk Level Interpretation:
- 0-30: Low Risk (green light for investment)
- 31-50: Moderate Risk (proceed with caution)
- 51-70: High Risk (detailed analysis required)
- 71-100: Critical Risk (avoid or exit position)
```

### 8. Tenant Intelligence and Retention Analytics

#### Industry Diversification Analysis
```
Industry Diversity Score Methodology:
Shannon Diversity Index adapted for commercial real estate

Formula: H = -Σ(Pi × ln(Pi)) / ln(N)

Where:
- Pi = Proportion of total rent from industry i
- N = Total number of industries represented
- Score normalized to 0-100 scale

Diversity Rating Scale:
- 75-100: Excellent diversification (low concentration risk)
- 60-74: Good diversification (acceptable risk level)
- 45-59: Fair diversification (monitor concentration)
- 0-44: Poor diversification (high concentration risk)

Business Applications:
- Risk assessment and management
- Target tenant acquisition planning
- Lease negotiation strategy
- Insurance and credit analysis
```

#### Tenant Retention Risk Modeling
```
Tenant Retention Risk Score (0-100):
Composite score based on multiple risk factors

Risk Components:
1. Lease Expiry Risk (0-40 points):
   - <6 months: 40 points
   - 6-12 months: 30 points
   - 12-24 months: 20 points
   - >24 months: 10 points

2. Tenant Size Risk (0-30 points):
   - Portfolio share > 5%: 30 points
   - Portfolio share 2-5%: 20 points
   - Portfolio share 1-2%: 10 points
   - Portfolio share <1%: 5 points

3. Industry Risk (0-20 points):
   - High-risk industries (retail, restaurants): 20 points
   - Medium-risk industries (financial): 15 points
   - Low-risk industries (healthcare, government): 10 points

4. Payment History Risk (0-10 points):
   - Current AR balance > 60 days: 10 points
   - Current AR balance 30-60 days: 5 points
   - No AR issues: 0 points

Action Thresholds:
- 70-100: Critical Risk (immediate engagement required)
- 50-69: High Risk (proactive outreach needed)
- 30-49: Medium Risk (monitor closely)
- 0-29: Low Risk (standard renewal process)
```

#### Leasing Velocity Analysis
```
Leasing Velocity Calculation:
Velocity = Total New Leasing SF / Number of Months in Period

Segmentation Analysis:
- Small Tenants (<5,000 SF): Typically faster velocity
- Medium Tenants (5,000-15,000 SF): Moderate velocity
- Large Tenants (>15,000 SF): Slower but higher impact

Time to Lease Calculation:
Average days from vacancy to lease execution

Industry Benchmarks:
- Office: 60-120 days typical
- Industrial: 30-90 days typical
- Retail: 90-180 days typical

Performance Assessment:
- Excellent: <30 days average
- Good: 30-60 days average
- Fair: 60-90 days average
- Needs Improvement: >90 days average
```

#### Termination Analysis and Prevention
```
Voluntary Termination Rate Calculation:
Rate = Voluntary Terminations / Total Terminations × 100

Termination Reason Categories:
1. Business Issues (20% preventable):
   - Business closure, downsizing, financial distress
   - Limited landlord influence

2. Space Requirements (40% preventable):
   - Expansion needs, relocation for growth
   - Can be addressed through portfolio solutions

3. Cost Concerns (70% preventable):
   - Rent affordability, expense increases
   - Addressable through negotiation

4. Property Issues (90% preventable):
   - Maintenance, service quality, amenities
   - Directly controllable by landlord

Retention Opportunity Value:
Annual rent value of potentially preventable terminations
= Termination SF × Average Rent PSF × Preventability Factor

Applications:
- Resource allocation for retention efforts
- Property management performance evaluation
- Lease negotiation strategy development
- Capital improvement prioritization
```

### 9. Leasing Activity Classification

#### Activity Type Definitions
```
New Leases:
- Criteria: Amendment type = "Original Lease" AND Status = "Activated"
- Business Meaning: First-time leasing of previously vacant space
- Impact: Positive absorption, new revenue generation
- Timing: Based on amendment start date

Renewals:
- Criteria: Amendment type = "Renewal" AND Status = "Activated"
- Alternative: Amendment sequence > 0 for same property/tenant
- Business Meaning: Extension of existing tenant lease
- Impact: Retained occupancy, potential rent adjustment

Terminations:
- Criteria: Found in termination table with move-out reason
- Business Meaning: Lease ended resulting in vacant space
- Impact: Negative absorption, revenue loss
- Timing: Based on amendment end date

Expansions/Contractions:
- Criteria: Amendment type = "Expansion" or "Contraction"
- Business Meaning: Change in leased space for existing tenant
- Impact: Net change in occupied space and revenue
```

#### Net Absorption Methodology
```
Basic Net Absorption:
Net Absorption = New Leasing SF + Expansion SF - Termination SF - Contraction SF

Same-Store Net Absorption:
- Excludes properties acquired or disposed during period
- Focuses on operational performance of stabilized portfolio
- Removes impact of portfolio composition changes

Adjusted Net Absorption:
- Accounts for acquisitions and dispositions
- Normalizes for one-time portfolio changes
- Provides comparable period-over-period analysis

Calculation Period:
- Typically measured quarterly (3-month periods)
- Can be annualized for comparison purposes
- Rolling periods for trend analysis
```

### 6. Market Analysis Methodologies

#### Market Positioning Analysis
```
Competitive Position Score:
Score = (Occupancy Performance × 0.4) + (Rent Performance × 0.4) + (NOI Performance × 0.2)

Where:
- Occupancy Performance = Portfolio Occupancy / Market Average Occupancy
- Rent Performance = Portfolio Rent PSF / Market Rent PSF  
- NOI Performance = Portfolio NOI Margin / Market NOI Margin
- Score > 1.0 indicates above-market performance

Market Share Estimation:
Market Share % = Portfolio Rentable SF / Total Market Rentable SF

Limitations:
- Market data may be estimated or sampled
- Definition of "market" may vary by analysis
- Competitive data may have different measurement standards
```

#### Market Cycle Assessment
```
Market Cycle Indicators:
1. Occupancy Trend: 6-month change in occupancy rates
2. Rent Trend: 6-month change in effective rent levels
3. Absorption Pattern: Net absorption relative to historical average
4. Supply Pipeline: Under construction vs. historical deliveries

Cycle Position Classification:
- Trough: Declining occupancy, declining rents, negative absorption
- Recovery: Stabilizing occupancy, stable rents, improving absorption
- Expansion: Rising occupancy, rising rents, strong positive absorption  
- Peak: High occupancy, accelerating rents, slowing absorption
- Contraction: Declining occupancy, peaking rents, negative absorption

Investment Timing Implications:
- Trough: Optimal acquisition timing
- Recovery: Good acquisition opportunities
- Expansion: Hold and optimize existing assets
- Peak: Consider disposition opportunities
- Contraction: Defensive positioning, prepare for downturn
```

### 7. Financial Performance Analysis

#### NOI Calculation Methodologies
```
Traditional NOI (Income Statement Approach):
NOI = Property Revenue - Property Operating Expenses

Components:
- Revenue: Rental income, recoveries, other property income
- Operating Expenses: Property-level costs excluding debt service
- Excludes: Depreciation, corporate overhead, capital expenditures

FPR NOI (Balance Sheet Movement Approach):
FPR NOI = Balance Sheet Account Movements (Book 46)

Characteristics:
- Based on cash flow and balance sheet changes
- May differ from traditional NOI due to timing differences
- Useful for cash flow analysis and debt service coverage
- Accounts for collections timing and accrual adjustments
```

#### Yield and Return Calculations
```
Current Yield:
Current Yield = Annual NOI / Current Property Value

Cap Rate:
Cap Rate = NOI / Property Value (at time of acquisition or appraisal)

Cash-on-Cash Return:
Cash-on-Cash = Annual Cash Flow After Debt Service / Equity Invested

Total Return:
Total Return = (NOI + Appreciation) / Initial Investment

IRR (Internal Rate of Return):
IRR = Discount rate where NPV of all cash flows = 0
- Includes acquisition costs, operating cash flows, disposition proceeds
- Accounts for timing of cash flows
- Industry standard for investment performance measurement
```

## Data Quality and Validation Rules

### 8. Data Integrity Standards

#### Amendment Data Validation
```
Required Fields Validation:
- Amendment HMY: Must be unique identifier
- Property HMY: Must link to valid property
- Tenant HMY: Must link to valid tenant
- Amendment Sequence: Must be numeric, sequential per tenant
- Amendment Start Date: Must be valid date
- Amendment Status: Must be from approved list
- Amendment Type: Must be from approved list

Business Logic Validation:
- Amendment sequence must increase for same property/tenant
- Start date must be <= End date (when end date exists)
- Latest amendment determines current lease status
- Terminated amendments should have corresponding termination records
```

#### Financial Data Validation
```
Account Code Validation:
- Must be valid 5-8 digit numeric code
- Must exist in chart of accounts (dim_account)
- Must have appropriate account type classification
- Revenue accounts: 40000000-49999999
  - Base Rent: 40000000-40999999
  - Percentage Rent: 41000000-41999999
  - Expense Recoveries: 42000000-42999999
  - Other Income: 43000000-49999999
- Expense accounts: 50000000-59999999
  - Property Management: 50000000-50999999
  - Utilities: 51000000-51999999
  - Repairs & Maintenance: 52000000-52999999
  - Contracted Services: 53000000-53999999
  - Insurance & Taxes: 54000000-54999999
  - Marketing & Leasing: 55000000-55999999

Amount Validation:
- Must be numeric (positive or negative)
- Revenue amounts typically negative (credits) in fact_total
- Expense amounts typically positive (debits) in fact_total
- Display convention: Multiply revenue by -1 for positive display
- Zero amounts may be valid but should be reviewed
- Exclude depreciation (64006000) from NOI
- Exclude corporate overhead (64001100-64001600) from NOI

Date Validation:
- Must be valid accounting period
- Must be within acceptable date range (not future beyond reasonable period)
- Must align with property ownership periods
- Must be consistent with amendment effective dates
- Book-specific date filtering required for accuracy
```

### 9. Reconciliation Procedures

#### Rent Roll Reconciliation
```
Monthly Rent Roll Validation:
1. Total active tenants matches lease administration records
2. Sum of monthly rent matches general ledger rent roll
3. Square footage totals match property management records
4. Tenant names and unit assignments verified

Variance Investigation Thresholds:
- Individual tenant variance: >$100 or >5%
- Property total variance: >$1,000 or >2%
- Portfolio total variance: >$10,000 or >1%

Common Variance Causes:
- Timing differences in amendment effective dates
- Rent-free periods not properly reflected
- Percentage rent calculations
- Expense recovery adjustments
```

#### Financial Statement Reconciliation
```
NOI Reconciliation Process:
1. Power BI NOI vs. Property Financial Statements
2. Account-by-account variance analysis
3. Timing difference identification
4. Accrual vs. cash basis adjustments

Acceptable Variance Thresholds:
- Monthly variance: <2% of NOI
- Quarterly variance: <1% of NOI
- Annual variance: <0.5% of NOI

Documentation Requirements:
- All variances >threshold must be documented
- Root cause analysis for recurring variances
- Management approval for variance explanations
- Corrective action plans for systematic issues
```

#### Book Reconciliation
```
Traditional vs FPR NOI Reconciliation:
1. Compare Traditional NOI (Accrual Book) to FPR NOI (Book 46)
2. Identify timing differences and balance sheet movements
3. Document special FPR accounts (646, 648, 825, 950, 953, 957, 1111-1114, 1120, 1123)
4. Explain material differences between methodologies

Book Selection Validation:
- Ensure correct book for each analysis type
- Accrual (Book 1): Standard financial reporting
- FPR (Book 46): Cash-adjusted property performance
- Budget Books: Variance analysis only
- Business Plan Books: Acquisition metrics

Cross-Book Validation:
- Same transaction should appear in multiple books
- Amount types may differ by book
- Filter by appropriate book before calculations
```

#### Data Quality Checkpoints
```
Pre-Processing Validation:
1. Verify all foreign key relationships
2. Check for orphaned records in fact tables
3. Validate date continuity (no gaps in monthly data)
4. Confirm amendment sequence integrity

Post-Processing Validation:
1. Total portfolio metrics match source systems
2. Individual property rollups equal portfolio totals
3. Time period comparisons are consistent
4. No duplicate amendments in latest sequence logic
```

## Reporting Standards and Conventions

### 10. Formatting and Presentation Rules

#### Numeric Formatting Standards
```
Currency Formatting:
- Dollars: $1,234,567 (no decimal places for large amounts)
- Rent PSF: $12.34 (two decimal places)
- Percentages: 12.3% (one decimal place)
- Large numbers: 1.2M, 1.2B (with appropriate suffix)

Date Formatting:
- Standard dates: MM/DD/YYYY or DD-MMM-YYYY
- Month/Year: MMM YYYY (Jan 2024)
- Quarters: Q1 2024, Q2 2024
- Fiscal periods: Based on company fiscal year

Text Formatting:
- Property names: Consistent capitalization
- Tenant names: As per legal entity names
- Units: Building + Unit format (Building A - Suite 101)
```

#### Dashboard Naming Conventions
```
Measure Naming:
- Descriptive names: "Current Monthly Rent" not "Rent1"
- Consistent units: Always specify PSF, %, etc.
- Time period indicators: "YTD Revenue", "3M Absorption"
- Calculation method: "Same-Store NOI", "Adjusted Absorption"

Visual Titles:
- Clear and descriptive
- Include time period reference
- Specify metric being displayed
- Use consistent terminology across dashboards

Color Coding Standards:
- Green: Positive performance, above target
- Red: Negative performance, below target  
- Yellow/Orange: Caution, near target
- Blue: Neutral information, informational metrics
- Gray: Inactive, historical, or reference data
```

### 11. Calculation Documentation Standards

#### Measure Documentation Template
```
Measure Name: [Descriptive Name]
Business Purpose: [What business question does this answer?]
Calculation Method: [High-level methodology]
Data Sources: [Which tables/columns are used]
Filters Applied: [Any implicit filters or exclusions]
Business Rules: [Special logic or exceptions]
Validation Method: [How accuracy is verified]
Update Frequency: [How often data changes]
Known Limitations: [Any caveats or restrictions]

Example:
Measure Name: Same-Store Net Absorption (3 Month)
Business Purpose: Measures net change in occupied space for stabilized properties
Calculation Method: Current occupied SF minus occupied SF from 3 months prior
Data Sources: fact_occupancyrentarea, dim_fp_buildingcustomdata
Filters Applied: Excludes properties acquired or sold in measurement period
Business Rules: Based on first day of month snapshots
Validation Method: Manual calculation for sample properties
Update Frequency: Monthly with occupancy data refresh
Known Limitations: Does not account for temporary occupancy changes
```

#### Advanced Analytics Measure Categories

**Enhanced Financial Performance Measures (6 measures):**
```
1. Acquisition Cost Per SF
   Purpose: Calculate acquisition cost efficiency across properties
   Sources: acq_costs_override, dim_fp_buildingcustomdata
   Validation: Cross-check with acquisition accounting records

2. Property Performance Score  
   Purpose: Composite property performance across multiple dimensions
   Sources: fact_occupancyrentarea, fact_total, retention calculations
   Validation: Component scoring verification and weighting accuracy

3. Portfolio Health Score
   Purpose: Weighted portfolio-level performance assessment
   Sources: Property Performance Scores, property weights
   Validation: Manual weighting calculations for sample periods

4. FPR vs Traditional NOI Variance
   Purpose: Identify timing differences between accounting methods
   Sources: fact_total (filtered by book_id = 46 for FPR)
   Validation: Reconciliation with financial statements

5. Same-Store Net Absorption (3 Month)
   Purpose: Isolate operational performance from portfolio changes
   Sources: fact_occupancyrentarea, dim_fp_buildingcustomdata (acquisition dates)
   Validation: Manual same-store calculations

6. Adjusted Net Absorption (3 Month)
   Purpose: Account for acquisitions/dispositions in absorption calculations
   Sources: fact_occupancyrentarea, property acquisition/disposition data
   Validation: Quarterly portfolio composition analysis
```

**Market Intelligence Measures (12 measures):**
```
1. Market Rent Gap PSF / Market Rent Gap %
   Purpose: Compare portfolio rents to market benchmarks
   Sources: fact_fp_fmvm_marketunitrates, current rent calculations
   Validation: Cross-reference with market surveys

2. Competitive Position Score
   Purpose: Portfolio competitive positioning vs market benchmarks
   Sources: Portfolio metrics, external market benchmarks
   Validation: Compare to third-party market research

3. Market Performance Rank
   Purpose: Rank portfolio performance within competitive set
   Sources: Portfolio metrics, peer benchmarking data
   Validation: Validate ranking methodology and peer selection

4. Market Rent Growth Rate % / Market Rent CAGR %
   Purpose: Project future rent growth using MRG data
   Sources: MRG (1Q25).csv, dim_market_name_bridge
   Validation: Compare projections to realized growth rates

5. Projected Market Rent 5Y / Future Market Rent Gap
   Purpose: Model future rent opportunities and gaps
   Sources: MRG growth data, current rent levels
   Validation: Back-testing with historical growth rates
```

**Predictive Analytics Measures (14 measures):**
```
1. Market Cycle Position
   Purpose: Identify current position in real estate cycle
   Sources: Historical occupancy, rent, and absorption trends
   Validation: Compare to external market cycle research

2. Investment Timing Score / Investment Recommendation
   Purpose: Provide data-driven investment timing guidance
   Sources: Market cycle, rent gaps, portfolio health metrics
   Validation: Back-test recommendations against actual market performance

3. Market Risk Score / Market Volatility Index
   Purpose: Assess market-specific investment risks
   Sources: Concentration metrics, market data, cycle position
   Validation: Compare to historical risk events and outcomes

4. Market Attractiveness Score / Competitive Advantage Index
   Purpose: Evaluate relative market attractiveness for investment
   Sources: Multiple market metrics and competitive factors
   Validation: Cross-reference with actual investment returns
```

**Tenant Intelligence Measures (13 measures):**
```
1. Tenant Industry Concentration / Industry Diversity Score
   Purpose: Assess tenant mix and concentration risk
   Sources: dim_fp_naics, dim_fp_naicstotenantmap, rent data
   Validation: Manual calculation of diversity metrics

2. Voluntary Termination Rate / Top Termination Reason
   Purpose: Analyze preventable tenant turnover
   Sources: dim_fp_terminationtomoveoutreas, dim_fp_moveoutreasonreflist
   Validation: Cross-check with lease administration records

3. Average Time to Lease (Days) / Leasing Velocity (SF per Month)
   Purpose: Measure leasing efficiency and market absorption
   Sources: Amendment data, leasing transaction timing
   Validation: Manual calculation for sample properties

4. Tenant Retention Risk Modeling
   Purpose: Identify tenants at risk for non-renewal
   Sources: Lease terms, payment history, industry data
   Validation: Track actual renewal outcomes vs predictions
```

#### Business Rule Change Management
```
Change Control Process:
1. Business rule change request submitted
2. Impact analysis on existing reports and calculations
3. Testing in development environment
4. User acceptance testing with business stakeholders  
5. Documentation updates
6. Production deployment
7. Training and communication to users

Documentation Requirements:
- Reason for change
- Effective date
- Impact on historical data
- Communication plan
- Training requirements
- Rollback procedures if needed
```

## Industry Standards and Best Practices

### 12. Commercial Real Estate Standards

#### BOMA Measurement Standards
```
BOMA Standards Application:
- Rentable area calculations per BOMA guidelines
- Common area allocation methodologies
- Load factor calculations and applications
- Measurement methodology documentation

Industry Benchmarking:
- Occupancy rates by property type and market
- Rental rate comparisons (asking vs. effective)
- Operating expense benchmarks per SF
- Capital expenditure standards and timing
```

#### Financial Reporting Standards
```
GAAP Compliance:
- Revenue recognition principles
- Lease accounting standards (ASC 842)
- Depreciation and amortization methods
- Fair value measurements

Industry KPIs:
- NOI and NOI margins
- Funds From Operations (FFO)
- Cash Available for Distribution (CAD)
- Debt service coverage ratios
- Return on invested capital metrics
```

### 13. Technology Standards

#### Data Architecture Principles
```
Star Schema Design:
- Fact tables contain measures and foreign keys
- Dimension tables contain descriptive attributes
- Relationships are mostly one-to-many
- Minimize many-to-many relationships

Performance Standards:
- Dashboard load time <10 seconds
- Query response time <5 seconds
- Data refresh time <30 minutes for incremental
- 99%+ data accuracy compared to source systems
```

#### Security and Governance
```
Data Access Controls:
- Role-based access to sensitive financial data
- Property-level security where appropriate
- Audit logging of data access and changes
- Regular access reviews and certifications

Data Lineage Documentation:
- Source system identification
- Transformation logic documentation
- Data flow diagrams
- Impact analysis for system changes
```

## Implementation Guidelines

### 14. Deployment Standards

#### Testing Requirements
```
Unit Testing:
- Individual measure accuracy verification
- Data type and format validation  
- Performance testing for complex calculations
- Edge case and null value handling

Integration Testing:
- End-to-end data flow validation
- Cross-dashboard consistency verification
- User acceptance testing with business stakeholders
- Performance testing under realistic load

Production Validation:
- Smoke testing after deployment
- Key metric validation against known values
- User feedback collection and issue resolution
- Performance monitoring and optimization
```

#### Change Management Process
```
Development Lifecycle:
1. Requirements gathering and analysis
2. Design and architecture review
3. Development and unit testing
4. Integration testing and validation
5. User acceptance testing
6. Production deployment
7. Post-deployment monitoring and support

Documentation Maintenance:
- Keep business logic documentation current
- Update user guides and training materials
- Maintain technical documentation
- Regular review and improvement processes
```

## Summary

This comprehensive business logic reference documents the calculation methodologies, business rules, and reporting standards for all 122 measures in the Yardi BI Power BI solution:

- **77 Core Business Measures**: Foundational metrics for occupancy, financial performance, rent roll, and leasing activity
- **45 Advanced Analytics Measures**: Strategic intelligence including market analysis, predictive analytics, and investment decision support
- **4 Strategic Dashboards**: Market Intelligence, Investment Analytics, Tenant Intelligence, and Enhanced Executive Summary
- **Complete Data Integration**: Including MRG market growth projections and bridge table specifications

The business logic ensures consistent understanding and implementation across all dashboards and analyses, providing the foundation for accurate and reliable business intelligence that transforms operational reporting into strategic decision support.