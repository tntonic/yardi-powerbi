#!/usr/bin/env python3
"""
Fix Column Names in SQL View Definitions
Maps underscored column names to space-separated quoted column names
"""

import duckdb
import re
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ViewColumnFixer:
    def __init__(self, db_path: str = "yardi.duckdb"):
        self.db_path = db_path
        self.conn = duckdb.connect(db_path)
        self.column_mappings = {}
        
    def get_actual_column_names(self):
        """Get actual column names from all tables"""
        tables_query = """
        SELECT DISTINCT table_name 
        FROM information_schema.tables 
        WHERE table_type = 'BASE TABLE'
        """
        
        tables = self.conn.execute(tables_query).fetchall()
        
        for table in tables:
            table_name = table[0]
            cols_query = f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = '{table_name}'
            """
            cols = self.conn.execute(cols_query).fetchall()
            
            self.column_mappings[table_name] = {}
            for col in cols:
                actual_name = col[0]
                # Create mapping from underscore version to actual name
                underscore_name = actual_name.replace(' ', '_').lower()
                self.column_mappings[table_name][underscore_name] = actual_name
                
        logger.info(f"Loaded column mappings for {len(self.column_mappings)} tables")
        
    def fix_sql_content(self, sql_content: str) -> str:
        """Fix column names in SQL content"""
        fixed_sql = sql_content
        
        # First pass: Fix simple column references
        replacements = {
            # dim_lastclosedperiod
            'last_closed_period': '"last closed period"',
            
            # dim_fp_amendmentsunitspropertytenant
            'amendment_hmy': '"amendment hmy"',
            'property_hmy': '"property hmy"',
            'tenant_hmy': '"tenant hmy"',
            'amendment_status': '"amendment status"',
            'amendment_type': '"amendment type"',
            'amendment_sequence': '"amendment sequence"',
            'amendment_start_date': '"amendment start date"',
            'amendment_end_date': '"amendment end date"',
            'leased_area': '"leased area"',
            'unit_number': '"unit number"',
            
            # dim_property - NOTE: uses "property id" not "property hmy"
            'property_id': '"property id"',
            'property_name': '"property name"',
            'property_code': '"property code"',
            'rentable_area': '"rentable area"',
            
            # dim_commcustomer
            'customer_id': '"customer id"',
            'customer_name': '"customer name"',
            'tenant_code': '"tenant code"',
            'lessee_name': '"lessee name"',
            
            # dim_fp_amendmentchargeschedule
            'charge_code': '"charge code"',
            'charge_amount': '"charge amount"',
            'charge_frequency': '"charge frequency"',
            'charge_type': '"charge type"',
            'monthly_amount': '"monthly amount"',
            
            # dim_fp_customercreditscorecustomdata
            'hmyperson_customer': '"hmyperson customer"',
            'credit_score': '"credit score"',
            'annual_revenue': '"annual revenue"',
            'primary_industry': '"primary industry"',
            'customer_code': '"customer code"',
            
            # dim_fp_customertoparentmap
            'customer_hmy': '"customer hmy"',
            'parent_customer_hmy': '"parent customer hmy"',
            
            # fact_total
            'account_id': '"account id"',
            'book_id': '"book id"',
            
            # fact_occupancyrentarea
            'occupied_area': '"occupied area"',
            'potential_rent': '"potential rent"',
            'actual_rent': '"actual rent"',
            'first_day_of_month': '"first day of month"',
            
            # dim_commlease
            'lease_hmy': '"lease hmy"',
            
            # Generic fixes for table aliases
            '.property_hmy': '."property hmy"',
            '.tenant_hmy': '."tenant hmy"',
            '.amendment_hmy': '."amendment hmy"',
            '.amendment_sequence': '."amendment sequence"',
            '.amendment_status': '."amendment status"',
            '.property_id': '."property id"',
            '.property_code': '."property code"',
            '.property_name': '."property name"',
        }
        
        # Apply replacements
        for old, new in replacements.items():
            # Use word boundaries to avoid partial replacements
            pattern = r'\b' + re.escape(old) + r'\b'
            fixed_sql = re.sub(pattern, new, fixed_sql)
        
        # Second pass: Fix join conditions between dim_property and other tables
        # The dim_property table uses "property id" while amendments use "property hmy"
        # We need to be careful about these joins
        fixed_sql = re.sub(
            r'ON\s+a\."property hmy"\s*=\s*p\."property hmy"',
            'ON a."property hmy" = p."property id"',
            fixed_sql
        )
        fixed_sql = re.sub(
            r'ON\s+p\."property hmy"\s*=\s*',
            'ON p."property id" = ',
            fixed_sql
        )
        fixed_sql = re.sub(
            r'p\."property hmy"',
            'p."property id"',
            fixed_sql
        )
        
        # Fix dim_property references in select lists
        fixed_sql = re.sub(
            r'SELECT\s+(.*?)p\."property hmy"',
            r'SELECT \1p."property id"',
            fixed_sql,
            flags=re.DOTALL
        )
            
        return fixed_sql
        
    def fix_view_file(self, file_path: Path) -> str:
        """Fix a single SQL view file"""
        logger.info(f"Fixing {file_path.name}")
        
        with open(file_path, 'r') as f:
            original_content = f.read()
            
        fixed_content = self.fix_sql_content(original_content)
        
        # Save fixed version
        fixed_path = file_path.parent / f"{file_path.stem}_fixed.sql"
        with open(fixed_path, 'w') as f:
            f.write(fixed_content)
            
        logger.info(f"Created fixed version: {fixed_path.name}")
        return fixed_content
        
    def create_views_from_fixed_sql(self, sql_content: str):
        """Execute the fixed SQL to create views"""
        # Split by CREATE OR REPLACE VIEW statements
        view_statements = re.split(r'(?=CREATE OR REPLACE VIEW)', sql_content)
        
        created_views = []
        failed_views = []
        
        for statement in view_statements:
            if not statement.strip() or statement.strip().startswith('--'):
                continue
                
            # Extract view name
            match = re.search(r'CREATE OR REPLACE VIEW\s+(\w+)', statement)
            if not match:
                continue
                
            view_name = match.group(1)
            
            try:
                # Remove comments and clean up
                clean_statement = re.sub(r'/\*.*?\*/', '', statement, flags=re.DOTALL)
                clean_statement = re.sub(r'--.*?$', '', clean_statement, flags=re.MULTILINE)
                
                # Execute only if it's a complete CREATE VIEW statement
                if 'CREATE OR REPLACE VIEW' in clean_statement and 'AS' in clean_statement:
                    # Find the end of the statement (next CREATE or end of string)
                    end_match = re.search(r'(;|$)', clean_statement)
                    if end_match:
                        final_statement = clean_statement[:end_match.end()].strip()
                        if final_statement.endswith(';'):
                            final_statement = final_statement[:-1]
                        
                        self.conn.execute(final_statement)
                        created_views.append(view_name)
                        logger.info(f"✓ Created view: {view_name}")
                        
            except Exception as e:
                failed_views.append((view_name, str(e)))
                logger.error(f"✗ Failed to create {view_name}: {str(e)[:100]}")
                
        return created_views, failed_views
        
    def verify_views(self):
        """Verify that critical views exist"""
        critical_views = [
            'v_current_date',
            'v_base_active_amendments',
            'v_latest_amendments',
            'v_latest_amendments_with_charges',
            'v_current_rent_roll_enhanced',
            'v_occupancy_metrics',
            'v_rent_roll_with_credit'
        ]
        
        logger.info("\nVerifying critical views:")
        for view_name in critical_views:
            exists = self.conn.execute(f"""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_name = '{view_name}'
                AND table_type = 'VIEW'
            """).fetchone()[0] > 0
            
            if exists:
                logger.info(f"  ✓ {view_name} exists")
            else:
                logger.warning(f"  ✗ {view_name} missing")
                
    def run(self):
        """Main execution"""
        logger.info("Starting column name fixing process...")
        
        # Get actual column names
        self.get_actual_column_names()
        
        # Fix SQL files
        sql_files = [
            Path(__file__).parent / "amendment_views.sql",
            Path(__file__).parent / "net_absorption_views.sql",
            Path(__file__).parent / "portfolio_health_views.sql",
        ]
        
        all_created = []
        all_failed = []
        
        for sql_file in sql_files:
            if sql_file.exists():
                logger.info(f"\nProcessing {sql_file.name}...")
                fixed_content = self.fix_view_file(sql_file)
                
                # Try to create views
                created, failed = self.create_views_from_fixed_sql(fixed_content)
                all_created.extend(created)
                all_failed.extend(failed)
            else:
                logger.warning(f"File not found: {sql_file}")
                
        # Summary
        logger.info("\n" + "="*50)
        logger.info(f"Summary:")
        logger.info(f"  Views created: {len(all_created)}")
        logger.info(f"  Views failed: {len(all_failed)}")
        
        if all_failed:
            logger.info("\nFailed views:")
            for view_name, error in all_failed:
                logger.info(f"  - {view_name}: {error[:50]}...")
                
        # Verify critical views
        self.verify_views()
        
        self.conn.close()
        logger.info("\nProcess complete!")

if __name__ == "__main__":
    fixer = ViewColumnFixer()
    fixer.run()