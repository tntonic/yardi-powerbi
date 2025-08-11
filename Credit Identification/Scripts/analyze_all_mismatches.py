#!/usr/bin/env python3
"""
Comprehensive analysis of all credit report mismatches with specific recommendations.
"""

import pandas as pd
import os
from datetime import datetime

# Paths
MISMATCH_REPORT = "/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Credit Identification/Reports/credit_mismatch_report_20250810_173734.csv"
CSV_PATH = "/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Credit Identification/Data/final_tenant_credit_with_ids.csv"
OUTPUT_DIR = "/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Credit Identification/Reports"

def analyze_mismatches():
    """Analyze all mismatches and provide specific recommendations."""
    
    # Load the mismatch report
    mismatches_df = pd.read_csv(MISMATCH_REPORT)
    
    # Load the full data for context
    full_df = pd.read_csv(CSV_PATH)
    
    # Categorize mismatches
    critical_mismatches = []  # Completely wrong company
    parent_subsidiary = []     # Parent/subsidiary confusion
    name_variations = []       # Same company, different name format
    industry_confusion = []    # Similar industry, wrong company
    
    for _, row in mismatches_df.iterrows():
        tenant = str(row['Tenant Name']).lower() if pd.notna(row['Tenant Name']) else ''
        credit = str(row['Matched Credit Name']).lower() if pd.notna(row['Matched Credit Name']) else ''
        similarity = row['Calculated Similarity']
        
        # Analyze the type of mismatch
        if similarity < 30:
            # Very low similarity - likely completely wrong
            critical_mismatches.append(row)
        elif 'sub of' in credit or 'wholly-owned' in credit or 'parent' in credit:
            # Parent/subsidiary issue
            parent_subsidiary.append(row)
        elif any(word in tenant for word in tenant.split() if word in credit.split()):
            # Some name overlap - could be variation
            name_variations.append(row)
        else:
            # Industry confusion or other
            industry_confusion.append(row)
    
    return {
        'critical': pd.DataFrame(critical_mismatches),
        'parent_sub': pd.DataFrame(parent_subsidiary),
        'name_var': pd.DataFrame(name_variations),
        'industry': pd.DataFrame(industry_confusion),
        'all': mismatches_df
    }

def generate_recommendations():
    """Generate specific recommendations for each mismatch category."""
    
    categories = analyze_mismatches()
    
    recommendations = []
    
    # Critical mismatches - need immediate replacement
    if not categories['critical'].empty:
        for _, row in categories['critical'].iterrows():
            rec = {
                'Priority': 'CRITICAL',
                'Customer ID': row['Customer ID'],
                'Tenant Name': row['Tenant Name'],
                'Wrong Credit': row['Matched Credit Name'],
                'Similarity': f"{row['Calculated Similarity']:.1f}%",
                'Action': 'REPLACE - Obtain correct credit report',
                'Details': f"Wrong company entirely. Currently has {row['Credit File']}"
            }
            recommendations.append(rec)
    
    # Parent/subsidiary issues - verify if acceptable
    if not categories['parent_sub'].empty:
        for _, row in categories['parent_sub'].iterrows():
            rec = {
                'Priority': 'MEDIUM',
                'Customer ID': row['Customer ID'],
                'Tenant Name': row['Tenant Name'],
                'Wrong Credit': row['Matched Credit Name'],
                'Similarity': f"{row['Calculated Similarity']:.1f}%",
                'Action': 'VERIFY - Check if parent/sub relationship is acceptable',
                'Details': 'May be acceptable if parent company guarantees'
            }
            recommendations.append(rec)
    
    # Name variations - likely correct but verify
    if not categories['name_var'].empty:
        for _, row in categories['name_var'].iterrows():
            rec = {
                'Priority': 'LOW',
                'Customer ID': row['Customer ID'],
                'Tenant Name': row['Tenant Name'],
                'Wrong Credit': row['Matched Credit Name'],
                'Similarity': f"{row['Calculated Similarity']:.1f}%",
                'Action': 'VERIFY - Confirm same company',
                'Details': 'Appears to be name variation of same company'
            }
            recommendations.append(rec)
    
    # Industry confusion - replace
    if not categories['industry'].empty:
        for _, row in categories['industry'].iterrows():
            rec = {
                'Priority': 'HIGH',
                'Customer ID': row['Customer ID'],
                'Tenant Name': row['Tenant Name'],
                'Wrong Credit': row['Matched Credit Name'],
                'Similarity': f"{row['Calculated Similarity']:.1f}%",
                'Action': 'REPLACE - Wrong company in similar industry',
                'Details': 'Industry confusion - needs correct credit report'
            }
            recommendations.append(rec)
    
    return pd.DataFrame(recommendations)

