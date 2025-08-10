#!/usr/bin/env python3
"""
Missing Charges Deep Analysis
=============================
Detailed analysis of amendments missing rent charges
and their impact on rent roll accuracy.
"""

import pandas as pd
import numpy as np
from pathlib import Path

def analyze_missing_charges():
    """Detailed analysis of amendments missing rent charges"""
    
    data_path = Path("/Users/michaeltang/Documents/GitHub/BI/PBI v1.7/Data/Yardi_Tables")
    
    print("🔍 Loading data for missing charges analysis...")
    
    try:
        amendments = pd.read_csv(data_path / "dim_fp_amendmentsunitspropertytenant.csv")
        charges = pd.read_csv(data_path / "dim_fp_amendmentchargeschedule.csv")
        properties = pd.read_csv(data_path / "dim_property.csv")
        
        # Normalize column names
        amendments.columns = amendments.columns.str.lower().str.strip()
        charges.columns = charges.columns.str.lower().str.strip()
        properties.columns = properties.columns.str.lower().str.strip()
        
        print(f"✅ Data loaded successfully")
        print(f"   - amendments: {len(amendments):,} records")
        print(f"   - charges: {len(charges):,} records")
        print(f"   - properties: {len(properties):,} records")
        
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return
    
    # Filter to active amendments
    active_amendments = amendments[amendments['amendment status'].isin(['Activated', 'Superseded'])]
    print(f"\n📊 Active amendments: {len(active_amendments):,}")
    
    # Find amendments with and without charges
    amendments_with_charges = active_amendments[
        active_amendments['amendment hmy'].isin(charges['amendment hmy'])
    ]
    amendments_without_charges = active_amendments[
        ~active_amendments['amendment hmy'].isin(charges['amendment hmy'])
    ]
    
    missing_pct = len(amendments_without_charges) / len(active_amendments) * 100
    
    print(f"\n🚨 MISSING CHARGES ANALYSIS:")
    print(f"   Total active amendments: {len(active_amendments):,}")
    print(f"   Amendments with charges: {len(amendments_with_charges):,}")
    print(f"   Amendments WITHOUT charges: {len(amendments_without_charges):,} ({missing_pct:.2f}%)")
    
    # Analyze missing charges by property
    print(f"\n🏢 MISSING CHARGES BY PROPERTY:")
    
    # Merge with properties for property names
    missing_with_props = amendments_without_charges.merge(
        properties[['property hmy', 'property code', 'property name']], 
        on='property hmy', 
        how='left'
    )
    
    prop_missing_summary = missing_with_props.groupby(['property hmy', 'property code', 'property name']).agg({
        'amendment hmy': 'count'
    }).reset_index()
    prop_missing_summary.columns = ['property_hmy', 'property_code', 'property_name', 'missing_charges_count']
    prop_missing_summary = prop_missing_summary.sort_values('missing_charges_count', ascending=False)
    
    print(f"   Properties with missing charges: {len(prop_missing_summary):,}")
    print(f"   Top 15 properties with most missing charges:")
    
    for _, row in prop_missing_summary.head(15).iterrows():
        prop_name = row['property_name'] if pd.notna(row['property_name']) else 'Unknown'
        print(f"      {row['property_code']}: {row['missing_charges_count']:,} missing charges ({prop_name[:40]}...)")
    
    # Analyze by amendment status
    print(f"\n📋 MISSING CHARGES BY AMENDMENT STATUS:")
    status_missing = amendments_without_charges['amendment status'].value_counts()
    for status, count in status_missing.items():
        status_pct = count / len(amendments_without_charges) * 100
        print(f"   {status}: {count:,} ({status_pct:.1f}%)")
    
    # Analyze amendment sequences for missing charges
    print(f"\n🔢 AMENDMENT SEQUENCE ANALYSIS:")
    
    # Get latest sequences per property/tenant
    latest_sequences = active_amendments.groupby(['property hmy', 'tenant hmy'])['amendment sequence'].max().reset_index()
    
    # Check how many latest amendments are missing charges
    latest_amendments = active_amendments.merge(
        latest_sequences, 
        on=['property hmy', 'tenant hmy', 'amendment sequence']
    )
    
    latest_missing_charges = latest_amendments[
        ~latest_amendments['amendment hmy'].isin(charges['amendment hmy'])
    ]
    
    latest_missing_pct = len(latest_missing_charges) / len(latest_amendments) * 100
    
    print(f"   Total latest amendments: {len(latest_amendments):,}")
    print(f"   Latest amendments missing charges: {len(latest_missing_charges):,} ({latest_missing_pct:.2f}%)")
    print(f"   🚨 This affects current rent roll accuracy!")
    
    # Date range analysis
    if 'lease expiration date' in amendments_without_charges.columns:
        print(f"\n📅 LEASE EXPIRATION ANALYSIS FOR MISSING CHARGES:")
        
        # Convert expiration dates
        missing_with_props_copy = missing_with_props.copy()
        missing_with_props_copy['lease expiration date'] = pd.to_datetime(
            missing_with_props_copy['lease expiration date'], 
            errors='coerce'
        )
        
        # Group by expiration year
        expiry_analysis = missing_with_props_copy.dropna(subset=['lease expiration date']).groupby(
            missing_with_props_copy['lease expiration date'].dt.year
        ).size()
        
        print(f"   Missing charges by lease expiration year:")
        for year, count in expiry_analysis.items():
            print(f"      {year}: {count:,} amendments")
    
    # Charge type analysis for existing charges
    print(f"\n💰 EXISTING CHARGES ANALYSIS:")
    
    if 'charge code' in charges.columns:
        charge_types = charges['charge code'].value_counts().head(10)
        print(f"   Total charge records: {len(charges):,}")
        print(f"   Top 10 charge types:")
        for charge_code, count in charge_types.items():
            print(f"      {charge_code}: {count:,} records")
    
    # Monthly amount analysis
    if 'monthly amount' in charges.columns:
        monthly_amounts = charges['monthly amount'].describe()
        print(f"\n   Monthly charge amounts statistics:")
        print(f"      Count: {monthly_amounts['count']:,.0f}")
        print(f"      Mean: ${monthly_amounts['mean']:,.2f}")
        print(f"      Median: ${monthly_amounts['50%']:,.2f}")
        print(f"      Max: ${monthly_amounts['max']:,.2f}")
        print(f"      Min: ${monthly_amounts['min']:,.2f}")
        
        total_monthly_rent = charges['monthly amount'].sum()
        print(f"      Total monthly rent: ${total_monthly_rent:,.2f}")
    
    # Sample missing amendments
    print(f"\n📝 SAMPLE AMENDMENTS WITHOUT CHARGES (First 10):")
    sample_columns = ['amendment hmy', 'property hmy', 'tenant hmy', 'amendment status', 'amendment sequence']
    sample_missing = amendments_without_charges[sample_columns].head(10)
    print(sample_missing.to_string(index=False))
    
    # Cross-reference with other tables
    print(f"\n🔍 CROSS-TABLE VALIDATION:")
    
    missing_amendment_hmys = set(amendments_without_charges['amendment hmy'].unique())
    
    # Check if these amendments exist in other charge-related tables
    other_tables = ['dim_fp_chargecodetypeandgl']
    
    for table_name in other_tables:
        table_path = data_path / f"{table_name}.csv"
        if table_path.exists():
            try:
                table_df = pd.read_csv(table_path)
                print(f"   {table_name}: {len(table_df):,} records (reference table)")
            except Exception as e:
                print(f"   {table_name}: Error reading - {e}")
    
    # Impact assessment
    print(f"\n📈 BUSINESS IMPACT ASSESSMENT:")
    
    # Estimate rental income impact
    if 'monthly amount' in charges.columns and len(charges) > 0:
        avg_monthly_rent = charges['monthly amount'].mean()
        estimated_missing_monthly_rent = len(amendments_without_charges) * avg_monthly_rent
        estimated_annual_impact = estimated_missing_monthly_rent * 12
        
        print(f"   Average monthly rent per charge: ${avg_monthly_rent:,.2f}")
        print(f"   Estimated missing monthly rent: ${estimated_missing_monthly_rent:,.2f}")
        print(f"   Estimated annual revenue impact: ${estimated_annual_impact:,.2f}")
    
    # Rent roll accuracy impact
    rent_roll_accuracy = len(amendments_with_charges) / len(active_amendments) * 100
    print(f"   Current rent roll accuracy: {rent_roll_accuracy:.2f}%")
    print(f"   Target accuracy (95%): {'✅ ACHIEVED' if rent_roll_accuracy >= 95 else '❌ NOT MET'}")
    
    # Recommendations
    print(f"\n✅ REMEDIATION RECOMMENDATIONS:")
    print(f"   1. IMMEDIATE: Investigate top {min(10, len(prop_missing_summary))} properties with missing charges")
    print(f"   2. HIGH PRIORITY: Fix {len(latest_missing_charges):,} latest amendments missing charges")
    print(f"   3. DATA VALIDATION: Ensure charge creation process works with amendment creation")
    print(f"   4. ETL PROCESS: Add validation to prevent amendments without charges")
    
    if missing_pct > 20:
        print(f"   5. CRITICAL: High percentage ({missing_pct:.2f}%) affects rent roll reliability")
    
    if latest_missing_pct > 10:
        print(f"   6. URGENT: {latest_missing_pct:.2f}% of current leases missing charges")
    
    # Generate remediation queries
    print(f"\n📝 REMEDIATION APPROACH:")
    print(f"```sql")
    print(f"-- Identify amendments without charges")
    print(f"SELECT a.[amendment hmy], a.[property hmy], a.[tenant hmy], ")
    print(f"       a.[amendment status], a.[amendment sequence]")
    print(f"FROM dim_fp_amendmentsunitspropertytenant a")
    print(f"LEFT JOIN dim_fp_amendmentchargeschedule c ON a.[amendment hmy] = c.[amendment hmy]")
    print(f"WHERE a.[amendment status] IN ('Activated', 'Superseded')")
    print(f"  AND c.[amendment hmy] IS NULL;")
    print(f"")
    print(f"-- Expected results: {len(amendments_without_charges):,} records")
    print(f"```")

if __name__ == "__main__":
    analyze_missing_charges()