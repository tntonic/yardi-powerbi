#!/usr/bin/env python3
"""
Comprehensive Rent Roll Accuracy Testing Script
PowerBI Measure Accuracy Testing Agent

This script performs comprehensive accuracy testing of DAX measures against actual Yardi exports
for Fund 2 properties, targeting 95%+ accuracy validation.

Test Dates: March 31, 2025 and December 31, 2024
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

class RentRollAccuracyTester:
    """Comprehensive accuracy testing for rent roll measures"""
    
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
        
        # Filter for active Fund 2 properties (codes starting with 'x')
        fund2_props = self.properties_df[
            self.properties_df['property code'].str.startswith('x', na=False)
        ]
        self.log(f"✓ Identified {len(fund2_props)} Fund 2 properties (codes starting with 'x')")
    
    def load_yardi_export(self, test_date_key):
        """Load and clean Yardi export for specific test date"""
        test_config = self.test_dates[test_date_key]
        yardi_file_path = os.path.join(self.base_path, test_config['yardi_file'])
        
        self.log(f"\n--- Loading Yardi Export for {test_config['date_str']} ---")
        
        try:
            # Try different sheet names and skip rows
            yardi_df = None
            for sheet_name in [0, 'Sheet1', 'Rent Roll', 'Data']:
                for skip_rows in [0, 1, 2, 3]:
                    try:
                        df = pd.read_excel(yardi_file_path, sheet_name=sheet_name, skiprows=skip_rows)
                        
                        # Score this attempt
                        score = 0
                        meaningful_cols = sum(1 for col in df.columns 
                                             if not str(col).startswith('Unnamed') and not pd.isna(col))
                        score += meaningful_cols * 10
                        
                        if len(df) > 10:
                            score += 20
                        
                        # Check for expected terms
                        col_str = ' '.join(str(col).lower() for col in df.columns)
                        expected_terms = ['property', 'tenant', 'rent', 'area', 'lease', 'square']
                        for term in expected_terms:
                            if term in col_str:
                                score += 5
                        
                        if yardi_df is None or score > 50:  # Use if good score
                            yardi_df = df
                            best_sheet = sheet_name
                            best_skip = skip_rows
                            best_score = score
                            
                            if score > 80:  # Stop if excellent score
                                break
                    except:
                        continue
                if yardi_df is not None and best_score > 80:
                    break
            
            if yardi_df is None or len(yardi_df) == 0:
                raise ValueError(f"Could not load Yardi export: {yardi_file_path}")
            
            self.log(f"   ✓ Loaded with sheet={best_sheet}, skip_rows={best_skip}")
            self.log(f"   ✓ Shape: {yardi_df.shape}")
            
            # Clean and standardize the Yardi export
            yardi_df = self.clean_yardi_export(yardi_df, test_date_key)
            
            return yardi_df
            
        except Exception as e:
            self.log(f"   ✗ Error loading {yardi_file_path}: {str(e)}")
            return None
    
    def clean_yardi_export(self, df, test_date_key):
        """Clean and standardize Yardi export data"""
        self.log(f"   Cleaning Yardi export data...")
        
        # Standardize column names
        column_mapping = {
            # Common variations for property
            'property': 'property_name',
            'property name': 'property_name', 
            'building': 'property_name',
            'asset': 'property_name',
            
            # Property code
            'property code': 'property_code',
            'prop code': 'property_code', 
            'asset code': 'property_code',
            
            # Tenant information
            'tenant': 'tenant_name',
            'tenant name': 'tenant_name',
            'lessee': 'tenant_name',
            'company': 'tenant_name',
            
            # Suite/Unit
            'suite': 'suite',
            'unit': 'suite',
            'suite/unit': 'suite',
            'space': 'suite',
            
            # Area
            'area': 'square_feet',
            'square feet': 'square_feet',
            'sf': 'square_feet',
            'rsf': 'square_feet',
            'square footage': 'square_feet',
            'rentable sf': 'square_feet',
            'leased sf': 'square_feet',
            
            # Rent fields
            'monthly rent': 'monthly_rent',
            'base rent': 'monthly_rent',
            'monthly base rent': 'monthly_rent',
            'rent/month': 'monthly_rent',
            'monthly': 'monthly_rent',
            
            'annual rent': 'annual_rent',
            'yearly rent': 'annual_rent',
            'annual base rent': 'annual_rent',
            'total rent': 'annual_rent',
            'annual': 'annual_rent',
            
            # Dates
            'lease from': 'lease_start',
            'lease start': 'lease_start',
            'commencement': 'lease_start',
            'start date': 'lease_start',
            'from': 'lease_start',
            
            'lease to': 'lease_end',
            'lease end': 'lease_end',
            'expiration': 'lease_end',
            'end date': 'lease_end',
            'to': 'lease_end',
        }
        
        # Apply column mapping
        new_columns = {}
        for col in df.columns:
            col_lower = str(col).lower().strip()
            
            # Find mapping
            mapped = False
            for standard_name, variations in column_mapping.items():
                if isinstance(variations, str):
                    variations = [variations]
                for variation in variations:
                    if variation == col_lower:
                        new_columns[col] = standard_name
                        mapped = True
                        break
                if mapped:
                    break
            
            # Keep original if no mapping
            if not mapped:
                if 'unnamed' in col_lower:
                    new_columns[col] = f'column_{len(new_columns)}'
                else:
                    new_columns[col] = col_lower.replace(' ', '_').replace('/', '_')
        
        df = df.rename(columns=new_columns)
        
        # Extract property code if not separate column
        if 'property_name' in df.columns and 'property_code' not in df.columns:
            df['property_code'] = df['property_name'].str.extract(r'\(([^)]+)\)')
            df['property_name_clean'] = df['property_name'].str.replace(r'\s*\([^)]+\)', '', regex=True).str.strip()
        
        # Clean numeric fields
        numeric_fields = ['square_feet', 'monthly_rent', 'annual_rent']
        for field in numeric_fields:
            if field in df.columns:
                # Remove currency symbols and commas
                df[field] = df[field].astype(str).str.replace('[\$,]', '', regex=True)
                df[field] = pd.to_numeric(df[field], errors='coerce')
        
        # Calculate derived fields
        if 'monthly_rent' in df.columns and 'annual_rent' not in df.columns:
            df['annual_rent'] = df['monthly_rent'] * 12
        elif 'annual_rent' in df.columns and 'monthly_rent' not in df.columns:
            df['monthly_rent'] = df['annual_rent'] / 12
        
        # Calculate rent PSF
        if 'annual_rent' in df.columns and 'square_feet' in df.columns:
            df['rent_psf'] = np.where(
                df['square_feet'] > 0,
                df['annual_rent'] / df['square_feet'],
                0
            )
        
        # Filter for Fund 2 properties only
        if 'property_code' in df.columns:
            fund2_mask = df['property_code'].str.startswith('x', na=False)
            df_fund2 = df[fund2_mask].copy()
            
            self.log(f"   ✓ Filtered to {len(df_fund2)} Fund 2 records (from {len(df)} total)")
            return df_fund2
        else:
            self.log(f"   ⚠ No property_code column found, returning all records")
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
        
        # Merge amendments with active charges
        rent_data = pd.merge(
            latest_amendments,
            active_charges[['amendment hmy', 'monthly amount']],
            on='amendment hmy',
            how='left'
        )
        
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
        
        self.log(f"      Calculated rent for {len(rent_summary)} leases")
        
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
        
        # Standardize calculated data columns
        calc_std = calculated_df.copy()
        calc_std = calc_std.rename(columns={
            'property code': 'property_code',
            'tenant id': 'tenant_name',
            'amendment sf': 'square_feet',
            'monthly_rent': 'monthly_rent',
            'annual_rent': 'annual_rent'
        })
        
        # Comparison metrics
        metrics = {}
        
        # 1. Record Count Comparison
        metrics['record_count'] = {
            'calculated': len(calc_std),
            'yardi': len(yardi_df),
            'difference': len(calc_std) - len(yardi_df),
            'accuracy': min(len(calc_std), len(yardi_df)) / max(len(calc_std), len(yardi_df)) * 100
        }
        
        # 2. Monthly Rent Total Comparison
        if 'monthly_rent' in calc_std.columns and 'monthly_rent' in yardi_df.columns:
            calc_monthly_total = calc_std['monthly_rent'].sum()
            yardi_monthly_total = yardi_df['monthly_rent'].sum()
            
            metrics['monthly_rent'] = {
                'calculated': calc_monthly_total,
                'yardi': yardi_monthly_total,
                'difference': calc_monthly_total - yardi_monthly_total,
                'accuracy': min(calc_monthly_total, yardi_monthly_total) / max(calc_monthly_total, yardi_monthly_total) * 100
            }
        
        # 3. Square Feet Total Comparison
        if 'square_feet' in calc_std.columns and 'square_feet' in yardi_df.columns:
            calc_sf_total = calc_std['square_feet'].sum()
            yardi_sf_total = yardi_df['square_feet'].sum()
            
            metrics['square_feet'] = {
                'calculated': calc_sf_total,
                'yardi': yardi_sf_total,
                'difference': calc_sf_total - yardi_sf_total,
                'accuracy': min(calc_sf_total, yardi_sf_total) / max(calc_sf_total, yardi_sf_total) * 100 if yardi_sf_total > 0 else 0
            }
        
        # 4. Property-level comparison
        property_comparison = self.compare_by_property(calc_std, yardi_df)
        
        # Store results
        self.test_results[test_date_key] = {
            'metrics': metrics,
            'property_comparison': property_comparison,
            'calculated_records': len(calc_std),
            'yardi_records': len(yardi_df)
        }
        
        return metrics, property_comparison
    
    def compare_by_property(self, calc_df, yardi_df):
        """Compare rent rolls at property level"""
        self.log("   Comparing by property...")
        
        property_results = []
        
        # Get common properties
        calc_props = set(calc_df['property_code'].unique()) if 'property_code' in calc_df.columns else set()
        yardi_props = set(yardi_df['property_code'].unique()) if 'property_code' in yardi_df.columns else set()
        common_props = calc_props & yardi_props
        
        for prop_code in common_props:
            calc_prop = calc_df[calc_df['property_code'] == prop_code]
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
            'record_count': 0.15,
            'monthly_rent': 0.50,
            'square_feet': 0.35
        }
        
        weighted_score = 0
        total_weight = 0
        
        for metric_name, weight in weights.items():
            if metric_name in metrics and 'accuracy' in metrics[metric_name]:
                weighted_score += metrics[metric_name]['accuracy'] * weight
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
            
            if 'calculated' in values and 'yardi' in values:
                if 'rent' in metric_name:
                    self.log(f"  Calculated: ${values['calculated']:,.2f}")
                    self.log(f"  Yardi:      ${values['yardi']:,.2f}")
                    self.log(f"  Difference: ${values['difference']:,.2f}")
                else:
                    self.log(f"  Calculated: {values['calculated']:,}")
                    self.log(f"  Yardi:      {values['yardi']:,}")
                    self.log(f"  Difference: {values['difference']:,}")
                
                self.log(f"  Accuracy:   {values['accuracy']:.1f}%")
        
        # Property-level results (top 10 discrepancies)
        if 'property_comparison' in results:
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
        
        # Recommendations
        self.log(f"\nRECOMMENDATIONS:")
        if valid_tests == 0:
            self.log("- No valid test data available. Check Yardi export file formats.")
        else:
            for test_date_key in self.test_dates.keys():
                if test_date_key in self.test_results:
                    results = self.test_results[test_date_key]
                    if 'property_comparison' in results:
                        high_discrepancy_props = [
                            p for p in results['property_comparison'] 
                            if p['monthly_accuracy'] < 90
                        ]
                        if high_discrepancy_props:
                            self.log(f"- Investigate properties with <90% accuracy in {test_date_key}:")
                            for prop in high_discrepancy_props[:5]:
                                self.log(f"  • {prop['property_code']}: {prop['monthly_accuracy']:.1f}% accuracy")
        
        self.log(f"\nVALIDATION CRITERIA:")
        self.log("- Amendment sequence logic: MAX per property/tenant combination")
        self.log("- Status filtering: 'Activated' AND 'Superseded' only")
        self.log("- Date filtering: Active on specific test date")
        self.log("- Charge code filtering: 'rent' charges only")
        
        return valid_tests > 0 and (total_accuracy / valid_tests) >= 95
    
    def run_comprehensive_test(self):
        """Run comprehensive accuracy test for all test dates"""
        self.log("🚀 STARTING COMPREHENSIVE RENT ROLL ACCURACY TEST")
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
        self.log("COMPREHENSIVE ACCURACY TEST COMPLETE")
        self.log(f"{'='*80}")
        
        return overall_success


def main():
    """Main execution function"""
    tester = RentRollAccuracyTester(verbose=True)
    success = tester.run_comprehensive_test()
    
    if success:
        print("\n🎉 All tests passed! DAX measures meet accuracy targets.")
        return 0
    else:
        print("\n⚠ Some tests failed. Review results and improve DAX measures.")
        return 1


if __name__ == "__main__":
    exit(main())