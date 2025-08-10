#!/usr/bin/env python3
"""
Examine Yardi Export Structure
Analyze the structure of the rent roll Excel files to understand column mapping
"""

import pandas as pd
import numpy as np
import os

def examine_excel_file(file_path, max_sheets=3, max_skip_rows=5):
    """Examine Excel file structure in detail"""
    print(f"\n{'='*80}")
    print(f"EXAMINING FILE: {os.path.basename(file_path)}")
    print(f"{'='*80}")
    
    try:
        # Get sheet names
        xl = pd.ExcelFile(file_path)
        print(f"Sheet names: {xl.sheet_names}")
        
        for sheet_idx, sheet_name in enumerate(xl.sheet_names[:max_sheets]):
            print(f"\n--- SHEET: {sheet_name} ---")
            
            for skip_rows in range(max_skip_rows):
                try:
                    df = pd.read_excel(file_path, sheet_name=sheet_name, skiprows=skip_rows, nrows=10)
                    
                    print(f"\nSkip rows {skip_rows}:")
                    print(f"  Shape: {df.shape}")
                    print(f"  Columns: {list(df.columns)}")
                    
                    # Show first few rows
                    if len(df) > 0:
                        print(f"  Sample data:")
                        for idx, row in df.head(3).iterrows():
                            print(f"    Row {idx}: {dict(row)}")
                    
                    # Look for property codes
                    property_indicators = []
                    for col in df.columns:
                        col_str = str(col).lower()
                        if any(term in col_str for term in ['property', 'building', 'asset', 'code']):
                            property_indicators.append(col)
                    
                    if property_indicators:
                        print(f"  Potential property columns: {property_indicators}")
                        
                        # Check for Fund 2 properties (codes starting with 'x')
                        for col in property_indicators:
                            if col in df.columns:
                                sample_values = df[col].dropna().astype(str).head(10).tolist()
                                fund2_count = sum(1 for val in sample_values if val.lower().startswith('x'))
                                print(f"    {col} sample: {sample_values}")
                                print(f"    Fund 2 indicators (starting with 'x'): {fund2_count}")
                    
                    # Look for tenant information
                    tenant_indicators = []
                    for col in df.columns:
                        col_str = str(col).lower()
                        if any(term in col_str for term in ['tenant', 'lessee', 'company', 'client']):
                            tenant_indicators.append(col)
                    
                    if tenant_indicators:
                        print(f"  Potential tenant columns: {tenant_indicators}")
                    
                    # Look for financial data
                    financial_indicators = []
                    for col in df.columns:
                        col_str = str(col).lower()
                        if any(term in col_str for term in ['rent', 'monthly', 'annual', '$', 'amount']):
                            financial_indicators.append(col)
                    
                    if financial_indicators:
                        print(f"  Potential financial columns: {financial_indicators}")
                    
                    # Count non-null data in each column
                    non_null_counts = df.count()
                    meaningful_cols = non_null_counts[non_null_counts > 0]
                    if len(meaningful_cols) > 0:
                        print(f"  Non-null data counts: {meaningful_cols.to_dict()}")
                    
                    print("-" * 60)
                    
                except Exception as e:
                    print(f"  Skip rows {skip_rows}: Error - {str(e)}")
                    continue
            
            if sheet_idx >= max_sheets - 1:
                break
                
    except Exception as e:
        print(f"Error examining {file_path}: {str(e)}")

def main():
    """Examine both target files"""
    base_path = "/Users/michaeltang/Documents/GitHub/BI/PBI v1.7"
    
    files_to_examine = [
        "rent rolls/03.31.25.xlsx",
        "rent rolls/12.31.24.xlsx"
    ]
    
    for file_path in files_to_examine:
        full_path = os.path.join(base_path, file_path)
        if os.path.exists(full_path):
            examine_excel_file(full_path)
        else:
            print(f"File not found: {full_path}")
    
    print(f"\n{'='*80}")
    print("EXAMINATION COMPLETE")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()