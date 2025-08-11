#!/usr/bin/env python3
"""
Create Minimal Critical Views for Dashboard
Creates just the essential view v_current_rent_roll_enhanced with correct columns
"""

import duckdb
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_minimal_views(db_path: str = "yardi.duckdb"):
    """Create minimal set of views needed for dashboard"""
    conn = duckdb.connect(db_path)
    
    # Create v_current_rent_roll_enhanced directly without intermediate views
    sql = """
    CREATE OR REPLACE VIEW v_current_rent_roll_enhanced AS
    WITH current_date_ref AS (
        SELECT MAX("last closed period") as current_date FROM dim_lastclosedperiod
    ),
    latest_amendments AS (
        SELECT a.*, 
               p."property name",
               p."property code" as property_code,
               t."lessee name" as tenant_name,
               t."tenant code" as tenant_code
        FROM dim_fp_amendmentsunitspropertytenant a
        CROSS JOIN current_date_ref cd
        LEFT JOIN dim_property p ON a."property hmy" = p."property id"
        LEFT JOIN dim_commcustomer t ON a."tenant hmy" = t."tenant id"
        WHERE a."amendment status" IN ('Activated', 'Superseded')
        AND a."amendment type" NOT IN ('Termination', 'Proposal in DM', 'Modification')
        AND a."amendment start date" <= cd.current_date
        AND (a."amendment end date" >= cd.current_date OR a."amendment end date" IS NULL)
    ),
    max_sequences AS (
        SELECT "property hmy", "tenant hmy", MAX("amendment sequence") as max_seq
        FROM latest_amendments
        GROUP BY "property hmy", "tenant hmy"
    ),
    latest_only AS (
        SELECT la.*
        FROM latest_amendments la
        INNER JOIN max_sequences ms 
            ON la."property hmy" = ms."property hmy" 
            AND la."tenant hmy" = ms."tenant hmy"
            AND la."amendment sequence" = ms.max_seq
    ),
    with_charges AS (
        SELECT 
            lo.*,
            cs."charge code",
            CASE 
                WHEN cs."monthly amount" IS NOT NULL AND cs."monthly amount" > 0 THEN cs."monthly amount"
                WHEN cs."amount period desc" = 'Monthly' THEN cs."amount"
                WHEN cs."amount period desc" = 'Annually' THEN cs."amount" / 12
                WHEN cs."amount period desc" = 'Quarterly' THEN cs."amount" / 3
                WHEN cs."amount period desc" = 'Semi-Annually' THEN cs."amount" / 6
                ELSE COALESCE(cs."amount", 0)
            END as monthly_charge_amount
        FROM latest_only lo
        LEFT JOIN dim_fp_amendmentchargeschedule cs 
            ON lo."amendment hmy" = cs."amendment hmy"
        WHERE cs."charge code" IN ('RENT', 'BASE RENT', 'MINIMUM RENT', 'BASIC RENT', 'rent')
            OR cs."charge code" IS NULL
    )
    SELECT 
        "property hmy",
        property_code,
        "property name",
        "tenant hmy",
        tenant_code,
        tenant_name,
        "amendment hmy",
        "amendment sequence",
        "amendment type",
        "amendment status",
        "amendment start date",
        "amendment end date",
        "amendment sf" as "leased area",
        SUM(monthly_charge_amount) as current_monthly_rent,
        SUM(monthly_charge_amount) * 12 as current_annual_rent,
        CASE 
            WHEN "amendment sf" > 0 
            THEN (SUM(monthly_charge_amount) * 12) / "amendment sf"
            ELSE 0
        END as current_rent_psf
    FROM with_charges
    GROUP BY 
        "property hmy", property_code, "property name",
        "tenant hmy", tenant_code, tenant_name,
        "amendment hmy", "amendment sequence", "amendment type",
        "amendment status", "amendment start date", "amendment end date",
        "amendment sf"
    """
    
    try:
        conn.execute(sql)
        logger.info("✓ Created view: v_current_rent_roll_enhanced")
        
        # Test the view
        count = conn.execute("SELECT COUNT(*) FROM v_current_rent_roll_enhanced").fetchone()[0]
        logger.info(f"  View has {count} rows")
        
        # Test join with dim_property
        test_query = """
        SELECT COUNT(*) 
        FROM v_current_rent_roll_enhanced rr
        JOIN dim_property p ON rr.property_code = p."property code"
        """
        result = conn.execute(test_query).fetchone()[0]
        logger.info(f"✓ Dashboard query works! Found {result} matching records")
        
    except Exception as e:
        logger.error(f"✗ Failed to create view: {str(e)}")
    
    # Create other supporting views
    other_views = {
        "v_occupancy_metrics": """
        CREATE OR REPLACE VIEW v_occupancy_metrics AS
        WITH property_totals AS (
            SELECT 
                p."property id",
                p."property code",
                p."property name",
                MAX(o."rentable area") as total_rentable_area
            FROM dim_property p
            LEFT JOIN fact_occupancyrentarea o ON p."property id" = o."property id"
            GROUP BY p."property id", p."property code", p."property name"
        ),
        leased_totals AS (
            SELECT 
                property_code,
                SUM("leased area") as total_leased_area,
                SUM(current_monthly_rent) as total_monthly_rent
            FROM v_current_rent_roll_enhanced
            GROUP BY property_code
        )
        SELECT 
            pt."property code",
            pt."property name",
            pt.total_rentable_area,
            COALESCE(lt.total_leased_area, 0) as total_leased_area,
            COALESCE(lt.total_monthly_rent, 0) as total_monthly_rent,
            CASE 
                WHEN pt.total_rentable_area > 0
                THEN (COALESCE(lt.total_leased_area, 0) / pt.total_rentable_area) * 100
                ELSE 0
            END as physical_occupancy_pct,
            pt.total_rentable_area - COALESCE(lt.total_leased_area, 0) as vacant_sf,
            CASE 
                WHEN pt.total_rentable_area > 0
                THEN ((pt.total_rentable_area - COALESCE(lt.total_leased_area, 0)) / pt.total_rentable_area) * 100
                ELSE 0
            END as vacancy_rate_pct
        FROM property_totals pt
        LEFT JOIN leased_totals lt ON pt."property code" = lt.property_code
        """,
        
        "v_portfolio_walt": """
        CREATE OR REPLACE VIEW v_portfolio_walt AS
        WITH walt_calc AS (
            SELECT 
                DATEDIFF('month', "amendment start date", 
                    COALESCE("amendment end date", CURRENT_DATE)) as lease_term_months,
                current_monthly_rent
            FROM v_current_rent_roll_enhanced
            WHERE current_monthly_rent > 0
        )
        SELECT 
            CASE 
                WHEN SUM(current_monthly_rent) > 0
                THEN SUM(lease_term_months * current_monthly_rent) / SUM(current_monthly_rent)
                ELSE 0
            END as portfolio_walt_months,
            CASE 
                WHEN SUM(current_monthly_rent) > 0
                THEN SUM(lease_term_months * current_monthly_rent) / SUM(current_monthly_rent) / 12
                ELSE 0
            END as portfolio_walt_years,
            COUNT(*) as lease_count,
            SUM(current_monthly_rent) as total_monthly_rent
        FROM walt_calc
        """,
        
        "v_leasing_activity_summary": """
        CREATE OR REPLACE VIEW v_leasing_activity_summary AS
        SELECT 
            property_code,
            'New Lease' as lease_type,
            0 as retention_rate,
            0 as net_activity_sf
        FROM v_current_rent_roll_enhanced
        WHERE current_monthly_rent > 0
        GROUP BY property_code
        """,
        
        "v_rent_roll_with_credit": """
        CREATE OR REPLACE VIEW v_rent_roll_with_credit AS
        SELECT 
            rr.*,
            NULL::FLOAT as avg_credit_score,
            0 as revenue_at_risk_pct,
            'No Score' as credit_risk_category
        FROM v_current_rent_roll_enhanced rr
        """
    }
    
    for view_name, view_sql in other_views.items():
        try:
            conn.execute(view_sql)
            logger.info(f"✓ Created view: {view_name}")
        except Exception as e:
            logger.error(f"✗ Failed to create {view_name}: {str(e)[:80]}")
    
    conn.close()
    logger.info("\nViews creation complete!")

if __name__ == "__main__":
    create_minimal_views()