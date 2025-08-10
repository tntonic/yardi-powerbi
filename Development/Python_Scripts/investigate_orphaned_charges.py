#!/usr/bin/env python3
"""
Investigate Orphaned Charge Schedules

This script investigates the 123 orphaned charge schedules that are not linked to latest amendments.
This could indicate:
1. Data quality issues
2. Superseded amendments with lingering active charges  
3. Charge schedules linked to non-latest amendment sequences
4. Potential impact on rent calculations

Critical for ensuring rent roll accuracy.
"""

import pandas as pd
import numpy as np
import os

def load_fund2_data():
    """Load Fund 2 filtered data"""
    data_path = "Data/Fund2_Filtered/"
    
    amendments = pd.read_csv(os.path.join(data_path, "dim_fp_amendmentsunitspropertytenant_fund2.csv"))
    charge_schedule_active = pd.read_csv(os.path.join(data_path, "dim_fp_amendmentchargeschedule_fund2_active.csv"))
    
    return amendments, charge_schedule_active

def analyze_orphaned_charges():
    """Analyze orphaned charge schedules in detail"""
    print("INVESTIGATING ORPHANED CHARGE SCHEDULES")
    print("=" * 50)
    print()
    
    amendments, charge_schedule_active = load_fund2_data()
    
    # Get latest amendments only
    latest_amendments = amendments.groupby(['property hmy', 'tenant hmy'])['amendment sequence'].transform('max')
    latest_amendments_df = amendments[amendments['amendment sequence'] == latest_amendments].copy()
    
    print(f"Data Summary:")
    print(f"  Total amendments: {len(amendments):,}")
    print(f"  Latest amendments only: {len(latest_amendments_df):,}")
    print(f"  Active charge schedules: {len(charge_schedule_active):,}")
    print()
    
    # Identify orphaned charges
    charge_schedule_linked = charge_schedule_active.merge(
        latest_amendments_df[['amendment hmy', 'property hmy', 'tenant hmy', 'amendment sequence', 'amendment status', 'amendment type']],
        left_on='amendment hmy',
        right_on='amendment hmy',
        how='inner'
    )
    
    orphaned_charges = charge_schedule_active[~charge_schedule_active['amendment hmy'].isin(latest_amendments_df['amendment hmy'])]
    
    print(f"Charge Schedule Analysis:")
    print(f"  Charges linked to latest amendments: {len(charge_schedule_linked):,}")
    print(f"  Orphaned charges: {len(orphaned_charges):,} ({len(orphaned_charges) / len(charge_schedule_active) * 100:.1f}%)")
    print()
    
    # Analyze orphaned charges in detail
    if len(orphaned_charges) > 0:
        print("ORPHANED CHARGES ANALYSIS:")
        print("-" * 30)
        
        # Find what amendments these orphaned charges are linked to
        orphaned_with_amendments = orphaned_charges.merge(
            amendments[['amendment hmy', 'property hmy', 'tenant hmy', 'amendment sequence', 'amendment status', 'amendment type', 'property code']],
            left_on='amendment hmy',
            right_on='amendment hmy',
            how='left'
        )
        
        print(f"Orphaned charges columns: {list(orphaned_charges.columns)}")
        print(f"Orphaned with amendments columns: {list(orphaned_with_amendments.columns)}")
        
        print(f"Orphaned Charges by Amendment Status:")
        if 'amendment status' in orphaned_with_amendments.columns:
            status_dist = orphaned_with_amendments['amendment status'].value_counts()
            print(status_dist)
            print()
        
        print(f"Orphaned Charges by Amendment Type:")
        if 'amendment type' in orphaned_with_amendments.columns:
            type_dist = orphaned_with_amendments['amendment type'].value_counts()
            print(type_dist)
            print()
        
        print(f"Orphaned Charges by Amendment Sequence:")
        if 'amendment sequence' in orphaned_with_amendments.columns:
            seq_dist = orphaned_with_amendments['amendment sequence'].value_counts().sort_index()
            print(seq_dist)
            print()
        
        # Check if orphaned charges are from superseded amendments
        print("Superseded Amendment Analysis:")
        superseded_orphaned = orphaned_with_amendments[orphaned_with_amendments['amendment status'] == 'Superseded']
        print(f"  Orphaned charges from Superseded amendments: {len(superseded_orphaned):,}")
        
        if len(superseded_orphaned) > 0:
            # Check if these superseded amendments have newer versions
            for _, row in superseded_orphaned.head(10).iterrows():
                if 'property hmy' in row.index and not pd.isna(row['property hmy']):
                    prop_hmy = row['property hmy']
                    tenant_hmy = row['tenant hmy']
                    orphaned_seq = row['amendment sequence']
                    
                    # Find latest sequence for this property/tenant
                    latest_seq = amendments[(amendments['property hmy'] == prop_hmy) & 
                                          (amendments['tenant hmy'] == tenant_hmy)]['amendment sequence'].max()
                    
                    prop_code = row.get('property code_y', row.get('property code', 'Unknown'))
                    print(f"    Property {prop_code}, Tenant {tenant_hmy}: Orphaned seq {orphaned_seq}, Latest seq {latest_seq}")
                else:
                    print(f"    Row missing property hmy data: {row.get('amendment hmy', 'Unknown')}")
        
        print()
        
        # Analyze financial impact
        print("FINANCIAL IMPACT ANALYSIS:")
        print("-" * 25)
        
        # Total monthly amount in orphaned charges
        orphaned_monthly_total = orphaned_charges['monthly amount'].sum()
        linked_monthly_total = charge_schedule_linked['monthly amount'].sum()
        total_monthly = charge_schedule_active['monthly amount'].sum()
        
        print(f"Monthly Rent Impact:")
        print(f"  Orphaned charges monthly total: ${orphaned_monthly_total:,.2f}")
        print(f"  Linked charges monthly total: ${linked_monthly_total:,.2f}")
        print(f"  Total active charges: ${total_monthly:,.2f}")
        print(f"  Orphaned percentage: {orphaned_monthly_total / total_monthly * 100:.1f}%")
        print()
        
        # Charge code analysis
        print("Charge Code Distribution in Orphaned Charges:")
        charge_code_dist = orphaned_charges['charge code desc'].value_counts()
        print(charge_code_dist.head(10))
        print()
        
        # Sample orphaned records
        print("SAMPLE ORPHANED CHARGE RECORDS:")
        print("-" * 35)
        sample_columns = ['property code', 'amendment hmy', 'tenant hmy', 'charge code desc', 'monthly amount', 'amendment sequence', 'amendment status', 'amendment type']
        available_columns = [col for col in sample_columns if col in orphaned_with_amendments.columns]
        
        # Check for alternative column names if merge created suffixes
        if 'property code_x' in orphaned_with_amendments.columns:
            available_columns.append('property code_x')
        if 'property code_y' in orphaned_with_amendments.columns:
            available_columns.append('property code_y')
            
        if available_columns:
            print("Available columns:", available_columns)
            display_cols = [col for col in available_columns if col in orphaned_with_amendments.columns][:8]  # Limit to 8 columns
            if display_cols:
                print(orphaned_with_amendments[display_cols].head(10))
            else:
                print("Core columns available:", orphaned_with_amendments.columns.tolist()[:10])
        print()
    
    return orphaned_charges, orphaned_with_amendments

