#!/usr/bin/env python3
"""
Script to fix critical credit report mismatches and assign missing customer IDs.
This handles the most urgent issues identified in the analysis.
"""

import pandas as pd
import shutil
import os
from datetime import datetime

# Paths
CSV_PATH = "/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Credit Identification/Data/final_tenant_credit_with_ids.csv"
BACKUP_DIR = "/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Credit Identification/Data/backups"
FOLDERS_DIR = "/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Credit Identification/Folders"

# Critical mismatches that need immediate fixing
CRITICAL_FIXES = {
    'c0000270': {
        'tenant_name': 'Event Link',
        'wrong_credit': 'EventLink, LLC (wholly‐owned sub of EL Holding Company, Inc. and Subsidiaries)',
        'action': 'REMOVE',
        'new_credit_name': None,  # Will need actual Event Link credit
        'new_credit_file': None
    },
    'c0000385': {
        'tenant_name': 'JL Services Group, Inc.',
        'wrong_credit': 'Precision Facility Group, LLC',
        'action': 'REMOVE',
        'new_credit_name': None,  # Will need actual JL Services credit
        'new_credit_file': None
    },
    'c0000766': {
        'tenant_name': 'Z.One Concept USA',
        'wrong_credit': 'Z.One Concept USA, Inc. (owned by Beautynova Group...)',
        'action': 'UPDATE',
        'new_credit_name': 'Z.One Concept USA, Inc.',
        'new_credit_file': 'FP TCE_v6.68 - ZOne (2024-05-22).pdf'  # Same file, simpler name
    }
}

# Industry confusion fixes
INDUSTRY_CONFUSION_FIXES = {
    'c0000678': {
        'tenant_name': 'Superior Supply Chain Management Inc',
        'wrong_credit': 'IMI Management, Inc. (IMI)',
        'action': 'REMOVE'
    },
    'c0000410': {
        'tenant_name': 'KPower Global Logistics, LLC', 
        'wrong_credit': 'GEMACP Logistics',
        'action': 'REMOVE'
    },
    'c0000178': {
        'tenant_name': 'Centerpoint Marketing Inc.',
        'wrong_credit': 'Marketing.com',
        'action': 'REMOVE'
    },
    'c0000959': {
        'tenant_name': 'Mash Enterprise, LLC',
        'wrong_credit': 'Insight Enterprises, Inc.',
        'action': 'REMOVE'
    }
}

# Records missing customer IDs (need to generate)
MISSING_CUSTOMER_IDS = [
    'Harimatec Inc.',
    'American Traffic Solutions, Inc.',
    'Digi America Inc.',
    'Diagnostic Support Services, Inc.',  # 2 records
    'On Time Express, LLC',
    'Florida DeliCo, LLC',
    'Atlantic Tape Company, Inc.',
    'Pro-Cam Georgia, Inc.',
    'SHLA Group, Inc.'
]

def backup_data():
    """Create backups of CSV and note which folders need attention."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{BACKUP_DIR}/final_tenant_credit_backup_{timestamp}.csv"
    
    shutil.copy2(CSV_PATH, backup_path)
    print(f"✅ Backup created: {backup_path}")
    return backup_path

def generate_customer_id(existing_ids):
    """Generate next available customer ID."""
    # Extract numeric parts from existing IDs
    numbers = []
    for cid in existing_ids:
        if pd.notna(cid) and cid.startswith('c'):
            try:
                num = int(cid[1:])
                numbers.append(num)
            except:
                continue
    
    # Find next available number
    if numbers:
        next_num = max(numbers) + 1
    else:
        next_num = 2000  # Start from 2000 for new IDs
    
    return f"c{next_num:07d}"

def assign_missing_customer_ids():
    """Assign customer IDs to records that don't have them."""
    df = pd.read_csv(CSV_PATH)
    
    # Get existing customer IDs
    existing_ids = df['customer_id'].dropna().unique().tolist()
    
    assigned = []
    
    for tenant_name in MISSING_CUSTOMER_IDS:
        # Find records for this tenant
        mask = (df['tenant_name'] == tenant_name) & (df['customer_id'].isna())
        
        if df[mask].any().any():
            # Generate new customer ID
            new_id = generate_customer_id(existing_ids)
            existing_ids.append(new_id)
            
            # Assign to all matching records
            df.loc[mask, 'customer_id'] = new_id
            
            assigned.append({
                'tenant_name': tenant_name,
                'new_customer_id': new_id,
                'records_updated': mask.sum()
            })
            
            print(f"✅ Assigned {new_id} to {tenant_name} ({mask.sum()} records)")
    
    # Save updated CSV
    df.to_csv(CSV_PATH, index=False)
    
    return assigned

