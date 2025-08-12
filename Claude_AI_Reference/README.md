 # Power BI Dashboard Reference Library for Claude.ai

## 🎯 Purpose

This is a curated reference library designed specifically for teams building Power BI dashboards with assistance from Claude.ai. The library contains production-ready DAX measures, comprehensive documentation, and validated implementation patterns for commercial real estate analytics using Yardi data.

## ⚠️ Critical Update: v5.1 Date Handling

**IMPORTANT**: As of v5.1, all DAX measures use the Yardi closed period date dynamically:
- **Old Pattern (v5.0)**: `VAR CurrentDate = TODAY()`
- **New Pattern (v5.1)**: `VAR CurrentDate = CALCULATE(MAX(dim_lastclosedperiod[last closed period]), ALL(dim_lastclosedperiod))`
- **Benefits**: Ensures consistency with Yardi financial reporting periods
- **Automatic Updates**: Date updates when Power BI data is refreshed
- **Required Table**: `dim_lastclosedperiod` must be in your data model

## 📚 How to Use with Claude.ai

### Setting Up Your Claude.ai Project

1. **Create a new project** in Claude.ai
2. **Upload this entire Claude_AI_Reference folder** to your project
3. **Reference these materials** when asking Claude questions about:
   - DAX measure creation
   - Dashboard design patterns
   - Data model relationships
   - Troubleshooting common issues
   - Performance optimization

### Best Practices for Asking Claude Questions

#### Effective Question Examples:
✅ "Using the Top 20 measures, create a KPI card for Current Monthly Rent"
✅ "Based on the Executive Dashboard template, how should I structure my filters?"
✅ "The rent roll accuracy is below 95% - what should I check based on Common Issues?"
✅ "How do I implement the amendment-based logic for rent roll calculations?"

#### Include Context:
- Specify which dashboard you're building (Executive, Financial, Leasing, Rent Roll)
- Mention your data source (Yardi tables) and any customizations
- State your accuracy requirements (95-99% for rent roll)
- Describe any error messages or unexpected results

## 📁 Library Structure

### DAX_Measures/ (Total: 257+ measures v5.1 including enhanced)
- **01_Core_Financial_Rent_Roll_Measures_v5.0.dax** - 42 core financial and rent roll measures
- **02_Leasing_Activity_Pipeline_Measures_v5.0.dax** - 85 leasing activity and pipeline measures
- **03_Credit_Risk_Tenant_Analysis_Measures_v5.0.dax** - 45 credit risk and tenant analysis measures (expanded with customer code mappings)
- **04_Net_Absorption_Fund_Analysis_Measures_v5.0.dax** - 35 net absorption and fund-specific measures
- **05_Performance_Validation_Measures_v5.0.dax** - 25 performance monitoring and validation measures
- **Top_20_Essential_Measures.dax** - Most commonly used measures (quick reference)
- **Validation_Measures.dax** - Testing and validation measures

### Enhanced Leasing Measures (New - 40+ additional measures):
- **../Enhanced_Leasing_Activity_Measures.dax** - Advanced leasing analytics including:
  - SF-weighted rent calculations for accurate portfolio averages
  - Lease vacancy downtime analysis (months between prior lease end and new lease start)
  - Lease spread vs prior lease with area weighting
  - Fund-specific measures for Fund 2 and Fund 3
  - Lost rent from downtime calculations
- **../Leasing_Activity_Downtime_Analysis.md** - Complete implementation guide

### Documentation/
- **01_Quick_Start_Guide.md** - Implementation timeline and checklist
- **02_Data_Model_Guide.md** - 32-table architecture details
- **03_Data_Dictionary.md** - Column definitions and data types (updated with v5.0 tables)
- **04_Implementation_Guide.md** - Step-by-step implementation
- **05_Business_Logic_Reference.md** - Comprehensive business logic for all calculations
- **06_Common_Issues_Solutions.md** - Troubleshooting guide

### Dashboard_Templates/
- **Executive_Summary_Dashboard.md** - C-suite level KPIs
- **Financial_Performance_Dashboard.md** - Revenue, expenses, NOI
- **Leasing_Activity_Dashboard.md** - New leases, renewals, terminations
- **Rent_Roll_Dashboard.md** - Current rent roll analysis

