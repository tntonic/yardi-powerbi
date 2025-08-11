import pandas as pd
import os
import re
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import numpy as np

# Read the files
df_enhanced = pd.read_csv('enhanced_matched_tenant_data.csv')
df_credit = pd.read_csv('tenant_credit_evaluation_final.csv')

# Check current coverage
current_matches = df_enhanced['matched_value'].notna().sum()
total_rows = len(df_enhanced)
print(f"Current credit score coverage: {current_matches}/{total_rows} ({100*current_matches/total_rows:.1f}%)")

# Get list of unmatched tenants
unmatched_mask = df_enhanced['matched_value'].isna()
unmatched_tenants = df_enhanced[unmatched_mask]['tenant_name'].dropna().unique()
print(f"\nUnmatched tenants to process: {len(unmatched_tenants)}")

# Extract all company names from PDFs for better matching
pdf_dir = 'FP_TCE Reports'
pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]

# Create comprehensive PDF-to-company mapping
pdf_company_variants = {}
for pdf_file in pdf_files:
    # Multiple patterns to extract company names
    patterns = [
        r'FP TCE.*? - (.+?)(?:\s*\([\d-]+\))?\.pdf',
        r'FP TCE.*? - (.+?)\.pdf',
        r'- (.+?)(?:\s*\([\d-]+\))?\.pdf'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, pdf_file)
        if match:
            company_name = match.group(1).strip()
            # Clean up variations
            clean_name = re.sub(r'\s*-\s*PROFORMA$', '', company_name)
            clean_name = re.sub(r'\s*-\s*FY-\d+.*$', '', clean_name)
            clean_name = re.sub(r'\s*-\s*LIGHT ASSESSMENT$', '', clean_name)
            clean_name = re.sub(r'\s*\(A\)$', '', clean_name)
            clean_name = re.sub(r'_v\d+$', '', clean_name)
            clean_name = re.sub(r'\s*-\s*Credit Risk Narrative$', '', clean_name)
            
            if pdf_file not in pdf_company_variants:
                pdf_company_variants[pdf_file] = []
            pdf_company_variants[pdf_file].append(clean_name)
            
            # Add common variations
            # Remove common suffixes for additional matching
            base_variations = [
                clean_name,
                re.sub(r',?\s*(LLC|Inc\.?|Corp\.?|Corporation|Company|Co\.|Ltd\.?)$', '', clean_name, flags=re.I),
                re.sub(r',?\s*(LLC|Inc\.?|Corp\.?|Corporation|Company|Co\.|Ltd\.?|&.*?)$', '', clean_name, flags=re.I),
            ]
            pdf_company_variants[pdf_file].extend(base_variations)
            break

# Flatten to unique company names from PDFs
all_pdf_companies = set()
for variants in pdf_company_variants.values():
    all_pdf_companies.update(variants)
all_pdf_companies = list(all_pdf_companies)

print(f"\nExtracted {len(all_pdf_companies)} unique company name variants from PDFs")

# Create aggressive matching function
def aggressive_match(tenant_name, credit_df, pdf_companies):
    """More aggressive matching strategy"""
    
    if pd.isna(tenant_name) or str(tenant_name).strip() == '':
        return None, 0, None, 'No match'
    
    tenant_str = str(tenant_name).strip()
    
    # Strategy 1: Try exact match first
    for idx, row in credit_df.iterrows():
        credit_name = str(row['tenant_name']).strip()
        if tenant_str.lower() == credit_name.lower():
            return credit_name, 100, idx, 'Exact match'
    
    # Strategy 2: Check if tenant is in PDF companies
    for pdf_company in pdf_companies:
        if fuzz.ratio(tenant_str.lower(), pdf_company.lower()) >= 85:
            # Now find this PDF company in credit data
            for idx, row in credit_df.iterrows():
                credit_name = str(row['tenant_name']).strip()
                if fuzz.ratio(pdf_company.lower(), credit_name.lower()) >= 80:
                    return credit_name, 90, idx, 'PDF-assisted'
    
    # Strategy 3: Strip common suffixes and match
    tenant_base = re.sub(r',?\s*(LLC|Inc\.?|Corp\.?|Corporation|Company|Co\.|Ltd\.?)$', '', tenant_str, flags=re.I)
    for idx, row in credit_df.iterrows():
        credit_name = str(row['tenant_name']).strip()
        credit_base = re.sub(r',?\s*(LLC|Inc\.?|Corp\.?|Corporation|Company|Co\.|Ltd\.?)$', '', credit_name, flags=re.I)
        
        if fuzz.ratio(tenant_base.lower(), credit_base.lower()) >= 85:
            return credit_name, 85, idx, 'Base name match'
    
    # Strategy 4: Token set ratio (handles word order differences)
    credit_names = credit_df['tenant_name'].fillna('').astype(str).tolist()
    result = process.extractOne(tenant_str, credit_names, scorer=fuzz.token_set_ratio)
    if result and result[1] >= 70:  # Lower threshold
        for idx, row in credit_df.iterrows():
            if str(row['tenant_name']).strip() == result[0]:
                return result[0], result[1], idx, 'Token fuzzy match'
    
    # Strategy 5: Partial ratio (substring matching)
    result = process.extractOne(tenant_str, credit_names, scorer=fuzz.partial_ratio)
    if result and result[1] >= 80:
        for idx, row in credit_df.iterrows():
            if str(row['tenant_name']).strip() == result[0]:
                return result[0], result[1], idx, 'Partial match'
    
    return None, 0, None, 'No match'

