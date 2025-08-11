#!/usr/bin/env python3
"""
Find tenants from Faropoint lease data that have credit scores but are missing from Yardi credit score tables.
Uses fuzzy matching to identify potential matches and outputs results to CSV.
"""

import pandas as pd
import numpy as np
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import os
import re
from datetime import datetime

# Define paths
BASE_PATH = "/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI"
CREDIT_PATH = os.path.join(BASE_PATH, "Credit Identification")
DATA_PATH = os.path.join(BASE_PATH, "Data/Yardi_Tables")
OUTPUT_PATH = os.path.join(CREDIT_PATH, "Reports")

def parse_faropoint_markdown():
    """Parse the Faropoint markdown file to extract tenant data"""
    print("Parsing Faropoint lease data...")
    
    file_path = os.path.join(CREDIT_PATH, "faropoint_lease_data.md")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Extract the table data (between the header and the summary)
    lines = content.split('\n')
    data_lines = []
    in_table = False
    
    for line in lines:
        if '| Fund | Quarter | Property |' in line:
            in_table = True
            continue
        elif '---' in line and in_table:
            continue
        elif in_table and line.startswith('|'):
            # Skip summary lines
            if 'Total Leases Signed' in line or 'Combined Portfolio Metrics' in line:
                break
            data_lines.append(line)
        elif in_table and not line.startswith('|'):
            break
    
    # Parse each data line
    faropoint_data = []
    for line in data_lines:
        if line.strip():
            parts = [p.strip() for p in line.split('|')[1:-1]]  # Remove empty first and last elements
            if len(parts) >= 18:  # Ensure we have all columns
                try:
                    record = {
                        'fund': parts[0],
                        'quarter': parts[1],
                        'property': parts[2],
                        'market': parts[3],
                        'activity': parts[4],
                        'tenant_name': parts[5],
                        'term_months': parts[6],
                        'sf': parts[7],
                        'rate_psf': parts[8],
                        'bp_rate': parts[9],
                        'fm_rate': parts[10],
                        'escalation_pct': parts[11],
                        'rd_escalation_pct': parts[12],
                        'total_lease_value': parts[13],
                        'ctv_pct': parts[14],
                        'downtime_months': parts[15],
                        'rexy': parts[16],
                        'credit_score': parts[17],
                        'aml': parts[18] if len(parts) > 18 else 'N/A'
                    }
                    faropoint_data.append(record)
                except Exception as e:
                    print(f"Error parsing line: {line}")
                    print(f"Error: {e}")
    
    df = pd.DataFrame(faropoint_data)
    print(f"  Parsed {len(df)} lease records from Faropoint")
    
    # Filter for records with actual credit scores (not N/A)
    df_with_scores = df[df['credit_score'].notna() & (df['credit_score'] != 'N/A')].copy()
    print(f"  Found {len(df_with_scores)} records with credit scores")
    
    return df_with_scores

def load_yardi_data():
    """Load Yardi credit score and customer data"""
    print("\nLoading Yardi data tables...")
    
    # Load credit scores
    credit_scores = pd.read_csv(os.path.join(DATA_PATH, "dim_fp_customercreditscorecustomdata.csv"))
    print(f"  Credit Scores: {len(credit_scores)} records")
    
    # Load customer data
    customers = pd.read_csv(os.path.join(DATA_PATH, "dim_commcustomer.csv"))
    print(f"  Customers: {len(customers)} records")
    
    # Load parent mapping for customer codes
    parent_map = pd.read_csv(os.path.join(DATA_PATH, "dim_fp_customertoparentmap.csv"))
    print(f"  Parent Mapping: {len(parent_map)} records")
    
    return credit_scores, customers, parent_map

def clean_company_name(name):
    """Clean company name for better matching"""
    if pd.isna(name):
        return ""
    
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

def fuzzy_match_tenant(tenant_name, yardi_names, threshold=75):
    """Find best fuzzy match for a tenant name"""
    if pd.isna(tenant_name) or str(tenant_name) == 'nan':
        return None, 0, None
    
    # Clean the input name
    clean_tenant = clean_company_name(tenant_name)
    
    # Prepare choices with both original and cleaned names
    choices = []
    choice_map = {}
    
    for idx, (orig_name, clean_name) in enumerate(yardi_names):
        if not pd.isna(orig_name):
            choices.append(clean_name)
            choice_map[clean_name] = (orig_name, idx)
    
    if not choices:
        return None, 0, None
    
    # Get the best match using cleaned names
    result = process.extractOne(clean_tenant, choices, scorer=fuzz.token_sort_ratio)
    
    if result and result[1] >= threshold:
        matched_clean = result[0]
        original_name, idx = choice_map[matched_clean]
        return original_name, result[1], idx
    else:
        return None, 0, None

