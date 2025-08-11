#!/usr/bin/env python3
"""
Script to improve accuracy by analyzing and removing incorrect credit matches.
Focuses on identifying and cleaning up bad data to improve overall quality.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os
from difflib import SequenceMatcher

# Paths
CSV_PATH = "/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Credit Identification/Data/final_tenant_credit_with_ids.csv"
BACKUP_DIR = "/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Credit Identification/Data/backups"
OUTPUT_DIR = "/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Credit Identification/Reports"

def backup_data():
    """Create backup before making changes."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{BACKUP_DIR}/backup_before_accuracy_improvement_{timestamp}.csv"
    
    df = pd.read_csv(CSV_PATH)
    df.to_csv(backup_path, index=False)
    print(f"✅ Backup created: {backup_path}")
    return backup_path

def calculate_name_similarity(name1, name2):
    """Calculate similarity between two company names."""
    if pd.isna(name1) or pd.isna(name2):
        return 0
    
    # Clean and normalize
    name1 = str(name1).lower().strip()
    name2 = str(name2).lower().strip()
    
    # Remove common suffixes for better comparison
    suffixes = ['inc', 'inc.', 'llc', 'corp', 'corporation', 'company', 'co.', 'ltd', 'limited', 'l.l.c.', 'incorporated']
    for suffix in suffixes:
        name1 = name1.replace(suffix, '').strip().replace(',', '').replace('.', '')
        name2 = name2.replace(suffix, '').strip().replace(',', '').replace('.', '')
    
    return SequenceMatcher(None, name1, name2).ratio() * 100

def analyze_credit_inconsistencies():
    """Analyze records for credit data inconsistencies."""
    
    df = pd.read_csv(CSV_PATH)
    
    issues = []
    
    # Only look at records with credit matches
    matched_df = df[df['match_score'] > 0].copy()
    
    for idx, row in matched_df.iterrows():
        issue_flags = []
        
        # Calculate actual name similarity
        actual_similarity = calculate_name_similarity(row['tenant_name'], row['matched_credit_name'])
        
        # Check 1: Very low name similarity but high match score
        if actual_similarity < 40 and row['match_score'] > 70:
            issue_flags.append('LOW_NAME_SIMILARITY')
        
        # Check 2: Match method is suspicious
        if row['match_method'] == 'Token fuzzy match' and actual_similarity < 50:
            issue_flags.append('SUSPICIOUS_FUZZY_MATCH')
        
        # Check 3: Credit score seems wrong (check if fields mismatch)
        if pd.notna(row.get('credit_credit_score')) and pd.notna(row.get('credit_score')):
            if row['credit_credit_score'] != row['credit_score']:
                issue_flags.append('CREDIT_SCORE_MISMATCH')
        
        # Check 4: Industry mismatch (if we can detect it)
        tenant_lower = str(row['tenant_name']).lower() if pd.notna(row['tenant_name']) else ''
        credit_industry = str(row.get('credit_industry', '')).lower() if pd.notna(row.get('credit_industry')) else ''
        
        # Simple industry checks
        if 'tire' in tenant_lower and 'tire' not in credit_industry and 'wheel' not in credit_industry:
            if 'wheel' in str(row.get('matched_credit_name', '')).lower():
                issue_flags.append('INDUSTRY_MISMATCH')
        
        # Check 5: Parent/subsidiary confusion that might be wrong
        if 'subsidiary' in str(row.get('matched_credit_name', '')).lower() or 'parent' in str(row.get('matched_credit_name', '')).lower():
            if actual_similarity < 60:
                issue_flags.append('PARENT_SUB_CONFUSION')
        
        if issue_flags:
            issues.append({
                'index': idx,
                'customer_id': row['customer_id'],
                'tenant_name': row['tenant_name'],
                'matched_credit_name': row['matched_credit_name'],
                'match_score': row['match_score'],
                'actual_similarity': round(actual_similarity, 1),
                'match_method': row['match_method'],
                'credit_score': row.get('credit_credit_score', ''),
                'issues': ', '.join(issue_flags),
                'recommendation': 'REMOVE' if actual_similarity < 40 else 'REVIEW'
            })
    
    return pd.DataFrame(issues)

def identify_clear_mismatches():
    """Identify records that are clearly wrong and should be removed."""
    
    issues_df = analyze_credit_inconsistencies()
    
    # Filter for clear mismatches
    clear_mismatches = issues_df[
        (issues_df['actual_similarity'] < 40) |
        (issues_df['issues'].str.contains('LOW_NAME_SIMILARITY')) |
        (issues_df['issues'].str.contains('INDUSTRY_MISMATCH'))
    ].copy()
    
    # Sort by similarity to show worst first
    clear_mismatches = clear_mismatches.sort_values('actual_similarity')
    
    return clear_mismatches

