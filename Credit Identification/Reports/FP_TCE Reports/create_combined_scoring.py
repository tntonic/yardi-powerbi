import pandas as pd
import numpy as np
from datetime import datetime

def create_combined_scoring():
    """Create a comprehensive CSV with combined credit scoring from all sources"""
    
    print("=" * 80)
    print(" " * 20 + "CREATING COMBINED CREDIT SCORING CSV")
    print("=" * 80)
    
    # Read the final joined data
    df = pd.read_csv('/Users/michaeltang/Downloads/Credit/FP_TCE Reports/final_tenants_with_all_evaluations.csv')
    
    print(f"\n📊 Processing {len(df)} tenant records...")
    
    # Create combined credit score (prioritize Q2 PDF scores as most recent)
    df['combined_credit_score'] = np.where(
        df['credit_score'].notna(),
        df['credit_score'],
        df['eval_credit_score']
    )
    
    # Create score source indicator
    def get_score_source(row):
        if pd.notna(row['credit_score']) and pd.notna(row['eval_credit_score']):
            return 'Both (Q2 Primary)'
        elif pd.notna(row['credit_score']):
            return 'Q2 2025 PDF'
        elif pd.notna(row['eval_credit_score']):
            return 'TCE Evaluation'
        else:
            return 'No Score'
    
    df['score_source'] = df.apply(get_score_source, axis=1)
    
    # Create combined credit rating (use TCE if available)
    df['combined_credit_rating'] = df['eval_credit_rating']
    
    # Create risk level based on score and rating
    def get_risk_level(row):
        score = row['combined_credit_score']
        rating = row['combined_credit_rating']
        
        if pd.isna(score) and pd.isna(rating):
            return 'Not Evaluated'
        
        # Use score if available
        if pd.notna(score):
            if score >= 7:
                return 'Low Risk'
            elif score >= 5:
                return 'Medium Risk'
            elif score >= 4:
                return 'Medium-High Risk'
            else:
                return 'High Risk'
        
        # Otherwise use rating
        if pd.notna(rating):
            if rating in ['AAA', 'AA', 'A', 'BBB']:
                return 'Low Risk'
            elif rating in ['BB', 'B']:
                return 'Medium Risk'
            elif rating in ['CCC']:
                return 'Medium-High Risk'
            else:
                return 'High Risk'
        
        return 'Not Evaluated'
    
    df['risk_level'] = df.apply(get_risk_level, axis=1)
    
    # Select and reorder columns for final output
    output_columns = [
        # Core identification
        'customer_id',
        'tenant_id',
        'tenant_name',
        
        # Property information
        'property_name',
        'property_code',
        'property_address',
        'fund',
        
        # Lease information
        'lease_id',
        'amendment_type',
        'amendment_status',
        'amendment_start_date',
        
        # Combined credit scoring
        'combined_credit_score',
        'combined_credit_rating',
        'risk_level',
        'score_source',
        
        # Original scores for reference
        'credit_score',
        'credit_score_date',
        'eval_credit_score',
        'eval_credit_rating',
        
        # TCE evaluation details
        'eval_revenue',
        'eval_website',
        'eval_industry',
        'eval_business_description',
        'eval_probability_of_default',
        
        # Matching metadata
        'matched_tenant_name',
        'match_score'
    ]
    
    # Filter to only include columns that exist
    output_columns = [col for col in output_columns if col in df.columns]
    
    # Create the final dataframe
    final_df = df[output_columns].copy()
    
    # Sort by risk level and combined score
    risk_order = {'High Risk': 1, 'Medium-High Risk': 2, 'Medium Risk': 3, 'Low Risk': 4, 'Not Evaluated': 5}
    final_df['risk_sort'] = final_df['risk_level'].map(risk_order)
    final_df = final_df.sort_values(['risk_sort', 'combined_credit_score', 'tenant_name'])
    final_df = final_df.drop('risk_sort', axis=1)
    
    # Save the combined scoring CSV
    output_path = '/Users/michaeltang/Downloads/Credit/FP_TCE Reports/tenant_combined_credit_scoring.csv'
    final_df.to_csv(output_path, index=False)
    
    print("\n" + "=" * 80)
    print("📈 COMBINED SCORING SUMMARY")
    print("=" * 80)
    
    # Print summary statistics
    print(f"\n✅ Total Records: {len(final_df)}")
    
    # Score source breakdown
    print("\n📊 Score Sources:")
    source_counts = final_df['score_source'].value_counts()
    for source, count in source_counts.items():
        print(f"   • {source}: {count} ({count/len(final_df)*100:.1f}%)")
    
    # Risk level breakdown
    print("\n⚠️ Risk Distribution:")
    risk_counts = final_df['risk_level'].value_counts()
    for risk, count in risk_counts.items():
        print(f"   • {risk}: {count} ({count/len(final_df)*100:.1f}%)")
    
    # Credit score statistics
    scored = final_df[final_df['combined_credit_score'].notna()]
    if len(scored) > 0:
        print(f"\n💳 Combined Credit Score Statistics:")
        print(f"   • Tenants with scores: {len(scored)}")
        print(f"   • Average score: {scored['combined_credit_score'].mean():.2f}")
        print(f"   • Median score: {scored['combined_credit_score'].median():.2f}")
        print(f"   • Score range: {scored['combined_credit_score'].min():.1f} - {scored['combined_credit_score'].max():.1f}")
    
    # Fund breakdown
    print(f"\n🏢 Fund Analysis:")
    for fund in [2, 3]:
        fund_df = final_df[final_df['fund'] == fund]
        fund_scored = fund_df[fund_df['combined_credit_score'].notna()]
        print(f"   Fund {fund}:")
        print(f"      • Total tenants: {len(fund_df)}")
        print(f"      • With credit scores: {len(fund_scored)}")
        if len(fund_scored) > 0:
            print(f"      • Average score: {fund_scored['combined_credit_score'].mean():.2f}")
            
            # Risk breakdown for fund
            fund_risk = fund_df['risk_level'].value_counts()
            high_risk = fund_risk.get('High Risk', 0) + fund_risk.get('Medium-High Risk', 0)
            if high_risk > 0:
                print(f"      • High/Medium-High Risk: {high_risk} tenants")
    
    # Highlight key tenants
    print("\n🔍 Notable Tenants:")
    
    # Highest risk with scores
    high_risk_df = final_df[final_df['risk_level'].isin(['High Risk', 'Medium-High Risk'])]
    high_risk_scored = high_risk_df[high_risk_df['combined_credit_score'].notna()]
    if len(high_risk_scored) > 0:
        print("\n   Highest Risk (with scores):")
        for _, row in high_risk_scored.head(5).iterrows():
            score = f"{row['combined_credit_score']:.1f}" if pd.notna(row['combined_credit_score']) else "N/A"
            rating = row['combined_credit_rating'] if pd.notna(row['combined_credit_rating']) else "N/A"
            print(f"      • {row['tenant_name'][:35]:35s} | Score: {score:>4s} | Rating: {rating:>4s} | {row['risk_level']}")
    
    # Best performers
    low_risk_df = final_df[final_df['risk_level'] == 'Low Risk']
    if len(low_risk_df) > 0:
        print("\n   Best Performers:")
        for _, row in low_risk_df.head(3).iterrows():
            score = f"{row['combined_credit_score']:.1f}" if pd.notna(row['combined_credit_score']) else "N/A"
            rating = row['combined_credit_rating'] if pd.notna(row['combined_credit_rating']) else "N/A"
            print(f"      • {row['tenant_name'][:35]:35s} | Score: {score:>4s} | Rating: {rating:>4s}")
    
    print("\n" + "=" * 80)
    print(f"✅ Combined scoring CSV created successfully!")
    print(f"   Output file: {output_path}")
    print("=" * 80)
    
    return final_df

if __name__ == "__main__":
    combined_df = create_combined_scoring()