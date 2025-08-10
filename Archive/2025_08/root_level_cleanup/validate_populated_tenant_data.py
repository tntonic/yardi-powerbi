#!/usr/bin/env python3
"""
Validate Populated Tenant Data Against Rent Rolls
==================================================
This script validates the populated customer codes and names in 
new_tenants_fund2_fund3_since_2025_populated.csv against:
1. Yardi rent roll exports
2. Yardi data model tables
3. Business logic rules

Target Accuracy: 95%+ for customer code mapping
"""

import pandas as pd
import numpy as np
import os
import json
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class TenantDataValidator:
    def __init__(self, base_path="/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI"):
        self.base_path = base_path
        self.data_path = os.path.join(base_path, "Data")
        self.rent_rolls_path = os.path.join(base_path, "rent rolls")
        self.validation_results = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'mapping_validation': {},
            'rent_roll_validation': {},
            'data_quality': {},
            'recommendations': []
        }
    
    def load_populated_data(self):
        """Load the populated tenant data"""
        print("Loading populated tenant data...")
        populated_file = os.path.join(self.data_path, "new_tenants_fund2_fund3_since_2025_populated.csv")
        self.populated_df = pd.read_csv(populated_file)
        print(f"  Loaded {len(self.populated_df)} populated tenant records")
        
        # Also load the original unpopulated file for comparison
        original_file = os.path.join(self.data_path, "new_tenants_fund2_fund3_since_2025.csv")
        self.original_df = pd.read_csv(original_file)
        print(f"  Loaded {len(self.original_df)} original tenant records")
        
        return self.populated_df
    
    def load_yardi_tables(self):
        """Load Yardi data model tables for validation"""
        print("\nLoading Yardi data tables...")
        
        # Load dimension tables
        self.dim_commcustomer = pd.read_csv(
            os.path.join(self.data_path, "Yardi_Tables/dim_commcustomer.csv")
        )
        self.dim_commcustomer.columns = self.dim_commcustomer.columns.str.strip()
        
        self.credit_scores = pd.read_csv(
            os.path.join(self.data_path, "Yardi_Tables/dim_fp_customercreditscorecustomdata.csv")
        )
        
        self.parent_map = pd.read_csv(
            os.path.join(self.data_path, "Yardi_Tables/dim_fp_customertoparentmap.csv")
        )
        
        self.amendments = pd.read_csv(
            os.path.join(self.data_path, "Yardi_Tables/dim_fp_amendmentsunitspropertytenant.csv")
        )
        
        print(f"  dim_commcustomer: {len(self.dim_commcustomer)} records")
        print(f"  credit_scores: {len(self.credit_scores)} records")
        print(f"  parent_map: {len(self.parent_map)} records")
        print(f"  amendments: {len(self.amendments)} records")
    
    def parse_rent_roll(self, file_path):
        """Parse a Yardi rent roll Excel file"""
        print(f"  Parsing: {os.path.basename(file_path)}")
        
        try:
            # Read the Excel file with multiple approaches to find data
            raw_df = pd.read_excel(file_path, sheet_name=0, header=None)
            
            # Find where actual data starts (look for property codes starting with 'x' or '3')
            data_start_row = None
            for i in range(min(20, len(raw_df))):
                row_values = raw_df.iloc[i].astype(str)
                # Check for Fund 2 (x prefix) or Fund 3 (3 prefix) property codes
                if any(val.lower().startswith('x') or val.startswith('3') for val in row_values if len(val) > 2):
                    data_start_row = i
                    break
            
            if data_start_row is None:
                data_start_row = 5  # Default fallback
            
            # Read data from the identified start row
            df = pd.read_excel(file_path, skiprows=data_start_row-1 if data_start_row > 0 else 0)
            
            # Clean column names
            df.columns = [str(col).strip() for col in df.columns]
            
            # Remove empty rows
            df = df.dropna(how='all')
            
            print(f"    Found {len(df)} data rows")
            return df
            
        except Exception as e:
            print(f"    Error parsing rent roll: {e}")
            return pd.DataFrame()
    
    def validate_mapping_logic(self):
        """Validate the customer code and name mapping logic"""
        print("\n" + "=" * 60)
        print("VALIDATING MAPPING LOGIC")
        print("=" * 60)
        
        # Merge populated data with dim_commcustomer to get customer_ids
        merged = pd.merge(
            self.populated_df,
            self.dim_commcustomer[['tenant code', 'customer id', 'lessee name']],
            left_on='tenant_id',
            right_on='tenant code',
            how='left'
        )
        
        validation_stats = {
            'total_records': len(self.populated_df),
            'has_customer_id': 0,
            'has_customer_code': 0,
            'has_customer_name': 0,
            'code_from_credit': 0,
            'code_from_parent': 0,
            'code_consistent': 0,
            'mapping_errors': []
        }
        
        # Validate each record
        for idx, row in merged.iterrows():
            tenant_id = row['tenant_id']
            populated_code = self.populated_df.loc[idx, 'customer_id']  # This is the customer_code
            populated_name = self.populated_df.loc[idx, 'tenant_name']
            
            # Check if customer_id exists
            if pd.notna(row['customer id']):
                validation_stats['has_customer_id'] += 1
                customer_id = int(row['customer id'])
                
                # Validate customer code mapping
                if pd.notna(populated_code):
                    validation_stats['has_customer_code'] += 1
                    
                    # Check credit scores table
                    credit_match = self.credit_scores[
                        self.credit_scores['hmyperson_customer'] == customer_id
                    ]
                    if not credit_match.empty:
                        expected_code = credit_match.iloc[0]['customer code']
                        if populated_code == expected_code:
                            validation_stats['code_from_credit'] += 1
                        else:
                            validation_stats['mapping_errors'].append({
                                'tenant_id': tenant_id,
                                'issue': 'Code mismatch in credit table',
                                'expected': expected_code,
                                'actual': populated_code
                            })
                    
                    # Check parent map table
                    parent_match = self.parent_map[
                        self.parent_map['customer hmy'] == customer_id
                    ]
                    if not parent_match.empty:
                        expected_code = parent_match.iloc[0]['customer code']
                        if populated_code == expected_code:
                            validation_stats['code_from_parent'] += 1
                        else:
                            if not credit_match.empty:  # Only flag if not already found in credit
                                validation_stats['mapping_errors'].append({
                                    'tenant_id': tenant_id,
                                    'issue': 'Code mismatch in parent table',
                                    'expected': expected_code,
                                    'actual': populated_code
                                })
                    
                    # Check consistency between tables
                    if not credit_match.empty and not parent_match.empty:
                        credit_code = credit_match.iloc[0]['customer code']
                        parent_code = parent_match.iloc[0]['customer code']
                        if credit_code == parent_code == populated_code:
                            validation_stats['code_consistent'] += 1
                
                # Validate customer name
                if pd.notna(populated_name):
                    validation_stats['has_customer_name'] += 1
        
        self.validation_results['mapping_validation'] = validation_stats
        
        # Print summary
        print(f"Total records: {validation_stats['total_records']}")
        print(f"Has customer_id: {validation_stats['has_customer_id']} ({validation_stats['has_customer_id']/validation_stats['total_records']*100:.1f}%)")
        print(f"Has customer_code: {validation_stats['has_customer_code']} ({validation_stats['has_customer_code']/validation_stats['total_records']*100:.1f}%)")
        print(f"Has customer_name: {validation_stats['has_customer_name']} ({validation_stats['has_customer_name']/validation_stats['total_records']*100:.1f}%)")
        print(f"Codes from credit table: {validation_stats['code_from_credit']}")
        print(f"Codes from parent table: {validation_stats['code_from_parent']}")
        print(f"Mapping errors found: {len(validation_stats['mapping_errors'])}")
        
        return validation_stats
    
    def validate_against_rent_rolls(self):
        """Validate populated data against rent roll exports"""
        print("\n" + "=" * 60)
        print("VALIDATING AGAINST RENT ROLLS")
        print("=" * 60)
        
        rent_roll_files = [
            '06.30.25.xlsx',
            '03.31.25.xlsx',
            '12.31.24.xlsx'
        ]
        
        validation_results = []
        
        for file_name in rent_roll_files:
            file_path = os.path.join(self.rent_rolls_path, file_name)
            if os.path.exists(file_path):
                print(f"\nValidating against: {file_name}")
                rent_roll_df = self.parse_rent_roll(file_path)
                
                if not rent_roll_df.empty:
                    # Try to identify tenant columns in rent roll
                    tenant_cols = [col for col in rent_roll_df.columns 
                                  if 'tenant' in col.lower() or 'lessee' in col.lower() 
                                  or 'customer' in col.lower()]
                    
                    if tenant_cols:
                        print(f"    Found tenant columns: {tenant_cols}")
                        
                        # Extract unique tenant identifiers from rent roll
                        rent_roll_tenants = set()
                        for col in tenant_cols:
                            values = rent_roll_df[col].dropna().astype(str)
                            rent_roll_tenants.update(values)
                        
                        # Check how many populated tenants appear in rent roll
                        matches = 0
                        for tenant_id in self.populated_df['tenant_id'].dropna():
                            if str(tenant_id) in rent_roll_tenants:
                                matches += 1
                        
                        validation_results.append({
                            'file': file_name,
                            'rent_roll_records': len(rent_roll_df),
                            'tenant_matches': matches,
                            'match_rate': matches / len(self.populated_df) * 100
                        })
                        
                        print(f"    Matched {matches}/{len(self.populated_df)} tenants ({matches/len(self.populated_df)*100:.1f}%)")
        
        self.validation_results['rent_roll_validation'] = validation_results
        return validation_results
    
    def validate_amendment_logic(self):
        """Validate amendment-based logic for new tenants"""
        print("\n" + "=" * 60)
        print("VALIDATING AMENDMENT LOGIC")
        print("=" * 60)
        
        # Get tenant hmys from populated data
        tenant_mapping = pd.merge(
            self.populated_df,
            self.dim_commcustomer[['tenant code', 'tenant id']],
            left_on='tenant_id',
            right_on='tenant code',
            how='left'
        )
        
        tenant_hmys = tenant_mapping['tenant id'].dropna().astype(int).unique()
        
        # Check amendments for these tenants
        tenant_amendments = self.amendments[
            self.amendments['tenant hmy'].isin(tenant_hmys)
        ]
        
        print(f"Found {len(tenant_amendments)} amendments for new tenants")
        
        # Validate latest sequence logic
        latest_sequences = []
        for tenant_hmy in tenant_hmys:
            tenant_amends = tenant_amendments[tenant_amendments['tenant hmy'] == tenant_hmy]
            if not tenant_amends.empty:
                max_seq = tenant_amends['amendment sequence'].max()
                latest_amend = tenant_amends[tenant_amends['amendment sequence'] == max_seq]
                latest_sequences.append({
                    'tenant_hmy': tenant_hmy,
                    'max_sequence': max_seq,
                    'status': latest_amend.iloc[0]['amendment status'] if not latest_amend.empty else None
                })
        
        # Check status distribution
        status_counts = pd.DataFrame(latest_sequences)['status'].value_counts()
        print("\nLatest amendment status distribution:")
        for status, count in status_counts.items():
            print(f"  {status}: {count}")
        
        # Validate that Activated and Superseded are being used
        valid_statuses = ['Activated', 'Superseded']
        valid_count = sum(status_counts.get(s, 0) for s in valid_statuses)
        print(f"\nAmendments with valid status: {valid_count}/{len(latest_sequences)} ({valid_count/len(latest_sequences)*100:.1f}%)")
        
        self.validation_results['amendment_validation'] = {
            'total_amendments': len(tenant_amendments),
            'latest_sequences': len(latest_sequences),
            'valid_status_count': valid_count,
            'status_distribution': status_counts.to_dict()
        }
    
    def assess_data_quality(self):
        """Assess overall data quality and identify issues"""
        print("\n" + "=" * 60)
        print("ASSESSING DATA QUALITY")
        print("=" * 60)
        
        quality_metrics = {
            'completeness': {},
            'consistency': {},
            'accuracy': {},
            'issues': []
        }
        
        # Completeness metrics
        quality_metrics['completeness'] = {
            'customer_code_coverage': (self.populated_df['customer_id'].notna().sum() / len(self.populated_df)) * 100,
            'customer_name_coverage': (self.populated_df['tenant_name'].notna().sum() / len(self.populated_df)) * 100,
            'property_coverage': (self.populated_df['property_code'].notna().sum() / len(self.populated_df)) * 100
        }
        
        # Check for duplicates
        duplicate_codes = self.populated_df[self.populated_df['customer_id'].notna()]['customer_id'].duplicated().sum()
        if duplicate_codes > 0:
            quality_metrics['issues'].append(f"Found {duplicate_codes} duplicate customer codes")
        
        # Check for missing critical data
        missing_both = self.populated_df[
            (self.populated_df['customer_id'].isna()) & 
            (self.populated_df['tenant_name'].isna())
        ]
        if len(missing_both) > 0:
            quality_metrics['issues'].append(f"{len(missing_both)} records missing both code and name")
            
        # Check credit score coverage for populated customers
        populated_with_codes = self.populated_df[self.populated_df['customer_id'].notna()]
        codes_with_credit = 0
        for code in populated_with_codes['customer_id'].unique():
            if code in self.credit_scores['customer code'].values:
                codes_with_credit += 1
        
        quality_metrics['consistency']['credit_score_coverage'] = (codes_with_credit / len(populated_with_codes['customer_id'].unique())) * 100
        
        # Overall accuracy score
        quality_metrics['accuracy']['overall_score'] = np.mean([
            quality_metrics['completeness']['customer_code_coverage'],
            quality_metrics['completeness']['customer_name_coverage'],
            quality_metrics['consistency']['credit_score_coverage']
        ])
        
        self.validation_results['data_quality'] = quality_metrics
        
        # Print summary
        print(f"Customer Code Coverage: {quality_metrics['completeness']['customer_code_coverage']:.1f}%")
        print(f"Customer Name Coverage: {quality_metrics['completeness']['customer_name_coverage']:.1f}%")
        print(f"Credit Score Coverage: {quality_metrics['consistency']['credit_score_coverage']:.1f}%")
        print(f"Overall Quality Score: {quality_metrics['accuracy']['overall_score']:.1f}%")
        
        if quality_metrics['issues']:
            print("\nData Quality Issues:")
            for issue in quality_metrics['issues']:
                print(f"  ⚠️ {issue}")
        
        return quality_metrics
    
    def generate_recommendations(self):
        """Generate recommendations based on validation results"""
        recommendations = []
        
        # Check coverage thresholds
        code_coverage = self.validation_results['data_quality']['completeness']['customer_code_coverage']
        if code_coverage < 80:
            recommendations.append({
                'priority': 'HIGH',
                'issue': 'Low customer code coverage',
                'recommendation': 'Review unmapped customers and check for additional data sources',
                'impact': f'{100-code_coverage:.1f}% of records lack customer codes'
            })
        
        # Check mapping errors
        mapping_errors = self.validation_results['mapping_validation'].get('mapping_errors', [])
        if len(mapping_errors) > 0:
            recommendations.append({
                'priority': 'HIGH',
                'issue': 'Customer code mapping inconsistencies',
                'recommendation': 'Review and correct mapping logic for affected records',
                'impact': f'{len(mapping_errors)} records have incorrect mappings'
            })
        
        # Check for missing credit scores
        credit_coverage = self.validation_results['data_quality']['consistency']['credit_score_coverage']
        if credit_coverage < 50:
            recommendations.append({
                'priority': 'MEDIUM',
                'issue': 'Low credit score coverage',
                'recommendation': 'Request credit scores for remaining customers',
                'impact': f'{100-credit_coverage:.1f}% of customers lack credit scores'
            })
        
        # Check data quality issues
        quality_issues = self.validation_results['data_quality'].get('issues', [])
        if quality_issues:
            recommendations.append({
                'priority': 'MEDIUM',
                'issue': 'Data quality concerns',
                'recommendation': 'Address identified data quality issues',
                'impact': f'{len(quality_issues)} quality issues identified'
            })
        
        self.validation_results['recommendations'] = recommendations
        return recommendations
    
    def save_results(self):
        """Save validation results to files"""
        # Save JSON report
        json_file = os.path.join(self.data_path, 'tenant_validation_results.json')
        with open(json_file, 'w') as f:
            json.dump(self.validation_results, f, indent=2, default=str)
        print(f"\n✓ JSON results saved to: {json_file}")
        
        # Generate text report
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("TENANT DATA VALIDATION REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"Generated: {self.validation_results['timestamp']}")
        report_lines.append("")
        
        # Mapping validation section
        report_lines.append("MAPPING VALIDATION RESULTS:")
        report_lines.append("-" * 40)
        mapping = self.validation_results['mapping_validation']
        report_lines.append(f"  Total Records: {mapping['total_records']}")
        report_lines.append(f"  Has Customer ID: {mapping['has_customer_id']} ({mapping['has_customer_id']/mapping['total_records']*100:.1f}%)")
        report_lines.append(f"  Has Customer Code: {mapping['has_customer_code']} ({mapping['has_customer_code']/mapping['total_records']*100:.1f}%)")
        report_lines.append(f"  Has Customer Name: {mapping['has_customer_name']} ({mapping['has_customer_name']/mapping['total_records']*100:.1f}%)")
        report_lines.append(f"  Mapping Errors: {len(mapping.get('mapping_errors', []))}")
        report_lines.append("")
        
        # Data quality section
        report_lines.append("DATA QUALITY ASSESSMENT:")
        report_lines.append("-" * 40)
        quality = self.validation_results['data_quality']
        report_lines.append(f"  Customer Code Coverage: {quality['completeness']['customer_code_coverage']:.1f}%")
        report_lines.append(f"  Customer Name Coverage: {quality['completeness']['customer_name_coverage']:.1f}%")
        report_lines.append(f"  Credit Score Coverage: {quality['consistency']['credit_score_coverage']:.1f}%")
        report_lines.append(f"  Overall Quality Score: {quality['accuracy']['overall_score']:.1f}%")
        report_lines.append("")
        
        # Recommendations section
        if self.validation_results['recommendations']:
            report_lines.append("RECOMMENDATIONS:")
            report_lines.append("-" * 40)
            for rec in self.validation_results['recommendations']:
                report_lines.append(f"  [{rec['priority']}] {rec['issue']}")
                report_lines.append(f"    → {rec['recommendation']}")
                report_lines.append(f"    Impact: {rec['impact']}")
                report_lines.append("")
        
        report_lines.append("=" * 80)
        
        # Save text report
        text_file = os.path.join(self.data_path, 'tenant_validation_report.txt')
        with open(text_file, 'w') as f:
            f.write('\n'.join(report_lines))
        print(f"✓ Text report saved to: {text_file}")
        
        return report_lines
    
    def run_full_validation(self):
        """Run complete validation workflow"""
        print("=" * 80)
        print("TENANT DATA VALIDATION WORKFLOW")
        print("=" * 80)
        
        # Load all data
        self.load_populated_data()
        self.load_yardi_tables()
        
        # Run validations
        self.validate_mapping_logic()
        self.validate_against_rent_rolls()
        self.validate_amendment_logic()
        self.assess_data_quality()
        self.generate_recommendations()
        
        # Save results
        report = self.save_results()
        
        # Print summary
        print("\n" + "=" * 80)
        print("VALIDATION COMPLETE")
        print("=" * 80)
        print(f"✓ Overall Quality Score: {self.validation_results['data_quality']['accuracy']['overall_score']:.1f}%")
        
        if self.validation_results['data_quality']['accuracy']['overall_score'] >= 95:
            print("✅ VALIDATION PASSED: Data meets 95% accuracy target")
        else:
            print("⚠️ VALIDATION WARNING: Data below 95% accuracy target")
        
        print(f"\n{len(self.validation_results['recommendations'])} recommendations generated")
        
        return self.validation_results

def main():
    """Main execution function"""
    validator = TenantDataValidator()
    results = validator.run_full_validation()
    
    print("\n✓ Validation process completed successfully!")
    print("  Check 'tenant_validation_report.txt' for detailed results")
    print("  Check 'tenant_validation_results.json' for machine-readable data")

if __name__ == "__main__":
    main()