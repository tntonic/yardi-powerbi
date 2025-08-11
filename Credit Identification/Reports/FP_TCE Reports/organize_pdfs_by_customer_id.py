#!/usr/bin/env python3
"""
Organize PDF credit reports by customer ID (c0000xxx format).
Reads customer ID mappings from CSV and copies PDFs to organized folder.
"""

import os
import re
import csv
import shutil
from pathlib import Path
from difflib import SequenceMatcher
import warnings

# Suppress warnings
warnings.filterwarnings('ignore')

def clean_filename(text):
    """Clean text for use in filename."""
    # Remove special characters but keep underscores and hyphens
    text = re.sub(r'[^\w\s-]', '', text)
    # Replace spaces with underscores
    text = re.sub(r'\s+', '_', text)
    # Remove multiple underscores
    text = re.sub(r'_+', '_', text)
    return text.strip('_')

def extract_company_from_pdf_name(pdf_filename):
    """Extract company name from PDF filename."""
    # Pattern: FP TCE_vX.XX - Company Name (date).pdf
    match = re.search(r'FP TCE.*?-\s*(.+?)\s*\([\d-]+\)\.pdf', pdf_filename)
    if match:
        company = match.group(1).strip()
        # Remove common suffixes like "PROFORMA", "FY-24", etc.
        company = re.sub(r'\s*-?\s*(PROFORMA|FY-\d+|v\d+|\(A\)).*$', '', company)
        return company.strip()
    return None

def fuzzy_match_score(str1, str2):
    """Calculate fuzzy match score between two strings."""
    if not str1 or not str2:
        return 0
    
    # Normalize strings for comparison
    str1_norm = str1.lower().strip()
    str2_norm = str2.lower().strip()
    
    # Remove common company suffixes for matching
    for suffix in ['llc', 'inc', 'corp', 'corporation', 'company', 'ltd', 'limited', 
                   'group', 'partners', 'industries', 'co', '.', ',', '&']:
        str1_norm = str1_norm.replace(suffix, ' ')
        str2_norm = str2_norm.replace(suffix, ' ')
    
    # Clean up multiple spaces
    str1_norm = ' '.join(str1_norm.split())
    str2_norm = ' '.join(str2_norm.split())
    
    # Calculate similarity ratio
    return SequenceMatcher(None, str1_norm, str2_norm).ratio() * 100

def load_customer_mappings(csv_path):
    """Load customer ID mappings from CSV file."""
    mappings = {}
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            customer_id = row.get('customer_id', '').strip()
            tenant_name = row.get('tenant_name', '').strip()
            eval_filename = row.get('eval_filename', '').strip()
            matched_name = row.get('matched_tenant_name', '').strip()
            
            if customer_id and customer_id.startswith('c'):
                # Store all variations for matching
                mappings[customer_id] = {
                    'tenant_name': tenant_name,
                    'eval_filename': eval_filename,
                    'matched_name': matched_name,
                    'all_names': [n for n in [tenant_name, matched_name] if n]
                }
    
    return mappings

def find_customer_id_for_pdf(pdf_filename, mappings):
    """Find customer ID for a given PDF filename."""
    pdf_company = extract_company_from_pdf_name(pdf_filename)
    if not pdf_company:
        return None, None, 0
    
    best_match = None
    best_score = 0
    best_tenant_name = None
    
    for customer_id, data in mappings.items():
        # Check for exact filename match first
        if data['eval_filename'] and pdf_filename == data['eval_filename']:
            return customer_id, data['tenant_name'], 100
        
        # Fuzzy match against all known names
        for name in data['all_names']:
            score = fuzzy_match_score(pdf_company, name)
            if score > best_score:
                best_score = score
                best_match = customer_id
                best_tenant_name = data['tenant_name']
    
    # Return match if score is high enough (threshold: 80%)
    if best_score >= 80:
        return best_match, best_tenant_name, best_score
    
    return None, None, best_score

