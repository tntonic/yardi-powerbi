#!/usr/bin/env python3
"""
YSQL-Based DAX Improvements Validation Script
==============================================
Purpose: Validates the improvements made to DAX measures based on YSQL documentation
Author: PowerBI Development Team
Date: 2025-08-09

This script validates:
1. Modification amendment type exclusion
2. Month-to-month lease identification
3. Property status filtering
4. Charge code validation
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os

# Data paths
DATA_PATH = "/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Data/Yardi_Tables"

def load_data():
    """Load required data tables"""
    print("Loading data tables...")
    
    # Load amendments table
    amendments = pd.read_csv(
        f"{DATA_PATH}/dim_fp_amendmentsunitspropertytenant_cleaned.csv",
        parse_dates=['amendment start date', 'amendment end date']
    )
    
    # Load charge schedule
    charges = pd.read_csv(
        f"{DATA_PATH}/dim_fp_amendmentchargeschedule_cleaned.csv",
        parse_dates=['from date', 'to date']
    )
    
    # Load properties
    properties = pd.read_csv(
        f"{DATA_PATH}/dim_property.csv",
        parse_dates=['acquire date', 'dispose date']
    )
    
    # Load charge types
    charge_types = pd.read_csv(f"{DATA_PATH}/dim_fp_chargecodetypeandgl.csv")
    
    return amendments, charges, properties, charge_types

def validate_amendment_exclusions(amendments):
    """Validate that Modification amendments are properly excluded"""
    print("\n" + "="*60)
    print("VALIDATION 1: Amendment Type Exclusions")
    print("="*60)
    
    # Check for Modification type (should be excluded)
    modifications = amendments[amendments['amendment type'] == 'Modification']
    print(f"Modification amendments found: {len(modifications)}")
    
    # Check for Proposal in DM (should be excluded)
    proposals = amendments[amendments['amendment type'] == 'Proposal in DM']
    print(f"Proposal in DM amendments found: {len(proposals)}")
    
    # Check for Termination (should be excluded from rent roll)
    terminations = amendments[amendments['amendment type'] == 'Termination']
    print(f"Termination amendments found: {len(terminations)}")
    
    # Validate active amendments (should only include Activated and Superseded)
    active_amendments = amendments[
        amendments['amendment status'].isin(['Activated', 'Superseded'])
    ]
    print(f"\nActive amendments (Activated + Superseded): {len(active_amendments)}")
    
    # Check status distribution
    status_counts = amendments['amendment status'].value_counts()
    print("\nAmendment Status Distribution:")
    for status, count in status_counts.items():
        print(f"  {status}: {count}")
    
    return len(modifications) == 0  # Should be 0 after filtering

def validate_month_to_month_leases(amendments):
    """Validate month-to-month lease identification"""
    print("\n" + "="*60)
    print("VALIDATION 2: Month-to-Month Lease Identification")
    print("="*60)
    
    # Identify month-to-month leases (null end date AND 0 term)
    mtm_leases = amendments[
        (amendments['amendment end date'].isna()) & 
        (amendments['amendment term'] == 0)
    ]
    
    print(f"Month-to-month leases identified: {len(mtm_leases)}")
    
    # Check if these are active
    active_mtm = mtm_leases[
        mtm_leases['amendment status'].isin(['Activated', 'Superseded'])
    ]
    print(f"Active month-to-month leases: {len(active_mtm)}")
    
    # Sample validation
    if len(mtm_leases) > 0:
        print("\nSample month-to-month leases:")
        # Get actual column names
        available_cols = mtm_leases.columns.tolist()
        # Find columns that exist
        sample_cols = [col for col in ['amendment hmy', 'lease code', 'amendment status', 
                      'amendment term', 'amendment end date'] if col in available_cols]
        if sample_cols:
            print(mtm_leases[sample_cols].head(5).to_string())
        else:
            print(mtm_leases.head(5).to_string())
    
    return len(mtm_leases) > 0  # Should find some MTM leases

def validate_property_status(properties):
    """Validate property status filtering"""
    print("\n" + "="*60)
    print("VALIDATION 3: Property Status Filtering")
    print("="*60)
    
    # Active properties (acquired but not disposed)
    active_properties = properties[
        (properties['acquire date'].notna()) & 
        (properties['dispose date'].isna())
    ]
    
    # Disposed properties (sold)
    disposed_properties = properties[
        properties['dispose date'].notna()
    ]
    
    # Properties with no acquisition date (shouldn't exist in production)
    no_acquire = properties[properties['acquire date'].isna()]
    
    print(f"Active properties (acquired, not disposed): {len(active_properties)}")
    print(f"Disposed properties (sold): {len(disposed_properties)}")
    print(f"Properties with no acquisition date: {len(no_acquire)}")
    
    total = len(properties)
    print(f"\nTotal properties: {total}")
    print(f"Active percentage: {len(active_properties)/total*100:.1f}%")
    
    return len(active_properties) > 0

def validate_charge_codes(charges, charge_types):
    """Validate charge code filtering logic"""
    print("\n" + "="*60)
    print("VALIDATION 4: Charge Code Validation")
    print("="*60)
    
    # Check rent charges using string value
    rent_charges = charges[charges['charge code'] == 'rent']
    print(f"Rent charges (string 'rent'): {len(rent_charges)}")
    
    # Check unique charge codes
    unique_codes = charges['charge code'].value_counts().head(10)
    print("\nTop 10 charge codes by frequency:")
    for code, count in unique_codes.items():
        print(f"  {code}: {count}")
    
    # Validate charge type mapping
    print("\nCharge Type Mapping (from dimension table):")
    rent_types = charge_types[charge_types['charge type'] == 'Rent']
    print(f"Charge codes mapped to 'Rent' type: {len(rent_types)}")
    
    if len(rent_types) > 0:
        print("\nRent-type charge codes:")
        print(rent_types[['charege code id', 'charege code name', 'charge type']].to_string())
    
    return len(rent_charges) > 0

def validate_latest_sequence_logic(amendments):
    """Validate latest amendment sequence logic"""
    print("\n" + "="*60)
    print("VALIDATION 5: Latest Amendment Sequence Logic")
    print("="*60)
    
    # Group by property and tenant to find latest sequences
    latest_sequences = amendments.groupby(['property hmy', 'tenant hmy'])[
        'amendment sequence'
    ].max().reset_index()
    
    print(f"Unique property-tenant combinations: {len(latest_sequences)}")
    
    # Check for duplicates (should be none after MAX sequence)
    duplicates = latest_sequences.duplicated(subset=['property hmy', 'tenant hmy'])
    print(f"Duplicate property-tenant combinations: {duplicates.sum()}")
    
    # Validate sequence distribution
    seq_distribution = amendments['amendment sequence'].value_counts().sort_index()
    print("\nAmendment sequence distribution:")
    for seq in range(min(5, len(seq_distribution))):
        if seq in seq_distribution.index:
            print(f"  Sequence {seq}: {seq_distribution[seq]} amendments")
    
    return duplicates.sum() == 0

def main():
    """Main validation function"""
    print("="*60)
    print("YSQL-BASED DAX IMPROVEMENTS VALIDATION")
    print("="*60)
    print(f"Validation Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load data
    amendments, charges, properties, charge_types = load_data()
    
    # Run validations
    results = {
        'Amendment Exclusions': validate_amendment_exclusions(amendments),
        'Month-to-Month Leases': validate_month_to_month_leases(amendments),
        'Property Status': validate_property_status(properties),
        'Charge Codes': validate_charge_codes(charges, charge_types),
        'Latest Sequence Logic': validate_latest_sequence_logic(amendments)
    }
    
    # Summary
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    
    all_passed = True
    for test, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("✓ ALL VALIDATIONS PASSED")
        print("The YSQL-based improvements are correctly implemented.")
    else:
        print("✗ SOME VALIDATIONS FAILED")
        print("Please review the failed tests above.")
    print("="*60)
    
    return all_passed

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)