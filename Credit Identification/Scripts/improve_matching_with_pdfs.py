import pandas as pd
import os
import re
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import numpy as np

# Read the CSV files
df1 = pd.read_csv('new_tenants_fund2_fund3_since_2025_populated.csv')
df2 = pd.read_csv('tenant_credit_evaluation_final.csv')

# Extract tenant names from PDF filenames
pdf_dir = 'FP_TCE Reports'
pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]

# Extract company names from PDF filenames
pdf_tenant_map = {}
for pdf_file in pdf_files:
    # Pattern to extract company name from filename
    # Format: FP TCE_vX.XX - Company Name (date).pdf
    match = re.search(r'FP TCE.*? - (.+?)(?:\s*\([\d-]+\))?\.pdf', pdf_file)
    if match:
        company_name = match.group(1).strip()
        # Clean up company name
        company_name = re.sub(r'\s*-\s*PROFORMA$', '', company_name)
        company_name = re.sub(r'\s*-\s*FY-\d+.*$', '', company_name)
        company_name = re.sub(r'\s*-\s*LIGHT ASSESSMENT$', '', company_name)
        company_name = re.sub(r'\s*\(A\)$', '', company_name)
        company_name = re.sub(r'_v\d+$', '', company_name)
        pdf_tenant_map[pdf_file] = company_name

# Create a list of unique company names from PDFs
pdf_companies = list(set(pdf_tenant_map.values()))
print(f"Found {len(pdf_companies)} unique companies from {len(pdf_files)} PDF files")

# Create a mapping between df1 tenant names and PDF company names
print("\n=== Matching Tenant Names from CSV with PDF Company Names ===")
tenant_to_pdf = {}
for tenant in df1['tenant_name'].dropna().unique():
    # Try to find best match in PDF companies
    result = process.extractOne(str(tenant), pdf_companies, scorer=fuzz.token_sort_ratio)
    if result and result[1] >= 80:  # High threshold for name matching
        tenant_to_pdf[tenant] = result[0]
        print(f"Matched: {tenant} -> {result[0]} (score: {result[1]})")

print(f"\nMatched {len(tenant_to_pdf)} tenants with PDF companies")

# Now let's see if these PDF companies are in df2
print("\n=== Checking if PDF Companies exist in Credit Evaluation File ===")
pdf_in_df2 = {}
for pdf_company in pdf_companies:
    # Try to find in df2
    result = process.extractOne(pdf_company, 
                                df2['tenant_name'].dropna().astype(str).tolist(), 
                                scorer=fuzz.token_sort_ratio)
    if result and result[1] >= 80:
        pdf_in_df2[pdf_company] = result[0]

print(f"Found {len(pdf_in_df2)} PDF companies in credit evaluation file")

# Create enhanced matching using PDF information
print("\n=== Enhanced Matching Using PDF Information ===")

def enhanced_match(tenant_name, df2_names, pdf_mapping):
    """Enhanced matching that uses PDF information as additional context"""
    
    if pd.isna(tenant_name):
        return None, 0, None
    
    tenant_str = str(tenant_name).strip()
    
    # First check if we have a PDF mapping for this tenant
    if tenant_str in tenant_to_pdf:
        pdf_company = tenant_to_pdf[tenant_str]
        # Check if this PDF company is in df2
        if pdf_company in pdf_in_df2:
            df2_match = pdf_in_df2[pdf_company]
            # Find index in df2
            for idx, name in enumerate(df2_names):
                if name == df2_match:
                    return df2_match, 95, idx  # High confidence match via PDF
    
    # Fall back to regular fuzzy matching
    choices_dict = {name: idx for idx, name in enumerate(df2_names)}
    result = process.extractOne(tenant_str, choices_dict.keys(), scorer=fuzz.token_sort_ratio)
    
    if result and result[1] >= 75:
        return result[0], result[1], choices_dict[result[0]]
    else:
        return None, 0, None

# Prepare df2 names
df2_names = df2['tenant_name'].fillna('').astype(str).tolist()

# Perform enhanced matching
matches = []
match_scores = []
match_indices = []
match_methods = []

for idx, tenant_name in enumerate(df1['tenant_name']):
    if idx % 50 == 0:
        print(f"Processing row {idx}/{len(df1)}...")
    
    match, score, match_idx = enhanced_match(tenant_name, df2_names, pdf_in_df2)
    matches.append(match)
    match_scores.append(score)
    match_indices.append(match_idx)
    
    # Track matching method
    if match and score == 95 and str(tenant_name) in tenant_to_pdf:
        match_methods.append('PDF-assisted')
    elif match:
        match_methods.append('Fuzzy match')
    else:
        match_methods.append('No match')

# Create result dataframe
df_result = df1.copy()
df_result['matched_value'] = matches
df_result['match_score'] = match_scores
df_result['match_method'] = match_methods

# Add all columns from df2 with 'credit_' prefix
for col in df2.columns:
    df_result[f'credit_{col}'] = None

# Fill in the matched data
for idx, match_idx in enumerate(match_indices):
    if match_idx is not None:
        row = df2.iloc[match_idx]
        for col in df2.columns:
            df_result.loc[idx, f'credit_{col}'] = row[col]

# Save the enhanced result
output_file = 'enhanced_matched_tenant_data.csv'
df_result.to_csv(output_file, index=False)

print(f"\n✅ Enhanced matching completed!")
print(f"Output saved to: {output_file}")
print(f"Total rows: {len(df_result)}")
print(f"Matched rows: {sum(1 for m in matches if m is not None)}")
print(f"  - PDF-assisted matches: {sum(1 for m in match_methods if m == 'PDF-assisted')}")
print(f"  - Fuzzy matches: {sum(1 for m in match_methods if m == 'Fuzzy match')}")
print(f"Unmatched rows: {sum(1 for m in matches if m is None)}")

# Show match score distribution
if sum(1 for m in matches if m is not None) > 0:
    avg_score = np.mean([s for s in match_scores if s > 0])
    print(f"Average match score: {avg_score:.1f}%")
    
    print("\nMatch score distribution:")
    score_ranges = [(90, 100), (80, 89), (70, 79)]
    for low, high in score_ranges:
        count = sum(1 for s in match_scores if low <= s <= high)
        if count > 0:
            print(f"  {low}-{high}%: {count} matches")

# Display sample results
print("\nSample of enhanced matches:")
enhanced_df = df_result[df_result['match_method'] == 'PDF-assisted']
if not enhanced_df.empty:
    print("\nPDF-assisted matches (high confidence):")
    print(enhanced_df[['tenant_name', 'matched_value', 'match_score', 'match_method']].head(10).to_string())

regular_df = df_result[(df_result['match_method'] == 'Fuzzy match') & (df_result['match_score'] >= 90)]
if not regular_df.empty:
    print("\nHigh-confidence fuzzy matches:")
    print(regular_df[['tenant_name', 'matched_value', 'match_score']].head(5).to_string())

# Show some interesting PDF mappings found
if tenant_to_pdf:
    print("\n=== Interesting PDF Name Mappings Found ===")
    for tenant, pdf_name in list(tenant_to_pdf.items())[:10]:
        if tenant != pdf_name:  # Show only where names differ
            print(f"  {tenant} -> {pdf_name}")