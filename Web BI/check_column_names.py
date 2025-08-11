#!/usr/bin/env python3
"""
Check actual column names in tables
"""

import duckdb
import pandas as pd

def get_db_connection():
    """Get database connection"""
    db_path = '/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Web BI/yardi_dashboard.db'
    return duckdb.connect(db_path)

def check_table_columns(conn, table_name):
    """Check columns for a specific table"""
    try:
        # Get column information
        columns = conn.execute(f"""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = '{table_name}'
            ORDER BY ordinal_position
        """).fetchdf()
        
        print(f"\nColumns in {table_name}:")
        for idx, row in columns.iterrows():
            print(f"  • {row['column_name']} ({row['data_type']})")
        
        return columns
    except Exception as e:
        print(f"Error checking {table_name}: {str(e)}")
        return None

def main():
    """Main execution"""
    conn = get_db_connection()
    
    print("="*60)
    print("CHECKING TABLE COLUMN NAMES")
    print("="*60)
    
    # Check critical tables
    tables_to_check = [
        'dim_property',
        'dim_fp_amendmentsunitspropertytenant',
        'fact_total',
        'dim_lastclosedperiod',
        'dim_commcustomer'
    ]
    
    for table in tables_to_check:
        check_table_columns(conn, table)
    
    # Test query with correct column names
    print("\n" + "="*60)
    print("SAMPLE DATA")
    print("="*60)
    
    # Check dim_property sample
    try:
        df = conn.execute("SELECT * FROM dim_property LIMIT 2").fetchdf()
        print("\nSample dim_property:")
        print(df.columns.tolist())
    except Exception as e:
        print(f"Error: {e}")
    
    # Check dim_lastclosedperiod
    try:
        df = conn.execute("SELECT * FROM dim_lastclosedperiod").fetchdf()
        print("\ndim_lastclosedperiod data:")
        print(df)
    except Exception as e:
        print(f"Error: {e}")
    
    conn.close()

if __name__ == "__main__":
    main()