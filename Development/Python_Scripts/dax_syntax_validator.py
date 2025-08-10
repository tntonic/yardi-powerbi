#!/usr/bin/env python3
import re
import sys

def validate_dax_syntax(filepath):
    print(f'Validating DAX syntax in: {filepath}')
    errors = []
    warnings = []
    measures = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f'Error reading file: {e}')
        return {'measures': 0, 'errors': [f'File read error: {e}'], 'warnings': [], 'measure_names': []}
    
    # Extract all measures
    measure_pattern = r'^([A-Za-z][A-Za-z0-9\s%().-]+?)\s*=\s*$'
    lines = content.split('\n')
    current_measure = None
    measure_content = []
    
    for i, line in enumerate(lines, 1):
        line_stripped = line.strip()
        
        # Skip comments and empty lines
        if not line_stripped or line_stripped.startswith('//'):
            continue
        
        # Check for measure definitions
        if re.match(measure_pattern, line_stripped):
            if current_measure:
                measures.append({
                    'name': current_measure,
                    'content': '\n'.join(measure_content),
                    'line': i - len(measure_content)
                })
            current_measure = line_stripped.replace(' =', '').strip()
            measure_content = []
            continue
        
        if current_measure and line_stripped:
            measure_content.append(line_stripped)
    
    # Add last measure
    if current_measure:
        measures.append({
            'name': current_measure,
            'content': '\n'.join(measure_content),
            'line': len(lines) - len(measure_content)
        })
    
    print(f'Found {len(measures)} DAX measures')
    
    # Validate syntax patterns
    for measure in measures:
        name = measure['name']
        content = measure['content']
        line_num = measure['line']
        
        # Check for balanced parentheses
        paren_count = content.count('(') - content.count(')')
        if paren_count != 0:
            errors.append(f'Line {line_num}: {name} - Unbalanced parentheses (diff: {paren_count})')
        
        # Check for proper DIVIDE usage
        if '/' in content and 'DIVIDE(' not in content and '//' not in content:
            warnings.append(f'Line {line_num}: {name} - Consider using DIVIDE() instead of / for safety')
        
        # Check for common DAX function usage
        if 'SUM(' in content and 'SUMX(' not in content:
            # This is actually good - SUM is simpler than SUMX when appropriate
            pass
        
        # Check for variable naming conventions
        var_matches = re.findall(r'VAR\s+([A-Za-z][A-Za-z0-9]*)', content)
        for var_name in var_matches:
            if not var_name[0].isupper():
                warnings.append(f'Line {line_num}: {name} - Variable "{var_name}" should start with capital letter')
    
    return {
        'measures': len(measures),
        'errors': errors,
        'warnings': warnings,
        'measure_names': [m['name'] for m in measures]
    }

def main():
    # Validate the main DAX file
    dax_file = 'Documentation/Core_Guides/Complete_DAX_Library_v3_Fund2_Fixed.dax'
    result = validate_dax_syntax(dax_file)
    
    print(f'\n=== DAX SYNTAX VALIDATION RESULTS ===')
    print(f'Total Measures Found: {result["measures"]}')
    print(f'Syntax Errors: {len(result["errors"])}')
    print(f'Warnings: {len(result["warnings"])}')
    
    if result['errors']:
        print('\n🚨 SYNTAX ERRORS:')
        for error in result['errors']:
            print(f'  - {error}')
    
    if result['warnings']:
        print('\n⚠️  WARNINGS:')
        for warning in result['warnings'][:5]:  # Show first 5 warnings
            print(f'  - {warning}')
        if len(result['warnings']) > 5:
            print(f'  ... and {len(result["warnings"]) - 5} more warnings')
    
    print('\n📊 SAMPLE MEASURES:')
    for measure in result['measure_names'][:10]:
        print(f'  ✓ {measure}')
    if len(result['measure_names']) > 10:
        print(f'  ... and {len(result["measure_names"]) - 10} more measures')
    
    accuracy = (result['measures'] - len(result['errors'])) / result['measures'] * 100 if result['measures'] > 0 else 0
    print(f'\n🎯 VALIDATION SCORE: {accuracy:.1f}%')
    
    # Return success status
    return len(result['errors']) == 0

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)