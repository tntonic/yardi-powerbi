#!/usr/bin/env python3
"""Debug the structure of actual Yardi rent roll exports"""

import pandas as pd
import numpy as np

def examine_yardi_file(file_path, file_desc):
    """Examine the structure of a Yardi rent roll file"""
    print(f"\n{'='*60}")
    print(f"EXAMINING: {file_desc}")
    print(f"File: {file_path}")
    print(f"{'='*60}")
    
    try:
        # Try reading with different approaches
        print("1. Reading Excel file structure...")
        
        # Get sheet names
        excel_file = pd.ExcelFile(file_path)
        print(f"   Sheet names: {excel_file.sheet_names}")
        
        # Read first sheet
        df = pd.read_excel(file_path, sheet_name=0)
        print(f"   Raw shape: {df.shape}")
        print(f"   Raw columns: {list(df.columns)[:10]}")
        
        # Look for header row by examining first few rows
        print("\n2. First 5 rows content:")
        for i in range(min(5, len(df))):
            row_content = [str(val)[:20] for val in df.iloc[i].values[:5]]
            print(f"   Row {i}: {row_content}")
        
        # Try different skiprows values
        print("\n3. Testing different skip rows:")
        for skip in [0, 1, 2, 3, 4]:
            try:
                test_df = pd.read_excel(file_path, skiprows=skip)
                meaningful_cols = sum(1 for col in test_df.columns 
                                    if not str(col).startswith('Unnamed') 
                                    and not pd.isna(col)
                                    and 'sheet' not in str(col).lower())
                print(f"   Skip {skip}: {test_df.shape}, {meaningful_cols} meaningful columns")
                
                if meaningful_cols > 5:  # Found likely header row
                    print(f"     Columns: {list(test_df.columns)[:8]}")
                    
                    # Look for rent-related columns
                    rent_cols = [col for col in test_df.columns if 'rent' in str(col).lower()]
                    sf_cols = [col for col in test_df.columns if any(term in str(col).lower() for term in ['sf', 'square', 'area'])]
                    prop_cols = [col for col in test_df.columns if 'prop' in str(col).lower()]
                    
                    print(f"     Rent columns: {rent_cols[:3]}")
                    print(f"     SF columns: {sf_cols[:3]}")
                    print(f"     Property columns: {prop_cols[:3]}")
                    
                    # Check for Fund 2 data
                    if prop_cols:
                        fund2_check = test_df[prop_cols[0]].astype(str).str.upper().str.startswith('X').sum()
                        print(f"     Fund 2 properties (X-prefix): {fund2_check}")
                    
                    # Sample data
                    if len(test_df) > 0:
                        print(f"     Sample row: {dict(list(test_df.iloc[0].items())[:3])}")
                    
            except Exception as e:
                print(f"   Skip {skip}: Error - {str(e)[:50]}")
    
    except Exception as e:
        print(f"Error examining file: {e}")

def main():
    """Main examination function"""
    files_to_examine = [
        ('/Users/michaeltang/Documents/GitHub/BI/PBI v1.7/rent rolls/03.31.25.xlsx', 'March 31, 2025 Rent Roll'),
        ('/Users/michaeltang/Documents/GitHub/BI/PBI v1.7/rent rolls/12.31.24.xlsx', 'December 31, 2024 Rent Roll')
    ]
    
    print("YARDI RENT ROLL STRUCTURE ANALYSIS")
    print("=" * 80)
    
    for file_path, file_desc in files_to_examine:
        examine_yardi_file(file_path, file_desc)
    
    print(f"\n{'='*80}")
    print("ANALYSIS COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()