import pandas as pd
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import numpy as np
import sys

# Read the CSV files
df1 = pd.read_csv('new_tenants_fund2_fund3_since_2025_populated.csv')
df2 = pd.read_csv('tenant_credit_evaluation_final.csv')

print("First file columns:")
for i, col in enumerate(df1.columns):
    print(f"  Column {chr(65+i)}: {col}")

print("\nSecond file columns:")
for i, col in enumerate(df2.columns):
    print(f"  Column {chr(65+i)}: {col}")

# Ask user to confirm matching approach
print("\n" + "="*60)
print("MATCHING OPTIONS:")
print("1. Match Column D (property_address) from file 1 with Column B (tenant_name) from file 2 [AS REQUESTED]")
print("2. Match Column C (tenant_name) from file 1 with Column B (tenant_name) from file 2 [RECOMMENDED]")
print("="*60)

# Default to option 2 (recommended)
option = input("\nSelect option (1 or 2, default is 2): ").strip()
if option == "1":
    col1_idx = 3  # Column D - property_address
    col2_idx = 1  # Column B - tenant_name
    threshold = 50  # Lower threshold for address-name matching
    print("\n⚠️  Warning: Matching addresses with tenant names will likely produce poor results.")
else:
    col1_idx = 2  # Column C - tenant_name
    col2_idx = 1  # Column B - tenant_name
    threshold = 75  # Higher threshold for name-name matching

col1_name = df1.columns[col1_idx]
col2_name = df2.columns[col2_idx]

print(f"\nMatching '{col1_name}' from first file with '{col2_name}' from second file")
print(f"Using similarity threshold: {threshold}%")
print(f"First file has {len(df1)} rows")
print(f"Second file has {len(df2)} rows")

# Function to find best fuzzy match
def find_best_match(value, choices_dict, threshold=75):
    if pd.isna(value) or str(value).strip() == '' or str(value) == 'nan':
        return None, 0, None
    
    # Clean the value
    value_str = str(value).strip()
    
    # Get the best match
    result = process.extractOne(value_str, choices_dict.keys(), scorer=fuzz.token_sort_ratio)
    
    if result and result[1] >= threshold:
        return result[0], result[1], choices_dict[result[0]]
    else:
        return None, 0, None

# Prepare choices from df2's column with index mapping
choices_dict = {str(val).strip(): idx for idx, val in enumerate(df2[col2_name]) 
                 if pd.notna(val) and str(val).strip() != ''}

# Find matches for each row in df1
print("\nPerforming fuzzy matching... This may take a few minutes...")
matches = []
match_scores = []
match_indices = []

for idx, value in enumerate(df1[col1_name]):
    if idx % 50 == 0:
        print(f"Processing row {idx}/{len(df1)}...")
    
    match, score, match_idx = find_best_match(value, choices_dict, threshold=threshold)
    matches.append(match)
    match_scores.append(score)
    match_indices.append(match_idx)

# Create result dataframe by copying df1
df_result = df1.copy()

# Add match information
df_result['matched_value'] = matches
df_result['match_score'] = match_scores

# Add all columns from df2 with 'credit_' prefix
for col in df2.columns:
    df_result[f'credit_{col}'] = None

# Fill in the matched data
for idx, match_idx in enumerate(match_indices):
    if match_idx is not None:
        # Get the matching row from df2
        row = df2.iloc[match_idx]
        for col in df2.columns:
            df_result.loc[idx, f'credit_{col}'] = row[col]

# Save the result
output_file = 'joined_tenant_credit_data_final.csv'
df_result.to_csv(output_file, index=False)

print(f"\n✅ Fuzzy match left join completed!")
print(f"Output saved to: {output_file}")
print(f"Total rows: {len(df_result)}")
print(f"Matched rows: {sum(1 for m in matches if m is not None)}")
print(f"Unmatched rows: {sum(1 for m in matches if m is None)}")

# Display statistics
if sum(1 for m in matches if m is not None) > 0:
    avg_score = np.mean([s for s in match_scores if s > 0])
    print(f"Average match score: {avg_score:.1f}%")
    
    print("\nMatch score distribution:")
    score_ranges = [(90, 100), (80, 89), (70, 79), (60, 69), (50, 59)]
    for low, high in score_ranges:
        count = sum(1 for s in match_scores if low <= s <= high)
        if count > 0:
            print(f"  {low}-{high}%: {count} matches")

# Display sample of matched results
print("\nSample of matched results (showing best and worst matches):")
matched_df = df_result[df_result['matched_value'].notna()].copy()
if not matched_df.empty:
    matched_df = matched_df.sort_values('match_score', ascending=False)
    
    print("\nTop 5 best matches:")
    print(matched_df[[col1_name, 'matched_value', 'match_score']].head(5).to_string())
    
    if len(matched_df) > 5:
        print("\n5 lowest scoring matches:")
        print(matched_df[[col1_name, 'matched_value', 'match_score']].tail(5).to_string())
else:
    print("No matches found with the current threshold.")

# Show some unmatched records
unmatched_df = df_result[df_result['matched_value'].isna()]
if not unmatched_df.empty:
    print(f"\nSample of {min(5, len(unmatched_df))} unmatched records from first file:")
    print(unmatched_df[col1_name].head(5).to_string())