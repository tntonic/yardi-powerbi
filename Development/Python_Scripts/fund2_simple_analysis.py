#!/usr/bin/env python3
"""
Fund 2 Simple Data Issues Analysis
==================================

Simple but effective analysis of critical data integrity issues.
"""

import pandas as pd
import numpy as np
from datetime import datetime

def load_and_analyze():
    print("Loading Fund 2 data...")
    
    # Load data
    properties = pd.read_csv("Data/Fund2_Filtered/dim_property_fund2.csv")
    amendments = pd.read_csv("Data/Fund2_Filtered/dim_fp_amendmentsunitspropertytenant_fund2.csv")
    charges_all = pd.read_csv("Data/Fund2_Filtered/dim_fp_amendmentchargeschedule_fund2_all.csv")
    charges_active = pd.read_csv("Data/Fund2_Filtered/dim_fp_amendmentchargeschedule_fund2_active.csv")
    
    print("✓ Data loaded successfully")
    
    # Show column names for debugging
    print(f"\nAMENDMENT COLUMNS: {amendments.columns.tolist()}")
    
    # ISSUE 1: Duplicate Active Amendments
    print("\n" + "="*60)
    print("ISSUE 1: DUPLICATE ACTIVE AMENDMENTS")
    print("="*60)
    
    active_amendments = amendments[amendments['amendment status'] == 'Activated']
    print(f"Total active amendments: {len(active_amendments)}")
    
    # Group by property and tenant to find duplicates
    prop_tenant_counts = active_amendments.groupby(['property hmy', 'tenant hmy']).size()
    duplicates = prop_tenant_counts[prop_tenant_counts > 1]
    
    print(f"Property/tenant combinations with multiple active amendments: {len(duplicates)}")
    print(f"Total extra amendment records: {duplicates.sum() - len(duplicates)}")
    
    if len(duplicates) > 0:
        print("\nTop 10 problematic combinations:")
        top_duplicates = duplicates.nlargest(10)
        for (prop_hmy, tenant_hmy), count in top_duplicates.items():
            # Get details for this combination
            combo_details = active_amendments[
                (active_amendments['property hmy'] == prop_hmy) & 
                (active_amendments['tenant hmy'] == tenant_hmy)
            ]
            prop_code = combo_details['property code'].iloc[0]
            tenant_id = combo_details['tenant id'].iloc[0]
            sequences = combo_details['amendment sequence'].tolist()
            
            print(f"  {prop_code} | {tenant_id} | {count} active amendments (sequences: {sequences})")
    
    # ISSUE 2: Invalid Amendment Statuses
    print("\n" + "="*60)
    print("ISSUE 2: INVALID AMENDMENT STATUSES")
    print("="*60)
    
    valid_statuses = ['Activated', 'Superseded', 'Cancelled', 'Pending']
    status_counts = amendments['amendment status'].value_counts()
    print("All amendment statuses found:")
    for status, count in status_counts.items():
        is_valid = status in valid_statuses
        status_marker = "✓" if is_valid else "❌"
        print(f"  {status_marker} '{status}': {count}")
    
    invalid_amendments = amendments[~amendments['amendment status'].isin(valid_statuses)]
    if len(invalid_amendments) > 0:
        print(f"\nInvalid status examples:")
        examples = invalid_amendments[['property code', 'tenant id', 'amendment status', 'amendment type']].head(5)
        print(examples.to_string(index=False))
    
    # ISSUE 3: Date Range Issues  
    print("\n" + "="*60)
    print("ISSUE 3: CHARGE DATE RANGE ISSUES")
    print("="*60)
    
    print(f"Total charges: {len(charges_all)}")
    
    # Check for missing dates
    missing_from = charges_all['from date'].isnull().sum()
    missing_to = charges_all['to date'].isnull().sum()
    
    print(f"Charges with missing from date: {missing_from}")
    print(f"Charges with missing to date: {missing_to}")
    
    # Try to identify date format issues
    print("\nSample date values (from date):")
    sample_dates = charges_all['from date'].dropna().head(10)
    for i, date_val in enumerate(sample_dates):
        print(f"  {i+1}. {date_val} (type: {type(date_val)})")
    
    # ISSUE 4: Rent Roll Impact Analysis
    print("\n" + "="*60)
    print("ISSUE 4: RENT ROLL IMPACT ANALYSIS")
    print("="*60)
    
    # Count amendments without rent charges
    rent_charges = charges_active[charges_active['charge code desc'].str.contains('Rent', na=False, case=False)]
    amendments_with_rent = set(rent_charges['amendment hmy'])
    total_amendment_hmys = set(amendments['amendment hmy'])
    amendments_without_rent = total_amendment_hmys - amendments_with_rent
    
    print(f"Total amendments: {len(amendments)}")
    print(f"Amendments with rent charges: {len(amendments_with_rent)}")
    print(f"Amendments without rent charges: {len(amendments_without_rent)}")
    
    # Analysis of rent charges
    if len(rent_charges) > 0:
        print(f"\nRent charge analysis:")
        print(f"  Total rent charges: {len(rent_charges)}")
        print(f"  Average monthly rent: ${rent_charges['monthly amount'].mean():,.2f}")
        print(f"  Total monthly rent: ${rent_charges['monthly amount'].sum():,.2f}")
    
    # SUMMARY AND RECOMMENDATIONS
    print("\n" + "="*60)
    print("SUMMARY AND CRITICAL RECOMMENDATIONS")
    print("="*60)
    
    issues_found = []
    
    if len(duplicates) > 0:
        issues_found.append(f"🚨 {len(duplicates)} property/tenant combinations with duplicate active amendments")
        
    if len(invalid_amendments) > 0:
        issues_found.append(f"🚨 {len(invalid_amendments)} amendments with invalid statuses")
        
    if missing_from + missing_to > 0:
        issues_found.append(f"⚠️  {missing_from + missing_to} charges with missing dates")
        
    if len(amendments_without_rent) > 0:
        issues_found.append(f"⚠️  {len(amendments_without_rent)} amendments without rent charges")
    
    print(f"Issues identified: {len(issues_found)}")
    for i, issue in enumerate(issues_found, 1):
        print(f"  {i}. {issue}")
    
    if len(issues_found) > 0:
        print(f"\n💡 IMMEDIATE ACTIONS REQUIRED:")
        print(f"1. Fix duplicate active amendments (impacts rent roll accuracy)")
        print(f"2. Resolve invalid amendment statuses")
        print(f"3. Review and fix date format issues")
        print(f"4. Validate rent charges for completeness")
        print(f"\nEstimated impact on rent roll accuracy: HIGH")
        print(f"These issues will cause incorrect rent calculations and occupancy metrics.")
    else:
        print(f"\n✅ No critical issues found - data appears clean for rent roll calculations")

if __name__ == "__main__":
    load_and_analyze()