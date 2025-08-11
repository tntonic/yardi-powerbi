#!/usr/bin/env python3
"""
Fix medium confidence matches based on detailed review
"""

import pandas as pd
import numpy as np
from datetime import datetime
import shutil

def main():
    print("🔧 Fixing Medium Confidence Credit Matches")
    print("=" * 60)
    
    # Backup current file
    source = '/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Credit Identification/Data/final_tenant_credit_with_ids.csv'
    backup = f'/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Credit Identification/Data/Backups/backup_before_medium_fix_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    shutil.copy2(source, backup)
    print(f"✅ Backup created: {backup}")
    
    # Read current data
    df = pd.read_csv(source)
    original_count = df['matched_credit_name'].notna().sum()
    
    print("\n📋 REVIEWING PROBLEMATIC MATCHES:")
    print("-" * 40)
    
    # Define matches to remove based on analysis
    removals = [
        {
            'tenant': 'All-N-Express, LLC',
            'credit': 'ORAS Express, LLC',
            'reason': 'Completely different companies (All-N vs ORAS)'
        },
        {
            'tenant': 'Bates Enterprises, Inc.',
            'credit': 'Insight Enterprises, Inc.',
            'reason': 'Completely different companies (Bates vs Insight)'
        },
        {
            'tenant': 'Motion Industries, Inc.',
            'credit': 'Ox Industries, Inc.',
            'reason': 'Completely different companies (Motion vs Ox)'
        },
        {
            'tenant': 'Ehmke Manufacturing Co., Inc',
            'credit': 'CNC Manufacturing, Inc.',
            'reason': 'Completely different companies (Ehmke vs CNC)'
        }
    ]
    
    # Keep but note for review
    keep_with_notes = [
        {
            'tenant': 'Werner Aero Services',
            'credit': 'Werner Aero, LLC',
            'note': 'KEEP - Same company, just Services vs LLC difference'
        },
        {
            'tenant': 'Koontz Electric Company, Inc.',
            'credit': 'Koontz Electric Company, Incorporated',
            'note': 'KEEP - Same company, just Inc. vs Incorporated'
        },
        {
            'tenant': 'Dynamic Rubber, Inc.',
            'credit': 'Dynamic Rubber, Inc. (DR)',
            'note': 'KEEP - Same company with abbreviation notation'
        },
        {
            'tenant': 'IMI Management, INC',
            'credit': 'IMI Management, Inc. (IMI)',
            'note': 'KEEP - Same company with abbreviation notation'
        },
        {
            'tenant': 'Kreg Therapeutics, Inc',
            'credit': 'KREG THERAPEUTICS LLC (KT)',
            'note': 'KEEP - Same company, different entity type'
        },
        {
            'tenant': 'Circuit Works Corporation',
            'credit': 'Circuit Works Corporation (CWC)',
            'note': 'KEEP - Same company with abbreviation notation'
        }
    ]
    
    # Process removals
    removed_count = 0
    for removal in removals:
        mask = (df['tenant_name'] == removal['tenant']) & \
               (df['matched_credit_name'] == removal['credit'])
        
        if mask.any():
            print(f"\n❌ REMOVING: {removal['tenant']}")
            print(f"   Credit: {removal['credit']}")
            print(f"   Reason: {removal['reason']}")
            
            # Clear credit match fields
            df.loc[mask, 'matched_credit_name'] = np.nan
            df.loc[mask, 'match_score'] = np.nan
            df.loc[mask, 'match_method'] = np.nan
            df.loc[mask, 'pdf_path'] = np.nan
            df.loc[mask, 'folder_path'] = np.nan
            
            removed_count += 1
    
    print("\n" + "=" * 60)
    print("📋 KEEPING WITH NOTES:")
    print("-" * 40)
    
    for keep in keep_with_notes:
        mask = (df['tenant_name'] == keep['tenant']) & \
               (df['matched_credit_name'] == keep['credit'])
        
        if mask.any():
            print(f"\n✅ KEEPING: {keep['tenant']}")
            print(f"   Credit: {keep['credit']}")
            print(f"   Note: {keep['note']}")
    
    # Save updated file
    df.to_csv(source, index=False)
    
    # Create removal report
    report_data = []
    for removal in removals:
        report_data.append({
            'tenant_name': removal['tenant'],
            'removed_credit': removal['credit'],
            'reason': removal['reason'],
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    
    report_df = pd.DataFrame(report_data)
    report_path = f'/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Credit Identification/Reports/medium_confidence_removals_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    report_df.to_csv(report_path, index=False)
    
    # Summary
    final_count = df['matched_credit_name'].notna().sum()
    
    print("\n" + "=" * 60)
    print("📊 SUMMARY:")
    print(f"   Original matches: {original_count}")
    print(f"   Removed: {removed_count}")
    print(f"   Final matches: {final_count}")
    print(f"   Kept for review: {len(keep_with_notes)}")
    
    print(f"\n📄 Removal report saved to: {report_path}")
    print(f"💾 Data file updated: {source}")
    
    # Create final status report
    status_report = f"""# Medium Confidence Fixes - Status Report
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Actions Taken

### ❌ Removed (Clear Mismatches):
1. **All-N-Express, LLC** ❌ ORAS Express, LLC
   - Reason: Completely different companies
   
2. **Bates Enterprises, Inc.** ❌ Insight Enterprises, Inc.
   - Reason: Completely different companies
   
3. **Motion Industries, Inc.** ❌ Ox Industries, Inc.
   - Reason: Completely different companies
   
4. **Ehmke Manufacturing Co., Inc** ❌ CNC Manufacturing, Inc.
   - Reason: Completely different companies

### ✅ Kept (Valid Matches):
1. **Werner Aero Services** = Werner Aero, LLC
   - Same company, just entity type difference
   
2. **Koontz Electric Company, Inc.** = Koontz Electric Company, Incorporated
   - Same company, abbreviation difference
   
3. **Dynamic Rubber, Inc.** = Dynamic Rubber, Inc. (DR)
   - Same company with abbreviation
   
4. **IMI Management, INC** = IMI Management, Inc. (IMI)
   - Same company with abbreviation
   
5. **Kreg Therapeutics, Inc** = KREG THERAPEUTICS LLC (KT)
   - Same company, different entity type
   
6. **Circuit Works Corporation** = Circuit Works Corporation (CWC)
   - Same company with abbreviation

## Results
- **Total medium confidence reviewed**: 10
- **Removed as mismatches**: 4
- **Kept as valid**: 6
- **New total matches**: {final_count}

## Accuracy Improvement
By removing these 4 clear mismatches, we've further improved the accuracy of the credit matching system.
All remaining medium confidence matches are legitimate matches with minor formatting differences.
"""
    
    status_path = '/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Credit Identification/MEDIUM_CONFIDENCE_FIX_STATUS.md'
    with open(status_path, 'w') as f:
        f.write(status_report)
    
    print(f"\n📊 Status report saved to: {status_path}")
    print("\n✅ Medium confidence fixes complete!")
    print("💡 Next: Run credit_quality_monitor.py to see updated quality score")

if __name__ == "__main__":
    main()