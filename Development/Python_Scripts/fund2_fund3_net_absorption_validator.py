#!/usr/bin/env python3
"""
Fund 2 & Fund 3 Net Absorption Validator
Tests Same-Store Net Absorption measures against FPR Q1/Q2 2025 benchmarks for both funds.

Target values from FPR CSV:
- Fund 2 Q1 2025: Gross 198,000 SF, Move-Outs 712,000 SF, Net -514,000 SF
- Fund 2 Q2 2025: Gross 258,000 SF, Move-Outs 458,000 SF, Net -200,000 SF  
- Fund 3 Q1 2025: Gross 365,000 SF, Move-Outs 111,000 SF, Net 254,000 SF
- Fund 3 Q2 2025: Gross 112,000 SF, Move-Outs 250,600 SF, Net -138,600 SF

Author: Claude Code
Date: 2025-08-10
"""

import pandas as pd
import numpy as np
from datetime import datetime, date
import json
import sys
import os

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class MultiFundNetAbsorptionValidator:
    """Validates same-store net absorption for Fund 2 and Fund 3"""
    
    def __init__(self):
        """Initialize validator with FPR benchmarks"""
        # FPR benchmarks from CSV
        self.benchmarks = {
            'Fund 2': {
                'Q1 2025': {
                    'period_start': pd.Timestamp('2025-01-01'),
                    'period_end': pd.Timestamp('2025-03-31'),
                    'Gross Absorption SF': 198_000,
                    'Move-Outs SF': 712_000,
                    'Net Absorption': -514_000,
                    'Contract Occupancy %': 90.1,
                    'Adjusted Occupancy %': 88.3
                },
                'Q2 2025': {
                    'period_start': pd.Timestamp('2025-04-01'),
                    'period_end': pd.Timestamp('2025-06-30'),
                    'Gross Absorption SF': 258_000,
                    'Move-Outs SF': 458_000,
                    'Net Absorption': -200_000,
                    'Contract Occupancy %': 89.1,
                    'Adjusted Occupancy %': 88.1
                }
            },
            'Fund 3': {
                'Q1 2025': {
                    'period_start': pd.Timestamp('2025-01-01'),
                    'period_end': pd.Timestamp('2025-03-31'),
                    'Gross Absorption SF': 365_000,
                    'Move-Outs SF': 111_000,
                    'Net Absorption': 254_000,
                    'Contract Occupancy %': 93.4
                },
                'Q2 2025': {
                    'period_start': pd.Timestamp('2025-04-01'),
                    'period_end': pd.Timestamp('2025-06-30'),
                    'Gross Absorption SF': 112_000,
                    'Move-Outs SF': 250_600,
                    'Net Absorption': -138_600,
                    'Contract Occupancy %': 93.0,
                    'Adjusted Occupancy %': 92.9
                }
            }
        }
        
        # Data file paths
        self.base_path = "/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Data"
        self.fund2_path = f"{self.base_path}/Fund2_Filtered"
        self.yardi_path = f"{self.base_path}/Yardi_Tables"
        
        # Initialize results storage
        self.test_results = {}
        self.validation_errors = []
        
    def load_data(self):
        """Load all required data sources"""
        try:
            print("Loading data sources...")
            
            # Fund 2 filtered data
            if os.path.exists(f"{self.fund2_path}/dim_fp_amendmentsunitspropertytenant_fund2.csv"):
                self.amendments_fund2 = pd.read_csv(f"{self.fund2_path}/dim_fp_amendmentsunitspropertytenant_fund2.csv")
                self.properties_fund2 = pd.read_csv(f"{self.fund2_path}/dim_property_fund2.csv")
                print(f"Loaded Fund 2 amendments: {len(self.amendments_fund2):,} records")
                print(f"Loaded Fund 2 properties: {len(self.properties_fund2):,} records")
            else:
                print("Fund 2 filtered data not found, using full data")
                self.amendments_fund2 = None
                self.properties_fund2 = None
            
            # Full data sources
            self.amendments_all = pd.read_csv(f"{self.yardi_path}/dim_fp_amendmentsunitspropertytenant.csv")
            self.terminations = pd.read_csv(f"{self.yardi_path}/dim_fp_terminationtomoveoutreas.csv")
            self.properties_all = pd.read_csv(f"{self.yardi_path}/dim_property.csv")
            self.charge_schedule = pd.read_csv(f"{self.yardi_path}/dim_fp_amendmentchargeschedule.csv")
            
            print(f"Loaded all amendments: {len(self.amendments_all):,} records")
            print(f"Loaded terminations: {len(self.terminations):,} records")
            print(f"Loaded all properties: {len(self.properties_all):,} records")
            
            # Convert date columns
            self._convert_dates()
            
            # Identify fund properties
            self._identify_fund_properties()
            
            return True
            
        except Exception as e:
            self.validation_errors.append(f"Data loading error: {str(e)}")
            print(f"ERROR: {str(e)}")
            return False
            
    def _convert_dates(self):
        """Convert date columns to proper datetime format"""
        try:
            # Amendment dates
            date_cols_amendments = ['amendment start date', 'amendment end date', 'amendment sign date']
            for df in [self.amendments_all, self.amendments_fund2]:
                if df is not None:
                    for col in date_cols_amendments:
                        if col in df.columns:
                            df[col] = pd.to_datetime(df[col], errors='coerce')
            
            # Termination dates
            date_cols_terminations = ['amendment start date', 'amendment end date', 'amendment sign date']
            for col in date_cols_terminations:
                if col in self.terminations.columns:
                    self.terminations[col] = pd.to_datetime(self.terminations[col], errors='coerce')
                    
            # Property dates
            date_cols_property = ['acquire date', 'dispose date', 'in service date']
            for df in [self.properties_all, self.properties_fund2]:
                if df is not None:
                    for col in date_cols_property:
                        if col in df.columns:
                            df[col] = pd.to_datetime(df[col], errors='coerce')
                            
        except Exception as e:
            print(f"Date conversion warning: {str(e)}")
            
    def _identify_fund_properties(self):
        """Identify properties belonging to each fund"""
        print("\nIdentifying fund properties...")
        
        # Look for fund indicators in property data
        if 'fund' in self.properties_all.columns:
            self.fund2_properties = self.properties_all[
                self.properties_all['fund'].str.contains('2', na=False) |
                self.properties_all['fund'].str.contains('Fund 2', na=False)
            ]['property id'].unique()
            
            self.fund3_properties = self.properties_all[
                self.properties_all['fund'].str.contains('3', na=False) |
                self.properties_all['fund'].str.contains('Fund 3', na=False)
            ]['property id'].unique()
        else:
            # Use Fund 2 filtered data if available
            if self.properties_fund2 is not None:
                self.fund2_properties = self.properties_fund2['property id'].unique()
                print(f"Fund 2 properties from filtered data: {len(self.fund2_properties)}")
            else:
                # Try to infer from property codes or names
                self.fund2_properties = self.properties_all[
                    self.properties_all['property code'].str.startswith(('xfl', 'xnj', 'xtn'), na=False)
                ]['property id'].unique()
                
            # Fund 3 properties (need to identify pattern)
            self.fund3_properties = self.properties_all[
                ~self.properties_all['property id'].isin(self.fund2_properties)
            ]['property id'].unique()[:20]  # Take subset for testing
            
        print(f"Identified Fund 2 properties: {len(self.fund2_properties)}")
        print(f"Identified Fund 3 properties: {len(self.fund3_properties)}")
        
    def calculate_same_store_properties(self, fund, period_start, period_end):
        """Identify same-store properties for a specific fund and period"""
        
        if fund == 'Fund 2':
            fund_properties = self.fund2_properties
        else:
            fund_properties = self.fund3_properties
            
        # Filter to fund properties
        fund_props_df = self.properties_all[
            self.properties_all['property id'].isin(fund_properties)
        ]
        
        # Same-store criteria: acquired before period start, not disposed during period
        same_store = fund_props_df[
            (fund_props_df['acquire date'] < period_start) &
            (
                fund_props_df['dispose date'].isna() |
                (fund_props_df['dispose date'] > period_end)
            )
        ]
        
        # Get property codes for joining with amendments
        return same_store['property code'].unique()
        
    def calculate_sf_expired(self, fund, quarter):
        """Calculate SF Expired (Move-Outs) for a fund and quarter"""
        
        benchmark = self.benchmarks[fund][quarter]
        period_start = benchmark['period_start']
        period_end = benchmark['period_end']
        
        # Get same-store property codes
        same_store_prop_codes = self.calculate_same_store_properties(fund, period_start, period_end)
        
        # Filter terminations to period and same-store properties (using property code)
        period_terminations = self.terminations[
            (self.terminations['amendment end date'] >= period_start) &
            (self.terminations['amendment end date'] <= period_end) &
            (self.terminations['amendment status'].isin(['Activated', 'Superseded'])) &
            (self.terminations['amendment type'] == 'Termination') &
            (self.terminations['property code'].isin(same_store_prop_codes))
        ]
        
        # Get latest amendment sequence per property/tenant
        if len(period_terminations) > 0:
            latest_terminations = period_terminations.sort_values('amendment sequence').groupby(
                ['property hmy', 'tenant hmy']
            ).last()
            
            sf_expired = latest_terminations['amendment sf'].sum()
        else:
            sf_expired = 0
            
        return sf_expired, len(period_terminations)
        
    def calculate_sf_commenced(self, fund, quarter):
        """Calculate SF Commenced (Gross Absorption) for a fund and quarter"""
        
        benchmark = self.benchmarks[fund][quarter]
        period_start = benchmark['period_start']
        period_end = benchmark['period_end']
        
        # Get same-store property codes
        same_store_prop_codes = self.calculate_same_store_properties(fund, period_start, period_end)
        
        # Filter new leases to period and same-store properties (using property code)
        period_new_leases = self.amendments_all[
            (self.amendments_all['amendment start date'] >= period_start) &
            (self.amendments_all['amendment start date'] <= period_end) &
            (self.amendments_all['amendment status'].isin(['Activated', 'Superseded'])) &
            (self.amendments_all['amendment type'].isin(['Original Lease', 'New Lease'])) &
            (self.amendments_all['property code'].isin(same_store_prop_codes))
        ]
        
        # Filter to amendments with rent charges
        if len(period_new_leases) > 0:
            # Check for rent charges
            amendments_with_charges = []
            for _, lease in period_new_leases.iterrows():
                has_charge = len(self.charge_schedule[
                    (self.charge_schedule['amendment hmy'] == lease['amendment hmy']) &
                    (self.charge_schedule['charge code'] == 'rent')
                ]) > 0
                if has_charge:
                    amendments_with_charges.append(lease['amendment hmy'])
            
            period_new_leases = period_new_leases[
                period_new_leases['amendment hmy'].isin(amendments_with_charges)
            ]
            
            # Get latest amendment sequence per property/tenant
            latest_new_leases = period_new_leases.sort_values('amendment sequence').groupby(
                ['property hmy', 'tenant hmy']
            ).last()
            
            sf_commenced = latest_new_leases['amendment sf'].sum()
        else:
            sf_commenced = 0
            
        return sf_commenced, len(period_new_leases)
        
    def run_validation(self):
        """Run validation for all funds and quarters"""
        
        print("\n" + "="*80)
        print("FUND 2 & FUND 3 NET ABSORPTION VALIDATION")
        print("="*80)
        
        results = {}
        
        for fund in ['Fund 2', 'Fund 3']:
            print(f"\n{fund} Validation")
            print("-" * 40)
            
            fund_results = {}
            
            for quarter in ['Q1 2025', 'Q2 2025']:
                print(f"\n{quarter}:")
                
                benchmark = self.benchmarks[fund][quarter]
                
                # Calculate metrics
                sf_expired, expired_count = self.calculate_sf_expired(fund, quarter)
                sf_commenced, commenced_count = self.calculate_sf_commenced(fund, quarter)
                net_absorption = sf_commenced - sf_expired
                
                # Compare to benchmarks
                expired_variance = sf_expired - benchmark['Move-Outs SF']
                expired_accuracy = (1 - abs(expired_variance) / benchmark['Move-Outs SF']) * 100 if benchmark['Move-Outs SF'] > 0 else 0
                
                commenced_variance = sf_commenced - benchmark['Gross Absorption SF']
                commenced_accuracy = (1 - abs(commenced_variance) / benchmark['Gross Absorption SF']) * 100 if benchmark['Gross Absorption SF'] > 0 else 0
                
                net_variance = net_absorption - benchmark['Net Absorption']
                net_accuracy = (1 - abs(net_variance) / abs(benchmark['Net Absorption'])) * 100 if benchmark['Net Absorption'] != 0 else 0
                
                # Store results
                quarter_results = {
                    'SF Expired (Actual)': sf_expired,
                    'SF Expired (Target)': benchmark['Move-Outs SF'],
                    'SF Expired Variance': expired_variance,
                    'SF Expired Accuracy': expired_accuracy,
                    'SF Commenced (Actual)': sf_commenced,
                    'SF Commenced (Target)': benchmark['Gross Absorption SF'],
                    'SF Commenced Variance': commenced_variance,
                    'SF Commenced Accuracy': commenced_accuracy,
                    'Net Absorption (Actual)': net_absorption,
                    'Net Absorption (Target)': benchmark['Net Absorption'],
                    'Net Absorption Variance': net_variance,
                    'Net Absorption Accuracy': net_accuracy,
                    'Records': {
                        'Terminations': expired_count,
                        'New Leases': commenced_count
                    }
                }
                
                fund_results[quarter] = quarter_results
                
                # Print results
                print(f"  Move-Outs (Expired):    {sf_expired:>10,.0f} SF | Target: {benchmark['Move-Outs SF']:>10,.0f} | Accuracy: {expired_accuracy:>6.1f}%")
                print(f"  Gross Absorption:       {sf_commenced:>10,.0f} SF | Target: {benchmark['Gross Absorption SF']:>10,.0f} | Accuracy: {commenced_accuracy:>6.1f}%")
                print(f"  Net Absorption:         {net_absorption:>10,.0f} SF | Target: {benchmark['Net Absorption']:>10,.0f} | Accuracy: {net_accuracy:>6.1f}%")
                
            results[fund] = fund_results
            
        self.test_results = results
        return results
        
    def generate_report(self):
        """Generate detailed validation report"""
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = f"""# Fund 2 & Fund 3 Net Absorption Validation Report

**Test Date:** {timestamp}
**Test Periods:** Q1 2025 (Jan-Mar) and Q2 2025 (Apr-Jun)
**Data Source:** Yardi PowerBI Data Model

## Executive Summary

This validation tests Same-Store Net Absorption measures for Fund 2 and Fund 3 against FPR benchmarks.

## Fund 2 Results

### Q1 2025 (January 1 - March 31, 2025)
"""
        
        if 'Fund 2' in self.test_results:
            f2q1 = self.test_results['Fund 2']['Q1 2025']
            report += f"""
| Metric | Actual | Target | Variance | Accuracy |
|--------|--------|--------|----------|----------|
| Move-Outs (SF Expired) | {f2q1['SF Expired (Actual)']:,.0f} | {f2q1['SF Expired (Target)']:,.0f} | {f2q1['SF Expired Variance']:+,.0f} | {f2q1['SF Expired Accuracy']:.1f}% |
| Gross Absorption (SF Commenced) | {f2q1['SF Commenced (Actual)']:,.0f} | {f2q1['SF Commenced (Target)']:,.0f} | {f2q1['SF Commenced Variance']:+,.0f} | {f2q1['SF Commenced Accuracy']:.1f}% |
| Net Absorption | {f2q1['Net Absorption (Actual)']:,.0f} | {f2q1['Net Absorption (Target)']:,.0f} | {f2q1['Net Absorption Variance']:+,.0f} | {f2q1['Net Absorption Accuracy']:.1f}% |
"""
            
            f2q2 = self.test_results['Fund 2']['Q2 2025']
            report += f"""
### Q2 2025 (April 1 - June 30, 2025)

| Metric | Actual | Target | Variance | Accuracy |
|--------|--------|--------|----------|----------|
| Move-Outs (SF Expired) | {f2q2['SF Expired (Actual)']:,.0f} | {f2q2['SF Expired (Target)']:,.0f} | {f2q2['SF Expired Variance']:+,.0f} | {f2q2['SF Expired Accuracy']:.1f}% |
| Gross Absorption (SF Commenced) | {f2q2['SF Commenced (Actual)']:,.0f} | {f2q2['SF Commenced (Target)']:,.0f} | {f2q2['SF Commenced Variance']:+,.0f} | {f2q2['SF Commenced Accuracy']:.1f}% |
| Net Absorption | {f2q2['Net Absorption (Actual)']:,.0f} | {f2q2['Net Absorption (Target)']:,.0f} | {f2q2['Net Absorption Variance']:+,.0f} | {f2q2['Net Absorption Accuracy']:.1f}% |

## Fund 3 Results

### Q1 2025 (January 1 - March 31, 2025)
"""
        
        if 'Fund 3' in self.test_results:
            f3q1 = self.test_results['Fund 3']['Q1 2025']
            report += f"""
| Metric | Actual | Target | Variance | Accuracy |
|--------|--------|--------|----------|----------|
| Move-Outs (SF Expired) | {f3q1['SF Expired (Actual)']:,.0f} | {f3q1['SF Expired (Target)']:,.0f} | {f3q1['SF Expired Variance']:+,.0f} | {f3q1['SF Expired Accuracy']:.1f}% |
| Gross Absorption (SF Commenced) | {f3q1['SF Commenced (Actual)']:,.0f} | {f3q1['SF Commenced (Target)']:,.0f} | {f3q1['SF Commenced Variance']:+,.0f} | {f3q1['SF Commenced Accuracy']:.1f}% |
| Net Absorption | {f3q1['Net Absorption (Actual)']:,.0f} | {f3q1['Net Absorption (Target)']:,.0f} | {f3q1['Net Absorption Variance']:+,.0f} | {f3q1['Net Absorption Accuracy']:.1f}% |
"""
            
            f3q2 = self.test_results['Fund 3']['Q2 2025']
            report += f"""
### Q2 2025 (April 1 - June 30, 2025)

| Metric | Actual | Target | Variance | Accuracy |
|--------|--------|--------|----------|----------|
| Move-Outs (SF Expired) | {f3q2['SF Expired (Actual)']:,.0f} | {f3q2['SF Expired (Target)']:,.0f} | {f3q2['SF Expired Variance']:+,.0f} | {f3q2['SF Expired Accuracy']:.1f}% |
| Gross Absorption (SF Commenced) | {f3q2['SF Commenced (Actual)']:,.0f} | {f3q2['SF Commenced (Target)']:,.0f} | {f3q2['SF Commenced Variance']:+,.0f} | {f3q2['SF Commenced Accuracy']:.1f}% |
| Net Absorption | {f3q2['Net Absorption (Actual)']:,.0f} | {f3q2['Net Absorption (Target)']:,.0f} | {f3q2['Net Absorption Variance']:+,.0f} | {f3q2['Net Absorption Accuracy']:.1f}% |

## Overall Accuracy Summary

| Fund | Quarter | Move-Outs Accuracy | Gross Absorption Accuracy | Net Absorption Accuracy |
|------|---------|-------------------|---------------------------|-------------------------|"""
            
            for fund in ['Fund 2', 'Fund 3']:
                if fund in self.test_results:
                    for quarter in ['Q1 2025', 'Q2 2025']:
                        q = self.test_results[fund][quarter]
                        report += f"""
| {fund} | {quarter} | {q['SF Expired Accuracy']:.1f}% | {q['SF Commenced Accuracy']:.1f}% | {q['Net Absorption Accuracy']:.1f}% |"""
        
        report += """

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
"""
        
        # Save report
        report_path = f"{self.base_path}/../Documentation/Validation/Fund2_Fund3_Net_Absorption_Validation_{datetime.now().strftime('%Y%m%d')}.md"
        with open(report_path, 'w') as f:
            f.write(report)
        
        print(f"\nReport saved to: {report_path}")
        
        return report

def main():
    """Main execution function"""
    print("Starting Fund 2 & Fund 3 Net Absorption Validation")
    print("="*80)
    
    validator = MultiFundNetAbsorptionValidator()
    
    # Load data
    if not validator.load_data():
        print("ERROR: Failed to load data")
        return
    
    # Run validation
    results = validator.run_validation()
    
    # Generate report
    report = validator.generate_report()
    
    print("\n" + "="*80)
    print("VALIDATION COMPLETE")
    print("="*80)
    
    # Print summary
    overall_accuracy = []
    for fund in results:
        for quarter in results[fund]:
            overall_accuracy.append(results[fund][quarter]['Net Absorption Accuracy'])
    
    avg_accuracy = np.mean(overall_accuracy) if overall_accuracy else 0
    print(f"\nOverall Average Accuracy: {avg_accuracy:.1f}%")
    print(f"Target Accuracy: 95%+")
    
    if avg_accuracy >= 95:
        print("✅ VALIDATION PASSED")
    else:
        print("❌ VALIDATION FAILED - Further investigation required")

if __name__ == "__main__":
    main()