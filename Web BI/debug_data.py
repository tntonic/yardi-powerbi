#!/usr/bin/env python3
"""
Debug data availability
"""

import duckdb
import pandas as pd

def get_db_connection():
    """Get database connection"""
    db_path = '/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Web BI/yardi_dashboard.db'
    return duckdb.connect(db_path)

def debug_queries(conn):
    """Run debug queries to understand the data"""
    
    print("\n" + "="*60)
    print("DATA DEBUGGING")
    print("="*60)
    
    # 1. Check financial data
    print("\n1. Financial Data Check:")
    try:
        df = conn.execute("""
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT "property id") as properties,
                MIN(month) as min_month,
                MAX(month) as max_month,
                SUM(amount) as total_amount
            FROM fact_total
        """).fetchdf()
        print(df)
    except Exception as e:
        print(f"Error: {e}")
    
    # 2. Check property data
    print("\n2. Property Data Check:")
    try:
        df = conn.execute("""
            SELECT 
                COUNT(*) as total_properties,
                COUNT(CASE WHEN "is active" = true THEN 1 END) as active_properties
            FROM dim_property
        """).fetchdf()
        print(df)
    except Exception as e:
        print(f"Error: {e}")
    
    # 3. Check occupancy data
    print("\n3. Occupancy Data Check:")
    try:
        df = conn.execute("""
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT "property id") as properties,
                AVG("occupied area") as avg_occupied,
                AVG("rentable area") as avg_rentable
            FROM fact_occupancyrentarea
        """).fetchdf()
        print(df)
    except Exception as e:
        print(f"Error: {e}")
    
    # 4. Check amendment data
    print("\n4. Amendment Data Check:")
    try:
        df = conn.execute("""
            SELECT 
                COUNT(*) as total_amendments,
                COUNT(DISTINCT "property code") as properties,
                COUNT(CASE WHEN "amendment status" = 'Activated' THEN 1 END) as activated,
                COUNT(CASE WHEN "amendment status" = 'Superseded' THEN 1 END) as superseded
            FROM dim_fp_amendmentsunitspropertytenant
        """).fetchdf()
        print(df)
    except Exception as e:
        print(f"Error: {e}")
    
    # 5. Test v_financial_summary
    print("\n5. Test v_financial_summary:")
    try:
        df = conn.execute("""
            SELECT * FROM v_financial_summary 
            WHERE revenue > 0
            LIMIT 5
        """).fetchdf()
        print(f"Found {len(df)} properties with revenue")
        if not df.empty:
            print(df[['property code', 'revenue', 'noi']].head())
    except Exception as e:
        print(f"Error: {e}")
    
    # 6. Test v_occupancy_basic
    print("\n6. Test v_occupancy_basic:")
    try:
        df = conn.execute("""
            SELECT * FROM v_occupancy_basic
            WHERE occupancy_pct > 0
            LIMIT 5
        """).fetchdf()
        print(f"Found {len(df)} properties with occupancy")
        if not df.empty:
            print(df[['property code', 'occupancy_pct']].head())
    except Exception as e:
        print(f"Error: {e}")
    
    # 7. Sample properties with all data
    print("\n7. Properties with complete data:")
    try:
        df = conn.execute("""
            SELECT 
                p."property code",
                p."property name",
                COUNT(DISTINCT ft."property id") as has_financial,
                COUNT(DISTINCT o."property id") as has_occupancy,
                COUNT(DISTINCT a."property code") as has_amendments
            FROM dim_property p
            LEFT JOIN fact_total ft ON p."property id" = ft."property id"
            LEFT JOIN fact_occupancyrentarea o ON p."property id" = o."property id"
            LEFT JOIN dim_fp_amendmentsunitspropertytenant a ON p."property code" = a."property code"
            WHERE p."is active" = true
            GROUP BY p."property code", p."property name"
            HAVING COUNT(DISTINCT ft."property id") > 0
            LIMIT 10
        """).fetchdf()
        print(df)
    except Exception as e:
        print(f"Error: {e}")

def main():
    conn = get_db_connection()
    debug_queries(conn)
    conn.close()

if __name__ == "__main__":
    main()