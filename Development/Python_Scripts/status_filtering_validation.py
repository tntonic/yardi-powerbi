import pandas as pd
import numpy as np

print('=== STATUS FILTERING VALIDATION ===')
df_cleaned = pd.read_csv('Data/Yardi_Tables/dim_fp_amendmentsunitspropertytenant_cleaned.csv')

# Test the critical status filtering logic for rent roll accuracy
print('Testing Yardi amendment status filtering logic...')

# Status distribution
print('\n1. OVERALL STATUS DISTRIBUTION:')
status_counts = df_cleaned['amendment status'].value_counts()
total_amendments = len(df_cleaned)

for status, count in status_counts.items():
    percentage = (count / total_amendments) * 100
    print(f'   {status}: {count:,} ({percentage:.1f}%)')

# Critical test: Activated + Superseded filtering (the Yardi standard)
activated_superseded = df_cleaned[df_cleaned['amendment status'].isin(['Activated', 'Superseded'])]
print(f'\n2. ACTIVATED + SUPERSEDED FILTERING:')
print(f'   Total amendments with Activated OR Superseded status: {len(activated_superseded):,}')
print(f'   Percentage of total data: {len(activated_superseded)/total_amendments*100:.1f}%')

# Test what happens with just Activated (common mistake)
activated_only = df_cleaned[df_cleaned['amendment status'] == 'Activated']
print(f'\n3. ACTIVATED ONLY FILTERING (Common Mistake):')
print(f'   Total amendments with Activated status only: {len(activated_only):,}')
print(f'   Percentage of total data: {len(activated_only)/total_amendments*100:.1f}%')

# Calculate the impact of including Superseded
superseded_only = df_cleaned[df_cleaned['amendment status'] == 'Superseded']
print(f'\n4. IMPACT OF INCLUDING SUPERSEDED:')
print(f'   Superseded amendments: {len(superseded_only):,}')
print(f'   Data loss if excluding Superseded: {len(superseded_only)/len(activated_superseded)*100:.1f}%')

# Rent roll impact analysis
print(f'\n5. RENT ROLL IMPACT ANALYSIS:')

# For rent roll, we typically want the latest amendment per property/tenant
latest_amendments = df_cleaned.loc[df_cleaned.groupby(['property hmy', 'tenant hmy'])['amendment sequence'].idxmax()]
print(f'   Total unique property/tenant pairs: {len(latest_amendments):,}')

# Status distribution of latest amendments
latest_status_counts = latest_amendments['amendment status'].value_counts()
print(f'   Status distribution of LATEST amendments:')
for status, count in latest_status_counts.items():
    percentage = (count / len(latest_amendments)) * 100
    print(f'     {status}: {count:,} ({percentage:.1f}%)')

# Critical validation: Check if any rent roll records would be lost
latest_activated_superseded = latest_amendments[latest_amendments['amendment status'].isin(['Activated', 'Superseded'])]
latest_activated_only = latest_amendments[latest_amendments['amendment status'] == 'Activated']

print(f'\n6. RENT ROLL FILTERING VALIDATION:')
print(f'   Latest amendments (Activated + Superseded): {len(latest_activated_superseded):,}')
print(f'   Latest amendments (Activated only): {len(latest_activated_only):,}')
print(f'   Records lost if excluding Superseded: {len(latest_activated_superseded) - len(latest_activated_only):,}')

if len(latest_activated_superseded) - len(latest_activated_only) > 0:
    print('   🚨 WARNING: Excluding Superseded would lose rent roll records!')
else:
    print('   ✅ INFO: No latest amendments have Superseded status')

# Test for other statuses that might be relevant
other_statuses = df_cleaned[~df_cleaned['amendment status'].isin(['Activated', 'Superseded'])]
print(f'\n7. OTHER STATUS ANALYSIS:')
if len(other_statuses) > 0:
    other_status_counts = other_statuses['amendment status'].value_counts()
    print(f'   Non-Activated/Superseded statuses:')
    for status, count in other_status_counts.items():
        percentage = (count / total_amendments) * 100
        print(f'     {status}: {count:,} ({percentage:.1f}%)')
    
    # Check if any "other" statuses are latest amendments
    latest_other = latest_amendments[~latest_amendments['amendment status'].isin(['Activated', 'Superseded'])]
    if len(latest_other) > 0:
        print(f'   ⚠️  Latest amendments with other statuses: {len(latest_other):,}')
        print('     These may need business review:')
        for status, count in latest_other['amendment status'].value_counts().items():
            print(f'       {status}: {count:,}')
else:
    print('   All amendments have Activated or Superseded status')

# Final validation score
print(f'\n8. STATUS FILTERING VALIDATION SCORE:')
expected_rent_roll_count = len(latest_amendments)
actual_rent_roll_count = len(latest_activated_superseded)
accuracy_percentage = (actual_rent_roll_count / expected_rent_roll_count) * 100

print(f'   Expected rent roll records: {expected_rent_roll_count:,}')
print(f'   Actual records with Activated+Superseded filter: {actual_rent_roll_count:,}')
print(f'   Status filtering accuracy: {accuracy_percentage:.2f}%')

if accuracy_percentage >= 99.0:
    print('   ✅ STATUS FILTERING VALIDATION PASSED: >99% accuracy')
elif accuracy_percentage >= 95.0:
    print('   ⚠️  STATUS FILTERING WARNING: 95-99% accuracy')
else:
    print('   🚨 STATUS FILTERING FAILED: <95% accuracy')