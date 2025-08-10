#!/usr/bin/env python3
"""
Find location of unbalanced parentheses in DAX file
"""

def find_unbalanced_parens(filepath):
    """Find the line where parentheses become unbalanced"""
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    open_count = 0
    close_count = 0
    problem_lines = []
    
    for i, line in enumerate(lines, 1):
        line_open = line.count('(')
        line_close = line.count(')')
        open_count += line_open
        close_count += line_close
        
        # Check if unbalanced after this line
        if open_count < close_count:
            problem_lines.append(f"Line {i}: Too many closing parens (open:{open_count}, close:{close_count})")
            print(f"❌ Line {i}: '{line.strip()[:60]}...'")
            print(f"   Running total: Open={open_count}, Close={close_count}")
    
    print(f"\n📊 Final counts: Open={open_count}, Close={close_count}, Diff={open_count-close_count}")
    
    # Find measures with issues
    current_measure = None
    measure_balance = {}
    
    for i, line in enumerate(lines, 1):
        if '=' in line and not line.strip().startswith('//'):
            if current_measure and current_measure in measure_balance:
                if measure_balance[current_measure] != 0:
                    print(f"⚠️  Measure '{current_measure}' has balance: {measure_balance[current_measure]}")
            current_measure = line.split('=')[0].strip()
            measure_balance[current_measure] = 0
        
        if current_measure:
            measure_balance[current_measure] += line.count('(') - line.count(')')
    
    # Check last measure
    if current_measure and measure_balance[current_measure] != 0:
        print(f"⚠️  Measure '{current_measure}' has balance: {measure_balance[current_measure]}")

# Run it
filepath = '/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Claude_AI_Reference/DAX_Measures/03_Credit_Risk_Tenant_Analysis_Measures_v5.1.dax'
find_unbalanced_parens(filepath)