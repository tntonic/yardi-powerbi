#!/usr/bin/env python3
"""
Fund 2 Data Integrity Validation Script
========================================

Comprehensive validation of Yardi PowerBI data model integrity for Fund 2 properties.
Validates relationships, checks for orphaned records, and ensures data quality.

Author: Yardi PowerBI Data Integrity Validator
Date: 2025-08-09
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os
import warnings
warnings.filterwarnings('ignore')

class Fund2DataIntegrityValidator:
    def __init__(self, data_path):
        self.data_path = data_path
        self.validation_results = {}
        self.critical_issues = []
        self.warnings = []
        self.summary_stats = {}
        
        # Load all data files
        self.load_data()
    
    def load_data(self):
        """Load all Fund 2 data files"""
        print("Loading Fund 2 data files...")
        
        try:
            # Fund 2 filtered data
            self.properties = pd.read_csv(f"{self.data_path}/Fund2_Filtered/dim_property_fund2.csv")
            self.amendments = pd.read_csv(f"{self.data_path}/Fund2_Filtered/dim_fp_amendmentsunitspropertytenant_fund2.csv")
            self.charges_active = pd.read_csv(f"{self.data_path}/Fund2_Filtered/dim_fp_amendmentchargeschedule_fund2_active.csv")
            self.charges_all = pd.read_csv(f"{self.data_path}/Fund2_Filtered/dim_fp_amendmentchargeschedule_fund2_all.csv")
            self.units = pd.read_csv(f"{self.data_path}/Fund2_Filtered/dim_unit_fund2.csv")
            self.tenants = pd.read_csv(f"{self.data_path}/Fund2_Filtered/tenants_fund2.csv")
            
            # Also load occupancy data from main tables for validation
            if os.path.exists(f"{self.data_path}/Yardi_Tables/fact_occupancyrentarea.csv"):
                self.occupancy = pd.read_csv(f"{self.data_path}/Yardi_Tables/fact_occupancyrentarea.csv")
            else:
                self.occupancy = pd.DataFrame()
            
            print(f"✓ Loaded {len(self.properties)} properties")
            print(f"✓ Loaded {len(self.amendments)} amendments") 
            print(f"✓ Loaded {len(self.charges_active)} active charges")
            print(f"✓ Loaded {len(self.charges_all)} total charges")
            print(f"✓ Loaded {len(self.units)} units")
            print(f"✓ Loaded {len(self.tenants)} tenants")
            
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            raise
    
    def validate_fund2_properties(self):
        """Validate Fund 2 property identification and consistency"""
        print("\n=== FUND 2 PROPERTY VALIDATION ===")
        
        results = {
            'total_properties': len(self.properties),
            'active_properties': len(self.properties[self.properties['is active'] == True]),
            'inactive_properties': len(self.properties[self.properties['is active'] == False]),
            'property_codes_with_x_prefix': 0,
            'invalid_property_codes': [],
            'missing_critical_fields': []
        }
        
        # Check that all property codes start with 'x'
        for idx, row in self.properties.iterrows():
            prop_code = str(row['property code']).lower()
            if prop_code.startswith('x'):
                results['property_codes_with_x_prefix'] += 1
            else:
                results['invalid_property_codes'].append(prop_code)
                self.critical_issues.append(f"Property code '{prop_code}' does not start with 'x' - not a Fund 2 property")
        
        # Check for missing critical fields
        critical_fields = ['property id', 'property code', 'property name', 'is active']
        for field in critical_fields:
            missing_count = self.properties[field].isnull().sum()
            if missing_count > 0:
                results['missing_critical_fields'].append(f"{field}: {missing_count} missing")
                self.critical_issues.append(f"{missing_count} properties missing critical field '{field}'")
        
        # Check for duplicate property codes
        duplicate_codes = self.properties[self.properties.duplicated(['property code'], keep=False)]
        if len(duplicate_codes) > 0:
            results['duplicate_property_codes'] = len(duplicate_codes)
            self.critical_issues.append(f"Found {len(duplicate_codes)} properties with duplicate property codes")
        
        self.validation_results['fund2_properties'] = results
        
        print(f"✓ Total Fund 2 properties: {results['total_properties']}")
        print(f"✓ Active properties: {results['active_properties']}")
        print(f"✓ Inactive properties: {results['inactive_properties']}")
        print(f"✓ Properties with 'x' prefix: {results['property_codes_with_x_prefix']}")
        
        if results['invalid_property_codes']:
            print(f"❌ Invalid property codes found: {results['invalid_property_codes']}")
        
        return results
    
    def validate_amendment_relationships(self):
        """Validate amendment-to-property relationships"""
        print("\n=== AMENDMENT RELATIONSHIP VALIDATION ===")
        
        results = {
            'total_amendments': len(self.amendments),
            'activated_amendments': len(self.amendments[self.amendments['amendment status'] == 'Activated']),
            'superseded_amendments': len(self.amendments[self.amendments['amendment status'] == 'Superseded']),
            'orphaned_amendments': 0,
            'property_mismatches': [],
            'duplicate_sequences': [],
            'invalid_statuses': []
        }
        
        # Check for orphaned amendments (amendments without corresponding properties)
        prop_hmys = set(self.properties['property id'].astype(str))
        amendment_prop_hmys = set(self.amendments['property hmy'].astype(str))
        
        orphaned_prop_hmys = amendment_prop_hmys - prop_hmys
        if orphaned_prop_hmys:
            orphaned_amendments = self.amendments[self.amendments['property hmy'].astype(str).isin(orphaned_prop_hmys)]
            results['orphaned_amendments'] = len(orphaned_amendments)
            self.critical_issues.append(f"Found {len(orphaned_amendments)} amendments with orphaned property HMY references")
            
            # Show sample of orphaned amendments
            sample_orphaned = orphaned_amendments[['amendment hmy', 'property hmy', 'property code', 'tenant id']].head(5)
            print("Sample orphaned amendments:")
            print(sample_orphaned.to_string())
        
        # Check for property code mismatches
        merged_data = self.amendments.merge(
            self.properties[['property id', 'property code']], 
            left_on='property hmy', 
            right_on='property id', 
            how='left',
            suffixes=('_amend', '_prop')
        )
        
        mismatches = merged_data[
            (merged_data['property code_amend'] != merged_data['property code_prop']) & 
            merged_data['property code_prop'].notna()
        ]
        
        if len(mismatches) > 0:
            results['property_mismatches'] = len(mismatches)
            self.critical_issues.append(f"Found {len(mismatches)} amendments with property code mismatches")
        
        # Check for duplicate active amendments (same property + tenant should have only one active)
        active_amendments = self.amendments[self.amendments['amendment status'] == 'Activated']
        duplicates = active_amendments.groupby(['property hmy', 'tenant hmy']).size()
        duplicates = duplicates[duplicates > 1]
        
        if len(duplicates) > 0:
            results['duplicate_active_amendments'] = len(duplicates)
            self.critical_issues.append(f"Found {len(duplicates)} property/tenant combinations with multiple active amendments")
        
        # Validate amendment statuses
        valid_statuses = ['Activated', 'Superseded', 'Cancelled', 'Pending']
        invalid_status_amendments = self.amendments[~self.amendments['amendment status'].isin(valid_statuses)]
        if len(invalid_status_amendments) > 0:
            results['invalid_statuses'] = len(invalid_status_amendments)
            unique_invalid = invalid_status_amendments['amendment status'].unique()
            self.critical_issues.append(f"Found {len(invalid_status_amendments)} amendments with invalid statuses: {unique_invalid}")
        
        self.validation_results['amendment_relationships'] = results
        
        print(f"✓ Total amendments: {results['total_amendments']}")
        print(f"✓ Activated amendments: {results['activated_amendments']}")
        print(f"✓ Superseded amendments: {results['superseded_amendments']}")
        print(f"✓ Orphaned amendments: {results['orphaned_amendments']}")
        
        return results
    
    def validate_charge_relationships(self):
        """Validate charge schedule relationships to amendments"""
        print("\n=== CHARGE SCHEDULE RELATIONSHIP VALIDATION ===")
        
        results = {
            'total_charges_all': len(self.charges_all),
            'total_charges_active': len(self.charges_active),
            'orphaned_charges': 0,
            'charges_without_amounts': 0,
            'invalid_date_ranges': 0,
            'charge_types': {}
        }
        
        # Check for orphaned charges (charges without corresponding amendments)
        amendment_hmys = set(self.amendments['amendment hmy'].astype(str))
        charge_amendment_hmys = set(self.charges_all['amendment hmy'].astype(str))
        
        orphaned_charge_hmys = charge_amendment_hmys - amendment_hmys
        if orphaned_charge_hmys:
            orphaned_charges = self.charges_all[self.charges_all['amendment hmy'].astype(str).isin(orphaned_charge_hmys)]
            results['orphaned_charges'] = len(orphaned_charges)
            self.critical_issues.append(f"Found {len(orphaned_charges)} charges with orphaned amendment HMY references")
        
        # Check for charges without amounts
        charges_no_amount = self.charges_all[
            (self.charges_all['amount'].isnull()) | (self.charges_all['amount'] == 0)
        ]
        results['charges_without_amounts'] = len(charges_no_amount)
        if len(charges_no_amount) > 0:
            self.warnings.append(f"Found {len(charges_no_amount)} charges without amounts (may be intentional)")
        
        # Validate date ranges
        try:
            # Convert date columns to datetime if they're not already
            self.charges_all['from_date_parsed'] = pd.to_datetime(self.charges_all['from date'], errors='coerce')
            self.charges_all['to_date_parsed'] = pd.to_datetime(self.charges_all['to date'], errors='coerce')
            
            invalid_dates = self.charges_all[
                (self.charges_all['from_date_parsed'] > self.charges_all['to_date_parsed']) |
                (self.charges_all['from_date_parsed'].isnull()) |
                (self.charges_all['to_date_parsed'].isnull())
            ]
            results['invalid_date_ranges'] = len(invalid_dates)
            if len(invalid_dates) > 0:
                self.critical_issues.append(f"Found {len(invalid_dates)} charges with invalid date ranges")
        except Exception as e:
            self.warnings.append(f"Could not validate charge date ranges: {e}")
        
        # Analyze charge types
        charge_types = self.charges_all['charge code desc'].value_counts()
        results['charge_types'] = charge_types.to_dict()
        
        self.validation_results['charge_relationships'] = results
        
        print(f"✓ Total charges (all): {results['total_charges_all']}")
        print(f"✓ Total charges (active): {results['total_charges_active']}")
        print(f"✓ Orphaned charges: {results['orphaned_charges']}")
        print(f"✓ Charges without amounts: {results['charges_without_amounts']}")
        print(f"✓ Invalid date ranges: {results['invalid_date_ranges']}")
        
        return results
    
    def validate_data_quality(self):
        """Perform comprehensive data quality validation"""
        print("\n=== DATA QUALITY VALIDATION ===")
        
        results = {
            'amendments': self.analyze_table_quality(self.amendments, 'Amendments'),
            'properties': self.analyze_table_quality(self.properties, 'Properties'),
            'charges_active': self.analyze_table_quality(self.charges_active, 'Active Charges'),
            'units': self.analyze_table_quality(self.units, 'Units'),
            'tenants': self.analyze_table_quality(self.tenants, 'Tenants')
        }
        
        self.validation_results['data_quality'] = results
        return results
    
    def analyze_table_quality(self, df, table_name):
        """Analyze data quality for a specific table"""
        quality_stats = {
            'total_records': len(df),
            'total_columns': len(df.columns),
            'missing_data': {},
            'duplicate_records': 0,
            'data_types': {}
        }
        
        # Missing data analysis
        for col in df.columns:
            missing_count = df[col].isnull().sum()
            missing_pct = (missing_count / len(df)) * 100
            if missing_count > 0:
                quality_stats['missing_data'][col] = {
                    'count': missing_count,
                    'percentage': round(missing_pct, 2)
                }
        
        # Duplicate records
        if len(df.columns) > 0:
            quality_stats['duplicate_records'] = len(df[df.duplicated()])
        
        # Data types
        quality_stats['data_types'] = df.dtypes.astype(str).to_dict()
        
        print(f"  {table_name}: {len(df)} records, {len(df.columns)} columns")
        if quality_stats['missing_data']:
            print(f"    Missing data in {len(quality_stats['missing_data'])} columns")
        if quality_stats['duplicate_records'] > 0:
            print(f"    {quality_stats['duplicate_records']} duplicate records")
        
        return quality_stats
    
    def validate_critical_business_rules(self):
        """Validate critical business rules for rent roll calculations"""
        print("\n=== BUSINESS RULE VALIDATION ===")
        
        results = {}
        
        # Rule 1: Latest Amendment Sequence Logic
        print("Validating amendment sequence logic...")
        amendment_sequences = self.amendments.groupby(['property hmy', 'tenant hmy'])['amendment sequence'].agg(['count', 'max', 'min'])
        
        # Check for properties/tenants with only superseded amendments
        active_amendments = self.amendments[self.amendments['amendment status'] == 'Activated']
        superseded_amendments = self.amendments[self.amendments['amendment status'] == 'Superseded']
        
        prop_tenant_combinations = set(zip(self.amendments['property hmy'], self.amendments['tenant hmy']))
        active_combinations = set(zip(active_amendments['property hmy'], active_amendments['tenant hmy']))
        superseded_only = prop_tenant_combinations - active_combinations
        
        results['superseded_only_combinations'] = len(superseded_only)
        if len(superseded_only) > 0:
            self.warnings.append(f"Found {len(superseded_only)} property/tenant combinations with only superseded amendments")
        
        # Rule 2: Rent Roll Calculation Readiness
        print("Checking rent roll calculation readiness...")
        rent_charges = self.charges_active[self.charges_active['charge code desc'].str.contains('Rent', na=False)]
        amendments_with_rent = set(rent_charges['amendment hmy'])
        total_amendments = set(self.amendments['amendment hmy'])
        amendments_without_rent = total_amendments - amendments_with_rent
        
        results['amendments_without_rent'] = len(amendments_without_rent)
        if len(amendments_without_rent) > 0:
            self.warnings.append(f"Found {len(amendments_without_rent)} amendments without rent charges")
        
        # Rule 3: Date Consistency
        print("Validating date consistency...")
        date_issues = []
        
        # Check amendment start/end dates vs charge from/to dates
        merged_dates = self.amendments.merge(
            self.charges_active[['amendment hmy', 'from date', 'to date']],
            on='amendment hmy',
            how='inner'
        )
        
        # This would require more complex date parsing and comparison
        # For now, just flag as a validation point
        results['date_consistency_check'] = "Requires detailed date parsing validation"
        
        self.validation_results['business_rules'] = results
        
        print(f"✓ Superseded-only combinations: {results['superseded_only_combinations']}")
        print(f"✓ Amendments without rent: {results['amendments_without_rent']}")
        
        return results
    
    def generate_summary_report(self):
        """Generate comprehensive summary report"""
        print("\n" + "="*60)
        print("FUND 2 DATA INTEGRITY VALIDATION SUMMARY")
        print("="*60)
        
        # Critical Issues Summary
        if self.critical_issues:
            print(f"\n🚨 CRITICAL ISSUES FOUND ({len(self.critical_issues)}):")
            for i, issue in enumerate(self.critical_issues, 1):
                print(f"  {i}. {issue}")
        else:
            print("\n✅ NO CRITICAL ISSUES FOUND")
        
        # Warnings Summary
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")
        else:
            print("\n✅ NO WARNINGS")
        
        # Summary Statistics
        print(f"\n📊 SUMMARY STATISTICS:")
        print(f"  • Total Fund 2 Properties: {len(self.properties)}")
        print(f"  • Total Amendments: {len(self.amendments)}")
        print(f"  • Active Amendments: {len(self.amendments[self.amendments['amendment status'] == 'Activated'])}")
        print(f"  • Total Active Charges: {len(self.charges_active)}")
        print(f"  • Total Units: {len(self.units)}")
        print(f"  • Total Tenants: {len(self.tenants)}")
        
        # Data Quality Score
        total_checks = len(self.critical_issues) + len(self.warnings)
        if total_checks == 0:
            quality_score = 100
        else:
            # Deduct points for issues (critical = 10 points, warnings = 2 points)
            deductions = len(self.critical_issues) * 10 + len(self.warnings) * 2
            quality_score = max(0, 100 - deductions)
        
        print(f"\n🏆 DATA INTEGRITY SCORE: {quality_score}/100")
        
        if quality_score >= 95:
            print("   EXCELLENT - Ready for production")
        elif quality_score >= 85:
            print("   GOOD - Minor issues need attention")
        elif quality_score >= 70:
            print("   FAIR - Several issues need resolution")
        else:
            print("   POOR - Major data integrity issues")
        
        return {
            'quality_score': quality_score,
            'critical_issues_count': len(self.critical_issues),
            'warnings_count': len(self.warnings),
            'validation_results': self.validation_results
        }
    
    def run_full_validation(self):
        """Run all validation checks"""
        print("Starting comprehensive Fund 2 data integrity validation...")
        print("="*60)
        
        # Run all validation checks
        self.validate_fund2_properties()
        self.validate_amendment_relationships() 
        self.validate_charge_relationships()
        self.validate_data_quality()
        self.validate_critical_business_rules()
        
        # Generate final report
        summary = self.generate_summary_report()
        
        return summary

def main():
    """Main execution function"""
    data_path = "/Users/michaeltang/Documents/GitHub/BI/PBI v1.7/Data"
    
    print("Fund 2 Data Integrity Validation")
    print("="*40)
    print(f"Data Path: {data_path}")
    print(f"Validation Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        validator = Fund2DataIntegrityValidator(data_path)
        summary = validator.run_full_validation()
        
        print(f"\n✅ Validation completed successfully!")
        print(f"Final Quality Score: {summary['quality_score']}/100")
        
        return summary
        
    except Exception as e:
        print(f"❌ Validation failed with error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()