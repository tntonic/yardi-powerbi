#!/usr/bin/env python3
"""
Generate Rent Roll from Yardi Tables for a specific date
Flexible date version of the rent roll generator
"""

import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime

class RentRollGenerator:
    def __init__(self, report_date_str, base_path="/Users/michaeltang/Documents/GitHub/BI/PBI v1.7"):
        """Initialize with report date and base path"""
        self.base_path = base_path
        self.report_date_str = report_date_str
        self.report_date = pd.to_datetime(report_date_str)
        
        # Convert to Excel serial date (days since 1899-12-30)
        excel_epoch = pd.Timestamp('1899-12-30')
        self.report_date_excel = (self.report_date - excel_epoch).days
        
        # Create date suffix for output files
        self.date_suffix = self.report_date.strftime('%m%d%y')
        
        print(f"Initializing Rent Roll Generator for {report_date_str}")
        print(f"  Report Date: {self.report_date}")
        print(f"  Excel Serial: {self.report_date_excel}")
        
        self.load_data()
        
    def load_data(self):
        """Load Fund 2 filtered data files"""
        print("\nLOADING FUND 2 DATA FILES...")
        
        data_path = os.path.join(self.base_path, "Data/Fund2_Filtered")
        
        # Load amendments
        amendments_file = os.path.join(data_path, "dim_fp_amendmentsunitspropertytenant_fund2.csv")
        self.amendments_df = pd.read_csv(amendments_file)
        print(f"  Amendments: {len(self.amendments_df)} rows")
        
        # Load charge schedules  
        charges_file = os.path.join(data_path, "dim_fp_amendmentchargeschedule_fund2_active.csv")
        self.charges_df = pd.read_csv(charges_file)
        print(f"  Charge Schedules: {len(self.charges_df)} rows")
        
        # Load property data
        property_file = os.path.join(data_path, "dim_property_fund2.csv")
        self.property_df = pd.read_csv(property_file)
        print(f"  Properties: {len(self.property_df)} rows")
        
        # Load unit data
        unit_file = os.path.join(data_path, "dim_unit_fund2.csv")
        self.unit_df = pd.read_csv(unit_file)
        print(f"  Units: {len(self.unit_df)} rows")
        
    def filter_valid_amendments(self):
        """Apply business logic filters to amendments"""
        print(f"\nFILTERING AMENDMENTS FOR {self.report_date_str}...")
        
        # Convert date columns
        self.amendments_df['start_date'] = pd.to_datetime(self.amendments_df['amendment start date'], errors='coerce')
        self.amendments_df['end_date'] = pd.to_datetime(self.amendments_df['amendment end date'], errors='coerce')
        
        # Filter 1: Status must be Activated or Superseded
        valid_statuses = ['Activated', 'Superseded']
        status_filtered = self.amendments_df[
            self.amendments_df['amendment status'].isin(valid_statuses)
        ]
        print(f"  After status filter: {len(status_filtered)} amendments")
        
        # Filter 2: Exclude Termination type
        type_filtered = status_filtered[
            status_filtered['amendment type'] != 'Termination'
        ]
        print(f"  After type filter: {len(type_filtered)} amendments")
        
        # Filter 3: Active on report date
        date_filtered = type_filtered[
            (type_filtered['start_date'] <= self.report_date) &
            ((type_filtered['end_date'] >= self.report_date) | type_filtered['end_date'].isna())
        ]
        print(f"  After date filter: {len(date_filtered)} amendments")
        
        self.valid_amendments = date_filtered
        
    def select_latest_amendments(self):
        """Select the latest amendment sequence per property/tenant"""
        print("\nSELECTING LATEST AMENDMENTS...")
        
        # Group by property and tenant to find max sequence
        latest_sequences = self.valid_amendments.groupby(
            ['property hmy', 'tenant hmy']
        )['amendment sequence'].max().reset_index()
        
        # Merge to filter only latest amendments
        self.latest_amendments = self.valid_amendments.merge(
            latest_sequences,
            on=['property hmy', 'tenant hmy', 'amendment sequence'],
            how='inner'
        )
        
        print(f"  Latest amendments: {len(self.latest_amendments)} rows")
        print(f"  Unique properties: {self.latest_amendments['property hmy'].nunique()}")
        print(f"  Unique tenants: {self.latest_amendments['tenant hmy'].nunique()}")
        
    def calculate_monthly_rent(self):
        """Calculate monthly rent from charge schedules"""
        print(f"\nCALCULATING MONTHLY RENT FOR {self.report_date_str}...")
        
        # Filter charges for base rent and active on report date
        rent_charges = self.charges_df[
            (self.charges_df['charge code'] == 'rent') &
            (self.charges_df['from date'] <= self.report_date_excel) &
            (self.charges_df['to date'] >= self.report_date_excel)
        ]
        print(f"  Active rent charges: {len(rent_charges)} rows")
        print(f"  Unique amendments with charges: {rent_charges['amendment hmy'].nunique()}")
        
        # Group charges by amendment to sum monthly amounts
        rent_by_amendment = rent_charges.groupby('amendment hmy').agg({
            'monthly amount': 'sum'
        }).reset_index()
        rent_by_amendment.columns = ['amendment hmy', 'current_monthly_rent']
        
        # Merge with latest amendments
        self.rent_roll = self.latest_amendments.merge(
            rent_by_amendment,
            on='amendment hmy',
            how='left'
        )
        
        # Fill NaN rent with 0
        self.rent_roll['current_monthly_rent'] = self.rent_roll['current_monthly_rent'].fillna(0)
        
        print(f"  Amendments with rent > 0: {len(self.rent_roll[self.rent_roll['current_monthly_rent'] > 0])}")
        print(f"  Total monthly rent: ${self.rent_roll['current_monthly_rent'].sum():,.2f}")
        
    def calculate_derived_metrics(self):
        """Calculate annual rent and rent PSF"""
        print("\nCALCULATING DERIVED METRICS...")
        
        # Annual rent
        self.rent_roll['current_annual_rent'] = self.rent_roll['current_monthly_rent'] * 12
        
        # Rent per square foot
        self.rent_roll['current_rent_psf'] = np.where(
            self.rent_roll['amendment sf'] > 0,
            self.rent_roll['current_annual_rent'] / self.rent_roll['amendment sf'],
            0
        )
        
        print(f"  Total annual rent: ${self.rent_roll['current_annual_rent'].sum():,.2f}")
        print(f"  Average rent PSF: ${self.rent_roll[self.rent_roll['current_rent_psf'] > 0]['current_rent_psf'].mean():.2f}")
        
    def add_property_details(self):
        """Add property name and location details"""
        print("\nADDING PROPERTY DETAILS...")
        
        # First, drop any existing property columns from amendments to avoid duplicates
        cols_to_drop = [col for col in self.rent_roll.columns if 'property code' in col or 'property name' in col]
        if cols_to_drop:
            self.rent_roll = self.rent_roll.drop(columns=cols_to_drop)
        
        # Merge with property data
        self.rent_roll = self.rent_roll.merge(
            self.property_df[['property id', 'property code', 'property name', 'postal city', 'postal state']],
            left_on='property hmy',
            right_on='property id',
            how='left'
        )
        
        print(f"  Properties matched: {self.rent_roll['property name'].notna().sum()}")
        
    def prepare_output(self):
        """Prepare final output dataframe"""
        print("\nPREPARING OUTPUT...")
        
        # Debug: Print available columns
        print(f"  Available columns: {self.rent_roll.columns.tolist()[:10]}...")
        
        # Select and rename columns for output
        output_columns = {
            'property code': 'property_code',
            'property name': 'property_name',
            'postal city': 'city',
            'postal state': 'state',
            'tenant id': 'tenant_id',
            'tenant name': 'tenant_name',
            'units under amendment': 'suite',
            'amendment sf': 'square_feet',
            'current_monthly_rent': 'monthly_rent',
            'current_annual_rent': 'annual_rent',
            'current_rent_psf': 'rent_psf',
            'amendment start date': 'lease_start',
            'amendment end date': 'lease_end',
            'amendment type': 'lease_type',
            'amendment status': 'status'
        }
        
        # Select available columns
        available_columns = {k: v for k, v in output_columns.items() if k in self.rent_roll.columns}
        
        self.output_df = self.rent_roll[list(available_columns.keys())].copy()
        self.output_df = self.output_df.rename(columns=available_columns)
        
        # Sort by property and tenant (using renamed columns)
        self.output_df = self.output_df.sort_values(['property_code', 'tenant_id'])
        
        print(f"  Output rows: {len(self.output_df)}")
        print(f"  Output columns: {list(self.output_df.columns)}")
        
    def save_output(self):
        """Save rent roll to CSV and Excel"""
        output_dir = os.path.join(self.base_path, "Generated_Rent_Rolls")
        os.makedirs(output_dir, exist_ok=True)
        
        # Create filenames with date
        csv_file = os.path.join(output_dir, f"fund2_rent_roll_generated_{self.date_suffix}.csv")
        excel_file = os.path.join(output_dir, f"fund2_rent_roll_generated_{self.date_suffix}.xlsx")
        
        # Save CSV
        self.output_df.to_csv(csv_file, index=False)
        print(f"\n✓ CSV saved: {csv_file}")
        
        # Save Excel with formatting
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            self.output_df.to_excel(writer, sheet_name='Rent Roll', index=False)
            
            # Auto-adjust column widths
            worksheet = writer.sheets['Rent Roll']
            for column in self.output_df:
                column_width = max(self.output_df[column].astype(str).map(len).max(), len(column))
                column_width = min(column_width, 50)  # Cap at 50 characters
                col_letter = chr(65 + self.output_df.columns.get_loc(column))
                worksheet.column_dimensions[col_letter].width = column_width + 2
        
        print(f"✓ Excel saved: {excel_file}")
        
    def print_summary(self):
        """Print summary statistics"""
        print("\n" + "=" * 80)
        print(f"RENT ROLL SUMMARY FOR {self.report_date_str}")
        print("=" * 80)
        
        print(f"\nPortfolio Metrics:")
        print(f"  Total Properties: {self.output_df['property_code'].nunique()}")
        print(f"  Total Tenants: {len(self.output_df)}")
        print(f"  Total Square Feet: {self.output_df['square_feet'].sum():,.0f}")
        print(f"  Total Monthly Rent: ${self.output_df['monthly_rent'].sum():,.2f}")
        print(f"  Total Annual Rent: ${self.output_df['annual_rent'].sum():,.2f}")
        
        if self.output_df['rent_psf'].sum() > 0:
            avg_psf = self.output_df[self.output_df['rent_psf'] > 0]['rent_psf'].mean()
            print(f"  Average Rent PSF: ${avg_psf:.2f}")
        
        print(f"\nLease Status Distribution:")
        status_counts = self.output_df['status'].value_counts()
        for status, count in status_counts.items():
            print(f"  {status}: {count} ({count/len(self.output_df)*100:.1f}%)")
        
    def generate(self):
        """Run the complete rent roll generation process"""
        print("=" * 80)
        print(f"GENERATING RENT ROLL FROM YARDI TABLES FOR {self.report_date_str}")
        print("=" * 80)
        
        self.filter_valid_amendments()
        self.select_latest_amendments()
        self.calculate_monthly_rent()
        self.calculate_derived_metrics()
        self.add_property_details()
        self.prepare_output()
        self.save_output()
        self.print_summary()
        
        return self.output_df

def main():
    """Main function to run rent roll generation for specified date"""
    
    # Get date from command line argument or use default
    if len(sys.argv) > 1:
        report_date = sys.argv[1]
    else:
        report_date = input("Enter report date (MM/DD/YYYY) [default: 6/1/2025]: ") or "6/1/2025"
    
    try:
        # Validate date format
        pd.to_datetime(report_date)
        
        # Generate rent roll
        generator = RentRollGenerator(report_date)
        rent_roll_df = generator.generate()
        
        print("\n✓ RENT ROLL GENERATION COMPLETE")
        
        return rent_roll_df
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        return None

if __name__ == "__main__":
    main()