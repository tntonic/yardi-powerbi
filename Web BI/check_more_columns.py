#!/usr/bin/env python3
"""
Check column names for amendment charges and leasing activity tables
"""

import duckdb

def get_db_connection():
    """Get database connection"""
    db_path = '/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Web BI/yardi_dashboard.db'
    return duckdb.connect(db_path)

def check_columns(conn, table_name):
    """Check columns and sample data"""
    print(f"\n{'='*60}")
    print(f"TABLE: {table_name}")
    print('='*60)
    
    # Get columns
    try:
        columns = conn.execute(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = '{table_name}'
            ORDER BY ordinal_position
        """).fetchdf()
        
        print("Columns:")
        for col in columns['column_name']:
            print(f"  • {col}")
        
        # Get sample data
        sample = conn.execute(f"SELECT * FROM {table_name} LIMIT 2").fetchdf()
        print(f"\nSample data ({len(sample)} rows):")
        print(sample.columns.tolist())
        
    except Exception as e:
        print(f"Error: {e}")

def main():
    conn = get_db_connection()
    
    # Check critical tables
    tables = [
        'dim_fp_amendmentchargeschedule',
        'fact_leasingactivity',
        'dim_fp_terminationtomoveoutreas',
        'fact_occupancyrentarea'
    ]
    
    for table in tables:
        check_columns(conn, table)
    
    conn.close()

if __name__ == "__main__":
    main()