def print_analysis():
    """Print detailed analysis and recommendations."""
    
    categories = analyze_mismatches()
    recommendations_df = generate_recommendations()
    
    print("\n" + "="*80)
    print("COMPREHENSIVE CREDIT MISMATCH ANALYSIS")
    print("="*80)
    
    # Summary statistics
    print("\n📊 MISMATCH CATEGORIES:")
    print(f"  • Critical (Wrong Company): {len(categories['critical'])} records")
    print(f"  • Parent/Subsidiary Issues: {len(categories['parent_sub'])} records")
    print(f"  • Name Variations: {len(categories['name_var'])} records")
    print(f"  • Industry Confusion: {len(categories['industry'])} records")
    
    # Critical issues that need immediate attention
    print("\n🚨 CRITICAL MISMATCHES (Need Immediate Replacement):")
    print("-"*80)
    
    critical = recommendations_df[recommendations_df['Priority'] == 'CRITICAL'].head(10)
    for _, row in critical.iterrows():
        print(f"\n{row['Customer ID'] if pd.notna(row['Customer ID']) else 'NO ID'}: {row['Tenant Name']}")
        print(f"  ❌ Wrong: {row['Wrong Credit']}")
        print(f"  📊 Similarity: {row['Similarity']}")
        print(f"  ⚠️  {row['Details']}")
    
    # High priority issues
    print("\n⚠️  HIGH PRIORITY (Industry Confusion):")
    print("-"*80)
    
    high = recommendations_df[recommendations_df['Priority'] == 'HIGH'].head(5)
    for _, row in high.iterrows():
        print(f"\n{row['Customer ID'] if pd.notna(row['Customer ID']) else 'NO ID'}: {row['Tenant Name']}")
        print(f"  Wrong: {row['Wrong Credit']}")
        print(f"  Similarity: {row['Similarity']}")
    
    # Save detailed recommendations
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    rec_path = os.path.join(OUTPUT_DIR, f"mismatch_recommendations_{timestamp}.csv")
    recommendations_df.to_csv(rec_path, index=False)
    print(f"\n📄 Detailed recommendations saved to: {rec_path}")
    
    return recommendations_df

def generate_action_list():
    """Generate a prioritized action list."""
    
    recommendations_df = generate_recommendations()
    
    # Sort by priority
    priority_order = {'CRITICAL': 1, 'HIGH': 2, 'MEDIUM': 3, 'LOW': 4}
    recommendations_df['Priority_Num'] = recommendations_df['Priority'].map(priority_order)
    recommendations_df = recommendations_df.sort_values('Priority_Num')
    
    print("\n" + "="*80)
    print("ACTION LIST")
    print("="*80)
    
    # Group by action type
    replace_list = recommendations_df[recommendations_df['Action'].str.contains('REPLACE')]
    verify_list = recommendations_df[recommendations_df['Action'].str.contains('VERIFY')]
    
    print(f"\n📝 RECORDS NEEDING REPLACEMENT: {len(replace_list)}")
    print("-"*40)
    for _, row in replace_list.head(15).iterrows():
        cust_id = row['Customer ID'] if pd.notna(row['Customer ID']) else 'NO_ID'
        print(f"  • {cust_id}: {row['Tenant Name']}")
    
    print(f"\n✅ RECORDS NEEDING VERIFICATION: {len(verify_list)}")
    print("-"*40)
    for _, row in verify_list.head(10).iterrows():
        cust_id = row['Customer ID'] if pd.notna(row['Customer ID']) else 'NO_ID'
        print(f"  • {cust_id}: {row['Tenant Name']}")
    
    # Missing customer IDs
    missing_ids = recommendations_df[recommendations_df['Customer ID'].isna()]
    if not missing_ids.empty:
        print(f"\n🔍 RECORDS MISSING CUSTOMER IDs: {len(missing_ids)}")
        print("-"*40)
        for _, row in missing_ids.iterrows():
            print(f"  • {row['Tenant Name']}")
    
    return recommendations_df

if __name__ == "__main__":
    print("🔍 Analyzing All Credit Report Mismatches...")
    
    # Run analysis
    recommendations = print_analysis()
    
    # Generate action list
    action_list = generate_action_list()
    
    print("\n" + "="*80)
    print("NEXT STEPS")
    print("="*80)
    print("\n1. CRITICAL: Replace credit reports for completely wrong companies")
    print("2. HIGH: Fix industry confusion cases")
    print("3. MEDIUM: Verify parent/subsidiary relationships")
    print("4. LOW: Confirm name variations are same company")
    print("5. Assign customer IDs to records missing them")
    
    print("\n✅ Analysis complete!")