def remove_bad_matches(indices_to_remove):
    """Remove credit information from specified records."""
    
    df = pd.read_csv(CSV_PATH)
    
    # Fields to clear for bad matches
    credit_fields = [
        'matched_credit_name', 'match_score', 'match_method', 'credit_filename',
        'credit_tenant_name', 'credit_revenue', 'credit_website', 'credit_industry',
        'credit_business_description', 'credit_credit_score', 'credit_credit_rating',
        'credit_probability_of_default'
    ]
    
    removed_count = 0
    
    for idx in indices_to_remove:
        if idx in df.index:
            # Clear all credit fields
            for field in credit_fields:
                if field in df.columns:
                    df.at[idx, field] = np.nan
            
            # Set match score to 0 and method to 'No match'
            df.at[idx, 'match_score'] = 0
            df.at[idx, 'match_method'] = 'No match'
            
            removed_count += 1
    
    # Save updated data
    df.to_csv(CSV_PATH, index=False)
    
    return removed_count

def interactive_review(issues_df):
    """Interactive review of problematic matches."""
    
    print("\n" + "="*80)
    print("INTERACTIVE REVIEW OF PROBLEMATIC MATCHES")
    print("="*80)
    
    indices_to_remove = []
    
    # Group by recommendation
    clear_removes = issues_df[issues_df['recommendation'] == 'REMOVE']
    reviews = issues_df[issues_df['recommendation'] == 'REVIEW']
    
    if len(clear_removes) > 0:
        print(f"\n🚨 CLEAR MISMATCHES (Recommend Removal): {len(clear_removes)} records")
        print("-"*60)
        
        for _, row in clear_removes.iterrows():
            print(f"\nRecord #{row['index']}")
            print(f"  Tenant: {row['tenant_name']}")
            print(f"  Matched To: {row['matched_credit_name']}")
            print(f"  Similarity: {row['actual_similarity']}%")
            print(f"  Issues: {row['issues']}")
        
        print("\n" + "-"*60)
        response = input("Remove ALL clear mismatches? (yes/no/review): ").lower()
        
        if response == 'yes':
            indices_to_remove.extend(clear_removes['index'].tolist())
            print(f"✅ Marked {len(clear_removes)} records for removal")
        elif response == 'review':
            # Review each one
            for _, row in clear_removes.iterrows():
                print(f"\n---\nTenant: {row['tenant_name']}")
                print(f"Matched: {row['matched_credit_name']}")
                print(f"Similarity: {row['actual_similarity']}%")
                r = input("Remove this match? (y/n): ").lower()
                if r == 'y':
                    indices_to_remove.append(row['index'])
    
    if len(reviews) > 0:
        print(f"\n⚠️  REVIEW NEEDED: {len(reviews)} records")
        response = input("Review these individually? (yes/no): ").lower()
        
        if response == 'yes':
            for _, row in reviews.head(10).iterrows():  # Limit to 10 for sanity
                print(f"\n---\nTenant: {row['tenant_name']}")
                print(f"Matched: {row['matched_credit_name']}")
                print(f"Similarity: {row['actual_similarity']}%")
                print(f"Issues: {row['issues']}")
                r = input("Remove this match? (y/n): ").lower()
                if r == 'y':
                    indices_to_remove.append(row['index'])
    
    return indices_to_remove

