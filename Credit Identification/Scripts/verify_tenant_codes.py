#!/usr/bin/env python3
"""
Verify and double-check tenant codes - ensure we're getting the right column data.
"""

import pandas as pd
import numpy as np
from fuzzywuzzy import fuzz
import os

# Define paths
BASE_PATH = "/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI"
CREDIT_PATH = os.path.join(BASE_PATH, "Credit Identification")
DATA_PATH = os.path.join(BASE_PATH, "Data/Yardi_Tables")
REPORTS_PATH = os.path.join(CREDIT_PATH, "Reports")

def clean_company_name(name):
    """Clean company name for better matching"""
    if pd.isna(name):
        return ""
    
    import re
    name = str(name).upper()
    
    # Remove common suffixes
    suffixes = ['LLC', 'INC', 'CORP', 'CORPORATION', 'LP', 'LTD', 'COMPANY', 'CO', 
                'GROUP', 'HOLDINGS', 'PARTNERS', 'PARTNERSHIP', 'LLP', 'PLC']
    for suffix in suffixes:
        name = re.sub(r'\b' + suffix + r'\b\.?', '', name)
    
    # Remove punctuation and extra spaces
    name = re.sub(r'[^\w\s]', ' ', name)
    name = ' '.join(name.split())
    
    return name.strip()

