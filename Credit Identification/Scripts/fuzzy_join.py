import pandas as pd
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import numpy as np

# Read the CSV files
df1 = pd.read_csv('new_tenants_fund2_fund3_since_2025_populated.csv')
df2 = pd.read_csv('tenant_credit_evaluation_final.csv')

# Match tenant_name (column C) from first file with tenant_name (column B) from second file
col_d_name = df1.columns[2]  # Column C - tenant_name (0-indexed: 2)  
col_b_name = df2.columns[1]  # Column B - tenant_name (0-indexed: 1)

print(f"Matching column '{col_d_name}' from first file with column '{col_b_name}' from second file")
print(f"First file has {len(df1)} rows")
print(f"Second file has {len(df2)} rows")

# Function to find best fuzzy match
def find_best_match(value, choices, threshold=80):
    if pd.isna(value) or str(value) == 'nan':
        return None, 0
    
    # Get the best match
    result = process.extractOne(str(value), choices, scorer=fuzz.token_sort_ratio)
    
    if result and result[1] >= threshold:
        return result[0], result[1]
    else:
        return None, 0

# Prepare choices from df2's column B
choices = df2[col_b_name].dropna().astype(str).tolist()

# Find matches for each row in df1
print("\nPerforming fuzzy matching... This may take a few minutes...")
matches = []
match_scores = []

for idx, value in enumerate(df1[col_d_name]):
    if idx % 100 == 0:
        print(f"Processing row {idx}/{len(df1)}...")
    
    match, score = find_best_match(value, choices, threshold=60)  # Lower threshold for address-name matching
    matches.append(match)
    match_scores.append(score)

# Add match information to df1
df1['matched_tenant_name'] = matches
df1['match_score'] = match_scores

# Perform the left join
df_result = df1.copy()

# For each matched row, add the corresponding data from df2
for col in df2.columns:
    if col != col_b_name:  # Don't duplicate the matching column
        df_result[f'credit_{col}'] = None

# Fill in the matched data
for idx, match in enumerate(matches):
    if match:
        # Find the row in df2 that matches
        matching_rows = df2[df2[col_b_name] == match]
        if not matching_rows.empty:
            # Take the first match
            row = matching_rows.iloc[0]
            for col in df2.columns:
                if col != col_b_name:
                    df_result.loc[idx, f'credit_{col}'] = row[col]

# Save the result
output_file = 'joined_tenant_credit_data.csv'
df_result.to_csv(output_file, index=False)

print(f"\n✅ Fuzzy match left join completed!")
print(f"Output saved to: {output_file}")
print(f"Total rows: {len(df_result)}")
print(f"Matched rows: {sum(1 for m in matches if m is not None)}")
print(f"Unmatched rows: {sum(1 for m in matches if m is None)}")

# Display sample of matched results
print("\nSample of matched results (first 10 matches):")
matched_sample = df_result[df_result['matched_tenant_name'].notna()].head(10)
if not matched_sample.empty:
    print(matched_sample[[col_d_name, 'matched_tenant_name', 'match_score']].to_string())
else:
    print("No matches found with the current threshold.")