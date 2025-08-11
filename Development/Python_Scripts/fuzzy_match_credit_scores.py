#!/usr/bin/env python3
"""
Fuzzy Match Credit Scores Script

Purpose: Match tenants from missing credit scores report to Yardi data
         and retrieve their credit scores using fuzzy string matching.

Author: Claude AI Assistant
Date: 2025-08-11
"""

import pandas as pd
import numpy as np
from rapidfuzz import fuzz, process
import os
from datetime import datetime
import re

# Paths
BASE_DIR = "/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI"
INPUT_CSV = f"{BASE_DIR}/Credit Identification/Reports/missing_credit_scores_report copy.csv"
OUTPUT_CSV = f"{BASE_DIR}/Credit Identification/Reports/tenants_with_credit_scores.csv"
YARDI_DATA_DIR = f"{BASE_DIR}/Data/Yardi_Tables"

# Configuration
MATCH_THRESHOLD = 85  # Minimum similarity score for fuzzy matching
PARTIAL_MATCH_THRESHOLD = 80  # For partial ratio matching

def normalize_company_name(name):
    """Normalize company names for better matching"""
    if pd.isna(name):
        return ""
    
    # Convert to uppercase for consistency
    name = str(name).upper()
    
    # Remove common suffixes and punctuation for matching
    replacements = {
        r'\bLLC\b': '',
        r'\bL\.L\.C\.\b': '',
        r'\bINC\b': '',
        r'\bINC\.\b': '',
        r'\bCORP\b': '',
        r'\bCORP\.\b': '',
        r'\bCORPORATION\b': '',
        r'\bCOMPANY\b': '',
        r'\bCO\.\b': '',
        r'\bLTD\b': '',
        r'\bLIMITED\b': '',
        r'\bLP\b': '',
        r'\bL\.P\.\b': '',
        r'\bGROUP\b': '',
        r'\bGRP\b': '',
        r'\bUSA\b': '',
        r'\bU\.S\.A\.\b': '',
        r'\bUS\b': '',
        r'\bU\.S\.\b': '',
        r'[,.]': '',
        r'[\(\)]': '',
        r'\s+': ' '  # Multiple spaces to single space
    }
    
    for pattern, replacement in replacements.items():
        name = re.sub(pattern, replacement, name, flags=re.IGNORECASE)
    
    return name.strip()

def load_data():
    """Load all necessary data files"""
    print("Loading data files...")
    
    # Load missing credit scores report
    missing_df = pd.read_csv(INPUT_CSV)
    print(f"Loaded {len(missing_df)} tenants from missing credit scores report")
    
    # Load credit score data
    credit_df = pd.read_csv(f"{YARDI_DATA_DIR}/dim_fp_customercreditscorecustomdata.csv")
    print(f"Loaded {len(credit_df)} records from credit score data")
    
    # Load customer data
    customer_df = pd.read_csv(f"{YARDI_DATA_DIR}/dim_commcustomer.csv")
    print(f"Loaded {len(customer_df)} records from customer data")
    
    # Load customer to parent map (might have additional names)
    parent_map_df = pd.read_csv(f"{YARDI_DATA_DIR}/dim_fp_customertoparentmap.csv")
    print(f"Loaded {len(parent_map_df)} records from parent mapping data")
    
    return missing_df, credit_df, customer_df, parent_map_df

def fuzzy_match_tenant(tenant_name, customer_code, credit_df, customer_df, parent_map_df):
    """
    Perform fuzzy matching for a single tenant
    Returns: dict with match results
    """
    result = {
        'matched_customer_name': None,
        'match_confidence': 0,
        'credit_score': None,
        'credit_score_date': None,
        'match_source': None,
        'match_method': None
    }
    
    # First, try direct customer code match if provided
    if pd.notna(customer_code) and customer_code:
        # Check credit score table
        credit_match = credit_df[credit_df['customer code'] == customer_code]
        if not credit_match.empty:
            row = credit_match.iloc[0]
            result.update({
                'matched_customer_name': row['customer name'],
                'match_confidence': 100,
                'credit_score': row['credit score'],
                'credit_score_date': row['date'],
                'match_source': 'credit_score_table',
                'match_method': 'customer_code_exact'
            })
            return result
    
    # Normalize the tenant name for fuzzy matching
    normalized_tenant = normalize_company_name(tenant_name)
    
    # Prepare name lists for fuzzy matching
    credit_names = [(idx, row['customer name'], normalize_company_name(row['customer name'])) 
                    for idx, row in credit_df.iterrows() if pd.notna(row['customer name'])]
    
    customer_names = [(idx, row['lessee name'], normalize_company_name(row['lessee name'])) 
                      for idx, row in customer_df.iterrows() if pd.notna(row['lessee name'])]
    
    # Try fuzzy matching on credit score table
    if credit_names:
        # Use multiple matching strategies
        matches = []
        
        # Token Sort Ratio - handles word order differences
        for idx, orig_name, norm_name in credit_names:
            score = fuzz.token_sort_ratio(normalized_tenant, norm_name)
            if score >= MATCH_THRESHOLD:
                matches.append((idx, orig_name, score, 'token_sort'))
        
        # Partial Ratio - handles substring matches
        for idx, orig_name, norm_name in credit_names:
            score = fuzz.partial_ratio(normalized_tenant, norm_name)
            if score >= PARTIAL_MATCH_THRESHOLD:
                matches.append((idx, orig_name, score, 'partial'))
        
        # Take the best match
        if matches:
            matches.sort(key=lambda x: x[2], reverse=True)
            best_idx, best_name, best_score, match_type = matches[0]
            row = credit_df.iloc[best_idx]
            result.update({
                'matched_customer_name': best_name,
                'match_confidence': best_score,
                'credit_score': row['credit score'],
                'credit_score_date': row['date'],
                'match_source': 'credit_score_table',
                'match_method': f'fuzzy_{match_type}'
            })
            return result
    
    # Try fuzzy matching on customer table (no credit score, but confirms existence)
    if customer_names:
        matches = []
        
        for idx, orig_name, norm_name in customer_names:
            score = fuzz.token_sort_ratio(normalized_tenant, norm_name)
            if score >= MATCH_THRESHOLD:
                matches.append((idx, orig_name, score))
        
        if matches:
            matches.sort(key=lambda x: x[2], reverse=True)
            best_idx, best_name, best_score = matches[0]
            row = customer_df.iloc[best_idx]
            
            # Check if this customer has a credit score via customer_id
            if pd.notna(row['customer id']):
                credit_match = credit_df[credit_df['hmyperson_customer'] == row['customer id']]
                if not credit_match.empty:
                    credit_row = credit_match.iloc[0]
                    result.update({
                        'matched_customer_name': best_name,
                        'match_confidence': best_score,
                        'credit_score': credit_row['credit score'],
                        'credit_score_date': credit_row['date'],
                        'match_source': 'customer_table_with_credit',
                        'match_method': 'fuzzy_token_sort'
                    })
                else:
                    result.update({
                        'matched_customer_name': best_name,
                        'match_confidence': best_score,
                        'credit_score': None,
                        'credit_score_date': None,
                        'match_source': 'customer_table_no_credit',
                        'match_method': 'fuzzy_token_sort'
                    })
            else:
                result.update({
                    'matched_customer_name': best_name,
                    'match_confidence': best_score,
                    'credit_score': None,
                    'credit_score_date': None,
                    'match_source': 'customer_table_no_id',
                    'match_method': 'fuzzy_token_sort'
                })
            return result
    
    return result

