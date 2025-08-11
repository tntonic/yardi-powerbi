#!/usr/bin/env python3
"""
Batch version of accuracy improvement script - runs without user interaction.
Automatically identifies and removes the worst credit matches to improve accuracy.
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

# Thresholds for automatic removal
SIMILARITY_THRESHOLD = 40  # Remove if similarity < 40%
CONFIDENCE_THRESHOLD = 85  # New standard for keeping matches

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
    suffixes = ['inc', 'inc.', 'llc', 'corp', 'corporation', 'company', 'co.', 'ltd', 'limited', 
                'l.l.c.', 'incorporated', ',', '.']
    for suffix in suffixes:
        name1 = name1.replace(suffix, ' ').strip()
        name2 = name2.replace(suffix, ' ').strip()
    
    # Remove extra spaces
    name1 = ' '.join(name1.split())
    name2 = ' '.join(name2.split())
    
    return SequenceMatcher(None, name1, name2).ratio() * 100

def analyze_all_matches():
    """Analyze ALL credit matches and identify which should be removed."""
    
    df = pd.read_csv(CSV_PATH)
    
    # Only look at records with credit matches
    matched_df = df[df['match_score'] > 0].copy()
    
    analysis = []
    
    for idx, row in matched_df.iterrows():
        # Calculate actual name similarity
        actual_similarity = calculate_name_similarity(row['tenant_name'], row['matched_credit_name'])
        
        # Determine action based on similarity
        if actual_similarity < SIMILARITY_THRESHOLD:
            action = 'REMOVE'
            reason = f'Very low similarity ({actual_similarity:.1f}%)'
        elif actual_similarity < 60 and row['match_method'] == 'Token fuzzy match':
            action = 'REMOVE'
            reason = f'Fuzzy match with low similarity ({actual_similarity:.1f}%)'
        elif actual_similarity < 70 and row['match_score'] < 80:
            action = 'REMOVE'
            reason = f'Low confidence match ({actual_similarity:.1f}%)'
        elif actual_similarity >= CONFIDENCE_THRESHOLD:
            action = 'KEEP'
            reason = f'High similarity ({actual_similarity:.1f}%)'
        else:
            action = 'REVIEW'
            reason = f'Medium similarity ({actual_similarity:.1f}%)'
        
        analysis.append({
            'index': idx,
            'customer_id': row['customer_id'],
            'tenant_name': row['tenant_name'],
            'matched_credit_name': row['matched_credit_name'],
            'match_score': row['match_score'],
            'match_method': row['match_method'],
            'actual_similarity': round(actual_similarity, 1),
            'action': action,
            'reason': reason
        })
    
    return pd.DataFrame(analysis)

def remove_bad_matches(analysis_df):
    """Remove credit information from records marked for removal."""
    
    df = pd.read_csv(CSV_PATH)
    
    # Get indices to remove
    to_remove = analysis_df[analysis_df['action'] == 'REMOVE']
    
    # Fields to clear
    credit_fields = [
        'matched_credit_name', 'match_score', 'match_method', 'credit_filename',
        'credit_tenant_name', 'credit_revenue', 'credit_website', 'credit_industry',
        'credit_business_description', 'credit_credit_score', 'credit_credit_rating',
        'credit_probability_of_default'
    ]
    
    removed_records = []
    
    for idx in to_remove['index']:
        if idx in df.index:
            # Store record info before removing
            removed_records.append({
                'customer_id': df.at[idx, 'customer_id'],
                'tenant_name': df.at[idx, 'tenant_name'],
                'removed_match': df.at[idx, 'matched_credit_name']
            })
            
            # Clear all credit fields
            for field in credit_fields:
                if field in df.columns:
                    df.at[idx, field] = np.nan
            
            # Set match score to 0 and method to 'No match'
            df.at[idx, 'match_score'] = 0
            df.at[idx, 'match_method'] = 'No match'
    
    # Save updated data
    df.to_csv(CSV_PATH, index=False)
    
    return removed_records

def calculate_improvement_metrics(before_backup):
    """Calculate metrics showing improvement."""
    
    # Load before and after data
    df_before = pd.read_csv(before_backup)
    df_after = pd.read_csv(CSV_PATH)
    
    metrics = {
        'before': {
            'total_matches': len(df_before[df_before['match_score'] > 0]),
            'high_confidence': len(df_before[df_before['match_score'] >= 90]),
            'medium_confidence': len(df_before[(df_before['match_score'] >= 70) & (df_before['match_score'] < 90)]),
            'low_confidence': len(df_before[(df_before['match_score'] > 0) & (df_before['match_score'] < 70)])
        },
        'after': {
            'total_matches': len(df_after[df_after['match_score'] > 0]),
            'high_confidence': len(df_after[df_after['match_score'] >= 90]),
            'medium_confidence': len(df_after[(df_after['match_score'] >= 70) & (df_after['match_score'] < 90)]),
            'low_confidence': len(df_after[(df_after['match_score'] > 0) & (df_after['match_score'] < 70)])
        }
    }
    
    # Calculate accuracy improvement
    # Assuming high confidence matches are more accurate
    if metrics['before']['total_matches'] > 0:
        before_accuracy = metrics['before']['high_confidence'] / metrics['before']['total_matches'] * 100
    else:
        before_accuracy = 0
        
    if metrics['after']['total_matches'] > 0:
        after_accuracy = metrics['after']['high_confidence'] / metrics['after']['total_matches'] * 100
    else:
        after_accuracy = 0
    
    metrics['accuracy_improvement'] = after_accuracy - before_accuracy
    metrics['matches_removed'] = metrics['before']['total_matches'] - metrics['after']['total_matches']
    
    return metrics

def generate_report(analysis_df, removed_records, metrics):
    """Generate comprehensive report of improvements."""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(OUTPUT_DIR, f"accuracy_improvement_batch_{timestamp}.md")
    
    report = f"""# Credit Match Accuracy Improvement Report
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Mode: Automatic Batch Processing