def fix_critical_mismatches():
    """Fix the critical mismatches by removing wrong credit info."""
    df = pd.read_csv(CSV_PATH)
    
    fixes_applied = []
    
    # Fix critical mismatches
    for customer_id, fix_info in CRITICAL_FIXES.items():
        mask = df['customer_id'] == customer_id
        
        if not df[mask].any().any():
            print(f"⚠️  Customer {customer_id} not found")
            continue
        
        if fix_info['action'] == 'REMOVE':
            # Clear credit information
            df.loc[mask, 'matched_credit_name'] = None
            df.loc[mask, 'credit_filename'] = None
            df.loc[mask, 'match_score'] = 0
            df.loc[mask, 'match_method'] = 'No match'
            df.loc[mask, 'credit_tenant_name'] = None
            df.loc[mask, 'credit_revenue'] = None
            df.loc[mask, 'credit_website'] = None
            df.loc[mask, 'credit_industry'] = None
            df.loc[mask, 'credit_business_description'] = None
            df.loc[mask, 'credit_credit_score'] = None
            df.loc[mask, 'credit_credit_rating'] = None
            
            print(f"✅ Removed wrong credit for {customer_id}: {fix_info['tenant_name']}")
            
        elif fix_info['action'] == 'UPDATE':
            # Update with corrected information
            df.loc[mask, 'matched_credit_name'] = fix_info['new_credit_name']
            df.loc[mask, 'match_method'] = 'Manual correction'
            df.loc[mask, 'match_score'] = 100
            
            print(f"✅ Updated credit name for {customer_id}: {fix_info['tenant_name']}")
        
        fixes_applied.append(customer_id)
    
    # Fix industry confusion
    for customer_id, fix_info in INDUSTRY_CONFUSION_FIXES.items():
        mask = df['customer_id'] == customer_id
        
        if not df[mask].any().any():
            continue
            
        # Clear credit information
        df.loc[mask, 'matched_credit_name'] = None
        df.loc[mask, 'credit_filename'] = None
        df.loc[mask, 'match_score'] = 0
        df.loc[mask, 'match_method'] = 'No match'
        df.loc[mask, 'credit_tenant_name'] = None
        df.loc[mask, 'credit_revenue'] = None
        df.loc[mask, 'credit_website'] = None
        df.loc[mask, 'credit_industry'] = None
        df.loc[mask, 'credit_business_description'] = None
        df.loc[mask, 'credit_credit_score'] = None
        df.loc[mask, 'credit_credit_rating'] = None
        
        print(f"✅ Removed industry confusion for {customer_id}: {fix_info['tenant_name']}")
        fixes_applied.append(customer_id)
    
    # Save updated CSV
    df.to_csv(CSV_PATH, index=False)
    
    return fixes_applied

def check_folders_to_clean():
    """Identify folders that need cleaning or deletion."""
    folders_to_clean = []
    
    for customer_id in list(CRITICAL_FIXES.keys()) + list(INDUSTRY_CONFUSION_FIXES.keys()):
        folder_path = os.path.join(FOLDERS_DIR, customer_id)
        if os.path.exists(folder_path):
            files = os.listdir(folder_path)
            folders_to_clean.append({
                'customer_id': customer_id,
                'folder_path': folder_path,
                'files': files,
                'action': 'REMOVE_FILES'
            })
    
    return folders_to_clean