### Reference_Guides/
- **Account_Mapping_Reference.md** - GL account structure (4xxxx, 5xxxx)
- **Calculation_Patterns.md** - Common DAX patterns
- **Column_Name_Mapping.md** - PowerBI to Yardi field mapping
- **Granularity_Best_Practices.md** - Data granularity guidelines
- **Table_Relationships.md** - Data model relationships

### Validation_Framework/
- **Testing_Guide.md** - How to validate your implementation
- **Accuracy_Benchmarks.md** - Expected accuracy levels
- **Validation_Scripts.sql** - SQL scripts for data validation

## 🔑 Key Concepts to Remember

### 1. Amendment-Based Logic
The most critical innovation is using amendment tables for rent roll:
- Filter by **latest sequence** per property/tenant
- Include both **"Activated" AND "Superseded"** status
- This achieves 95-99% accuracy vs native Yardi

### 2. Revenue Sign Convention
- Revenue accounts (4xxxx) are stored as **negative** in GL
- Always **multiply by -1** for display in reports
- Operating expenses (5xxxx) are positive

### 3. Data Model Structure
- **32 optimized tables** in star schema
- **Single-direction relationships** except Calendar (bi-directional)
- **Hybrid approach**: Detail + pre-aggregated summary tables

### 4. Performance Standards
- Dashboard load: < 10 seconds
- Query response: < 5 seconds
- Data refresh: < 30 minutes
- Accuracy: 95-99% for critical metrics

## 💡 Quick Reference: Top 5 Most-Used Measures

1. **Total Revenue**: `SUM(fact_total[amount]) * -1` with account filtering
2. **NOI**: `[Total Revenue] - [Operating Expenses]`
3. **Physical Occupancy %**: `[Occupied Area] / [Rentable Area] * 100`
4. **Current Monthly Rent**: Amendment-based with charge schedule lookup
5. **Retention Rate %**: `[Renewals] / ([Renewals] + [Terminations]) * 100`

## ⚠️ Critical Implementation Notes

1. **Always validate** rent roll accuracy before deployment (95%+ required)
2. **Test with multiple periods** to ensure time intelligence works correctly
3. **Check amendment sequences** are properly filtered to latest
4. **Verify revenue signs** are handled correctly (negative to positive)
5. **Monitor performance** during development - refactor if >10 second loads

## 📊 Expected Outcomes

When properly implemented, this solution delivers:
- **97-99% accuracy** for rent roll vs native Yardi
- **97-98% accuracy** for leasing activity metrics
- **98%+ accuracy** for financial calculations
- **Real-time dashboards** replacing monthly Excel exports
- **Enhanced analytics** beyond standard Yardi reports
- **Month-to-month lease tracking** with proper identification

## 🆘 Getting Help

### When Working with Claude.ai:
1. Reference specific files from this library
2. Provide error messages and screenshots
3. Specify which measures or calculations are problematic
4. Include sample data if possible

### Common Starting Points:
- Begin with **01_Quick_Start_Guide.md** for initial setup
- Use **Top_20_Essential_Measures.dax** for basic dashboards
- Check **05_Common_Issues_Solutions.md** when troubleshooting
- Validate with scripts in **Validation_Framework/**

## 📈 Success Metrics

Your implementation is successful when:
- ✅ All 217+ DAX measures execute without errors
- ✅ Rent roll accuracy: 95-99% vs Yardi reports
- ✅ Dashboard performance: <10 second load times
- ✅ Users can self-serve analytics without IT support
- ✅ Monthly reporting time reduced by 70%+

---

**Version**: 5.1 Production Ready (Dynamic Date Handling)
**Last Updated**: 2025-08-10  
**Validated Against**: Yardi Voyager 7S with enhanced data integration
**Power BI Version**: Latest (2024.x or newer recommended)
**New in v5.1**: All measures now use `dim_lastclosedperiod` for dynamic date references (replacing TODAY())
**v5.0 Features**: Net absorption (FPR methodology), leasing spreads analysis, credit risk scoring, downtime tracking, comprehensive pipeline analytics, fund-specific enhanced filtering