def organize_pdfs():
    """Main function to organize PDFs by customer ID."""
    # Paths
    base_dir = Path('/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Credit Identification/Reports/FP_TCE Reports')
    csv_path = base_dir / 'final_tenants_with_all_evaluations.csv'
    output_dir = base_dir / 'FP_TCE_Reports_Organized'
    
    # Create output directory
    output_dir.mkdir(exist_ok=True)
    
    # Load customer mappings
    print("Loading customer ID mappings...")
    mappings = load_customer_mappings(csv_path)
    print(f"Loaded {len(mappings)} customer ID mappings")
    
    # Get all PDF files
    pdf_files = list(base_dir.glob('FP TCE*.pdf'))
    print(f"Found {len(pdf_files)} PDF files to organize")
    
    # Track results
    successful = []
    unmatched = []
    errors = []
    
    # Process each PDF
    print("\nProcessing PDFs...")
    for pdf_path in pdf_files:
        pdf_filename = pdf_path.name
        
        try:
            # Find customer ID
            customer_id, tenant_name, score = find_customer_id_for_pdf(pdf_filename, mappings)
            
            if customer_id:
                # Create new filename
                company_clean = clean_filename(tenant_name or extract_company_from_pdf_name(pdf_filename))
                new_filename = f"{customer_id}_{company_clean}.pdf"
                new_path = output_dir / new_filename
                
                # Copy file
                shutil.copy2(pdf_path, new_path)
                
                successful.append({
                    'original': pdf_filename,
                    'new': new_filename,
                    'customer_id': customer_id,
                    'tenant_name': tenant_name,
                    'match_score': score
                })
                print(f"✓ {pdf_filename} → {new_filename} (Score: {score:.1f}%)")
            else:
                unmatched.append({
                    'filename': pdf_filename,
                    'company': extract_company_from_pdf_name(pdf_filename),
                    'best_score': score
                })
                print(f"✗ {pdf_filename} - No match found (Best score: {score:.1f}%)")
                
        except Exception as e:
            errors.append({'filename': pdf_filename, 'error': str(e)})
            print(f"✗ Error processing {pdf_filename}: {e}")
    
    # Generate summary report
    generate_report(successful, unmatched, errors, output_dir)
    
    # Print summary
    print("\n" + "="*60)
    print("ORGANIZATION COMPLETE")
    print("="*60)
    print(f"✓ Successfully organized: {len(successful)} PDFs")
    print(f"✗ Unmatched: {len(unmatched)} PDFs")
    print(f"⚠ Errors: {len(errors)} PDFs")
    print(f"\nOrganized PDFs saved to: {output_dir}")
    print(f"Summary report: {output_dir / 'organization_report.txt'}")

def generate_report(successful, unmatched, errors, output_dir):
    """Generate a detailed report of the organization process."""
    report_path = output_dir / 'organization_report.txt'
    
    with open(report_path, 'w') as f:
        f.write("PDF ORGANIZATION REPORT\n")
        f.write("="*60 + "\n\n")
        
        # Summary statistics
        f.write("SUMMARY\n")
        f.write("-"*30 + "\n")
        f.write(f"Total PDFs processed: {len(successful) + len(unmatched) + len(errors)}\n")
        f.write(f"Successfully organized: {len(successful)}\n")
        f.write(f"Unmatched: {len(unmatched)}\n")
        f.write(f"Errors: {len(errors)}\n\n")
        
        # Successfully organized
        f.write("SUCCESSFULLY ORGANIZED\n")
        f.write("-"*30 + "\n")
        for item in sorted(successful, key=lambda x: x['customer_id']):
            f.write(f"{item['customer_id']} - {item['tenant_name']}\n")
            f.write(f"  Original: {item['original']}\n")
            f.write(f"  New: {item['new']}\n")
            f.write(f"  Match Score: {item['match_score']:.1f}%\n\n")
        
        # Unmatched PDFs
        if unmatched:
            f.write("\nUNMATCHED PDFS\n")
            f.write("-"*30 + "\n")
            for item in sorted(unmatched, key=lambda x: x['filename']):
                f.write(f"{item['filename']}\n")
                f.write(f"  Extracted Company: {item['company']}\n")
                f.write(f"  Best Match Score: {item['best_score']:.1f}%\n\n")
        
        # Errors
        if errors:
            f.write("\nERRORS\n")
            f.write("-"*30 + "\n")
            for item in errors:
                f.write(f"{item['filename']}: {item['error']}\n")
    
    # Also create a CSV summary for easy analysis
    csv_path = output_dir / 'organization_summary.csv'
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Status', 'Customer_ID', 'Tenant_Name', 'Original_Filename', 'New_Filename', 'Match_Score'])
        
        for item in successful:
            writer.writerow(['Matched', item['customer_id'], item['tenant_name'], 
                           item['original'], item['new'], f"{item['match_score']:.1f}"])
        
        for item in unmatched:
            writer.writerow(['Unmatched', '', item['company'], item['filename'], '', 
                           f"{item['best_score']:.1f}"])

if __name__ == "__main__":
    organize_pdfs()