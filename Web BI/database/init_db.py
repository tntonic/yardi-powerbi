#!/usr/bin/env python3
"""
DuckDB Database Initialization Script
Creates and populates the Yardi data warehouse from CSV files
"""

import duckdb
import pandas as pd
import os
from pathlib import Path
import logging
from typing import Dict, List
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class YardiDatabaseInitializer:
    def __init__(self, db_path: str = "yardi.duckdb"):
        """Initialize the database connection"""
        self.db_path = db_path
        self.conn = None
        self.base_path = Path(__file__).parent.parent.parent  # Points to Yardi PowerBI folder
        self.data_path = self.base_path / "Data" / "Yardi_Tables"
        
    def connect(self):
        """Establish database connection"""
        self.conn = duckdb.connect(self.db_path)
        logger.info(f"Connected to database: {self.db_path}")
        
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
            
    def load_csv_files(self):
        """Load all CSV files from the Yardi_Tables directory"""
        csv_files = list(self.data_path.glob("*.csv"))
        logger.info(f"Found {len(csv_files)} CSV files to load")
        
        for csv_file in csv_files:
            table_name = csv_file.stem.lower()
            
            # Skip cleaned versions if original exists
            if "_cleaned" in table_name:
                original_name = table_name.replace("_cleaned", "")
                if (self.data_path / f"{original_name}.csv").exists():
                    logger.info(f"Skipping {table_name} (using original)")
                    continue
            
            try:
                # Create table from CSV
                query = f"""
                CREATE OR REPLACE TABLE {table_name} AS 
                SELECT * FROM read_csv_auto('{csv_file}', 
                    header=true,
                    sample_size=10000,
                    all_varchar=false,
                    ignore_errors=true)
                """
                self.conn.execute(query)
                
                # Get row count
                count = self.conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                logger.info(f"Loaded {table_name}: {count:,} rows")
                
            except Exception as e:
                logger.error(f"Error loading {table_name}: {str(e)}")
                
    def create_indexes(self):
        """Create indexes for better query performance"""
        indexes = [
            # Amendment tables - critical for rent roll
            ("dim_fp_amendmentsunitspropertytenant", ["property_hmy", "tenant_hmy", "amendment_sequence"]),
            ("dim_fp_amendmentsunitspropertytenant", ["amendment_status"]),
            ("dim_fp_amendmentchargeschedule", ["amendment_hmy"]),
            
            # Fact tables
            ("fact_total", ["property_id", "period"]),
            ("fact_total", ["book_id"]),
            ("fact_occupancyrentarea", ["property_id", "period"]),
            
            # Dimension tables
            ("dim_property", ["property_id"]),
            ("dim_commcustomer", ["tenant_hmy"]),
            ("dim_commlease", ["lease_hmy"]),
        ]
        
        for table, columns in indexes:
            try:
                # Check if table exists
                table_exists = self.conn.execute(f"""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_name = '{table}'
                """).fetchone()[0] > 0
                
                if table_exists:
                    for col in columns:
                        # DuckDB doesn't support traditional indexes, but we can create statistics
                        self.conn.execute(f"ANALYZE {table}({col})")
                    logger.info(f"Analyzed columns for {table}: {columns}")
            except Exception as e:
                logger.warning(f"Could not analyze {table}: {str(e)}")
                
    def create_base_views(self):
        """Create base views that replicate critical DAX logic"""
        views = {
            # Latest amendments view - CRITICAL for rent roll accuracy
            "v_latest_amendments": """
                CREATE OR REPLACE VIEW v_latest_amendments AS
                WITH latest_seq AS (
                    SELECT 
                        property_hmy,
                        tenant_hmy,
                        MAX(amendment_sequence) as max_seq
                    FROM dim_fp_amendmentsunitspropertytenant
                    WHERE amendment_status IN ('Activated', 'Superseded')
                    GROUP BY property_hmy, tenant_hmy
                )
                SELECT a.*
                FROM dim_fp_amendmentsunitspropertytenant a
                INNER JOIN latest_seq l 
                    ON a.property_hmy = l.property_hmy 
                    AND a.tenant_hmy = l.tenant_hmy
                    AND a.amendment_sequence = l.max_seq
                WHERE a.amendment_status IN ('Activated', 'Superseded')
            """,
            
            # Current rent roll view
            "v_current_rent_roll": """
                CREATE OR REPLACE VIEW v_current_rent_roll AS
                SELECT 
                    la.*,
                    cs.charge_code,
                    cs.monthly_amount,
                    cs.charge_type,
                    p.property_name,
                    p.property_code,
                    c.customer_name as tenant_name
                FROM v_latest_amendments la
                LEFT JOIN dim_fp_amendmentchargeschedule cs 
                    ON la.hmy = cs.amendment_hmy
                LEFT JOIN dim_property p 
                    ON la.property_hmy = p.property_id
                LEFT JOIN dim_commcustomer c 
                    ON la.tenant_hmy = c.tenant_hmy
            """,
            
            # Financial summary view
            "v_financial_summary": """
                CREATE OR REPLACE VIEW v_financial_summary AS
                SELECT 
                    f.property_id,
                    f.period,
                    f.book_id,
                    p.property_name,
                    p.property_code,
                    -- Revenue (4xxxx accounts stored as negative, multiply by -1)
                    SUM(CASE 
                        WHEN f.account_id LIKE '4%' THEN f.amount * -1 
                        ELSE 0 
                    END) as revenue,
                    -- Operating Expenses (5xxxx accounts)
                    SUM(CASE 
                        WHEN f.account_id LIKE '5%' THEN f.amount 
                        ELSE 0 
                    END) as operating_expenses,
                    -- NOI Calculation
                    SUM(CASE 
                        WHEN f.account_id LIKE '4%' THEN f.amount * -1
                        WHEN f.account_id LIKE '5%' THEN f.amount * -1
                        ELSE 0 
                    END) as noi
                FROM fact_total f
                LEFT JOIN dim_property p ON f.property_id = p.property_id
                GROUP BY f.property_id, f.period, f.book_id, p.property_name, p.property_code
            """,
            
            # Occupancy metrics view
            "v_occupancy_metrics": """
                CREATE OR REPLACE VIEW v_occupancy_metrics AS
                SELECT 
                    o.*,
                    p.property_name,
                    p.property_code,
                    -- Physical Occupancy
                    CASE 
                        WHEN o.rentable_area > 0 
                        THEN (o.occupied_area / o.rentable_area) * 100 
                        ELSE 0 
                    END as physical_occupancy_pct,
                    -- Economic Occupancy
                    CASE 
                        WHEN o.potential_rent > 0 
                        THEN (o.actual_rent / o.potential_rent) * 100 
                        ELSE 0 
                    END as economic_occupancy_pct,
                    -- Vacancy Rate
                    CASE 
                        WHEN o.rentable_area > 0 
                        THEN ((o.rentable_area - o.occupied_area) / o.rentable_area) * 100 
                        ELSE 0 
                    END as vacancy_rate_pct
                FROM fact_occupancyrentarea o
                LEFT JOIN dim_property p ON o.property_id = p.property_id
            """
        }
        
        for view_name, view_sql in views.items():
            try:
                self.conn.execute(view_sql)
                logger.info(f"Created view: {view_name}")
            except Exception as e:
                logger.error(f"Error creating view {view_name}: {str(e)}")
                
    def create_materialized_views(self):
        """Create materialized views for performance-critical queries"""
        mat_views = {
            # Monthly rent roll snapshot
            "mv_monthly_rent_roll": """
                CREATE OR REPLACE TABLE mv_monthly_rent_roll AS
                SELECT 
                    DATE_TRUNC('month', CURRENT_DATE) as snapshot_month,
                    property_code,
                    property_name,
                    COUNT(DISTINCT tenant_hmy) as tenant_count,
                    SUM(CAST(monthly_amount AS DECIMAL(15,2))) as total_monthly_rent,
                    SUM(CAST(leased_area AS DECIMAL(15,2))) as total_leased_sf,
                    AVG(CAST(monthly_amount AS DECIMAL(15,2)) / NULLIF(CAST(leased_area AS DECIMAL(15,2)), 0)) as avg_rent_psf
                FROM v_current_rent_roll
                WHERE charge_code = 'rent'
                GROUP BY property_code, property_name
            """,
            
            # Property performance summary
            "mv_property_performance": """
                CREATE OR REPLACE TABLE mv_property_performance AS
                SELECT 
                    property_id,
                    property_name,
                    property_code,
                    AVG(physical_occupancy_pct) as avg_physical_occupancy,
                    AVG(economic_occupancy_pct) as avg_economic_occupancy,
                    AVG(vacancy_rate_pct) as avg_vacancy_rate,
                    MAX(period) as last_updated
                FROM v_occupancy_metrics
                WHERE period >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '12 months')
                GROUP BY property_id, property_name, property_code
            """
        }
        
        for mv_name, mv_sql in mat_views.items():
            try:
                self.conn.execute(mv_sql)
                count = self.conn.execute(f"SELECT COUNT(*) FROM {mv_name}").fetchone()[0]
                logger.info(f"Created materialized view {mv_name}: {count:,} rows")
            except Exception as e:
                logger.error(f"Error creating materialized view {mv_name}: {str(e)}")
                
    def validate_data_quality(self):
        """Run basic data quality checks"""
        checks = [
            ("Orphaned amendment charges", """
                SELECT COUNT(*) 
                FROM dim_fp_amendmentchargeschedule cs
                WHERE NOT EXISTS (
                    SELECT 1 FROM dim_fp_amendmentsunitspropertytenant a 
                    WHERE a.hmy = cs.amendment_hmy
                )
            """),
            
            ("Properties without names", """
                SELECT COUNT(*) 
                FROM dim_property 
                WHERE property_name IS NULL OR property_name = ''
            """),
            
            ("Amendments without status", """
                SELECT COUNT(*) 
                FROM dim_fp_amendmentsunitspropertytenant 
                WHERE amendment_status IS NULL OR amendment_status = ''
            """),
            
            ("Future dated transactions", """
                SELECT COUNT(*) 
                FROM fact_total 
                WHERE period > CURRENT_DATE
            """)
        ]
        
        logger.info("Running data quality checks...")
        for check_name, check_query in checks:
            try:
                result = self.conn.execute(check_query).fetchone()[0]
                if result > 0:
                    logger.warning(f"{check_name}: {result:,} records found")
                else:
                    logger.info(f"{check_name}: ✓ No issues")
            except Exception as e:
                logger.error(f"Error running check '{check_name}': {str(e)}")
                
    def initialize_database(self):
        """Main initialization routine"""
        try:
            self.connect()
            
            # Load CSV files
            logger.info("=" * 50)
            logger.info("Step 1: Loading CSV files")
            logger.info("=" * 50)
            self.load_csv_files()
            
            # Create indexes/statistics
            logger.info("=" * 50)
            logger.info("Step 2: Creating indexes and statistics")
            logger.info("=" * 50)
            self.create_indexes()
            
            # Create base views
            logger.info("=" * 50)
            logger.info("Step 3: Creating base views")
            logger.info("=" * 50)
            self.create_base_views()
            
            # Create materialized views
            logger.info("=" * 50)
            logger.info("Step 4: Creating materialized views")
            logger.info("=" * 50)
            self.create_materialized_views()
            
            # Validate data quality
            logger.info("=" * 50)
            logger.info("Step 5: Validating data quality")
            logger.info("=" * 50)
            self.validate_data_quality()
            
            # Final summary
            tables = self.conn.execute("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = 'main' AND table_type = 'BASE TABLE'
            """).fetchone()[0]
            
            views = self.conn.execute("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = 'main' AND table_type = 'VIEW'
            """).fetchone()[0]
            
            logger.info("=" * 50)
            logger.info(f"Database initialization complete!")
            logger.info(f"- Tables loaded: {tables}")
            logger.info(f"- Views created: {views}")
            logger.info(f"- Database file: {self.db_path}")
            logger.info("=" * 50)
            
        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
            raise
        finally:
            self.close()

if __name__ == "__main__":
    # Initialize the database
    db = YardiDatabaseInitializer("yardi.duckdb")
    db.initialize_database()