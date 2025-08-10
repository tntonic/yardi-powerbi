#!/usr/bin/env python3
"""
Compare June 1, 2025 vs June 30, 2025 Rent Rolls
Analyze changes in the portfolio over the month
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime

def load_rent_rolls():
    """Load both June rent rolls"""
    base_path = "/Users/michaeltang/Documents/GitHub/BI/PBI v1.7/Generated_Rent_Rolls"
    
    # Load June 1
    june1_file = os.path.join(base_path, "fund2_rent_roll_generated_060125.csv")
    june1_df = pd.read_csv(june1_file)
    
    # Load June 30
    june30_file = os.path.join(base_path, "fund2_rent_roll_generated_063025.csv")
    june30_df = pd.read_csv(june30_file)
    
    print("DATA LOADED:")
    print(f"  June 1, 2025: {len(june1_df)} records")
    print(f"  June 30, 2025: {len(june30_df)} records")
    
    return june1_df, june30_df

def compare_totals(june1_df, june30_df):
    """Compare high-level metrics"""
    print("\n" + "=" * 80)
    print("HIGH-LEVEL METRICS COMPARISON")
    print("=" * 80)
    
    metrics = {
        'Record Count': {
            'June 1': len(june1_df),
            'June 30': len(june30_df),
            'Change': len(june30_df) - len(june1_df)
        },
        'Total Properties': {
            'June 1': june1_df['property_code'].nunique(),
            'June 30': june30_df['property_code'].nunique(),
            'Change': june30_df['property_code'].nunique() - june1_df['property_code'].nunique()
        },
        'Monthly Rent': {
            'June 1': june1_df['monthly_rent'].sum(),
            'June 30': june30_df['monthly_rent'].sum(),
            'Change': june30_df['monthly_rent'].sum() - june1_df['monthly_rent'].sum()
        },
        'Annual Rent': {
            'June 1': june1_df['annual_rent'].sum(),
            'June 30': june30_df['annual_rent'].sum(),
            'Change': june30_df['annual_rent'].sum() - june1_df['annual_rent'].sum()
        },
        'Square Feet': {
            'June 1': june1_df['square_feet'].sum(),
            'June 30': june30_df['square_feet'].sum(),
            'Change': june30_df['square_feet'].sum() - june1_df['square_feet'].sum()
        }
    }
    
    # Print comparison table
    print(f"\n{'Metric':<20} {'June 1, 2025':>15} {'June 30, 2025':>15} {'Change':>15} {'% Change':>10}")
    print("-" * 80)
    
    for metric_name, values in metrics.items():
        june1_val = values['June 1']
        june30_val = values['June 30']
        change = values['Change']
        pct_change = (change / june1_val * 100) if june1_val > 0 else 0
        
        if 'Rent' in metric_name:
            print(f"{metric_name:<20} ${june1_val:>14,.2f} ${june30_val:>14,.2f} ${change:>14,.2f} {pct_change:>9.1f}%")
        elif metric_name in ['Record Count', 'Total Properties']:
            print(f"{metric_name:<20} {june1_val:>15,} {june30_val:>15,} {change:>15,} {pct_change:>9.1f}%")
        else:
            print(f"{metric_name:<20} {june1_val:>15,.0f} {june30_val:>15,.0f} {change:>15,.0f} {pct_change:>9.1f}%")
    
    return metrics

def analyze_lease_activity(june1_df, june30_df):
    """Analyze lease activity between June 1 and June 30"""
    print("\n" + "=" * 80)
    print("LEASE ACTIVITY ANALYSIS")
    print("=" * 80)
    
    # Create unique identifiers for matching
    june1_df['lease_id'] = june1_df['property_code'].astype(str) + '_' + june1_df['tenant_id'].astype(str)
    june30_df['lease_id'] = june30_df['property_code'].astype(str) + '_' + june30_df['tenant_id'].astype(str)
    
    june1_leases = set(june1_df['lease_id'])
    june30_leases = set(june30_df['lease_id'])
    
    # Identify changes
    new_leases = june30_leases - june1_leases
    terminated_leases = june1_leases - june30_leases
    continuing_leases = june1_leases & june30_leases
    
    print(f"\nLease Movement:")
    print(f"  Continuing Leases: {len(continuing_leases)}")
    print(f"  New Leases: {len(new_leases)}")
    print(f"  Terminated Leases: {len(terminated_leases)}")
    print(f"  Net Change: {len(new_leases) - len(terminated_leases)}")
    
    # Analyze new leases
    if new_leases:
        new_lease_df = june30_df[june30_df['lease_id'].isin(new_leases)]
        print(f"\nNew Leases Details:")
        print(f"  Total Square Feet: {new_lease_df['square_feet'].sum():,.0f}")
        print(f"  Total Monthly Rent: ${new_lease_df['monthly_rent'].sum():,.2f}")
        print(f"  Average Rent PSF: ${new_lease_df[new_lease_df['rent_psf'] > 0]['rent_psf'].mean():.2f}")
        
        # Top 5 new leases by rent
        top_new = new_lease_df.nlargest(5, 'monthly_rent')[['property_code', 'tenant_id', 'square_feet', 'monthly_rent']]
        print(f"\n  Top 5 New Leases by Monthly Rent:")
        for idx, row in top_new.iterrows():
            print(f"    {row['property_code']} - {row['tenant_id']}: {row['square_feet']:,.0f} SF @ ${row['monthly_rent']:,.2f}/mo")
    
    # Analyze terminated leases
    if terminated_leases:
        terminated_lease_df = june1_df[june1_df['lease_id'].isin(terminated_leases)]
        print(f"\nTerminated Leases Details:")
        print(f"  Total Square Feet: {terminated_lease_df['square_feet'].sum():,.0f}")
        print(f"  Total Monthly Rent Lost: ${terminated_lease_df['monthly_rent'].sum():,.2f}")
        print(f"  Average Rent PSF: ${terminated_lease_df[terminated_lease_df['rent_psf'] > 0]['rent_psf'].mean():.2f}")
        
        # Top 5 terminated leases by rent
        top_terminated = terminated_lease_df.nlargest(5, 'monthly_rent')[['property_code', 'tenant_id', 'square_feet', 'monthly_rent']]
        print(f"\n  Top 5 Terminated Leases by Monthly Rent:")
        for idx, row in top_terminated.iterrows():
            print(f"    {row['property_code']} - {row['tenant_id']}: {row['square_feet']:,.0f} SF @ ${row['monthly_rent']:,.2f}/mo")
    
    return new_leases, terminated_leases, continuing_leases

def analyze_rent_changes(june1_df, june30_df):
    """Analyze rent changes for continuing leases"""
    print("\n" + "=" * 80)
    print("RENT CHANGES FOR CONTINUING LEASES")
    print("=" * 80)
    
    # Create unique identifiers
    june1_df['lease_id'] = june1_df['property_code'].astype(str) + '_' + june1_df['tenant_id'].astype(str)
    june30_df['lease_id'] = june30_df['property_code'].astype(str) + '_' + june30_df['tenant_id'].astype(str)
    
    # Get continuing leases
    continuing_leases = set(june1_df['lease_id']) & set(june30_df['lease_id'])
    
    if continuing_leases:
        # Prepare data for comparison
        june1_cont = june1_df[june1_df['lease_id'].isin(continuing_leases)].set_index('lease_id')
        june30_cont = june30_df[june30_df['lease_id'].isin(continuing_leases)].set_index('lease_id')
        
        # Calculate rent changes
        rent_changes = []
        for lease_id in continuing_leases:
            june1_rent = june1_cont.loc[lease_id, 'monthly_rent']
            june30_rent = june30_cont.loc[lease_id, 'monthly_rent']
            
            if june1_rent != june30_rent:
                rent_changes.append({
                    'lease_id': lease_id,
                    'property_code': june1_cont.loc[lease_id, 'property_code'],
                    'tenant_id': june1_cont.loc[lease_id, 'tenant_id'],
                    'june1_rent': june1_rent,
                    'june30_rent': june30_rent,
                    'change': june30_rent - june1_rent,
                    'pct_change': ((june30_rent - june1_rent) / june1_rent * 100) if june1_rent > 0 else 0
                })
        
        if rent_changes:
            changes_df = pd.DataFrame(rent_changes)
            
            print(f"\nRent Changes Summary:")
            print(f"  Leases with rent changes: {len(changes_df)}")
            print(f"  Leases with no change: {len(continuing_leases) - len(changes_df)}")
            
            increases = changes_df[changes_df['change'] > 0]
            decreases = changes_df[changes_df['change'] < 0]
            
            if len(increases) > 0:
                print(f"\n  Rent Increases: {len(increases)}")
                print(f"    Total increase: ${increases['change'].sum():,.2f}")
                print(f"    Average increase: ${increases['change'].mean():,.2f}")
                print(f"    Average % increase: {increases['pct_change'].mean():.1f}%")
            
            if len(decreases) > 0:
                print(f"\n  Rent Decreases: {len(decreases)}")
                print(f"    Total decrease: ${decreases['change'].sum():,.2f}")
                print(f"    Average decrease: ${decreases['change'].mean():,.2f}")
                print(f"    Average % decrease: {decreases['pct_change'].mean():.1f}%")
            
            # Show top 5 changes
            if len(changes_df) > 0:
                print(f"\n  Top 5 Rent Changes (by $ amount):")
                top_changes = changes_df.nlargest(5, 'change', keep='all')[['property_code', 'tenant_id', 'june1_rent', 'june30_rent', 'change', 'pct_change']]
                for idx, row in top_changes.iterrows():
                    print(f"    {row['property_code']} - {row['tenant_id']}: ${row['june1_rent']:,.2f} → ${row['june30_rent']:,.2f} (${row['change']:+,.2f}, {row['pct_change']:+.1f}%)")
        else:
            print(f"\n  No rent changes detected for continuing leases")

def analyze_property_performance(june1_df, june30_df):
    """Analyze performance by property"""
    print("\n" + "=" * 80)
    print("PROPERTY-LEVEL PERFORMANCE")
    print("=" * 80)
    
    # Aggregate by property
    june1_by_prop = june1_df.groupby('property_code').agg({
        'tenant_id': 'count',
        'square_feet': 'sum',
        'monthly_rent': 'sum'
    }).rename(columns={'tenant_id': 'tenant_count'})
    
    june30_by_prop = june30_df.groupby('property_code').agg({
        'tenant_id': 'count',
        'square_feet': 'sum',
        'monthly_rent': 'sum'
    }).rename(columns={'tenant_id': 'tenant_count'})
    
    # Calculate changes
    all_properties = set(june1_by_prop.index) | set(june30_by_prop.index)
    
    property_changes = []
    for prop in all_properties:
        june1_data = june1_by_prop.loc[prop] if prop in june1_by_prop.index else pd.Series({'tenant_count': 0, 'square_feet': 0, 'monthly_rent': 0})
        june30_data = june30_by_prop.loc[prop] if prop in june30_by_prop.index else pd.Series({'tenant_count': 0, 'square_feet': 0, 'monthly_rent': 0})
        
        property_changes.append({
            'property_code': prop,
            'tenant_change': june30_data['tenant_count'] - june1_data['tenant_count'],
            'sf_change': june30_data['square_feet'] - june1_data['square_feet'],
            'rent_change': june30_data['monthly_rent'] - june1_data['monthly_rent']
        })
    
    changes_df = pd.DataFrame(property_changes)
    
    # Show properties with biggest changes
    print(f"\nProperties with Biggest Gains (by monthly rent):")
    top_gains = changes_df.nlargest(5, 'rent_change')
    for idx, row in top_gains.iterrows():
        if row['rent_change'] > 0:
            print(f"  {row['property_code']}: +${row['rent_change']:,.2f} rent, {row['tenant_change']:+d} tenants, {row['sf_change']:+,.0f} SF")
    
    print(f"\nProperties with Biggest Losses (by monthly rent):")
    top_losses = changes_df.nsmallest(5, 'rent_change')
    for idx, row in top_losses.iterrows():
        if row['rent_change'] < 0:
            print(f"  {row['property_code']}: ${row['rent_change']:,.2f} rent, {row['tenant_change']:+d} tenants, {row['sf_change']:+,.0f} SF")

def main():
    """Main comparison function"""
    print("=" * 80)
    print("JUNE 2025 RENT ROLL COMPARISON")
    print("Comparing June 1, 2025 vs June 30, 2025")
    print("=" * 80)
    
    # Load data
    june1_df, june30_df = load_rent_rolls()
    
    # Run comparisons
    metrics = compare_totals(june1_df, june30_df)
    new_leases, terminated_leases, continuing_leases = analyze_lease_activity(june1_df, june30_df)
    analyze_rent_changes(june1_df, june30_df)
    analyze_property_performance(june1_df, june30_df)
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    print(f"\nKey Findings:")
    print(f"  • Portfolio grew by {metrics['Record Count']['Change']} leases ({metrics['Record Count']['Change']/metrics['Record Count']['June 1']*100:.1f}%)")
    print(f"  • Monthly rent {'increased' if metrics['Monthly Rent']['Change'] > 0 else 'decreased'} by ${abs(metrics['Monthly Rent']['Change']):,.2f}")
    print(f"  • Net leasing activity: {len(new_leases)} new - {len(terminated_leases)} terminated = {len(new_leases) - len(terminated_leases)} net")
    print(f"  • Square footage {'increased' if metrics['Square Feet']['Change'] > 0 else 'decreased'} by {abs(metrics['Square Feet']['Change']):,.0f} SF")
    
    return metrics

if __name__ == "__main__":
    main()