import pandas as pd
from rapidfuzz import fuzz, process
import warnings
warnings.filterwarnings('ignore')

def fuzzy_left_join(left_df, right_df, left_col, right_col, threshold=80):
    """
    Perform a left join using fuzzy matching on specified columns.
    """
    
    # Initialize columns for matching results
    left_df = left_df.copy()
    matched_indices = []
    match_scores = []
    matched_names = []
    
    # Create a list of right dataframe values for matching
    right_values = right_df[right_col].fillna('').tolist()
    
    print(f"Starting fuzzy matching for {len(left_df)} records...")
    print(f"Using threshold: {threshold}%")
    print("-" * 50)
    
    # For each record in left dataframe, find best match in right dataframe
    for idx, left_value in enumerate(left_df[left_col].fillna('').values):
        if idx % 100 == 0:
            print(f"Processing record {idx}/{len(left_df)}...")
        
        if left_value:
            # Find best match using rapidfuzz
            match = process.extractOne(
                left_value, 
                right_values, 
                scorer=fuzz.token_sort_ratio
            )
            
            if match and match[1] >= threshold:
                # Found a good match
                match_idx = right_values.index(match[0])
                matched_indices.append(match_idx)
                match_scores.append(match[1])
                matched_names.append(match[0])
            else:
                # No good match found
                matched_indices.append(None)
                match_scores.append(None)
                matched_names.append(None)
        else:
            # Empty value
            matched_indices.append(None)
            match_scores.append(None)
            matched_names.append(None)
    
    # Add match information to left dataframe
    left_df['matched_tenant_name'] = matched_names
    left_df['match_score'] = match_scores
    
    # Perform the join
    result_df = left_df.copy()
    
    # Add columns from right dataframe for matched records
    right_cols_to_add = [col for col in right_df.columns if col != right_col]
    
    for col in right_cols_to_add:
        result_df[f'eval_{col}'] = None
        for i, match_idx in enumerate(matched_indices):
            if match_idx is not None:
                result_df.at[i, f'eval_{col}'] = right_df.iloc[match_idx][col]
    
    return result_df

def main():
    # Read the CSV files
    print("=" * 70)
    print("FINAL FUZZY MATCHING WITH Q2 2025 UPDATES")
    print("=" * 70)
    print("\nReading CSV files...")
    
    # Use the updated CSV with Q2 2025 data
    left_file = '/Users/michaeltang/Downloads/Credit/FP_TCE Reports/new_tenants_with_q2_2025_updates.csv'
    right_file = '/Users/michaeltang/Downloads/Credit/tenant_credit_evaluation_final.csv'
    
    left_df = pd.read_csv(left_file)
    right_df = pd.read_csv(right_file)
    
    print(f"Updated tenant file records: {len(left_df)}")
    print(f"Credit evaluation file records: {len(right_df)}")
    print()
    
    # Perform fuzzy left join
    result_df = fuzzy_left_join(
        left_df, 
        right_df, 
        'tenant_name', 
        'tenant_name', 
        threshold=80
    )
    
    # Save the result
    output_file = '/Users/michaeltang/Downloads/Credit/FP_TCE Reports/final_tenants_with_all_evaluations.csv'
    result_df.to_csv(output_file, index=False)
    
    print()
    print("=" * 70)
    print(f"✅ Join completed! Output saved to:")
    print(f"   {output_file}")
    
    # Print summary statistics
    matched_count = result_df['match_score'].notna().sum()
    total_count = len(result_df)
    
    print(f"\n📊 Matching Summary:")
    print(f"   - Total records: {total_count}")
    print(f"   - Matched with credit evaluations: {matched_count} ({matched_count/total_count*100:.1f}%)")
    print(f"   - Unmatched records: {total_count - matched_count} ({(total_count - matched_count)/total_count*100:.1f}%)")
    
    if matched_count > 0:
        avg_score = result_df['match_score'].mean()
        print(f"   - Average match confidence: {avg_score:.1f}%")
    
    # Show credit score summary
    print(f"\n💳 Credit Score Summary:")
    
    # Q2 PDF credit scores
    q2_scores = result_df['credit_score'].notna().sum()
    print(f"   - Tenants with Q2 2025 PDF scores: {q2_scores}")
    
    # TCE evaluation scores
    tce_scores = result_df['eval_credit_score'].notna().sum()
    print(f"   - Tenants with TCE evaluation scores: {tce_scores}")
    
    # Combined coverage
    combined_scores = result_df[(result_df['credit_score'].notna()) | (result_df['eval_credit_score'].notna())]
    print(f"   - Total tenants with any credit score: {len(combined_scores)} ({len(combined_scores)/total_count*100:.1f}%)")
    
    # Check for Olive My Pickle
    olive = result_df[result_df['tenant_name'] == 'Olive My Pickle']
    if not olive.empty:
        print(f"\n🫒 Olive My Pickle status:")
        print(f"   - Q2 PDF Credit Score: {olive['credit_score'].values[0]}")
        if olive['matched_tenant_name'].notna().any():
            print(f"   - TCE Match Found: {olive['matched_tenant_name'].values[0]}")
            print(f"   - TCE Credit Score: {olive['eval_credit_score'].values[0]}")
        else:
            print(f"   - No TCE evaluation found")
    
    # Show examples of new matches
    print("\n🔍 Example matches (first 10):")
    matched_examples = result_df[result_df['match_score'].notna()].head(10)
    for _, row in matched_examples.iterrows():
        q2_score = f"Q2:{row['credit_score']}" if pd.notna(row['credit_score']) else ""
        tce_score = f"TCE:{row['eval_credit_score']}" if pd.notna(row['eval_credit_score']) else ""
        scores = f" [{q2_score} {tce_score}]".strip() if q2_score or tce_score else ""
        print(f"   '{row['tenant_name']}' → '{row['matched_tenant_name']}' (Match: {row['match_score']:.0f}%){scores}")
    
    # Create a summary report
    print("\n" + "=" * 70)
    print("📝 FINAL SUMMARY REPORT")
    print("=" * 70)
    
    # Fund breakdown
    fund2 = result_df[result_df['fund'] == 2]
    fund3 = result_df[result_df['fund'] == 3]
    
    print(f"\n🏢 Fund Distribution:")
    print(f"   Fund 2: {len(fund2)} tenants")
    print(f"   - With Q2 scores: {fund2['credit_score'].notna().sum()}")
    print(f"   - With TCE evaluations: {fund2['eval_credit_score'].notna().sum()}")
    print(f"   Fund 3: {len(fund3)} tenants")
    print(f"   - With Q2 scores: {fund3['credit_score'].notna().sum()}")
    print(f"   - With TCE evaluations: {fund3['eval_credit_score'].notna().sum()}")
    
    # Risk distribution
    if result_df['eval_credit_rating'].notna().any():
        print(f"\n⚠️ Credit Rating Distribution:")
        ratings = result_df['eval_credit_rating'].value_counts()
        for rating, count in ratings.items():
            print(f"   {rating}: {count} tenants")
    
    print("\n" + "=" * 70)
    print("✅ Process completed successfully!")
    
    return result_df

if __name__ == "__main__":
    result = main()