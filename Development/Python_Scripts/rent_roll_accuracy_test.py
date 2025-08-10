import pandas as pd
import numpy as np
from datetime import datetime

print('=== RENT ROLL ACCURACY TEST WITH CLEANED DATA ===')

# Load cleaned data
amendments = pd.read_csv('Data/Yardi_Tables/dim_fp_amendmentsunitspropertytenant_cleaned.csv')
charges = pd.read_csv('Data/Yardi_Tables/dim_fp_amendmentchargeschedule_cleaned.csv')

print(f'Cleaned amendments loaded: {len(amendments):,}')
print(f'Cleaned charges loaded: {len(charges):,}')

# Convert dates
amendments['amendment start date'] = pd.to_datetime(amendments['amendment start date'])
amendments['amendment end date'] = pd.to_datetime(amendments['amendment end date'])

# Step 1: Generate rent roll using cleaned amendment logic
print('\n1. GENERATING RENT ROLL FROM CLEANED DATA...')

# Get latest amendments per property/tenant (correct rent roll logic)
latest_amendments = amendments.loc[amendments.groupby(['property hmy', 'tenant hmy'])['amendment sequence'].idxmax()]
print(f'Latest amendments (unique property/tenant pairs): {len(latest_amendments):,}')

# Filter to active statuses (Activated + Superseded, but latest should be mostly Activated)
active_latest = latest_amendments[latest_amendments['amendment status'].isin(['Activated', 'Superseded', 'In Process'])]
print(f'Active latest amendments: {len(active_latest):,}')

# Step 2: Join with base rent charges
print('\n2. JOINING WITH RENT CHARGES...')

# Get base rent charges only
base_rent_charges = charges[charges['charge code desc'] == 'Rent - Base'].copy()
print(f'Base rent charge records: {len(base_rent_charges):,}')

# Join amendments with their base rent charges
rent_roll_data = active_latest.merge(
    base_rent_charges, 
    on='amendment hmy', 
    how='left',
    suffixes=('_amend', '_charge')
)

print(f'Amendments with charge data joined: {len(rent_roll_data):,}')

# Step 3: Calculate data quality metrics
total_amendments_with_charges = rent_roll_data['amount'].notna().sum()
total_amendments_missing_charges = rent_roll_data['amount'].isna().sum()

print(f'\n3. RENT ROLL DATA QUALITY:')
print(f'   Amendments with base rent charges: {total_amendments_with_charges:,}')
print(f'   Amendments missing base rent charges: {total_amendments_missing_charges:,}')
print(f'   Charge coverage: {(total_amendments_with_charges/len(rent_roll_data)*100):.1f}%')

# Step 4: Calculate key rent roll metrics
amendments_with_rent = rent_roll_data[rent_roll_data['amount'].notna()].copy()

if len(amendments_with_rent) > 0:
    # Use monthly amount if available, otherwise amount
    amendments_with_rent['monthly_rent'] = amendments_with_rent['monthly amount'].fillna(amendments_with_rent['amount'])
    
    total_monthly_rent = amendments_with_rent['monthly_rent'].sum()
    total_leased_sf = amendments_with_rent['amendment sf'].sum()
    
    print(f'\n4. KEY RENT ROLL METRICS:')
    print(f'   Total monthly rent: ${total_monthly_rent:,.2f}')
    print(f'   Total leased SF (with rent): {total_leased_sf:,.0f}')
    
    if total_leased_sf > 0:
        avg_rent_psf = (total_monthly_rent * 12) / total_leased_sf
        print(f'   Average rent PSF (annual): ${avg_rent_psf:.2f}')
else:
    print(f'\n4. KEY RENT ROLL METRICS:')
    print('   No amendments with rent charges found!')

# Step 5: Analyze missing charges impact
missing_rent_amendments = rent_roll_data[rent_roll_data['amount'].isna()]
missing_rent_sf = missing_rent_amendments['amendment sf'].sum()
total_sf = rent_roll_data['amendment sf'].sum()

print(f'\n5. MISSING CHARGES IMPACT:')
print(f'   Total SF in active amendments: {total_sf:,.0f}')
print(f'   SF missing rent charges: {missing_rent_sf:,.0f}')
if total_sf > 0:
    print(f'   Percentage of SF missing charges: {(missing_rent_sf/total_sf*100):.1f}%')

# Step 6: Amendment status validation
print(f'\n6. AMENDMENT STATUS VALIDATION:')
status_counts = active_latest['amendment status'].value_counts()
for status, count in status_counts.items():
    percentage = (count / len(active_latest)) * 100
    print(f'   {status}: {count:,} ({percentage:.1f}%)')

# Step 7: Accuracy estimation
charge_coverage_accuracy = (total_amendments_with_charges / len(active_latest)) * 100
sf_coverage_accuracy = ((total_sf - missing_rent_sf) / total_sf * 100) if total_sf > 0 else 0

print(f'\n7. RENT ROLL ACCURACY ESTIMATION:')
print(f'   Charge coverage accuracy: {charge_coverage_accuracy:.1f}%')
print(f'   SF coverage accuracy: {sf_coverage_accuracy:.1f}%')

# Determine overall accuracy (use the lower of the two)
overall_accuracy = min(charge_coverage_accuracy, sf_coverage_accuracy)
print(f'   Overall estimated accuracy: {overall_accuracy:.1f}%')

if overall_accuracy >= 95:
    print('   ✅ ACCURACY TARGET MET: >95% coverage')
elif overall_accuracy >= 90:
    print('   ⚠️ ACCURACY WARNING: 90-95% coverage')
else:
    print('   🚨 ACCURACY ISSUE: <90% coverage')

# Step 8: Validation against known issues
print(f'\n8. VALIDATION AGAINST KNOWN MISSING CHARGES:')
print(f'   Known RENT_EXPECTED (critical): 528 amendments')
print(f'   Actual missing base rent charges: {total_amendments_missing_charges:,}')

difference = abs(total_amendments_missing_charges - 528)
if difference <= 50:  # Some tolerance
    print('   ✅ MISSING CHARGES MATCH EXPECTED RANGE')
else:
    print(f'   ⚠️ DIFFERENCE FROM EXPECTED: {difference:,} amendments')

# Step 9: Sample missing charge analysis
if len(missing_rent_amendments) > 0:
    print(f'\n9. SAMPLE MISSING CHARGES ANALYSIS:')
    print('   Top properties by SF missing base rent:')
    missing_by_property = missing_rent_amendments.groupby('property code_amend')['amendment sf'].sum().sort_values(ascending=False)
    for prop, sf in missing_by_property.head(5).items():
        print(f'     {prop}: {sf:,.0f} SF')

print('\n=== RENT ROLL ACCURACY TEST COMPLETE ===')