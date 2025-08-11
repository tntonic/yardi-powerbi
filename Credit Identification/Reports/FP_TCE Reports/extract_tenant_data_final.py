#!/usr/bin/env python3
"""
Final version: Extract tenant credit evaluation data from PDF files with numerical credit scores.
"""

import os
import re
import csv
import warnings
from pathlib import Path
import pdfplumber

# Suppress warnings
warnings.filterwarnings('ignore')

def clean_company_name(name):
    """Clean up company name by removing extra information."""
    # Remove probability percentages
    name = re.sub(r'^\d+\.\d+%\s+to\s+\d+\.\d+%.*', '', name)
    # Remove benchmark info
    name = re.sub(r'#\s+of\s+Benchmarks:.*', '', name)
    # Remove d/b/a or f/k/a patterns but keep the company name
    name = re.sub(r'\s*\(.*?[df]/[bk]/a.*?\)', '', name)
    # Remove trailing numbers and special characters
    name = re.sub(r'\s+\d+\.\d+\s*$', '', name)
    # Clean up quotes
    name = name.replace('""', '"').replace('"', '')
    return name.strip()

def extract_pdf_data(pdf_path):
    """Extract relevant data from a PDF file with numerical credit scores."""
    data = {
        'filename': os.path.basename(pdf_path),
        'tenant_name': '',
        'revenue': '',
        'website': '',
        'industry': '',
        'business_description': '',
        'credit_score': '',
        'credit_rating': '',
        'probability_of_default': ''
    }
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Get text from first page
            if len(pdf.pages) > 0:
                text = pdf.pages[0].extract_text()
                if not text:
                    return data
                
                lines = text.split('\n')
                
                # Extract numerical credit score (the gauge value like 3.00, 6.50, etc.)
                # This typically appears near the top of the document
                score_patterns = [
                    r'\b(\d\.\d{2})\b(?:\s+[A-Z]{1,3}[+-]?\s+)',  # Score followed by rating
                    r'(?:^|\n)\s*(\d\.\d{2})\s*(?:\n|$)',  # Score on its own line
                    r'(?:^|\s)(\d\.\d{2})(?:\s+(?:AA|A|BBB|BB|B|CCC|CC|C|D))',  # Score with rating
                    r'(?:Summary|Snapshot)[\s\S]{0,200}?(\d\.\d{2})\s+[A-Z]'  # Score after Summary/Snapshot
                ]
                
                for pattern in score_patterns:
                    score_match = re.search(pattern, text[:2000], re.MULTILINE)  # Look in first part of document
                    if score_match:
                        score = score_match.group(1)
                        # Validate it's a reasonable credit score (typically 1.00 to 10.00)
                        try:
                            score_float = float(score)
                            if 0.5 <= score_float <= 10.0:
                                data['credit_score'] = score
                                break
                        except:
                            pass
                
                # Extract letter credit rating (BB, BBB, etc.)
                rating_patterns = [
                    r'\b(AAA?|BBB?|CCC?|CC?|DD?|[AB][+-]?)\b\s+1\s+year\s+PD',
                    r'1\s+year\s+PD\s+\b(AAA?|BBB?|CCC?|CC?|DD?|[AB][+-]?)\b',
                    r'\d\.\d{2}\s+(AAA?|BBB?|CCC?|CC?|DD?|[AB][+-]?)\s',
                    r'Rating.*?\b(AAA?|BBB?|CCC?|CC?|DD?|[AB][+-]?)\b'
                ]
                for pattern in rating_patterns:
                    rating_match = re.search(pattern, text)
                    if rating_match:
                        rating = rating_match.group(1).strip()
                        if re.match(r'^[A-D]{1,3}[+-]?$', rating):
                            data['credit_rating'] = rating
                            break
                
                # Extract tenant/company name (improved)
                for i, line in enumerate(lines[:20]):
                    # Skip lines that are clearly not company names
                    if any(skip in line.lower() for skip in ['tenant credit', 'summary', 'snapshot', 'light assessment', 
                                                              'financial', 'benchmarks', 'company overview']):
                        continue
                    
                    # Look for company indicators
                    if any(keyword in line for keyword in ['Corporation', 'Company', 'LLC', 'Inc.', 'Inc ', 'L.L.C.', 
                                                           'Ltd', 'Group', 'Partners', 'Industries', 'Corp']):
                        company_name = clean_company_name(line)
                        # Additional validation
                        if company_name and len(company_name) > 3 and not company_name.startswith('FP TCE'):
                            data['tenant_name'] = company_name
                            break
                
                # If no company name found, try alternative patterns
                if not data['tenant_name']:
                    # Look for pattern after "Summary" or "Snapshot"
                    for i, line in enumerate(lines):
                        if 'Summary' in line or 'Snapshot' in line:
                            if i + 1 < len(lines):
                                next_line = lines[i + 1]
                                if not any(skip in next_line.lower() for skip in ['financial', 'company overview', 'weight']):
                                    company_name = clean_company_name(next_line)
                                    if company_name and len(company_name) > 3:
                                        data['tenant_name'] = company_name
                                        break
                
                # Extract website (improved)
                website_patterns = [
                    r'Website\s+([^\s]+(?:\.com|\.org|\.net|\.biz|\.io|\.co)[^\s]*)',
                    r'https?://[^\s]+',
                    r'www\.[^\s]+'
                ]
                for pattern in website_patterns:
                    website_match = re.search(pattern, text, re.IGNORECASE)
                    if website_match:
                        website = website_match.group(0) if pattern.startswith('http') else website_match.group(1)
                        # Clean up website
                        website = website.replace('Website', '').strip()
                        if not website.startswith('http'):
                            website = website.replace('www.', 'https://www.') if 'www.' in website else 'https://' + website
                        # Remove trailing characters
                        website = re.sub(r'[;,\s]+$', '', website)
                        data['website'] = website
                        break
                
                # Extract business description (improved)
                business_patterns = [
                    r'Business\s+([^$\n]+?)(?:Revenues?|Adjusted|Income Statement|Gross Profit)',
                    r'Business\s+([^\n]+)',
                ]
                for pattern in business_patterns:
                    business_match = re.search(pattern, text, re.IGNORECASE)
                    if business_match:
                        description = business_match.group(1).strip()
                        # Clean up description
                        description = re.sub(r'\s+Adjusted EBITDA.*', '', description)
                        description = re.sub(r'\s+Gross Profit.*', '', description)
                        description = re.sub(r'\s+Total Revenue.*', '', description)
                        description = re.sub(r'\s+EBITDA Margin.*', '', description)
                        description = re.sub(r'\s+Profitability.*', '', description)
                        data['business_description'] = description.strip()
                        data['industry'] = description.strip()  # Often the same
                        break
                
                # Extract revenue (improved)
                revenue_patterns = [
                    r'Revenues?\s+\$?([\d,]+(?:\.\d+)?)\s*([MmBb])',
                    r'Total Revenue[^\$]*\$?([\d,]+(?:\.\d+)?)\s*([MmBb]?)',
                    r'\$?([\d,]+(?:\.\d+)?)\s*([MmBb])\s+(?:revenue|Revenue)',
                    r'Revenue\s+\$?([\d,]+)(?:\s+|$)'
                ]
                for pattern in revenue_patterns:
                    revenue_match = re.search(pattern, text)
                    if revenue_match:
                        revenue_str = revenue_match.group(1).replace(',', '')
                        suffix = ''
                        if len(revenue_match.groups()) > 1 and revenue_match.group(2):
                            suffix = revenue_match.group(2).upper()
                        
                        # Format revenue
                        if suffix in ['M', 'B']:
                            data['revenue'] = f"${revenue_str}{suffix}"
                        elif float(revenue_str) > 1000000:
                            # Convert to millions if large number
                            revenue_m = float(revenue_str) / 1000000
                            data['revenue'] = f"${revenue_m:.1f}M"
                        else:
                            data['revenue'] = f"${revenue_str}"
                        break
                
                # Extract probability of default (improved)
                pd_patterns = [
                    r'([\d.]+%\s+to\s+[\d.]+%)\s*1\s+year\s+PD',
                    r'1\s+year\s+PD[:\s]+([\d.]+%\s+to\s+[\d.]+%)',
                    r'1\s+year\s+PD.*?([\d.]+%)'
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
    csv_file = current_dir / 'tenant_credit_evaluation_final.csv'
    
    fieldnames = ['filename', 'tenant_name', 'revenue', 'website', 'industry', 
                  'business_description', 'credit_score', 'credit_rating', 'probability_of_default']
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_data)
    
    print(f"\nCSV file created: {csv_file}")
    print(f"Total records: {len(all_data)}")
    
    # Print some statistics
    companies_found = sum(1 for d in all_data if d['tenant_name'])
    revenues_found = sum(1 for d in all_data if d['revenue'])
    scores_found = sum(1 for d in all_data if d['credit_score'])
    ratings_found = sum(1 for d in all_data if d['credit_rating'])
    
    print(f"\nExtraction Statistics:")
    print(f"  Company names found: {companies_found}/{len(all_data)}")
    print(f"  Revenues found: {revenues_found}/{len(all_data)}")
    print(f"  Numerical credit scores found: {scores_found}/{len(all_data)}")
    print(f"  Letter credit ratings found: {ratings_found}/{len(all_data)}")

if __name__ == "__main__":
    main()