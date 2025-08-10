#!/usr/bin/env python3
"""
Populate New Tenants with Customer Codes and Names
===================================================
This script populates the new_tenants_fund2_fund3_since_2025.csv file with:
- customer_id (column 1): Customer code from credit scores or parent mapping tables
- tenant_name (column 3): Customer name from credit scores table or lessee name from dim_commcustomer

Data Flow:
1. Join new_tenants with dim_commcustomer using tenant_id → tenant_code
2. Get customer_id from dim_commcustomer
3. Look up customer code from dim_fp_customercreditscorecustomdata (priority) or dim_fp_customertoparentmap
4. Look up customer name from dim_fp_customercreditscorecustomdata or use lessee_name from dim_commcustomer
"""

import pandas as pd
import warnings
from datetime import datetime

warnings.filterwarnings('ignore')

def load_data():
    """Load all required data tables"""
    print("Loading data tables...")
    
    # Load new tenants file
    new_tenants = pd.read_csv('Data/new_tenants_fund2_fund3_since_2025.csv')
    
    # Load Yardi tables
    dim_commcustomer = pd.read_csv('Data/Yardi_Tables/dim_commcustomer.csv')
    credit_scores = pd.read_csv('Data/Yardi_Tables/dim_fp_customercreditscorecustomdata.csv')
    parent_map = pd.read_csv('Data/Yardi_Tables/dim_fp_customertoparentmap.csv')
    
    # Clean column names
    dim_commcustomer.columns = dim_commcustomer.columns.str.strip()
    
    return new_tenants, dim_commcustomer, credit_scores, parent_map

def populate_customer_data(new_tenants, dim_commcustomer, credit_scores, parent_map):
    """
    Populate customer codes and names for new tenants
    
    Priority logic for customer_code:
    1. Check dim_fp_customercreditscorecustomdata (credit scores table)
    2. If not found, check dim_fp_customertoparentmap (parent mapping table)
    
    Priority logic for customer_name:
    1. Use customer name from dim_fp_customercreditscorecustomdata
    2. If not found, use lessee_name from dim_commcustomer
    """
    
    print("\n=== Starting population process ===")
    
    # Step 1: Join new_tenants with dim_commcustomer to get customer_id
    print("Step 1: Joining with dim_commcustomer...")
    populated = pd.merge(
        new_tenants,
        dim_commcustomer[['tenant code', 'customer id', 'lessee name']],
        left_on='tenant_id',
        right_on='tenant code',
        how='left'
    )
    
    # Initialize customer_code and customer_name columns
    populated['customer_code'] = None
    populated['customer_name'] = None
    
    # Statistics tracking
    stats = {
        'total_rows': len(populated),
        'has_customer_id': 0,
        'found_in_credit': 0,
        'found_in_parent': 0,
        'found_in_both': 0,
        'no_code_found': 0,
        'has_name': 0
    }
    
    # Step 2: Populate customer codes and names
    print("Step 2: Looking up customer codes and names...")
    
    for idx, row in populated.iterrows():
        if pd.notna(row['customer id']):
            stats['has_customer_id'] += 1
            customer_id = int(row['customer id'])
            
            # Check credit scores table first
            credit_match = credit_scores[credit_scores['hmyperson_customer'] == customer_id]
            parent_match = parent_map[parent_map['customer hmy'] == customer_id]
            
            customer_code = None
            customer_name = None
            
            if not credit_match.empty:
                # Found in credit scores table
                customer_code = credit_match.iloc[0]['customer code']
                customer_name = credit_match.iloc[0]['customer name']
                stats['found_in_credit'] += 1
                
                if not parent_match.empty:
                    stats['found_in_both'] += 1
                    
            elif not parent_match.empty:
                # Found only in parent map table
                customer_code = parent_match.iloc[0]['customer code']
                customer_name = parent_match.iloc[0]['customer name']
                stats['found_in_parent'] += 1
            else:
                # No customer code found
                stats['no_code_found'] += 1
                # Use lessee_name from dim_commcustomer as fallback for name
                if pd.notna(row['lessee name']):
                    customer_name = row['lessee name']
            
            # Update the populated dataframe
            populated.at[idx, 'customer_code'] = customer_code
            populated.at[idx, 'customer_name'] = customer_name
            
            if pd.notna(customer_name):
                stats['has_name'] += 1
    
    # Step 3: Prepare final output
    print("Step 3: Preparing final output...")
    
    # Copy original new_tenants structure and update columns
    output = new_tenants.copy()
    
    # Update customer_id column with customer_code
    output['customer_id'] = populated['customer_code']
    
    # Update tenant_name column with customer_name
    output['tenant_name'] = populated['customer_name']
    
    return output, stats

