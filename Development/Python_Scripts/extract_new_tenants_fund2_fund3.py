#!/usr/bin/env python3
"""
Extract new tenants in Fund 2 and Fund 3 since January 1, 2025
Exports to CSV with customer id, tenant id, property address, naics, lease id, credit score, tenant risk
"""

import pandas as pd
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Define paths
base_path = "/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI"
data_path = os.path.join(base_path, "Data/Yardi_Tables")
output_path = os.path.join(base_path, "Data")

# Define date thresholds
NEW_TENANT_START_DATE = pd.Timestamp('2025-01-01')
EXCEL_EPOCH = pd.Timestamp('1899-12-30')
NEW_TENANT_EXCEL_SERIAL = (NEW_TENANT_START_DATE - EXCEL_EPOCH).days  # 45658 for Jan 1, 2025

def excel_serial_to_datetime(serial):
    """Convert Excel serial date to datetime"""
    if pd.isna(serial):
        return pd.NaT
    try:
        return EXCEL_EPOCH + pd.Timedelta(days=int(serial))
    except:
        return pd.NaT

def load_data():
    """Load required data tables with limited rows for fact tables"""
    print("Loading data tables...")
    
    # Load dimension tables (full)
    properties = pd.read_csv(os.path.join(data_path, "dim_property.csv"))
    customers = pd.read_csv(os.path.join(data_path, "dim_commcustomer.csv"))
    amendments = pd.read_csv(os.path.join(data_path, "dim_fp_amendmentsunitspropertytenant.csv"))
    
    # Load fact table with row limit
    leasing_activity = pd.read_csv(os.path.join(data_path, "fact_leasingactivity.csv"), nrows=10000)
    
    # Load credit score and parent mapping tables
    try:
        credit_scores = pd.read_csv(os.path.join(data_path, "dim_fp_customercreditscorecustomdata.csv"))
        print(f"  Credit Scores: {len(credit_scores)} records")
    except FileNotFoundError:
        print("  Credit Scores: Table not found, skipping")
        credit_scores = pd.DataFrame()
    
    try:
        parent_mapping = pd.read_csv(os.path.join(data_path, "dim_fp_customertoparentmap.csv"))
        print(f"  Parent Mapping: {len(parent_mapping)} records")
    except FileNotFoundError:
        print("  Parent Mapping: Table not found, skipping")
        parent_mapping = pd.DataFrame()
    
    print(f"  Properties: {len(properties)} records")
    print(f"  Customers: {len(customers)} records")
    print(f"  Amendments: {len(amendments)} records")
    print(f"  Leasing Activity: {len(leasing_activity)} records (limited to 10,000)")
    
    return properties, customers, amendments, leasing_activity, credit_scores, parent_mapping

def identify_fund_properties(properties):
    """Identify Fund 2 and Fund 3 properties"""
    print("\nIdentifying Fund 2 and Fund 3 properties...")
    
    # Fund 2: property codes starting with 'x'
    fund2_properties = properties[properties['property code'].str.startswith('x', na=False)].copy()
    fund2_properties['fund'] = 2
    
    # Fund 3: property codes starting with '3'
    fund3_properties = properties[properties['property code'].str.startswith('3', na=False)].copy()
    fund3_properties['fund'] = 3
    
    # Combine Fund 2 and Fund 3
    fund_properties = pd.concat([fund2_properties, fund3_properties], ignore_index=True)
    
    print(f"  Fund 2 properties: {len(fund2_properties)}")
    print(f"  Fund 3 properties: {len(fund3_properties)}")
    print(f"  Total Fund 2 & 3 properties: {len(fund_properties)}")
    
    return fund_properties

