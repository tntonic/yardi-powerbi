#!/usr/bin/env python3
"""
Script to remove rows from credit upload CSV that already have credit scores in Yardi data.
"""

import pandas as pd
from pathlib import Path

# File paths
yardi_credit_file = Path("/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Data/Yardi_Tables/dim_fp_customercreditscorecustomdata.csv")
credit_upload_file = Path("/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Credit Identification/Tenant_Credit_Upload_Clean_Fixed.csv")
output_file = Path("/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Credit Identification/Tenant_Credit_Upload_No_Duplicates.csv")

# Read Yardi credit score data
print("Reading Yardi credit score data...")
yardi_df = pd.read_csv(yardi_credit_file)

# Extract customer codes that have credit scores
yardi_customer_codes = set(yardi_df['customer code'].dropna().unique())
print(f"Found {len(yardi_customer_codes)} unique customer codes with credit scores in Yardi")

# Read credit upload file
print("\nReading credit upload file...")
credit_df = pd.read_csv(credit_upload_file, header=None)

# Store header rows (first 3 rows)
header_rows = credit_df.iloc[:3]

# Process data rows (from row 4 onwards)
data_rows = credit_df.iloc[3:].copy()

# Extract customer codes from the data rows (column 1)
# The customer code is in column 1 (index 1) and format is like "c0000046"
data_rows['customer_code'] = data_rows.iloc[:, 1].astype(str)

# Count rows before filtering
total_rows_before = len(data_rows)

# Filter out rows where customer code exists in Yardi data
print(f"\nTotal rows before filtering: {total_rows_before}")
filtered_data = data_rows[~data_rows['customer_code'].isin(yardi_customer_codes)]

# Count rows after filtering
total_rows_after = len(filtered_data)
rows_removed = total_rows_before - total_rows_after

print(f"Total rows after filtering: {total_rows_after}")
print(f"Rows removed (already have Yardi credit scores): {rows_removed}")

# Drop the temporary customer_code column
filtered_data = filtered_data.drop('customer_code', axis=1)

# Combine header rows with filtered data
result_df = pd.concat([header_rows, filtered_data], ignore_index=True)

# Save to new file
print(f"\nSaving cleaned file to: {output_file}")
result_df.to_csv(output_file, index=False, header=False)

# Show which customer codes were removed
if rows_removed > 0:
    removed_codes = set(data_rows['customer_code']) & yardi_customer_codes
    print(f"\nRemoved customer codes that already have Yardi credit scores:")
    for code in sorted(removed_codes):
        # Find the company name for this code
        company_row = data_rows[data_rows['customer_code'] == code].iloc[0] if len(data_rows[data_rows['customer_code'] == code]) > 0 else None
        if company_row is not None:
            company_name = company_row.iloc[3]  # Company name is in column 3
            print(f"  - {code}: {company_name}")

print("\nProcess completed successfully!")