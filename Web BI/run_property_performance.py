#!/usr/bin/env python3
"""
Property Performance Dashboard Query
Creates necessary views and runs property performance analysis
"""

import duckdb
import pandas as pd
from datetime import datetime
import os

def get_db_connection():
    """Get database connection"""
    db_path = '/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Web BI/yardi_dashboard.db'
    return duckdb.connect(db_path)

def create_corrected_views(conn):
    """Create the corrected views"""
    print("\n" + "="*60)
    print("CREATING CORRECTED VIEWS")
    print("="*60)
    
    # Read and execute corrected amendment views
    views_created = 0
    views_failed = 0
    
    # List of SQL files to execute
    sql_files = [
        'database/corrected_amendment_views.sql',
        'database/corrected_leasing_views.sql'
    ]
    
    for sql_file in sql_files:
        if not os.path.exists(sql_file):
            print(f"File not found: {sql_file}")
            continue
            
        print(f"\nProcessing: {sql_file}")
        
        with open(sql_file, 'r') as f:
            sql_content = f.read()
        
        # Split by CREATE OR REPLACE VIEW
        statements = sql_content.split('CREATE OR REPLACE VIEW')
        
        for statement in statements[1:]:  # Skip first empty split
            try:
                # Extract view name
                view_name = statement.split(' AS')[0].strip()
                
                # Reconstruct full statement
                full_statement = 'CREATE OR REPLACE VIEW ' + statement
                
                # Remove comments at end if any
                if '-- =' in full_statement:
                    parts = full_statement.split('-- =')
                    full_statement = parts[0]
                
                # Execute
                conn.execute(full_statement)
                print(f"  ✓ Created view: {view_name}")
                views_created += 1
                
            except Exception as e:
                print(f"  ✗ Failed to create view: {str(e)[:100]}")
                views_failed += 1
    
    print(f"\nSummary: Created {views_created} views, {views_failed} failed")
    return views_created > 0

def run_property_performance_query(conn, property_codes=None, 
                                  start_date='2020-01-01', 
                                  end_date='2035-12-31'):
    """Run the property performance query with corrected column names"""
    print("\n" + "="*60)
    print("RUNNING PROPERTY PERFORMANCE QUERY")
    print(f"Date Range: {start_date} to {end_date}")
    print("="*60)
    
    # Build property filter
    property_filter = ""
    if property_codes:
        codes_str = "','".join(property_codes)
        property_filter = f"WHERE p.\"property code\" IN ('{codes_str}')"
    
    query = f"""
    WITH date_range AS (
        SELECT 
            DATE '{start_date}' as start_date,
            DATE '{end_date}' as end_date
    ),
    occupancy_data AS (
        SELECT 
            "property code",
            "property name",
            physical_occupancy_pct,
            vacancy_rate_pct,
            total_rentable_area,
            total_leased_area,
            total_monthly_rent
        FROM v_occupancy_metrics
    ),
    financial_data AS (
        SELECT 
            p."property code",
            -- Revenue (4xxxx accounts, multiply by -1)
            SUM(CASE 
                WHEN CAST(ft."account id" AS VARCHAR) LIKE '4%' 
                THEN ft.amount * -1 
                ELSE 0 
            END) as revenue,
            -- Operating Expenses (5xxxx accounts)
            SUM(CASE 
                WHEN CAST(ft."account id" AS VARCHAR) LIKE '5%' 
                THEN ft.amount 
                ELSE 0 
            END) as operating_expenses,
            -- NOI
            SUM(CASE 
                WHEN CAST(ft."account id" AS VARCHAR) LIKE '4%' THEN ft.amount * -1
                WHEN CAST(ft."account id" AS VARCHAR) LIKE '5%' THEN -ft.amount
                ELSE 0 
            END) as noi
        FROM fact_total ft
        CROSS JOIN date_range dr
        JOIN dim_property p ON ft."property id" = p."property id"
        WHERE DATE '1900-01-01' + INTERVAL '1 day' * (ft.month - 2) 
              BETWEEN dr.start_date AND dr.end_date
        GROUP BY p."property code"
    ),
    rent_roll_data AS (
        SELECT 
            "property code",
            SUM(current_monthly_rent) as total_monthly_rent,
            AVG(current_rent_psf) as avg_rent_psf,
            COUNT(DISTINCT "tenant hmy") as tenant_count,
            SUM("leased area") as leased_sf
        FROM v_current_rent_roll_enhanced
        WHERE current_monthly_rent > 0
        GROUP BY "property code"
    ),
    leasing_data AS (
        SELECT 
            "property code",
            SUM(new_leases_count) as total_new_leases,
            SUM(renewals_count) as total_renewals,
            SUM(terminations_count) as total_terminations,
            SUM(net_activity_sf) as total_net_activity_sf,
            AVG(retention_rate) as avg_retention_rate
        FROM v_leasing_activity_summary
        GROUP BY "property code"
    ),
    credit_data AS (
        SELECT 
            "property code",
            AVG(CASE 
                WHEN "credit score" IS NOT NULL 
                THEN "credit score" 
                ELSE NULL 
            END) as avg_credit_score,
            COUNT(CASE 
                WHEN credit_risk_category IN ('High Risk', 'Very High Risk') 
                THEN 1 
            END) as high_risk_tenants,
            SUM(CASE 
                WHEN credit_risk_category IN ('High Risk', 'Very High Risk') 
                THEN current_monthly_rent 
                ELSE 0 
            END) * 100.0 / NULLIF(SUM(current_monthly_rent), 0) as revenue_at_risk_pct
        FROM v_rent_roll_with_credit
        WHERE current_monthly_rent > 0
        GROUP BY "property code"
    )
    SELECT 
        COALESCE(od."property code", fd."property code", rr."property code") as "Property Code",
        COALESCE(od."property name", 'Unknown') as "Property Name",
        
        -- Occupancy Metrics
        ROUND(COALESCE(od.physical_occupancy_pct, 0), 1) as "Occupancy %",
        ROUND(COALESCE(od.vacancy_rate_pct, 0), 1) as "Vacancy %",
        CAST(COALESCE(od.total_rentable_area, 0) AS INTEGER) as "Rentable SF",
        CAST(COALESCE(od.total_leased_area, 0) AS INTEGER) as "Occupied SF",
        
        -- Financial Metrics  
        ROUND(COALESCE(fd.revenue, 0), 0) as "Revenue",
        ROUND(COALESCE(fd.operating_expenses, 0), 0) as "Expenses",
        ROUND(COALESCE(fd.noi, 0), 0) as "NOI",
        ROUND(CASE 
            WHEN fd.revenue > 0 
            THEN (fd.noi / fd.revenue) * 100 
            ELSE 0 
        END, 1) as "NOI Margin %",
        
        -- Rent Roll Metrics
        ROUND(COALESCE(rr.total_monthly_rent, od.total_monthly_rent, 0), 0) as "Monthly Rent",
        ROUND(COALESCE(rr.avg_rent_psf, 0), 2) as "Avg Rent PSF",
        COALESCE(rr.tenant_count, 0) as "Tenants",
        
        -- Leasing Activity
        COALESCE(ld.total_new_leases, 0) as "New Leases",
        COALESCE(ld.total_renewals, 0) as "Renewals",
        COALESCE(ld.total_terminations, 0) as "Terms",
        CAST(COALESCE(ld.total_net_activity_sf, 0) AS INTEGER) as "Net SF",
        ROUND(COALESCE(ld.avg_retention_rate, 0), 1) as "Retention %",
        
        -- Credit Risk
        ROUND(COALESCE(cd.avg_credit_score, 0), 1) as "Avg Credit",
        COALESCE(cd.high_risk_tenants, 0) as "High Risk",
        ROUND(COALESCE(cd.revenue_at_risk_pct, 0), 1) as "Rev at Risk %"
        
    FROM occupancy_data od
    FULL OUTER JOIN financial_data fd ON od."property code" = fd."property code"
    LEFT JOIN rent_roll_data rr ON COALESCE(od."property code", fd."property code") = rr."property code"
    LEFT JOIN leasing_data ld ON COALESCE(od."property code", fd."property code") = ld."property code"
    LEFT JOIN credit_data cd ON COALESCE(od."property code", fd."property code") = cd."property code"
    {property_filter}
    ORDER BY COALESCE(fd.revenue, 0) DESC
    LIMIT 20
    """
    
    try:
        df = conn.execute(query).fetchdf()
        return df
    except Exception as e:
        print(f"Error running query: {str(e)}")
        return None

