#!/usr/bin/env python3
"""
Specialized parser for Yardi rent roll Excel exports
Handles complex multi-header structure to extract actual rent roll data
"""

import pandas as pd
import numpy as np
import os

def parse_yardi_rent_roll(file_path):
    """Parse Yardi rent roll with complex header structure"""
    print(f"Parsing Yardi file: {os.path.basename(file_path)}")
    
    # Read the file to understand structure
    excel_file = pd.ExcelFile(file_path)
    raw_df = pd.read_excel(file_path, sheet_name=0, header=None)
    
    # Find the actual data rows by looking for the combined header structure
    data_start_row = None
    header_row = None
    
    # Look through first 10 rows to find where real data starts
    for i in range(min(10, len(raw_df))):
        row_values = raw_df.iloc[i].astype(str).str.lower()
        
        # Check if this looks like a data row (has property code pattern)
        if row_values.str.contains('x[a-z0-9]', regex=True, na=False).any():
            data_start_row = i
            print(f"   Found data starting at row {i}")
            break
    
    if data_start_row is None:
        print("   Warning: Could not find data start row, using row 5")
        data_start_row = 5
    
    # Create column headers by combining info from multiple header rows
    # Row 1 typically has: Property, Unit(s), Lease, Lease Type, Area, etc.
    # Row 3 (skip 2) sometimes has rent columns
    
    try:
        # Try to read from row 1 for initial headers
        header_df = pd.read_excel(file_path, skiprows=1, nrows=1)
        initial_headers = [str(col).strip() for col in header_df.columns]
        
        # Clean up the headers
        clean_headers = []
        for i, header in enumerate(initial_headers):
            if header.startswith('Unnamed'):
                clean_headers.append(f'Column_{i}')
            else:
                clean_headers.append(header.strip())
        
        print(f"   Initial headers: {clean_headers[:8]}")
        
    except:
        # Fallback headers
        clean_headers = [f'Column_{i}' for i in range(17)]
    
    # Read the actual data
    data_df = pd.read_excel(file_path, skiprows=data_start_row, header=None)
    
    # Assign column names
    if len(clean_headers) >= len(data_df.columns):
        data_df.columns = clean_headers[:len(data_df.columns)]
    else:
        # Extend headers if needed
        extended_headers = clean_headers + [f'Column_{i}' for i in range(len(clean_headers), len(data_df.columns))]
        data_df.columns = extended_headers
    
    print(f"   Data shape: {data_df.shape}")
    print(f"   Columns: {list(data_df.columns)[:8]}")
    
    # Remove completely empty rows
    data_df = data_df.dropna(how='all')
    
    # Filter to Fund 2 properties (looking for X-prefixed property codes)
    fund2_mask = False
    for col in data_df.columns:
        if data_df[col].astype(str).str.upper().str.match(r'^X[A-Z0-9]').any():
            fund2_mask = data_df[col].astype(str).str.upper().str.match(r'^X[A-Z0-9]')
            print(f"   Found Fund 2 properties in column: {col}")
            break
    
    if isinstance(fund2_mask, pd.Series):
        fund2_df = data_df[fund2_mask].copy()
        print(f"   Fund 2 records: {len(fund2_df)}")
    else:
        fund2_df = data_df.copy()
        print(f"   Could not filter Fund 2 - using all records: {len(fund2_df)}")
    
    return fund2_df