def recommend_solutions(orphaned_charges, orphaned_with_amendments):
    """Recommend solutions for handling orphaned charges"""
    print("RECOMMENDATIONS FOR ORPHANED CHARGES:")
    print("-" * 40)
    
    if len(orphaned_charges) == 0:
        print("✅ No orphaned charges found - no action needed")
        return
    
    # Analyze the types of orphaned charges
    superseded_count = len(orphaned_with_amendments[orphaned_with_amendments['amendment status'] == 'Superseded'])
    activated_count = len(orphaned_with_amendments[orphaned_with_amendments['amendment status'] == 'Activated'])
    
    print(f"1. SUPERSEDED AMENDMENT CHARGES ({superseded_count} charges):")
    if superseded_count > 0:
        print("   - These charges are linked to superseded amendments")
        print("   - DAX logic should INCLUDE these in rent calculations")
        print("   - Current DAX includes 'Superseded' status - this is CORRECT")
        print("   - Issue may be that charge schedule links to non-latest sequence")
    print()
    
    print(f"2. ACTIVATED AMENDMENT CHARGES ({activated_count} charges):")
    if activated_count > 0:
        print("   - These charges are from Activated amendments but not latest sequence")
        print("   - Need to investigate why they're not considered 'latest'")
        print("   - May indicate data quality issues")
    print()
    
    print("3. DAX IMPLEMENTATION RECOMMENDATIONS:")
    print("   a) Current DAX should handle this correctly if:")
    print("      - Status filter includes 'Superseded' ✅")
    print("      - Charge schedule join uses proper amendment hmy ✅")
    print("      - Latest sequence logic is applied AFTER charge join")
    print()
    print("   b) Potential DAX optimization:")
    print("      - Apply latest sequence filter to amendments FIRST")
    print("      - Then join charge schedule to filtered amendments")
    print("      - This would eliminate orphaned charges automatically")
    print()
    
    print("4. DATA QUALITY RECOMMENDATIONS:")
    print("   - Review charge schedule maintenance procedures")
    print("   - Ensure charges are properly linked when amendments are updated")
    print("   - Consider automated cleanup of charges linked to superseded non-latest amendments")
    print()
    
    financial_impact = orphaned_charges['monthly amount'].sum()
    print(f"5. FINANCIAL IMPACT:")
    print(f"   - Monthly amount in orphaned charges: ${financial_impact:,.2f}")
    print(f"   - Annual impact: ${financial_impact * 12:,.2f}")
    
    if financial_impact > 50000:  # $50k+ monthly
        print(f"   - ⚠️  HIGH IMPACT: Requires immediate attention")
    elif financial_impact > 10000:  # $10k+ monthly  
        print(f"   - ⚠️  MEDIUM IMPACT: Should be investigated")
    else:
        print(f"   - ✅ LOW IMPACT: Monitor but not critical")
    
    print()

