#!/usr/bin/env python3
"""
Check medium confidence credit matches for potential issues
"""

import pandas as pd
import numpy as np
from datetime import datetime
from difflib import SequenceMatcher
import os

def calculate_name_similarity(name1, name2):
    """Calculate similarity between two names"""
    if pd.isna(name1) or pd.isna(name2):
        return 0
    
    # Clean names
    name1 = str(name1).lower().strip()
    name2 = str(name2).lower().strip()
    
    # Remove common suffixes for comparison
    suffixes = ['inc', 'inc.', 'llc', 'corp', 'corporation', 'company', 'co.', 'ltd', 'limited', 'llp', 'lp']
    for suffix in suffixes:
        name1 = name1.replace(suffix, '').strip()
        name2 = name2.replace(suffix, '').strip()
    
    # Remove punctuation
    for char in [',', '.', '-', '&']:
        name1 = name1.replace(char, ' ')
        name2 = name2.replace(char, ' ')
    
    # Remove extra spaces
    name1 = ' '.join(name1.split())
    name2 = ' '.join(name2.split())
    
    return SequenceMatcher(None, name1, name2).ratio() * 100

def main():
    # Read current data
    df = pd.read_csv('/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Credit Identification/Data/final_tenant_credit_with_ids.csv')
    
    print("🔍 Analyzing Medium Confidence Credit Matches")
    print("=" * 60)
    
    # Filter for records with credit matches
    matched_df = df[df['matched_credit_name'].notna()].copy()
    
    # Calculate actual similarity
    matched_df['actual_similarity'] = matched_df.apply(
        lambda row: calculate_name_similarity(row['tenant_name'], row['matched_credit_name']),
        axis=1
    )
    
    # Filter for medium confidence (70-89%)
    medium_conf = matched_df[
        (matched_df['actual_similarity'] >= 70) & 
        (matched_df['actual_similarity'] < 90)
    ].copy()
    
    if len(medium_conf) == 0:
        print("✅ No medium confidence matches found!")
        return
    
    print(f"\n📊 Found {len(medium_conf)} medium confidence matches (70-89% similarity)\n")
    
    # Sort by similarity (lowest first - most problematic)
    medium_conf = medium_conf.sort_values('actual_similarity')
    
    # Detailed analysis
    print("📋 DETAILED ANALYSIS OF MEDIUM CONFIDENCE MATCHES:")
    print("=" * 60)
    
    for idx, row in medium_conf.iterrows():
        print(f"\n{idx + 1}. Customer ID: {row['customer_id'] if pd.notna(row['customer_id']) else 'MISSING'}")
        print(f"   Tenant Name:  {row['tenant_name']}")
        print(f"   Credit Match: {row['matched_credit_name']}")
        print(f"   Similarity:   {row['actual_similarity']:.1f}%")
        print(f"   Match Score:  {row['match_score'] if pd.notna(row['match_score']) else 'N/A'}")
        print(f"   Match Method: {row['match_method'] if pd.notna(row['match_method']) else 'N/A'}")
        
        # Analyze the differences
        tenant_clean = str(row['tenant_name']).lower().strip()
        credit_clean = str(row['matched_credit_name']).lower().strip()
        
        # Check for specific issues
        issues = []
        
        # Check if it's a subsidiary notation issue
        if '(' in str(row['matched_credit_name']) and ')' in str(row['matched_credit_name']):
            issues.append("Has subsidiary/parent notation")
        
        # Check if it's just a suffix difference
        if tenant_clean.replace('llc', '').replace('inc', '').strip() == \
           credit_clean.replace('llc', '').replace('inc', '').strip():
            issues.append("Only suffix differs")
        
        # Check if it's a spacing/punctuation issue
        tenant_no_space = tenant_clean.replace(' ', '').replace(',', '').replace('.', '')
        credit_no_space = credit_clean.replace(' ', '').replace(',', '').replace('.', '')
        if tenant_no_space == credit_no_space:
            issues.append("Only spacing/punctuation differs")
        
        # Check for word order differences
        tenant_words = set(tenant_clean.split())
        credit_words = set(credit_clean.split())
        if tenant_words == credit_words:
            issues.append("Same words, different order")
        
        if issues:
            print(f"   Issues: {', '.join(issues)}")
        
        # Recommendation
        if row['actual_similarity'] >= 85:
            print("   ✅ RECOMMENDATION: KEEP (High enough similarity)")
        elif row['actual_similarity'] >= 75:
            print("   ⚠️  RECOMMENDATION: MANUAL REVIEW (Borderline case)")
        else:
            print("   ❌ RECOMMENDATION: CONSIDER REMOVING (Low similarity)")
    
    # Summary statistics
    print("\n" + "=" * 60)
    print("📊 SUMMARY STATISTICS:")
    print(f"   Total Medium Confidence: {len(medium_conf)}")
    print(f"   Average Similarity: {medium_conf['actual_similarity'].mean():.1f}%")
    print(f"   Lowest Similarity: {medium_conf['actual_similarity'].min():.1f}%")
    print(f"   Highest Similarity: {medium_conf['actual_similarity'].max():.1f}%")
    
    # Group by similarity ranges
    print("\n📈 DISTRIBUTION:")
    print(f"   70-74%: {len(medium_conf[(medium_conf['actual_similarity'] >= 70) & (medium_conf['actual_similarity'] < 75)])} matches")
    print(f"   75-79%: {len(medium_conf[(medium_conf['actual_similarity'] >= 75) & (medium_conf['actual_similarity'] < 80)])} matches")
    print(f"   80-84%: {len(medium_conf[(medium_conf['actual_similarity'] >= 80) & (medium_conf['actual_similarity'] < 85)])} matches")
    print(f"   85-89%: {len(medium_conf[(medium_conf['actual_similarity'] >= 85) & (medium_conf['actual_similarity'] < 90)])} matches")
    
    # Save detailed report
    report_path = f'/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Credit Identification/Reports/medium_confidence_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    medium_conf[['customer_id', 'tenant_name', 'matched_credit_name', 'actual_similarity', 
                 'match_score', 'match_method']].to_csv(report_path, index=False)
    
    print(f"\n📄 Detailed report saved to: {report_path}")
    
    # Check for potential removals
    removals = medium_conf[medium_conf['actual_similarity'] < 75]
    if len(removals) > 0:
        print(f"\n⚠️  WARNING: {len(removals)} matches below 75% similarity should be reviewed for removal")
        print("\nPotential removals:")
        for _, row in removals.iterrows():
            print(f"  - {row['tenant_name']} ❌ {row['matched_credit_name']} ({row['actual_similarity']:.1f}%)")
    
    print("\n✅ Analysis complete!")

if __name__ == "__main__":
    main()