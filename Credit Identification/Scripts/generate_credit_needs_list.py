#!/usr/bin/env python3
"""
Generate a prioritized list of companies needing credit reports.
Exports to both CSV and formatted report for action planning.
"""

import pandas as pd
import os
from datetime import datetime

# Paths
CSV_PATH = "/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Credit Identification/Data/final_tenant_credit_with_ids.csv"
OUTPUT_DIR = "/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Credit Identification/Reports"
FOLDERS_DIR = "/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Credit Identification/Folders"

def load_and_analyze_data():
    """Load data and identify companies needing credit reports."""
    
    df = pd.read_csv(CSV_PATH)
    
    # Categorize records
    needs_credit = {
        'critical_cleared': [],  # Critical mismatches we cleared
        'new_customer_ids': [],  # Newly assigned IDs
        'no_match_high_value': [],  # No match but important tenants
        'no_match_regular': [],  # Regular no match records
        'low_confidence': [],  # Existing but low confidence matches
        'missing_customer_id': []  # Still need customer IDs first
    }
    
    # Critical cleared records (these were wrong and removed)
    critical_ids = ['c0000270', 'c0000385', 'c0000678', 'c0000410', 'c0000178', 'c0000959']
    
    for _, row in df.iterrows():
        customer_id = row['customer_id']
        match_score = row['match_score'] if pd.notna(row['match_score']) else 0
        
        if pd.isna(customer_id):
            # Missing customer ID
            needs_credit['missing_customer_id'].append({
                'customer_id': 'NEEDS_ID',
                'tenant_name': row['tenant_name'],
                'property': row['property_name'],
                'fund': row['fund'],
                'lease_id': row['lease_id'],
                'priority': 'ASSIGN_ID_FIRST'
            })
        elif customer_id in critical_ids and match_score == 0:
            # Critical cleared records
            needs_credit['critical_cleared'].append({
                'customer_id': customer_id,
                'tenant_name': row['tenant_name'],
                'property': row['property_name'],
                'fund': row['fund'],
                'lease_id': row['lease_id'],
                'priority': 'CRITICAL'
            })
        elif customer_id and customer_id.startswith('c00010'):  # New IDs start with c00010
            # Newly assigned customer IDs
            needs_credit['new_customer_ids'].append({
                'customer_id': customer_id,
                'tenant_name': row['tenant_name'],
                'property': row['property_name'],
                'fund': row['fund'],
                'lease_id': row['lease_id'],
                'priority': 'HIGH'
            })
        elif match_score == 0:
            # No match records - check if high value
            if row['fund'] == 2:  # Fund 2 is priority
                needs_credit['no_match_high_value'].append({
                    'customer_id': customer_id,
                    'tenant_name': row['tenant_name'],
                    'property': row['property_name'],
                    'fund': row['fund'],
                    'lease_id': row['lease_id'],
                    'priority': 'MEDIUM'
                })
            else:
                needs_credit['no_match_regular'].append({
                    'customer_id': customer_id,
                    'tenant_name': row['tenant_name'],
                    'property': row['property_name'],
                    'fund': row['fund'],
                    'lease_id': row['lease_id'],
                    'priority': 'LOW'
                })
        elif match_score < 70:
            # Low confidence matches
            needs_credit['low_confidence'].append({
                'customer_id': customer_id,
                'tenant_name': row['tenant_name'],
                'property': row['property_name'],
                'fund': row['fund'],
                'lease_id': row['lease_id'],
                'current_match': row.get('matched_credit_name', ''),
                'match_score': match_score,
                'priority': 'REVIEW'
            })
    
    return needs_credit

def check_folder_status(customer_id):
    """Check if folder exists and is empty."""
    if pd.isna(customer_id) or customer_id == 'NEEDS_ID':
        return 'NO_ID'
    
    folder_path = os.path.join(FOLDERS_DIR, customer_id)
    if not os.path.exists(folder_path):
        return 'NO_FOLDER'
    
    files = os.listdir(folder_path)
    if not files:
        return 'EMPTY'
    else:
        return f"HAS_{len(files)}_FILES"

def generate_prioritized_list():
    """Generate a prioritized list of credit report needs."""
    
    needs_credit = load_and_analyze_data()
    
    all_needs = []
    
    # Add all categories with priority
    for category, records in needs_credit.items():
        for record in records:
            record['category'] = category
            record['folder_status'] = check_folder_status(record['customer_id'])
            all_needs.append(record)
    
    # Convert to DataFrame
    needs_df = pd.DataFrame(all_needs)
    
    # Sort by priority
    priority_order = {'CRITICAL': 1, 'HIGH': 2, 'MEDIUM': 3, 'LOW': 4, 'REVIEW': 5, 'ASSIGN_ID_FIRST': 6}
    needs_df['priority_num'] = needs_df['priority'].map(priority_order)
    needs_df = needs_df.sort_values(['priority_num', 'tenant_name'])
    
    return needs_df

