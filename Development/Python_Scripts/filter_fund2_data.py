#!/usr/bin/env python3
"""
Filter Yardi tables to extract only Fund 2 data for June 30, 2025
This creates smaller working files to avoid context overload
"""

import pandas as pd
import os
from datetime import datetime

# Define paths
base_path = "/Users/michaeltang/Documents/GitHub/BI/PBI v1.7"
yardi_path = os.path.join(base_path, "Data/Yardi_Tables")
output_path = os.path.join(base_path, "Data/Fund2_Filtered")

# Create output directory
os.makedirs(output_path, exist_ok=True)

# June 30, 2025 in Excel serial format
REPORT_DATE_EXCEL = 45838  # June 30, 2025
REPORT_DATE_STR = "6/30/2025"

def convert_date_to_excel_serial(date_str):
    """Convert MM/DD/YYYY string to Excel serial date"""
    if pd.isna(date_str) or date_str == '':
        return None
    try:
        # Parse the date
        date_obj = pd.to_datetime(date_str)
        # Excel epoch is December 30, 1899
        excel_epoch = pd.Timestamp('1899-12-30')
        # Calculate days since epoch
        return (date_obj - excel_epoch).days
    except:
        return None

def filter_amendments():
    """Filter amendments table for Fund 2 properties"""
    print("Filtering amendments table...")
    
    # Read the amendments table
    df = pd.read_csv(os.path.join(yardi_path, "dim_fp_amendmentsunitspropertytenant.csv"))
    
    # Filter for Fund 2 (property code starts with 'x')
    fund2_df = df[df['property code'].str.startswith('x', na=False)]
    
    # Convert date strings to Excel serial for consistency
    fund2_df['amendment start date serial'] = fund2_df['amendment start date'].apply(convert_date_to_excel_serial)
    fund2_df['amendment end date serial'] = fund2_df['amendment end date'].apply(convert_date_to_excel_serial)
    
    # Save filtered data
    output_file = os.path.join(output_path, "dim_fp_amendmentsunitspropertytenant_fund2.csv")
    fund2_df.to_csv(output_file, index=False)
    print(f"  Saved {len(fund2_df)} Fund 2 amendment records to {output_file}")
    
    # Print summary statistics
    print(f"  Status distribution: {fund2_df['amendment status'].value_counts().to_dict()}")
    print(f"  Type distribution: {fund2_df['amendment type'].value_counts().to_dict()}")
    
    return fund2_df

def filter_charge_schedule():
    """Filter charge schedule for Fund 2 properties and June 30, 2025"""
    print("\nFiltering charge schedule...")
    
    # Read the charge schedule table
    df = pd.read_csv(os.path.join(yardi_path, "dim_fp_amendmentchargeschedule.csv"))
    
    # Filter for Fund 2 (property code starts with 'x')
    fund2_df = df[df['property code'].str.startswith('x', na=False)]
    
    # Filter for charges active on June 30, 2025
    # from_date <= REPORT_DATE and (to_date >= REPORT_DATE or to_date is null)
    active_charges = fund2_df[
        (fund2_df['from date'] <= REPORT_DATE_EXCEL) & 
        ((fund2_df['to date'] >= REPORT_DATE_EXCEL) | fund2_df['to date'].isna())
    ]
    
    # Save all Fund 2 charges (for debugging)
    all_output_file = os.path.join(output_path, "dim_fp_amendmentchargeschedule_fund2_all.csv")
    fund2_df.to_csv(all_output_file, index=False)
    print(f"  Saved {len(fund2_df)} Fund 2 charge records (all) to {all_output_file}")
    
    # Save active charges for June 30, 2025
    active_output_file = os.path.join(output_path, "dim_fp_amendmentchargeschedule_fund2_active.csv")
    active_charges.to_csv(active_output_file, index=False)
    print(f"  Saved {len(active_charges)} active charge records for June 30, 2025")
    
    # Print summary
    print(f"  Charge code distribution: {active_charges['charge code'].value_counts().head(5).to_dict()}")
    
    return active_charges

