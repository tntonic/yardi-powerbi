#!/usr/bin/env python3
"""
Script to clean up wrong PDFs from folders and prepare for correct credit reports.
Also archives the removed files for safety.
"""

import os
import shutil
from datetime import datetime
import pandas as pd

# Paths
FOLDERS_DIR = "/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Credit Identification/Folders"
ARCHIVE_DIR = "/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Credit Identification/Archive_Wrong_PDFs"
CSV_PATH = "/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Credit Identification/Data/final_tenant_credit_with_ids.csv"

# PDFs to remove (based on our analysis)
PDFS_TO_REMOVE = {
    'c0000270': {
        'wrong_file': 'c0000270_FP TCE_v6.66 - EventLink (2024-04-09).pdf',
        'tenant': 'Event Link',
        'reason': 'Wrong company - EventLink subsidiary instead of Event Link'
    },
    'c0000385': {
        'wrong_file': None,  # May not have file in folder
        'tenant': 'JL Services Group, Inc.',
        'reason': 'Wrong company - Precision Facility Group'
    },
    'c0000678': {
        'wrong_file': 'c0000678_FP TCE_v7.45 - IMI Management (2025-01-29).pdf',
        'tenant': 'Superior Supply Chain Management Inc',
        'reason': 'Wrong company - IMI Management'
    },
    'c0000410': {
        'wrong_file': 'c0000410_FP TCE_v6.65 - Gemcap (2023-11-17).pdf',
        'tenant': 'KPower Global Logistics, LLC',
        'reason': 'Wrong company - GEMACP Logistics'
    },
    'c0000178': {
        'wrong_file': 'c0000178_FP TCE_v7.25 - Marketing.com (12.15.23).pdf',
        'tenant': 'Centerpoint Marketing Inc.',
        'reason': 'Wrong company - Marketing.com'
    },
    'c0000959': {
        'wrong_file': None,  # May not have folder
        'tenant': 'Mash Enterprise, LLC',
        'reason': 'Wrong company - Insight Enterprises'
    },
    'c0000638': {
        'wrong_file': 'c0000638_FP TCE_v7.44 - USA Wheel & Tire (2024-11-23).pdf',
        'tenant': 'Snap Tire, Inc.',
        'reason': 'Wrong company - USA Wheel & Tire instead of Snap Tire'
    }
}

def create_archive_directory():
    """Create archive directory for removed PDFs."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_path = os.path.join(ARCHIVE_DIR, f"archive_{timestamp}")
    os.makedirs(archive_path, exist_ok=True)
    return archive_path

def cleanup_wrong_pdfs():
    """Remove wrong PDFs from folders and archive them."""
    
    archive_path = create_archive_directory()
    results = []
    
    print("🧹 Cleaning Up Wrong PDFs from Folders")
    print("="*60)
    
    for customer_id, info in PDFS_TO_REMOVE.items():
        folder_path = os.path.join(FOLDERS_DIR, customer_id)
        
        result = {
            'customer_id': customer_id,
            'tenant': info['tenant'],
            'status': '',
            'action': '',
            'archived_to': ''
        }
        
        if not os.path.exists(folder_path):
            result['status'] = 'NO_FOLDER'
            result['action'] = 'Folder does not exist'
            print(f"⚠️  {customer_id}: Folder doesn't exist")
        else:
            # List files in folder
            files = os.listdir(folder_path)
            
            if not files:
                result['status'] = 'EMPTY'
                result['action'] = 'Folder already empty'
                print(f"✅ {customer_id}: Folder already empty")
            else:
                # Look for wrong file
                removed = False
                for file in files:
                    if info['wrong_file'] and file == info['wrong_file']:
                        # Archive the file
                        src = os.path.join(folder_path, file)
                        dst = os.path.join(archive_path, f"{customer_id}_{file}")
                        shutil.move(src, dst)
                        result['status'] = 'CLEANED'
                        result['action'] = f'Archived and removed: {file}'
                        result['archived_to'] = dst
                        removed = True
                        print(f"✅ {customer_id}: Removed {file}")
                        print(f"   → Archived to: {archive_path}")
                    elif file.endswith('.pdf'):
                        # Archive any PDF if no specific file mentioned
                        if not info['wrong_file']:
                            src = os.path.join(folder_path, file)
                            dst = os.path.join(archive_path, f"{customer_id}_{file}")
                            shutil.move(src, dst)
                            result['status'] = 'CLEANED'
                            result['action'] = f'Archived and removed: {file}'
                            result['archived_to'] = dst
                            removed = True
                            print(f"✅ {customer_id}: Removed {file}")
                
                if not removed:
                    result['status'] = 'NO_MATCH'
                    result['action'] = f'Expected file not found. Files present: {files}'
                    print(f"⚠️  {customer_id}: Expected file not found")
                    print(f"   Files in folder: {files}")
        
        results.append(result)
    
    return results, archive_path

def generate_cleanup_report(results, archive_path):
    """Generate a report of the cleanup actions."""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = f"/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Credit Identification/Reports/cleanup_report_{timestamp}.md"
    
    cleaned_count = sum(1 for r in results if r['status'] == 'CLEANED')
    no_folder_count = sum(1 for r in results if r['status'] == 'NO_FOLDER')
    empty_count = sum(1 for r in results if r['status'] == 'EMPTY')
    no_match_count = sum(1 for r in results if r['status'] == 'NO_MATCH')
    
    report = f"""# PDF Cleanup Report
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Summary
- **Total Folders Checked**: {len(results)}
- **PDFs Removed**: {cleaned_count}
- **Already Empty**: {empty_count}
- **Folders Not Found**: {no_folder_count}
- **Files Not Matching**: {no_match_count}
- **Archive Location**: {archive_path}

