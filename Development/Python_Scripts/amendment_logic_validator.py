#!/usr/bin/env python3
"""
Amendment Logic Validation for PowerBI DAX Measures
===================================================

This script validates that DAX measures properly implement:
1. Latest amendment sequence selection (MAX sequence per property/tenant)
2. Proper status filtering (Activated + Superseded)
3. Charge integration logic (amendments WITH rent charges)
4. Business rule compliance (exclude Proposal in DM, etc.)

Validation Target: 95%+ accuracy for rent roll calculations
"""

import re
import pandas as pd
import os
from typing import Dict, List, Tuple

class AmendmentLogicValidator:
    def __init__(self, dax_file_path: str, data_path: str):
        self.dax_file_path = dax_file_path
        self.data_path = data_path
        self.measures = self._extract_measures()
        self.validation_results = {}
    
    def _extract_measures(self) -> Dict[str, str]:
        """Extract all DAX measures from the file"""
        measures = {}
        
        with open(self.dax_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split by measure definitions
        measure_pattern = r'^([A-Za-z][A-Za-z0-9\s%().-]+?)\s*=\s*\n(.*?)(?=\n^[A-Za-z]|\Z)'
        matches = re.findall(measure_pattern, content, re.MULTILINE | re.DOTALL)
        
        for measure_name, measure_content in matches:
            measures[measure_name.strip()] = measure_content.strip()
        
        return measures
    
    def validate_all_measures(self) -> Dict[str, any]:
        """Run validation on all rent roll related measures"""
        print("🔍 Validating Amendment Logic in DAX Measures...")
        
        # Categories of measures that should use amendment logic
        rent_roll_measures = [name for name in self.measures.keys() 
                             if any(keyword in name.lower() for keyword in 
                                   ['rent', 'lease', 'walt', 'expir', 'psf', 'current'])]
        
        results = {
            'total_measures': len(self.measures),
            'rent_roll_measures': len(rent_roll_measures),
            'validation_details': {},
            'critical_issues': [],
            'recommendations': []
        }
        
        print(f"Found {len(rent_roll_measures)} rent roll related measures to validate")
        
        for measure_name in rent_roll_measures:
            measure_content = self.measures[measure_name]
            validation = self._validate_measure_logic(measure_name, measure_content)
            results['validation_details'][measure_name] = validation
            
            # Collect critical issues
            if not validation['has_latest_sequence_logic']:
                results['critical_issues'].append(f"{measure_name}: Missing latest sequence filter")
            if not validation['has_proper_status_filter']:
                results['critical_issues'].append(f"{measure_name}: Improper status filtering")
            if not validation['has_charge_integration'] and 'rent' in measure_name.lower():
                results['critical_issues'].append(f"{measure_name}: Missing charge integration")
        
        # Generate recommendations
        results['recommendations'] = self._generate_recommendations(results)
        
        return results
    
    def _validate_measure_logic(self, measure_name: str, measure_content: str) -> Dict[str, any]:
        """Validate amendment logic patterns in a single measure"""
        validation = {
            'measure_name': measure_name,
            'has_latest_sequence_logic': False,
            'has_proper_status_filter': False,
            'has_charge_integration': False,
            'has_business_rule_exclusions': False,
            'uses_deprecated_patterns': False,
            'complexity_score': 0
        }
        
        # Check for latest sequence logic
        sequence_patterns = [
            r'MAX\(.*?amendment sequence.*?\)',
            r'amendment sequence.*?=.*?MAX\(',
            r'MaxSequence.*?=.*?MAX\('
        ]
        validation['has_latest_sequence_logic'] = any(
            re.search(pattern, measure_content, re.IGNORECASE | re.DOTALL) 
            for pattern in sequence_patterns
        )
        
        # Check for proper status filtering
        status_patterns = [
            r'amendment status.*?IN\s*\{.*?"Activated".*?"Superseded"',
            r'"Activated".*?"Superseded"',
            r'\["Activated",\s*"Superseded"\]'
        ]
        validation['has_proper_status_filter'] = any(
            re.search(pattern, measure_content, re.IGNORECASE | re.DOTALL)
            for pattern in status_patterns
        )
        
        # Check for charge integration
        charge_patterns = [
            r'dim_fp_amendmentchargeschedule',
            r'charge code.*?=.*?"rent"',
            r'WITH.*?charges',
            r'AmendmentsWithCharges'
        ]
        validation['has_charge_integration'] = any(
            re.search(pattern, measure_content, re.IGNORECASE | re.DOTALL)
            for pattern in charge_patterns
        )
        
        # Check for business rule exclusions
        business_rule_patterns = [
            r'NOT.*?"Proposal in DM"',
            r'NOT.*?"Termination"',
            r'NOT.*?amendment type.*?IN'
        ]
        validation['has_business_rule_exclusions'] = any(
            re.search(pattern, measure_content, re.IGNORECASE | re.DOTALL)
            for pattern in business_rule_patterns
        )
        
        # Check for deprecated patterns (old logic)
        deprecated_patterns = [
            r'amendment status.*?=.*?"Activated"(?!.*?"Superseded")',
            r'FILTER\(.*?ALL\(.*?\).*?\)',  # Old FILTER(ALL()) patterns
            r'COUNTROWS.*?>.*?0'  # Simple existence checks without proper logic
        ]
        validation['uses_deprecated_patterns'] = any(
            re.search(pattern, measure_content, re.IGNORECASE | re.DOTALL)
            for pattern in deprecated_patterns
        )
        
        # Calculate complexity score
        validation['complexity_score'] = sum([
            validation['has_latest_sequence_logic'] * 30,
            validation['has_proper_status_filter'] * 25,
            validation['has_charge_integration'] * 25,
            validation['has_business_rule_exclusions'] * 20
        ])
        
        return validation
    
    def _generate_recommendations(self, results: Dict) -> List[str]:
        """Generate specific recommendations based on validation results"""
        recommendations = []
        
        issues = results['critical_issues']
        total_rent_measures = results['rent_roll_measures']
        
        # Count issue types
        missing_sequence = len([i for i in issues if 'Missing latest sequence' in i])
        improper_status = len([i for i in issues if 'Improper status' in i])
        missing_charges = len([i for i in issues if 'Missing charge integration' in i])
        
        if missing_sequence > 0:
            recommendations.append(
                f"CRITICAL: {missing_sequence}/{total_rent_measures} rent roll measures missing latest sequence logic. "
                f"Add MAX(amendment sequence) filter per property/tenant combination."
            )
        
        if improper_status > 0:
            recommendations.append(
                f"HIGH: {improper_status}/{total_rent_measures} measures using improper status filtering. "
                f"Include both 'Activated' AND 'Superseded' statuses."
            )
        
        if missing_charges > 0:
            recommendations.append(
                f"HIGH: {missing_charges}/{total_rent_measures} rent measures missing charge integration. "
                f"Only use amendments WITH active rent charges."
            )
        
        # Overall recommendations
        if len(issues) == 0:
            recommendations.append("✅ All rent roll measures pass amendment logic validation.")
        elif len(issues) <= total_rent_measures * 0.1:  # <10% issues
            recommendations.append("⚠️ Minor amendment logic issues found - target 95%+ accuracy achievable.")
        else:
            recommendations.append("❌ Significant amendment logic issues - accuracy below target without fixes.")
        
        return recommendations
    
    def validate_data_consistency(self) -> Dict[str, any]:
        """Validate the underlying amendment data for consistency"""
        print("\n🔍 Validating Amendment Data Consistency...")
        
        # Load amendment data
        amendments_file = os.path.join(self.data_path, 'Fund2_Filtered', 'dim_fp_amendmentsunitspropertytenant_fund2.csv')
        charges_file = os.path.join(self.data_path, 'Fund2_Filtered', 'dim_fp_amendmentchargeschedule_fund2_active.csv')
        
        if not os.path.exists(amendments_file) or not os.path.exists(charges_file):
            return {'error': f'Missing data files: {amendments_file} or {charges_file}'}
        
        amendments_df = pd.read_csv(amendments_file)
        charges_df = pd.read_csv(charges_file)
        
        # Analyze data consistency
        consistency_results = {
            'total_amendments': len(amendments_df),
            'active_amendments': len(amendments_df[amendments_df['amendment status'].isin(['Activated', 'Superseded'])]),
            'amendments_with_charges': 0,
            'unique_property_tenant_combinations': 0,
            'duplicate_latest_amendments': 0,
            'proposal_amendments': 0
        }
        
        # Count amendments with charges
        amendments_with_charges = amendments_df[
            amendments_df['amendment hmy'].isin(charges_df['amendment hmy'])
        ]
        consistency_results['amendments_with_charges'] = len(amendments_with_charges)
        
        # Count unique property/tenant combinations
        property_tenant_groups = amendments_df.groupby(['property hmy', 'tenant hmy'])
        consistency_results['unique_property_tenant_combinations'] = len(property_tenant_groups)
        
        # Check for duplicate latest amendments (critical issue)
        active_amendments = amendments_df[amendments_df['amendment status'].isin(['Activated', 'Superseded'])]
        latest_per_group = active_amendments.loc[active_amendments.groupby(['property hmy', 'tenant hmy'])['amendment sequence'].idxmax()]
        duplicates = active_amendments.groupby(['property hmy', 'tenant hmy', 'amendment sequence']).size()
        consistency_results['duplicate_latest_amendments'] = len(duplicates[duplicates > 1])
        
        # Count proposal amendments (should be excluded)
        consistency_results['proposal_amendments'] = len(
            amendments_df[amendments_df['amendment type'] == 'Proposal in DM']
        )
        
        # Calculate coverage rates
        consistency_results['charge_coverage_rate'] = (
            consistency_results['amendments_with_charges'] / consistency_results['active_amendments'] * 100
        ) if consistency_results['active_amendments'] > 0 else 0
        
        return consistency_results

def main():
    # Configuration
    dax_file = 'Documentation/Core_Guides/Complete_DAX_Library_v3_Fund2_Fixed.dax'
    data_path = 'Data'
    
    validator = AmendmentLogicValidator(dax_file, data_path)
    
    # Run DAX logic validation
    logic_results = validator.validate_all_measures()
    
    # Run data consistency validation
    data_results = validator.validate_data_consistency()
    
    # Print results
    print("\n" + "="*80)
    print("AMENDMENT LOGIC VALIDATION RESULTS")
    print("="*80)
    
    print(f"📊 DAX MEASURES ANALYSIS:")
    print(f"   Total measures: {logic_results['total_measures']}")
    print(f"   Rent roll measures: {logic_results['rent_roll_measures']}")
    print(f"   Critical issues: {len(logic_results['critical_issues'])}")
    
    if logic_results['critical_issues']:
        print(f"\n🚨 CRITICAL ISSUES:")
        for issue in logic_results['critical_issues'][:5]:  # Show first 5
            print(f"   - {issue}")
        if len(logic_results['critical_issues']) > 5:
            print(f"   ... and {len(logic_results['critical_issues']) - 5} more issues")
    
    print(f"\n📈 RECOMMENDATIONS:")
    for rec in logic_results['recommendations']:
        print(f"   • {rec}")
    
    if 'error' not in data_results:
        print(f"\n📋 DATA CONSISTENCY:")
        print(f"   Amendment charge coverage: {data_results['charge_coverage_rate']:.1f}%")
        print(f"   Duplicate latest amendments: {data_results['duplicate_latest_amendments']}")
        print(f"   Proposal amendments (to exclude): {data_results['proposal_amendments']}")
    
    # Calculate overall score
    issues_rate = len(logic_results['critical_issues']) / logic_results['rent_roll_measures']
    overall_score = max(0, (1 - issues_rate) * 100)
    
    print(f"\n🎯 AMENDMENT LOGIC VALIDATION SCORE: {overall_score:.1f}%")
    
    if overall_score >= 95:
        print("✅ Amendment logic validation PASSED - Ready for production")
    elif overall_score >= 85:
        print("⚠️ Amendment logic validation WARNING - Minor fixes needed")
    else:
        print("❌ Amendment logic validation FAILED - Major fixes required")
    
    return overall_score >= 95

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)