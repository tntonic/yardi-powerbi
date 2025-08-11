#!/usr/bin/env python3
"""
Fix Property Performance Views and Query
This script creates all necessary database views and runs the property performance query
"""

import duckdb
import pandas as pd
import os
from datetime import datetime
from pathlib import Path

def get_db_connection():
    """Get database connection"""
    db_path = '/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Web BI/yardi_dashboard.db'
    return duckdb.connect(db_path)

def create_views_from_file(conn, sql_file_path, view_name_prefix=""):
    """Create views from SQL file"""
    print(f"\n{'='*60}")
    print(f"Creating views from: {os.path.basename(sql_file_path)}")
    print(f"{'='*60}")
    
    if not os.path.exists(sql_file_path):
        print(f"WARNING: File not found: {sql_file_path}")
        return False
    
    with open(sql_file_path, 'r') as f:
        sql_content = f.read()
    
    # Split by CREATE OR REPLACE VIEW statements
    view_statements = []
    current_statement = []
    lines = sql_content.split('\n')
    
    for line in lines:
        if 'CREATE OR REPLACE VIEW' in line and current_statement:
            view_statements.append('\n'.join(current_statement))
            current_statement = [line]
        else:
            current_statement.append(line)
    
    if current_statement:
        view_statements.append('\n'.join(current_statement))
    
    created_views = []
    failed_views = []
    
    for statement in view_statements:
        if 'CREATE OR REPLACE VIEW' in statement:
            # Extract view name
            try:
                view_name = statement.split('CREATE OR REPLACE VIEW')[1].split(' AS')[0].strip()
                
                # Skip validation queries in comments
                if '/*' in statement:
                    statement = statement.split('/*')[0]
                
                # Try to create the view
                try:
                    conn.execute(statement)
                    created_views.append(view_name)
                    print(f"✓ Created view: {view_name}")
                except Exception as e:
                    failed_views.append((view_name, str(e)))
                    print(f"✗ Failed to create {view_name}: {str(e)[:100]}")
            except Exception as e:
                print(f"✗ Error parsing statement: {str(e)[:100]}")
    
    print(f"\nSummary: Created {len(created_views)} views, {len(failed_views)} failed")
    return len(failed_views) == 0

def create_all_views(conn):
    """Create all necessary views in the correct order"""
    print("\n" + "="*60)
    print("INITIALIZING DATABASE VIEWS")
    print("="*60)
    
    base_path = '/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Web BI/database'
    
    # Order matters! Base views must be created first
    view_files = [
        'amendment_views_fixed.sql',      # Base views (v_current_date, v_current_rent_roll_enhanced, etc.)
        'advanced_views.sql',              # Leasing activity and enhanced views
        'net_absorption_views_fixed.sql',  # Net absorption calculations
        'portfolio_health_views_fixed.sql' # Portfolio health metrics
    ]
    
    all_success = True
    for sql_file in view_files:
        file_path = os.path.join(base_path, sql_file)
        success = create_views_from_file(conn, file_path)
        all_success = all_success and success
    
    return all_success

