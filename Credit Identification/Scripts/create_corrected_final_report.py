#!/usr/bin/env python3
"""
Create corrected final report with proper understanding of both tenant code formats.
"""

import pandas as pd
import os

# Define paths
BASE_PATH = "/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI"
CREDIT_PATH = os.path.join(BASE_PATH, "Credit Identification")
REPORTS_PATH = os.path.join(CREDIT_PATH, "Reports")

def main():
    print("=" * 60)
    print("Creating Corrected Final Report with All Code Formats")
    print("=" * 60)
    
    # Load the verification report with correct data
    verification_df = pd.read_csv(os.path.join(REPORTS_PATH, "tenant_codes_verification_report.csv"))
    
    # Load the original missing credit scores report
    missing_report = pd.read_csv(os.path.join(REPORTS_PATH, "missing_credit_scores_report.csv"))
    
    # Create mapping for tenant codes and customer IDs
    tenant_info_map = {}
    for _, row in verification_df.iterrows():
        tenant_name = row['tenant_name']
        tenant_info_map[tenant_name] = {
            'tenant_code': row['tenant_code'] if pd.notna(row['tenant_code']) else '',
            'tenant_id': row['tenant_id'] if pd.notna(row['tenant_id']) else '',
            'customer_id': row['customer_id'] if pd.notna(row['customer_id']) else '',
            'code_format': row['code_format'] if pd.notna(row['code_format']) else ''
        }
    
    # Create the final comprehensive report
    final_data = []
    
    for _, row in missing_report.iterrows():
        tenant_name = row['tenant_name']
        
        # Get tenant info if available
        tenant_info = tenant_info_map.get(tenant_name, {})
        tenant_code = tenant_info.get('tenant_code', '')
        tenant_id = tenant_info.get('tenant_id', '')
        customer_id = tenant_info.get('customer_id', '')
        code_format = tenant_info.get('code_format', '')
        
        # Determine customer code status
        has_customer_code = pd.notna(row['customer_code']) and row['customer_code'] != ''
        
        # Determine code completeness
        if has_customer_code and tenant_code:
            code_status = 'Complete - Has Both Codes'
        elif has_customer_code and not tenant_code:
            code_status = 'Has Customer Code Only'
        elif not has_customer_code and tenant_code:
            if customer_id:
                code_status = 'Has Tenant Code + Customer ID (needs c-code)'
            else:
                code_status = 'Has Tenant Code Only (needs customer record)'
        else:
            code_status = 'Missing Both Codes'
        
        final_record = {
            'tenant_name': tenant_name,
            'credit_score': row['faropoint_credit_score'],
            'fund': row['fund'],
            'property': row['property'],
            'market': row['market'],
            'customer_code': row['customer_code'] if has_customer_code else '',
            'tenant_code': tenant_code,
            'tenant_code_format': code_format if tenant_code else 'N/A',
            'tenant_id': tenant_id,
            'customer_id': customer_id,
            'code_status': code_status,
            'action_required': 'Add Credit Score to Yardi'
        }
        
        final_data.append(final_record)
    
    # Create DataFrame and sort
    final_df = pd.DataFrame(final_data)
    final_df = final_df.sort_values(['fund', 'tenant_name'])
    
    # Save the comprehensive report
    output_file = os.path.join(REPORTS_PATH, "FINAL_CORRECTED_missing_credit_scores_all_codes.csv")
    final_df.to_csv(output_file, index=False)
    
    # Print summary
    print("\n" + "=" * 60)
    print("CORRECTED FINAL SUMMARY - ALL TENANT CODES ARE VALID")
    print("=" * 60)
    
    print(f"\nTotal tenants needing credit scores added: {len(final_df)}")
    print(f"  Fund 2: {len(final_df[final_df['fund'] == 'Fund 2'])}")
    print(f"  Fund 3: {len(final_df[final_df['fund'] == 'Fund 3'])}")
    
    print("\n" + "-" * 60)
    print("TENANT CODE FORMATS (Both are valid in Yardi):")
    print("-" * 60)
    
    standard_format = final_df[final_df['tenant_code_format'] == 'Standard']
    nonstandard_format = final_df[final_df['tenant_code_format'] == 'Non-standard']
    no_code = final_df[final_df['tenant_code'] == '']
    
    print(f"  Standard format (t0xxxxx): {len(standard_format)} tenants")
    print(f"  ML format (mlXXXXXX): {len(nonstandard_format)} tenants")
    print(f"  No tenant code: {len(no_code)} tenants")
    
    print("\n" + "-" * 60)
    print("CODE COMPLETENESS STATUS:")
    print("-" * 60)
    
    for status in final_df['code_status'].unique():
        count = len(final_df[final_df['code_status'] == status])
        print(f"  {status}: {count}")
    
    # Show breakdown by tenant code format
    print("\n" + "-" * 60)
    print("TENANTS BY CODE FORMAT:")
    print("-" * 60)
    
    print("\nStandard Format (t0xxxxx):")
    for _, row in standard_format.iterrows():
        ccode = f" + {row['customer_code']}" if row['customer_code'] else " (no c-code)"
        print(f"  • {row['tenant_name']}: {row['tenant_code']}{ccode}")
    
    print("\nML Format (mlXXXXXX) - Valid Alternative Format:")
    for _, row in nonstandard_format.iterrows():
        ccode = f" + {row['customer_code']}" if row['customer_code'] else " (no c-code)"
        cust_id = f" [Customer ID: {row['customer_id']}]" if row['customer_id'] else ""
        print(f"  • {row['tenant_name']}: {row['tenant_code']}{ccode}{cust_id}")
    
    # Show who needs customer codes
    needs_customer_codes = final_df[
        (final_df['customer_code'] == '') & 
        (final_df['customer_id'] != '') & 
        (pd.notna(final_df['customer_id']))
    ]
    
    if not needs_customer_codes.empty:
        print("\n" + "-" * 60)
        print("TENANTS THAT CAN BE ASSIGNED CUSTOMER CODES:")
        print("-" * 60)
        for _, row in needs_customer_codes.iterrows():
            print(f"  • {row['tenant_name']} - Customer ID: {row['customer_id']} → Generate c-code")
    
    print(f"\nCorrected final report saved to: {output_file}")
    
    # Display summary table
    print("\n" + "-" * 60)
    print("SUMMARY TABLE:")
    print("-" * 60)
    summary_cols = ['tenant_name', 'credit_score', 'customer_code', 'tenant_code', 'tenant_code_format']
    print(final_df[summary_cols].head(10).to_string())
    
    return final_df

if __name__ == "__main__":
    main()