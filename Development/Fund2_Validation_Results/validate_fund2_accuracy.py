#!/usr/bin/env python3
"""
Fund 2 Rent Roll Accuracy Validation
Compare generated rent rolls against actual Yardi exports for validation
Target: 95-99% accuracy for comprehensive validation success
"""

import pandas as pd
import numpy as np
import os
import sys

# Add parent directory to path for importing clean_rent_roll
sys.path.append('/Users/michaeltang/Documents/GitHub/BI/PBI v1.7/python scripts')
from clean_rent_roll import RentRollCleaner

class Fund2AccuracyValidator:
    """Validate generated rent rolls against actual Yardi exports"""
    
    def __init__(self, verbose=True):
        self.verbose = verbose
        self.results = {}
        self.cleaner = RentRollCleaner(verbose=False)
        
        # Define validation targets
        self.validation_targets = [
            {
                'target_date': '2025-03-31',
                'date_str': 'March 31, 2025',
                'generated_file': '/Users/michaeltang/Documents/GitHub/BI/PBI v1.7/Fund2_Validation_Results/fund2_rent_roll_generated_mar31_2025.csv',
                'actual_file': '/Users/michaeltang/Documents/GitHub/BI/PBI v1.7/rent rolls/03.31.25.xlsx'
            },
            {
                'target_date': '2024-12-31', 
                'date_str': 'December 31, 2024',
                'generated_file': '/Users/michaeltang/Documents/GitHub/BI/PBI v1.7/Fund2_Validation_Results/fund2_rent_roll_generated_dec31_2024.csv',
                'actual_file': '/Users/michaeltang/Documents/GitHub/BI/PBI v1.7/rent rolls/12.31.24.xlsx'
            }
        ]
    
    def load_and_clean_actual_rent_roll(self, actual_file, target_date_str):
        """Load and clean actual Yardi rent roll export"""
        if self.verbose:
            print(f"Loading actual rent roll: {os.path.basename(actual_file)}")
        
        # Clean the actual rent roll
        actual_df = self.cleaner.clean_rent_roll(actual_file)
        
        # Filter to Fund 2 properties (property codes starting with 'x')
        if 'property_code' in actual_df.columns:
            fund2_actual = actual_df[
                actual_df['property_code'].astype(str).str.upper().str.startswith('X')
            ].copy()
        else:
            # Try other possible column names
            prop_cols = [col for col in actual_df.columns if 'prop' in col.lower() and 'code' in col.lower()]
            if prop_cols:
                fund2_actual = actual_df[
                    actual_df[prop_cols[0]].astype(str).str.upper().str.startswith('X')
                ].copy()
            else:
                fund2_actual = actual_df.copy()  # Use all if can't filter
        
        if self.verbose:
            print(f"   Total records: {len(actual_df):,}")
            print(f"   Fund 2 records: {len(fund2_actual):,}")
        
        return fund2_actual
    
    def load_generated_rent_roll(self, generated_file, target_date_str):
        """Load generated rent roll"""
        if self.verbose:
            print(f"Loading generated rent roll: {os.path.basename(generated_file)}")
        
        generated_df = pd.read_csv(generated_file)
        
        if self.verbose:
            print(f"   Generated records: {len(generated_df):,}")
        
        return generated_df
    
    def compare_rent_rolls(self, actual_df, generated_df, target_info):
        """Compare actual vs generated rent rolls for accuracy metrics"""
        date_str = target_info['date_str']
        
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"ACCURACY COMPARISON - {date_str.upper()}")
            print(f"{'='*60}")
        
        # Calculate summary metrics
        actual_summary = self.calculate_summary_metrics(actual_df, "Actual")
        generated_summary = self.calculate_summary_metrics(generated_df, "Generated")
        
        # Compare key metrics
        comparison_results = {
            'date': date_str,
            'actual_summary': actual_summary,
            'generated_summary': generated_summary,
            'accuracy_metrics': {}
        }
        
        # Key accuracy comparisons
        key_metrics = [
            ('record_count', 'Record Count'),
            ('total_monthly_rent', 'Total Monthly Rent'),
            ('total_leased_sf', 'Total Leased SF'),
            ('property_count', 'Property Count'),
            ('tenant_count', 'Tenant Count'),
            ('avg_rent_psf', 'Average Rent PSF')
        ]
        
        if self.verbose:
            print("\nKey Metric Comparisons:")
            print("-" * 50)
        
        for metric_key, metric_name in key_metrics:
            actual_val = actual_summary.get(metric_key, 0)
            generated_val = generated_summary.get(metric_key, 0)
            
            # Calculate accuracy percentage
            if actual_val > 0:
                accuracy_pct = min(100, (1 - abs(actual_val - generated_val) / actual_val) * 100)
            else:
                accuracy_pct = 100 if generated_val == 0 else 0
            
            comparison_results['accuracy_metrics'][metric_key] = {
                'actual': actual_val,
                'generated': generated_val,
                'accuracy_pct': accuracy_pct,
                'variance': generated_val - actual_val,
                'variance_pct': ((generated_val - actual_val) / actual_val * 100) if actual_val > 0 else 0
            }
            
            if self.verbose:
                print(f"{metric_name}:")
                if metric_key in ['total_monthly_rent', 'avg_rent_psf']:
                    print(f"  Actual:    ${actual_val:,.2f}")
                    print(f"  Generated: ${generated_val:,.2f}")
                elif metric_key == 'total_leased_sf':
                    print(f"  Actual:    {actual_val:,.0f}")
                    print(f"  Generated: {generated_val:,.0f}")
                else:
                    print(f"  Actual:    {actual_val:,}")
                    print(f"  Generated: {generated_val:,}")
                
                print(f"  Accuracy:  {accuracy_pct:.1f}%")
                if accuracy_pct < 95:
                    print(f"  ⚠️ Below 95% target")
                elif accuracy_pct >= 95:
                    print(f"  ✅ Above 95% target")
                print()
        
        # Calculate overall accuracy score
        accuracy_scores = [v['accuracy_pct'] for v in comparison_results['accuracy_metrics'].values()]
        overall_accuracy = sum(accuracy_scores) / len(accuracy_scores) if accuracy_scores else 0
        comparison_results['overall_accuracy'] = overall_accuracy
        
        if self.verbose:
            print(f"Overall Accuracy Score: {overall_accuracy:.1f}%")
            if overall_accuracy >= 95:
                print("✅ MEETS 95-99% ACCURACY TARGET")
            else:
                print("❌ BELOW 95% ACCURACY TARGET")
        
        return comparison_results
    
    def calculate_summary_metrics(self, df, source_label):
        """Calculate key summary metrics from a rent roll dataframe"""
        summary = {'source': source_label}
        
        try:
            # Record count
            summary['record_count'] = len(df)
            
            # Total monthly rent - try multiple column names
            rent_cols = [col for col in df.columns if 'rent' in col.lower() and 'month' in col.lower()]
            if not rent_cols:
                rent_cols = [col for col in df.columns if 'month' in col.lower() and ('rent' in col.lower() or 'amount' in col.lower())]
            if not rent_cols:
                rent_cols = [col for col in df.columns if 'rent' in col.lower()]
            
            if rent_cols:
                summary['total_monthly_rent'] = df[rent_cols[0]].sum() if df[rent_cols[0]].notna().any() else 0
            else:
                summary['total_monthly_rent'] = 0
            
            # Total leased SF - try multiple column names
            sf_cols = [col for col in df.columns if ('sf' in col.lower() or 'square' in col.lower() or 'area' in col.lower()) and 'amendment' in col.lower()]
            if not sf_cols:
                sf_cols = [col for col in df.columns if 'sf' in col.lower() or 'square' in col.lower() or 'area' in col.lower()]
            
            if sf_cols:
                summary['total_leased_sf'] = df[sf_cols[0]].sum() if df[sf_cols[0]].notna().any() else 0
            else:
                summary['total_leased_sf'] = 0
            
            # Property count
            prop_cols = [col for col in df.columns if 'prop' in col.lower() and 'code' in col.lower()]
            if prop_cols:
                summary['property_count'] = df[prop_cols[0]].nunique()
            else:
                summary['property_count'] = 0
            
            # Tenant count
            tenant_cols = [col for col in df.columns if 'tenant' in col.lower() and ('id' in col.lower() or 'name' in col.lower())]
            if tenant_cols:
                summary['tenant_count'] = df[tenant_cols[0]].nunique()
            else:
                summary['tenant_count'] = 0
            
            # Average rent PSF
            if summary['total_monthly_rent'] > 0 and summary['total_leased_sf'] > 0:
                summary['avg_rent_psf'] = (summary['total_monthly_rent'] * 12) / summary['total_leased_sf']
            else:
                summary['avg_rent_psf'] = 0
                
        except Exception as e:
            print(f"Warning: Error calculating metrics for {source_label}: {e}")
            # Provide defaults
            for key in ['record_count', 'total_monthly_rent', 'total_leased_sf', 'property_count', 'tenant_count', 'avg_rent_psf']:
                if key not in summary:
                    summary[key] = 0
        
        return summary
    
    def validate_all_target_dates(self):
        """Run validation for all target dates"""
        print("=" * 80)
        print("FUND 2 RENT ROLL ACCURACY VALIDATION")
        print("Target: 95-99% accuracy for validation success")
        print("=" * 80)
        
        overall_results = []
        
        for target_info in self.validation_targets:
            try:
                # Load actual and generated rent rolls
                actual_df = self.load_and_clean_actual_rent_roll(
                    target_info['actual_file'], 
                    target_info['date_str']
                )
                
                generated_df = self.load_generated_rent_roll(
                    target_info['generated_file'],
                    target_info['date_str']
                )
                
                # Compare for accuracy
                comparison_result = self.compare_rent_rolls(actual_df, generated_df, target_info)
                overall_results.append(comparison_result)
                
            except Exception as e:
                print(f"Error validating {target_info['date_str']}: {e}")
                continue
        
        # Calculate final validation score
        if overall_results:
            final_accuracy = sum(r['overall_accuracy'] for r in overall_results) / len(overall_results)
            
            print(f"\n{'='*60}")
            print("FINAL VALIDATION RESULTS")
            print(f"{'='*60}")
            print(f"Overall Accuracy Score: {final_accuracy:.1f}%")
            
            if final_accuracy >= 95:
                print("✅ SUCCESS: Meets 95-99% accuracy target")
                print("✅ Ready for Phase 3: Performance Testing")
            else:
                print("❌ NEEDS IMPROVEMENT: Below 95% accuracy target")
                print("❌ Phase 3 testing should be skipped until accuracy improves")
            
            # Save detailed results
            results_file = '/Users/michaeltang/Documents/GitHub/BI/PBI v1.7/Fund2_Validation_Results/accuracy_validation_results.csv'
            self.save_results_summary(overall_results, results_file)
            
        return overall_results
    
    def save_results_summary(self, results, output_file):
        """Save validation results summary to CSV"""
        if not results:
            return
        
        summary_data = []
        for result in results:
            row = {'date': result['date'], 'overall_accuracy': result['overall_accuracy']}
            for metric_key, metric_data in result['accuracy_metrics'].items():
                row[f'{metric_key}_accuracy'] = metric_data['accuracy_pct']
                row[f'{metric_key}_actual'] = metric_data['actual']
                row[f'{metric_key}_generated'] = metric_data['generated']
            summary_data.append(row)
        
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_csv(output_file, index=False)
        
        if self.verbose:
            print(f"\nDetailed results saved to: {output_file}")

def main():
    """Main execution function"""
    validator = Fund2AccuracyValidator(verbose=True)
    results = validator.validate_all_target_dates()
    
    return results

if __name__ == "__main__":
    main()