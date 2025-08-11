import pandas as pd
import numpy as np
from datetime import datetime

def generate_comprehensive_report():
    """Generate a comprehensive analysis report of the tenant credit data"""
    
    # Read the final joined CSV
    df = pd.read_csv('/Users/michaeltang/Downloads/Credit/FP_TCE Reports/final_tenants_with_all_evaluations.csv')
    
    print("=" * 80)
    print(" " * 20 + "COMPREHENSIVE CREDIT ANALYSIS REPORT")
    print(" " * 25 + f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 80)
    
    # 1. Overall Portfolio Metrics
    print("\n📊 PORTFOLIO OVERVIEW")
    print("-" * 80)
    total_tenants = len(df)
    fund2_count = len(df[df['fund'] == 2])
    fund3_count = len(df[df['fund'] == 3])
    
    print(f"Total Tenants: {total_tenants}")
    print(f"  • Fund 2: {fund2_count} ({fund2_count/total_tenants*100:.1f}%)")
    print(f"  • Fund 3: {fund3_count} ({fund3_count/total_tenants*100:.1f}%)")
    
    # 2. Credit Coverage Analysis
    print("\n💳 CREDIT SCORE COVERAGE")
    print("-" * 80)
    
    # Q2 PDF Scores
    q2_scores = df[df['credit_score'].notna()]
    print(f"Q2 2025 PDF Credit Scores: {len(q2_scores)} tenants")
    if len(q2_scores) > 0:
        print(f"  • Average Score: {q2_scores['credit_score'].mean():.2f}")
        print(f"  • Score Range: {q2_scores['credit_score'].min():.1f} - {q2_scores['credit_score'].max():.1f}")
    
    # TCE Evaluation Scores
    tce_scores = df[df['eval_credit_score'].notna()]
    print(f"\nTCE Credit Evaluations: {len(tce_scores)} tenants")
    if len(tce_scores) > 0:
        print(f"  • Average Score: {tce_scores['eval_credit_score'].mean():.2f}")
        print(f"  • Score Range: {tce_scores['eval_credit_score'].min():.1f} - {tce_scores['eval_credit_score'].max():.1f}")
    
    # Combined Coverage
    any_score = df[(df['credit_score'].notna()) | (df['eval_credit_score'].notna())]
    print(f"\nTotal Credit Coverage: {len(any_score)} of {total_tenants} ({len(any_score)/total_tenants*100:.1f}%)")
    
    # 3. Risk Analysis
    print("\n⚠️ RISK ASSESSMENT")
    print("-" * 80)
    
    # Credit Rating Distribution
    if 'eval_credit_rating' in df.columns:
        ratings = df['eval_credit_rating'].value_counts()
        if not ratings.empty:
            print("Credit Rating Distribution (TCE):")
            rating_order = ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC', 'CC', 'C', 'D']
            for rating in rating_order:
                if rating in ratings.index:
                    count = ratings[rating]
                    pct = count/len(tce_scores)*100 if len(tce_scores) > 0 else 0
                    print(f"  • {rating:4s}: {count:3d} tenants ({pct:5.1f}% of evaluated)")
    
    # High Risk Tenants (Score < 4.0 or Rating CCC or below)
    high_risk = df[
        (df['credit_score'] < 4.0) | 
        (df['eval_credit_score'] < 4.0) | 
        (df['eval_credit_rating'].isin(['CCC', 'CC', 'C', 'D']))
    ]
    print(f"\nHigh Risk Tenants (Score < 4.0 or Rating ≤ CCC): {len(high_risk)}")
    if len(high_risk) > 0:
        print("  Top 5 High Risk:")
        for _, row in high_risk.head(5).iterrows():
            score = row['credit_score'] if pd.notna(row['credit_score']) else row['eval_credit_score']
            rating = row['eval_credit_rating'] if pd.notna(row['eval_credit_rating']) else 'N/A'
            score_str = f"{score:.1f}" if pd.notna(score) else "N/A"
            print(f"    - {row['tenant_name'][:40]:40s} Score: {score_str:>5s} Rating: {rating}")
    
    # 4. New Q2 2025 Additions
    print("\n🆕 Q2 2025 UPDATES")
    print("-" * 80)
    
    # Check for Olive My Pickle
    olive = df[df['tenant_name'] == 'Olive My Pickle']
    if not olive.empty:
        print("New Tenant Added:")
        print(f"  • Olive My Pickle - Credit Score: {olive['credit_score'].values[0]}")
    
    # Tenants with Q2 updates
    q2_updated = df[df['credit_score_date'] == '2025-07-01']
    print(f"\nTenants with Q2 2025 Credit Updates: {len(q2_updated)}")
    if len(q2_updated) > 0:
        print("  Recent Updates:")
        for _, row in q2_updated.head(5).iterrows():
            print(f"    - {row['tenant_name'][:40]:40s} Score: {row['credit_score']:.1f}")
    
    # 5. Data Quality Metrics
    print("\n📈 DATA QUALITY METRICS")
    print("-" * 80)
    
    # Fuzzy Match Quality
    matched = df[df['match_score'].notna()]
    if len(matched) > 0:
        print(f"Fuzzy Matching Results:")
        print(f"  • Total Matches: {len(matched)} ({len(matched)/total_tenants*100:.1f}%)")
        print(f"  • Average Match Confidence: {matched['match_score'].mean():.1f}%")
        print(f"  • Perfect Matches (100%): {len(matched[matched['match_score'] == 100])}")
        print(f"  • High Confidence (≥90%): {len(matched[matched['match_score'] >= 90])}")
    
    # Missing Data Analysis
    print(f"\nMissing Data:")
    print(f"  • No Credit Score (Q2 or TCE): {total_tenants - len(any_score)} ({(total_tenants - len(any_score))/total_tenants*100:.1f}%)")
    print(f"  • No TCE Match: {total_tenants - len(matched)} ({(total_tenants - len(matched))/total_tenants*100:.1f}%)")
    
    # 6. Recommendations
    print("\n💡 RECOMMENDATIONS")
    print("-" * 80)
    
    no_score = df[(df['credit_score'].isna()) & (df['eval_credit_score'].isna())]
    print(f"1. Priority Credit Evaluations Needed: {len(no_score)} tenants without any credit score")
    
    low_match = matched[matched['match_score'] < 90]
    if len(low_match) > 0:
        print(f"2. Review Low-Confidence Matches: {len(low_match)} matches below 90% confidence")
    
    if len(high_risk) > 0:
        print(f"3. Risk Mitigation: {len(high_risk)} high-risk tenants require closer monitoring")
    
    # 7. Export Summary Statistics
    summary_stats = {
        'Total_Tenants': total_tenants,
        'Fund_2_Count': fund2_count,
        'Fund_3_Count': fund3_count,
        'Q2_Credit_Scores': len(q2_scores),
        'TCE_Evaluations': len(tce_scores),
        'Total_Credit_Coverage': len(any_score),
        'Coverage_Percentage': len(any_score)/total_tenants*100,
        'High_Risk_Count': len(high_risk),
        'Fuzzy_Matches': len(matched),
        'Average_Match_Confidence': matched['match_score'].mean() if len(matched) > 0 else 0,
        'Report_Date': datetime.now().strftime('%Y-%m-%d %H:%M')
    }
    
    # Save summary to CSV
    summary_df = pd.DataFrame([summary_stats])
    summary_path = '/Users/michaeltang/Downloads/Credit/FP_TCE Reports/analysis_summary_stats.csv'
    summary_df.to_csv(summary_path, index=False)
    
    print("\n" + "=" * 80)
    print("✅ ANALYSIS COMPLETE")
    print(f"   Summary statistics saved to: {summary_path}")
    print(f"   Full data available at: final_tenants_with_all_evaluations.csv")
    print("=" * 80)
    
    return df, summary_stats

if __name__ == "__main__":
    data, stats = generate_comprehensive_report()