import pandas as pd
import numpy as np
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

# Read the original file with customer_id and tenant_id (LEFT table)
df_left = pd.read_csv('new_tenants_fund2_fund3_since_2025_populated.csv')

# Read the credit evaluation file (RIGHT table)  
df_credit = pd.read_csv('tenant_credit_evaluation_final.csv')

print("="*70)
print("PERFORMING LEFT JOIN WITH CUSTOMER/TENANT ID PRESERVATION")
print("="*70)

# Check that we have the ID columns
print("\n📋 Original file columns check:")
print(f"  - customer_id present: {'customer_id' in df_left.columns}")
print(f"  - tenant_id present: {'tenant_id' in df_left.columns}")
print(f"  - Total rows: {len(df_left)}")

# Load the previous matching results to use the same logic
df_previous = pd.read_csv('fully_populated_credit_scores.csv')

# Create a mapping of tenant names to their best credit match
tenant_to_credit_map = {}
for idx, row in df_previous.iterrows():
    if pd.notna(row['matched_value']) and pd.notna(row['tenant_name']):
        tenant_to_credit_map[row['tenant_name']] = {
            'matched_value': row['matched_value'],
            'match_score': row['match_score'],
            'match_method': row['match_method']
        }

print(f"\n✅ Using {len(tenant_to_credit_map)} previously established matches")

# Start with the LEFT table (preserve ALL rows and ALL columns)
df_result = df_left.copy()

# Add matching columns
df_result['matched_credit_name'] = None
df_result['match_score'] = 0
df_result['match_method'] = 'No match'

# Add all credit evaluation columns with 'credit_' prefix
for col in df_credit.columns:
    df_result[f'credit_{col}'] = None

# Apply matches based on tenant name
matched_count = 0
for idx, row in df_result.iterrows():
    tenant_name = row['tenant_name']
    
    if pd.notna(tenant_name) and tenant_name in tenant_to_credit_map:
        # We have a match for this tenant
        match_info = tenant_to_credit_map[tenant_name]
        matched_credit_name = match_info['matched_value']
        
        # Update match info
        df_result.loc[idx, 'matched_credit_name'] = matched_credit_name
        df_result.loc[idx, 'match_score'] = match_info['match_score']
        df_result.loc[idx, 'match_method'] = match_info['match_method']
        
        # Find the credit data for this match
        credit_matches = df_credit[df_credit['tenant_name'] == matched_credit_name]
        if not credit_matches.empty:
            credit_row = credit_matches.iloc[0]
            # Populate all credit fields
            for col in df_credit.columns:
                df_result.loc[idx, f'credit_{col}'] = credit_row[col]
            matched_count += 1

print(f"\n📊 Join Results:")
print(f"  - Total rows preserved: {len(df_result)}")
print(f"  - Rows with credit data: {matched_count}")
print(f"  - Rows without matches: {len(df_result) - matched_count}")

# Verify ID preservation
print(f"\n✅ ID Preservation Check:")
customer_ids_preserved = df_result['customer_id'].notna().sum()
tenant_ids_preserved = df_result['tenant_id'].notna().sum()
print(f"  - Customer IDs preserved: {customer_ids_preserved}/{len(df_result)}")
print(f"  - Tenant IDs preserved: {tenant_ids_preserved}/{len(df_result)}")

# Save the final result
output_file = 'final_tenant_credit_with_ids.csv'
df_result.to_csv(output_file, index=False)

# Create a summary report
print("\n" + "="*70)
print("SUMMARY REPORT")
print("="*70)

# Show sample of data with IDs and credit scores
print("\n📋 Sample of joined data (first 10 rows with credit scores):")
sample = df_result[df_result['credit_credit_score'].notna()].head(10)
if not sample.empty:
    print("\n{:<12} {:<12} {:<35} {:<7} {:<10}".format(
        "Customer ID", "Tenant ID", "Tenant Name", "Score", "Rating"
    ))
    print("-"*80)
    for idx, row in sample.iterrows():
        cust_id = row['customer_id'] if pd.notna(row['customer_id']) else 'N/A'
        tenant_id = row['tenant_id'] if pd.notna(row['tenant_id']) else 'N/A'
        score = row['credit_credit_score'] if pd.notna(row['credit_credit_score']) else 'N/A'
        rating = row['credit_credit_rating'] if pd.notna(row['credit_credit_rating']) else 'N/A'
        print("{:<12} {:<12} {:<35} {:<7} {:<10}".format(
            str(cust_id)[:11],
            str(tenant_id)[:11],
            str(row['tenant_name'])[:34],
            str(score)[:6],
            str(rating)[:9]
        ))

# Risk analysis with IDs
print("\n⚠️  HIGH RISK TENANTS (Score ≤ 3.0) with IDs:")
print("-"*70)
high_risk = df_result[
    (df_result['credit_credit_score'] <= 3.0) & 
    (df_result['credit_credit_score'].notna())
].sort_values('credit_credit_score')

if not high_risk.empty:
    for idx, row in high_risk.iterrows():
        cust_id = row['customer_id'] if pd.notna(row['customer_id']) else 'N/A'
        tenant_id = row['tenant_id'] if pd.notna(row['tenant_id']) else 'N/A'
        print(f"  Customer: {cust_id:<10} | Tenant: {tenant_id:<10} | {row['tenant_name'][:30]:<30}")
        print(f"    → Credit Score: {row['credit_credit_score']:.1f} | Fund: {row['fund']}")

# Fund-level summary
print("\n📊 SUMMARY BY FUND:")
print("-"*70)
for fund in df_result['fund'].dropna().unique():
    fund_data = df_result[df_result['fund'] == fund]
    total = len(fund_data)
    with_scores = fund_data['credit_credit_score'].notna().sum()
    if with_scores > 0:
        avg_score = fund_data['credit_credit_score'].mean()
        print(f"Fund {int(fund)}: {with_scores}/{total} with scores ({100*with_scores/total:.1f}%), Avg Score: {avg_score:.2f}")
    else:
        print(f"Fund {int(fund)}: {with_scores}/{total} with scores ({100*with_scores/total:.1f}%)")

print("\n" + "="*70)
print(f"✅ OUTPUT FILE: {output_file}")
print("="*70)
print("This file contains:")
print("  • All original columns including customer_id and tenant_id")
print("  • Matched credit evaluation data where available")
print("  • Match confidence scores and methods")
print("  • All 149 original rows preserved (true LEFT JOIN)")
print("="*70)