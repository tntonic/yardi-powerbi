#!/usr/bin/env python3
"""
Script to identify potential credit report mismatches in the tenant credit data.
Focuses on:
1. Low match scores (< 80%)
2. Token fuzzy matches
3. Name similarity analysis
"""

import pandas as pd
from difflib import SequenceMatcher
import os
from datetime import datetime

# Paths
CSV_PATH = "/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Credit Identification/Data/final_tenant_credit_with_ids.csv"
OUTPUT_DIR = "/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Credit Identification/Reports"

def calculate_name_similarity(name1, name2):
    """Calculate similarity between two company names."""
    if pd.isna(name1) or pd.isna(name2):
        return 0
    
    # Clean and normalize names
    name1 = str(name1).lower().strip()
    name2 = str(name2).lower().strip()
    
    # Remove common suffixes
    suffixes = ['inc', 'inc.', 'llc', 'corp', 'corporation', 'company', 'co.', 'ltd', 'limited']
    for suffix in suffixes:
        name1 = name1.replace(suffix, '').strip()
        name2 = name2.replace(suffix, '').strip()
    
    return SequenceMatcher(None, name1, name2).ratio() * 100

def analyze_credit_matches():
    """Analyze credit report matches for potential issues."""
    
    # Load the data
    df = pd.read_csv(CSV_PATH)
    
    # Filter for records with credit matches
    matched_df = df[df['match_score'] > 0].copy()
    
    # Calculate actual name similarity
    matched_df['calculated_similarity'] = matched_df.apply(
        lambda row: calculate_name_similarity(row['tenant_name'], row['matched_credit_name']),
        axis=1
    )
    
    # Identify potential mismatches
    potential_mismatches = matched_df[
        (matched_df['match_score'] < 80) | 
        (matched_df['calculated_similarity'] < 60) |
        (matched_df['match_method'] == 'Token fuzzy match')
    ].copy()
    
    # Sort by calculated similarity to show worst matches first
    potential_mismatches = potential_mismatches.sort_values('calculated_similarity')
    
    # Prepare the report
    report_data = []
    
    for _, row in potential_mismatches.iterrows():
        report_data.append({
            'Customer ID': row['customer_id'],
            'Tenant Name': row['tenant_name'],
            'Matched Credit Name': row['matched_credit_name'],
            'Match Score': row['match_score'],
            'Calculated Similarity': round(row['calculated_similarity'], 1),
            'Match Method': row['match_method'],
            'Credit File': row['credit_filename'],
            'Mismatch Flag': 'HIGH' if row['calculated_similarity'] < 50 else 'MEDIUM'
        })
    
    # Create report DataFrame
    report_df = pd.DataFrame(report_data)
    
    # Generate summary statistics
    summary = {
        'Total Records with Credit Matches': len(matched_df),
        'Potential Mismatches Found': len(potential_mismatches),
        'High Risk Mismatches (< 50% similarity)': len(report_df[report_df['Mismatch Flag'] == 'HIGH']),
        'Medium Risk Mismatches (50-60% similarity)': len(report_df[report_df['Mismatch Flag'] == 'MEDIUM']),
        'Token Fuzzy Matches': len(report_df[report_df['Match Method'] == 'Token fuzzy match'])
    }
    
    return report_df, summary

def generate_report():
    """Generate and save the mismatch report."""
    
    print("Analyzing credit report matches...")
    report_df, summary = analyze_credit_matches()
    
    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Generate timestamp for file naming
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save detailed report to CSV
    report_path = os.path.join(OUTPUT_DIR, f"credit_mismatch_report_{timestamp}.csv")
    report_df.to_csv(report_path, index=False)
    print(f"Detailed report saved to: {report_path}")
    
    # Print summary to console
    print("\n" + "="*60)
    print("CREDIT MATCH ANALYSIS SUMMARY")
    print("="*60)
    for key, value in summary.items():
        print(f"{key}: {value}")
    
    # Print top mismatches
    print("\n" + "="*60)
    print("TOP 10 POTENTIAL MISMATCHES (Lowest Similarity)")
    print("="*60)
    
    top_mismatches = report_df.head(10)
    for _, row in top_mismatches.iterrows():
        print(f"\nCustomer ID: {row['Customer ID']}")
        print(f"  Tenant: {row['Tenant Name']}")
        print(f"  Credit: {row['Matched Credit Name']}")
        print(f"  Similarity: {row['Calculated Similarity']}%")
        print(f"  Match Method: {row['Match Method']}")
        print(f"  Risk Level: {row['Mismatch Flag']}")
    
    # Specific check for Snap Tire
    snap_tire = report_df[report_df['Customer ID'] == 'c0000638']
    if not snap_tire.empty:
        print("\n" + "="*60)
        print("SNAP TIRE SPECIFIC ISSUE")
        print("="*60)
        row = snap_tire.iloc[0]
        print(f"Customer ID: {row['Customer ID']}")
        print(f"Tenant Name: {row['Tenant Name']}")
        print(f"Incorrectly Matched To: {row['Matched Credit Name']}")
        print(f"Calculated Similarity: {row['Calculated Similarity']}%")
        print(f"This confirms the mismatch - 'Snap Tire' != 'USA Wheel & Tire'")
    
    return report_df

if __name__ == "__main__":
    report = generate_report()
    print("\n✅ Analysis complete! Check the Reports folder for detailed results.")