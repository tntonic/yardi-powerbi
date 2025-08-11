#!/usr/bin/env python3
"""
Create core views with correct column names for Web BI
Using actual column names from the database
"""

import duckdb
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_core_views(conn):
    """Create essential views with correct column names"""
    
    views = [
        # 1. Latest amendments view - CRITICAL for rent roll accuracy
        ("""
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
        """, "v_latest_amendments"),
        
        # 2. Current date reference
        ("""
            CREATE OR REPLACE VIEW v_current_date AS
            SELECT 
                MAX("last closed period") as current_date,
                MAX("last closed period") as reporting_date
            FROM dim_lastclosedperiod
        """, "v_current_date"),
        
        # 3. Financial summary view
        ("""
            CREATE OR REPLACE VIEW v_financial_summary AS
            SELECT 
                f."property id",
                DATE '1900-01-01' + INTERVAL (f.month - 2) DAY as period,
                f."book id",
                p."property name",
                p."property code",
                -- Revenue (4xxxx accounts stored as negative, multiply by -1)
                SUM(CASE 
                    WHEN CAST(f."account id" AS VARCHAR) LIKE '4%' THEN f.amount * -1 
                    ELSE 0 
                END) as revenue,
                -- Operating Expenses (5xxxx accounts)
                SUM(CASE 
                    WHEN CAST(f."account id" AS VARCHAR) LIKE '5%' THEN f.amount 
                    ELSE 0 
                END) as operating_expenses,
                -- NOI Calculation
                SUM(CASE 
                    WHEN CAST(f."account id" AS VARCHAR) LIKE '4%' THEN f.amount * -1
                    WHEN CAST(f."account id" AS VARCHAR) LIKE '5%' THEN f.amount * -1
                    ELSE 0 
                END) as noi
            FROM fact_total f
            LEFT JOIN dim_property p ON f."property id" = p."property id"
            GROUP BY f."property id", f.month, f."book id", p."property name", p."property code"
        """, "v_financial_summary"),
        
        # 4. Occupancy metrics view (simplified without potential rent)
        ("""
            CREATE OR REPLACE VIEW v_occupancy_metrics AS
            SELECT 
                o."property id",
                o."first day of month" as period_date,
                o."occupied area",
                o."rentable area",
                o."total rent",
                p."property name",
                p."property code",
                -- Physical Occupancy
                CASE 
                    WHEN o."rentable area" > 0 
                    THEN (o."occupied area" / o."rentable area") * 100 
                    ELSE 0 
                END as physical_occupancy_pct,
                -- Vacancy Rate
                CASE 
                    WHEN o."rentable area" > 0 
                    THEN ((o."rentable area" - o."occupied area") / o."rentable area") * 100 
                    ELSE 0 
                END as vacancy_rate_pct,
                -- Vacant SF
                o."rentable area" - o."occupied area" as vacant_sf
            FROM fact_occupancyrentarea o
            LEFT JOIN dim_property p ON o."property id" = p."property id"
        """, "v_occupancy_metrics"),
        
        # 5. Current rent roll with charges
        ("""
            CREATE OR REPLACE VIEW v_current_rent_roll_enhanced AS
            SELECT 
                la."property hmy",
                la."property code",
                la."tenant hmy",
                la."tenant id",
                la."lessee name",
                la."amendment hmy",
                la."amendment sequence",
                la."amendment type",
                la."amendment status",
                la."amendment start date",
                la."amendment end date",
                la."unit number",
                la."amendment sf" as leased_area,
                -- Get monthly rent from charge schedule
                COALESCE(SUM(cs."monthly amount"), 0) as current_monthly_rent,
                COALESCE(SUM(cs."monthly amount"), 0) * 12 as current_annual_rent,
                -- Calculate PSF
                CASE 
                    WHEN la."amendment sf" > 0 AND SUM(cs."monthly amount") > 0
                    THEN (SUM(cs."monthly amount") * 12) / la."amendment sf"
                    ELSE 0
                END as current_rent_psf
            FROM v_latest_amendments la
            LEFT JOIN dim_fp_amendmentchargeschedule cs 
                ON la."amendment hmy" = cs."amendment hmy"
                AND cs."charge code" IN ('RENT', 'BASE RENT', 'MINIMUM RENT', 'BASIC RENT')
            GROUP BY 
                la."property hmy", la."property code", la."tenant hmy", la."tenant id", 
                la."lessee name", la."amendment hmy", la."amendment sequence", 
                la."amendment type", la."amendment status", la."amendment start date", 
                la."amendment end date", la."unit number", la."amendment sf"
        """, "v_current_rent_roll_enhanced"),
        
        # 6. Portfolio WALT calculation
        ("""
            CREATE OR REPLACE VIEW v_portfolio_walt AS
            WITH lease_details AS (
                SELECT 
                    rr.*,
                    CASE 
                        WHEN rr."amendment end date" IS NOT NULL 
                        THEN GREATEST(DATEDIFF('month', CURRENT_DATE, rr."amendment end date"), 0)
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
        """, "v_portfolio_walt"),
        
        # 7. WALT by property
        ("""
            CREATE OR REPLACE VIEW v_walt_by_property AS
            WITH lease_details AS (
                SELECT 
                    rr.*,
                    CASE 
                        WHEN rr."amendment end date" IS NOT NULL 
                        THEN GREATEST(DATEDIFF('month', CURRENT_DATE, rr."amendment end date"), 0)
                        ELSE 36  -- Default for month-to-month
                    END as remaining_term_months
                FROM v_current_rent_roll_enhanced rr
                WHERE rr.current_monthly_rent > 0
            )
            SELECT 
                "property code",
                MAX(p."property name") as property_name,
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
                COUNT(DISTINCT ld."tenant hmy") as tenant_count,
                SUM(current_monthly_rent) as total_monthly_rent,
                SUM(leased_area) as total_leased_sf
            FROM lease_details ld
            LEFT JOIN dim_property p ON ld."property hmy" = p."property id"
            GROUP BY "property code"
        """, "v_walt_by_property"),
        
        # 8. Lease expirations
        ("""
            CREATE OR REPLACE VIEW v_lease_expirations AS
            SELECT 
                -- Expiration period buckets
                CASE 
                    WHEN "amendment end date" IS NULL THEN 'Month-to-Month'
                    WHEN DATEDIFF('month', CURRENT_DATE, "amendment end date") <= 0 THEN 'Expired'
                    WHEN DATEDIFF('month', CURRENT_DATE, "amendment end date") <= 3 THEN '0-3 Months'
                    WHEN DATEDIFF('month', CURRENT_DATE, "amendment end date") <= 6 THEN '4-6 Months'
                    WHEN DATEDIFF('month', CURRENT_DATE, "amendment end date") <= 12 THEN '7-12 Months'
                    WHEN DATEDIFF('month', CURRENT_DATE, "amendment end date") <= 24 THEN '13-24 Months'
                    ELSE '24+ Months'
                END as expiration_bucket,
                "property code",
                "lessee name" as tenant_name,
                "amendment end date",
                leased_area,
                current_monthly_rent,
                current_rent_psf
            FROM v_current_rent_roll_enhanced
            ORDER BY "amendment end date"
        """, "v_lease_expirations"),
        
        # 9. Credit risk integration (simplified without all parent company logic)
        ("""
            CREATE OR REPLACE VIEW v_rent_roll_with_credit AS
            SELECT 
                rr.*,
                cs."credit score",
                cs."annual revenue",
                cs."primary industry",
                cs.ownership,
                cs."customer code",
                -- Credit Risk Category
                CASE 
                    WHEN cs."credit score" >= 8 THEN 'Low Risk'
                    WHEN cs."credit score" >= 6 THEN 'Medium Risk'
                    WHEN cs."credit score" >= 4 THEN 'High Risk'
                    WHEN cs."credit score" IS NOT NULL THEN 'Very High Risk'
                    ELSE 'No Score'
                END as credit_risk_category,
                pm."parent customer hmy",
                parent_cs."customer name" as parent_company_name,
                parent_cs."credit score" as parent_credit_score
            FROM v_current_rent_roll_enhanced rr
            LEFT JOIN dim_commcustomer c ON rr."tenant hmy" = c."customer id"
            LEFT JOIN dim_fp_customercreditscorecustomdata cs 
                ON c."customer id" = cs."hmyperson_customer"
            LEFT JOIN dim_fp_customertoparentmap pm 
                ON c."customer id" = pm."customer hmy"
            LEFT JOIN dim_fp_customercreditscorecustomdata parent_cs 
                ON pm."parent customer hmy" = parent_cs."hmyperson_customer"
        """, "v_rent_roll_with_credit"),
        
        # 10. Leasing activity summary
        ("""
            CREATE OR REPLACE VIEW v_leasing_activity_summary AS
            SELECT 
                la."property id",
                DATE_TRUNC('month', la."lease start date") as activity_month,
                p."property name",
                p."property code",
                
                -- New Leases
                COUNT(CASE WHEN la."lease type" = 'New' THEN 1 END) as new_leases_count,
                SUM(CASE WHEN la."lease type" = 'New' THEN la."leased area" ELSE 0 END) as new_leases_sf,
                SUM(CASE WHEN la."lease type" = 'New' THEN la."annual rent" ELSE 0 END) as new_leases_rent,
                
                -- Renewals
                COUNT(CASE WHEN la."lease type" = 'Renewal' THEN 1 END) as renewals_count,
                SUM(CASE WHEN la."lease type" = 'Renewal' THEN la."leased area" ELSE 0 END) as renewals_sf,
                SUM(CASE WHEN la."lease type" = 'Renewal' THEN la."annual rent" ELSE 0 END) as renewals_rent,
                
                -- Terminations
                COUNT(CASE WHEN la."lease type" = 'Termination' THEN 1 END) as terminations_count,
                SUM(CASE WHEN la."lease type" = 'Termination' THEN la."leased area" ELSE 0 END) as terminations_sf,
                SUM(CASE WHEN la."lease type" = 'Termination' THEN la."annual rent" ELSE 0 END) as terminations_rent,
                
                -- Net Leasing Activity
                (COUNT(CASE WHEN la."lease type" IN ('New', 'Renewal') THEN 1 END) - 
                 COUNT(CASE WHEN la."lease type" = 'Termination' THEN 1 END)) as net_activity_count,
                
                (SUM(CASE WHEN la."lease type" IN ('New', 'Renewal') THEN la."leased area" ELSE 0 END) - 
                 SUM(CASE WHEN la."lease type" = 'Termination' THEN la."leased area" ELSE 0 END)) as net_activity_sf,
                
                -- Retention Rate
                CASE
                    WHEN (COUNT(CASE WHEN la."lease type" = 'Renewal' THEN 1 END) + 
                          COUNT(CASE WHEN la."lease type" = 'Termination' THEN 1 END)) > 0
                    THEN COUNT(CASE WHEN la."lease type" = 'Renewal' THEN 1 END) * 100.0 / 
                         (COUNT(CASE WHEN la."lease type" = 'Renewal' THEN 1 END) + 
                          COUNT(CASE WHEN la."lease type" = 'Termination' THEN 1 END))
                    ELSE 0
                END as retention_rate

            FROM fact_leasingactivity la
            LEFT JOIN dim_property p ON la."property id" = p."property id"
            GROUP BY la."property id", DATE_TRUNC('month', la."lease start date"), p."property name", p."property code"
        """, "v_leasing_activity_summary")
    ]
    
    # Create each view
    success_count = 0
    for view_sql, view_name in views:
        try:
            conn.execute(view_sql)
            logger.info(f"✅ Created view: {view_name}")
            success_count += 1
        except Exception as e:
            logger.error(f"❌ Error creating view {view_name}: {str(e)[:200]}")
    
    logger.info(f"\n📊 Summary: {success_count}/{len(views)} views created successfully")
    
    # Test the views
    logger.info("\n🧪 Testing views...")
    tests = [
        ("SELECT COUNT(*) FROM v_latest_amendments", "Latest amendments"),
        ("SELECT COUNT(*) FROM v_current_rent_roll_enhanced", "Rent roll records"),
        ("SELECT AVG(physical_occupancy_pct) FROM v_occupancy_metrics", "Average occupancy"),
        ("SELECT portfolio_walt_months FROM v_portfolio_walt", "Portfolio WALT"),
        ("SELECT SUM(revenue) FROM v_financial_summary WHERE month > 40000", "Total revenue")
    ]
    
    for query, description in tests:
        try:
            result = conn.execute(query).fetchone()
            if result[0] is not None:
                if "occupancy" in description.lower():
                    logger.info(f"  ✅ {description}: {result[0]:.1f}%")
                elif "walt" in description.lower():
                    logger.info(f"  ✅ {description}: {result[0]:.1f} months")
                elif "revenue" in description.lower():
                    logger.info(f"  ✅ {description}: ${result[0]:,.0f}")
                else:
                    logger.info(f"  ✅ {description}: {result[0]:,}")
        except Exception as e:
            logger.warning(f"  ⚠️ Could not test {description}: {str(e)[:100]}")

if __name__ == "__main__":
    logger.info("Creating core views for Web BI...")
    logger.info("=" * 60)
    
    conn = duckdb.connect("database/yardi.duckdb")
    create_core_views(conn)
    conn.close()
    
    logger.info("=" * 60)
    logger.info("✅ Core views created and ready for Web BI!")