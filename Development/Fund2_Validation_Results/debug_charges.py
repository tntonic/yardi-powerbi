#!/usr/bin/env python3
"""Debug charge schedule data structure"""

import pandas as pd

# Load data
charges = pd.read_csv('../Data/Fund2_Filtered/dim_fp_amendmentchargeschedule_fund2_all.csv')
amendments = pd.read_csv('../Data/Fund2_Filtered/dim_fp_amendmentsunitspropertytenant_fund2.csv')

print('=== CHARGE SCHEDULE DEBUG ===')
print(f'Total charges: {len(charges):,}')
print(f'Charge columns: {list(charges.columns)}')
print()

print('Charge codes distribution:')
print(charges['charge code'].value_counts().head(10))
print()

print('Sample charge records:')
sample_cols = ['amendment hmy', 'charge code', 'monthly amount'] if all(col in charges.columns for col in ['amendment hmy', 'charge code', 'monthly amount']) else charges.columns[:5]
print(charges[sample_cols].head())
print()

print('Amendment HMY overlap:')
amendment_hmys = set(amendments['amendment hmy'])
charge_hmys = set(charges['amendment hmy']) if 'amendment hmy' in charges.columns else set()
if charge_hmys:
    overlap = len(amendment_hmys.intersection(charge_hmys))
    print(f'Amendments with charges: {overlap}/{len(amendment_hmys)} ({overlap/len(amendment_hmys)*100:.1f}%)')
else:
    print('No amendment hmy column found in charges')
print()

if 'monthly amount' in charges.columns:
    print('Monthly amount analysis:')
    non_zero = charges[charges['monthly amount'] > 0]
    print(f'Records with rent > 0: {len(non_zero):,}')
    if len(non_zero) > 0:
        print(f'Average monthly amount: ${non_zero["monthly amount"].mean():.2f}')
        print(f'Max monthly amount: ${non_zero["monthly amount"].max():.2f}')