def run_fixed_property_performance_query(conn, property_codes=None, 
                                         start_date='2020-01-01', 
                                         end_date='2035-12-31'):
    """Run the fixed property performance query"""
    print("\n" + "="*60)
    print("RUNNING PROPERTY PERFORMANCE QUERY")
    print("="*60)
    
    # Build property filter
    property_filter = ""
    if property_codes:
        codes_str = "','".join(property_codes)
        property_filter = f"AND p.\"property code\" IN ('{codes_str}')"
    
    query = f"""
    WITH date_range AS (
        SELECT 
            DATE '{start_date}' as start_date,
            DATE '{end_date}' as end_date
    ),
    occupancy_data AS (
        SELECT 
            p."property code",
            p."property name",
            om.physical_occupancy_pct,
            om.vacancy_rate_pct,
            om.total_rentable_area,
            om.total_leased_area
        FROM dim_property p
        LEFT JOIN v_occupancy_metrics om ON p."property code" = om."property code"
        WHERE 1=1 {property_filter}
    ),
    financial_data AS (
        SELECT 
            ft."property id",
            p."property code",
            -- Revenue (4xxxx accounts, multiply by -1)
            SUM(CASE 
                WHEN ft."account code" LIKE '4%' 
                THEN ft.amount * -1 
                ELSE 0 
            END) as revenue,
            -- Operating Expenses (5xxxx accounts)
            SUM(CASE 
                WHEN ft."account code" LIKE '5%' 
                THEN ft.amount 
                ELSE 0 
            END) as operating_expenses,
            -- NOI
            SUM(CASE 
                WHEN ft."account code" LIKE '4%' THEN ft.amount * -1
                WHEN ft."account code" LIKE '5%' THEN -ft.amount
                ELSE 0 
            END) as noi
        FROM fact_total ft
        CROSS JOIN date_range dr
        JOIN dim_property p ON ft."property id" = p."property id"
        WHERE DATE '1900-01-01' + INTERVAL '1 day' * (ft.month - 2) 
              BETWEEN dr.start_date AND dr.end_date
          {property_filter.replace('p.', 'p.')}
        GROUP BY ft."property id", p."property code"
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
            property_code,
            SUM(new_leases_count) as total_new_leases,
            SUM(renewals_count) as total_renewals,
            SUM(terminations_count) as total_terminations,
            SUM(net_activity_sf) as total_net_activity_sf,
            -- Calculate retention rate
            CASE 
                WHEN SUM(renewals_count + terminations_count) > 0
                THEN (SUM(renewals_count) * 100.0) / SUM(renewals_count + terminations_count)
                ELSE 0
            END as retention_rate
        FROM v_leasing_activity_summary
        GROUP BY property_code
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
        od."property code",
        od."property name",
        -- Occupancy Metrics
        ROUND(od.physical_occupancy_pct, 2) as occupancy_pct,
        ROUND(od.vacancy_rate_pct, 2) as vacancy_pct,
        od.total_rentable_area as rentable_sf,
        od.total_leased_area as occupied_sf,
        -- Financial Metrics
        ROUND(COALESCE(fd.revenue, 0), 2) as revenue,
        ROUND(COALESCE(fd.operating_expenses, 0), 2) as expenses,
        ROUND(COALESCE(fd.noi, 0), 2) as noi,
        ROUND(CASE 
            WHEN fd.revenue > 0 
            THEN (fd.noi / fd.revenue) * 100 
            ELSE 0 
        END, 2) as noi_margin_pct,
        -- Rent Roll Metrics
        ROUND(COALESCE(rr.total_monthly_rent, 0), 2) as monthly_rent,
        ROUND(COALESCE(rr.avg_rent_psf, 0), 2) as avg_rent_psf,
        COALESCE(rr.tenant_count, 0) as tenant_count,
        -- Leasing Activity
        COALESCE(ld.total_new_leases, 0) as new_leases,
        COALESCE(ld.total_renewals, 0) as renewals,
        COALESCE(ld.total_terminations, 0) as terminations,
        ROUND(COALESCE(ld.total_net_activity_sf, 0), 2) as net_leasing_sf,
        ROUND(COALESCE(ld.retention_rate, 0), 2) as retention_rate_pct,
        -- Credit Risk
        ROUND(COALESCE(cd.avg_credit_score, 0), 2) as avg_credit_score,
        COALESCE(cd.high_risk_tenants, 0) as high_risk_tenants,
        ROUND(COALESCE(cd.revenue_at_risk_pct, 0), 2) as revenue_at_risk_pct
    FROM occupancy_data od
    LEFT JOIN financial_data fd ON od."property code" = fd."property code"
    LEFT JOIN rent_roll_data rr ON od."property code" = rr."property code"
    LEFT JOIN leasing_data ld ON od."property code" = ld.property_code
    LEFT JOIN credit_data cd ON od."property code" = cd."property code"
    WHERE COALESCE(fd.revenue, 0) > 0
       OR COALESCE(rr.total_monthly_rent, 0) > 0
    ORDER BY COALESCE(fd.revenue, 0) DESC
    LIMIT 20
    """
    
    try:
        df = conn.execute(query).fetchdf()
        print(f"\nSuccessfully retrieved {len(df)} properties")
        return df
    except Exception as e:
        print(f"\nError running query: {str(e)}")
        return None

def test_individual_views(conn):
    """Test each view individually to identify issues"""
    print("\n" + "="*60)
    print("TESTING INDIVIDUAL VIEWS")
    print("="*60)
    
    test_views = [
        'v_current_date',
        'v_current_rent_roll_enhanced',
        'v_occupancy_metrics',
        'v_leasing_activity_summary',
        'v_rent_roll_with_credit'
    ]
    
    for view in test_views:
        try:
            result = conn.execute(f"SELECT COUNT(*) as cnt FROM {view}").fetchone()
            print(f"✓ {view}: {result[0]} records")
        except Exception as e:
            print(f"✗ {view}: {str(e)[:100]}")

def main():
    """Main execution"""
    print("\n" + "="*60)
    print("PROPERTY PERFORMANCE VIEWS FIX")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Connect to database
    conn = get_db_connection()
    
    try:
        # Step 1: Create all views
        success = create_all_views(conn)
        
        if not success:
            print("\nWARNING: Some views failed to create. Continuing anyway...")
        
        # Step 2: Test individual views
        test_individual_views(conn)
        
        # Step 3: Run the property performance query
        # Test with sample property codes
        sample_properties = ['3ca00001', '3ca00002', '3ca00003', '3ca00004', '3ca00005']
        
        df = run_fixed_property_performance_query(
            conn, 
            property_codes=sample_properties,
            start_date='2020-01-01',
            end_date='2035-12-31'
        )
        
        if df is not None and not df.empty:
            print("\n" + "="*60)
            print("PROPERTY PERFORMANCE DATA")
            print("="*60)
            print(df.to_string())
            
            # Save to CSV for reference
            output_file = 'property_performance_results.csv'
            df.to_csv(output_file, index=False)
            print(f"\nResults saved to: {output_file}")
        else:
            print("\nNo data retrieved or query failed")
            
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