def generate_reports():
    """Generate both CSV and formatted reports."""
    
    print("📊 Analyzing Credit Report Needs...")
    
    needs_df = generate_prioritized_list()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save to CSV
    csv_path = os.path.join(OUTPUT_DIR, f"credit_needs_list_{timestamp}.csv")
    needs_df.to_csv(csv_path, index=False)
    print(f"✅ CSV saved to: {csv_path}")
    
    # Generate formatted report
    report_path = os.path.join(OUTPUT_DIR, f"credit_needs_report_{timestamp}.md")
    
    report = f"""# Credit Report Needs Analysis
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Summary Statistics

- **Total Companies Needing Credit Reports**: {len(needs_df)}
- **Critical Priority**: {len(needs_df[needs_df['priority'] == 'CRITICAL'])}
- **High Priority**: {len(needs_df[needs_df['priority'] == 'HIGH'])}
- **Medium Priority**: {len(needs_df[needs_df['priority'] == 'MEDIUM'])}
- **Low Priority**: {len(needs_df[needs_df['priority'] == 'LOW'])}
- **Need Review**: {len(needs_df[needs_df['priority'] == 'REVIEW'])}
- **Need Customer ID First**: {len(needs_df[needs_df['priority'] == 'ASSIGN_ID_FIRST'])}

## Priority Categories

### 🚨 CRITICAL - Immediate Action Required
These are companies where we removed wrong credit reports and need replacements:

| Customer ID | Company Name | Property | Folder Status |
|-------------|--------------|----------|---------------|
"""
    
    critical = needs_df[needs_df['priority'] == 'CRITICAL']
    for _, row in critical.iterrows():
        report += f"| {row['customer_id']} | {row['tenant_name']} | {row['property']} | {row['folder_status']} |\n"
    
    report += """

### ⚠️ HIGH - New Customer IDs
Companies with newly assigned customer IDs needing first credit reports:

| Customer ID | Company Name | Property | Folder Status |
|-------------|--------------|----------|---------------|
"""
    
    high = needs_df[needs_df['priority'] == 'HIGH']
    for _, row in high.head(10).iterrows():
        report += f"| {row['customer_id']} | {row['tenant_name']} | {row['property']} | {row['folder_status']} |\n"
    
    if len(high) > 10:
        report += f"\n*Plus {len(high) - 10} more...*\n"
    
    report += """

### 📋 MEDIUM - Fund 2 Companies
Important Fund 2 companies without credit reports:

| Customer ID | Company Name | Property |
|-------------|--------------|----------|
"""
    
    medium = needs_df[needs_df['priority'] == 'MEDIUM']
    for _, row in medium.head(10).iterrows():
        report += f"| {row['customer_id']} | {row['tenant_name']} | {row['property']} |\n"
    
    if len(medium) > 10:
        report += f"\n*Plus {len(medium) - 10} more...*\n"
    
    report += """

### 📊 Statistics by Fund

| Fund | Need Credit Reports | Percentage of Fund |
|------|-------------------|-------------------|
"""
    
    fund_stats = needs_df.groupby('fund').size()
    for fund, count in fund_stats.items():
        report += f"| Fund {fund} | {count} | - |\n"
    
    report += """

## Recommended Action Plan

### Week 1 - Critical & High Priority
1. **Obtain credit reports for 6 critical companies** where wrong reports were removed
2. **Process credit reports for 9 new customer IDs** with empty folders ready

### Week 2-3 - Medium Priority
1. **Fund 2 companies** - Focus on high-value tenants
2. **Create folders** for companies without them
3. **Assign remaining customer IDs** to companies missing them

### Week 4 - Low Priority & Review
1. **Review low confidence matches** to determine if replacement needed
2. **Process remaining low priority** companies

## Export Files

- **Full List**: `{csv_path}`
- **This Report**: `{report_path}`

## Folder Readiness

- **Empty Folders (Ready)**: {len(needs_df[needs_df['folder_status'] == 'EMPTY'])}
- **No Folder Yet**: {len(needs_df[needs_df['folder_status'] == 'NO_FOLDER'])}
- **Has Files (Need Cleanup)**: {len(needs_df[needs_df['folder_status'].str.startswith('HAS_') == True]) if 'folder_status' in needs_df.columns else 0}
- **No Customer ID**: {len(needs_df[needs_df['folder_status'] == 'NO_ID'])}
"""
    
    with open(report_path, 'w') as f:
        f.write(report)
    
    print(f"✅ Report saved to: {report_path}")
    
    return needs_df, csv_path, report_path

def print_summary(needs_df):
    """Print a summary to console."""
    
    print("\n" + "="*60)
    print("CREDIT REPORT NEEDS SUMMARY")
    print("="*60)
    
    print("\n🎯 IMMEDIATE NEEDS (This Week):")
    critical = needs_df[needs_df['priority'] == 'CRITICAL']
    for _, row in critical.iterrows():
        print(f"  • {row['customer_id']}: {row['tenant_name']}")
    
    print(f"\n📊 TOTAL NEEDS BY PRIORITY:")
    priority_counts = needs_df['priority'].value_counts()
    for priority, count in priority_counts.items():
        print(f"  • {priority}: {count} companies")
    
    print(f"\n📁 FOLDER STATUS:")
    folder_counts = needs_df['folder_status'].value_counts()
    for status, count in folder_counts.items():
        print(f"  • {status}: {count}")
    
    # Special note about Snap Tire
    if 'c0000638' not in needs_df['customer_id'].values:
        print("\n⚠️  Note: Snap Tire (c0000638) has been corrected but needs the right PDF copied to its folder")

if __name__ == "__main__":
    print("🔍 Credit Report Needs Analysis Tool")
    print("="*60)
    
    # Generate reports
    needs_df, csv_path, report_path = generate_reports()
    
    # Print summary
    print_summary(needs_df)
    
    print("\n" + "="*60)
    print("✅ ANALYSIS COMPLETE")
    print("="*60)
    print("\n📄 Files Generated:")
    print(f"  • CSV List: {csv_path}")
    print(f"  • Formatted Report: {report_path}")
    print("\nUse the CSV for tracking and the report for planning.")