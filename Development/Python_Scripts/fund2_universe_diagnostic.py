#!/usr/bin/env python3
"""
Fund 2 Universe Diagnostic Tool

This script helps diagnose and resolve the same-store net absorption 
universe mismatch issue by testing different property universe definitions
and comparing them to FPR benchmarks.

Author: Claude Code - Power BI Test Orchestrator
Date: August 10, 2025
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import sys
import os

class Fund2UniverseDiagnostic:
    """Diagnoses Fund 2 same-store universe definition issues"""
    
    def __init__(self):
        """Initialize diagnostic tool"""
        # FPR Q4 2024 Fund 2 Benchmarks
        self.benchmarks = {
            'SF Expired': 256_303,
            'SF Commenced': 88_482,
            'Net Absorption': -167_821,
            'Disposition SF': 160_925,
            'Acquisition SF': 81_400
        }
        
        # Q4 2024 period definition
        self.period_start = pd.Timestamp('2024-10-01')
        self.period_end = pd.Timestamp('2024-12-31')
        
        # Data paths
        self.base_path = "/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Data"
        
        # Results storage
        self.test_results = {}
        self.universe_analysis = {}
        
    def load_data(self):
        """Load all required datasets"""
        print("Loading data sources...")
        
        # Property data
        self.fund2_properties = pd.read_csv(f"{self.base_path}/Fund2_Filtered/dim_property_fund2.csv")
        self.all_properties = pd.read_csv(f"{self.base_path}/Yardi_Tables/dim_property.csv")
        
        # Amendment data
        self.fund2_amendments = pd.read_csv(f"{self.base_path}/Fund2_Filtered/dim_fp_amendmentsunitspropertytenant_fund2.csv")
        self.all_amendments = pd.read_csv(f"{self.base_path}/Yardi_Tables/dim_fp_amendmentsunitspropertytenant.csv")
        
        # Termination data
        self.terminations = pd.read_csv(f"{self.base_path}/Yardi_Tables/dim_fp_terminationtomoveoutreas.csv")
        
        # Convert dates
        self._convert_dates()
        
        print(f"✅ Loaded Fund 2 properties: {len(self.fund2_properties):,}")
        print(f"✅ Loaded Fund 2 amendments: {len(self.fund2_amendments):,}")
        print(f"✅ Loaded terminations: {len(self.terminations):,}")
        
        return True
        
    def _convert_dates(self):
        """Convert date columns"""
        date_columns = ['acquire date', 'dispose date', 'inactive date']
        for col in date_columns:
            if col in self.fund2_properties.columns:
                self.fund2_properties[col] = pd.to_datetime(self.fund2_properties[col], errors='coerce')
        
        amendment_date_cols = ['amendment start date', 'amendment end date', 'amendment sign date']
        for col in amendment_date_cols:
            if col in self.fund2_amendments.columns:
                self.fund2_amendments[col] = pd.to_datetime(self.fund2_amendments[col], errors='coerce')
            if col in self.terminations.columns:
                self.terminations[col] = pd.to_datetime(self.terminations[col], errors='coerce')
                
    def test_universe_definitions(self):
        """Test different property universe definitions"""
        print("\\n" + "="*80)
        print("UNIVERSE DEFINITION ANALYSIS")
        print("="*80)
        
        universes = self._define_universes()
        
        for universe_name, properties in universes.items():
            print(f"\\n{universe_name} ({len(properties)} properties)")
            print("-" * 60)
            
            # Calculate activity for this universe
            results = self._calculate_activity_for_universe(properties, universe_name)
            
            # Compare to benchmarks
            accuracy_analysis = self._compare_to_benchmarks(results, universe_name)
            
            # Store results
            self.universe_analysis[universe_name] = {
                'property_count': len(properties),
                'property_codes': sorted(properties['property code'].tolist()),
                'activity_results': results,
                'accuracy_analysis': accuracy_analysis
            }
            
    def _define_universes(self):
        """Define different property universe scenarios"""
        universes = {}
        
        # Universe 1: Current Same-Store (acquired before Q4 2024)
        same_store_mask = (
            (self.fund2_properties['acquire date'] < self.period_start) &
            (
                self.fund2_properties['dispose date'].isna() |
                (self.fund2_properties['dispose date'] > self.period_end)
            )
        )
        universes['Current Same-Store'] = self.fund2_properties[same_store_mask].copy()
        
        # Universe 2: All Fund 2 Properties
        universes['All Fund 2'] = self.fund2_properties.copy()
        
        # Universe 3: 6-Month Same-Store (acquired before Apr 1, 2024)
        six_month_cutoff = pd.Timestamp('2024-04-01')
        six_month_mask = (
            (self.fund2_properties['acquire date'] < six_month_cutoff) &
            (
                self.fund2_properties['dispose date'].isna() |
                (self.fund2_properties['dispose date'] > self.period_end)
            )
        )
        universes['6-Month Same-Store'] = self.fund2_properties[six_month_mask].copy()
        
        # Universe 4: 12-Month Same-Store (acquired before Oct 1, 2023)
        twelve_month_cutoff = pd.Timestamp('2023-10-01')
        twelve_month_mask = (
            (self.fund2_properties['acquire date'] < twelve_month_cutoff) &
            (
                self.fund2_properties['dispose date'].isna() |
                (self.fund2_properties['dispose date'] > self.period_end)
            )
        )
        universes['12-Month Same-Store'] = self.fund2_properties[twelve_month_mask].copy()
        
        # Universe 5: Active Properties (not disposed during Q4)
        active_mask = (
            self.fund2_properties['dispose date'].isna() |
            (self.fund2_properties['dispose date'] > self.period_end)
        )
        universes['Active Fund 2'] = self.fund2_properties[active_mask].copy()
        
        return universes
        
    def _calculate_activity_for_universe(self, properties, universe_name):
        """Calculate Q4 2024 activity for a property universe"""
        property_codes = set(properties['property code'].unique())
        
        # SF Expired calculation
        q4_terminations = self.terminations[
            (self.terminations['amendment end date'] >= self.period_start) &
            (self.terminations['amendment end date'] <= self.period_end) &
            (self.terminations['amendment status'].isin(['Activated', 'Superseded'])) &
            (self.terminations['property code'].isin(property_codes))
        ].copy()
        
        if len(q4_terminations) > 0:
            # Get latest amendments per property/tenant
            latest_terminations = q4_terminations.loc[
                q4_terminations.groupby(['property hmy', 'tenant hmy'])['amendment sequence'].idxmax()
            ]
            sf_expired = latest_terminations['amendment sf'].sum()
        else:
            sf_expired = 0
            
        # SF Commenced calculation
        q4_new_leases = self.fund2_amendments[
            (self.fund2_amendments['amendment start date'] >= self.period_start) &
            (self.fund2_amendments['amendment start date'] <= self.period_end) &
            (self.fund2_amendments['amendment status'].isin(['Activated', 'Superseded'])) &
            (self.fund2_amendments['amendment type'].isin(['Original Lease', 'New Lease'])) &
            (self.fund2_amendments['property code'].isin(property_codes))
        ].copy()
        
        if len(q4_new_leases) > 0:
            # Get latest amendments per property/tenant  
            latest_new_leases = q4_new_leases.loc[
                q4_new_leases.groupby(['property hmy', 'tenant hmy'])['amendment sequence'].idxmax()
            ]
            sf_commenced = latest_new_leases['amendment sf'].sum()
        else:
            sf_commenced = 0
            
        # Net Absorption
        net_absorption = sf_commenced - sf_expired
        
        results = {
            'SF Expired': sf_expired,
            'SF Commenced': sf_commenced, 
            'Net Absorption': net_absorption,
            'termination_records': len(q4_terminations),
            'new_lease_records': len(q4_new_leases),
            'termination_properties': len(q4_terminations['property code'].unique()) if len(q4_terminations) > 0 else 0,
            'new_lease_properties': len(q4_new_leases['property code'].unique()) if len(q4_new_leases) > 0 else 0
        }
        
        # Print results
        print(f"SF Expired: {sf_expired:,.0f} SF ({results['termination_records']} records)")
        print(f"SF Commenced: {sf_commenced:,.0f} SF ({results['new_lease_records']} records)")
        print(f"Net Absorption: {net_absorption:,.0f} SF")
        print(f"Properties with terminations: {results['termination_properties']}")
        print(f"Properties with new leases: {results['new_lease_properties']}")
        
        return results
        
    def _compare_to_benchmarks(self, results, universe_name):
        """Compare results to FPR benchmarks"""
        analysis = {}
        
        for measure in ['SF Expired', 'SF Commenced', 'Net Absorption']:
            if measure in results:
                benchmark = self.benchmarks[measure]
                calculated = results[measure]
                
                if benchmark != 0:
                    variance_pct = ((calculated - benchmark) / benchmark) * 100
                    accuracy_pct = max(0, 100 - abs(variance_pct))
                else:
                    variance_pct = 0 if calculated == 0 else float('inf')
                    accuracy_pct = 100 if calculated == 0 else 0
                    
                analysis[measure] = {
                    'benchmark': benchmark,
                    'calculated': calculated,
                    'variance': calculated - benchmark,
                    'variance_pct': variance_pct,
                    'accuracy_pct': accuracy_pct,
                    'status': 'PASS' if accuracy_pct >= 95 else 'FAIL'
                }
                
        return analysis
        
    def identify_best_universe(self):
        """Identify the universe definition that best matches benchmarks"""
        print("\\n" + "="*80)
        print("UNIVERSE RANKING ANALYSIS")
        print("="*80)
        
        universe_scores = {}
        
        for universe_name, analysis in self.universe_analysis.items():
            accuracy_analysis = analysis['accuracy_analysis']
            
            # Calculate average accuracy across measures
            total_accuracy = sum(measure['accuracy_pct'] for measure in accuracy_analysis.values())
            avg_accuracy = total_accuracy / len(accuracy_analysis)
            
            universe_scores[universe_name] = {
                'avg_accuracy': avg_accuracy,
                'measures_passing': sum(1 for measure in accuracy_analysis.values() if measure['status'] == 'PASS'),
                'total_measures': len(accuracy_analysis)
            }
            
        # Rank universes by accuracy
        ranked_universes = sorted(universe_scores.items(), key=lambda x: x[1]['avg_accuracy'], reverse=True)
        
        print("Universe Rankings (by average accuracy):")
        print("-" * 50)
        
        for i, (universe_name, scores) in enumerate(ranked_universes, 1):
            print(f"{i}. {universe_name}")
            print(f"   Average Accuracy: {scores['avg_accuracy']:.1f}%")
            print(f"   Measures Passing: {scores['measures_passing']}/{scores['total_measures']}")
            print(f"   Properties: {self.universe_analysis[universe_name]['property_count']}")
            
            if i == 1 and scores['avg_accuracy'] >= 95:
                print("   🎯 RECOMMENDED UNIVERSE - High accuracy match!")
            elif i == 1:
                print("   ⚠️  BEST MATCH - But still below 95% target")
                
            print()
            
        return ranked_universes[0] if ranked_universes else None
        
    def generate_property_comparison(self):
        """Generate detailed property comparison between universes"""
        print("\\n" + "="*80)
        print("PROPERTY UNIVERSE COMPARISON")
        print("="*80)
        
        # Get property codes for each universe
        universe_properties = {}
        for universe_name, analysis in self.universe_analysis.items():
            universe_properties[universe_name] = set(analysis['property_codes'])
            
        # Find overlaps and differences
        all_fund2_props = universe_properties.get('All Fund 2', set())
        same_store_props = universe_properties.get('Current Same-Store', set())
        
        print(f"All Fund 2 Properties: {len(all_fund2_props)}")
        print(f"Current Same-Store Properties: {len(same_store_props)}")
        print(f"Same-Store ⊆ All Fund 2: {same_store_props.issubset(all_fund2_props)}")
        
        # Properties excluded from same-store
        excluded_props = all_fund2_props - same_store_props
        print(f"\\nProperties EXCLUDED from Same-Store: {len(excluded_props)}")
        if excluded_props:
            print("Sample excluded properties:", sorted(list(excluded_props))[:10])
            
        # Check if Q4 activity happened at excluded properties
        if excluded_props:
            self._analyze_excluded_properties(excluded_props)
            
    def _analyze_excluded_properties(self, excluded_props):
        """Analyze activity at properties excluded from same-store"""
        print("\\nAnalyzing activity at EXCLUDED properties...")
        
        # Q4 terminations at excluded properties
        excluded_terminations = self.terminations[
            (self.terminations['amendment end date'] >= self.period_start) &
            (self.terminations['amendment end date'] <= self.period_end) &
            (self.terminations['amendment status'].isin(['Activated', 'Superseded'])) &
            (self.terminations['property code'].isin(excluded_props))
        ]
        
        # Q4 new leases at excluded properties  
        excluded_new_leases = self.fund2_amendments[
            (self.fund2_amendments['amendment start date'] >= self.period_start) &
            (self.fund2_amendments['amendment start date'] <= self.period_end) &
            (self.fund2_amendments['amendment status'].isin(['Activated', 'Superseded'])) &
            (self.fund2_amendments['amendment type'].isin(['Original Lease', 'New Lease'])) &
            (self.fund2_amendments['property code'].isin(excluded_props))
        ]
        
        print(f"Q4 terminations at excluded properties: {len(excluded_terminations)} records")
        print(f"Q4 new leases at excluded properties: {len(excluded_new_leases)} records")
        
        if len(excluded_terminations) > 0 or len(excluded_new_leases) > 0:
            print("\\n🔍 KEY INSIGHT: Activity exists at excluded properties!")
            print("This suggests FPR benchmarks may include ALL Fund 2 properties, not just same-store.")
            
    def save_diagnostic_report(self):
        """Save comprehensive diagnostic report"""
        report_file = f"{self.base_path}/../Documentation/Validation/Fund2_Universe_Diagnostic_Report.md"
        
        with open(report_file, 'w') as f:
            f.write("# Fund 2 Universe Diagnostic Report\\n\\n")
            f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n")
            f.write(f"**Period**: Q4 2024 ({self.period_start.date()} to {self.period_end.date()})\\n\\n")
            
            # Executive summary
            f.write("## Executive Summary\\n\\n")
            
            # Find best universe
            best_universe = None
            best_accuracy = 0
            for universe_name, analysis in self.universe_analysis.items():
                accuracy_analysis = analysis['accuracy_analysis']
                avg_accuracy = sum(measure['accuracy_pct'] for measure in accuracy_analysis.values()) / len(accuracy_analysis)
                if avg_accuracy > best_accuracy:
                    best_accuracy = avg_accuracy
                    best_universe = universe_name
                    
            if best_universe and best_accuracy >= 95:
                f.write(f"**✅ SOLUTION FOUND**: {best_universe} achieves {best_accuracy:.1f}% accuracy\\n\\n")
            else:
                f.write(f"**⚠️ ISSUE CONFIRMED**: Best match ({best_universe}) only achieves {best_accuracy:.1f}% accuracy\\n\\n")
                
            # Detailed results
            f.write("## Universe Analysis Results\\n\\n")
            
            for universe_name, analysis in self.universe_analysis.items():
                f.write(f"### {universe_name}\\n\\n")
                f.write(f"**Properties**: {analysis['property_count']}\\n")
                
                activity = analysis['activity_results']
                f.write(f"**SF Expired**: {activity['SF Expired']:,.0f} SF\\n")
                f.write(f"**SF Commenced**: {activity['SF Commenced']:,.0f} SF\\n")
                f.write(f"**Net Absorption**: {activity['Net Absorption']:,.0f} SF\\n\\n")
                
                # Accuracy table
                accuracy = analysis['accuracy_analysis']
                f.write("| Measure | Benchmark | Calculated | Accuracy | Status |\\n")
                f.write("|---------|-----------|------------|----------|--------|\\n")
                
                for measure, results in accuracy.items():
                    status_icon = "✅" if results['status'] == 'PASS' else "❌"
                    f.write(f"| {measure} | {results['benchmark']:,.0f} | {results['calculated']:,.0f} | ")
                    f.write(f"{results['accuracy_pct']:.1f}% | {results['status']} {status_icon} |\\n")
                    
                f.write("\\n")
                
            # Recommendations
            f.write("## Recommendations\\n\\n")
            
            if best_accuracy >= 95:
                f.write(f"1. **Implement {best_universe} Definition**: Update DAX measures to use this universe\\n")
                f.write("2. **Validate with Finance Team**: Confirm this matches FPR expectations\\n")
                f.write("3. **Update Documentation**: Document the correct same-store definition\\n")
            else:
                f.write("1. **Investigate FPR Methodology**: Deep dive into FPR calculation approach\\n")
                f.write("2. **Validate Source Data**: Ensure completeness of Fund 2 property universe\\n")
                f.write("3. **Consider Hybrid Approach**: May need combination of universes or adjustments\\n")
                
        print(f"\\n✅ Diagnostic report saved: {report_file}")
        return report_file

def main():
    """Main execution function"""
    diagnostic = Fund2UniverseDiagnostic()
    
    try:
        print("="*80)
        print("FUND 2 UNIVERSE DIAGNOSTIC TOOL")
        print("="*80)
        print("Analyzing same-store property universe definitions...")
        print()
        
        # Load data
        if not diagnostic.load_data():
            print("❌ Failed to load data")
            return False
            
        # Test different universe definitions
        diagnostic.test_universe_definitions()
        
        # Identify best match
        best_universe = diagnostic.identify_best_universe()
        
        # Generate property comparison
        diagnostic.generate_property_comparison()
        
        # Save comprehensive report
        report_file = diagnostic.save_diagnostic_report()
        
        print("\\n" + "="*80)
        print("DIAGNOSTIC COMPLETE")
        print("="*80)
        
        if best_universe:
            universe_name, scores = best_universe
            print(f"Best Universe: {universe_name}")
            print(f"Average Accuracy: {scores['avg_accuracy']:.1f}%")
            print(f"Report: {report_file}")
            
            if scores['avg_accuracy'] >= 95:
                print("\\n🎯 SUCCESS: Found universe definition matching benchmarks!")
                return True
            else:
                print("\\n⚠️  ISSUE: No universe achieves 95%+ accuracy. Further investigation needed.")
                return False
        else:
            print("❌ No valid universe definitions found")
            return False
            
    except Exception as e:
        print(f"❌ Diagnostic error: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)