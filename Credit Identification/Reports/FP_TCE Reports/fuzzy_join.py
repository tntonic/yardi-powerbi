import pandas as pd
from rapidfuzz import fuzz, process
import warnings
warnings.filterwarnings('ignore')

def fuzzy_left_join(left_df, right_df, left_col, right_col, threshold=80):
    """
    Perform a left join using fuzzy matching on specified columns.
    
    Parameters:
    - left_df: Left dataframe (all records will be kept)
    - right_df: Right dataframe (matched records will be joined)
    - left_col: Column name in left_df to match on
    - right_col: Column name in right_df to match on
    - threshold: Minimum similarity score (0-100) to consider a match
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
    print("Reading CSV files...")
    left_file = '/Users/michaeltang/Downloads/Credit/new_tenants_fund2_fund3_since_2025_populated.csv'
    right_file = '/Users/michaeltang/Downloads/Credit/tenant_credit_evaluation_final.csv'
    
    left_df = pd.read_csv(left_file)
    right_df = pd.read_csv(right_file)
    
    print(f"Left file records: {len(left_df)}")
    print(f"Right file records: {len(right_df)}")
    print()
    
    # Perform fuzzy left join
    result_df = fuzzy_left_join(
        left_df, 
        right_df, 
        'tenant_name', 
        'tenant_name', 
        threshold=80  # Adjust this threshold as needed (0-100)
    )
    
    # Save the result
    output_file = '/Users/michaeltang/Downloads/Credit/FP_TCE Reports/joined_tenants_with_evaluation.csv'
    result_df.to_csv(output_file, index=False)
    
    print()
    print("=" * 50)
    print(f"Join completed! Output saved to: {output_file}")
    
    # Print summary statistics
    matched_count = result_df['match_score'].notna().sum()
    total_count = len(result_df)
    
    print(f"\nMatching Summary:")
    print(f"- Total records: {total_count}")
    print(f"- Matched records: {matched_count} ({matched_count/total_count*100:.1f}%)")
    print(f"- Unmatched records: {total_count - matched_count} ({(total_count - matched_count)/total_count*100:.1f}%)")
    
    if matched_count > 0:
        avg_score = result_df['match_score'].mean()
        print(f"- Average match score: {avg_score:.1f}%")
        
        # Show some examples of matches
        print("\nExample matches (first 10):")
        matched_examples = result_df[result_df['match_score'].notna()].head(10)
        for _, row in matched_examples.iterrows():
            print(f"  '{row['tenant_name']}' → '{row['matched_tenant_name']}' (Score: {row['match_score']:.0f}%)")
    
    # Show columns in the output file
    print(f"\nOutput file contains {len(result_df.columns)} columns:")
    print("Original columns plus:")
    new_cols = [col for col in result_df.columns if col.startswith('eval_') or col in ['matched_tenant_name', 'match_score']]
    for col in new_cols:
        print(f"  - {col}")
    
    return result_df

if __name__ == "__main__":
    result = main()