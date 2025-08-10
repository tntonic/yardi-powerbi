# Faropoint Dashboard Visualizations Guide

## Overview
This directory contains 10 comprehensive PNG visualizations created from Faropoint's leasing data, covering 469 lease transactions across 15.3M square feet and $690M in total lease value.

## Portfolio Summary Statistics
- **Total Leases**: 469 transactions
- **Total Square Feet**: 15,328,755 SF
- **Total Portfolio Value**: $689,987,387
- **Average Rent PSF**: $9.00
- **Average Lease Term**: 53 months
- **Markets**: 20 geographic markets
- **Properties**: 330 unique properties
- **Funds**: 5 investment funds
- **Date Range**: Q2 2021 to Q2 2025

---

## Visualization Details

### 01_executive_dashboard.png
**Purpose**: High-level executive summary for C-suite and board presentations
**Contents**: 
- Key KPI cards (Total Leases, SF, WAR, Lease Term)
- Quarterly leasing volume trends
- Top 10 market distribution
- Deal type breakdown (pie chart)
- Average rent trends over time
- Fund performance comparison

**Best Used For**: 
- Board presentations
- Executive committee meetings
- Quarterly business reviews
- Investor updates

---

### 02_quarterly_trends.png
**Purpose**: Track portfolio performance over time
**Contents**:
- Quarterly leasing volume (SF)
- Average rent trends by quarter
- Number of deals per quarter
- Total lease value trends

**Best Used For**:
- Identifying seasonal patterns
- Performance trending analysis
- Budget vs actual comparisons
- Market cycle analysis

---

### 03_market_performance.png
**Purpose**: Compare performance across geographic markets
**Contents**:
- Top 10 markets by square footage
- Average rent by market
- Number of deals by market
- Total lease value by market

**Best Used For**:
- Market strategy decisions
- Geographic allocation planning
- Rent benchmarking
- Market opportunity assessment

---

### 04_top_tenants.png
**Purpose**: Analyze tenant concentration and performance
**Contents**:
- Top 15 tenants by square footage
- Top 15 tenants by lease value
- Tenant concentration risk (pie chart)
- Highest-paying tenants by rent PSF

**Best Used For**:
- Tenant retention planning
- Concentration risk assessment
- Renewal strategy development
- Credit risk analysis

---

### 05_lease_metrics.png
**Purpose**: Understand lease characteristics and distributions
**Contents**:
- Lease term distribution histogram
- Square footage distribution
- Starting rent distribution
- Rent vs. square footage correlation scatter plot

**Best Used For**:
- Portfolio composition analysis
- Lease structuring decisions
- Risk assessment
- Pricing strategy development

---

### 06_spread_analysis.png
**Purpose**: Analyze rent performance and deal type effectiveness
**Contents**:
- Rent spread distribution (where available)
- Performance by deal type
- Year-over-year comparison
- Top 10 properties by square footage

**Best Used For**:
- Mark-to-market analysis
- Deal type strategy
- Property performance evaluation
- Pricing optimization

---

### 07_fund_performance.png
**Purpose**: Compare performance across investment funds
**Contents**:
- Square footage distribution by fund (pie chart)
- Average rent by fund
- Number of deals by fund
- Total lease value by fund

**Best Used For**:
- Fund performance evaluation
- Investment strategy analysis
- Capital allocation decisions
- Fund comparison reporting

---

### 08_lease_expiration.png
**Purpose**: Assess portfolio rollover risk and timing
**Contents**:
- Lease expirations by year (SF and count)
- Downtime distribution analysis
- Large lease concentration risk (>50k SF)

**Best Used For**:
- Rollover risk management
- Leasing pipeline planning
- Vacancy forecasting
- Risk mitigation strategies

---

### 09_financial_performance.png
**Purpose**: Focus on financial metrics and revenue generation
**Contents**:
- Financial KPI cards (Portfolio Value, Deal Size, Revenue PSF)
- Quarterly revenue trends
- Deal size distribution
- Revenue by market and fund

**Best Used For**:
- Financial reporting
- Revenue optimization
- Deal sizing analysis
- Market revenue comparison

---

### 10_portfolio_heatmap.png
**Purpose**: Visual performance matrix across markets and funds
**Contents**:
- Heat map showing average rent PSF by market and fund
- Color-coded performance indicators
- Top markets vs. top funds analysis

**Best Used For**:
- Quick performance comparison
- Identifying high/low performing combinations
- Strategic decision making
- Visual trend identification

---

## Usage Guidelines

### For Executive Presentations
- Use **01_executive_dashboard.png** as the main summary slide
- Add **02_quarterly_trends.png** for performance context
- Include **09_financial_performance.png** for financial focus

### For Asset Management
- Start with **03_market_performance.png** for market overview
- Use **04_top_tenants.png** for tenant analysis
- Reference **08_lease_expiration.png** for rollover planning

### For Investment Committee
- Lead with **07_fund_performance.png** for fund comparison
- Include **05_lease_metrics.png** for portfolio composition
- Add **10_portfolio_heatmap.png** for visual performance matrix

### For Leasing Teams
- Focus on **06_spread_analysis.png** for pricing insights
- Use **03_market_performance.png** for market context
- Reference **04_top_tenants.png** for tenant relationships

## Technical Specifications

### File Format
- **Format**: PNG (high resolution)
- **Resolution**: 300 DPI
- **Color Space**: RGB
- **Background**: White
- **Size Range**: 276KB - 688KB per file

### Design Standards
- **Brand Colors**: Faropoint blue (#1f4e79), green (#2e8b57), orange (#ff6b35)
- **Typography**: Professional, clean fonts
- **Layout**: Consistent grid-based design
- **Accessibility**: High contrast, readable text

### Data Currency
- **Source**: all_leases_comprehensive_final.json
- **Last Updated**: July 25, 2025
- **Refresh Frequency**: Recommended quarterly
- **Validation**: Comprehensive data quality checks performed

## Integration Options

### PowerPoint/Keynote
- Direct PNG import for presentations
- Maintain high resolution for printing
- Combine multiple charts per slide as needed

### Web Dashboards
- Embed as static images
- Link to interactive versions
- Use as thumbnails for detailed views

### Reports
- Include in PDF reports
- Scale appropriately for document format
- Add captions and data sources

### Email Updates
- Attach key charts for stakeholder updates
- Resize for email-friendly viewing
- Include brief explanations

## Maintenance and Updates

### Monthly
- Review data accuracy
- Update trend arrows and indicators
- Validate calculation accuracy

### Quarterly
- Full data refresh with new lease data
- Recalculate all metrics
- Update chart ranges and scales
- Review and update color coding

### Annually
- Review chart types and layouts
- Update brand colors if needed
- Assess new visualization needs
- Archive previous versions

## Support and Troubleshooting

### Data Issues
- Verify source data integrity
- Check calculation formulas
- Validate date ranges and filters

### Display Issues
- Ensure proper PNG viewer
- Check resolution settings
- Verify color display accuracy

### Updates Needed
- Re-run create_dashboard_visualizations.py
- Update data source file path
- Modify chart parameters as needed

---

*Last Updated: July 25, 2025*
*Generated from 469 lease transactions covering $690M in portfolio value*