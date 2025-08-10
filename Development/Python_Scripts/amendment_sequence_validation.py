import pandas as pd
import numpy as np

print('=== AMENDMENT SEQUENCE VALIDATION ===')
df_cleaned = pd.read_csv('Data/Yardi_Tables/dim_fp_amendmentsunitspropertytenant_cleaned.csv')

# Convert dates for proper sequence validation
df_cleaned['amendment start date'] = pd.to_datetime(df_cleaned['amendment start date'])

print('Validating amendment sequences are properly ordered...')

sequence_issues = []
date_sequence_issues = []
status_sequence_issues = []

# Check each property/tenant combination
for (prop, tenant), group in df_cleaned.groupby(['property hmy', 'tenant hmy']):
    amendments = group.sort_values('amendment sequence')
    
    # Check 1: Sequences should be sequential (0, 1, 2, etc.)
    expected_sequences = list(range(len(amendments)))
    actual_sequences = sorted(amendments['amendment sequence'].tolist())
    
    if actual_sequences != expected_sequences:
        sequence_issues.append({
            'property': prop,
            'tenant': tenant, 
            'expected': expected_sequences,
            'actual': actual_sequences,
            'issue': 'Non-sequential sequences'
        })
    
    # Check 2: Amendment dates should generally be in sequence order
    if len(amendments) > 1:
        dates = amendments['amendment start date'].tolist()
        sequences = amendments['amendment sequence'].tolist()
        
        for i in range(1, len(dates)):
            if pd.notna(dates[i-1]) and pd.notna(dates[i]):
                if dates[i] < dates[i-1]:  # Newer amendment has earlier date
                    date_sequence_issues.append({
                        'property': prop,
                        'tenant': tenant,
                        'seq1': sequences[i-1], 'date1': dates[i-1],
                        'seq2': sequences[i], 'date2': dates[i],
                        'issue': 'Date sequence violation'
                    })
    
    # Check 3: Latest sequence should be Activated (with rare exceptions)
    latest_amendment = amendments.iloc[-1]  # Highest sequence
    if latest_amendment['amendment status'] not in ['Activated', 'In Process']:
        status_sequence_issues.append({
            'property': prop,
            'tenant': tenant,
            'latest_sequence': latest_amendment['amendment sequence'],
            'status': latest_amendment['amendment status'],
            'issue': 'Latest amendment not Activated'
        })

print(f'Total property/tenant pairs analyzed: {len(df_cleaned.groupby(["property hmy", "tenant hmy"]))}')
print(f'Sequence numbering issues: {len(sequence_issues)}')
print(f'Date sequence issues: {len(date_sequence_issues)}')  
print(f'Status sequence issues: {len(status_sequence_issues)}')

# Report sequence numbering issues
if len(sequence_issues) > 0:
    print(f'\n🚨 SEQUENCE NUMBERING ISSUES ({len(sequence_issues)} cases):')
    for issue in sequence_issues[:5]:
        print(f'  Property {issue["property"]}, Tenant {issue["tenant"]}:')
        print(f'    Expected: {issue["expected"]}')
        print(f'    Actual: {issue["actual"]}')
else:
    print('\n✅ SEQUENCE NUMBERING: All amendment sequences are properly numbered')

# Report date sequence issues
if len(date_sequence_issues) > 0:
    print(f'\n⚠️ DATE SEQUENCE ISSUES ({len(date_sequence_issues)} cases):')
    for issue in date_sequence_issues[:5]:
        print(f'  Property {issue["property"]}, Tenant {issue["tenant"]}:')
        print(f'    Seq {issue["seq1"]} ({issue["date1"].strftime("%Y-%m-%d")}) -> Seq {issue["seq2"]} ({issue["date2"].strftime("%Y-%m-%d")})')
else:
    print('\n✅ DATE SEQUENCES: All amendment dates are in proper sequence')

# Report status sequence issues  
if len(status_sequence_issues) > 0:
    print(f'\n⚠️ STATUS SEQUENCE ISSUES ({len(status_sequence_issues)} cases):')
    for issue in status_sequence_issues[:5]:
        print(f'  Property {issue["property"]}, Tenant {issue["tenant"]}: Latest seq {issue["latest_sequence"]} is {issue["status"]}')
else:
    print('\n✅ STATUS SEQUENCES: All latest amendments have appropriate status')

# Summary
total_issues = len(sequence_issues) + len(date_sequence_issues) + len(status_sequence_issues)
if total_issues == 0:
    print('\n✅ AMENDMENT SEQUENCE VALIDATION PASSED: All sequences are properly ordered')
else:
    print(f'\n⚠️ AMENDMENT SEQUENCE VALIDATION: {total_issues} total issues found')