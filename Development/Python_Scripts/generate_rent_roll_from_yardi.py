#!/usr/bin/env python3
"""
Generate Rent Roll from Yardi Tables
Implements the validated business logic from PowerBI documentation
Focuses on Fund 2 properties as of June 30, 2025
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime

# Define paths
base_path = "/Users/michaeltang/Documents/GitHub/BI/PBI v1.7"
fund2_path = os.path.join(base_path, "Data/Fund2_Filtered")
output_path = os.path.join(base_path, "Generated_Rent_Rolls")

# Create output directory
os.makedirs(output_path, exist_ok=True)

# June 30, 2025 in different formats
REPORT_DATE_EXCEL = 45838  # June 30, 2025 in Excel serial format
REPORT_DATE_STR = "6/30/2025"
REPORT_DATE = pd.Timestamp('2025-06-30')

class RentRollGenerator:
    """Generate rent roll from Yardi tables using validated business logic"""
    
    def __init__(self, verbose=True):
        self.verbose = verbose
        self.amendments_df = None
        self.charges_df = None
        self.properties_df = None
        self.units_df = None
        self.latest_amendments = None
        
    def load_data(self):
        """Load all filtered Fund 2 data tables"""
        if self.verbose:
            print("\n1. LOADING FUND 2 DATA...")
        
        # Load amendments
        self.amendments_df = pd.read_csv(
            os.path.join(fund2_path, "dim_fp_amendmentsunitspropertytenant_fund2.csv")
        )
        if self.verbose:
            print(f"   Loaded {len(self.amendments_df)} amendment records")
        
        # Load active charges for June 30, 2025
        self.charges_df = pd.read_csv(
            os.path.join(fund2_path, "dim_fp_amendmentchargeschedule_fund2_active.csv")
        )
        if self.verbose:
            print(f"   Loaded {len(self.charges_df)} active charge records")
        
        # Load properties
        self.properties_df = pd.read_csv(
            os.path.join(fund2_path, "dim_property_fund2.csv")
        )
        if self.verbose:
            print(f"   Loaded {len(self.properties_df)} property records")
        
        # Load units
        self.units_df = pd.read_csv(
            os.path.join(fund2_path, "dim_unit_fund2.csv")
        )
        if self.verbose:
            print(f"   Loaded {len(self.units_df)} unit records")
    
    def apply_amendment_filters(self):
        """
        Apply the core business logic filters to amendments:
        1. Status IN ("Activated", "Superseded")
        2. Type NOT = "Termination"
        3. Active on report date (start <= report date AND end >= report date or null)
        """
        if self.verbose:
            print("\n2. APPLYING AMENDMENT FILTERS...")
        
        # Initial count
        initial_count = len(self.amendments_df)
        
        # Filter 1: Status must be Activated or Superseded
        valid_statuses = ['Activated', 'Superseded']
        status_filtered = self.amendments_df[
            self.amendments_df['amendment status'].isin(valid_statuses)
        ]
        if self.verbose:
            print(f"   After status filter: {len(status_filtered)} records (removed {initial_count - len(status_filtered)})")
        
        # Filter 2: Exclude Termination type
        type_filtered = status_filtered[
            status_filtered['amendment type'] != 'Termination'
        ]
        if self.verbose:
            print(f"   After excluding terminations: {len(type_filtered)} records (removed {len(status_filtered) - len(type_filtered)})")
        
        # Filter 3: Active on report date
        # Use the serial date columns we created during filtering
        date_filtered = type_filtered[
            (type_filtered['amendment start date serial'] <= REPORT_DATE_EXCEL) &
            ((type_filtered['amendment end date serial'] >= REPORT_DATE_EXCEL) | 
             type_filtered['amendment end date serial'].isna())
        ]
        if self.verbose:
            print(f"   After date filter (active on {REPORT_DATE_STR}): {len(date_filtered)} records")
        
        self.valid_amendments = date_filtered
        
        # Print status distribution of valid amendments
        if self.verbose:
            status_dist = self.valid_amendments['amendment status'].value_counts()
            print(f"   Status distribution: {status_dist.to_dict()}")
    
    def select_latest_amendments(self):
        """
        Select the LATEST amendment sequence per property/tenant combination
        This is the critical logic for accurate rent roll generation
        """
        if self.verbose:
            print("\n3. SELECTING LATEST AMENDMENTS PER TENANT...")
        
        # Group by property and tenant to find max sequence
        latest_sequences = self.valid_amendments.groupby(
            ['property hmy', 'tenant hmy']
        )['amendment sequence'].max().reset_index()
        latest_sequences.rename(columns={'amendment sequence': 'max_sequence'}, inplace=True)
        
        # Merge back to get full amendment records
        self.latest_amendments = pd.merge(
            self.valid_amendments,
            latest_sequences,
            left_on=['property hmy', 'tenant hmy', 'amendment sequence'],
            right_on=['property hmy', 'tenant hmy', 'max_sequence'],
            how='inner'
        )
        
        if self.verbose:
            print(f"   Selected {len(self.latest_amendments)} latest amendments")
            print(f"   Unique properties: {self.latest_amendments['property hmy'].nunique()}")
            print(f"   Unique tenants: {self.latest_amendments['tenant hmy'].nunique()}")
            
            # Show example of sequence selection
            sample_prop = self.latest_amendments['property hmy'].iloc[0]
            sample_tenant = self.latest_amendments['tenant hmy'].iloc[0]
            all_sequences = self.valid_amendments[
                (self.valid_amendments['property hmy'] == sample_prop) &
                (self.valid_amendments['tenant hmy'] == sample_tenant)
            ]['amendment sequence'].tolist()
            selected_seq = self.latest_amendments[
                (self.latest_amendments['property hmy'] == sample_prop) &
                (self.latest_amendments['tenant hmy'] == sample_tenant)
            ]['amendment sequence'].iloc[0]
            print(f"\n   Example - Property {sample_prop}, Tenant {sample_tenant}:")
            print(f"     All sequences: {all_sequences}")
            print(f"     Selected: {selected_seq}")
    
    def calculate_monthly_rent(self):
        """
        Calculate monthly rent from charge schedule
        Join latest amendments with active charges
        """
        if self.verbose:
            print("\n4. CALCULATING MONTHLY RENT FROM CHARGES...")
        
        # Prepare charges - filter for base rent charges
        rent_charges = self.charges_df[self.charges_df['charge code'] == 'rent'].copy()
        
        if self.verbose:
            print(f"   Found {len(rent_charges)} rent charge records")
        
        # Merge amendments with charges
        rent_data = pd.merge(
            self.latest_amendments,
            rent_charges,
            left_on='amendment hmy',
            right_on='amendment hmy',
            how='left',
            suffixes=('', '_charge')
        )
        
        # Group by amendment to sum monthly rent (in case of multiple charge lines)
        rent_summary = rent_data.groupby(
            ['property hmy', 'property code', 'tenant hmy', 'tenant id', 
             'amendment hmy', 'amendment sf', 'amendment term',
             'amendment start date', 'amendment end date',
             'units under amendment', 'amendment status', 'amendment type']
        ).agg({
            'monthly amount': 'sum'
        }).reset_index()
        
        # Rename for clarity
        rent_summary.rename(columns={'monthly amount': 'current_monthly_rent'}, inplace=True)
        
        # Calculate annual rent
        rent_summary['current_annual_rent'] = rent_summary['current_monthly_rent'] * 12
        
        # Calculate rent per square foot
        rent_summary['rent_psf'] = np.where(
            rent_summary['amendment sf'] > 0,
            rent_summary['current_annual_rent'] / rent_summary['amendment sf'],
            0
        )
        
        self.rent_roll_data = rent_summary
        
        if self.verbose:
            print(f"   Calculated rent for {len(self.rent_roll_data)} leases")
            total_monthly = self.rent_roll_data['current_monthly_rent'].sum()
            print(f"   Total monthly rent: ${total_monthly:,.2f}")
            avg_psf = self.rent_roll_data[self.rent_roll_data['rent_psf'] > 0]['rent_psf'].mean()
            print(f"   Average rent PSF: ${avg_psf:.2f}")
    
    def add_property_details(self):
        """Add property names and other details"""
        if self.verbose:
            print("\n5. ADDING PROPERTY DETAILS...")
        
        # Merge with property data
        self.rent_roll_data = pd.merge(
            self.rent_roll_data,
            self.properties_df[['property id', 'property code', 'property name', 
                               'postal city', 'postal state', 'postal zip code']],
            left_on='property code',
            right_on='property code',
            how='left'
        )
        
        if self.verbose:
            print(f"   Added property details for {self.rent_roll_data['property name'].notna().sum()} records")
    
    def calculate_derived_metrics(self):
        """Calculate additional metrics like remaining term, etc."""
        if self.verbose:
            print("\n6. CALCULATING DERIVED METRICS...")
        
        # Convert dates for calculations
        self.rent_roll_data['amendment_start_dt'] = pd.to_datetime(
            self.rent_roll_data['amendment start date']
        )
        self.rent_roll_data['amendment_end_dt'] = pd.to_datetime(
            self.rent_roll_data['amendment end date']
        )
        
        # Calculate lease term in months
        self.rent_roll_data['lease_term_months'] = (
            (self.rent_roll_data['amendment_end_dt'] - 
             self.rent_roll_data['amendment_start_dt']).dt.days / 30.44
        ).round(1)
        
        # Calculate remaining term from report date
        self.rent_roll_data['remaining_term_months'] = (
            (self.rent_roll_data['amendment_end_dt'] - REPORT_DATE).dt.days / 30.44
        ).round(1)
        self.rent_roll_data.loc[
            self.rent_roll_data['remaining_term_months'] < 0, 
            'remaining_term_months'
        ] = 0
        
        # Add Fund designation
        self.rent_roll_data['fund'] = 'Fund 2'
        
        # Add report date
        self.rent_roll_data['report_date'] = REPORT_DATE_STR
        
        if self.verbose:
            avg_remaining = self.rent_roll_data['remaining_term_months'].mean()
            print(f"   Average remaining term: {avg_remaining:.1f} months")
    
    def format_output(self):
        """Format the output to match expected rent roll structure"""
        if self.verbose:
            print("\n7. FORMATTING OUTPUT...")
        
        # Select and order columns
        output_columns = [
            'fund',
            'property code',  # Fixed column name
            'property name',  # Fixed column name
            'property id',
            'units under amendment',
            'tenant id',      # Fixed column name
            'tenant hmy',
            'amendment status',
            'amendment type',
            'amendment sf',
            'current_monthly_rent',
            'current_annual_rent',
            'rent_psf',
            'amendment_start_dt',
            'amendment_end_dt',
            'lease_term_months',
            'remaining_term_months',
            'postal city',
            'postal state',
            'report_date'
        ]
        
        # Filter to available columns
        available_columns = [col for col in output_columns if col in self.rent_roll_data.columns]
        
        self.final_rent_roll = self.rent_roll_data[available_columns].copy()
        
        # Sort by property and tenant
        self.final_rent_roll.sort_values(
            ['property code', 'tenant id'], 
            inplace=True
        )
        
        # Reset index
        self.final_rent_roll.reset_index(drop=True, inplace=True)
        
        if self.verbose:
            print(f"   Final rent roll has {len(self.final_rent_roll)} rows")
            print(f"   Columns: {list(self.final_rent_roll.columns)}")
    
    def save_output(self):
        """Save the generated rent roll"""
        if self.verbose:
            print("\n8. SAVING OUTPUT...")
        
        # Save as CSV
        csv_file = os.path.join(output_path, "fund2_rent_roll_generated_063025.csv")
        self.final_rent_roll.to_csv(csv_file, index=False)
        
        # Save as Excel
        excel_file = os.path.join(output_path, "fund2_rent_roll_generated_063025.xlsx")
        self.final_rent_roll.to_excel(excel_file, index=False)
        
        if self.verbose:
            print(f"   Saved CSV: {csv_file}")
            print(f"   Saved Excel: {excel_file}")
        
        return csv_file, excel_file
    
    def print_summary(self):
        """Print summary statistics"""
        print("\n" + "=" * 80)
        print("RENT ROLL GENERATION SUMMARY")
        print("=" * 80)
        
        print(f"Report Date: {REPORT_DATE_STR}")
        print(f"Fund: Fund 2")
        print(f"Total Records: {len(self.final_rent_roll)}")
        
        # Financial summary
        total_monthly = self.final_rent_roll['current_monthly_rent'].sum()
        total_annual = self.final_rent_roll['current_annual_rent'].sum()
        total_sf = self.final_rent_roll['amendment sf'].sum()
        
        print(f"\nFinancial Summary:")
        print(f"  Total Monthly Rent: ${total_monthly:,.2f}")
        print(f"  Total Annual Rent: ${total_annual:,.2f}")
        print(f"  Total Leased SF: {total_sf:,.0f}")
        
        if total_sf > 0:
            avg_psf = total_annual / total_sf
            print(f"  Portfolio Avg Rent PSF: ${avg_psf:.2f}")
        
        # Property summary
        property_count = self.final_rent_roll['property code'].nunique()
        tenant_count = self.final_rent_roll['tenant id'].nunique()
        
        print(f"\nPortfolio Summary:")
        print(f"  Properties: {property_count}")
        print(f"  Tenants: {tenant_count}")
        print(f"  Average Lease Term: {self.final_rent_roll['lease_term_months'].mean():.1f} months")
        print(f"  Average Remaining Term: {self.final_rent_roll['remaining_term_months'].mean():.1f} months")
        
        # Status distribution
        print(f"\nAmendment Status Distribution:")
        for status, count in self.final_rent_roll['amendment status'].value_counts().items():
            pct = (count / len(self.final_rent_roll)) * 100
            print(f"  {status}: {count} ({pct:.1f}%)")
        
        # Type distribution
        print(f"\nAmendment Type Distribution:")
        for atype, count in self.final_rent_roll['amendment type'].value_counts().head(5).items():
            pct = (count / len(self.final_rent_roll)) * 100
            print(f"  {atype}: {count} ({pct:.1f}%)")
        
        print("\n" + "=" * 80)
    
    def generate(self):
        """Main generation function"""
        print("=" * 80)
        print("GENERATING RENT ROLL FROM YARDI TABLES")
        print("=" * 80)
        
        # Load data
        self.load_data()
        
        # Apply business logic
        self.apply_amendment_filters()
        self.select_latest_amendments()
        self.calculate_monthly_rent()
        
        # Add details and metrics
        self.add_property_details()
        self.calculate_derived_metrics()
        
        # Format and save
        self.format_output()
        csv_file, excel_file = self.save_output()
        
        # Print summary
        self.print_summary()
        
        return self.final_rent_roll

def main():
    """Main execution function"""
    generator = RentRollGenerator(verbose=True)
    rent_roll = generator.generate()
    
    print("\nRent roll generation complete!")
    print(f"Output saved to: {output_path}")
    
    return rent_roll

if __name__ == "__main__":
    main()