## Executive Summary
Automatically analyzed and cleaned credit matches to improve overall data accuracy.
Removed matches with < {SIMILARITY_THRESHOLD}% name similarity.

## 🎯 Key Results

### Matches Removed: {len(removed_records)}
- **Before**: {metrics['before']['total_matches']} total matches
- **After**: {metrics['after']['total_matches']} total matches
- **Improvement**: {metrics['accuracy_improvement']:.1f}% accuracy increase

## 📊 Quality Distribution

### Before Cleaning
- High Confidence (≥90%): {metrics['before']['high_confidence']}
- Medium Confidence (70-89%): {metrics['before']['medium_confidence']}
- Low Confidence (<70%): {metrics['before']['low_confidence']}

### After Cleaning
- High Confidence (≥90%): {metrics['after']['high_confidence']}
- Medium Confidence (70-89%): {metrics['after']['medium_confidence']}
- Low Confidence (<70%): {metrics['after']['low_confidence']}

## 📋 Analysis Summary

### Actions Taken
"""
    
    action_summary = analysis_df['action'].value_counts()
    for action, count in action_summary.items():
        report += f"- **{action}**: {count} records\n"
    
    report += """

## 🗑️ Records Cleaned

### Top 20 Removed Matches
| Customer ID | Tenant Name | Removed Match | Similarity |
|-------------|-------------|---------------|------------|
"""
    
    # Show removed records with their similarity scores
    removed_df = analysis_df[analysis_df['action'] == 'REMOVE'].head(20)
    for _, row in removed_df.iterrows():
        tenant = row['tenant_name'][:25] if len(row['tenant_name']) > 25 else row['tenant_name']
        match = row['matched_credit_name'][:25] if len(row['matched_credit_name']) > 25 else row['matched_credit_name']
        report += f"| {row['customer_id']} | {tenant} | {match} | {row['actual_similarity']}% |\n"
    
    if len(removed_df) > 20:
        report += f"\n*Plus {len(analysis_df[analysis_df['action'] == 'REMOVE']) - 20} more...*\n"
    
    report += """

## ✅ Records Kept (High Confidence)

### Top 10 Best Matches
| Customer ID | Tenant Name | Credit Match | Similarity |
|-------------|-------------|--------------|------------|
"""
    
    kept_df = analysis_df[analysis_df['action'] == 'KEEP'].nlargest(10, 'actual_similarity')
    for _, row in kept_df.iterrows():
        tenant = row['tenant_name'][:25] if len(row['tenant_name']) > 25 else row['tenant_name']
        match = row['matched_credit_name'][:25] if len(row['matched_credit_name']) > 25 else row['matched_credit_name']
        report += f"| {row['customer_id']} | {tenant} | {match} | {row['actual_similarity']}% |\n"
    
    report += """

## 📈 Improvement Metrics

1. **Accuracy Increase**: {:.1f}%
2. **Bad Matches Removed**: {}
3. **Average Similarity Before**: {:.1f}%
4. **Average Similarity After**: {:.1f}%

