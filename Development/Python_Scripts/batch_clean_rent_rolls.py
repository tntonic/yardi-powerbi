#!/usr/bin/env python3
"""
Batch Rent Roll Cleaning Script
Processes all rent roll files in a directory and creates standardized outputs
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os
import glob
import json
from clean_rent_roll import RentRollCleaner


def batch_clean_rent_rolls(
    input_directory: str = "rent rolls",
    output_directory: str = "cleaned_rent_rolls",
    save_summary: bool = True
):
    """
    Clean all rent roll Excel files in a directory.
    
    Args:
        input_directory: Directory containing rent roll Excel files
        output_directory: Directory to save cleaned files
        save_summary: Whether to save a summary JSON file
    """
    
    print(f"\n{'='*80}")
    print("BATCH RENT ROLL CLEANING")
    print(f"{'='*80}")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_directory, exist_ok=True)
    
    # Find all Excel files
    excel_files = glob.glob(os.path.join(input_directory, "*.xlsx"))
    
    if not excel_files:
        print(f"No Excel files found in {input_directory}")
        return
    
    print(f"Found {len(excel_files)} Excel files to process")
    
    # Initialize cleaner
    cleaner = RentRollCleaner(verbose=False)
    
    # Process each file
    all_data = []
    summary = {
        'processing_date': datetime.now().isoformat(),
        'files_processed': [],
        'total_records': 0,
        'errors': []
    }
    
    for i, file_path in enumerate(excel_files, 1):
        file_name = os.path.basename(file_path)
        print(f"\n[{i}/{len(excel_files)}] Processing: {file_name}")
        
        try:
            # Clean the data
            df = cleaner.clean_rent_roll(file_path)
            
            # Add source file information
            df['source_file'] = file_name
            df['processing_date'] = datetime.now()
            
            # Extract period date from filename
            period_date = extract_date_from_filename(file_name)
            if period_date:
                df['period_date'] = period_date
                df['period_quarter'] = f"Q{(period_date.month-1)//3 + 1} {period_date.year}"
            
            # Save individual cleaned file
            output_file = os.path.join(
                output_directory,
                file_name.replace('.xlsx', '_cleaned.csv')
            )
            df.to_csv(output_file, index=False)
            
            # Add to combined dataset
            all_data.append(df)
            
            # Update summary
            file_summary = {
                'file_name': file_name,
                'period_date': period_date.isoformat() if period_date else None,
                'records': len(df),
                'funds': df['fund'].value_counts().to_dict() if 'fund' in df.columns else {},
                'occupancy_rate': calculate_occupancy_rate(df),
                'total_square_feet': df['square_feet'].sum() if 'square_feet' in df.columns else 0,
                'total_annual_rent': df['annual_rent'].sum() if 'annual_rent' in df.columns else 0
            }
            summary['files_processed'].append(file_summary)
            summary['total_records'] += len(df)
            
            print(f"  ✓ Processed: {len(df)} records")
            print(f"  ✓ Saved to: {output_file}")
            
        except Exception as e:
            print(f"  ✗ Error: {str(e)}")
            summary['errors'].append({
                'file_name': file_name,
                'error': str(e)
            })
    
    # Combine all data
    if all_data:
        print(f"\n{'='*50}")
        print("CREATING COMBINED DATASET...")
        
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Sort by period date and property
        sort_cols = []
        if 'period_date' in combined_df.columns:
            sort_cols.append('period_date')
        if 'fund' in combined_df.columns:
            sort_cols.append('fund')
        if 'property_code' in combined_df.columns:
            sort_cols.append('property_code')
        
        if sort_cols:
            combined_df = combined_df.sort_values(sort_cols)
        
        # Save combined dataset
        combined_file = os.path.join(output_directory, 'all_rent_rolls_combined.csv')
        combined_df.to_csv(combined_file, index=False)
        print(f"  ✓ Combined dataset saved to: {combined_file}")
        print(f"  ✓ Total records: {len(combined_df)}")
        
        # Create period comparison dataset
        if 'period_date' in combined_df.columns:
            create_period_comparison(combined_df, output_directory)
    
    # Save summary
    if save_summary:
        summary_file = os.path.join(output_directory, 'cleaning_summary.json')
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        print(f"\n✓ Summary saved to: {summary_file}")
    
    # Print final summary
    print(f"\n{'='*80}")
    print("BATCH PROCESSING COMPLETE")
    print(f"{'='*80}")
    print(f"Files processed: {len(summary['files_processed'])}")
    print(f"Total records: {summary['total_records']}")
    print(f"Errors: {len(summary['errors'])}")
    
    if summary['errors']:
        print("\nFiles with errors:")
        for error in summary['errors']:
            print(f"  - {error['file_name']}: {error['error']}")


def extract_date_from_filename(filename: str):
    """Extract date from filename."""
    import re
    
    # Pattern 1: MM.DD.YY format
    pattern1 = r'(\d{2})\.(\d{2})\.(\d{2})'
    match1 = re.search(pattern1, filename)
    if match1:
        month, day, year = match1.groups()
        year = f"20{year}"
        try:
            return datetime(int(year), int(month), int(day))
        except ValueError:
            pass
    
    # Pattern 2: (YYMM) format
    pattern2 = r'\((\d{2})([A-Z]{3})\)'
    match2 = re.search(pattern2, filename)
    if match2:
        year, month_abbr = match2.groups()
        year = f"20{year}"
        month_map = {
            'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4,
            'MAY': 5, 'JUN': 6, 'JUL': 7, 'AUG': 8,
            'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12
        }
        if month_abbr in month_map:
            month = month_map[month_abbr]
            # Assume last day of month
            if month == 12:
                day = 31
            elif month in [1, 3, 5, 7, 8, 10]:
                day = 31
            elif month in [4, 6, 9, 11]:
                day = 30
            else:  # February
                day = 29 if int(year) % 4 == 0 else 28
            try:
                return datetime(int(year), month, day)
            except ValueError:
                pass
    
    return None


def calculate_occupancy_rate(df: pd.DataFrame) -> float:
    """Calculate occupancy rate from dataframe."""
    if 'status' in df.columns:
        occupied = df['status'].isin(['Occupied', 'Month-to-Month']).sum()
        total = len(df)
        return round((occupied / total * 100) if total > 0 else 0, 2)
    elif 'is_vacant' in df.columns:
        occupied = (~df['is_vacant']).sum()
        total = len(df)
        return round((occupied / total * 100) if total > 0 else 0, 2)
    return 0


def create_period_comparison(df: pd.DataFrame, output_directory: str):
    """Create period-over-period comparison dataset."""
    print("\nCREATING PERIOD COMPARISON...")
    
    # Group by period and calculate metrics
    if 'period_date' in df.columns and 'fund' in df.columns:
        comparison = []
        
        for period in df['period_date'].unique():
            period_data = df[df['period_date'] == period]
            
            for fund in period_data['fund'].unique():
                fund_data = period_data[period_data['fund'] == fund]
                
                metrics = {
                    'period_date': period,
                    'fund': fund,
                    'total_properties': fund_data['property_code'].nunique() if 'property_code' in fund_data.columns else 0,
                    'total_tenants': fund_data['tenant_name'].nunique() if 'tenant_name' in fund_data.columns else 0,
                    'total_records': len(fund_data),
                    'total_square_feet': fund_data['square_feet'].sum() if 'square_feet' in fund_data.columns else 0,
                    'occupied_square_feet': fund_data[fund_data['status'] != 'Vacant']['square_feet'].sum() if 'status' in fund_data.columns and 'square_feet' in fund_data.columns else 0,
                    'total_annual_rent': fund_data['annual_rent'].sum() if 'annual_rent' in fund_data.columns else 0,
                    'avg_rent_psf': fund_data['rent_psf'].mean() if 'rent_psf' in fund_data.columns else 0,
                    'occupancy_rate': calculate_occupancy_rate(fund_data)
                }
                
                comparison.append(metrics)
        
        comparison_df = pd.DataFrame(comparison)
        comparison_df = comparison_df.sort_values(['fund', 'period_date'])
        
        # Calculate period-over-period changes
        for fund in comparison_df['fund'].unique():
            fund_mask = comparison_df['fund'] == fund
            comparison_df.loc[fund_mask, 'sq_ft_change'] = comparison_df.loc[fund_mask, 'occupied_square_feet'].diff()
            comparison_df.loc[fund_mask, 'rent_change'] = comparison_df.loc[fund_mask, 'total_annual_rent'].diff()
            comparison_df.loc[fund_mask, 'occupancy_change'] = comparison_df.loc[fund_mask, 'occupancy_rate'].diff()
        
        # Save comparison
        comparison_file = os.path.join(output_directory, 'period_comparison.csv')
        comparison_df.to_csv(comparison_file, index=False)
        print(f"  ✓ Period comparison saved to: {comparison_file}")
        
        # Print summary
        print(f"\nPeriod Comparison Summary:")
        for fund in comparison_df['fund'].unique():
            fund_data = comparison_df[comparison_df['fund'] == fund]
            print(f"\n  {fund}:")
            print(f"    Periods analyzed: {len(fund_data)}")
            
            if len(fund_data) > 1:
                latest = fund_data.iloc[-1]
                earliest = fund_data.iloc[0]
                print(f"    Occupancy change: {earliest['occupancy_rate']:.1f}% → {latest['occupancy_rate']:.1f}%")
                print(f"    SF change: {(latest['occupied_square_feet'] - earliest['occupied_square_feet']):,.0f}")
                print(f"    Rent change: ${(latest['total_annual_rent'] - earliest['total_annual_rent']):,.0f}")


def main():
    """Main execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Batch clean rent roll Excel files')
    parser.add_argument('--input', default='rent rolls', help='Input directory')
    parser.add_argument('--output', default='cleaned_rent_rolls', help='Output directory')
    parser.add_argument('--no-summary', action='store_true', help='Skip summary file')
    
    args = parser.parse_args()
    
    batch_clean_rent_rolls(
        input_directory=args.input,
        output_directory=args.output,
        save_summary=not args.no_summary
    )


if __name__ == "__main__":
    main()