def find_new_tenants(fund_properties, amendments, customers, leasing_activity):
    """Find tenants that are new since January 1, 2025"""
    print("\nFinding new tenants since January 1, 2025...")
    
    # Get Fund 2 & 3 property IDs
    fund_property_ids = fund_properties['property id'].unique()
    
    # Filter amendments for Fund 2 & 3 properties
    fund_amendments = amendments[amendments['property hmy'].isin(fund_property_ids)].copy()
    
    # Convert amendment dates
    fund_amendments['start_date'] = fund_amendments['amendment start date'].apply(excel_serial_to_datetime)
    fund_amendments['sign_date'] = fund_amendments['amendment sign date'].apply(excel_serial_to_datetime)
    
    # Find new amendments (started on or after Jan 1, 2025)
    new_amendments = fund_amendments[
        (fund_amendments['start_date'] >= NEW_TENANT_START_DATE) |
        (fund_amendments['sign_date'] >= NEW_TENANT_START_DATE)
    ].copy()
    
    # Get latest amendment per property/tenant combination
    new_amendments['seq_rank'] = new_amendments.groupby(['property hmy', 'tenant hmy'])['amendment sequence'].rank(method='max', ascending=False)
    latest_new_amendments = new_amendments[new_amendments['seq_rank'] == 1].copy()
    
    print(f"  New amendments since 2025: {len(new_amendments)}")
    print(f"  Latest new amendments: {len(latest_new_amendments)}")
    
    # Check for acquisitions (properties acquired since Jan 1, 2025)
    fund_properties['acquire_date'] = pd.to_datetime(fund_properties['acquire date'], errors='coerce')
    new_acquisitions = fund_properties[fund_properties['acquire_date'] >= NEW_TENANT_START_DATE]
    
    if len(new_acquisitions) > 0:
        print(f"  Properties acquired since 2025: {len(new_acquisitions)}")
        # Get all tenants in newly acquired properties
        acquired_property_ids = new_acquisitions['property id'].unique()
        acquired_amendments = amendments[amendments['property hmy'].isin(acquired_property_ids)].copy()
        
        # Combine with new amendments
        latest_new_amendments = pd.concat([latest_new_amendments, acquired_amendments], ignore_index=True).drop_duplicates()
    
    # Also check leasing activity for new deals
    if len(leasing_activity) > 0:
        # Convert dates in leasing activity
        leasing_activity['start_date'] = pd.to_datetime(leasing_activity['dtStartDate'], errors='coerce')
        
        # Find new leases
        new_leases = leasing_activity[
            (leasing_activity['start_date'] >= NEW_TENANT_START_DATE) &
            (leasing_activity['Tenant HMY'].notna())
        ].copy()
        
        if len(new_leases) > 0:
            print(f"  New leases in leasing activity: {len(new_leases)}")
            new_tenant_hmys = new_leases['Tenant HMY'].unique()
            
            # Add these tenants if not already included
            additional_amendments = fund_amendments[fund_amendments['tenant hmy'].isin(new_tenant_hmys)]
            latest_new_amendments = pd.concat([latest_new_amendments, additional_amendments], ignore_index=True).drop_duplicates()
    
    # Remove duplicates and keep latest
    latest_new_amendments = latest_new_amendments.sort_values('amendment sequence', ascending=False).drop_duplicates(subset=['property hmy', 'tenant hmy'], keep='first')
    
    print(f"  Total unique new tenants: {len(latest_new_amendments)}")
    
    return latest_new_amendments