def find_customer_code(tenant_name, customers, parent_map, credit_scores):
    """Try to find customer code for a tenant"""
    # First check credit scores table
    for _, row in credit_scores.iterrows():
        if pd.notna(row.get('customer name')):
            score = fuzz.token_sort_ratio(
                clean_company_name(tenant_name), 
                clean_company_name(row['customer name'])
            )
            if score >= 85:
                return row.get('customer code', None), score, 'credit_score_table'
    
    # Check parent mapping table
    for _, row in parent_map.iterrows():
        if pd.notna(row.get('customer name')):
            score = fuzz.token_sort_ratio(
                clean_company_name(tenant_name), 
                clean_company_name(row['customer name'])
            )
            if score >= 85:
                return row.get('customer code', None), score, 'parent_map_table'
    
    # Check customers table
    for _, row in customers.iterrows():
        if pd.notna(row.get('lessee name')):
            score = fuzz.token_sort_ratio(
                clean_company_name(tenant_name), 
                clean_company_name(row['lessee name'])
            )
            if score >= 85:
                # Try to find customer code from customer_id
                customer_id = row.get('customer id')
                if pd.notna(customer_id):
                    # Look up in parent map
                    parent_match = parent_map[parent_map['customer hmy'] == customer_id]
                    if not parent_match.empty:
                        return parent_match.iloc[0].get('customer code', None), score, 'customer_table'
    
    return None, 0, None

def main():
    """Main execution function"""
    print("=" * 60)
    print("Finding Missing Credit Scores from Faropoint Data")
    print("=" * 60)
    
    # Load data
    faropoint_df = parse_faropoint_markdown()
    credit_scores, customers, parent_map = load_yardi_data()
    
    # Prepare Yardi names for matching
    print("\nPreparing data for fuzzy matching...")
    
    # Create list of names from credit score table
    yardi_credit_names = [
        (row['customer name'], clean_company_name(row['customer name'])) 
        for _, row in credit_scores.iterrows()
    ]
    
    # Process each Faropoint tenant
    print("\nPerforming fuzzy matching analysis...")
    results = []
    
    unique_tenants = faropoint_df['tenant_name'].unique()
    print(f"Processing {len(unique_tenants)} unique tenants...")
    
    for idx, tenant_name in enumerate(unique_tenants):
        if idx % 10 == 0:
            print(f"  Processing tenant {idx + 1}/{len(unique_tenants)}...")
        
        # Get tenant records from Faropoint
        tenant_records = faropoint_df[faropoint_df['tenant_name'] == tenant_name]
        
        # Get credit score from Faropoint (use first non-NA value)
        faropoint_credit = None
        for _, rec in tenant_records.iterrows():
            if rec['credit_score'] not in ['N/A', None]:
                faropoint_credit = rec['credit_score']
                break
        
        if not faropoint_credit:
            continue
        
        # Check if tenant exists in Yardi credit scores
        matched_name, match_score, match_idx = fuzzy_match_tenant(tenant_name, yardi_credit_names, threshold=75)
        
        # Find customer code regardless of match status
        customer_code, code_score, code_source = find_customer_code(tenant_name, customers, parent_map, credit_scores)
        
        # Determine if credit score is missing in Yardi
        if matched_name:
            # Check if the matched record has a credit score
            matched_row = credit_scores.iloc[match_idx]
            yardi_credit = matched_row.get('credit score')
            is_missing = pd.isna(yardi_credit) or yardi_credit == 0
        else:
            is_missing = True
            yardi_credit = None
        
        # Only include if credit score is missing in Yardi
        if is_missing:
            # Get additional info from first tenant record
            first_record = tenant_records.iloc[0]
            
            result = {
                'tenant_name': tenant_name,
                'faropoint_credit_score': faropoint_credit,
                'fund': first_record['fund'],
                'property': first_record['property'],
                'market': first_record['market'],
                'activity': first_record['activity'],
                'yardi_match_found': 'Yes' if matched_name else 'No',
                'yardi_matched_name': matched_name if matched_name else '',
                'yardi_match_confidence': match_score if matched_name else 0,
                'yardi_credit_score': yardi_credit if matched_name else '',
                'customer_code': customer_code if customer_code else '',
                'customer_code_confidence': code_score if customer_code else 0,
                'customer_code_source': code_source if code_source else '',
                'status': 'Missing in Yardi'
            }
            results.append(result)
    
    # Create DataFrame and save results
    results_df = pd.DataFrame(results)
    
    # Sort by fund and tenant name
    results_df = results_df.sort_values(['fund', 'tenant_name'])
    
    # Save to CSV
    os.makedirs(OUTPUT_PATH, exist_ok=True)
    output_file = os.path.join(OUTPUT_PATH, 'missing_credit_scores_report.csv')
    results_df.to_csv(output_file, index=False)
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total unique tenants with credit scores in Faropoint: {len(unique_tenants)}")
    print(f"Tenants missing credit scores in Yardi: {len(results_df)}")
    print(f"  - Fund 2: {len(results_df[results_df['fund'] == 'Fund 2'])}")
    print(f"  - Fund 3: {len(results_df[results_df['fund'] == 'Fund 3'])}")
    print(f"\nCustomer codes found: {len(results_df[results_df['customer_code'] != ''])}")
    print(f"Customer codes not found: {len(results_df[results_df['customer_code'] == ''])}")
    
    print(f"\nOutput saved to: {output_file}")
    
    # Display first few rows
    print("\nFirst 10 missing credit scores:")
    print(results_df[['tenant_name', 'faropoint_credit_score', 'customer_code', 'fund']].head(10).to_string())
    
    return results_df

if __name__ == "__main__":
    main()