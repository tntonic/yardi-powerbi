#!/usr/bin/env python3
"""
Identifies properties that might be missing from Fund 2 based on activity patterns
"""

import pandas as pd

def main():
    print("="*80)
    print("MISSING FUND 2 PROPERTIES ANALYSIS")
    print("="*80)
    
    # Load data
    base_path = "/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Data"
    
    amendments = pd.read_csv(f"{base_path}/Yardi_Tables/dim_fp_amendmentsunitspropertytenant.csv")
    terminations = pd.read_csv(f"{base_path}/Yardi_Tables/dim_fp_terminationtomoveoutreas.csv")
    properties = pd.read_csv(f"{base_path}/Yardi_Tables/dim_property.csv")
    fund2_properties = pd.read_csv(f"{base_path}/Fund2_Filtered/dim_property_fund2.csv")
    
    # Convert dates
    for df in [amendments, terminations]:
        for col in ['amendment start date', 'amendment end date']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # Current Fund 2 property codes
    current_fund2_codes = fund2_properties['property code'].unique()
    print(f"Current Fund 2 properties: {len(current_fund2_codes)}")
    
    # Q1 2025 analysis
    q1_start = pd.Timestamp('2025-01-01')
    q1_end = pd.Timestamp('2025-03-31')
    
    # Properties with Q1 2025 terminations
    q1_terminations = terminations[
        (terminations['amendment end date'] >= q1_start) &
        (terminations['amendment end date'] <= q1_end) &
        (terminations['amendment status'].isin(['Activated', 'Superseded'])) &
        (terminations['amendment type'] == 'Termination')
    ]
    
    term_properties = q1_terminations.groupby('property code')['amendment sf'].sum().sort_values(ascending=False)
    
    print("\nQ1 2025 Termination Properties by SF:")
    print("-" * 40)
    for prop, sf in term_properties.head(20).items():
        in_fund2 = "✓" if prop in current_fund2_codes else "✗"
        print(f"{prop:>12}: {sf:>10,.0f} SF [{in_fund2}]")
    
    # Properties with Q1 2025 new leases
    q1_new_leases = amendments[
        (amendments['amendment start date'] >= q1_start) &
        (amendments['amendment start date'] <= q1_end) &
        (amendments['amendment status'].isin(['Activated', 'Superseded'])) &
        (amendments['amendment type'].isin(['Original Lease', 'New Lease']))
    ]
    
    new_lease_properties = q1_new_leases.groupby('property code')['amendment sf'].sum().sort_values(ascending=False)
    
    print("\nQ1 2025 New Lease Properties by SF:")
    print("-" * 40)
    for prop, sf in new_lease_properties.head(20).items():
        in_fund2 = "✓" if prop in current_fund2_codes else "✗"
        print(f"{prop:>12}: {sf:>10,.0f} SF [{in_fund2}]")
    
    # Identify properties that might belong to Fund 2 based on activity
    missing_term_props = [prop for prop in term_properties.index[:10] if prop not in current_fund2_codes]
    missing_new_props = [prop for prop in new_lease_properties.index[:10] if prop not in current_fund2_codes]
    
    print(f"\nPotentially missing Fund 2 properties (high termination activity):")
    for prop in missing_term_props:
        sf = term_properties[prop]
        print(f"  {prop}: {sf:,.0f} SF")
    
    print(f"\nPotentially missing Fund 2 properties (high new lease activity):")
    for prop in missing_new_props:
        sf = new_lease_properties[prop]
        print(f"  {prop}: {sf:,.0f} SF")
    
    # What if we include the top termination properties as Fund 2?
    print("\n" + "="*80)
    print("SCENARIO: Include Top Termination Properties in Fund 2")
    print("="*80)
    
    # Take top properties by termination activity that aren't currently in Fund 2
    additional_properties = []
    additional_sf = 0
    target_sf = 712_000 - term_properties[term_properties.index.isin(current_fund2_codes)].sum()
    
    print(f"Current Fund 2 Q1 termination SF: {term_properties[term_properties.index.isin(current_fund2_codes)].sum():,.0f}")
    print(f"Need additional: {target_sf:,.0f} SF to reach target of 712,000")
    
    for prop, sf in term_properties.items():
        if prop not in current_fund2_codes and additional_sf < target_sf:
            additional_properties.append(prop)
            additional_sf += sf
            print(f"Adding {prop}: {sf:,.0f} SF (Total additional: {additional_sf:,.0f})")
    
    # Test this expanded Fund 2 definition
    expanded_fund2_codes = list(current_fund2_codes) + additional_properties
    expanded_fund2_term_sf = term_properties[term_properties.index.isin(expanded_fund2_codes)].sum()
    expanded_fund2_new_sf = new_lease_properties[new_lease_properties.index.isin(expanded_fund2_codes)].sum()
    
    print(f"\nExpanded Fund 2 Results:")
    print(f"Q1 2025 Terminations: {expanded_fund2_term_sf:,.0f} SF (Target: 712,000)")
    print(f"Q1 2025 New Leases: {expanded_fund2_new_sf:,.0f} SF (Target: 198,000)")
    print(f"Q1 2025 Net Absorption: {expanded_fund2_new_sf - expanded_fund2_term_sf:,.0f} SF (Target: -514,000)")
    
    # Check Q2 2025 with expanded definition
    q2_start = pd.Timestamp('2025-04-01')
    q2_end = pd.Timestamp('2025-06-30')
    
    q2_terminations = terminations[
        (terminations['amendment end date'] >= q2_start) &
        (terminations['amendment end date'] <= q2_end) &
        (terminations['amendment status'].isin(['Activated', 'Superseded'])) &
        (terminations['amendment type'] == 'Termination')
    ]
    
    q2_new_leases = amendments[
        (amendments['amendment start date'] >= q2_start) &
        (amendments['amendment start date'] <= q2_end) &
        (amendments['amendment status'].isin(['Activated', 'Superseded'])) &
        (amendments['amendment type'].isin(['Original Lease', 'New Lease']))
    ]
    
    q2_term_props = q2_terminations.groupby('property code')['amendment sf'].sum()
    q2_new_props = q2_new_leases.groupby('property code')['amendment sf'].sum()
    
    expanded_q2_term_sf = q2_term_props[q2_term_props.index.isin(expanded_fund2_codes)].sum()
    expanded_q2_new_sf = q2_new_props[q2_new_props.index.isin(expanded_fund2_codes)].sum()
    
    print(f"\nQ2 2025 Terminations: {expanded_q2_term_sf:,.0f} SF (Target: 458,000)")
    print(f"Q2 2025 New Leases: {expanded_q2_new_sf:,.0f} SF (Target: 258,000)")
    print(f"Q2 2025 Net Absorption: {expanded_q2_new_sf - expanded_q2_term_sf:,.0f} SF (Target: -200,000)")
    
    # Save expanded property list
    print(f"\nExpanded Fund 2 property codes ({len(expanded_fund2_codes)} total):")
    print(sorted(expanded_fund2_codes))

if __name__ == "__main__":
    main()