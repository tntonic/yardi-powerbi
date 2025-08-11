import pandas as pd

# Read the results from both matching approaches
original_match = pd.read_csv('joined_tenant_credit_data_final.csv')
enhanced_match = pd.read_csv('enhanced_matched_tenant_data.csv')

print("="*70)
print("TENANT CREDIT DATA MATCHING SUMMARY")
print("="*70)

# Count matches in original approach
original_matched = original_match['matched_value'].notna().sum()
original_unmatched = original_match['matched_value'].isna().sum()

# Count matches in enhanced approach
enhanced_matched = enhanced_match['matched_value'].notna().sum()
enhanced_unmatched = enhanced_match['matched_value'].isna().sum()
pdf_assisted = (enhanced_match['match_method'] == 'PDF-assisted').sum()

print("\n📊 MATCHING RESULTS COMPARISON:")
print("-"*50)
print(f"{'Method':<30} {'Matched':<15} {'Unmatched':<15}")
print("-"*50)
print(f"{'Original (tenant names only)':<30} {original_matched:<15} {original_unmatched:<15}")
print(f"{'Enhanced (with PDF data)':<30} {enhanced_matched:<15} {enhanced_unmatched:<15}")
print("-"*50)

if enhanced_matched == original_matched:
    print("\n✅ Same number of matches achieved, but with PDF validation providing higher confidence")
    print(f"   - PDF-assisted matches: {pdf_assisted} (validated via PDF documents)")
else:
    improvement = enhanced_matched - original_matched
    if improvement > 0:
        print(f"\n✅ Improvement: +{improvement} additional matches found using PDF data")
    else:
        print(f"\n⚠️  {abs(improvement)} fewer matches (stricter matching with PDF validation)")

# Show score comparison
if 'match_score' in original_match.columns and 'match_score' in enhanced_match.columns:
    original_avg_score = original_match[original_match['match_score'] > 0]['match_score'].mean()
    enhanced_avg_score = enhanced_match[enhanced_match['match_score'] > 0]['match_score'].mean()
    
    print(f"\n📈 MATCH QUALITY:")
    print(f"   Original average score: {original_avg_score:.1f}%")
    print(f"   Enhanced average score: {enhanced_avg_score:.1f}%")

# List tenants that were matched only with PDF assistance
pdf_only_matches = enhanced_match[
    (enhanced_match['match_method'] == 'PDF-assisted') & 
    (enhanced_match['matched_value'].notna())
]

if not pdf_only_matches.empty:
    print(f"\n🔍 KEY PDF-ASSISTED MATCHES ({len(pdf_only_matches)} total):")
    print("-"*50)
    sample_size = min(10, len(pdf_only_matches))
    for idx, row in pdf_only_matches.head(sample_size).iterrows():
        tenant = row['tenant_name']
        matched = row['matched_value']
        if pd.notna(row.get('credit_credit_score')):
            credit_score = row['credit_credit_score']
            credit_rating = row.get('credit_credit_rating', 'N/A')
            print(f"   {tenant[:35]:<35} → Credit Score: {credit_score}, Rating: {credit_rating}")
        else:
            print(f"   {tenant[:35]:<35} → {matched[:35]}")

# Show unmatched high-value tenants
unmatched = enhanced_match[enhanced_match['matched_value'].isna()]
if not unmatched.empty:
    print(f"\n⚠️  UNMATCHED TENANTS ({len(unmatched)} total):")
    print("-"*50)
    print("First 10 unmatched tenants that may need manual review:")
    for idx, tenant in enumerate(unmatched['tenant_name'].head(10)):
        if pd.notna(tenant):
            print(f"   {idx+1:2}. {tenant}")

print("\n" + "="*70)
print("OUTPUT FILES CREATED:")
print("  • enhanced_matched_tenant_data.csv - Full dataset with enhanced matching")
print("  • joined_tenant_credit_data_final.csv - Original matching results")
print("="*70)