def main():
    print("=" * 60)
    print("Verifying Tenant Code Data")
    print("=" * 60)
    
    # Load the missing credit scores report
    report_df = pd.read_csv(os.path.join(REPORTS_PATH, "missing_credit_scores_report.csv"))
    
    # Filter for tenants without customer codes
    no_customer_code = report_df[report_df['customer_code'].isna() | (report_df['customer_code'] == '')].copy()
    print(f"\nChecking {len(no_customer_code)} tenants without customer codes")
    
    # Load dim_commcustomer to check for tenant codes
    customers = pd.read_csv(os.path.join(DATA_PATH, "dim_commcustomer.csv"))
    
    # Check column names
    print("\nColumns in dim_commcustomer:")
    for i, col in enumerate(customers.columns):
        print(f"  {i}: {col}")
    
    # Check data types and sample values
    print("\nSample tenant codes from dim_commcustomer:")
    tenant_code_samples = customers['tenant code'].dropna().head(20)
    for code in tenant_code_samples:
        print(f"  {code}")
    
    # Check for any 'ml' prefixed codes
    print("\nChecking for 'ml' prefixed codes in tenant code column:")
    ml_codes = customers[customers['tenant code'].str.startswith('ml', na=False)]['tenant code'].unique()
    if len(ml_codes) > 0:
        print(f"  Found {len(ml_codes)} 'ml' prefixed codes")
        for code in ml_codes[:10]:
            print(f"    {code}")
    else:
        print("  No 'ml' prefixed codes found in tenant code column")
    
    print("\n" + "-" * 60)
    print("Detailed check for each tenant without customer code:")
    print("-" * 60)
    
    results = []
    
    for idx, row in no_customer_code.iterrows():
        tenant_name = row['tenant_name']
        print(f"\n{idx + 1}. {tenant_name}")
        
        # Clean the tenant name for matching
        clean_tenant = clean_company_name(tenant_name)
        
        # Search in dim_commcustomer - check ALL columns
        matches_found = []
        
        for _, cust_row in customers.iterrows():
            lessee_name = cust_row.get('lessee name', '')
            dba_name = cust_row.get('dba name', '')
            
            # Check lessee name
            if pd.notna(lessee_name):
                score = fuzz.token_sort_ratio(clean_tenant, clean_company_name(lessee_name))
                if score >= 80:
                    matches_found.append({
                        'match_type': 'lessee_name',
                        'matched_value': lessee_name,
                        'tenant_code': cust_row.get('tenant code', ''),
                        'tenant_id': cust_row.get('tenant id', ''),
                        'customer_id': cust_row.get('customer id', ''),
                        'property_id': cust_row.get('property id', ''),
                        'score': score
                    })
            
            # Check DBA name
            if pd.notna(dba_name):
                score = fuzz.token_sort_ratio(clean_tenant, clean_company_name(dba_name))
                if score >= 80:
                    matches_found.append({
                        'match_type': 'dba_name',
                        'matched_value': dba_name,
                        'tenant_code': cust_row.get('tenant code', ''),
                        'tenant_id': cust_row.get('tenant id', ''),
                        'customer_id': cust_row.get('customer id', ''),
                        'property_id': cust_row.get('property id', ''),
                        'score': score
                    })
        
        # Sort matches by score
        matches_found.sort(key=lambda x: x['score'], reverse=True)
        
        if matches_found:
            best_match = matches_found[0]
            print(f"  ✓ Found match:")
            print(f"    Match type: {best_match['match_type']}")
            print(f"    Matched to: {best_match['matched_value']} (score: {best_match['score']}%)")
            print(f"    Tenant Code: {best_match['tenant_code']}")
            print(f"    Tenant ID: {best_match['tenant_id']}")
            print(f"    Customer ID: {best_match['customer_id']}")
            print(f"    Property ID: {best_match['property_id']}")
            
            # Check if tenant code looks valid
            tc = best_match['tenant_code']
            if pd.notna(tc) and tc != '':
                if tc.startswith('t0'):
                    print(f"    ✓ Valid tenant code format")
                elif tc.startswith('ml'):
                    print(f"    ⚠️ WARNING: Unusual code format (starts with 'ml')")
                else:
                    print(f"    ⚠️ WARNING: Unexpected code format")
            
            result = {
                'tenant_name': tenant_name,
                'fund': row['fund'],
                'credit_score': row['faropoint_credit_score'],
                'tenant_code': best_match['tenant_code'],
                'tenant_id': best_match['tenant_id'],
                'customer_id': best_match['customer_id'],
                'property_id': best_match['property_id'],
                'match_type': best_match['match_type'],
                'matched_name': best_match['matched_value'],
                'match_score': best_match['score'],
                'code_format': 'Standard' if str(best_match['tenant_code']).startswith('t0') else 'Non-standard'
            }
        else:
            print(f"  ✗ No match found")
            result = {
                'tenant_name': tenant_name,
                'fund': row['fund'],
                'credit_score': row['faropoint_credit_score'],
                'tenant_code': '',
                'tenant_id': '',
                'customer_id': '',
                'property_id': '',
                'match_type': 'None',
                'matched_name': '',
                'match_score': 0,
                'code_format': 'N/A'
            }
        
        results.append(result)
    
    # Create results DataFrame
    results_df = pd.DataFrame(results)
    
    # Save detailed verification results
    output_file = os.path.join(REPORTS_PATH, "tenant_codes_verification_report.csv")
    results_df.to_csv(output_file, index=False)
    
    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    print(f"\nTotal tenants checked: {len(results_df)}")
    
    with_codes = results_df[results_df['tenant_code'] != '']
    print(f"Tenants with tenant codes: {len(with_codes)}")
    
    standard_codes = results_df[results_df['code_format'] == 'Standard']
    nonstandard_codes = results_df[results_df['code_format'] == 'Non-standard']
    
    print(f"  Standard format (t0xxxxx): {len(standard_codes)}")
    print(f"  Non-standard format: {len(nonstandard_codes)}")
    
    if len(nonstandard_codes) > 0:
        print("\nNon-standard tenant codes found:")
        for _, row in nonstandard_codes.iterrows():
            print(f"  • {row['tenant_name']}: {row['tenant_code']} (Tenant ID: {row['tenant_id']})")
    
    # Check if these might be tenant IDs instead
    print("\nChecking if non-standard codes might be tenant IDs...")
    for _, row in nonstandard_codes.iterrows():
        code = row['tenant_code']
        # Check if this value appears in tenant id column
        tid_matches = customers[customers['tenant id'] == code]
        if not tid_matches.empty:
            print(f"  ⚠️ {code} appears to be a tenant ID, not a tenant code!")
            actual_tenant_code = tid_matches.iloc[0]['tenant code']
            print(f"     Actual tenant code should be: {actual_tenant_code}")
    
    print(f"\nDetailed verification report saved to: {output_file}")
    
    return results_df

if __name__ == "__main__":
    main()