def test_views(conn):
    """Test that critical views exist"""
    print("\n" + "="*60)
    print("TESTING VIEWS")
    print("="*60)
    
    test_views = [
        'v_current_date',
        'v_current_rent_roll_enhanced',
        'v_occupancy_metrics',
        'v_leasing_activity_summary',
        'v_rent_roll_with_credit'
    ]
    
    all_exist = True
    for view in test_views:
        try:
            count = conn.execute(f"SELECT COUNT(*) FROM {view}").fetchone()[0]
            print(f"  ✓ {view}: {count} records")
        except Exception as e:
            print(f"  ✗ {view}: Not found")
            all_exist = False
    
    return all_exist

def main():
    """Main execution"""
    print("\n" + "="*60)
    print("PROPERTY PERFORMANCE DASHBOARD")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    conn = get_db_connection()
    
    try:
        # Step 1: Create corrected views
        success = create_corrected_views(conn)
        
        if not success:
            print("\nWARNING: Failed to create views. Trying to continue...")
        
        # Step 2: Test views
        views_exist = test_views(conn)
        
        if not views_exist:
            print("\nERROR: Critical views are missing. Cannot continue.")
            return
        
        # Step 3: Run property performance query
        print("\nRunning query for all properties...")
        
        # First, get all properties
        df_all = run_property_performance_query(
            conn,
            property_codes=None,  # Get all properties
            start_date='2020-01-01',
            end_date='2035-12-31'
        )
        
        if df_all is not None and not df_all.empty:
            print("\n" + "="*60)
            print("TOP 20 PROPERTIES BY REVENUE")
            print("="*60)
            
            # Display results
            pd.set_option('display.max_columns', None)
            pd.set_option('display.width', None)
            pd.set_option('display.max_colwidth', 20)
            
            print(df_all.to_string(index=False))
            
            # Save to CSV
            output_file = 'property_performance_dashboard.csv'
            df_all.to_csv(output_file, index=False)
            print(f"\nResults saved to: {output_file}")
            
            # Summary statistics
            print("\n" + "="*60)
            print("PORTFOLIO SUMMARY")
            print("="*60)
            print(f"Total Properties: {len(df_all)}")
            print(f"Total Revenue: ${df_all['Revenue'].sum():,.0f}")
            print(f"Total NOI: ${df_all['NOI'].sum():,.0f}")
            print(f"Average Occupancy: {df_all['Occupancy %'].mean():.1f}%")
            print(f"Average NOI Margin: {df_all['NOI Margin %'].mean():.1f}%")
            print(f"Total Monthly Rent: ${df_all['Monthly Rent'].sum():,.0f}")
            print(f"Average Rent PSF: ${df_all['Avg Rent PSF'].mean():.2f}")
            
        else:
            print("\nNo data retrieved")
            
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()
    
    print("\n" + "="*60)
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

if __name__ == "__main__":
    main()