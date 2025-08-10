#!/usr/bin/env python3
"""
Financial Reconciliation Validator
==================================

Validates revenue sign conventions and NOI calculations against business rules:
1. Revenue accounts (4xxxx) stored as negative, multiply by -1 for display
2. Expense accounts (5xxxx) stored as positive, display as positive
3. NOI = Revenue - Operating Expenses
4. Account filtering properly implemented
5. Book filtering (Accrual, FPR) correctly applied
"""

import pandas as pd
import os
import re
from typing import Dict, List, Tuple

class FinancialReconciliationValidator:
    def __init__(self, dax_file_path: str, data_path: str):
        self.dax_file_path = dax_file_path
        self.data_path = data_path
        self.results = {}
    
    def validate_financial_measures(self) -> Dict[str, any]:
        """Validate financial measure logic against business rules"""
        print("💰 Validating Financial Measure Logic...")
        
        with open(self.dax_file_path, 'r', encoding='utf-8') as f:
            dax_content = f.read()
        
        # Extract financial measures
        financial_measures = {
            'Total Revenue': self._extract_measure(dax_content, 'Total Revenue'),
            'Operating Expenses': self._extract_measure(dax_content, 'Operating Expenses'), 
            'NOI (Net Operating Income)': self._extract_measure(dax_content, 'NOI (Net Operating Income)'),
            'FPR NOI': self._extract_measure(dax_content, 'FPR NOI'),
            'NOI Margin %': self._extract_measure(dax_content, 'NOI Margin %')
        }
        
        validation_results = {}
        
        # Validate each financial measure
        for measure_name, measure_content in financial_measures.items():
            if measure_content:
                validation_results[measure_name] = self._validate_financial_measure(measure_name, measure_content)
        
        return validation_results
    
    def _extract_measure(self, content: str, measure_name: str) -> str:
        """Extract a specific measure from DAX content"""
        pattern = rf'^{re.escape(measure_name)}\s*=\s*\n(.*?)(?=\n^[A-Za-z]|\Z)'
        match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
        return match.group(1).strip() if match else ""
    
    def _validate_financial_measure(self, measure_name: str, measure_content: str) -> Dict[str, any]:
        """Validate a single financial measure"""
        validation = {
            'measure_name': measure_name,
            'has_proper_sign_convention': False,
            'has_correct_account_filtering': False,
            'has_correct_book_filtering': False,
            'uses_safe_division': False,
            'business_rule_compliance': False,
            'issues': []
        }
        
        # Check revenue sign convention (multiply by -1)
        if measure_name == 'Total Revenue':
            validation['has_proper_sign_convention'] = '*' in measure_content and '-1' in measure_content
            if not validation['has_proper_sign_convention']:
                validation['issues'].append("Revenue should multiply by -1 (stored as negative)")
        
        # Check expense sign convention (use ABS or positive handling)
        elif measure_name == 'Operating Expenses':
            validation['has_proper_sign_convention'] = 'ABS(' in measure_content or 'amount]' in measure_content
            if not validation['has_proper_sign_convention']:
                validation['issues'].append("Expenses should use ABS() or proper positive handling")
        
        # Check account filtering
        if 'dim_account[account code]' in measure_content:
            if measure_name == 'Total Revenue':
                validation['has_correct_account_filtering'] = (
                    '40000000' in measure_content and '50000000' in measure_content
                )
            elif measure_name == 'Operating Expenses':
                validation['has_correct_account_filtering'] = (
                    '50000000' in measure_content and '60000000' in measure_content
                )
            else:
                validation['has_correct_account_filtering'] = True
        else:
            validation['has_correct_account_filtering'] = measure_name in ['NOI (Net Operating Income)', 'NOI Margin %']
        
        # Check book filtering
        if 'FPR' in measure_name:
            validation['has_correct_book_filtering'] = 'book_id' in measure_content and '46' in measure_content
        else:
            validation['has_correct_book_filtering'] = 'Accrual' in measure_content or measure_name in ['NOI (Net Operating Income)', 'NOI Margin %']
        
        # Check safe division
        if '%' in measure_name or 'Margin' in measure_name:
            validation['uses_safe_division'] = 'DIVIDE(' in measure_content
            if not validation['uses_safe_division']:
                validation['issues'].append("Should use DIVIDE() function for safe division")
        else:
            validation['uses_safe_division'] = True
        
        # Business rule compliance score
        validation['business_rule_compliance'] = all([
            validation['has_proper_sign_convention'],
            validation['has_correct_account_filtering'],
            validation['has_correct_book_filtering'],
            validation['uses_safe_division']
        ])
        
        return validation
    
    def validate_data_consistency(self) -> Dict[str, any]:
        """Validate financial data consistency"""
        print("💰 Validating Financial Data Consistency...")
        
        fact_total_file = os.path.join(self.data_path, 'Yardi_Tables', 'fact_total.csv')
        dim_account_file = os.path.join(self.data_path, 'Yardi_Tables', 'dim_account.csv')
        
        if not os.path.exists(fact_total_file) or not os.path.exists(dim_account_file):
            return {'error': f'Missing files: {fact_total_file} or {dim_account_file}'}
        
        fact_df = pd.read_csv(fact_total_file)
        account_df = pd.read_csv(dim_account_file)
        
        # Merge with account data
        merged_df = fact_df.merge(account_df, on='account id', how='left')
        
        # Analyze revenue sign convention
        revenue_accounts = merged_df[
            (merged_df['account code'] >= 40000000) & 
            (merged_df['account code'] < 50000000)
        ]
        
        expense_accounts = merged_df[
            (merged_df['account code'] >= 50000000) & 
            (merged_df['account code'] < 60000000)
        ]
        
        results = {
            'total_transactions': len(fact_df),
            'revenue_transactions': len(revenue_accounts),
            'expense_transactions': len(expense_accounts),
            'revenue_negative_pct': 0,
            'expense_positive_pct': 0,
            'orphaned_accounts': 0
        }
        
        if len(revenue_accounts) > 0:
            results['revenue_negative_pct'] = (revenue_accounts['amount'] < 0).mean() * 100
        
        if len(expense_accounts) > 0:
            results['expense_positive_pct'] = (expense_accounts['amount'] > 0).mean() * 100
        
        # Check for orphaned accounts
        results['orphaned_accounts'] = fact_df['account id'].isin(account_df['account id']).sum()
        results['orphaned_account_rate'] = (1 - results['orphaned_accounts'] / len(fact_df)) * 100
        
        return results

