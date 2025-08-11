#!/usr/bin/env python3
"""
Check and Load Yardi Tables into Database
This script checks for existing tables and loads CSV data if needed
"""

import duckdb
import pandas as pd
import os
from pathlib import Path
from datetime import datetime

def get_db_connection():
    """Get database connection"""
    db_path = '/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Web BI/yardi_dashboard.db'
    return duckdb.connect(db_path)

def check_existing_tables(conn):
    """Check which tables already exist in the database"""
    print("\n" + "="*60)
    print("CHECKING EXISTING TABLES")
    print("="*60)
    
    try:
        # Get list of all tables
        tables = conn.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'main'
            ORDER BY table_name
        """).fetchdf()
        
        if not tables.empty:
            print(f"\nFound {len(tables)} existing tables:")
            for idx, row in tables.iterrows():
                table_name = row['table_name']
                count = conn.execute(f"SELECT COUNT(*) as cnt FROM {table_name}").fetchone()[0]
                print(f"  • {table_name}: {count} records")
        else:
            print("\nNo tables found in database")
            
        return tables['table_name'].tolist() if not tables.empty else []
        
    except Exception as e:
        print(f"Error checking tables: {str(e)}")
        return []

def load_csv_tables(conn, force_reload=False):
    """Load CSV files from Yardi_Tables directory"""
    print("\n" + "="*60)
    print("LOADING CSV TABLES")
    print("="*60)
    
    # Path to CSV files
    csv_path = '/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Data/Yardi_Tables'
    
    if not os.path.exists(csv_path):
        print(f"ERROR: CSV directory not found: {csv_path}")
        return False
    
    # Get existing tables
    existing_tables = check_existing_tables(conn) if not force_reload else []
    
    # List all CSV files
    csv_files = [f for f in os.listdir(csv_path) if f.endswith('.csv')]
    print(f"\nFound {len(csv_files)} CSV files")
    
    loaded_count = 0
    skipped_count = 0
    failed_count = 0
    
    for csv_file in sorted(csv_files):
        # Get table name from file name (remove .csv extension)
        table_name = csv_file[:-4].lower()
        
        # Skip if table already exists (unless force reload)
        if table_name in existing_tables and not force_reload:
            print(f"  ⊘ Skipping {table_name} (already exists)")
            skipped_count += 1
            continue
        
        # Load CSV file
        file_path = os.path.join(csv_path, csv_file)
        try:
            # Read CSV
            df = pd.read_csv(file_path, low_memory=False)
            
            # Drop existing table if force reload
            if force_reload and table_name in existing_tables:
                conn.execute(f"DROP TABLE IF EXISTS {table_name}")
            
            # Load into database
            conn.register('temp_df', df)
            conn.execute(f"CREATE TABLE {table_name} AS SELECT * FROM temp_df")
            conn.unregister('temp_df')
            
            # Get record count
            count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            print(f"  ✓ Loaded {table_name}: {count} records")
            loaded_count += 1
            
        except Exception as e:
            print(f"  ✗ Failed to load {table_name}: {str(e)[:100]}")
            failed_count += 1
    
    print(f"\nSummary: Loaded {loaded_count}, Skipped {skipped_count}, Failed {failed_count}")
    return failed_count == 0

def verify_critical_tables(conn):
    """Verify critical tables are loaded"""
    print("\n" + "="*60)
    print("VERIFYING CRITICAL TABLES")
    print("="*60)
    
    critical_tables = [
        'dim_property',
        'dim_commcustomer',
        'dim_fp_amendmentsunitspropertytenant',
        'dim_fp_amendmentchargeschedule',
        'dim_fp_terminationtomoveoutreas',
        'dim_fp_customercreditscorecustomdata',
        'dim_fp_customertoparentmap',
        'dim_lastclosedperiod',
        'fact_total',
        'fact_occupancyrentarea',
        'fact_leasingactivity'
    ]
    
    all_present = True
    for table in critical_tables:
        try:
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"  ✓ {table}: {count} records")
        except:
            print(f"  ✗ {table}: NOT FOUND")
            all_present = False
    
    return all_present

def create_sample_query(conn):
    """Create and run a simple query to test the data"""
    print("\n" + "="*60)
    print("TESTING SIMPLE QUERY")
    print("="*60)
    
    try:
        # Simple property list query
        query = """
        SELECT 
            "property code",
            "property name",
            "rentable area",
            "book id"
        FROM dim_property
        LIMIT 10
        """
        
        df = conn.execute(query).fetchdf()
        print("\nSample Properties:")
        print(df.to_string())
        
        return True
    except Exception as e:
        print(f"Error running test query: {str(e)}")
        return False

def main():
    """Main execution"""
    print("\n" + "="*60)
    print("DATABASE TABLE LOADER")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Connect to database
    conn = get_db_connection()
    
    try:
        # Step 1: Check existing tables
        existing_tables = check_existing_tables(conn)
        
        # Step 2: Load CSV tables if needed
        if len(existing_tables) < 10:  # If we have less than 10 tables, load them
            print("\nDatabase appears empty or incomplete. Loading tables...")
            success = load_csv_tables(conn, force_reload=False)
            
            if not success:
                print("\nWARNING: Some tables failed to load")
        else:
            print(f"\nDatabase already contains {len(existing_tables)} tables")
        
        # Step 3: Verify critical tables
        all_present = verify_critical_tables(conn)
        
        if not all_present:
            print("\nWARNING: Some critical tables are missing!")
            print("Attempting to reload missing tables...")
            load_csv_tables(conn, force_reload=False)
        
        # Step 4: Test with simple query
        create_sample_query(conn)
        
        print("\n" + "="*60)
        print("DATABASE READY FOR VIEW CREATION")
        print("="*60)
        print("\nNext steps:")
        print("1. Run: python3 fix_property_performance_views.py")
        print("2. This will create all necessary views")
        print("3. Then run property performance queries")
        
    except Exception as e:
        print(f"\nFATAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()
    
    print("\n" + "="*60)
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

if __name__ == "__main__":
    main()