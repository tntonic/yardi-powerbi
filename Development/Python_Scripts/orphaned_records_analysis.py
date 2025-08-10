#!/usr/bin/env python3
"""
Orphaned Records Deep Analysis
==============================
Detailed analysis of orphaned records in fact_total table
and their impact on financial reporting accuracy.
"""

import pandas as pd
import numpy as np
from pathlib import Path

def analyze_orphaned_records():
    """Detailed analysis of orphaned records in fact_total"""
    
    data_path = Path("/Users/michaeltang/Documents/GitHub/BI/PBI v1.7/Data/Yardi_Tables")
    
    # Load required tables
    print("🔍 Loading data for orphaned records analysis...")
    
    try:
        fact_total = pd.read_csv(data_path / "fact_total.csv")
        dim_property = pd.read_csv(data_path / "dim_property.csv")
        dim_account = pd.read_csv(data_path / "dim_account.csv")
        
        # Normalize column names
        fact_total.columns = fact_total.columns.str.lower().str.strip()
        dim_property.columns = dim_property.columns.str.lower().str.strip()
        dim_account.columns = dim_account.columns.str.lower().str.strip()
        
        print(f"✅ Data loaded successfully")
        print(f"   - fact_total: {len(fact_total):,} records")
        print(f"   - dim_property: {len(dim_property):,} records") 
        print(f"   - dim_account: {len(dim_account):,} records")
        
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return
    
    # Identify orphaned records
    print(f"\n📊 Identifying orphaned records...")
    
    # Property orphans
    property_orphans = fact_total[~fact_total['property id'].isin(dim_property['property id'])]
    valid_records = fact_total[fact_total['property id'].isin(dim_property['property id'])]
    
    orphan_pct = len(property_orphans) / len(fact_total) * 100
    
    print(f"🚨 ORPHANED RECORDS ANALYSIS:")
    print(f"   Total fact_total records: {len(fact_total):,}")
    print(f"   Orphaned records: {len(property_orphans):,} ({orphan_pct:.2f}%)")
    print(f"   Valid records: {len(valid_records):,} ({100-orphan_pct:.2f}%)")
    
    # Analyze orphaned property IDs
    print(f"\n📋 ORPHANED PROPERTY ID ANALYSIS:")
    orphan_properties = property_orphans['property id'].value_counts().head(20)
    print(f"   Unique orphaned property IDs: {property_orphans['property id'].nunique():,}")
    print(f"   Top 20 orphaned properties by record count:")
    for prop_id, count in orphan_properties.items():
        print(f"      Property ID {prop_id}: {count:,} records")
    
    # Financial impact analysis
    print(f"\n💰 FINANCIAL IMPACT ANALYSIS:")
    
    # Total amounts
    total_amount = fact_total['amount'].sum()
    orphaned_amount = property_orphans['amount'].sum()
    valid_amount = valid_records['amount'].sum()
    
    orphan_amount_pct = abs(orphaned_amount) / abs(total_amount) * 100
    
    print(f"   Total transaction amount: ${total_amount:,.2f}")
    print(f"   Orphaned amount: ${orphaned_amount:,.2f} ({orphan_amount_pct:.2f}%)")
    print(f"   Valid amount: ${valid_amount:,.2f}")
    
    # Account type breakdown
    if 'account id' in fact_total.columns and not dim_account.empty:
        print(f"\n📈 ORPHANED RECORDS BY ACCOUNT TYPE:")
        
        # Merge with accounts to get account info
        orphan_with_accounts = property_orphans.merge(
            dim_account[['account id', 'account code', 'account name']], 
            on='account id', 
            how='left'
        )
        
        # Group by account code (first digit indicates type)
        orphan_with_accounts['account_type'] = orphan_with_accounts['account code'].str[:1]
        account_type_summary = orphan_with_accounts.groupby('account_type').agg({
            'amount': ['sum', 'count']
        }).round(2)
        
        account_type_summary.columns = ['total_amount', 'record_count']
        account_type_summary = account_type_summary.reset_index()
        
        # Add account type descriptions
        account_types = {
            '1': 'Assets', '2': 'Liabilities', '3': 'Equity',
            '4': 'Revenue', '5': 'Expenses', '6': 'Other'
        }
        
        account_type_summary['description'] = account_type_summary['account_type'].map(account_types)
        
        for _, row in account_type_summary.iterrows():
            type_desc = row['description'] or 'Unknown'
            print(f"   {row['account_type']}xxx ({type_desc}): ${row['total_amount']:,.2f} ({row['record_count']:,} records)")
    
    # Date range analysis
    if 'month' in fact_total.columns:
        print(f"\n📅 ORPHANED RECORDS BY TIME PERIOD:")
        
        # Convert month column to datetime
        property_orphans_dated = property_orphans.copy()
        property_orphans_dated['month'] = pd.to_datetime(property_orphans_dated['month'])
        
        # Group by year
        orphan_by_year = property_orphans_dated.groupby(
            property_orphans_dated['month'].dt.year
        ).agg({
            'amount': ['sum', 'count']
        }).round(2)
        
        orphan_by_year.columns = ['total_amount', 'record_count']
        
        print(f"   Orphaned records by year:")
        for year, row in orphan_by_year.iterrows():
            print(f"      {year}: ${row['total_amount']:,.2f} ({row['record_count']:,} records)")
    
    # Sample orphaned records
    print(f"\n📝 SAMPLE ORPHANED RECORDS (First 10):")
    sample_columns = ['property id', 'account id', 'month', 'amount']
    available_columns = [col for col in sample_columns if col in property_orphans.columns]
    
    sample_orphans = property_orphans[available_columns].head(10)
    print(sample_orphans.to_string(index=False))
    
    # Validation - check if these property IDs exist in other tables
    print(f"\n🔍 CROSS-TABLE VALIDATION:")
    
    orphaned_prop_ids = set(property_orphans['property id'].unique())
    
    # Check other tables for these property IDs
    other_tables = ['dim_unit', 'fact_occupancyrentarea', 'dim_fp_amendmentsunitspropertytenant']
    
    for table_name in other_tables:
        table_path = data_path / f"{table_name}.csv"
        if table_path.exists():
            try:
                table_df = pd.read_csv(table_path)
                table_df.columns = table_df.columns.str.lower().str.strip()
                
                # Find property ID column
                prop_col = None
                for col in ['property id', 'property hmy', 'property_id']:
                    if col in table_df.columns:
                        prop_col = col
                        break
                
                if prop_col:
                    table_prop_ids = set(table_df[prop_col].unique())
                    orphan_intersection = orphaned_prop_ids.intersection(table_prop_ids)
                    
                    if orphan_intersection:
                        print(f"   {table_name}: {len(orphan_intersection):,} orphaned property IDs found")
                    else:
                        print(f"   {table_name}: No orphaned property IDs found")
                else:
                    print(f"   {table_name}: No property ID column found")
                    
            except Exception as e:
                print(f"   {table_name}: Error reading file - {e}")
    
    # Recommendations
    print(f"\n✅ REMEDIATION RECOMMENDATIONS:")
    print(f"   1. IMMEDIATE: Remove {len(property_orphans):,} orphaned records")
    print(f"   2. INVESTIGATE: Why these {property_orphans['property id'].nunique():,} property IDs are missing from dim_property")
    print(f"   3. ETL FIX: Ensure fact_total extraction only includes active properties")
    print(f"   4. VALIDATION: Add referential integrity checks to ETL process")
    
    if orphan_amount_pct > 5:
        print(f"   5. PRIORITY: High financial impact ({orphan_amount_pct:.2f}%) - address immediately")
    
    # Generate cleanup query
    print(f"\n📝 CLEANUP SQL QUERY:")
    print(f"```sql")
    print(f"-- Remove orphaned records from fact_total")
    print(f"DELETE FROM fact_total ")
    print(f"WHERE [property id] NOT IN (")
    print(f"    SELECT [property id] FROM dim_property")
    print(f");")
    print(f"")
    print(f"-- Expected to remove: {len(property_orphans):,} records")
    print(f"-- Financial impact: ${orphaned_amount:,.2f}")
    print(f"```")

if __name__ == "__main__":
    analyze_orphaned_records()