def merge_tenant_data(new_tenants, fund_properties, customers, leasing_activity, credit_scores, parent_mapping):
    """Merge all required data for new tenants including credit scores"""
    print("\nMerging tenant data...")
    
    # Ensure tenant id columns are the same type (convert to string)
    new_tenants['tenant id'] = new_tenants['tenant id'].astype(str)
    customers['tenant id'] = customers['tenant id'].astype(str)
    
    # Merge with property data for addresses and fund info
    result = new_tenants.merge(
        fund_properties[['property id', 'property code', 'postal address', 'postal city', 
                        'postal state', 'postal zip code', 'property name', 'fund']],
        left_on='property hmy',
        right_on='property id',
        how='left'
    )
    
    # Merge with customer data for customer id, naics, and risk flag
    result = result.merge(
        customers[['tenant id', 'customer id', 'naics', 'is at risk tenant', 'lessee name', 'dba name']],
        left_on='tenant id',
        right_on='tenant id',
        how='left'
    )
    
    # Try to get lease IDs from leasing activity
    if len(leasing_activity) > 0:
        lease_info = leasing_activity[['Tenant HMY', 'Deal HMY', 'dtStartDate']].drop_duplicates()
        result = result.merge(
            lease_info,
            left_on='tenant hmy',
            right_on='Tenant HMY',
            how='left'
        )
    else:
        result['Deal HMY'] = None
    
    # Add credit scores if available
    if len(credit_scores) > 0:
        print("  Adding credit scores...")
        # Try to match by customer ID first
        credit_scores['hmyperson_customer'] = credit_scores['hmyperson_customer'].astype(str) if 'hmyperson_customer' in credit_scores.columns else ''
        result['customer_id_str'] = result['customer id'].astype(str) if 'customer id' in result.columns else ''
        
        # Merge credit scores
        if 'hmyperson_customer' in credit_scores.columns:
            credit_data = credit_scores[['hmyperson_customer', 'credit score', 'date']].copy()
            credit_data.columns = ['customer_id_str', 'credit_score', 'credit_score_date']
            result = result.merge(
                credit_data,
                on='customer_id_str',
                how='left'
            )
        else:
            result['credit_score'] = None
            result['credit_score_date'] = None
            
        # Try fuzzy name matching for unmatched records
        if 'customer name' in credit_scores.columns and result['credit_score'].isna().any():
            print("  Attempting name-based credit score matching...")
            unmatched = result[result['credit_score'].isna()].copy()
            for idx, row in unmatched.iterrows():
                lessee = str(row.get('lessee name', '')).lower().strip()
                dba = str(row.get('dba name', '')).lower().strip()
                if lessee or dba:
                    # Try exact match first
                    matches = credit_scores[
                        (credit_scores['customer name'].str.lower().str.strip() == lessee) |
                        (credit_scores['customer name'].str.lower().str.strip() == dba)
                    ]
                    if len(matches) > 0:
                        result.at[idx, 'credit_score'] = matches.iloc[0]['credit score']
                        result.at[idx, 'credit_score_date'] = matches.iloc[0]['date']
    else:
        result['credit_score'] = None
        result['credit_score_date'] = None
    
    # Add parent company mapping if available
    if len(parent_mapping) > 0:
        print("  Adding parent company mapping...")
        parent_data = parent_mapping[['customer hmy', 'parent customer hmy']].copy()
        parent_data['customer hmy'] = parent_data['customer hmy'].astype(str)
        parent_data['parent customer hmy'] = parent_data['parent customer hmy'].astype(str)
        parent_data.columns = ['customer_id_str', 'parent_customer_id']
        
        result = result.merge(
            parent_data,
            on='customer_id_str',
            how='left'
        )
        
        # Get parent credit score if child doesn't have one
        if 'credit_score' in result.columns and 'parent_customer_id' in result.columns:
            no_score = result[(result['credit_score'].isna()) & (result['parent_customer_id'].notna())].copy()
            for idx, row in no_score.iterrows():
                parent_id = row['parent_customer_id']
                parent_scores = credit_scores[credit_scores['hmyperson_customer'].astype(str) == parent_id]
                if len(parent_scores) > 0:
                    result.at[idx, 'credit_score'] = parent_scores.iloc[0]['credit score']
                    result.at[idx, 'credit_score_date'] = parent_scores.iloc[0]['date']
                    result.at[idx, 'credit_score_source'] = 'Parent Company'
    else:
        result['parent_customer_id'] = None
    
    print(f"  Merged records: {len(result)}")
    if 'credit_score' in result.columns:
        print(f"  Records with credit scores: {result['credit_score'].notna().sum()}")
    
    return result

