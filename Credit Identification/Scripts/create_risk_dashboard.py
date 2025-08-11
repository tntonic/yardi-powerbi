import pandas as pd
import numpy as np

# Read the fully populated data
df = pd.read_csv('fully_populated_credit_scores.csv')

# Create a risk dashboard
print("\n" + "="*80)
print(" "*25 + "TENANT CREDIT RISK DASHBOARD")
print("="*80)

# Create risk categories
def categorize_risk(score):
    if pd.isna(score):
        return 'No Score'
    elif score <= 3.0:
        return 'High Risk'
    elif score <= 5.0:
        return 'Medium Risk'
    else:
        return 'Low Risk'

df['risk_category'] = df['credit_credit_score'].apply(categorize_risk)

# Summary by Fund
print("\n📊 RISK SUMMARY BY FUND:")
print("-"*80)
fund_summary = df.groupby(['fund', 'risk_category']).size().unstack(fill_value=0)
fund_totals = df.groupby('fund').size()

for fund in fund_summary.index:
    if pd.notna(fund):
        fund_name = f"Fund {int(fund)}"
        total = fund_totals[fund]
        print(f"\n{fund_name} (Total: {total} tenants):")
        
        for risk in ['High Risk', 'Medium Risk', 'Low Risk', 'No Score']:
            if risk in fund_summary.columns:
                count = fund_summary.loc[fund, risk]
                pct = 100 * count / total
                if risk == 'High Risk' and count > 0:
                    print(f"  🔴 {risk:<15} {count:3} ({pct:5.1f}%)")
                elif risk == 'Medium Risk' and count > 0:
                    print(f"  🟡 {risk:<15} {count:3} ({pct:5.1f}%)")
                elif risk == 'Low Risk' and count > 0:
                    print(f"  🟢 {risk:<15} {count:3} ({pct:5.1f}%)")
                elif risk == 'No Score' and count > 0:
                    print(f"  ⚪ {risk:<15} {count:3} ({pct:5.1f}%)")

# Create actionable lists
print("\n" + "="*80)
print("📋 ACTION ITEMS:")
print("="*80)

# High risk tenants requiring immediate attention
high_risk_tenants = df[df['risk_category'] == 'High Risk'][
    ['tenant_name', 'property_name', 'fund', 'credit_credit_score', 'credit_revenue', 'amendment_type']
].sort_values('credit_credit_score')

if not high_risk_tenants.empty:
    print("\n🚨 HIGH PRIORITY - High Risk Tenants (Score ≤ 3.0):")
    print("-"*80)
    for idx, row in high_risk_tenants.iterrows():
        revenue = f"${row['credit_revenue']}" if pd.notna(row['credit_revenue']) else "N/A"
        amendment = row['amendment_type'] if pd.notna(row['amendment_type']) else "N/A"
        print(f"  {row['tenant_name'][:35]:<35}")
        print(f"    • Score: {row['credit_credit_score']:.1f} | Revenue: {revenue} | Status: {amendment}")

# Large tenants without scores (by property size assumptions)
no_score_tenants = df[df['risk_category'] == 'No Score'][
    ['tenant_name', 'property_name', 'fund', 'amendment_type']
]

if len(no_score_tenants) > 0:
    print("\n📝 MEDIUM PRIORITY - Tenants Needing Credit Evaluation:")
    print("-"*80)
    # Show first 10
    for idx, row in no_score_tenants.head(10).iterrows():
        if pd.notna(row['tenant_name']):
            amendment = row['amendment_type'] if pd.notna(row['amendment_type']) else "N/A"
            fund_str = f"Fund {int(row['fund'])}" if pd.notna(row['fund']) else "N/A"
            print(f"  • {row['tenant_name'][:40]:<40} | {fund_str} | {amendment}")
    
    if len(no_score_tenants) > 10:
        print(f"  ... and {len(no_score_tenants) - 10} more tenants")

# Export risk summary
risk_summary = df.groupby('risk_category').agg({
    'tenant_name': 'count',
    'credit_credit_score': 'mean',
    'credit_revenue': lambda x: x.dropna().apply(lambda y: float(str(y).replace('$','').replace('M','').replace(',','')) if pd.notna(y) else 0).sum()
}).round(2)

risk_summary.columns = ['Count', 'Avg Score', 'Total Revenue (M)']
risk_summary.to_csv('risk_summary_by_category.csv')

# Create detailed export for high and medium risk
risk_tenants = df[df['credit_credit_score'] <= 5.0][
    ['tenant_name', 'property_address', 'property_name', 'fund', 
     'credit_credit_score', 'credit_credit_rating', 'credit_revenue', 
     'amendment_type', 'amendment_status']
].sort_values('credit_credit_score')
risk_tenants.to_csv('high_medium_risk_tenants.csv', index=False)

print("\n" + "="*80)
print("📁 FILES CREATED:")
print("="*80)
print("  1. fully_populated_credit_scores.csv - Complete dataset with all matches")
print("  2. risk_summary_by_category.csv - Summary statistics by risk level")
print("  3. high_medium_risk_tenants.csv - Detailed list of risky tenants")

print("\n" + "="*80)
print("✅ SUMMARY:")
print("="*80)
print(f"  • Credit scores populated: {df['credit_credit_score'].notna().sum()}/{len(df)} tenants")
print(f"  • High-risk tenants identified: {len(high_risk_tenants)}")
print(f"  • Coverage improvement: +{df['credit_credit_score'].notna().sum() - 1} scores from baseline")
print(f"  • Success rate: {100*df['credit_credit_score'].notna().sum()/len(df):.1f}%")