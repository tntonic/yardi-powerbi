#!/usr/bin/env python3
"""
Extract tenant credit evaluation data from PDF files and create a CSV summary.
"""

import os
import re
import csv
import warnings
from pathlib import Path
import pdfplumber

# Suppress warnings
warnings.filterwarnings('ignore')

def extract_pdf_data(pdf_path):
    """Extract relevant data from a PDF file."""
    data = {
        'filename': os.path.basename(pdf_path),
        'tenant_name': '',
        'revenue': '',
        'website': '',
        'industry': '',
        'business_description': '',
        'credit_score': '',
        'probability_of_default': ''
    }
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Get text from first page (most info is there)
            if len(pdf.pages) > 0:
                text = pdf.pages[0].extract_text()
                if not text:
                    return data
                
                # Clean up text
                lines = text.split('\n')
                
                # Extract tenant/company name (usually at the top)
                for i, line in enumerate(lines[:10]):
                    if any(keyword in line for keyword in ['Corporation', 'Company', 'LLC', 'Inc', 'Group', 'Ltd']):
                        # Clean up company name
                        company_name = line.strip()
                        # Remove d/b/a or f/k/a patterns
                        company_name = re.sub(r'\(.*?[df]/[bk]/a.*?\)', '', company_name).strip()
                        if company_name and not company_name.startswith('Tenant'):
                            data['tenant_name'] = company_name
                            break
                
                # Extract website
                website_match = re.search(r'Website\s+(.+?(?:\.com|\.org|\.net|\.biz|\.io)[^\s]*)', text, re.IGNORECASE)
                if website_match:
                    data['website'] = website_match.group(1).strip()
                
                # Extract business description
                business_match = re.search(r'Business\s+([^\n]+)', text)
                if business_match:
                    data['business_description'] = business_match.group(1).strip()
                    data['industry'] = data['business_description']  # Often the same
                
                # Extract revenue (look for patterns like $XXM or $XX,XXX)
                revenue_patterns = [
                    r'Revenues?\s+\$?([\d,]+(?:\.\d+)?)[MmBb]',
                    r'Total Revenue.*?\$?([\d,]+)',
                    r'\$?([\d,]+(?:\.\d+)?)[MmBb]\s+(?:revenue|Revenue)'
                ]
                for pattern in revenue_patterns:
                    revenue_match = re.search(pattern, text)
                    if revenue_match:
                        revenue_str = revenue_match.group(1)
                        # Add M or B suffix if found
                        if 'M' in revenue_match.group(0) or 'm' in revenue_match.group(0):
                            data['revenue'] = f"${revenue_str}M"
                        elif 'B' in revenue_match.group(0) or 'b' in revenue_match.group(0):
                            data['revenue'] = f"${revenue_str}B"
                        else:
                            data['revenue'] = f"${revenue_str}"
                        break
                
                # Extract credit score (rating like BB, BBB, etc.)
                rating_patterns = [
                    r'\b([A-D]?[A-D]{1,3}[+\-]?)\s+1 year PD',
                    r'Rating.*?\b([A-D]?[A-D]{1,3}[+\-]?)\b',
                    r'\b(A{1,3}[+\-]?|B{1,3}[+\-]?|C{1,3}[+\-]?|D[+\-]?)\b(?!.*Supply)'
                ]
                for pattern in rating_patterns:
                    rating_match = re.search(pattern, text)
                    if rating_match:
                        rating = rating_match.group(1)
                        # Validate it's a credit rating
                        if re.match(r'^[A-D]{1,3}[+\-]?$', rating):
                            data['credit_score'] = rating
                            break
                
                # Extract probability of default (1 year PD)
                pd_patterns = [
                    r'1 year PD.*?([\d.]+%\s+to\s+[\d.]+%)',
                    r'([\d.]+%\s+to\s+[\d.]+%)\s*1 year PD',
                    r'1\s+year\s+PD[:\s]+([\d.]+%)'
                ]
                for pattern in pd_patterns:
                    pd_match = re.search(pattern, text, re.IGNORECASE)
                    if pd_match:
                        data['probability_of_default'] = pd_match.group(1).strip()
                        break
                
    except Exception as e:
        print(f"Error processing {pdf_path}: {str(e)}")
    
    return data

def main():
    """Main function to process all PDFs and create CSV."""
    # Get current directory
    current_dir = Path('/Users/michaeltang/Downloads/Credit/FP_TCE Reports')
    
    # Get all PDF files
    pdf_files = list(current_dir.glob('*.pdf'))
    print(f"Found {len(pdf_files)} PDF files to process")
    
    # Process each PDF
    all_data = []
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"Processing {i}/{len(pdf_files)}: {pdf_file.name}")
        data = extract_pdf_data(str(pdf_file))
        all_data.append(data)
    
    # Write to CSV
    csv_file = current_dir / 'tenant_credit_evaluation_summary.csv'
    
    fieldnames = ['filename', 'tenant_name', 'revenue', 'website', 'industry', 
                  'business_description', 'credit_score', 'probability_of_default']
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_data)
    
    print(f"\nCSV file created: {csv_file}")
    print(f"Total records: {len(all_data)}")

if __name__ == "__main__":
    main()