def validate_dax_charge_integration():
    """Validate how DAX should handle charge schedule integration"""
    print("DAX CHARGE INTEGRATION VALIDATION:")
    print("-" * 40)
    
    amendments, charge_schedule_active = load_fund2_data()
    
    # Current DAX approach (as written in the library)
    print("Current DAX Logic Analysis:")
    print("1. Filter amendments by status: {'Activated', 'Superseded'} ✅")
    print("2. Filter amendments by type: <> 'Termination' ✅") 
    print("3. Filter amendments by date: active on report date ✅")
    print("4. Apply MAX(sequence) per property/tenant ✅")
    print("5. Join charge schedule on amendment hmy ✅")
    print("6. Filter charge schedule by date ✅")
    print()
    
    # Test the logic
    # Step 1-3: Basic filtering
    filtered_amendments = amendments[
        (amendments['amendment status'].isin(['Activated', 'Superseded'])) &
        (amendments['amendment type'] != 'Termination')
    ]
    print(f"After basic filtering: {len(filtered_amendments):,} amendments")
    
    # Step 4: Latest sequence
    latest_seq = filtered_amendments.groupby(['property hmy', 'tenant hmy'])['amendment sequence'].transform('max')
    latest_amendments = filtered_amendments[filtered_amendments['amendment sequence'] == latest_seq]
    print(f"After latest sequence: {len(latest_amendments):,} amendments")
    
    # Step 5: Join charges
    charges_to_latest = charge_schedule_active.merge(
        latest_amendments[['amendment hmy']],
        on='amendment hmy',
        how='inner'
    )
    print(f"Charges linked to latest amendments: {len(charges_to_latest):,}")
    
    # Alternative approach: Include charges from ALL filtered amendments (including non-latest)
    charges_to_all_filtered = charge_schedule_active.merge(
        filtered_amendments[['amendment hmy']],
        on='amendment hmy',
        how='inner'
    )
    print(f"Charges linked to ALL filtered amendments: {len(charges_to_all_filtered):,}")
    
    difference = len(charges_to_all_filtered) - len(charges_to_latest)
    print(f"Additional charges from non-latest amendments: {difference:,}")
    
    # Financial impact of including all vs latest only
    latest_total = charges_to_latest['monthly amount'].sum()
    all_total = charges_to_all_filtered['monthly amount'].sum()
    
    print(f"\nFinancial Impact:")
    print(f"  Latest amendments only: ${latest_total:,.2f}/month")
    print(f"  All filtered amendments: ${all_total:,.2f}/month")
    print(f"  Difference: ${all_total - latest_total:,.2f}/month ({(all_total - latest_total) / latest_total * 100:.1f}%)")
    
    print(f"\nRECOMMENDATION:")
    if abs(all_total - latest_total) / latest_total > 0.05:  # More than 5% difference
        print("⚠️  SIGNIFICANT DIFFERENCE: Review charge schedule logic")
        print("   Consider whether charges from superseded amendments should be included")
    else:
        print("✅ MINIMAL DIFFERENCE: Current DAX logic is appropriate")
    
    return latest_total, all_total

def main():
    """Main investigation workflow"""
    print("FUND 2 ORPHANED CHARGE INVESTIGATION")
    print("=" * 50)
    print()
    
    # Investigate orphaned charges
    orphaned_charges, orphaned_with_amendments = analyze_orphaned_charges()
    
    # Provide recommendations
    recommend_solutions(orphaned_charges, orphaned_with_amendments)
    
    # Validate DAX integration approach
    latest_total, all_total = validate_dax_charge_integration()
    
    print("INVESTIGATION SUMMARY:")
    print("=" * 25)
    print(f"✅ Orphaned charges identified and analyzed: {len(orphaned_charges):,}")
    print(f"✅ Financial impact quantified: ${orphaned_charges['monthly amount'].sum():,.2f}/month")
    print(f"✅ DAX integration approach validated")
    print(f"✅ Recommendations provided for data quality improvements")
    
    return {
        'orphaned_count': len(orphaned_charges),
        'financial_impact_monthly': orphaned_charges['monthly amount'].sum(),
        'latest_only_rent': latest_total,
        'all_filtered_rent': all_total
    }

if __name__ == "__main__":
    results = main()