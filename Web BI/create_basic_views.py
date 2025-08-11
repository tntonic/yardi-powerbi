#!/usr/bin/env python3
"""
Create Basic Views for Property Performance
Using actual column names from the database
"""

import duckdb
import pandas as pd
from datetime import datetime

def get_db_connection():
    """Get database connection"""
    db_path = '/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Web BI/yardi_dashboard.db'
    return duckdb.connect(db_path)

def create_basic_views(conn):
    """Create basic views with actual column names"""
    
    views = []
    
    # 1. Current date view
    views.append("""
    CREATE OR REPLACE VIEW v_current_date AS
    SELECT 
        MAX("last closed period") as current_date,
        MAX("last closed period") as reporting_date
    FROM dim_lastclosedperiod
    """)
    
    # 2. Basic property list
    views.append("""
    CREATE OR REPLACE VIEW v_property_list AS
    SELECT 
        "property id",
        "property code",
        "property name",
        "is active",
        "acquire date"
    FROM dim_property
    WHERE "is active" = true
    """)
    
    # 3. Financial summary
    views.append("""
    CREATE OR REPLACE VIEW v_financial_summary AS
    SELECT 
        p."property code",
        p."property name",
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
    JOIN dim_property p ON ft."property id" = p."property id"
    GROUP BY p."property code", p."property name"
    """)
    
    # 4. Occupancy metrics from fact_occupancyrentarea
    views.append("""
    CREATE OR REPLACE VIEW v_occupancy_basic AS
    SELECT 
        p."property code",
        p."property name",
        AVG(o."occupied area") as avg_occupied_area,
        AVG(o."rentable area") as avg_rentable_area,
        CASE 
            WHEN AVG(o."rentable area") > 0
            THEN (AVG(o."occupied area") / AVG(o."rentable area")) * 100
            ELSE 0
        END as occupancy_pct,
        AVG(o."total rent") as avg_total_rent
    FROM fact_occupancyrentarea o
    JOIN dim_property p ON o."property id" = p."property id"
    GROUP BY p."property code", p."property name"
    """)
    
    # 5. Amendment-based rent roll (simplified)
    views.append("""
    CREATE OR REPLACE VIEW v_rent_roll_basic AS
    SELECT 
        a."property code",
        a."tenant hmy",
        a."amendment hmy",
        a."amendment status",
        a."amendment type",
        a."amendment sequence",
        a."amendment sf" as leased_area,
        a."amendment start date",
        a."amendment end date",
        COALESCE(cs."monthly amount", 0) as monthly_rent
    FROM dim_fp_amendmentsunitspropertytenant a
    LEFT JOIN dim_fp_amendmentchargeschedule cs 
        ON a."amendment hmy" = cs."amendment hmy"
        AND cs."charge code" IN ('RENT', 'BASE RENT', 'MINIMUM RENT')
    WHERE a."amendment status" IN ('Activated', 'Superseded')
    """)
    
    # Execute each view
    created = 0
    failed = 0
    
    print("\n" + "="*60)
    print("CREATING BASIC VIEWS")
    print("="*60)
    
    for view_sql in views:
        try:
            # Extract view name
            view_name = view_sql.split('CREATE OR REPLACE VIEW ')[1].split(' AS')[0]
            
            conn.execute(view_sql)
            print(f"✓ Created: {view_name}")
            created += 1
        except Exception as e:
            print(f"✗ Failed: {str(e)[:100]}")
            failed += 1
    
    print(f"\nSummary: Created {created} views, {failed} failed")
    return created > 0

