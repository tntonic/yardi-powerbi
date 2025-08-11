#!/usr/bin/env python3
"""
Fix column names in SQL views to match actual table structure
The CSV files have column names with spaces, not underscores
"""

import duckdb
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_fixed_views(conn):
    """Create views with correct column names"""
    
    views = {
        # Latest amendments view - CRITICAL for rent roll accuracy
        "v_latest_amendments": """
            CREATE OR REPLACE VIEW v_latest_amendments AS
            WITH latest_seq AS (
                SELECT 
                    "property hmy",
                    "tenant hmy",
                    MAX("amendment sequence") as max_seq
                FROM dim_fp_amendmentsunitspropertytenant
                WHERE "amendment status" IN ('Activated', 'Superseded')
                GROUP BY "property hmy", "tenant hmy"
            )
            SELECT a.*
            FROM dim_fp_amendmentsunitspropertytenant a
            INNER JOIN latest_seq l 
                ON a."property hmy" = l."property hmy" 
                AND a."tenant hmy" = l."tenant hmy"
                AND a."amendment sequence" = l.max_seq
            WHERE a."amendment status" IN ('Activated', 'Superseded')
        """,
        
        # Current rent roll view
        "v_current_rent_roll": """
            CREATE OR REPLACE VIEW v_current_rent_roll AS
            SELECT 
                la.*,
                cs."charge code",
                cs."monthly amount",
                cs."charge type",
                p."property name",
                p."property code",
                c."lessee name" as tenant_name
            FROM v_latest_amendments la
            LEFT JOIN dim_fp_amendmentchargeschedule cs 
                ON la."amendment hmy" = cs."amendment hmy"
            LEFT JOIN dim_property p 
                ON la."property hmy" = p."property id"
            LEFT JOIN dim_commcustomer c 
                ON la."tenant hmy" = c."tenant hmy"
        """,
        
        # Financial summary view
        "v_financial_summary": """
            CREATE OR REPLACE VIEW v_financial_summary AS
            SELECT 
                f."property id",
                f.month as period,
                f."book id",
                p."property name",
                p."property code",
                -- Revenue (4xxxx accounts stored as negative, multiply by -1)
                SUM(CASE 
                    WHEN f."account id" LIKE '4%' THEN f.amount * -1 
                    ELSE 0 
                END) as revenue,
                -- Operating Expenses (5xxxx accounts)
                SUM(CASE 
                    WHEN f."account id" LIKE '5%' THEN f.amount 
                    ELSE 0 
                END) as operating_expenses,
                -- NOI Calculation
                SUM(CASE 
                    WHEN f."account id" LIKE '4%' THEN f.amount * -1
                    WHEN f."account id" LIKE '5%' THEN f.amount * -1
                    ELSE 0 
                END) as noi
            FROM fact_total f
            LEFT JOIN dim_property p ON f."property id" = p."property id"
            GROUP BY f."property id", f.month, f."book id", p."property name", p."property code"
        """,
        
        # Occupancy metrics view
        "v_occupancy_metrics": """
            CREATE OR REPLACE VIEW v_occupancy_metrics AS
            SELECT 
                o.*,
                p."property name",
                p."property code",
                -- Physical Occupancy
                CASE 
                    WHEN o."rentable area" > 0 
                    THEN (o."occupied area" / o."rentable area") * 100 
                    ELSE 0 
                END as physical_occupancy_pct,
                -- Economic Occupancy
                CASE 
                    WHEN o."potential rent" > 0 
                    THEN (o."actual rent" / o."potential rent") * 100 
                    ELSE 0 
                END as economic_occupancy_pct,
                -- Vacancy Rate
                CASE 
                    WHEN o."rentable area" > 0 
                    THEN ((o."rentable area" - o."occupied area") / o."rentable area") * 100 
                    ELSE 0 
                END as vacancy_rate_pct
            FROM fact_occupancyrentarea o
            LEFT JOIN dim_property p ON o."property id" = p."property id"
        """,
        
        # Current date reference
        "v_current_date": """
            CREATE OR REPLACE VIEW v_current_date AS
            SELECT 
                MAX("last closed period") as current_date,
                MAX("last closed period") as reporting_date
            FROM dim_lastclosedperiod
        """,
        
        # Base active amendments
        "v_base_active_amendments": """
            CREATE OR REPLACE VIEW v_base_active_amendments AS
            WITH current_date_ref AS (
                SELECT current_date FROM v_current_date
            )
            SELECT 
                a.*,
                p."property name",
                p."property code",
                c."lessee name" as tenant_name,
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
            LEFT JOIN dim_commcustomer c ON a."tenant hmy" = c."tenant hmy"
            WHERE 
                a."amendment status" IN ('Activated', 'Superseded')
                AND a."amendment type" NOT IN ('Termination', 'Proposal in DM', 'Modification')
                AND a."amendment start date" <= cd.current_date
                AND (a."amendment end date" >= cd.current_date OR a."amendment end date" IS NULL)
        """,
        
        # Enhanced rent roll with charges
        "v_current_rent_roll_enhanced": """
            CREATE OR REPLACE VIEW v_current_rent_roll_enhanced AS
            WITH latest_amendments AS (
                SELECT 
                    la.*,
                    cs."charge code",
                    cs."monthly amount",
                    -- Calculate monthly amount based on frequency
                    CASE cs."charge frequency"
                        WHEN 'Monthly' THEN cs."monthly amount"
                        WHEN 'Annually' THEN cs."monthly amount" / 12
                        WHEN 'Quarterly' THEN cs."monthly amount" / 3
                        WHEN 'Semi-Annually' THEN cs."monthly amount" / 6
                        ELSE cs."monthly amount"
                    END as monthly_charge_amount
                FROM v_latest_amendments la
                LEFT JOIN dim_fp_amendmentchargeschedule cs 
                    ON la."amendment hmy" = cs."amendment hmy"
                WHERE 
                    cs."charge code" IN ('RENT', 'BASE RENT', 'MINIMUM RENT', 'BASIC RENT')
                    OR cs."charge code" IS NULL
            )
            SELECT 
                "property hmy",
                "property code",
                "tenant hmy",
                "tenant id",
                "lessee name",
                "amendment hmy",
                "amendment sequence",
                "amendment type",
                "amendment status",
                "amendment start date",
                "amendment end date",
                "unit number",
                "amendment sf" as leased_area,
                SUM(monthly_charge_amount) as current_monthly_rent,
                SUM(monthly_charge_amount) * 12 as current_annual_rent,
                CASE 
                    WHEN "amendment sf" > 0 
                    THEN (SUM(monthly_charge_amount) * 12) / "amendment sf"
                    ELSE 0
                END as current_rent_psf
            FROM latest_amendments
            GROUP BY 
                "property hmy", "property code", "tenant hmy", "tenant id", "lessee name",
                "amendment hmy", "amendment sequence", "amendment type",
                "amendment status", "amendment start date", "amendment end date",
                "unit number", "amendment sf"
        """,
        
        # WALT calculation
        "v_portfolio_walt": """
            CREATE OR REPLACE VIEW v_portfolio_walt AS
            WITH lease_details AS (
                SELECT 
                    rr.*,
                    CASE 
                        WHEN rr."amendment end date" IS NOT NULL 
                        THEN DATEDIFF('month', CURRENT_DATE, rr."amendment end date")
                        ELSE 36  -- Default for month-to-month
                    END as remaining_term_months
                FROM v_current_rent_roll_enhanced rr
                WHERE rr.current_monthly_rent > 0
            )
            SELECT 
                -- Portfolio-wide WALT
                CASE 
                    WHEN SUM(current_monthly_rent) > 0
                    THEN SUM(remaining_term_months * current_monthly_rent) / SUM(current_monthly_rent)
                    ELSE 0
                END as portfolio_walt_months,
                -- Convert to years
                CASE 
                    WHEN SUM(current_monthly_rent) > 0
                    THEN SUM(remaining_term_months * current_monthly_rent) / SUM(current_monthly_rent) / 12
                    ELSE 0
                END as portfolio_walt_years,
                -- Supporting metrics
                COUNT(DISTINCT "property hmy") as property_count,
                COUNT(DISTINCT "tenant hmy") as tenant_count,
                SUM(current_monthly_rent) as total_monthly_rent,
                SUM(leased_area) as total_leased_sf
            FROM lease_details
        """,
        
        # WALT by property
        "v_walt_by_property": """
            CREATE OR REPLACE VIEW v_walt_by_property AS
            WITH lease_details AS (
                SELECT 
                    rr.*,
                    CASE 
                        WHEN rr."amendment end date" IS NOT NULL 
                        THEN DATEDIFF('month', CURRENT_DATE, rr."amendment end date")
                        ELSE 36  -- Default for month-to-month
                    END as remaining_term_months
                FROM v_current_rent_roll_enhanced rr
                WHERE rr.current_monthly_rent > 0
            )
            SELECT 
                "property code",
                -- WALT weighted by monthly rent
                CASE 
                    WHEN SUM(current_monthly_rent) > 0
                    THEN SUM(remaining_term_months * current_monthly_rent) / SUM(current_monthly_rent)
                    ELSE 0
                END as walt_months,
                -- Convert to years
                CASE 
                    WHEN SUM(current_monthly_rent) > 0
                    THEN SUM(remaining_term_months * current_monthly_rent) / SUM(current_monthly_rent) / 12
                    ELSE 0
                END as walt_years,
                -- Supporting metrics
                COUNT(DISTINCT "tenant hmy") as tenant_count,
                SUM(current_monthly_rent) as total_monthly_rent,
                SUM(leased_area) as total_leased_sf,
                AVG(remaining_term_months) as avg_lease_term_months
            FROM lease_details
            GROUP BY "property code"
        """,
        
        # Lease expirations
        "v_lease_expirations": """
            CREATE OR REPLACE VIEW v_lease_expirations AS
            WITH current_date_ref AS (
                SELECT current_date FROM v_current_date
            )
            SELECT 
                -- Expiration period buckets
                CASE 
                    WHEN "amendment end date" IS NULL THEN 'Month-to-Month'
                    WHEN DATEDIFF('month', cd.current_date, "amendment end date") <= 0 THEN 'Expired'
                    WHEN DATEDIFF('month', cd.current_date, "amendment end date") <= 3 THEN '0-3 Months'
                    WHEN DATEDIFF('month', cd.current_date, "amendment end date") <= 6 THEN '4-6 Months'
                    WHEN DATEDIFF('month', cd.current_date, "amendment end date") <= 12 THEN '7-12 Months'
                    WHEN DATEDIFF('month', cd.current_date, "amendment end date") <= 24 THEN '13-24 Months'
                    ELSE '24+ Months'
                END as expiration_bucket,
                "property code",
                "lessee name" as tenant_name,
                "amendment end date",
                leased_area,
                current_monthly_rent,
                current_rent_psf
            FROM v_current_rent_roll_enhanced
            CROSS JOIN current_date_ref cd
            ORDER BY "amendment end date"
        """
    }
    
    # Create each view
    for view_name, view_sql in views.items():
        try:
            conn.execute(view_sql)
            logger.info(f"✅ Created view: {view_name}")
        except Exception as e:
            logger.error(f"❌ Error creating view {view_name}: {str(e)}")
    
    # Test the views
    try:
        # Test rent roll
        result = conn.execute("SELECT COUNT(*) FROM v_current_rent_roll_enhanced").fetchone()
        logger.info(f"📊 Rent roll records: {result[0]:,}")
        
        # Test occupancy
        result = conn.execute("SELECT AVG(physical_occupancy_pct) FROM v_occupancy_metrics").fetchone()
        if result[0]:
            logger.info(f"📊 Average occupancy: {result[0]:.1f}%")
        
        # Test WALT
        result = conn.execute("SELECT portfolio_walt_months FROM v_portfolio_walt").fetchone()
        if result[0]:
            logger.info(f"📊 Portfolio WALT: {result[0]:.1f} months")
        
    except Exception as e:
        logger.warning(f"Could not test views: {str(e)}")

if __name__ == "__main__":
    logger.info("Fixing column names in SQL views...")
    conn = duckdb.connect("database/yardi.duckdb")
    create_fixed_views(conn)
    conn.close()
    logger.info("✅ Views fixed and ready!")