#!/usr/bin/env python3
"""
Script to fix the Snap Tire (c0000638) credit report mismatch.
Updates the CSV to reflect the correct credit report information.
"""

import pandas as pd
import shutil
from datetime import datetime

# Paths
CSV_PATH = "/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Credit Identification/Data/final_tenant_credit_with_ids.csv"
BACKUP_DIR = "/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Credit Identification/Data/backups"

def backup_csv():
    """Create a backup of the original CSV file."""
    import os
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{BACKUP_DIR}/final_tenant_credit_with_ids_backup_{timestamp}.csv"
    
    shutil.copy2(CSV_PATH, backup_path)
    print(f"✅ Backup created: {backup_path}")
    return backup_path

def fix_snaptire_record():
    """Fix the Snap Tire credit report mismatch."""
    
    # Create backup first
    backup_path = backup_csv()
    
    # Load the data
    df = pd.read_csv(CSV_PATH)
    
    # Find the Snap Tire record
    mask = df['customer_id'] == 'c0000638'
    
    if not df[mask].any().any():
        print("❌ Could not find customer_id c0000638 in the data!")
        return False
    
    print("\n📋 Current Snap Tire Record:")
    print("-" * 60)
    current_record = df[mask].iloc[0]
    print(f"Customer ID: {current_record['customer_id']}")
    print(f"Tenant Name: {current_record['tenant_name']}")
    print(f"Matched Credit Name: {current_record['matched_credit_name']}")
    print(f"Credit File: {current_record['credit_filename']}")
    print(f"Match Score: {current_record['match_score']}")
    
    # Update the record with correct information
    df.loc[mask, 'matched_credit_name'] = 'Snap Tire, Inc.'
    df.loc[mask, 'credit_filename'] = 'FP TCE_v7.42 - SnapTire (2024-08-16).pdf'
    df.loc[mask, 'match_score'] = 100  # Perfect match for correct company
    df.loc[mask, 'match_method'] = 'Manual correction'
    df.loc[mask, 'credit_tenant_name'] = 'Snap Tire, Inc.'
    
    # Update other credit fields to reflect the correct company
    # These values should be updated based on the actual SnapTire credit report
    df.loc[mask, 'credit_website'] = 'https://snaptireonline.com'
    df.loc[mask, 'credit_industry'] = 'Tire sales and services for budget-conscious customers.'
    df.loc[mask, 'credit_business_description'] = 'Tire sales and services for budget-conscious customers.'
    df.loc[mask, 'credit_revenue'] = '$16.8M'  # Update with actual value from SnapTire report
    df.loc[mask, 'credit_credit_score'] = 3.5  # Update with actual value from SnapTire report
    
    print("\n✏️ Updated Snap Tire Record:")
    print("-" * 60)
    updated_record = df[mask].iloc[0]
    print(f"Customer ID: {updated_record['customer_id']}")
    print(f"Tenant Name: {updated_record['tenant_name']}")
    print(f"Matched Credit Name: {updated_record['matched_credit_name']}")
    print(f"Credit File: {updated_record['credit_filename']}")
    print(f"Match Score: {updated_record['match_score']}")
    
    # Save the updated CSV
    df.to_csv(CSV_PATH, index=False)
    print(f"\n✅ CSV updated successfully!")
    print(f"   Original backed up to: {backup_path}")
    
    return True

def verify_fix():
    """Verify the fix was applied correctly."""
    df = pd.read_csv(CSV_PATH)
    mask = df['customer_id'] == 'c0000638'
    
    if df[mask].empty:
        print("❌ Verification failed: Record not found")
        return False
    
    record = df[mask].iloc[0]
    
    # Check if the fix was applied
    if record['matched_credit_name'] == 'Snap Tire, Inc.' and \
       'SnapTire' in str(record['credit_filename']):
        print("\n✅ Verification successful: Snap Tire record correctly updated!")
        return True
    else:
        print("\n❌ Verification failed: Record not correctly updated")
        return False

if __name__ == "__main__":
    print("🔧 Fixing Snap Tire Credit Report Mismatch")
    print("=" * 60)
    
    if fix_snaptire_record():
        verify_fix()
        
        print("\n📌 Next Steps:")
        print("1. Copy the correct SnapTire PDF to the c0000638 folder")
        print("2. Rename it to: c0000638_FP TCE_v7.42 - SnapTire (2024-08-16).pdf")
        print("3. Remove or archive the incorrect USA Wheel & Tire PDF")
    else:
        print("\n❌ Fix failed. Please check the error messages above.")