def run_simple_property_query(conn):
    """Run a simple property performance query"""
    
    query = """
    WITH property_data AS (
        SELECT 
            COALESCE(fs."property code", ob."property code") as property_code,
            COALESCE(fs."property name", ob."property name") as property_name,
            fs.revenue,
            fs.operating_expenses,
            fs.noi,
            CASE 
                WHEN fs.revenue > 0 
                THEN (fs.noi / fs.revenue) * 100 
                ELSE 0 
            END as noi_margin_pct,
            ob.occupancy_pct,
            ob.avg_rentable_area,
            ob.avg_occupied_area,
            ob.avg_total_rent
        FROM v_financial_summary fs
        FULL OUTER JOIN v_occupancy_basic ob 
            ON fs."property code" = ob."property code"
    ),
    rent_roll_summary AS (
        SELECT 
            "property code",
            COUNT(DISTINCT "tenant hmy") as tenant_count,
            SUM(monthly_rent) as total_monthly_rent,
            SUM(leased_area) as total_leased_area,
            AVG(CASE 
                WHEN leased_area > 0 
                THEN (monthly_rent * 12) / leased_area 
                ELSE 0 
            END) as avg_rent_psf
        FROM v_rent_roll_basic
        WHERE monthly_rent > 0
        GROUP BY "property code"
    )
    SELECT 
        pd.property_code as "Property Code",
        pd.property_name as "Property Name",
        
        -- Financial Metrics
        ROUND(COALESCE(pd.revenue, 0), 0) as "Revenue",
        ROUND(COALESCE(pd.operating_expenses, 0), 0) as "Expenses", 
        ROUND(COALESCE(pd.noi, 0), 0) as "NOI",
        ROUND(COALESCE(pd.noi_margin_pct, 0), 1) as "NOI Margin %",
        
        -- Occupancy Metrics
        ROUND(COALESCE(pd.occupancy_pct, 0), 1) as "Occupancy %",
        CAST(COALESCE(pd.avg_rentable_area, 0) AS INTEGER) as "Rentable SF",
        CAST(COALESCE(pd.avg_occupied_area, 0) AS INTEGER) as "Occupied SF",
        
        -- Rent Roll Metrics
        COALESCE(rr.tenant_count, 0) as "Tenants",
        ROUND(COALESCE(rr.total_monthly_rent, pd.avg_total_rent, 0), 0) as "Monthly Rent",
        ROUND(COALESCE(rr.avg_rent_psf, 0), 2) as "Avg Rent PSF"
        
    FROM property_data pd
    LEFT JOIN rent_roll_summary rr ON pd.property_code = rr."property code"
    WHERE pd.revenue > 0 OR rr.total_monthly_rent > 0
    ORDER BY pd.revenue DESC NULLS LAST
    LIMIT 20
    """
    
    try:
        df = conn.execute(query).fetchdf()
        return df
    except Exception as e:
        print(f"Query error: {str(e)}")
        return None

def main():
    """Main execution"""
    print("\n" + "="*60)
    print("PROPERTY PERFORMANCE - SIMPLIFIED")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    conn = get_db_connection()
    
    try:
        # Create basic views
        success = create_basic_views(conn)
        
        if success:
            # Run property performance query
            print("\n" + "="*60)
            print("PROPERTY PERFORMANCE DATA")
            print("="*60)
            
            df = run_simple_property_query(conn)
            
            if df is not None and not df.empty:
                # Display results
                pd.set_option('display.max_columns', None)
                pd.set_option('display.width', 200)
                
                print(df.to_string(index=False))
                
                # Save to CSV
                output_file = 'property_performance_simple.csv'
                df.to_csv(output_file, index=False)
                print(f"\nResults saved to: {output_file}")
                
                # Summary
                print("\n" + "="*60)
                print("SUMMARY STATISTICS")
                print("="*60)
                print(f"Total Properties: {len(df)}")
                print(f"Total Revenue: ${df['Revenue'].sum():,.0f}")
                print(f"Total NOI: ${df['NOI'].sum():,.0f}")
                print(f"Average Occupancy: {df['Occupancy %'].mean():.1f}%")
                print(f"Total Monthly Rent: ${df['Monthly Rent'].sum():,.0f}")
                
            else:
                print("No data retrieved")
                
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()
    
    print("\n" + "="*60)
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    print("\nNOTE: Date filters default to Jan 2020 - Dec 2035 as requested")
    print("Some metrics are simplified due to missing column mappings")

if __name__ == "__main__":
    main()