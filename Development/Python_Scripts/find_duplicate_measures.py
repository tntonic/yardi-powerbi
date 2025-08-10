#!/usr/bin/env python3
"""
Find duplicate DAX measures across all DAX files
Identifies measures that appear in multiple files
"""

import re
import os
import glob
from collections import defaultdict

def extract_measures_from_file(filepath):
    """Extract all measure names from a DAX file"""
    measures = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f'Error reading {filepath}: {e}')
        return measures
    
    # Pattern to match measure definitions
    measure_pattern = r'^([A-Za-z_][A-Za-z0-9\s%()._-]+?)\s*=\s*$'
    
    for match in re.finditer(measure_pattern, content, re.MULTILINE):
        measure_name = match.group(1).strip()
        # Skip helper measures (starting with _)
        if not measure_name.startswith('//'):
            measures.append(measure_name)
    
    return measures

def find_duplicates():
    """Find duplicate measures across all DAX files"""
    
    dax_path = '/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Claude_AI_Reference/DAX_Measures'
    dax_files = glob.glob(f'{dax_path}/*.dax')
    
    # Dictionary to track which files contain each measure
    measure_locations = defaultdict(list)
    
    # Extract measures from each file
    for filepath in dax_files:
        filename = os.path.basename(filepath)
        measures = extract_measures_from_file(filepath)
        
        for measure in measures:
            measure_locations[measure].append(filename)
    
    # Find duplicates
    duplicates = {
        measure: files 
        for measure, files in measure_locations.items() 
        if len(files) > 1
    }
    
    return duplicates, measure_locations

def main():
    """Main analysis routine"""
    print('='*80)
    print('🔍 DAX MEASURE DUPLICATION ANALYSIS')
    print('='*80)
    
    duplicates, all_measures = find_duplicates()
    
    if duplicates:
        print(f'\n⚠️  Found {len(duplicates)} duplicate measures:\n')
        
        # Group duplicates by file pairs
        file_pairs = defaultdict(list)
        for measure, files in sorted(duplicates.items()):
            file_pair = ' <-> '.join(sorted(files))
            file_pairs[file_pair].append(measure)
        
        # Print duplicates by file pairs
        for file_pair, measures in sorted(file_pairs.items()):
            print(f'\n📁 {file_pair}')
            print(f'   Duplicate measures ({len(measures)}):')
            for measure in sorted(measures):
                print(f'     • {measure}')
        
        # Special focus on Top 20 duplicates
        top20_file = 'Top_20_Essential_Measures.dax'
        top20_duplicates = {
            measure: files 
            for measure, files in duplicates.items() 
            if top20_file in files
        }
        
        if top20_duplicates:
            print('\n' + '='*80)
            print('📌 TOP 20 ESSENTIAL MEASURES DUPLICATION')
            print('='*80)
            print(f'Found {len(top20_duplicates)} measures in Top 20 that exist elsewhere:\n')
            
            for measure in sorted(top20_duplicates.keys()):
                other_files = [f for f in duplicates[measure] if f != top20_file]
                print(f'  • {measure}')
                for file in other_files:
                    print(f'      → Also in: {file}')
            
            print('\n💡 Recommendation: Top 20 file should reference the main files')
            print('   instead of duplicating measure definitions.')
    else:
        print('\n✅ No duplicate measures found across files!')
    
    # Summary statistics
    print('\n' + '='*80)
    print('📊 SUMMARY STATISTICS')
    print('='*80)
    
    total_unique = len(all_measures)
    total_with_duplicates = sum(len(files) for files in all_measures.values())
    
    print(f'Total unique measures: {total_unique}')
    print(f'Total measure definitions (including duplicates): {total_with_duplicates}')
    print(f'Duplication factor: {total_with_duplicates / total_unique:.2f}x')
    
    # File statistics
    print('\n📈 Measures per file:')
    file_counts = defaultdict(int)
    for measure, files in all_measures.items():
        for file in files:
            file_counts[file] += 1
    
    for file, count in sorted(file_counts.items()):
        print(f'  • {file}: {count} measures')

if __name__ == '__main__':
    main()