def generate_accuracy_report(issues_df, removed_count):
    """Generate report of accuracy improvements."""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(OUTPUT_DIR, f"accuracy_improvement_report_{timestamp}.md")
    
    # Load updated data for new metrics
    df = pd.read_csv(CSV_PATH)
    
    # Calculate new metrics
    total_records = len(df)
    records_with_credit = len(df[df['match_score'] > 0])
    high_confidence = len(df[df['match_score'] >= 90])
    
    report = f"""# Accuracy Improvement Report
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Summary
- **Issues Identified**: {len(issues_df)}
- **Records Cleaned**: {removed_count}
- **Accuracy Improvement**: Removed low-confidence and incorrect matches

## Issues Found

### By Issue Type
"""
    
    # Count issues by type
    issue_types = {}
    for issues_str in issues_df['issues']:
        for issue in issues_str.split(', '):
            issue_types[issue] = issue_types.get(issue, 0) + 1
    
    for issue, count in sorted(issue_types.items(), key=lambda x: x[1], reverse=True):
        report += f"- {issue}: {count} records\n"
    
    report += f"""

## Records Removed

The following {removed_count} records had their credit information removed due to poor matches:

| Customer ID | Tenant | Wrong Match | Similarity | Issues |
|-------------|---------|-------------|------------|--------|
"""
    
    removed_df = issues_df[issues_df['index'].isin(
        issues_df['index'].tolist()[:removed_count]
    )].head(20)
    
    for _, row in removed_df.iterrows():
        report += f"| {row['customer_id']} | {row['tenant_name'][:30]} | {row['matched_credit_name'][:30]} | {row['actual_similarity']}% | {row['issues'][:30]} |\n"
    
    report += f"""

## New Metrics

- **Total Records**: {total_records}
- **Records with Credit**: {records_with_credit} ({records_with_credit/total_records*100:.1f}%)
- **High Confidence Matches**: {high_confidence}

## Recommendations

1. **Obtain Correct Credit Reports**: For the {removed_count} cleaned records
2. **Review Remaining Issues**: {len(issues_df) - removed_count} records still need review
3. **Update Match Threshold**: Increase to 85% minimum to prevent future issues
4. **Regular Monitoring**: Run accuracy checks monthly

## Files

- Issues Analysis: `accuracy_issues_{timestamp}.csv`
- This Report: `{report_path}`
"""
    
    with open(report_path, 'w') as f:
        f.write(report)
    
    # Also save issues to CSV
    issues_path = os.path.join(OUTPUT_DIR, f"accuracy_issues_{timestamp}.csv")
    issues_df.to_csv(issues_path, index=False)
    
    return report_path, issues_path

def main():
    print("🎯 Credit Match Accuracy Improvement Tool")
    print("="*60)
    print("This tool will:")
    print("1. Analyze existing credit matches for accuracy")
    print("2. Identify clear mismatches and issues")
    print("3. Remove incorrect credit information")
    print("4. Improve overall data quality")
    print()
    
    # Create backup
    backup_path = backup_data()
    
    # Analyze issues
    print("\n📊 Analyzing credit match accuracy...")
    issues_df = analyze_credit_inconsistencies()
    
    if len(issues_df) == 0:
        print("✅ No significant issues found!")
        return
    
    print(f"\n⚠️  Found {len(issues_df)} problematic matches")
    
    # Show summary
    print("\n" + "="*60)
    print("ISSUES SUMMARY")
    print("="*60)
    
    print("\n📊 By Similarity Range:")
    print(f"  • < 40% similarity: {len(issues_df[issues_df['actual_similarity'] < 40])} records")
    print(f"  • 40-60% similarity: {len(issues_df[(issues_df['actual_similarity'] >= 40) & (issues_df['actual_similarity'] < 60)])} records")
    print(f"  • 60-80% similarity: {len(issues_df[(issues_df['actual_similarity'] >= 60) & (issues_df['actual_similarity'] < 80)])} records")
    
    print("\n🚨 Top 10 Worst Matches:")
    print("-"*60)
    
    worst = issues_df.nsmallest(10, 'actual_similarity')
    for _, row in worst.iterrows():
        print(f"{row['tenant_name'][:30]:30} → {row['matched_credit_name'][:30]:30} ({row['actual_similarity']}%)")
    
    # Interactive review
    print("\n" + "="*60)
    response = input("Do you want to clean up these mismatches? (yes/no): ").lower()
    
    if response == 'yes':
        indices_to_remove = interactive_review(issues_df)
        
        if indices_to_remove:
            print(f"\n🔧 Removing credit information from {len(indices_to_remove)} records...")
            removed_count = remove_bad_matches(indices_to_remove)
            print(f"✅ Cleaned {removed_count} records")
            
            # Generate report
            report_path, issues_path = generate_accuracy_report(issues_df, removed_count)
            
            print("\n" + "="*60)
            print("✅ ACCURACY IMPROVEMENT COMPLETE")
            print("="*60)
            print(f"📊 Issues analyzed: {len(issues_df)}")
            print(f"🧹 Records cleaned: {removed_count}")
            print(f"💾 Backup saved: {backup_path}")
            print(f"📄 Report: {report_path}")
            print(f"📋 Issues list: {issues_path}")
        else:
            print("\n❌ No changes made")
    else:
        # Just save the analysis
        issues_path = os.path.join(OUTPUT_DIR, f"accuracy_issues_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        issues_df.to_csv(issues_path, index=False)
        print(f"\n📋 Issues analysis saved to: {issues_path}")
        print("No changes made to the data.")

if __name__ == "__main__":
    main()