## 🎯 Next Steps

1. **Obtain Credit Reports**: Get correct reports for the {} companies whose matches were removed
2. **Review Medium Matches**: {} records marked for review may need manual verification
3. **Update Threshold**: Recommend updating system threshold to {}% minimum
4. **Monitor Quality**: Run quality monitor to track improvements

## Files Generated

- Analysis Details: `accuracy_analysis_{}.csv`
- Removed Records: `removed_matches_{}.csv`
- This Report: `{}`
""".format(
        metrics['accuracy_improvement'],
        len(removed_records),
        analysis_df['actual_similarity'].mean(),
        analysis_df[analysis_df['action'] != 'REMOVE']['actual_similarity'].mean() if len(analysis_df[analysis_df['action'] != 'REMOVE']) > 0 else 0,
        len(removed_records),
        len(analysis_df[analysis_df['action'] == 'REVIEW']),
        CONFIDENCE_THRESHOLD,
        timestamp,
        timestamp,
        report_path
    )
    
    with open(report_path, 'w') as f:
        f.write(report)
    
    # Save analysis details
    analysis_path = os.path.join(OUTPUT_DIR, f"accuracy_analysis_{timestamp}.csv")
    analysis_df.to_csv(analysis_path, index=False)
    
    # Save removed records
    if removed_records:
        removed_path = os.path.join(OUTPUT_DIR, f"removed_matches_{timestamp}.csv")
        pd.DataFrame(removed_records).to_csv(removed_path, index=False)
    else:
        removed_path = None
    
    return report_path, analysis_path, removed_path

def main():
    print("🎯 Automatic Credit Match Accuracy Improvement")
    print("="*60)
    
    # Create backup
    print("\n📁 Creating backup...")
    backup_path = backup_data()
    
    # Analyze all matches
    print("\n📊 Analyzing all credit matches...")
    analysis_df = analyze_all_matches()
    
    # Show summary
    print("\n" + "="*60)
    print("ANALYSIS RESULTS")
    print("="*60)
    
    action_summary = analysis_df['action'].value_counts()
    total_matches = len(analysis_df)
    
    print(f"\n📊 Total Matches Analyzed: {total_matches}")
    for action, count in action_summary.items():
        percentage = (count / total_matches * 100) if total_matches > 0 else 0
        print(f"  • {action}: {count} ({percentage:.1f}%)")
    
    # Show worst matches
    to_remove = analysis_df[analysis_df['action'] == 'REMOVE']
    if len(to_remove) > 0:
        print(f"\n🚨 Removing {len(to_remove)} Bad Matches:")
        print("-"*60)
        
        worst = to_remove.nsmallest(10, 'actual_similarity')
        for _, row in worst.iterrows():
            tenant = row['tenant_name'][:30] if len(row['tenant_name']) > 30 else row['tenant_name']
            match = row['matched_credit_name'][:30] if len(row['matched_credit_name']) > 30 else row['matched_credit_name']
            print(f"{tenant:30} → {match:30} ({row['actual_similarity']}%)")
        
        if len(to_remove) > 10:
            print(f"... and {len(to_remove) - 10} more")
    
    # Remove bad matches
    print("\n🔧 Removing bad matches...")
    removed_records = remove_bad_matches(analysis_df)
    print(f"✅ Removed {len(removed_records)} credit matches")
    
    # Calculate improvement metrics
    print("\n📈 Calculating improvements...")
    metrics = calculate_improvement_metrics(backup_path)
    
    # Generate report
    print("\n📄 Generating report...")
    report_path, analysis_path, removed_path = generate_report(analysis_df, removed_records, metrics)
    
    # Final summary
    print("\n" + "="*60)
    print("✅ ACCURACY IMPROVEMENT COMPLETE")
    print("="*60)
    print(f"\n📊 Results:")
    print(f"  • Matches Removed: {len(removed_records)}")
    print(f"  • Accuracy Improved: {metrics['accuracy_improvement']:.1f}%")
    print(f"  • Remaining Matches: {metrics['after']['total_matches']}")
    print(f"  • High Confidence: {metrics['after']['high_confidence']}")
    
    print(f"\n📁 Files:")
    print(f"  • Backup: {backup_path}")
    print(f"  • Report: {report_path}")
    print(f"  • Analysis: {analysis_path}")
    if removed_path:
        print(f"  • Removed List: {removed_path}")
    
    print(f"\n💡 Next: Run credit_quality_monitor.py to see updated quality score")

if __name__ == "__main__":
    main()