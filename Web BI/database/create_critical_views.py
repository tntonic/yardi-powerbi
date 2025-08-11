#!/usr/bin/env python3
"""
Create Critical Views for Web BI Dashboard
Manually creates the essential views with correct column names
"""

import duckdb
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_critical_views(db_path: str = "yardi.duckdb"):
    """Create the most critical views needed for the dashboard"""
    conn = duckdb.connect(db_path)
    
    views_sql = {
        # 1. Current Date View (already works)
        "v_current_date": """
        CREATE OR REPLACE VIEW v_current_date AS
        SELECT 
            MAX("last closed period") as current_date,
            MAX("last closed period") as reporting_date
        FROM dim_lastclosedperiod
        """,
        
        # 2. Base Active Amendments (foundation)
        "v_base_active_amendments": """
        CREATE OR REPLACE VIEW v_base_active_amendments AS
        WITH current_date_ref AS (
            SELECT current_date FROM v_current_date
        )
        SELECT 
            a.*,
            p."property name",
            p."property code",
            t."lessee name" as tenant_name,
            t."tenant code",
            -- Calculate lease term in months
            CASE 
                WHEN a."amendment end date" IS NOT NULL 
                THEN DATEDIFF('month', a."amendment start date", a."amendment end date")
                ELSE DATEDIFF('month', a."amendment start date", cd.current_date)
            END as lease_term_months,
            -- Month-to-month flag
            CASE 
                WHEN a."amendment end date" IS NULL THEN 1
                WHEN DATEDIFF('month', a."amendment start date", a."amendment end date") <= 1 THEN 1
                ELSE 0
            END as is_month_to_month
        FROM dim_fp_amendmentsunitspropertytenant a
        CROSS JOIN current_date_ref cd
        LEFT JOIN dim_property p ON a."property hmy" = p."property id"
        LEFT JOIN dim_commcustomer t ON a."tenant hmy" = t."tenant id"
        WHERE 
            -- Critical status filtering for accuracy
            a."amendment status" IN ('Activated', 'Superseded')
            -- Exclude certain amendment types
            AND a."amendment type" NOT IN ('Termination', 'Proposal in DM', 'Modification')
            -- Date filtering
            AND a."amendment start date" <= cd.current_date
            AND (a."amendment end date" >= cd.current_date OR a."amendment end date" IS NULL)
        """,
        
        # 3. Latest Amendments (prevents double-counting)
        "v_latest_amendments": """
        CREATE OR REPLACE VIEW v_latest_amendments AS
        WITH max_sequences AS (
            SELECT 
                "property hmy",
                "tenant hmy",
                MAX("amendment sequence") as max_sequence
            FROM v_base_active_amendments
            GROUP BY "property hmy", "tenant hmy"
        )
        SELECT 
            a.*
        FROM v_base_active_amendments a
        INNER JOIN max_sequences ms 
            ON a."property hmy" = ms."property hmy" 
            AND a."tenant hmy" = ms."tenant hmy"
            AND a."amendment sequence" = ms.max_sequence
        """,
        
        # 4. Latest Amendments with Charges
        "v_latest_amendments_with_charges": """
        CREATE OR REPLACE VIEW v_latest_amendments_with_charges AS
        SELECT 
            la.*,
            cs."charge code",
            cs."amount",
            cs."amount period desc" as charge_frequency,
            cs."monthly amount",
            -- Use monthly amount directly or calculate from amount
            CASE 
                WHEN cs."monthly amount" IS NOT NULL AND cs."monthly amount" > 0 THEN cs."monthly amount"
                WHEN cs."amount period desc" = 'Monthly' THEN cs."amount"
                WHEN cs."amount period desc" = 'Annually' THEN cs."amount" / 12
                WHEN cs."amount period desc" = 'Quarterly' THEN cs."amount" / 3
                WHEN cs."amount period desc" = 'Semi-Annually' THEN cs."amount" / 6
                ELSE COALESCE(cs."amount", 0)
            END as monthly_charge_amount
        FROM v_latest_amendments la
        LEFT JOIN dim_fp_amendmentchargeschedule cs 
            ON la."amendment hmy" = cs."amendment hmy"
        WHERE 
            -- Only rent-related charges
            cs."charge code" IN ('RENT', 'BASE RENT', 'MINIMUM RENT', 'BASIC RENT', 'rent')
            OR cs."charge code" IS NULL
        """,
        
        # 5. Current Rent Roll Enhanced (critical for dashboard)
        "v_current_rent_roll_enhanced": """
        CREATE OR REPLACE VIEW v_current_rent_roll_enhanced AS
        SELECT 
            lac."property hmy",
            lac."property code",
            lac."property name",
            lac."tenant hmy",
            lac."tenant code",
            lac.tenant_name,
            lac."amendment hmy",
            lac."amendment sequence",
            lac."amendment type",
            lac."amendment status",
            lac."amendment start date",
            lac."amendment end date",
            lac.lease_term_months,
            lac.is_month_to_month,
            lac."unit number",
            lac."leased area",
            -- Aggregate monthly charges
            SUM(lac.monthly_charge_amount) as current_monthly_rent,
            -- Calculate annual rent
            SUM(lac.monthly_charge_amount) * 12 as current_annual_rent,
            -- Calculate PSF if area available
            CASE 
                WHEN lac."leased area" > 0 
                THEN (SUM(lac.monthly_charge_amount) * 12) / lac."leased area"
                ELSE 0
            END as current_rent_psf
        FROM v_latest_amendments_with_charges lac
        GROUP BY 
            lac."property hmy", lac."property code", lac."property name",
            lac."tenant hmy", lac."tenant code", lac.tenant_name,
            lac."amendment hmy", lac."amendment sequence", lac."amendment type",
            lac."amendment status", lac."amendment start date", lac."amendment end date",
            lac.lease_term_months, lac.is_month_to_month,
            lac."unit number", lac."leased area"
        """,
        
        # 6. Occupancy Metrics
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
                "property hmy",
                SUM("leased area") as total_leased_area,
                SUM(current_monthly_rent) as total_monthly_rent
            FROM v_current_rent_roll_enhanced
            GROUP BY "property hmy"
        )
        SELECT 
            pt."property code",
            pt."property name",
            pt.total_rentable_area,
            COALESCE(lt.total_leased_area, 0) as total_leased_area,
            COALESCE(lt.total_monthly_rent, 0) as total_monthly_rent,
            -- Physical Occupancy
            CASE 
                WHEN pt.total_rentable_area > 0
                THEN (COALESCE(lt.total_leased_area, 0) / pt.total_rentable_area) * 100
                ELSE 0
            END as physical_occupancy_pct,
            -- Vacant SF
            pt.total_rentable_area - COALESCE(lt.total_leased_area, 0) as vacant_sf,
            -- Vacancy Rate
            CASE 
                WHEN pt.total_rentable_area > 0
                THEN ((pt.total_rentable_area - COALESCE(lt.total_leased_area, 0)) / pt.total_rentable_area) * 100
                ELSE 0
            END as vacancy_rate_pct
        FROM property_totals pt
        LEFT JOIN leased_totals lt ON pt."property id" = lt."property hmy"
        """,
        
        # 7. Portfolio WALT
        "v_portfolio_walt": """
        CREATE OR REPLACE VIEW v_portfolio_walt AS
        SELECT 
            -- Portfolio-wide WALT
            CASE 
                WHEN SUM(current_monthly_rent) > 0
                THEN SUM(lease_term_months * current_monthly_rent) / SUM(current_monthly_rent)
                ELSE 0
            END as portfolio_walt_months,
            -- Convert to years
            CASE 
                WHEN SUM(current_monthly_rent) > 0
                THEN SUM(lease_term_months * current_monthly_rent) / SUM(current_monthly_rent) / 12
                ELSE 0
            END as portfolio_walt_years,
            -- Supporting metrics
            COUNT(DISTINCT "property hmy") as property_count,
            COUNT(DISTINCT "tenant hmy") as tenant_count,
            SUM(current_monthly_rent) as total_monthly_rent,
            SUM("leased area") as total_leased_sf
        FROM v_current_rent_roll_enhanced
        WHERE current_monthly_rent > 0
        """,
        
        # 8. Leasing Activity Summary (simplified for now)
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
        
        # 9. Rent Roll with Credit (simplified without credit tables for now)
        "v_rent_roll_with_credit": """
        CREATE OR REPLACE VIEW v_rent_roll_with_credit AS
        SELECT 
            rr.*,
            -- Placeholder credit fields
            NULL as credit_score,
            NULL as annual_revenue,
            NULL as primary_industry,
            NULL as ownership,
            tenant_code as customer_code,
            'No Score' as credit_risk_category,
            NULL as parent_customer_hmy,
            NULL as parent_company_name,
            NULL as parent_credit_score
        FROM v_current_rent_roll_enhanced rr
        """
    }
    
    # Create views in order
    created = []
    failed = []
    
    for view_name, view_sql in views_sql.items():
        try:
            conn.execute(view_sql)
            created.append(view_name)
            logger.info(f"✓ Created view: {view_name}")
        except Exception as e:
            failed.append((view_name, str(e)))
            logger.error(f"✗ Failed to create {view_name}: {str(e)[:100]}")
    
    # Verify critical views
    logger.info("\n" + "="*50)
    logger.info("Verification:")
    
    critical_views = [
        'v_current_date',
        'v_base_active_amendments',
        'v_latest_amendments',
        'v_current_rent_roll_enhanced',
        'v_occupancy_metrics',
        'v_portfolio_walt'
    ]
    
    for view_name in critical_views:
        try:
            count = conn.execute(f"SELECT COUNT(*) FROM {view_name}").fetchone()[0]
            logger.info(f"  ✓ {view_name}: {count} rows")
        except Exception as e:
            logger.warning(f"  ✗ {view_name}: {str(e)[:50]}")
    
    # Test the problematic query from the dashboard
    logger.info("\n" + "="*50)
    logger.info("Testing dashboard query:")
    
    test_query = """
    SELECT COUNT(*) 
    FROM v_current_rent_roll_enhanced rr
    JOIN dim_property p ON rr.property_code = p."property code"
    """
    
    try:
        result = conn.execute(test_query).fetchone()[0]
        logger.info(f"✓ Dashboard query works! Found {result} records")
    except Exception as e:
        logger.error(f"✗ Dashboard query failed: {str(e)}")
    
    conn.close()
    
    logger.info("\n" + "="*50)
    logger.info(f"Summary: Created {len(created)} views, {len(failed)} failed")
    
    if failed:
        logger.info("\nFailed views:")
        for name, error in failed:
            logger.info(f"  - {name}: {error[:80]}...")

if __name__ == "__main__":
    create_critical_views()