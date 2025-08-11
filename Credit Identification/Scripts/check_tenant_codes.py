#!/usr/bin/env python3
"""
Check if tenants without customer codes have tenant codes assigned in Yardi.
"""

import pandas as pd
import numpy as np
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
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
    print("Checking Tenant Codes for Tenants Without Customer Codes")
    print("=" * 60)
    
    # Load the missing credit scores report
    report_df = pd.read_csv(os.path.join(REPORTS_PATH, "missing_credit_scores_report.csv"))
    
    # Filter for tenants without customer codes
    no_customer_code = report_df[report_df['customer_code'].isna() | (report_df['customer_code'] == '')].copy()
    print(f"\nFound {len(no_customer_code)} tenants without customer codes")
    
    # Load dim_commcustomer to check for tenant codes
    customers = pd.read_csv(os.path.join(DATA_PATH, "dim_commcustomer.csv"))
    print(f"Loaded {len(customers)} customer records from dim_commcustomer")
    
    # Load amendments table for additional tenant info
    amendments = pd.read_csv(os.path.join(DATA_PATH, "dim_fp_amendmentsunitspropertytenant.csv"))
    print(f"Loaded {len(amendments)} amendment records")
    
    print("\n" + "-" * 60)
    print("Searching for tenant codes...")
    print("-" * 60)
    
    results = []
    
    for idx, row in no_customer_code.iterrows():
        tenant_name = row['tenant_name']
        print(f"\n{idx + 1}. {tenant_name}")
        
        # Clean the tenant name for matching
        clean_tenant = clean_company_name(tenant_name)
        
        # Search in dim_commcustomer
        best_match = None
        best_score = 0
        best_tenant_code = None
        best_customer_id = None
        
        for _, cust_row in customers.iterrows():
            lessee_name = cust_row.get('lessee name', '')
            dba_name = cust_row.get('dba name', '')
            
            # Check lessee name
            if pd.notna(lessee_name):
                score = fuzz.token_sort_ratio(clean_tenant, clean_company_name(lessee_name))
                if score > best_score:
                    best_score = score
                    best_match = lessee_name
                    best_tenant_code = cust_row.get('tenant code', '')
                    best_customer_id = cust_row.get('customer id', '')
            
            # Check DBA name
            if pd.notna(dba_name):
                score = fuzz.token_sort_ratio(clean_tenant, clean_company_name(dba_name))
                if score > best_score:
                    best_score = score
                    best_match = dba_name
                    best_tenant_code = cust_row.get('tenant code', '')
                    best_customer_id = cust_row.get('customer id', '')
        
        # Also check amendments table for tenant name
        amendment_match = None
        amendment_score = 0
        
        for _, amend_row in amendments.iterrows():
            amend_tenant = amend_row.get('tenant name', '')
            if pd.notna(amend_tenant):
                score = fuzz.token_sort_ratio(clean_tenant, clean_company_name(amend_tenant))
                if score > amendment_score:
                    amendment_score = score
                    amendment_match = amend_tenant
        
        # Determine if we found a good match (threshold of 80%)
        has_tenant_code = best_score >= 80 and pd.notna(best_tenant_code) and best_tenant_code != ''
        
        result = {
            'tenant_name': tenant_name,
            'fund': row['fund'],
            'property': row['property'],
            'credit_score': row['faropoint_credit_score'],
            'tenant_code_found': 'Yes' if has_tenant_code else 'No',
            'tenant_code': best_tenant_code if has_tenant_code else '',
            'customer_id': best_customer_id if best_score >= 80 else '',
            'matched_name': best_match if best_score >= 80 else '',
            'match_confidence': best_score if best_score >= 80 else 0,
            'amendment_match': amendment_match if amendment_score >= 80 else '',
            'amendment_confidence': amendment_score if amendment_score >= 80 else 0
        }
        
        results.append(result)
        
        if has_tenant_code:
            print(f"  ✓ Found tenant code: {best_tenant_code}")
            print(f"    Matched to: {best_match} (confidence: {best_score}%)")
            if pd.notna(best_customer_id) and best_customer_id != '':
                print(f"    Customer ID: {best_customer_id}")
        else:
            print(f"  ✗ No tenant code found")
            if best_score > 0:
                print(f"    Best match: {best_match} (confidence: {best_score}% - below threshold)")
            if amendment_score >= 80:
                print(f"    Found in amendments: {amendment_match} (confidence: {amendment_score}%)")
    
    # Create results DataFrame
    results_df = pd.DataFrame(results)
    
    # Save detailed results
    output_file = os.path.join(REPORTS_PATH, "tenant_codes_check_report.csv")
    results_df.to_csv(output_file, index=False)
    
    # Summary statistics
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total tenants without customer codes: {len(no_customer_code)}")
    print(f"Tenants with tenant codes found: {len(results_df[results_df['tenant_code_found'] == 'Yes'])}")
    print(f"Tenants without any codes: {len(results_df[results_df['tenant_code_found'] == 'No'])}")
    
    # Show tenants with codes
    with_codes = results_df[results_df['tenant_code_found'] == 'Yes']
    if not with_codes.empty:
        print("\nTenants WITH tenant codes:")
        for _, row in with_codes.iterrows():
            print(f"  • {row['tenant_name']}: {row['tenant_code']} (Customer ID: {row['customer_id']})")
    
    # Show tenants without any codes
    without_codes = results_df[results_df['tenant_code_found'] == 'No']
    if not without_codes.empty:
        print("\nTenants WITHOUT any codes (need to be created):")
        for _, row in without_codes.iterrows():
            status = ""
            if row['amendment_confidence'] > 0:
                status = f" [Found in amendments: {row['amendment_confidence']}% match]"
            print(f"  • {row['tenant_name']} ({row['fund']}){status}")
    
    print(f"\nDetailed report saved to: {output_file}")
    
    return results_df

if __name__ == "__main__":
    main()