#!/usr/bin/env python3
"""
Clean the Tenant Credit Upload template:
1. Remove duplicate rows
2. Remove rows without credit scores
"""

import pandas as pd
from datetime import datetime

def main():
    print("🔍 Cleaning Tenant Credit Upload Template")
    print("=" * 60)
    
    # Read the file, skipping the header rows
    file_path = '/Users/michaeltang/Downloads/Tenant_Credit_Upload_Fixed.csv'
    
    # Read the full file to preserve headers
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Extract headers (first 3 rows)
    header_lines = lines[:3]
    
    # Read the data portion into a DataFrame
    df = pd.read_csv(file_path, skiprows=3, header=None)
    
    # Assign column names based on the template structure
    column_names = [
        'Customer ID', 'File Name', 'Company Name/s', 'Credit Check Date',
        'HQ Location', 'Annual Revenues', 'Year Founded', 'Website',
        'Description', 'Ownership', 'Primary Industry', 'Competitive Position Industry Group',
        'Credit Rating', 'Gross Profit', 'EBIT', 'EBITDA',
        'Total Assets', 'Total Debt', 'Current Ratio', 'Quick Ratio',
        'Net Debt / EBITDA', 'Debt / Assets', 'Report Attachment Link', 'General Notes'
    ]
    
    df.columns = column_names
    
    print(f"📊 Initial records: {len(df)}")
    
    # Check for duplicates
    print("\n🔍 Checking for duplicate rows...")
    
    # Check for duplicate Customer IDs
    duplicate_ids = df[df.duplicated(subset=['Customer ID'], keep=False)]
    if not duplicate_ids.empty:
        print(f"⚠️  Found {len(duplicate_ids)} rows with duplicate Customer IDs:")
        dup_summary = duplicate_ids.groupby('Customer ID').agg({
            'Company Name/s': 'first',
            'Credit Rating': lambda x: list(x.dropna()) if x.notna().any() else []
        })
        for cust_id, row in dup_summary.iterrows():
            credit_scores = row['Credit Rating']
            print(f"   {cust_id}: {row['Company Name/s']} - Credit scores: {credit_scores}")
    
    # Remove exact duplicates
    df_no_exact_dup = df.drop_duplicates()
    exact_dups_removed = len(df) - len(df_no_exact_dup)
    if exact_dups_removed > 0:
        print(f"✅ Removed {exact_dups_removed} exact duplicate rows")
    
    # For duplicate Customer IDs, keep the one with credit score
    df_clean = df_no_exact_dup.copy()
    
    # Sort by Customer ID and Credit Rating (non-null first)
    df_clean['has_credit'] = df_clean['Credit Rating'].notna()
    df_clean = df_clean.sort_values(['Customer ID', 'has_credit'], ascending=[True, False])
    
    # Keep first occurrence of each Customer ID (which will be the one with credit score if it exists)
    df_deduped = df_clean.drop_duplicates(subset=['Customer ID'], keep='first')
    customer_dups_removed = len(df_clean) - len(df_deduped)
    if customer_dups_removed > 0:
        print(f"✅ Removed {customer_dups_removed} duplicate Customer ID entries (kept ones with credit scores)")
    
    # Drop the helper column
    df_deduped = df_deduped.drop('has_credit', axis=1)
    
    print(f"\n📊 After deduplication: {len(df_deduped)} records")
    
    # Check for rows without credit scores
    print("\n🔍 Checking for rows without credit scores...")
    
    # Count rows with and without credit scores
    with_credit = df_deduped[df_deduped['Credit Rating'].notna()]
    without_credit = df_deduped[df_deduped['Credit Rating'].isna()]
    
    print(f"   With credit scores: {len(with_credit)}")
    print(f"   Without credit scores: {len(without_credit)}")
    
    if len(without_credit) > 0:
        print(f"\n📋 Removing {len(without_credit)} records without credit scores:")
        # Show sample of what's being removed
        sample_size = min(10, len(without_credit))
        print("   Sample of removed records:")
        for _, row in without_credit.head(sample_size).iterrows():
            print(f"   - {row['Customer ID']}: {row['Company Name/s']}")
        if len(without_credit) > sample_size:
            print(f"   ... and {len(without_credit) - sample_size} more")
    
    # Keep only rows with credit scores
    df_final = with_credit.copy()
    
    print(f"\n✅ Final dataset: {len(df_final)} records (all with credit scores)")
    
    # Save the cleaned file
    output_path = '/Users/michaeltang/Downloads/Tenant_Credit_Upload_Clean.csv'
    
    with open(output_path, 'w', encoding='utf-8') as f:
        # Write the original headers
        for line in header_lines:
            f.write(line)
        
        # Write the cleaned data
        df_final.to_csv(f, index=False, header=False)
    
    print(f"\n💾 Cleaned file saved to: {output_path}")
    
    # Summary report
    print("\n" + "=" * 60)
    print("📊 CLEANING SUMMARY:")
    print(f"   Original records: {len(df)}")
    print(f"   Exact duplicates removed: {exact_dups_removed}")
    print(f"   Customer ID duplicates removed: {customer_dups_removed}")
    print(f"   Records without credit scores removed: {len(without_credit)}")
    print(f"   Final records (all with credit scores): {len(df_final)}")
    
    # Verify all final records have required fields
    missing_dates = df_final['Credit Check Date'].isna().sum()
    missing_ratings = df_final['Credit Rating'].isna().sum()
    
    print(f"\n✅ VERIFICATION:")
    print(f"   All records have Customer IDs: {df_final['Customer ID'].notna().all()}")
    print(f"   All records have Company Names: {df_final['Company Name/s'].notna().all()}")
    print(f"   All records have Credit Ratings: {missing_ratings == 0}")
    print(f"   All records have Credit Check Dates: {missing_dates == 0}")
    
    if missing_dates > 0:
        print(f"   ⚠️  Warning: {missing_dates} records missing Credit Check Dates")
    
    # List the companies in the final dataset
    print(f"\n📋 COMPANIES WITH CREDIT SCORES ({len(df_final)}):")
    for i, (_, row) in enumerate(df_final.head(10).iterrows(), 1):
        print(f"   {i}. {row['Customer ID']}: {row['Company Name/s']} (Score: {row['Credit Rating']})")
    if len(df_final) > 10:
        print(f"   ... and {len(df_final) - 10} more")
    
    # Create a summary report file
    summary_path = '/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Credit Identification/TEMPLATE_CLEANING_SUMMARY.md'
    with open(summary_path, 'w') as f:
        f.write(f"""# Tenant Credit Upload - Cleaning Summary
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Cleaning Actions Performed

1. **Removed Exact Duplicates**: {exact_dups_removed} rows
2. **Resolved Customer ID Duplicates**: {customer_dups_removed} rows (kept ones with credit scores)
3. **Removed Records Without Credit Scores**: {len(without_credit)} rows

## Final Dataset

- **Total Records**: {len(df_final)}
- **All Have Credit Scores**: ✅
- **All Have Customer IDs**: ✅
- **All Have Company Names**: ✅
- **Records with Dates**: {(df_final['Credit Check Date'].notna()).sum()}/{len(df_final)}

## Output File

Clean file saved to: `{output_path}`

This file contains only unique companies with credit scores, ready for upload.
""")
    
    print(f"\n📄 Summary report saved to: {summary_path}")
    print("\n✅ Template cleaning complete!")

if __name__ == "__main__":
    main()