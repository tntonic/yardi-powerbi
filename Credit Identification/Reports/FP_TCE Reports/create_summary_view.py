import pandas as pd

def create_summary_view():
    """Create a simplified summary view of the combined credit scoring"""
    
    # Read the combined scoring CSV
    df = pd.read_csv('/Users/michaeltang/Downloads/Credit/FP_TCE Reports/tenant_combined_credit_scoring.csv')
    
    # Create simplified summary with key fields only
    summary_df = df[[
        'tenant_name',
        'fund',
        'property_name',
        'combined_credit_score',
        'combined_credit_rating',
        'risk_level',
        'score_source'
    ]].copy()
    
    # Save summary view
    summary_path = '/Users/michaeltang/Downloads/Credit/FP_TCE Reports/tenant_credit_summary.csv'
    summary_df.to_csv(summary_path, index=False)
    
    print("=" * 80)
    print(" " * 25 + "CREDIT SUMMARY VIEW CREATED")
    print("=" * 80)
    
    print(f"\n✅ Summary saved to: {summary_path}")
    print(f"   Total records: {len(summary_df)}")
    
    # Show sample of each risk level
    print("\n📊 Sample Records by Risk Level:")
    print("-" * 80)
    
    for risk in ['High Risk', 'Medium-High Risk', 'Medium Risk', 'Low Risk']:
        risk_sample = summary_df[summary_df['risk_level'] == risk].head(2)
        if len(risk_sample) > 0:
            print(f"\n{risk}:")
            for _, row in risk_sample.iterrows():
                score = f"{row['combined_credit_score']:.1f}" if pd.notna(row['combined_credit_score']) else "N/A"
                rating = row['combined_credit_rating'] if pd.notna(row['combined_credit_rating']) else "N/A"
                print(f"  • {row['tenant_name'][:30]:30s} | Fund {int(row['fund'])} | Score: {score:>4s} | Rating: {rating:>4s}")
    
    # Not evaluated count
    not_eval = len(summary_df[summary_df['risk_level'] == 'Not Evaluated'])
    print(f"\nNot Evaluated: {not_eval} tenants (need credit assessment)")
    
    return summary_df

if __name__ == "__main__":
    summary = create_summary_view()