def extract_key_metrics(df):
    """Extract key metrics from parsed Yardi data"""
    metrics = {
        'record_count': len(df),
        'total_monthly_rent': 0,
        'total_leased_sf': 0,
        'property_count': 0,
        'tenant_count': 0,
        'avg_rent_psf': 0
    }
    
    # Try to find and sum rent columns
    rent_columns = [col for col in df.columns if 'rent' in str(col).lower() and not 'area' in str(col).lower()]
    if rent_columns:
        for rent_col in rent_columns[:1]:  # Use first rent column
            try:
                rent_values = pd.to_numeric(df[rent_col], errors='coerce')
                rent_sum = rent_values.sum()
                if rent_sum > 0:
                    metrics['total_monthly_rent'] = rent_sum
                    print(f"   Found monthly rent in '{rent_col}': ${rent_sum:,.2f}")
                    break
            except:
                continue
    
    # Try to find area/SF columns
    area_columns = [col for col in df.columns if any(term in str(col).lower() for term in ['area', 'sf', 'square'])]
    if area_columns:
        for area_col in area_columns[:1]:  # Use first area column
            try:
                area_values = pd.to_numeric(df[area_col], errors='coerce')
                area_sum = area_values.sum()
                if area_sum > 0:
                    metrics['total_leased_sf'] = area_sum
                    print(f"   Found leased SF in '{area_col}': {area_sum:,.0f}")
                    break
            except:
                continue
    
    # Try to count properties
    prop_columns = [col for col in df.columns if 'property' in str(col).lower() or 'prop' in str(col).lower()]
    if prop_columns:
        try:
            prop_count = df[prop_columns[0]].nunique()
            if prop_count > 0:
                metrics['property_count'] = prop_count
                print(f"   Property count from '{prop_columns[0]}': {prop_count}")
        except:
            pass
    
    # Try to count tenants
    tenant_columns = [col for col in df.columns if 'tenant' in str(col).lower() or 'lease' in str(col).lower()]
    if tenant_columns:
        try:
            tenant_count = df[tenant_columns[0]].nunique()
            if tenant_count > 0:
                metrics['tenant_count'] = tenant_count
                print(f"   Tenant count from '{tenant_columns[0]}': {tenant_count}")
        except:
            pass
    
    # Calculate average PSF
    if metrics['total_monthly_rent'] > 0 and metrics['total_leased_sf'] > 0:
        metrics['avg_rent_psf'] = (metrics['total_monthly_rent'] * 12) / metrics['total_leased_sf']
    
    return metrics

def main():
    """Parse both Yardi rent roll files and extract metrics"""
    print("=" * 80)
    print("YARDI RENT ROLL PARSING FOR VALIDATION")
    print("=" * 80)
    
    files_to_parse = [
        ('/Users/michaeltang/Documents/GitHub/BI/PBI v1.7/rent rolls/03.31.25.xlsx', 'March 31, 2025'),
        ('/Users/michaeltang/Documents/GitHub/BI/PBI v1.7/rent rolls/12.31.24.xlsx', 'December 31, 2024')
    ]
    
    results = {}
    
    for file_path, date_str in files_to_parse:
        print(f"\n{'='*60}")
        print(f"PARSING: {date_str}")
        print(f"{'='*60}")
        
        try:
            # Parse the file
            parsed_df = parse_yardi_rent_roll(file_path)
            
            # Extract key metrics
            metrics = extract_key_metrics(parsed_df)
            
            # Store results
            results[date_str] = {
                'dataframe': parsed_df,
                'metrics': metrics
            }
            
            # Print summary
            print(f"\nSUMMARY - {date_str}:")
            print(f"   Records: {metrics['record_count']:,}")
            print(f"   Monthly Rent: ${metrics['total_monthly_rent']:,.2f}")
            print(f"   Leased SF: {metrics['total_leased_sf']:,.0f}")
            print(f"   Properties: {metrics['property_count']}")
            print(f"   Tenants: {metrics['tenant_count']}")
            print(f"   Avg PSF: ${metrics['avg_rent_psf']:.2f}")
            
            # Save parsed data
            output_file = f"/Users/michaeltang/Documents/GitHub/BI/PBI v1.7/Fund2_Validation_Results/parsed_yardi_{date_str.replace(' ', '_').replace(',', '').lower().replace(' ', '_')}.csv"
            parsed_df.to_csv(output_file, index=False)
            print(f"   Saved to: {os.path.basename(output_file)}")
            
        except Exception as e:
            print(f"Error parsing {date_str}: {e}")
            continue
    
    return results

if __name__ == "__main__":
    main()