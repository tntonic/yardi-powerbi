#!/usr/bin/env python3
"""
DAX v5.1 Syntax and Pattern Validator
Validates harmonized v5.1 DAX measure files
"""

import re
import os
import glob
from pathlib import Path

def validate_dax_file(filepath):
    """Validate individual DAX file for v5.1 compliance"""
    print(f'\n📁 Validating: {os.path.basename(filepath)}')
    
    issues = []
    warnings = []
    patterns_found = {
        'version_5.1': False,
        'date_pattern_correct': True,
        'amendment_status_correct': True,
        'helper_measures': False
    }
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return {'error': str(e)}
    
    # Check version 5.1
    if 'VERSION 5.1' in content:
        patterns_found['version_5.1'] = True
    else:
        issues.append('❌ File not updated to VERSION 5.1')
    
    # Check for old TODAY() pattern
    if 'TODAY()' in content and 'dim_lastclosedperiod' not in content[:1000]:
        patterns_found['date_pattern_correct'] = False
        issues.append('❌ Still using TODAY() instead of dim_lastclosedperiod pattern')
    
    # Check for correct amendment status filtering
    if '"Activated"' in content and '"Superseded"' not in content:
        lines_with_activated = [i+1 for i, line in enumerate(content.split('\n')) 
                                if '"Activated"' in line and 'IN {' not in line]
        if lines_with_activated:
            patterns_found['amendment_status_correct'] = False
            warnings.append(f'⚠️  Possible single status filter at lines: {lines_with_activated[:3]}')
    
    # Check for helper measures
    if '_BaseActiveAmendments' in content or '_LatestAmendmentsWithCharges' in content:
        patterns_found['helper_measures'] = True
    
    # Count measures
    measure_pattern = r'^([A-Za-z_][A-Za-z0-9\s%()._-]+?)\s*=\s*$'
    measures = re.findall(measure_pattern, content, re.MULTILINE)
    
    # Check parentheses balance
    paren_balance = content.count('(') - content.count(')')
    if paren_balance != 0:
        issues.append(f'❌ Unbalanced parentheses (diff: {paren_balance})')
    
    # Check for DIVIDE safety
    unsafe_divisions = len(re.findall(r'[^/]/[^/]', content)) - content.count('DIVIDE(')
    if unsafe_divisions > 10:  # Allow some URL/comments
        warnings.append(f'⚠️  Consider using DIVIDE() for safety ({unsafe_divisions} potential unsafe divisions)')
    
    return {
        'filename': os.path.basename(filepath),
        'measures_count': len(measures),
        'issues': issues,
        'warnings': warnings,
        'patterns': patterns_found,
        'status': '✅ PASS' if not issues else '❌ FAIL'
    }

def main():
    """Main validation routine for all v5.1 DAX files"""
    print('='*80)
    print('🔍 DAX v5.1 HARMONIZATION VALIDATOR')
    print('='*80)
    
    # Path to DAX files
    dax_path = '/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Claude_AI_Reference/DAX_Measures'
    
    # Get all v5.1 DAX files
    dax_files = glob.glob(f'{dax_path}/*.dax')
    
    if not dax_files:
        print('❌ No DAX files found!')
        return
    
    print(f'📊 Found {len(dax_files)} DAX files to validate\n')
    
    all_results = []
    total_measures = 0
    total_issues = 0
    total_warnings = 0
    
    for filepath in sorted(dax_files):
        result = validate_dax_file(filepath)
        all_results.append(result)
        
        if 'error' not in result:
            total_measures += result['measures_count']
            total_issues += len(result['issues'])
            total_warnings += len(result['warnings'])
            
            # Print file results
            print(f"  Status: {result['status']}")
            print(f"  Measures: {result['measures_count']}")
            
            if result['issues']:
                print('  Issues:')
                for issue in result['issues']:
                    print(f'    {issue}')
            
            if result['warnings']:
                print('  Warnings:')
                for warning in result['warnings'][:2]:  # Limit warnings shown
                    print(f'    {warning}')
    
    # Print summary
    print('\n' + '='*80)
    print('📈 VALIDATION SUMMARY')
    print('='*80)
    print(f'Total Files Validated: {len(dax_files)}')
    print(f'Total Measures Found: {total_measures}')
    print(f'Total Issues: {total_issues}')
    print(f'Total Warnings: {total_warnings}')
    
    # Check v5.1 compliance
    v51_compliant = sum(1 for r in all_results if r.get('patterns', {}).get('version_5.1', False))
    print(f'\n📌 v5.1 Compliance: {v51_compliant}/{len(dax_files)} files')
    
    # Overall status
    if total_issues == 0:
        print('\n✅ ALL VALIDATIONS PASSED - Ready for testing!')
    else:
        print(f'\n❌ {total_issues} ISSUES FOUND - Review needed')
    
    # Pattern compliance report
    print('\n📋 PATTERN COMPLIANCE:')
    date_compliant = sum(1 for r in all_results if r.get('patterns', {}).get('date_pattern_correct', False))
    status_compliant = sum(1 for r in all_results if r.get('patterns', {}).get('amendment_status_correct', False))
    helper_usage = sum(1 for r in all_results if r.get('patterns', {}).get('helper_measures', False))
    
    print(f'  Date Handling (dim_lastclosedperiod): {date_compliant}/{len(dax_files)}')
    print(f'  Amendment Status Filtering: {status_compliant}/{len(dax_files)}')
    print(f'  Helper Measure Usage: {helper_usage}/{len(dax_files)}')

if __name__ == '__main__':
    main()