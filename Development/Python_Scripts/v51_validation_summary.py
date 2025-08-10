#!/usr/bin/env python3
"""
v5.1 DAX Harmonization Validation Summary
Comprehensive validation of all v5.1 updates
"""

import os
import re
import glob
from datetime import datetime

def validate_v51_compliance():
    """Validate v5.1 compliance across all DAX files"""
    
    dax_path = '/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Claude_AI_Reference/DAX_Measures'
    dax_files = glob.glob(f'{dax_path}/*.dax')
    
    results = {
        'total_files': len(dax_files),
        'v51_compliant': 0,
        'date_pattern_compliant': 0,
        'measures_total': 0,
        'files': []
    }
    
    for filepath in dax_files:
        filename = os.path.basename(filepath)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check v5.1 version
        is_v51 = 'VERSION 5.1' in content
        
        # Check date pattern (dim_lastclosedperiod)
        uses_correct_date = 'dim_lastclosedperiod[last closed period]' in content
        
        # Count measures
        measure_pattern = r'^([A-Za-z_][A-Za-z0-9\s%()._-]+?)\s*=\s*$'
        measures = re.findall(measure_pattern, content, re.MULTILINE)
        measure_count = len([m for m in measures if not m.startswith('//')])
        
        # Check for TODAY() usage
        has_today = 'TODAY()' in content
        
        # Check parentheses balance
        paren_balance = content.count('(') - content.count(')')
        
        file_result = {
            'filename': filename,
            'v51': is_v51,
            'correct_date': uses_correct_date,
            'measures': measure_count,
            'has_today': has_today,
            'balanced_parens': paren_balance == 0
        }
        
        results['files'].append(file_result)
        
        if is_v51:
            results['v51_compliant'] += 1
        if uses_correct_date:
            results['date_pattern_compliant'] += 1
        results['measures_total'] += measure_count
    
    return results

def print_validation_report(results):
    """Print formatted validation report"""
    
    print('='*80)
    print('📊 v5.1 DAX HARMONIZATION VALIDATION REPORT')
    print(f'📅 Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('='*80)
    
    # Overall compliance
    print('\n✅ OVERALL COMPLIANCE:')
    print(f'  • v5.1 Version: {results["v51_compliant"]}/{results["total_files"]} files')
    print(f'  • Date Pattern: {results["date_pattern_compliant"]}/{results["total_files"]} files')
    print(f'  • Total Measures: {results["measures_total"]}')
    
    # File-by-file report
    print('\n📁 FILE-BY-FILE STATUS:')
    for file_info in results['files']:
        status = '✅' if file_info['v51'] and file_info['correct_date'] and file_info['balanced_parens'] else '⚠️'
        print(f'\n  {status} {file_info["filename"]}')
        print(f'     v5.1: {"✓" if file_info["v51"] else "✗"}')
        print(f'     Date Pattern: {"✓" if file_info["correct_date"] else "✗"}')
        print(f'     Balanced Parens: {"✓" if file_info["balanced_parens"] else "✗"}')
        print(f'     Measures: {file_info["measures"]}')
        if file_info['has_today']:
            print(f'     ⚠️  Still uses TODAY() function')
    
    # Issues summary
    issues = []
    for file_info in results['files']:
        if not file_info['v51']:
            issues.append(f'{file_info["filename"]}: Not v5.1')
        if not file_info['balanced_parens']:
            issues.append(f'{file_info["filename"]}: Unbalanced parentheses')
        if file_info['has_today']:
            issues.append(f'{file_info["filename"]}: Uses TODAY()')
    
    if issues:
        print('\n⚠️  ISSUES FOUND:')
        for issue in issues:
            print(f'  • {issue}')
    else:
        print('\n✅ NO ISSUES FOUND - All files compliant!')
    
    # Success metrics
    print('\n📈 SUCCESS METRICS:')
    v51_pct = (results['v51_compliant'] / results['total_files']) * 100
    date_pct = (results['date_pattern_compliant'] / results['total_files']) * 100
    
    print(f'  • v5.1 Compliance: {v51_pct:.1f}%')
    print(f'  • Date Pattern Compliance: {date_pct:.1f}%')
    
    # Final status
    print('\n' + '='*80)
    if v51_pct == 100 and date_pct == 100:
        print('🎉 HARMONIZATION COMPLETE - All DAX measures updated to v5.1!')
    else:
        print('🔧 HARMONIZATION IN PROGRESS - Some files need attention')
    print('='*80)

def main():
    """Main validation routine"""
    results = validate_v51_compliance()
    print_validation_report(results)
    
    # Return exit code for CI/CD
    if results['v51_compliant'] == results['total_files']:
        return 0  # Success
    else:
        return 1  # Needs attention

if __name__ == '__main__':
    exit(main())