def generate_summary_report(stats, output_df):
    """Generate a summary report of the population results"""
    
    report = []
    report.append("=" * 60)
    report.append("NEW TENANTS POPULATION SUMMARY REPORT")
    report.append("=" * 60)
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    report.append("OVERALL STATISTICS:")
    report.append(f"  Total rows processed: {stats['total_rows']}")
    report.append(f"  Rows with customer_id from dim_commcustomer: {stats['has_customer_id']}")
    report.append("")
    
    report.append("CUSTOMER CODE POPULATION:")
    report.append(f"  Found in credit scores table only: {stats['found_in_credit'] - stats['found_in_both']}")
    report.append(f"  Found in parent map table only: {stats['found_in_parent']}")
    report.append(f"  Found in both tables: {stats['found_in_both']}")
    report.append(f"  Total with customer codes: {stats['found_in_credit'] + stats['found_in_parent']}")
    report.append(f"  No customer code found: {stats['no_code_found']}")
    report.append("")
    
    report.append("CUSTOMER NAME POPULATION:")
    report.append(f"  Rows with customer names: {stats['has_name']}")
    report.append(f"  Rows without customer names: {stats['total_rows'] - stats['has_name']}")
    report.append("")
    
    # Calculate coverage percentages
    if stats['has_customer_id'] > 0:
        code_coverage = ((stats['found_in_credit'] + stats['found_in_parent']) / stats['has_customer_id']) * 100
        report.append(f"COVERAGE METRICS:")
        report.append(f"  Customer code coverage: {code_coverage:.1f}%")
        report.append(f"  Customer name coverage: {(stats['has_name'] / stats['total_rows']) * 100:.1f}%")
        report.append("")
    
    # Add sample populated records
    report.append("SAMPLE POPULATED RECORDS:")
    populated_sample = output_df[output_df['customer_id'].notna()].head(5)
    for idx, row in populated_sample.iterrows():
        report.append(f"  Tenant: {row['tenant_id']}")
        report.append(f"    Customer Code: {row['customer_id']}")
        report.append(f"    Customer Name: {row['tenant_name']}")
        report.append("")
    
    report.append("=" * 60)
    
    return "\n".join(report)

def main():
    """Main execution function"""
    
    print("=" * 60)
    print("NEW TENANTS CUSTOMER CODE AND NAME POPULATION")
    print("=" * 60)
    
    # Load data
    new_tenants, dim_commcustomer, credit_scores, parent_map = load_data()
    
    # Populate customer data
    populated_df, stats = populate_customer_data(
        new_tenants, dim_commcustomer, credit_scores, parent_map
    )
    
    # Save populated data
    output_file = 'Data/new_tenants_fund2_fund3_since_2025_populated.csv'
    populated_df.to_csv(output_file, index=False)
    print(f"\n✓ Populated data saved to: {output_file}")
    
    # Generate and save summary report
    report = generate_summary_report(stats, populated_df)
    report_file = 'Data/new_tenants_population_summary.txt'
    with open(report_file, 'w') as f:
        f.write(report)
    print(f"✓ Summary report saved to: {report_file}")
    
    # Print summary to console
    print("\n" + report)
    
    print("\n✓ Population process completed successfully!")

if __name__ == "__main__":
    main()