def filter_properties():
    """Filter property table for Fund 2"""
    print("\nFiltering property table...")
    
    # Read the property table
    df = pd.read_csv(os.path.join(yardi_path, "dim_property.csv"))
    
    # Filter for Fund 2 (property code starts with 'x')
    fund2_df = df[df['property code'].str.startswith('x', na=False)]
    
    # Save filtered data
    output_file = os.path.join(output_path, "dim_property_fund2.csv")
    fund2_df.to_csv(output_file, index=False)
    print(f"  Saved {len(fund2_df)} Fund 2 properties to {output_file}")
    
    # Print summary
    print(f"  Active properties: {fund2_df['is active'].sum()}")
    
    return fund2_df

def filter_units():
    """Filter units table for Fund 2 properties"""
    print("\nFiltering units table...")
    
    # First get Fund 2 property IDs
    prop_df = pd.read_csv(os.path.join(yardi_path, "dim_property.csv"))
    fund2_prop_ids = prop_df[prop_df['property code'].str.startswith('x', na=False)]['property id'].tolist()
    
    # Read units table
    df = pd.read_csv(os.path.join(yardi_path, "dim_unit.csv"))
    
    # Filter for Fund 2 properties
    fund2_df = df[df['property id'].isin(fund2_prop_ids)]
    
    # Save filtered data
    output_file = os.path.join(output_path, "dim_unit_fund2.csv")
    fund2_df.to_csv(output_file, index=False)
    print(f"  Saved {len(fund2_df)} Fund 2 units to {output_file}")
    
    return fund2_df

def filter_tenants():
    """Extract unique tenants from amendments for Fund 2"""
    print("\nExtracting tenant information...")
    
    # Read the filtered amendments
    amend_df = pd.read_csv(os.path.join(output_path, "dim_fp_amendmentsunitspropertytenant_fund2.csv"))
    
    # Get unique tenants
    tenants = amend_df[['tenant hmy', 'tenant id']].drop_duplicates()
    
    # Save tenant list
    output_file = os.path.join(output_path, "tenants_fund2.csv")
    tenants.to_csv(output_file, index=False)
    print(f"  Saved {len(tenants)} unique tenants to {output_file}")
    
    return tenants

def create_summary():
    """Create a summary of the filtered data"""
    print("\nCreating data summary...")
    
    summary = {
        "Report Date": REPORT_DATE_STR,
        "Report Date (Excel Serial)": REPORT_DATE_EXCEL,
        "Tables Filtered": [],
        "Record Counts": {}
    }
    
    # Check each filtered file
    files = [
        ("Amendments", "dim_fp_amendmentsunitspropertytenant_fund2.csv"),
        ("Charge Schedule (All)", "dim_fp_amendmentchargeschedule_fund2_all.csv"),
        ("Charge Schedule (Active)", "dim_fp_amendmentchargeschedule_fund2_active.csv"),
        ("Properties", "dim_property_fund2.csv"),
        ("Units", "dim_unit_fund2.csv"),
        ("Tenants", "tenants_fund2.csv")
    ]
    
    for name, filename in files:
        filepath = os.path.join(output_path, filename)
        if os.path.exists(filepath):
            df = pd.read_csv(filepath)
            summary["Tables Filtered"].append(name)
            summary["Record Counts"][name] = len(df)
    
    # Save summary
    summary_file = os.path.join(output_path, "filter_summary.txt")
    with open(summary_file, 'w') as f:
        f.write("Fund 2 Data Filtering Summary\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Report Date: {summary['Report Date']}\n")
        f.write(f"Report Date (Excel Serial): {summary['Report Date (Excel Serial)']}\n\n")
        f.write("Record Counts:\n")
        for name, count in summary["Record Counts"].items():
            f.write(f"  {name}: {count:,} records\n")
    
    print(f"\nSummary saved to {summary_file}")
    
    return summary

def main():
    """Main execution function"""
    print("=" * 60)
    print("FILTERING FUND 2 DATA FOR JUNE 30, 2025")
    print("=" * 60)
    
    # Filter each table
    filter_amendments()
    filter_charge_schedule()
    filter_properties()
    filter_units()
    filter_tenants()
    
    # Create summary
    summary = create_summary()
    
    print("\n" + "=" * 60)
    print("FILTERING COMPLETE")
    print("=" * 60)
    print(f"Filtered data saved to: {output_path}")
    
    return summary

if __name__ == "__main__":
    main()