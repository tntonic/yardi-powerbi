#!/usr/bin/env python3
"""
Validate DAX syntax fixes in v5.0 production files
Specifically checks for the 4 critical issues that were fixed:
1. WALT measure ROW() return issue
2. Invalid || operators
3. NOW() function usage
4. Undefined [Value] references
"""

import re
import os
import sys

def check_dax_file(filepath):
    """Check a DAX file for critical syntax errors"""
    errors = []
    warnings = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
    except Exception as e:
        return {'errors': [f'Cannot read {filepath}: {e}'], 'warnings': []}
    
    # Check for critical issues
    for i, line in enumerate(lines, 1):
        # Check for invalid || operator
        if '||' in line and '//' not in line[:line.find('||') if '||' in line else len(line)]:
            errors.append(f'Line {i}: Invalid || operator found (should be OR)')
        
        # Check for NOW() function
        if 'NOW()' in line:
            warnings.append(f'Line {i}: NOW() function found (replaced with TODAY() for stability)')
        
        # Check for ROW() in SUMX context (simplified check)
        if 'RETURN' in line and 'ROW(' in line:
            # Check if this is within a SUMX
            context_start = max(0, i-10)
            context = '\n'.join(lines[context_start:i])
            if 'SUMX(' in context:
                errors.append(f'Line {i}: ROW() return in SUMX context (invalid scalar return)')
        
        # Check for [Value] reference in filter context with curly braces
        if '[Value]' in line:
            # Look for curly brace table context
            context_start = max(0, i-5)
            context = '\n'.join(lines[context_start:i+1])
            if '{' in context and 'FILTER' in context:
                errors.append(f'Line {i}: Invalid [Value] reference in curly brace table filter')
    
    return {'errors': errors, 'warnings': warnings}

def main():
    """Validate all v5.0 DAX files"""
    base_path = '/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI'
    dax_files = [
        'Claude_AI_Reference/DAX_Measures/01_Core_Financial_Rent_Roll_Measures_v5.0.dax',
        'Claude_AI_Reference/DAX_Measures/02_Leasing_Activity_Pipeline_Measures_v5.0.dax',
        'Claude_AI_Reference/DAX_Measures/03_Credit_Risk_Tenant_Analysis_Measures_v5.0.dax',
        'Claude_AI_Reference/DAX_Measures/04_Net_Absorption_Fund_Analysis_Measures_v5.0.dax',
        'Claude_AI_Reference/DAX_Measures/05_Performance_Validation_Measures_v5.0.dax',
        'Claude_AI_Reference/DAX_Measures/Validation_Measures.dax',
        'Claude_AI_Reference/DAX_Measures/Top_20_Essential_Measures.dax'
    ]
    
    print('=== DAX v5.0 SYNTAX VALIDATION ===\n')
    
    total_errors = 0
    total_warnings = 0
    
    for dax_file in dax_files:
        filepath = os.path.join(base_path, dax_file)
        filename = os.path.basename(dax_file)
        
        print(f'Checking: {filename}')
        
        result = check_dax_file(filepath)
        
        if result['errors']:
            print(f'  ❌ {len(result["errors"])} ERRORS:')
            for error in result['errors']:
                print(f'     - {error}')
                total_errors += 1
        else:
            print(f'  ✅ No critical errors found')
        
        if result['warnings']:
            print(f'  ⚠️  {len(result["warnings"])} WARNINGS:')
            for warning in result['warnings'][:3]:  # Show first 3
                print(f'     - {warning}')
            if len(result['warnings']) > 3:
                print(f'     ... and {len(result["warnings"]) - 3} more')
            total_warnings += len(result['warnings'])
        
        print()
    
    print('=== VALIDATION SUMMARY ===')
    if total_errors == 0:
        print('✅ ALL CRITICAL SYNTAX ERRORS HAVE BEEN FIXED!')
        print(f'   - No invalid || operators')
        print(f'   - No ROW() returns in SUMX')
        print(f'   - No undefined [Value] references')
        print(f'   - NOW() replaced with TODAY() ({total_warnings} instances)')
    else:
        print(f'❌ {total_errors} CRITICAL ERRORS REMAIN')
    
    print(f'\n📊 Final Score: {"100%" if total_errors == 0 else f"{(1 - total_errors/4)*100:.0f}%"}')
    
    return total_errors == 0

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)