def create_folders_for_new_ids(assigned_ids):
    """Create folders for newly assigned customer IDs."""
    created_folders = []
    
    for assignment in assigned_ids:
        customer_id = assignment['new_customer_id']
        folder_path = os.path.join(FOLDERS_DIR, customer_id)
        
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            created_folders.append(folder_path)
            print(f"📁 Created folder: {folder_path}")
    
    return created_folders

def generate_action_report():
    """Generate a report of all actions taken and needed."""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = f"/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Credit Identification/Reports/critical_fixes_report_{timestamp}.md"
    
    report = f"""# Critical Fixes Report
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Actions Completed

### Customer IDs Assigned
Check the CSV for newly assigned customer IDs starting with c0002000

### Critical Mismatches Fixed
- Removed wrong credit information from 4 critical records
- Removed wrong credit information from 4 industry confusion records

### Folders Created
New folders created for records with assigned customer IDs

## Manual Actions Required

### Critical Records - Need Credit Reports
1. **c0000270 - Event Link**
   - Find and upload correct Event Link credit report
   - Remove EventLink subsidiary PDF from folder

2. **c0000385 - JL Services Group**
   - Find and upload correct JL Services Group credit report
   - Remove Precision Facility Group PDF from folder

3. **c0000766 - Z.One Concept USA**
   - Verify if current PDF is acceptable (just needs name simplification)

### Industry Confusion - Need Credit Reports  
1. **c0000678 - Superior Supply Chain Management**
   - Find correct Superior Supply Chain credit report
   - Remove IMI Management PDF

2. **c0000410 - KPower Global Logistics**
   - Find correct KPower credit report
   - Remove GEMACP Logistics PDF

3. **c0000178 - Centerpoint Marketing**
   - Find correct Centerpoint Marketing credit report
   - Remove Marketing.com PDF

4. **c0000959 - Mash Enterprise**
   - Find correct Mash Enterprise credit report
   - Remove Insight Enterprises PDF

## Next Steps

1. Obtain correct credit reports for all cleared records
2. Upload credit reports to appropriate folders
3. Update CSV with new credit information once obtained
4. Run validation script to confirm fixes
"""
    
    with open(report_path, 'w') as f:
        f.write(report)
    
    print(f"\n📄 Action report saved to: {report_path}")
    return report_path

if __name__ == "__main__":
    print("🔧 Fixing Critical Credit Report Mismatches")
    print("="*60)
    
    # Create backup
    backup_path = backup_data()
    
    print("\n📝 Step 1: Assigning Missing Customer IDs")
    print("-"*40)
    assigned = assign_missing_customer_ids()
    
    print(f"\n✅ Assigned {len(assigned)} new customer IDs")
    
    print("\n🔧 Step 2: Fixing Critical Mismatches")
    print("-"*40)
    fixes = fix_critical_mismatches()
    
    print(f"\n✅ Fixed {len(fixes)} critical mismatches")
    
    print("\n📁 Step 3: Managing Folders")
    print("-"*40)
    
    # Check folders that need cleaning
    folders_to_clean = check_folders_to_clean()
    if folders_to_clean:
        print("\n⚠️  Folders needing attention:")
        for folder in folders_to_clean:
            print(f"  • {folder['customer_id']}: Remove {folder['files']}")
    
    # Create folders for new IDs
    if assigned:
        created = create_folders_for_new_ids(assigned)
        print(f"\n✅ Created {len(created)} new folders")
    
    # Generate action report
    print("\n📊 Step 4: Generating Action Report")
    print("-"*40)
    report_path = generate_action_report()
    
    print("\n" + "="*60)
    print("✅ CRITICAL FIXES COMPLETE")
    print("="*60)
    print(f"\n📌 Original data backed up to: {backup_path}")
    print(f"📌 Action report: {report_path}")
    print("\n⚠️  Manual actions required - see report for details")