## Details

### Successfully Cleaned
"""
    
    for r in results:
        if r['status'] == 'CLEANED':
            report += f"- **{r['customer_id']}** ({r['tenant']}): {r['action']}\n"
    
    report += "\n### Already Clean\n"
    for r in results:
        if r['status'] == 'EMPTY':
            report += f"- **{r['customer_id']}** ({r['tenant']}): Folder already empty\n"
    
    report += "\n### Issues\n"
    for r in results:
        if r['status'] in ['NO_FOLDER', 'NO_MATCH']:
            report += f"- **{r['customer_id']}** ({r['tenant']}): {r['action']}\n"
    
    report += f"""

## Next Steps

1. **For Cleaned Folders**: Obtain and upload correct credit reports
2. **For Missing Folders**: Create folders when credit reports are obtained
3. **For Snap Tire (c0000638)**: Upload the correct SnapTire PDF

## Folders Ready for New Credit Reports

The following folders are now empty and ready for correct credit reports:
"""
    
    for r in results:
        if r['status'] in ['CLEANED', 'EMPTY']:
            report += f"- {r['customer_id']}: {r['tenant']}\n"
    
    with open(report_path, 'w') as f:
        f.write(report)
    
    print(f"\n📄 Cleanup report saved to: {report_path}")
    return report_path

def check_folder_status():
    """Check the current status of all folders needing attention."""
    
    print("\n📁 Current Folder Status:")
    print("-"*40)
    
    for customer_id, info in PDFS_TO_REMOVE.items():
        folder_path = os.path.join(FOLDERS_DIR, customer_id)
        if os.path.exists(folder_path):
            files = os.listdir(folder_path)
            if files:
                print(f"📂 {customer_id}: Contains {len(files)} file(s)")
                for f in files:
                    print(f"   - {f}")
            else:
                print(f"📭 {customer_id}: Empty (ready for new credit report)")
        else:
            print(f"❌ {customer_id}: Folder doesn't exist")

if __name__ == "__main__":
    print("🔧 PDF Cleanup Tool")
    print("="*60)
    print("This tool will:")
    print("1. Remove wrong PDFs from customer folders")
    print("2. Archive removed files for safety")
    print("3. Prepare folders for correct credit reports")
    print()
    
    # Check current status
    check_folder_status()
    
    print("\n" + "="*60)
    response = input("Do you want to proceed with cleanup? (yes/no): ")
    
    if response.lower() == 'yes':
        # Perform cleanup
        results, archive_path = cleanup_wrong_pdfs()
        
        # Generate report
        report_path = generate_cleanup_report(results, archive_path)
        
        print("\n" + "="*60)
        print("✅ CLEANUP COMPLETE")
        print("="*60)
        print(f"📁 Archived files to: {archive_path}")
        print(f"📄 Report saved to: {report_path}")
        
        # Show final status
        print("\n📊 Final Status:")
        check_folder_status()
    else:
        print("\n❌ Cleanup cancelled. No changes made.")