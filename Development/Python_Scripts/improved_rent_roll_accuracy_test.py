#!/usr/bin/env python3
"""
Improved Rent Roll Accuracy Testing Script
PowerBI Measure Accuracy Testing Agent

Fixed version that properly parses Yardi exports with correct column mapping
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

class ImprovedRentRollTester:
    """Improved accuracy testing for rent roll measures"""
    
    def __init__(self, base_path="/Users/michaeltang/Documents/GitHub/BI/PBI v1.7", verbose=True):
        self.base_path = base_path
        self.verbose = verbose
        self.test_results = {}
        self.accuracy_scores = {}
        
        # Test dates configuration
        self.test_dates = {
            '03.31.25': {
                'excel_serial': 45474,  # March 31, 2025
                'date_str': '3/31/2025',
                'timestamp': pd.Timestamp('2025-03-31'),
                'yardi_file': 'rent rolls/03.31.25.xlsx'
            },
            '12.31.24': {
                'excel_serial': 45657,  # December 31, 2024  
                'date_str': '12/31/2024',
                'timestamp': pd.Timestamp('2024-12-31'),
                'yardi_file': 'rent rolls/12.31.24.xlsx'
            }
        }
    
    def log(self, message):
        """Logging function"""
        if self.verbose:
            print(message)
    
    def load_source_data(self):
        """Load all source Yardi tables for Fund 2"""
        self.log("\n" + "="*80)
        self.log("LOADING SOURCE DATA")
        self.log("="*80)
        
        fund2_path = os.path.join(self.base_path, "Data/Fund2_Filtered")
        
        # Load amendments table
        self.amendments_df = pd.read_csv(
            os.path.join(fund2_path, "dim_fp_amendmentsunitspropertytenant_fund2.csv")
        )
        self.log(f"✓ Loaded {len(self.amendments_df)} amendment records")
        
        # Load active charges
        self.charges_df = pd.read_csv(
            os.path.join(fund2_path, "dim_fp_amendmentchargeschedule_fund2_active.csv")
        )
        self.log(f"✓ Loaded {len(self.charges_df)} active charge records")
        
        # Load properties
        self.properties_df = pd.read_csv(
            os.path.join(fund2_path, "dim_property_fund2.csv")
        )
        self.log(f"✓ Loaded {len(self.properties_df)} Fund 2 properties")
    
    def load_yardi_export(self, test_date_key):
        """Load and clean Yardi export for specific test date with improved parsing"""
        test_config = self.test_dates[test_date_key]
        yardi_file_path = os.path.join(self.base_path, test_config['yardi_file'])
        
        self.log(f"\n--- Loading Yardi Export for {test_config['date_str']} ---")
        
        try:
            # Load with skiprows=3 which gives us the best structure based on examination
            df = pd.read_excel(yardi_file_path, sheet_name=0, skiprows=3)
            self.log(f"   ✓ Initial load: {df.shape}")
            
            # Remove empty rows (filled with NaT/NaN)
            df = df.dropna(how='all')
            self.log(f"   ✓ After removing empty rows: {df.shape}")
            
            # Filter to rows with actual lease data
            # Look for rows where first column contains property information with parentheses (property codes)
            mask = df.iloc[:, 0].astype(str).str.contains(r'\([^)]+\)', na=False, regex=True)
            df_filtered = df[mask].copy()
            self.log(f"   ✓ After filtering to lease rows: {df_filtered.shape}")
            
            # Clean and standardize the Yardi export
            yardi_df = self.clean_yardi_export(df_filtered, test_date_key)
            
            return yardi_df
            
        except Exception as e:
            self.log(f"   ✗ Error loading {yardi_file_path}: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def clean_yardi_export(self, df, test_date_key):
        """Clean and standardize Yardi export data with improved column mapping"""
        self.log(f"   Cleaning Yardi export data...")
        
        # Map columns based on position (since we know the structure from examination)
        # From the examination: skiprows=3 gives us these columns in order:
        expected_columns = [
            'property_full',     # Property with name and code: "11697 W Grand (xil11697)"
            'unit',              # Unit/Suite
            'tenant_full',       # Tenant with name and ID
            'lease_type',        # Lease Type
            'area',              # Area (square feet)
            'lease_from',        # Lease From date
            'lease_to',          # Lease To date  
            'term',              # Term
            'tenancy_years',     # Tenancy in Years
            'monthly_rent',      # Monthly Rent
            'monthly_rent_area', # Monthly Rent/Area
            'annual_rent',       # Annual Rent
            'annual_rent_area',  # Annual Rent/Area
            'annual_rec_area',   # Annual Rec./Area
            'annual_misc_area',  # Annual Misc/Area
            'security_deposit',  # Security Deposit
            'loc_amount'         # LOC Amount/Bank Guarantee
        ]
        
        # Rename columns
        if len(df.columns) >= len(expected_columns):
            column_mapping = {df.columns[i]: expected_columns[i] for i in range(len(expected_columns))}
            df = df.rename(columns=column_mapping)
        
        # Extract property code from property_full column
        if 'property_full' in df.columns:
            # Extract code from parentheses: "Property Name (CODE)"
            df['property_code'] = df['property_full'].str.extract(r'\(([^)]+)\)')
            df['property_name'] = df['property_full'].str.replace(r'\s*\([^)]+\)', '', regex=True).str.strip()
        
        # Extract tenant code from tenant_full column
        if 'tenant_full' in df.columns:
            df['tenant_code'] = df['tenant_full'].str.extract(r'\(([^)]+)\)')  
            df['tenant_name'] = df['tenant_full'].str.replace(r'\s*\([^)]+\)', '', regex=True).str.strip()
        
        # Standardize area column
        if 'area' in df.columns:
            df['square_feet'] = pd.to_numeric(df['area'], errors='coerce')
        
        # Clean financial columns
        financial_cols = ['monthly_rent', 'annual_rent', 'security_deposit']
        for col in financial_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Filter for Fund 2 properties (codes starting with 'x')
        if 'property_code' in df.columns:
            fund2_mask = df['property_code'].str.startswith('x', na=False)
            df_fund2 = df[fund2_mask].copy()
            self.log(f"   ✓ Filtered to {len(df_fund2)} Fund 2 records (from {len(df)} total)")
            
            # Show sample of Fund 2 properties found
            sample_props = df_fund2['property_code'].unique()[:5]
            self.log(f"   ✓ Sample Fund 2 properties: {list(sample_props)}")
            
            return df_fund2
        else:
            self.log(f"   ⚠ No property_code column found after extraction")
            return df
    
    def generate_calculated_rent_roll(self, test_date_key):
        """Generate rent roll using DAX business logic for specific test date"""
        test_config = self.test_dates[test_date_key]
        
        self.log(f"\n--- Generating Calculated Rent Roll for {test_config['date_str']} ---")
        
        # Step 1: Apply amendment filters using DAX business logic
        valid_amendments = self.apply_dax_amendment_filters(test_config)
        
        # Step 2: Select latest amendments per property/tenant
        latest_amendments = self.select_latest_amendments(valid_amendments)
        
        # Step 3: Calculate rent from charge schedule
        rent_roll = self.calculate_rent_from_charges(latest_amendments, test_config)
        
        # Step 4: Add property details
        rent_roll = self.add_property_details(rent_roll)
        
        self.log(f"   ✓ Generated rent roll with {len(rent_roll)} records")
        
        return rent_roll
    
    def apply_dax_amendment_filters(self, test_config):
        """Apply DAX business logic filters to amendments"""
        self.log(f"   Applying DAX amendment filters...")
        
        # Filter 1: Status IN ("Activated", "Superseded")
        valid_statuses = ['Activated', 'Superseded']
        status_filtered = self.amendments_df[
            self.amendments_df['amendment status'].isin(valid_statuses)
        ]
        
        # Filter 2: Type NOT = "Termination"  
        type_filtered = status_filtered[
            status_filtered['amendment type'] != 'Termination'
        ]
        
        # Filter 3: Active on report date
        date_filtered = type_filtered[
            (type_filtered['amendment start date serial'] <= test_config['excel_serial']) &
            ((type_filtered['amendment end date serial'] >= test_config['excel_serial']) | 
             type_filtered['amendment end date serial'].isna())
        ]
        
        self.log(f"      Status filter: {len(status_filtered)} records")
        self.log(f"      Type filter: {len(type_filtered)} records") 
        self.log(f"      Date filter: {len(date_filtered)} records")
        
        return date_filtered
    
    def select_latest_amendments(self, valid_amendments):
        """Select latest amendment sequence per property/tenant (DAX logic)"""
        self.log(f"   Selecting latest amendments per tenant...")
        
        # Group by property and tenant to find max sequence
        latest_sequences = valid_amendments.groupby(
            ['property hmy', 'tenant hmy']
        )['amendment sequence'].max().reset_index()
        latest_sequences.rename(columns={'amendment sequence': 'max_sequence'}, inplace=True)
        
        # Merge back to get full records
        latest_amendments = pd.merge(
            valid_amendments,
            latest_sequences,
            left_on=['property hmy', 'tenant hmy', 'amendment sequence'],
            right_on=['property hmy', 'tenant hmy', 'max_sequence'],
            how='inner'
        )
        
        self.log(f"      Selected {len(latest_amendments)} latest amendments")
        
        return latest_amendments
    
    def calculate_rent_from_charges(self, latest_amendments, test_config):
        """Calculate monthly rent from charge schedule (DAX logic)"""
        self.log(f"   Calculating rent from charges...")
        
        # Get rent charges only
        rent_charges = self.charges_df[self.charges_df['charge code'] == 'rent'].copy()
        
        # Filter charges active on test date
        active_charges = rent_charges[
            (rent_charges['from date'] <= test_config['excel_serial']) &
            ((rent_charges['to date'] >= test_config['excel_serial']) | 
             rent_charges['to date'].isna())
        ]
        
        self.log(f"      Active rent charges: {len(active_charges)}")
        
        # Merge amendments with active charges
        rent_data = pd.merge(
            latest_amendments,
            active_charges[['amendment hmy', 'monthly amount']],
            on='amendment hmy',
            how='left'
        )
        
        self.log(f"      Merged data: {len(rent_data)} records")
        
        # Group by amendment and sum monthly rent (handle multiple charge lines)
        rent_summary = rent_data.groupby([
            'property hmy', 'property code', 'tenant hmy', 'tenant id',
            'amendment hmy', 'amendment sf', 'amendment term',
            'amendment start date', 'amendment end date',
            'units under amendment', 'amendment status', 'amendment type'
        ]).agg({
            'monthly amount': 'sum'
        }).reset_index()
        
        # Calculate derived fields
        rent_summary.rename(columns={'monthly amount': 'monthly_rent'}, inplace=True)
        rent_summary['annual_rent'] = rent_summary['monthly_rent'] * 12
        
        # Calculate rent PSF
        rent_summary['rent_psf'] = np.where(
            rent_summary['amendment sf'] > 0,
            rent_summary['annual_rent'] / rent_summary['amendment sf'],
            0
        )
        
        # Rename columns for easier comparison
        rent_summary = rent_summary.rename(columns={
            'amendment sf': 'square_feet'
        })
        
        self.log(f"      Calculated rent for {len(rent_summary)} leases")
        self.log(f"      Total monthly rent: ${rent_summary['monthly_rent'].sum():,.2f}")
        
        return rent_summary
    
    def add_property_details(self, rent_roll):
        """Add property names and details"""
        return pd.merge(
            rent_roll,
            self.properties_df[['property code', 'property name', 'postal city', 'postal state']],
            on='property code',
            how='left'
        )
    
    def compare_rent_rolls(self, calculated_df, yardi_df, test_date_key):
        """Compare calculated rent roll with Yardi export"""
        test_config = self.test_dates[test_date_key]
        
        self.log(f"\n--- Comparing Rent Rolls for {test_config['date_str']} ---")
        
        # Comparison metrics
        metrics = {}
        
        # 1. Record Count Comparison
        metrics['record_count'] = {
            'calculated': len(calculated_df),
            'yardi': len(yardi_df),
            'difference': len(calculated_df) - len(yardi_df),
            'accuracy': min(len(calculated_df), len(yardi_df)) / max(len(calculated_df), len(yardi_df)) * 100
        }
        
        # 2. Property Coverage
        calc_props = set(calculated_df['property code'].dropna())
        yardi_props = set(yardi_df['property_code'].dropna()) if 'property_code' in yardi_df.columns else set()
        common_props = calc_props & yardi_props
        
        metrics['property_coverage'] = {
            'calculated_properties': len(calc_props),
            'yardi_properties': len(yardi_props), 
            'common_properties': len(common_props),
            'coverage_accuracy': len(common_props) / len(calc_props) * 100 if len(calc_props) > 0 else 0
        }
        
        # 3. Monthly Rent Comparison (for common properties)
        if len(common_props) > 0 and 'monthly_rent' in calculated_df.columns and 'monthly_rent' in yardi_df.columns:
            calc_total = calculated_df[calculated_df['property code'].isin(common_props)]['monthly_rent'].sum()
            yardi_total = yardi_df[yardi_df['property_code'].isin(common_props)]['monthly_rent'].sum()
            
            metrics['monthly_rent'] = {
                'calculated': calc_total,
                'yardi': yardi_total,
                'difference': calc_total - yardi_total,
                'accuracy': min(calc_total, yardi_total) / max(calc_total, yardi_total) * 100 if max(calc_total, yardi_total) > 0 else 100
            }
        
        # 4. Square Feet Comparison (for common properties)
        if len(common_props) > 0 and 'square_feet' in calculated_df.columns and 'square_feet' in yardi_df.columns:
            calc_sf = calculated_df[calculated_df['property code'].isin(common_props)]['square_feet'].sum()
            yardi_sf = yardi_df[yardi_df['property_code'].isin(common_props)]['square_feet'].sum()
            
            metrics['square_feet'] = {
                'calculated': calc_sf,
                'yardi': yardi_sf,
                'difference': calc_sf - yardi_sf,
                'accuracy': min(calc_sf, yardi_sf) / max(calc_sf, yardi_sf) * 100 if max(calc_sf, yardi_sf) > 0 else 100
            }
        
        # 5. Property-level comparison
        property_comparison = self.compare_by_property(calculated_df, yardi_df, common_props)
        
        # Store results
        self.test_results[test_date_key] = {
            'metrics': metrics,
            'property_comparison': property_comparison,
            'calculated_records': len(calculated_df),
            'yardi_records': len(yardi_df),
            'common_properties': len(common_props)
        }
        
        return metrics, property_comparison
    
    def compare_by_property(self, calc_df, yardi_df, common_props):
        """Compare rent rolls at property level"""
        self.log("   Comparing by property...")
        
        property_results = []
        
        for prop_code in common_props:
            calc_prop = calc_df[calc_df['property code'] == prop_code]
            yardi_prop = yardi_df[yardi_df['property_code'] == prop_code]
            
            # Monthly rent comparison
            calc_monthly = calc_prop['monthly_rent'].sum() if 'monthly_rent' in calc_prop.columns else 0
            yardi_monthly = yardi_prop['monthly_rent'].sum() if 'monthly_rent' in yardi_prop.columns else 0
            
            # Square feet comparison
            calc_sf = calc_prop['square_feet'].sum() if 'square_feet' in calc_prop.columns else 0
            yardi_sf = yardi_prop['square_feet'].sum() if 'square_feet' in yardi_prop.columns else 0
            
            # Calculate differences and accuracy
            monthly_diff = calc_monthly - yardi_monthly
            monthly_acc = (min(calc_monthly, yardi_monthly) / max(calc_monthly, yardi_monthly) * 100) if max(calc_monthly, yardi_monthly) > 0 else 100
            
            sf_diff = calc_sf - yardi_sf
            sf_acc = (min(calc_sf, yardi_sf) / max(calc_sf, yardi_sf) * 100) if max(calc_sf, yardi_sf) > 0 else 100
            
            property_results.append({
                'property_code': prop_code,
                'calc_monthly': calc_monthly,
                'yardi_monthly': yardi_monthly,
                'monthly_diff': monthly_diff,
                'monthly_accuracy': monthly_acc,
                'calc_sf': calc_sf,
                'yardi_sf': yardi_sf,
                'sf_diff': sf_diff,
                'sf_accuracy': sf_acc,
                'calc_units': len(calc_prop),
                'yardi_units': len(yardi_prop)
            })
        
        # Sort by largest monthly rent difference
        property_results.sort(key=lambda x: abs(x['monthly_diff']), reverse=True)
        
        self.log(f"   ✓ Compared {len(property_results)} common properties")
        
        return property_results
    
    def calculate_overall_accuracy(self, test_date_key):
        """Calculate overall accuracy score for test date"""
        if test_date_key not in self.test_results:
            return 0
        
        metrics = self.test_results[test_date_key]['metrics']
        
        # Weighted accuracy calculation
        weights = {
            'property_coverage': 0.20,
            'monthly_rent': 0.50,
            'square_feet': 0.30
        }
        
        weighted_score = 0
        total_weight = 0
        
        for metric_name, weight in weights.items():
            if metric_name in metrics:
                if metric_name == 'property_coverage':
                    accuracy = metrics[metric_name]['coverage_accuracy']
                else:
                    accuracy = metrics[metric_name]['accuracy']
                
                weighted_score += accuracy * weight
                total_weight += weight
        
        overall_accuracy = weighted_score / total_weight if total_weight > 0 else 0
        self.accuracy_scores[test_date_key] = overall_accuracy
        
        return overall_accuracy
    
    def print_test_results(self, test_date_key):
        """Print detailed test results for specific date"""
        test_config = self.test_dates[test_date_key]
        
        self.log(f"\n" + "="*80)
        self.log(f"ACCURACY TEST RESULTS - {test_config['date_str']}")
        self.log("="*80)
        
        if test_date_key not in self.test_results:
            self.log("No test results available")
            return
        
        results = self.test_results[test_date_key]
        metrics = results['metrics']
        
        # Overall Metrics
        self.log(f"\nOVERALL METRICS COMPARISON:")
        
        for metric_name, values in metrics.items():
            self.log(f"\n{metric_name.replace('_', ' ').title()}:")
            
            if metric_name == 'property_coverage':
                self.log(f"  Calculated Properties: {values['calculated_properties']}")
                self.log(f"  Yardi Properties: {values['yardi_properties']}")
                self.log(f"  Common Properties: {values['common_properties']}")
                self.log(f"  Coverage Accuracy: {values['coverage_accuracy']:.1f}%")
            elif metric_name == 'record_count':
                self.log(f"  Calculated: {values['calculated']:,}")
                self.log(f"  Yardi:      {values['yardi']:,}")
                self.log(f"  Difference: {values['difference']:,}")
                self.log(f"  Accuracy:   {values['accuracy']:.1f}%")
            elif 'rent' in metric_name and 'calculated' in values:
                self.log(f"  Calculated: ${values['calculated']:,.2f}")
                self.log(f"  Yardi:      ${values['yardi']:,.2f}")
                self.log(f"  Difference: ${values['difference']:,.2f}")
                self.log(f"  Accuracy:   {values['accuracy']:.1f}%")
            elif 'calculated' in values:
                self.log(f"  Calculated: {values['calculated']:,}")
                self.log(f"  Yardi:      {values['yardi']:,}")
                self.log(f"  Difference: {values['difference']:,}")
                self.log(f"  Accuracy:   {values['accuracy']:.1f}%")
        
        # Property-level results (top 10 discrepancies)
        if 'property_comparison' in results and len(results['property_comparison']) > 0:
            self.log(f"\nTOP 10 PROPERTY DISCREPANCIES (by Monthly Rent):")
            
            for i, prop in enumerate(results['property_comparison'][:10], 1):
                self.log(f"\n{i}. Property: {prop['property_code']}")
                self.log(f"   Monthly Rent - Calculated: ${prop['calc_monthly']:,.2f}, Yardi: ${prop['yardi_monthly']:,.2f}")
                self.log(f"   Difference: ${prop['monthly_diff']:,.2f} ({prop['monthly_accuracy']:.1f}% accuracy)")
                self.log(f"   Square Feet - Calculated: {prop['calc_sf']:,}, Yardi: {prop['yardi_sf']:,}")
                self.log(f"   Units - Calculated: {prop['calc_units']}, Yardi: {prop['yardi_units']}")
        
        # Overall accuracy assessment
        overall_accuracy = self.calculate_overall_accuracy(test_date_key)
        self.log(f"\nOVERALL ACCURACY SCORE: {overall_accuracy:.1f}%")
        
        if overall_accuracy >= 95:
            self.log("✓ EXCELLENT - Meets 95%+ accuracy target")
        elif overall_accuracy >= 90:
            self.log("✓ GOOD - Close to target, minor adjustments needed")
        elif overall_accuracy >= 80:
            self.log("⚠ FAIR - Significant discrepancies to investigate")
        else:
            self.log("✗ POOR - Major issues requiring investigation")
    
    def generate_comprehensive_report(self):
        """Generate comprehensive accuracy validation report"""
        self.log(f"\n" + "="*80)
        self.log("COMPREHENSIVE ACCURACY VALIDATION REPORT")
        self.log("="*80)
        
        self.log(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log(f"Target Accuracy: 95%+")
        self.log(f"Test Scenarios: {len(self.test_dates)} rent roll dates")
        
        # Summary of all tests
        self.log(f"\nTEST SUMMARY:")
        total_accuracy = 0
        valid_tests = 0
        
        for test_date_key in self.test_dates.keys():
            if test_date_key in self.accuracy_scores:
                accuracy = self.accuracy_scores[test_date_key]
                total_accuracy += accuracy
                valid_tests += 1
                
                status = "PASS" if accuracy >= 95 else "NEEDS IMPROVEMENT" if accuracy >= 90 else "FAIL"
                self.log(f"  {test_date_key}: {accuracy:.1f}% - {status}")
        
        # Overall assessment
        if valid_tests > 0:
            avg_accuracy = total_accuracy / valid_tests
            self.log(f"\nOVERALL AVERAGE ACCURACY: {avg_accuracy:.1f}%")
            
            if avg_accuracy >= 95:
                self.log("🎉 SUCCESS: DAX measures meet 95%+ accuracy target!")
            elif avg_accuracy >= 90:
                self.log("⚠ CLOSE: DAX measures are close to target, minor improvements needed")
            else:
                self.log("❌ FAILED: DAX measures require significant improvements")
        
        # Data quality insights
        self.log(f"\nDATA QUALITY INSIGHTS:")
        for test_date_key in self.test_dates.keys():
            if test_date_key in self.test_results:
                results = self.test_results[test_date_key]
                common_props = results.get('common_properties', 0)
                calc_records = results.get('calculated_records', 0)
                yardi_records = results.get('yardi_records', 0)
                
                self.log(f"\n{test_date_key}:")
                self.log(f"  Common Properties: {common_props}")
                self.log(f"  Calculated Records: {calc_records}")
                self.log(f"  Yardi Records: {yardi_records}")
                
                if 'property_comparison' in results:
                    high_accuracy_props = sum(1 for p in results['property_comparison'] if p['monthly_accuracy'] >= 95)
                    total_props = len(results['property_comparison'])
                    self.log(f"  Properties with 95%+ accuracy: {high_accuracy_props}/{total_props}")
        
        return valid_tests > 0 and (total_accuracy / valid_tests) >= 95
    
    def run_comprehensive_test(self):
        """Run comprehensive accuracy test for all test dates"""
        self.log("🚀 STARTING IMPROVED COMPREHENSIVE RENT ROLL ACCURACY TEST")
        self.log("="*80)
        
        # Load source data once
        self.load_source_data()
        
        # Test each date
        for test_date_key in self.test_dates.keys():
            try:
                # Load Yardi export
                yardi_df = self.load_yardi_export(test_date_key)
                
                if yardi_df is None or len(yardi_df) == 0:
                    self.log(f"⚠ Skipping {test_date_key} - could not load Yardi export")
                    continue
                
                # Generate calculated rent roll
                calculated_df = self.generate_calculated_rent_roll(test_date_key)
                
                # Compare results
                metrics, property_comparison = self.compare_rent_rolls(
                    calculated_df, yardi_df, test_date_key
                )
                
                # Print results for this test
                self.print_test_results(test_date_key)
                
            except Exception as e:
                self.log(f"❌ Error testing {test_date_key}: {str(e)}")
                import traceback
                traceback.print_exc()
        
        # Generate final report
        overall_success = self.generate_comprehensive_report()
        
        self.log(f"\n{'='*80}")
        self.log("IMPROVED COMPREHENSIVE ACCURACY TEST COMPLETE")
        self.log(f"{'='*80}")
        
        return overall_success


def main():
    """Main execution function"""
    tester = ImprovedRentRollTester(verbose=True)
    success = tester.run_comprehensive_test()
    
    if success:
        print("\n🎉 All tests passed! DAX measures meet accuracy targets.")
        return 0
    else:
        print("\n⚠ Some tests need improvement. Review results and improve DAX measures.")
        return 1


if __name__ == "__main__":
    exit(main())