def main():
    # Configuration
    dax_file = 'Documentation/Core_Guides/Complete_DAX_Library_v3_Fund2_Fixed.dax'
    data_path = 'Data'
    
    validator = FinancialReconciliationValidator(dax_file, data_path)
    
    # Run validations
    measure_results = validator.validate_financial_measures()
    data_results = validator.validate_data_consistency()
    
    # Print results
    print("\n" + "="*80)
    print("FINANCIAL RECONCILIATION VALIDATION RESULTS")
    print("="*80)
    
    total_measures = len(measure_results)
    compliant_measures = len([r for r in measure_results.values() if r['business_rule_compliance']])
    
    print(f"📊 FINANCIAL MEASURES ANALYSIS:")
    print(f"   Total financial measures: {total_measures}")
    print(f"   Business rule compliant: {compliant_measures}")
    print(f"   Compliance rate: {(compliant_measures/total_measures*100):.1f}%" if total_measures > 0 else "   No measures found")
    
    # Show detailed results
    print(f"\n📋 MEASURE VALIDATION DETAILS:")
    for measure_name, validation in measure_results.items():
        status = "✅" if validation['business_rule_compliance'] else "❌"
        print(f"   {status} {measure_name}")
        if validation['issues']:
            for issue in validation['issues']:
                print(f"      - {issue}")
    
    if 'error' not in data_results:
        print(f"\n📈 DATA CONSISTENCY:")
        print(f"   Revenue sign convention: {data_results['revenue_negative_pct']:.1f}% negative (target: 95%+)")
        print(f"   Expense sign convention: {data_results['expense_positive_pct']:.1f}% positive (target: 95%+)")
        print(f"   Account relationship integrity: {100-data_results['orphaned_account_rate']:.1f}%")
    
    # Calculate overall score
    if total_measures > 0:
        overall_score = (compliant_measures / total_measures) * 100
        
        # Adjust score based on data quality
        if 'error' not in data_results:
            data_quality_bonus = 0
            if data_results['revenue_negative_pct'] >= 90:
                data_quality_bonus += 10
            if data_results['expense_positive_pct'] >= 90:
                data_quality_bonus += 10
            if data_results['orphaned_account_rate'] < 5:
                data_quality_bonus += 10
            
            overall_score = min(100, overall_score + data_quality_bonus / 3)
    else:
        overall_score = 0
    
    print(f"\n🎯 FINANCIAL RECONCILIATION SCORE: {overall_score:.1f}%")
    
    if overall_score >= 98:
        print("✅ Financial reconciliation validation PASSED - Meets 98%+ target")
    elif overall_score >= 90:
        print("⚠️ Financial reconciliation validation WARNING - Minor improvements needed")
    else:
        print("❌ Financial reconciliation validation FAILED - Major fixes required")
    
    return overall_score >= 98

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)