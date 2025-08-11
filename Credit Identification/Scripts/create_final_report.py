#!/usr/bin/env python3
"""
Create final comprehensive report with both customer codes and tenant codes for all tenants missing credit scores.
"""

import pandas as pd
import os

# Define paths
BASE_PATH = "/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI"
CREDIT_PATH = os.path.join(BASE_PATH, "Credit Identification")
REPORTS_PATH = os.path.join(CREDIT_PATH, "Reports")

def main():
    print("=" * 60)
    print("Creating Final Comprehensive Report")
    print("=" * 60)
    
    # Load the original missing credit scores report
    missing_report = pd.read_csv(os.path.join(REPORTS_PATH, "missing_credit_scores_report.csv"))
    
    # Load the tenant codes check report
    tenant_codes_report = pd.read_csv(os.path.join(REPORTS_PATH, "tenant_codes_check_report.csv"))
    
    # Create a mapping of tenant names to their codes
    tenant_code_map = {}
    customer_id_map = {}
    
    for _, row in tenant_codes_report.iterrows():
        tenant_name = row['tenant_name']
        if pd.notna(row.get('tenant_code')) and row['tenant_code'] != '':
            tenant_code_map[tenant_name] = row['tenant_code']
        if pd.notna(row.get('customer_id')) and row['customer_id'] != '':
            customer_id_map[tenant_name] = row['customer_id']
    
    # Create the final comprehensive report
    final_data = []
    
    for _, row in missing_report.iterrows():
        tenant_name = row['tenant_name']
        
        # Determine which codes are available
        has_customer_code = pd.notna(row['customer_code']) and row['customer_code'] != ''
        tenant_code = tenant_code_map.get(tenant_name, '')
        customer_id = customer_id_map.get(tenant_name, '')
        
        # If no customer code but has customer_id from tenant table, note it
        if not has_customer_code and customer_id:
            needs_customer_code = 'Yes - Has Customer ID'
        elif not has_customer_code:
            needs_customer_code = 'Yes - No Customer ID'
        else:
            needs_customer_code = 'No'
        
        final_record = {
            'tenant_name': tenant_name,
            'credit_score': row['faropoint_credit_score'],
            'fund': row['fund'],
            'property': row['property'],
            'market': row['market'],
            'customer_code': row['customer_code'] if has_customer_code else '',
            'tenant_code': tenant_code,
            'customer_id': customer_id if customer_id else '',
            'needs_customer_code_assignment': needs_customer_code,
            'action_required': 'Add Credit Score to Yardi'
        }
        
        final_data.append(final_record)
    
    # Create DataFrame and sort
    final_df = pd.DataFrame(final_data)
    final_df = final_df.sort_values(['fund', 'tenant_name'])
    
    # Save the comprehensive report
    output_file = os.path.join(REPORTS_PATH, "FINAL_missing_credit_scores_with_all_codes.csv")
    final_df.to_csv(output_file, index=False)
    
    # Print summary
    print("\n" + "=" * 60)
    print("FINAL SUMMARY - TENANTS NEEDING CREDIT SCORES IN YARDI")
    print("=" * 60)
    
    print(f"\nTotal tenants needing credit scores added: {len(final_df)}")
    print(f"  Fund 2: {len(final_df[final_df['fund'] == 'Fund 2'])}")
    print(f"  Fund 3: {len(final_df[final_df['fund'] == 'Fund 3'])}")
    
    print("\nCode Status:")
    has_both = final_df[(final_df['customer_code'] != '') & (final_df['tenant_code'] != '')]
    print(f"  Has both customer code & tenant code: {len(has_both)}")
    
    has_customer_only = final_df[(final_df['customer_code'] != '') & (final_df['tenant_code'] == '')]
    print(f"  Has customer code only: {len(has_customer_only)}")
    
    has_tenant_only = final_df[(final_df['customer_code'] == '') & (final_df['tenant_code'] != '')]
    print(f"  Has tenant code only: {len(has_tenant_only)}")
    
    has_neither = final_df[(final_df['customer_code'] == '') & (final_df['tenant_code'] == '')]
    print(f"  Has neither code: {len(has_neither)}")
    
    # Show tenants that need customer codes created
    needs_codes = final_df[final_df['needs_customer_code_assignment'] != 'No']
    if not needs_codes.empty:
        print("\nTenants needing customer code assignment:")
        for _, row in needs_codes.iterrows():
            if row['customer_id']:
                print(f"  • {row['tenant_name']} - Has Customer ID: {row['customer_id']} (can generate c-code)")
            else:
                print(f"  • {row['tenant_name']} - No Customer ID (may need new customer record)")
    
    print(f"\nFinal report saved to: {output_file}")
    
    # Display sample
    print("\nSample of final report (first 5 records):")
    display_cols = ['tenant_name', 'credit_score', 'customer_code', 'tenant_code', 'fund']
    print(final_df[display_cols].head().to_string())
    
    return final_df

if __name__ == "__main__":
    main()