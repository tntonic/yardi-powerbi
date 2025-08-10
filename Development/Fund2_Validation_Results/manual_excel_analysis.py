#!/usr/bin/env python3
"""
Manual analysis of Excel rent roll structure
Deep dive into the actual data layout
"""

import pandas as pd
import numpy as np

def deep_examine_excel(file_path, max_rows=20):
    """Examine Excel file structure in detail"""
    print(f"\nDEEP EXAMINATION: {file_path}")
    print("=" * 60)
    
    # Read raw data without any processing
    raw_df = pd.read_excel(file_path, header=None, sheet_name=0)
    print(f"Raw file dimensions: {raw_df.shape}")
    
    # Look at first 20 rows to understand structure
    print(f"\nFirst {max_rows} rows (showing first 8 columns):")
    print("-" * 80)
    for i in range(min(max_rows, len(raw_df))):
        row_data = []
        for j in range(min(8, len(raw_df.columns))):
            val = raw_df.iloc[i, j]
            if pd.isna(val):
                row_data.append("NaN")
            else:
                row_data.append(str(val)[:15])
        print(f"Row {i:2d}: {row_data}")
    
    # Look for patterns that might indicate data rows
    print(f"\nLooking for data patterns...")
    
    # Search for property codes (X-prefix patterns)
    x_pattern_rows = []
    for i in range(len(raw_df)):
        for j in range(len(raw_df.columns)):
            val = str(raw_df.iloc[i, j]).upper()
            if len(val) >= 5 and val.startswith('X') and any(c.isalnum() for c in val[1:5]):
                x_pattern_rows.append((i, j, val[:10]))
    
    print(f"Found X-pattern values (potential Fund 2 properties):")
    for row, col, val in x_pattern_rows[:10]:  # Show first 10
        print(f"   Row {row}, Col {col}: {val}")
    
    # Look for numeric values that might be rent
    print(f"\nLooking for potential rent values (>1000)...")
    rent_candidates = []
    for i in range(len(raw_df)):
        for j in range(len(raw_df.columns)):
            val = raw_df.iloc[i, j]
            if isinstance(val, (int, float)) and not pd.isna(val) and val > 1000:
                rent_candidates.append((i, j, val))
    
    for row, col, val in rent_candidates[:10]:  # Show first 10
        print(f"   Row {row}, Col {col}: ${val:,.2f}")
    
    # If we found X-patterns, look at those rows in detail
    if x_pattern_rows:
        print(f"\nDetailed view of rows with X-patterns:")
        unique_rows = sorted(set([r[0] for r in x_pattern_rows[:5]]))
        for row_idx in unique_rows:
            print(f"\nRow {row_idx} (all columns):")
            row_values = []
            for col_idx in range(len(raw_df.columns)):
                val = raw_df.iloc[row_idx, col_idx]
                if pd.isna(val):
                    row_values.append("NaN")
                else:
                    row_values.append(str(val)[:12])
            
            # Print in chunks of 6 columns for readability
            for chunk_start in range(0, len(row_values), 6):
                chunk = row_values[chunk_start:chunk_start+6]
                print(f"   Cols {chunk_start}-{chunk_start+len(chunk)-1}: {chunk}")

def main():
    """Main analysis function"""
    files = [
        '/Users/michaeltang/Documents/GitHub/BI/PBI v1.7/rent rolls/03.31.25.xlsx',
        '/Users/michaeltang/Documents/GitHub/BI/PBI v1.7/rent rolls/12.31.24.xlsx'
    ]
    
    print("MANUAL EXCEL STRUCTURE ANALYSIS")
    print("=" * 80)
    
    for file_path in files:
        try:
            deep_examine_excel(file_path)
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
    
    print("\nAnalysis complete!")

if __name__ == "__main__":
    main()