def main():
    """Main execution function"""
    print("=" * 80)
    print("FUZZY MATCH CREDIT SCORES SCRIPT")
    print("=" * 80)
    
    # Load data
    missing_df, credit_df, customer_df, parent_map_df = load_data()
    
    # Process each tenant
    print("\nPerforming fuzzy matching...")
    results = []
    
    for idx, row in missing_df.iterrows():
        tenant_name = row['tenant_name']
        customer_code = row['customer_code'] if pd.notna(row['customer_code']) else None
        
        print(f"Processing {idx+1}/{len(missing_df)}: {tenant_name}")
        
        match_result = fuzzy_match_tenant(
            tenant_name, 
            customer_code, 
            credit_df, 
            customer_df, 
            parent_map_df
        )
        
        # Add original data to result
        result_row = row.to_dict()
        result_row.update(match_result)
        results.append(result_row)
    
    # Create results dataframe
    results_df = pd.DataFrame(results)
    
    # Save results
    results_df.to_csv(OUTPUT_CSV, index=False)
    print(f"\nResults saved to: {OUTPUT_CSV}")
    
    # Print summary statistics
    print("\n" + "=" * 80)
    print("MATCHING SUMMARY")
    print("=" * 80)
    
    total_tenants = len(results_df)
    matched_tenants = results_df['matched_customer_name'].notna().sum()
    credit_found = results_df['credit_score'].notna().sum()
    
    print(f"Total tenants processed: {total_tenants}")
    print(f"Tenants matched: {matched_tenants} ({matched_tenants/total_tenants*100:.1f}%)")
    print(f"Credit scores found: {credit_found} ({credit_found/total_tenants*100:.1f}%)")
    
    # Breakdown by match source
    print("\nMatch Sources:")
    source_counts = results_df['match_source'].value_counts()
    for source, count in source_counts.items():
        if source:
            print(f"  {source}: {count}")
    
    # Breakdown by match method
    print("\nMatch Methods:")
    method_counts = results_df['match_method'].value_counts()
    for method, count in method_counts.items():
        if method:
            print(f"  {method}: {count}")
    
    # Show confidence distribution for fuzzy matches
    fuzzy_matches = results_df[results_df['match_method'].str.contains('fuzzy', na=False)]
    if not fuzzy_matches.empty:
        print("\nFuzzy Match Confidence Distribution:")
        print(f"  Mean: {fuzzy_matches['match_confidence'].mean():.1f}")
        print(f"  Min: {fuzzy_matches['match_confidence'].min():.1f}")
        print(f"  Max: {fuzzy_matches['match_confidence'].max():.1f}")
    
    # Show credit score distribution
    credit_scores = results_df[results_df['credit_score'].notna()]['credit_score']
    if not credit_scores.empty:
        print("\nCredit Score Distribution:")
        print(f"  Mean: {credit_scores.mean():.2f}")
        print(f"  Min: {credit_scores.min():.2f}")
        print(f"  Max: {credit_scores.max():.2f}")
        
        # Risk categories
        high_risk = (credit_scores < 4.0).sum()
        medium_risk = ((credit_scores >= 4.0) & (credit_scores < 6.0)).sum()
        low_risk = (credit_scores >= 6.0).sum()
        
        print(f"\nRisk Categories:")
        print(f"  Low Risk (≥6.0): {low_risk}")
        print(f"  Medium Risk (4.0-5.9): {medium_risk}")
        print(f"  High Risk (<4.0): {high_risk}")
    
    print("\nScript completed successfully!")

if __name__ == "__main__":
    main()