def format_output(result):
    """Format the output dataframe with required columns"""
    print("\nFormatting output...")
    
    # Debug: Print available columns
    print(f"  Available columns: {list(result.columns)}")
    
    # Create property address string
    result['property_address'] = result.apply(lambda row: 
        f"{row.get('postal address', '') or ''} {row.get('postal city', '') or ''}, {row.get('postal state', '') or ''} {row.get('postal zip code', '') or ''}".strip(), 
        axis=1
    )
    
    # Use Deal HMY as lease_id, fallback to amendment HMY
    if 'Deal HMY' in result.columns:
        result['lease_id'] = result['Deal HMY'].fillna(result['amendment hmy'])
    else:
        result['lease_id'] = result['amendment hmy']
    
    # Create final output dataframe
    # Use property code_x from amendments or property code_y from properties
    property_code_col = 'property code_x' if 'property code_x' in result.columns else 'property code_y' if 'property code_y' in result.columns else 'property code' if 'property code' in result.columns else None
    
    output = pd.DataFrame({
        'customer_id': result['customer id'] if 'customer id' in result.columns else None,
        'tenant_id': result['tenant id'],
        'tenant_name': result['lessee name'].fillna(result['dba name']) if 'lessee name' in result.columns else '',
        'property_address': result['property_address'],
        'property_name': result['property name'] if 'property name' in result.columns else '',
        'property_code': result[property_code_col] if property_code_col else '',
        'fund': result['fund'] if 'fund' in result.columns else '',
        'naics': result['naics'] if 'naics' in result.columns else '',
        'lease_id': result['lease_id'],
        'credit_score': result['credit_score'] if 'credit_score' in result.columns else None,
        'credit_score_date': result['credit_score_date'] if 'credit_score_date' in result.columns else None,
        'parent_customer_id': result['parent_customer_id'] if 'parent_customer_id' in result.columns else None,
        'tenant_risk': result['is at risk tenant'] if 'is at risk tenant' in result.columns else 0,
        'amendment_start_date': result['start_date'],
        'amendment_type': result['amendment type'],
        'amendment_status': result['amendment status']
    })
    
    # Sort by fund and start date
    output = output.sort_values(['fund', 'amendment_start_date', 'tenant_id'])
    
    # Remove duplicates
    output = output.drop_duplicates(subset=['customer_id', 'tenant_id', 'property_code'], keep='first')
    
    print(f"  Final records: {len(output)}")
    print(f"  Fund 2 tenants: {len(output[output['fund'] == 2])}")
    print(f"  Fund 3 tenants: {len(output[output['fund'] == 3])}")
    
    return output

def main():
    """Main execution function"""
    print("=" * 60)
    print("EXTRACTING NEW TENANTS IN FUND 2 & FUND 3 SINCE 2025")
    print("=" * 60)
    
    # Load data
    properties, customers, amendments, leasing_activity, credit_scores, parent_mapping = load_data()
    
    # Identify Fund 2 & 3 properties
    fund_properties = identify_fund_properties(properties)
    
    # Find new tenants
    new_tenants = find_new_tenants(fund_properties, amendments, customers, leasing_activity)
    
    if len(new_tenants) == 0:
        print("\nNo new tenants found since January 1, 2025")
        # Create empty output file
        empty_df = pd.DataFrame(columns=['customer_id', 'tenant_id', 'tenant_name', 'property_address', 
                                        'property_name', 'property_code', 'fund', 'naics', 'lease_id', 
                                        'credit_score', 'credit_score_date', 'parent_customer_id',
                                        'tenant_risk', 'amendment_start_date', 
                                        'amendment_type', 'amendment_status'])
        output_file = os.path.join(output_path, "new_tenants_fund2_fund3_since_2025.csv")
        empty_df.to_csv(output_file, index=False)
        print(f"\nEmpty CSV saved to: {output_file}")
        return
    
    # Merge all data
    merged_data = merge_tenant_data(new_tenants, fund_properties, customers, leasing_activity, credit_scores, parent_mapping)
    
    # Format output
    output = format_output(merged_data)
    
    # Save to CSV
    output_file = os.path.join(output_path, "new_tenants_fund2_fund3_since_2025.csv")
    output.to_csv(output_file, index=False)
    
    print("\n" + "=" * 60)
    print("EXPORT COMPLETE!")
    print(f"Output saved to: {output_file}")
    print("=" * 60)
    
    # Display summary statistics
    print("\nSummary by Fund:")
    summary = output.groupby('fund').agg({
        'tenant_id': 'count',
        'tenant_risk': 'sum'
    }).rename(columns={'tenant_id': 'Total Tenants', 'tenant_risk': 'At-Risk Tenants'})
    
    # Add credit score statistics if available
    if 'credit_score' in output.columns:
        credit_summary = output.groupby('fund')['credit_score'].agg(['mean', 'count'])
        credit_summary.columns = ['Avg Credit Score', 'With Credit Score']
        summary = summary.join(credit_summary)
    
    print(summary)
    
    # Show sample records
    print("\nSample Records (first 5):")
    sample_cols = ['customer_id', 'tenant_id', 'tenant_name', 'fund', 'property_code', 'credit_score', 'amendment_start_date']
    display_cols = [col for col in sample_cols if col in output.columns]
    print(output[display_cols].head())

if __name__ == "__main__":
    main()