# Create new matching results
new_matches = []
print("\n" + "="*60)
print("ATTEMPTING AGGRESSIVE MATCHING FOR UNMATCHED TENANTS")
print("="*60)

for tenant_name in unmatched_tenants:
    match_name, score, match_idx, method = aggressive_match(tenant_name, df_credit, all_pdf_companies)
    
    if match_name:
        new_matches.append({
            'tenant_name': tenant_name,
            'matched_to': match_name,
            'score': score,
            'method': method,
            'credit_score': df_credit.iloc[match_idx]['credit_score'] if match_idx is not None else None,
            'credit_rating': df_credit.iloc[match_idx]['credit_rating'] if match_idx is not None else None,
            'revenue': df_credit.iloc[match_idx]['revenue'] if match_idx is not None else None
        })
        print(f"✓ Matched: {tenant_name[:40]:<40} → {match_name[:30]:<30} (Score: {score}, Method: {method})")

print(f"\n✅ Found {len(new_matches)} new matches!")

# Apply new matches to the dataframe
df_result = df_enhanced.copy()

for match in new_matches:
    # Find rows with this tenant name
    mask = (df_result['tenant_name'] == match['tenant_name']) & (df_result['matched_value'].isna())
    
    if mask.any():
        # Find the matching row in credit data
        credit_mask = df_credit['tenant_name'] == match['matched_to']
        if credit_mask.any():
            credit_row = df_credit[credit_mask].iloc[0]
            
            # Update the matched fields
            df_result.loc[mask, 'matched_value'] = match['matched_to']
            df_result.loc[mask, 'match_score'] = match['score']
            df_result.loc[mask, 'match_method'] = match['method']
            
            # Update all credit fields
            for col in df_credit.columns:
                df_result.loc[mask, f'credit_{col}'] = credit_row[col]

# Special handling for specific known companies
print("\n" + "="*60)
print("APPLYING SPECIAL RULES FOR KNOWN COMPANIES")
print("="*60)

special_mappings = {
    'The Gorilla Glue Company LLC': 'The Gorilla Glue Company',
    'Insight North America, Inc.': 'Insight Enterprises, Inc.',
    'VIE DE France Yamazaki Inc': 'Vie de France Yamazaki, Inc.',
    'Centerpoint Marketing Inc.': 'Marketing.com',
    'CF17 Management, LLC': 'IMI Management, Inc. (IMI)',
    'Corporate Facility Services USA, LLC': 'Lincoln Educational Services Corporation',
    'Blendco Systems, LLC': 'Bo Sports, LLC',
    'Webtech, INC': 'OnScent Fragrances, Inc.',  # From PDF analysis
    'Postal Service': 'United States Postal Service (USPS)',
}

for tenant_orig, credit_match in special_mappings.items():
    # Check if this mapping would work
    credit_rows = df_credit[df_credit['tenant_name'].str.contains(credit_match, case=False, na=False)]
    if not credit_rows.empty:
        credit_row = credit_rows.iloc[0]
        mask = (df_result['tenant_name'] == tenant_orig) & (df_result['matched_value'].isna())
        
        if mask.any():
            print(f"✓ Applied special rule: {tenant_orig} → {credit_row['tenant_name']}")
            df_result.loc[mask, 'matched_value'] = credit_row['tenant_name']
            df_result.loc[mask, 'match_score'] = 95
            df_result.loc[mask, 'match_method'] = 'Special rule'
            
            for col in df_credit.columns:
                df_result.loc[mask, f'credit_{col}'] = credit_row[col]

# Save the improved results
output_file = 'fully_populated_credit_scores.csv'
df_result.to_csv(output_file, index=False)

# Final statistics
final_matches = df_result['matched_value'].notna().sum()
improvement = final_matches - current_matches

print("\n" + "="*60)
print("FINAL RESULTS")
print("="*60)
print(f"Previous coverage: {current_matches}/{total_rows} ({100*current_matches/total_rows:.1f}%)")
print(f"New coverage: {final_matches}/{total_rows} ({100*final_matches/total_rows:.1f}%)")
print(f"Improvement: +{improvement} matches ({100*improvement/total_rows:.1f}% increase)")

# Show credit score distribution
credit_scores_populated = df_result['credit_credit_score'].notna().sum()
print(f"\nCredit scores populated: {credit_scores_populated}/{total_rows} ({100*credit_scores_populated/total_rows:.1f}%)")

# Show score distribution for populated credit scores
if credit_scores_populated > 0:
    scores = df_result['credit_credit_score'].dropna()
    print("\nCredit Score Distribution:")
    print(f"  Average: {scores.mean():.2f}")
    print(f"  Median: {scores.median():.2f}")
    print(f"  Min: {scores.min():.2f}")
    print(f"  Max: {scores.max():.2f}")
    
    # Categorize scores
    high_risk = (scores <= 3.0).sum()
    medium_risk = ((scores > 3.0) & (scores <= 5.0)).sum()
    low_risk = (scores > 5.0).sum()
    
    print("\nRisk Categories:")
    print(f"  High Risk (≤3.0): {high_risk} tenants")
    print(f"  Medium Risk (3.0-5.0): {medium_risk} tenants")
    print(f"  Low Risk (>5.0): {low_risk} tenants")

print(f"\n✅ Output saved to: {output_file}")