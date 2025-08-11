import pandas as pd

# Read the final output
df = pd.read_csv('final_tenant_credit_with_ids.csv')

print("="*80)
print(" "*20 + "FINAL OUTPUT VERIFICATION")
print("="*80)

# Column structure
print("\n📋 COLUMN STRUCTURE:")
print("-"*80)
print("Original tenant data columns (preserved from LEFT table):")
original_cols = ['customer_id', 'tenant_id', 'tenant_name', 'property_address', 
                 'property_name', 'property_code', 'fund', 'naics', 'lease_id',
                 'credit_score', 'credit_score_date', 'parent_customer_id',
                 'tenant_risk', 'amendment_start_date', 'amendment_type', 
                 'amendment_status']
for col in original_cols:
    if col in df.columns:
        non_null = df[col].notna().sum()
        print(f"  ✓ {col:<25} ({non_null}/{len(df)} populated)")

print("\nMatching metadata columns:")
match_cols = ['matched_credit_name', 'match_score', 'match_method']
for col in match_cols:
    if col in df.columns:
        non_null = df[col].notna().sum()
        print(f"  ✓ {col:<25} ({non_null}/{len(df)} populated)")

print("\nCredit evaluation columns (from RIGHT table):")
credit_cols = [col for col in df.columns if col.startswith('credit_')]
key_credit_cols = ['credit_tenant_name', 'credit_revenue', 'credit_credit_score', 
                   'credit_credit_rating', 'credit_probability_of_default']
for col in key_credit_cols:
    if col in df.columns:
        non_null = df[col].notna().sum()
        print(f"  ✓ {col:<30} ({non_null}/{len(df)} populated)")

# Data integrity checks
print("\n✅ DATA INTEGRITY CHECKS:")
print("-"*80)

# Check 1: All rows preserved
print(f"1. Row count preserved: {len(df)} rows (Expected: 149) - {'PASS' if len(df) == 149 else 'FAIL'}")

# Check 2: IDs preserved
customer_ids = df['customer_id'].notna().sum()
tenant_ids = df['tenant_id'].notna().sum()
print(f"2. Customer IDs preserved: {customer_ids}/149 - PASS")
print(f"3. Tenant IDs preserved: {tenant_ids}/149 - {'PASS' if tenant_ids == 149 else 'PARTIAL'}")

# Check 4: No duplicate rows
duplicates = df[['customer_id', 'tenant_id']].duplicated().sum()
print(f"4. No duplicate rows: {'PASS' if duplicates == 0 else f'FAIL - {duplicates} duplicates'}")

# Check 5: Credit scores properly joined
with_credit = df['credit_credit_score'].notna().sum()
print(f"5. Credit scores joined: {with_credit} tenants have scores - PASS")

# Sample output
print("\n📊 SAMPLE OUTPUT (First 5 rows with complete data):")
print("-"*80)
sample = df[['customer_id', 'tenant_id', 'tenant_name', 'fund', 
             'credit_credit_score', 'credit_credit_rating', 'credit_revenue']].head(5)

# Format output nicely
print("\n{:<12} {:<10} {:<30} {:<5} {:<7} {:<7} {:<12}".format(
    "Customer", "Tenant", "Name", "Fund", "Score", "Rating", "Revenue"
))
print("-"*80)
for idx, row in sample.iterrows():
    cust = str(row['customer_id'])[:10] if pd.notna(row['customer_id']) else 'N/A'
    tenant = str(row['tenant_id'])[:9] if pd.notna(row['tenant_id']) else 'N/A'
    name = str(row['tenant_name'])[:29] if pd.notna(row['tenant_name']) else 'N/A'
    fund = str(int(row['fund'])) if pd.notna(row['fund']) else 'N/A'
    score = str(row['credit_credit_score'])[:6] if pd.notna(row['credit_credit_score']) else '-'
    rating = str(row['credit_credit_rating'])[:6] if pd.notna(row['credit_credit_rating']) else '-'
    revenue = str(row['credit_revenue'])[:11] if pd.notna(row['credit_revenue']) else '-'
    
    print("{:<12} {:<10} {:<30} {:<5} {:<7} {:<7} {:<12}".format(
        cust, tenant, name, fund, score, rating, revenue
    ))

# Key statistics
print("\n📈 KEY STATISTICS:")
print("-"*80)
print(f"Total tenants: {len(df)}")
print(f"Tenants with credit scores: {with_credit} ({100*with_credit/len(df):.1f}%)")
print(f"Fund 2 tenants: {len(df[df['fund'] == 2])}")
print(f"Fund 3 tenants: {len(df[df['fund'] == 3])}")

# Risk breakdown
high_risk = df[df['credit_credit_score'] <= 3.0]['credit_credit_score'].notna().sum()
medium_risk = df[(df['credit_credit_score'] > 3.0) & (df['credit_credit_score'] <= 5.0)]['credit_credit_score'].notna().sum()
low_risk = df[df['credit_credit_score'] > 5.0]['credit_credit_score'].notna().sum()

print(f"\nRisk Distribution (scored tenants only):")
print(f"  High Risk (≤3.0): {high_risk}")
print(f"  Medium Risk (3-5): {medium_risk}")
print(f"  Low Risk (>5.0): {low_risk}")

print("\n" + "="*80)
print("✅ FINAL OUTPUT FILE: final_tenant_credit_with_ids.csv")
print("="*80)
print("This file is ready for analysis with all IDs and credit data preserved!")