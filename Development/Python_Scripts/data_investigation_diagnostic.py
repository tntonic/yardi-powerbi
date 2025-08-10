#!/usr/bin/env python3
"""
Data Investigation Diagnostic

Investigates why same-store net absorption measures are returning zero values.
Analyzes data structure, filtering logic, and date ranges.

Author: Claude Code
Date: 2025-08-10
"""

import pandas as pd
import numpy as np
from datetime import datetime, date
import sys
import os

def investigate_data_issues():
    """Investigate data filtering and matching issues"""
    
    print("="*80)
    print("DATA INVESTIGATION DIAGNOSTIC")
    print("="*80)
    
    # Data paths
    base_path = "/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Data"
    fund2_path = f"{base_path}/Fund2_Filtered"
    yardi_path = f"{base_path}/Yardi_Tables"
    
    # Q4 2024 period
    period_start = pd.Timestamp('2024-10-01')
    period_end = pd.Timestamp('2024-12-31')
    
    try:
        # Load data
        print("Loading data sources...")
        amendments_fund2 = pd.read_csv(f"{fund2_path}/dim_fp_amendmentsunitspropertytenant_fund2.csv")
        properties_fund2 = pd.read_csv(f"{fund2_path}/dim_property_fund2.csv")
        terminations = pd.read_csv(f"{yardi_path}/dim_fp_terminationtomoveoutreas.csv")
        properties_all = pd.read_csv(f"{yardi_path}/dim_property.csv")
        
        print(f"Fund 2 amendments: {len(amendments_fund2)}")
        print(f"Fund 2 properties: {len(properties_fund2)}")
        print(f"All terminations: {len(terminations)}")
        print(f"All properties: {len(properties_all)}")
        
        # Check date columns and formats
        print("\n" + "="*50)
        print("DATE COLUMN ANALYSIS")
        print("="*50)
        
        print("\nFund 2 Properties - Date Columns:")
        for col in properties_fund2.columns:
            if 'date' in col.lower():
                print(f"  {col}: {properties_fund2[col].dtype}")
                print(f"    Sample values: {properties_fund2[col].dropna().head(3).tolist()}")
                
        print("\nFund 2 Amendments - Date Columns:")
        for col in amendments_fund2.columns:
            if 'date' in col.lower():
                print(f"  {col}: {amendments_fund2[col].dtype}")
                print(f"    Sample values: {amendments_fund2[col].dropna().head(3).tolist()}")
                
        print("\nTerminations - Date Columns:")
        for col in terminations.columns:
            if 'date' in col.lower():
                print(f"  {col}: {terminations[col].dtype}")
                print(f"    Sample values: {terminations[col].dropna().head(3).tolist()}")
        
        # Convert dates
        print("\n" + "="*50)
        print("DATE CONVERSION")
        print("="*50)
        
        # Convert amendment dates
        date_cols_amendments = ['amendment start date', 'amendment end date', 'amendment sign date']
        for col in date_cols_amendments:
            if col in amendments_fund2.columns:
                amendments_fund2[col] = pd.to_datetime(amendments_fund2[col], errors='coerce')
                print(f"Converted Fund2 amendments '{col}': {amendments_fund2[col].dtype}")
                
        # Convert termination dates
        for col in date_cols_amendments:
            if col in terminations.columns:
                terminations[col] = pd.to_datetime(terminations[col], errors='coerce')
                print(f"Converted terminations '{col}': {terminations[col].dtype}")
                
        # Convert property dates
        property_date_cols = ['acquire date', 'dispose date', 'inactive date']
        for col in property_date_cols:
            if col in properties_fund2.columns:
                properties_fund2[col] = pd.to_datetime(properties_fund2[col], errors='coerce')
                print(f"Converted Fund2 properties '{col}': {properties_fund2[col].dtype}")
            if col in properties_all.columns:
                properties_all[col] = pd.to_datetime(properties_all[col], errors='coerce')
                print(f"Converted all properties '{col}': {properties_all[col].dtype}")
        
        # Analyze same-store properties logic
        print("\n" + "="*50)
        print("SAME-STORE PROPERTIES ANALYSIS")
        print("="*50)
        
        print(f"Period: {period_start} to {period_end}")
        
        # Check acquire dates
        print(f"\nFund 2 properties with acquire date:")
        acquire_mask = properties_fund2['acquire date'].notna()
        print(f"  Total with acquire date: {acquire_mask.sum()}")
        if acquire_mask.sum() > 0:
            print(f"  Acquire date range: {properties_fund2['acquire date'].min()} to {properties_fund2['acquire date'].max()}")
            print(f"  Properties acquired before {period_start}: {(properties_fund2['acquire date'] < period_start).sum()}")
        
        # Check dispose dates
        print(f"\nFund 2 properties with dispose date:")
        dispose_mask = properties_fund2['dispose date'].notna()
        print(f"  Total with dispose date: {dispose_mask.sum()}")
        if dispose_mask.sum() > 0:
            print(f"  Dispose date range: {properties_fund2['dispose date'].min()} to {properties_fund2['dispose date'].max()}")
            print(f"  Properties disposed after {period_end}: {(properties_fund2['dispose date'] > period_end).sum()}")
        
        # Same-store calculation
        same_store_mask = (
            (properties_fund2['acquire date'] < period_start) &
            (
                properties_fund2['dispose date'].isna() |
                (properties_fund2['dispose date'] > period_end)
            )
        )
        same_store_properties = properties_fund2[same_store_mask]
        print(f"\nSame-store properties identified: {len(same_store_properties)}")
        
        if len(same_store_properties) > 0:
            print("\nSame-store property codes:")
            for code in same_store_properties['property code'].head(10):
                print(f"  {code}")
        
        # Analyze Q4 2024 activity
        print("\n" + "="*50)
        print("Q4 2024 ACTIVITY ANALYSIS")
        print("="*50)
        
        # Terminations in Q4 2024
        print("\nTerminations Analysis:")
        terminations_q4 = terminations[
            (terminations['amendment end date'] >= period_start) &
            (terminations['amendment end date'] <= period_end)
        ]
        print(f"  Total terminations in Q4 2024: {len(terminations_q4)}")
        
        if len(terminations_q4) > 0:
            print(f"  Status breakdown:")
            status_counts = terminations_q4['amendment status'].value_counts()
            for status, count in status_counts.items():
                print(f"    {status}: {count}")
            
            print(f"\n  Sample termination property codes:")
            for code in terminations_q4['property code'].head(10):
                print(f"    {code}")
        
        # New leases in Q4 2024  
        print("\nNew Leases Analysis:")
        new_leases_q4 = amendments_fund2[
            (amendments_fund2['amendment start date'] >= period_start) &
            (amendments_fund2['amendment start date'] <= period_end)
        ]
        print(f"  Total amendments starting in Q4 2024: {len(new_leases_q4)}")
        
        if len(new_leases_q4) > 0:
            print(f"  Amendment type breakdown:")
            type_counts = new_leases_q4['amendment type'].value_counts()
            for atype, count in type_counts.items():
                print(f"    {atype}: {count}")
                
            print(f"  Status breakdown:")
            status_counts = new_leases_q4['amendment status'].value_counts()
            for status, count in status_counts.items():
                print(f"    {status}: {count}")
        
        # Check for disposal properties
        print("\n" + "="*50)
        print("DISPOSAL PROPERTIES ANALYSIS")
        print("="*50)
        
        # Look for disposed properties in Q4 2024
        disposed_q4_all = properties_all[
            (properties_all['dispose date'] >= period_start) &
            (properties_all['dispose date'] <= period_end) &
            (properties_all['dispose date'].notna())
        ]
        print(f"Disposed properties in Q4 2024 (all): {len(disposed_q4_all)}")
        
        if len(disposed_q4_all) > 0:
            print("Disposed properties:")
            for _, prop in disposed_q4_all.iterrows():
                print(f"  {prop['property name']} ({prop['property code']}) - {prop['dispose date']}")
                
        # Check for "14 Morris" and "187 Bobrick"
        morris_mask = properties_all['property name'].str.contains('14 Morris', case=False, na=False)
        bobrick_mask = properties_all['property name'].str.contains('187 Bobrick', case=False, na=False)
        
        print(f"\n'14 Morris' properties found: {morris_mask.sum()}")
        if morris_mask.sum() > 0:
            morris_props = properties_all[morris_mask]
            for _, prop in morris_props.iterrows():
                print(f"  {prop['property name']} - Dispose date: {prop['dispose date']}")
                
        print(f"'187 Bobrick' properties found: {bobrick_mask.sum()}")
        if bobrick_mask.sum() > 0:
            bobrick_props = properties_all[bobrick_mask]
            for _, prop in bobrick_props.iterrows():
                print(f"  {prop['property name']} - Dispose date: {prop['dispose date']}")
        
        # Property HMY matching analysis
        print("\n" + "="*50)
        print("PROPERTY HMY MATCHING ANALYSIS")
        print("="*50)
        
        # Check if property HMY exists and matches
        if 'property hmy' in same_store_properties.columns:
            same_store_hmys = same_store_properties['property hmy'].tolist()
            print(f"Same-store property HMYs: {len(same_store_hmys)}")
            print(f"Sample HMYs: {same_store_hmys[:5]}")
            
            # Check terminations matching
            if len(terminations_q4) > 0:
                termination_hmys = terminations_q4['property hmy'].unique()
                matching_termination_hmys = [hmy for hmy in termination_hmys if hmy in same_store_hmys]
                print(f"\nTermination HMYs in Q4: {len(termination_hmys)}")
                print(f"Matching same-store termination HMYs: {len(matching_termination_hmys)}")
                
            # Check amendments matching
            if len(new_leases_q4) > 0:
                amendment_hmys = new_leases_q4['property hmy'].unique()
                matching_amendment_hmys = [hmy for hmy in amendment_hmys if hmy in same_store_hmys]
                print(f"Amendment HMYs in Q4: {len(amendment_hmys)}")
                print(f"Matching same-store amendment HMYs: {len(matching_amendment_hmys)}")
        else:
            print("No 'property hmy' column in same-store properties")
            
            # Try property code matching instead
            same_store_codes = same_store_properties['property code'].tolist()
            print(f"Same-store property codes: {len(same_store_codes)}")
            print(f"Sample codes: {same_store_codes[:5]}")
            
            if len(terminations_q4) > 0:
                termination_codes = terminations_q4['property code'].unique()
                matching_termination_codes = [code for code in termination_codes if code in same_store_codes]
                print(f"\nTermination codes in Q4: {len(termination_codes)}")
                print(f"Matching same-store termination codes: {len(matching_termination_codes)}")
                if matching_termination_codes:
                    print(f"Matching codes: {matching_termination_codes}")
                
            if len(new_leases_q4) > 0:
                amendment_codes = new_leases_q4['property code'].unique()
                matching_amendment_codes = [code for code in amendment_codes if code in same_store_codes]
                print(f"Amendment codes in Q4: {len(amendment_codes)}")
                print(f"Matching same-store amendment codes: {len(matching_amendment_codes)}")
                if matching_amendment_codes:
                    print(f"Matching codes: {matching_amendment_codes}")
                    
        # Summary and recommendations
        print("\n" + "="*50)
        print("SUMMARY AND RECOMMENDATIONS")
        print("="*50)
        
        print("KEY FINDINGS:")
        print(f"1. Same-store properties identified: {len(same_store_properties)}")
        print(f"2. Q4 2024 terminations: {len(terminations_q4)}")
        print(f"3. Q4 2024 new amendments: {len(new_leases_q4)}")
        print(f"4. Q4 2024 dispositions: {len(disposed_q4_all)}")
        
        print("\nPOTENTIAL ISSUES:")
        if len(same_store_properties) < 50:
            print("- Very few same-store properties identified")
            print("- Check acquire date filtering logic")
        if len(disposed_q4_all) == 0:
            print("- No disposed properties found in Q4 2024")
            print("- Check dispose date format and filtering")
        if len(terminations_q4) > 0 and len(same_store_properties) > 0:
            print("- Terminations exist but may not match same-store properties")
            print("- Check HMY/property code matching logic")
        
        print("\nRECOMMENDATIONS:")
        print("1. Verify Fund 2 data completeness")
        print("2. Check date format consistency")
        print("3. Validate property HMY matching between datasets")
        print("4. Review same-store property criteria")
        print("5. Consider using property codes instead of HMYs for matching")
                
    except Exception as e:
        print(f"Error during investigation: {str(e)}")
        
if __name__ == "__main__":
    investigate_data_issues()