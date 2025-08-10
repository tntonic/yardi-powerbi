#!/usr/bin/env python3
"""
Investigates Fund 2 and Fund 3 data to understand the discrepancies
"""

import pandas as pd
import numpy as np
from datetime import datetime

def main():
    print("="*80)
    print("FUND 2 & FUND 3 DATA INVESTIGATION")
    print("="*80)
    
    # Load data
    base_path = "/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Data"
    
    # Load all data
    amendments = pd.read_csv(f"{base_path}/Yardi_Tables/dim_fp_amendmentsunitspropertytenant.csv")
    terminations = pd.read_csv(f"{base_path}/Yardi_Tables/dim_fp_terminationtomoveoutreas.csv")
    properties = pd.read_csv(f"{base_path}/Yardi_Tables/dim_property.csv")
    
    # Load Fund 2 filtered data
    fund2_amendments = pd.read_csv(f"{base_path}/Fund2_Filtered/dim_fp_amendmentsunitspropertytenant_fund2.csv")
    fund2_properties = pd.read_csv(f"{base_path}/Fund2_Filtered/dim_property_fund2.csv")
    
    # Convert dates
    for df in [amendments, terminations, fund2_amendments]:
        for col in ['amendment start date', 'amendment end date']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
    
    for df in [properties, fund2_properties]:
        for col in ['acquire date', 'dispose date']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
    
    print("\n1. DATA OVERVIEW")
    print("-" * 40)
    print(f"Total amendments: {len(amendments):,}")
    print(f"Total terminations: {len(terminations):,}")
    print(f"Total properties: {len(properties):,}")
    print(f"Fund 2 amendments: {len(fund2_amendments):,}")
    print(f"Fund 2 properties: {len(fund2_properties):,}")
    
    # Check Fund 2 property codes
    fund2_prop_codes = fund2_properties['property code'].unique()
    print(f"\nFund 2 property codes sample: {fund2_prop_codes[:10]}")
    
    # Q1 2025 Analysis
    print("\n2. Q1 2025 TERMINATIONS (Jan 1 - Mar 31, 2025)")
    print("-" * 40)
    
    q1_2025_start = pd.Timestamp('2025-01-01')
    q1_2025_end = pd.Timestamp('2025-03-31')
    
    # All terminations in Q1 2025
    q1_terminations = terminations[
        (terminations['amendment end date'] >= q1_2025_start) &
        (terminations['amendment end date'] <= q1_2025_end) &
        (terminations['amendment status'].isin(['Activated', 'Superseded'])) &
        (terminations['amendment type'] == 'Termination')
    ]
    
    print(f"Total Q1 2025 terminations: {len(q1_terminations)}")
    print(f"Total Q1 2025 terminations SF: {q1_terminations['amendment sf'].sum():,.0f}")
    
    # Property codes in terminations
    term_prop_codes = q1_terminations['property code'].unique()
    print(f"Properties with terminations: {len(term_prop_codes)}")
    print(f"Sample termination property codes: {term_prop_codes[:10]}")
    
    # Fund 2 terminations
    fund2_q1_terminations = q1_terminations[
        q1_terminations['property code'].isin(fund2_prop_codes)
    ]
    
    print(f"\nFund 2 Q1 2025 terminations: {len(fund2_q1_terminations)}")
    print(f"Fund 2 Q1 2025 terminations SF: {fund2_q1_terminations['amendment sf'].sum():,.0f}")
    print(f"Target: 712,000 SF")
    
    # Q1 2025 New Leases
    print("\n3. Q1 2025 NEW LEASES (Jan 1 - Mar 31, 2025)")
    print("-" * 40)
    
    q1_new_leases = amendments[
        (amendments['amendment start date'] >= q1_2025_start) &
        (amendments['amendment start date'] <= q1_2025_end) &
        (amendments['amendment status'].isin(['Activated', 'Superseded'])) &
        (amendments['amendment type'].isin(['Original Lease', 'New Lease']))
    ]
    
    print(f"Total Q1 2025 new leases: {len(q1_new_leases)}")
    print(f"Total Q1 2025 new leases SF: {q1_new_leases['amendment sf'].sum():,.0f}")
    
    # Fund 2 new leases
    fund2_q1_new_leases = q1_new_leases[
        q1_new_leases['property code'].isin(fund2_prop_codes)
    ]
    
    print(f"\nFund 2 Q1 2025 new leases: {len(fund2_q1_new_leases)}")
    print(f"Fund 2 Q1 2025 new leases SF: {fund2_q1_new_leases['amendment sf'].sum():,.0f}")
    print(f"Target: 198,000 SF")
    
    # Q2 2025 Analysis
    print("\n4. Q2 2025 ANALYSIS (Apr 1 - Jun 30, 2025)")
    print("-" * 40)
    
    q2_2025_start = pd.Timestamp('2025-04-01')
    q2_2025_end = pd.Timestamp('2025-06-30')
    
    # Q2 terminations
    q2_terminations = terminations[
        (terminations['amendment end date'] >= q2_2025_start) &
        (terminations['amendment end date'] <= q2_2025_end) &
        (terminations['amendment status'].isin(['Activated', 'Superseded'])) &
        (terminations['amendment type'] == 'Termination')
    ]
    
    fund2_q2_terminations = q2_terminations[
        q2_terminations['property code'].isin(fund2_prop_codes)
    ]
    
    print(f"Fund 2 Q2 2025 terminations: {len(fund2_q2_terminations)}")
    print(f"Fund 2 Q2 2025 terminations SF: {fund2_q2_terminations['amendment sf'].sum():,.0f}")
    print(f"Target: 458,000 SF")
    
    # Q2 new leases
    q2_new_leases = amendments[
        (amendments['amendment start date'] >= q2_2025_start) &
        (amendments['amendment start date'] <= q2_2025_end) &
        (amendments['amendment status'].isin(['Activated', 'Superseded'])) &
        (amendments['amendment type'].isin(['Original Lease', 'New Lease']))
    ]
    
    fund2_q2_new_leases = q2_new_leases[
        q2_new_leases['property code'].isin(fund2_prop_codes)
    ]
    
    print(f"\nFund 2 Q2 2025 new leases: {len(fund2_q2_new_leases)}")
    print(f"Fund 2 Q2 2025 new leases SF: {fund2_q2_new_leases['amendment sf'].sum():,.0f}")
    print(f"Target: 258,000 SF")
    
    # Check if FPR data might be using different fund definitions
    print("\n5. ALTERNATIVE FUND IDENTIFICATION")
    print("-" * 40)
    
    # Try to identify funds by property name patterns
    if 'property name' in properties.columns:
        fund2_by_name = properties[
            properties['property name'].str.contains('Fund 2|Fund2|F2', case=False, na=False)
        ]
        fund3_by_name = properties[
            properties['property name'].str.contains('Fund 3|Fund3|F3', case=False, na=False)
        ]
        
        print(f"Properties with 'Fund 2' in name: {len(fund2_by_name)}")
        print(f"Properties with 'Fund 3' in name: {len(fund3_by_name)}")
    
    # Check if there's a fund column
    for col in properties.columns:
        if 'fund' in col.lower():
            print(f"\nFound fund column: {col}")
            print(properties[col].value_counts().head(10))
    
    # Check property code patterns
    print("\n6. PROPERTY CODE PATTERNS")
    print("-" * 40)
    
    all_prop_codes = properties['property code'].dropna()
    code_prefixes = all_prop_codes.str[:3].value_counts().head(10)
    print("Top property code prefixes:")
    print(code_prefixes)
    
    # Calculate using ALL properties (no fund filtering) for comparison
    print("\n7. ALL PROPERTIES ANALYSIS (No Fund Filter)")
    print("-" * 40)
    
    all_q1_term_sf = q1_terminations['amendment sf'].sum()
    all_q1_new_sf = q1_new_leases['amendment sf'].sum()
    
    print(f"All properties Q1 2025 terminations SF: {all_q1_term_sf:,.0f}")
    print(f"All properties Q1 2025 new leases SF: {all_q1_new_sf:,.0f}")
    print(f"All properties Q1 2025 net absorption: {all_q1_new_sf - all_q1_term_sf:,.0f}")
    
    all_q2_term_sf = q2_terminations['amendment sf'].sum()
    all_q2_new_sf = q2_new_leases['amendment sf'].sum()
    
    print(f"\nAll properties Q2 2025 terminations SF: {all_q2_term_sf:,.0f}")
    print(f"All properties Q2 2025 new leases SF: {all_q2_new_sf:,.0f}")
    print(f"All properties Q2 2025 net absorption: {all_q2_new_sf - all_q2_term_sf:,.0f}")

if __name__ == "__main__":
    main()