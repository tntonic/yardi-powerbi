#!/usr/bin/env python3
"""
Generate Fund 2 Rent Rolls for Target Dates: March 31, 2025 and December 31, 2024
Implements validated amendment logic from DAX library for comprehensive validation
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime

# Define paths
base_path = "/Users/michaeltang/Documents/GitHub/BI/PBI v1.7"
fund2_path = os.path.join(base_path, "Data/Fund2_Filtered")
output_path = "/Users/michaeltang/Documents/GitHub/BI/PBI v1.7/Fund2_Validation_Results"

# Target dates for validation
target_dates = [
    {
        'date': '2025-03-31',
        'date_str': 'March 31, 2025',
        'excel_serial': 45383,  # March 31, 2025 in Excel format
        'file_suffix': 'mar31_2025'
    },
    {
        'date': '2024-12-31', 
        'date_str': 'December 31, 2024',
        'excel_serial': 45292,  # December 31, 2024 in Excel format
        'file_suffix': 'dec31_2024'
    }
]

class Fund2RentRollGenerator:
    """Generate rent roll for specific target dates using validated business logic"""
    
    def __init__(self, verbose=True):
        self.verbose = verbose
        self.amendments_df = None
        self.charges_df = None
        self.properties_df = None
        
    def load_data(self):
        """Load Fund 2 filtered data"""
        if self.verbose:
            print("Loading Fund 2 data...")
        
        self.amendments_df = pd.read_csv(
            os.path.join(fund2_path, "dim_fp_amendmentsunitspropertytenant_fund2.csv")
        )
        self.charges_df = pd.read_csv(
            os.path.join(fund2_path, "dim_fp_amendmentchargeschedule_fund2_all.csv")
        )
        self.properties_df = pd.read_csv(
            os.path.join(fund2_path, "dim_property_fund2.csv")
        )
        
        # Convert dates
        self.amendments_df['start_dt'] = pd.to_datetime(self.amendments_df['amendment start date'])
        self.amendments_df['end_dt'] = pd.to_datetime(self.amendments_df['amendment end date'])
        
        if self.verbose:
            print(f"Loaded {len(self.amendments_df):,} amendments")
            print(f"Loaded {len(self.charges_df):,} charges")
            print(f"Loaded {len(self.properties_df):,} properties")
    
    def generate_rent_roll_for_date(self, target_info):
        """Generate rent roll for specific target date"""
        target_date = pd.Timestamp(target_info['date'])
        date_str = target_info['date_str']
        
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"GENERATING RENT ROLL FOR {date_str.upper()}")
            print(f"{'='*60}")
        
        # Step 1: Apply validated business logic filters
        if self.verbose:
            print("1. Applying validated amendment filters...")
        
        # Filter: Status IN ("Activated", "Superseded") AND Type <> "Termination"
        valid_amendments = self.amendments_df[
            (self.amendments_df['amendment status'].isin(['Activated', 'Superseded'])) &
            (self.amendments_df['amendment type'] != 'Termination') &
            (self.amendments_df['start_dt'] <= target_date) &
            ((self.amendments_df['end_dt'] >= target_date) | self.amendments_df['end_dt'].isna())
        ].copy()
        
        if self.verbose:
            print(f"   Active amendments on {date_str}: {len(valid_amendments):,}")
            status_dist = valid_amendments['amendment status'].value_counts()
            for status, count in status_dist.items():
                print(f"     {status}: {count:,} ({count/len(valid_amendments)*100:.1f}%)")
        
        # Step 2: Select latest amendment sequence per property/tenant (Critical Logic)
        if self.verbose:
            print("2. Selecting latest amendment sequences...")
        
        latest_sequences = valid_amendments.groupby(
            ['property hmy', 'tenant hmy']
        )['amendment sequence'].max().reset_index()
        latest_sequences.rename(columns={'amendment sequence': 'max_sequence'}, inplace=True)
        
        latest_amendments = pd.merge(
            valid_amendments,
            latest_sequences,
            left_on=['property hmy', 'tenant hmy', 'amendment sequence'],
            right_on=['property hmy', 'tenant hmy', 'max_sequence'],
            how='inner'
        )
        
        if self.verbose:
            print(f"   Latest amendments selected: {len(latest_amendments):,}")
            print(f"   Unique properties: {latest_amendments['property hmy'].nunique()}")
            print(f"   Unique tenants: {latest_amendments['tenant hmy'].nunique()}")
        
        # Step 3: Calculate monthly rent from charge schedule
        if self.verbose:
            print("3. Calculating monthly rent from charges...")
        
        # Filter charges for base rent (simplified date logic for validation)
        active_charges = self.charges_df[
            (self.charges_df['charge code'] == 'rent') &
            (self.charges_df['monthly amount'] > 0)
        ].copy()
        
        if self.verbose:
            print(f"   Total rent charges found: {len(active_charges):,}")
        
        # Merge amendments with charges
        rent_data = pd.merge(
            latest_amendments,
            active_charges,
            on='amendment hmy',
            how='left',
            suffixes=('', '_charge')
        )
        
        # Group by amendment to sum monthly rent
        rent_summary = rent_data.groupby([
            'property hmy', 'property code', 'tenant hmy', 'tenant id', 
            'amendment hmy', 'amendment sf', 'amendment start date', 'amendment end date',
            'amendment status', 'amendment type', 'amendment sequence'
        ]).agg({
            'monthly amount': 'sum'
        }).reset_index()
        
        # Clean up rent data
        rent_summary['monthly_rent'] = rent_summary['monthly amount'].fillna(0)
        rent_summary['annual_rent'] = rent_summary['monthly_rent'] * 12
        rent_summary['rent_psf'] = np.where(
            rent_summary['amendment sf'] > 0,
            rent_summary['annual_rent'] / rent_summary['amendment sf'],
            0
        )
        
        if self.verbose:
            total_monthly = rent_summary['monthly_rent'].sum()
            total_sf = rent_summary['amendment sf'].sum()
            print(f"   Total monthly rent: ${total_monthly:,.2f}")
            print(f"   Total leased SF: {total_sf:,.0f}")
            if total_sf > 0:
                avg_psf = rent_summary['annual_rent'].sum() / total_sf
                print(f"   Portfolio average PSF: ${avg_psf:.2f}")
        
        # Step 4: Add property details
        rent_summary = pd.merge(
            rent_summary,
            self.properties_df[['property code', 'property name', 'postal city', 'postal state']],
            on='property code',
            how='left'
        )
        
        # Step 5: Add metadata
        rent_summary['fund'] = 'Fund 2'
        rent_summary['report_date'] = date_str
        rent_summary['target_date'] = target_info['date']
        
        # Step 6: Format for output
        output_columns = [
            'fund', 'report_date', 'target_date',
            'property code', 'property name', 'postal city', 'postal state',
            'tenant id', 'tenant hmy',
            'amendment status', 'amendment type', 'amendment sequence',
            'amendment sf', 'monthly_rent', 'annual_rent', 'rent_psf',
            'amendment start date', 'amendment end date'
        ]
        
        final_rent_roll = rent_summary[output_columns].copy()
        final_rent_roll.sort_values(['property code', 'tenant id'], inplace=True)
        final_rent_roll.reset_index(drop=True, inplace=True)
        
        # Save output
        csv_file = os.path.join(output_path, f"fund2_rent_roll_generated_{target_info['file_suffix']}.csv")
        excel_file = os.path.join(output_path, f"fund2_rent_roll_generated_{target_info['file_suffix']}.xlsx")
        
        final_rent_roll.to_csv(csv_file, index=False)
        final_rent_roll.to_excel(excel_file, index=False)
        
        if self.verbose:
            print(f"4. Saved outputs:")
            print(f"   CSV: {csv_file}")
            print(f"   Excel: {excel_file}")
        
        return final_rent_roll, csv_file, excel_file
    
    def generate_all_target_dates(self):
        """Generate rent rolls for all target dates"""
        print("=" * 80)
        print("FUND 2 RENT ROLL VALIDATION - TARGET DATES GENERATION")
        print("=" * 80)
        
        self.load_data()
        
        results = {}
        
        for target_info in target_dates:
            rent_roll, csv_file, excel_file = self.generate_rent_roll_for_date(target_info)
            results[target_info['date_str']] = {
                'rent_roll': rent_roll,
                'csv_file': csv_file,
                'excel_file': excel_file,
                'summary': {
                    'records': len(rent_roll),
                    'total_monthly_rent': rent_roll['monthly_rent'].sum(),
                    'total_sf': rent_roll['amendment sf'].sum(),
                    'properties': rent_roll['property code'].nunique(),
                    'tenants': rent_roll['tenant id'].nunique()
                }
            }
        
        # Print summary
        print(f"\n{'='*60}")
        print("GENERATION SUMMARY")
        print(f"{'='*60}")
        
        for date_str, result in results.items():
            summary = result['summary']
            print(f"\n{date_str}:")
            print(f"  Records: {summary['records']:,}")
            print(f"  Total Monthly Rent: ${summary['total_monthly_rent']:,.2f}")
            print(f"  Total Leased SF: {summary['total_sf']:,.0f}")
            print(f"  Properties: {summary['properties']}")
            print(f"  Tenants: {summary['tenants']}")
            if summary['total_sf'] > 0:
                avg_psf = (summary['total_monthly_rent'] * 12) / summary['total_sf']
                print(f"  Portfolio Avg PSF: ${avg_psf:.2f}")
        
        return results

def main():
    """Main execution function"""
    generator = Fund2RentRollGenerator(verbose=True)
    results = generator.generate_all_target_dates()
    
    print(f"\n{'='*80}")
    print("✅ Fund 2 rent roll generation completed for target dates!")
    print("Files saved to: /Users/michaeltang/Documents/GitHub/BI/PBI v1.7/Fund2_Validation_Results/")
    print(f"{'='*80}")
    
    return results

if __name__ == "__main__":
    main()