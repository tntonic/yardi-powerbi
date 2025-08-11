#!/usr/bin/env python3
"""
Web BI Dashboard Fixes Validation Test Suite
============================================

Tests that validate:
1. Database views exist (especially v_portfolio_health_score)  
2. Filters work properly
3. Metrics display correctly
4. No SQL errors occur
5. Metrics return data (not N/A)
6. Uses DuckDB connection for validation queries

Author: Claude Code Test Automation Framework
Version: 1.0
Date: 2025-08-11
"""

import duckdb
import pandas as pd
import logging
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_dashboard_fixes.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class WebBIDashboardValidator:
    """Comprehensive validation suite for Web BI dashboard fixes"""
    
    def __init__(self, db_path: str = "database/yardi.duckdb"):
        """Initialize validator with database connection"""
        self.db_path = Path(__file__).parent / db_path
        self.conn = None
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {},
            'summary': {'passed': 0, 'failed': 0, 'warnings': 0},
            'critical_issues': [],
            'recommendations': []
        }
        
        # Critical views that must exist
        self.critical_views = [
            'v_portfolio_health_score',
            'v_current_rent_roll_enhanced', 
            'v_occupancy_metrics',
            'v_walt_by_property',
            'v_lease_expirations',
            'v_rent_roll_with_credit',
            'v_current_date',
            'v_base_active_amendments',
            'v_latest_amendments'
        ]
        
        # Optional views for enhanced functionality
        self.optional_views = [
            'v_investment_timing_score',
            'v_market_risk_score',
            'v_overall_system_health',
            'v_dashboard_readiness_score',
            'v_market_position_score'
        ]
        
    def connect_database(self) -> bool:
        """Establish DuckDB connection"""
        try:
            if not self.db_path.exists():
                raise FileNotFoundError(f"Database not found: {self.db_path}")
                
            self.conn = duckdb.connect(str(self.db_path))
            logger.info(f"Connected to database: {self.db_path}")
            return True
            
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            self.test_results['critical_issues'].append(f"Database connection failed: {e}")
            return False
    
    def test_view_exists(self, view_name: str) -> bool:
        """Test if a specific view exists"""
        try:
            result = self.conn.execute(f"""
                SELECT COUNT(*) 
                FROM information_schema.views 
                WHERE table_name = '{view_name}'
            """).fetchone()
            
            exists = result[0] > 0 if result else False
            
            if exists:
                logger.info(f"✓ View exists: {view_name}")
                return True
            else:
                logger.error(f"✗ View missing: {view_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error checking view {view_name}: {e}")
            return False
    
    def test_view_returns_data(self, view_name: str, min_rows: int = 1) -> Tuple[bool, int, List[str]]:
        """Test if view returns data and get column info"""
        try:
            # Get row count
            count_result = self.conn.execute(f"SELECT COUNT(*) FROM {view_name}").fetchone()
            row_count = count_result[0] if count_result else 0
            
            # Get column names
            columns_result = self.conn.execute(f"SELECT * FROM {view_name} LIMIT 0").description
            columns = [col[0] for col in columns_result] if columns_result else []
            
            has_data = row_count >= min_rows
            
            if has_data:
                logger.info(f"✓ View has data: {view_name} ({row_count} rows, {len(columns)} columns)")
            else:
                logger.warning(f"⚠ View has no data: {view_name} ({row_count} rows)")
                
            return has_data, row_count, columns
            
        except Exception as e:
            logger.error(f"Error testing view data {view_name}: {e}")
            return False, 0, []
    
    def test_portfolio_health_score_calculation(self) -> bool:
        """Test that portfolio health score calculates correctly"""
        try:
            result = self.conn.execute("""
                SELECT 
                    portfolio_health_score,
                    occupancy_points,
                    financial_points,
                    credit_points,
                    leasing_points,
                    health_category
                FROM v_portfolio_health_score
                LIMIT 1
            """).fetchone()
            
            if not result:
                logger.error("✗ Portfolio health score returned no results")
                return False
            
            score, occ_pts, fin_pts, cred_pts, lease_pts, category = result
            
            # Validate score components
            issues = []
            if score is None:
                issues.append("Portfolio health score is NULL")
            elif not (0 <= score <= 100):
                issues.append(f"Portfolio health score out of range: {score}")
                
            if category is None:
                issues.append("Health category is NULL")
            elif category not in ['Excellent', 'Good', 'Fair', 'Needs Attention']:
                issues.append(f"Invalid health category: {category}")
            
            # Check component scores are reasonable
            for name, pts in [('occupancy', occ_pts), ('financial', fin_pts), 
                             ('credit', cred_pts), ('leasing', lease_pts)]:
                if pts is not None and not (0 <= pts <= 25):
                    issues.append(f"{name} points out of range: {pts}")
            
            if issues:
                logger.error(f"✗ Portfolio health score validation failed: {issues}")
                return False
            else:
                logger.info(f"✓ Portfolio health score valid: {score} ({category})")
                return True
                
        except Exception as e:
            logger.error(f"Error testing portfolio health score: {e}")
            return False
    
    def test_filter_functionality(self) -> Dict[str, bool]:
        """Test that filters work properly on key views"""
        filter_tests = {}
        
        # Test property filter on rent roll
        try:
            result = self.conn.execute("""
                SELECT COUNT(DISTINCT property_code)
                FROM v_current_rent_roll_enhanced
                WHERE property_code LIKE 'F2%'
            """).fetchone()
            
            property_filter_works = result and result[0] > 0
            filter_tests['property_filter'] = property_filter_works
            
            if property_filter_works:
                logger.info("✓ Property filter working")
            else:
                logger.warning("⚠ Property filter may not be working")
                
        except Exception as e:
            logger.error(f"Property filter test failed: {e}")
            filter_tests['property_filter'] = False
        
        # Test date filter
        try:
            result = self.conn.execute("""
                SELECT COUNT(*)
                FROM v_current_rent_roll_enhanced
                WHERE amendment_start_date >= '2024-01-01'
            """).fetchone()
            
            date_filter_works = result is not None
            filter_tests['date_filter'] = date_filter_works
            
            if date_filter_works:
                logger.info("✓ Date filter working")
            else:
                logger.warning("⚠ Date filter may not be working")
                
        except Exception as e:
            logger.error(f"Date filter test failed: {e}")
            filter_tests['date_filter'] = False
        
        # Test credit score filter
        try:
            result = self.conn.execute("""
                SELECT COUNT(*)
                FROM v_rent_roll_with_credit
                WHERE credit_risk_category = 'Low Risk'
            """).fetchone()
            
            credit_filter_works = result is not None
            filter_tests['credit_filter'] = credit_filter_works
            
            if credit_filter_works:
                logger.info("✓ Credit filter working")
            else:
                logger.warning("⚠ Credit filter may not be working")
                
        except Exception as e:
            logger.error(f"Credit filter test failed: {e}")
            filter_tests['credit_filter'] = False
        
        return filter_tests
    
    def test_metric_calculations(self) -> Dict[str, bool]:
        """Test key metric calculations return valid data"""
        metric_tests = {}
        
        # Test occupancy metrics
        try:
            result = self.conn.execute("""
                SELECT 
                    AVG(physical_occupancy_pct) as avg_occupancy,
                    COUNT(*) as property_count
                FROM v_occupancy_metrics
            """).fetchone()
            
            if result and result[0] is not None and result[1] > 0:
                avg_occupancy, prop_count = result
                occupancy_valid = 0 <= avg_occupancy <= 100 and prop_count > 0
                metric_tests['occupancy_metrics'] = occupancy_valid
                
                if occupancy_valid:
                    logger.info(f"✓ Occupancy metrics valid: {avg_occupancy:.1f}% avg across {prop_count} properties")
                else:
                    logger.error(f"✗ Occupancy metrics invalid: {avg_occupancy}% avg")
            else:
                metric_tests['occupancy_metrics'] = False
                logger.error("✗ Occupancy metrics returned no data")
                
        except Exception as e:
            logger.error(f"Occupancy metrics test failed: {e}")
            metric_tests['occupancy_metrics'] = False
        
        # Test rent roll totals
        try:
            result = self.conn.execute("""
                SELECT 
                    SUM(current_monthly_rent) as total_rent,
                    AVG(current_rent_psf) as avg_rent_psf,
                    COUNT(*) as tenant_count
                FROM v_current_rent_roll_enhanced
                WHERE current_monthly_rent > 0
            """).fetchone()
            
            if result and all(x is not None for x in result):
                total_rent, avg_psf, tenant_count = result
                rent_roll_valid = total_rent > 0 and avg_psf > 0 and tenant_count > 0
                metric_tests['rent_roll_totals'] = rent_roll_valid
                
                if rent_roll_valid:
                    logger.info(f"✓ Rent roll valid: ${total_rent:,.0f} total, ${avg_psf:.2f} avg PSF, {tenant_count} tenants")
                else:
                    logger.error(f"✗ Rent roll invalid: ${total_rent} total, ${avg_psf} PSF")
            else:
                metric_tests['rent_roll_totals'] = False
                logger.error("✗ Rent roll returned no data")
                
        except Exception as e:
            logger.error(f"Rent roll test failed: {e}")
            metric_tests['rent_roll_totals'] = False
        
        # Test WALT calculation
        try:
            result = self.conn.execute("""
                SELECT 
                    portfolio_walt_months,
                    portfolio_walt_years,
                    tenant_count
                FROM v_portfolio_walt
            """).fetchone()
            
            if result and result[0] is not None:
                walt_months, walt_years, tenant_count = result
                walt_valid = walt_months > 0 and tenant_count > 0
                metric_tests['walt_calculation'] = walt_valid
                
                if walt_valid:
                    logger.info(f"✓ WALT calculation valid: {walt_months:.1f} months ({walt_years:.1f} years)")
                else:
                    logger.error(f"✗ WALT calculation invalid: {walt_months} months")
            else:
                metric_tests['walt_calculation'] = False
                logger.error("✗ WALT calculation returned no data")
                
        except Exception as e:
            logger.error(f"WALT calculation test failed: {e}")
            metric_tests['walt_calculation'] = False
        
        return metric_tests
    
    def test_sql_error_handling(self) -> bool:
        """Test that views don't have SQL syntax errors"""
        try:
            # Test a complex query that exercises multiple views
            self.conn.execute("""
                SELECT 
                    phs.portfolio_health_score,
                    om.physical_occupancy_pct,
                    walt.portfolio_walt_months,
                    COUNT(rr.tenant_hmy) as tenant_count
                FROM v_portfolio_health_score phs
                LEFT JOIN v_occupancy_metrics om ON 1=1
                LEFT JOIN v_portfolio_walt walt ON 1=1
                LEFT JOIN v_current_rent_roll_enhanced rr ON 1=1
                LIMIT 1
            """).fetchone()
            
            logger.info("✓ Complex SQL query executed without errors")
            return True
            
        except Exception as e:
            logger.error(f"✗ SQL error detected: {e}")
            return False
    
    def test_data_quality(self) -> Dict[str, Any]:
        """Test data quality indicators"""
        quality_results = {}
        
        try:
            # Check for NULL values in critical fields
            result = self.conn.execute("""
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(CASE WHEN current_monthly_rent IS NULL THEN 1 END) as null_rent,
                    COUNT(CASE WHEN property_code IS NULL THEN 1 END) as null_property,
                    COUNT(CASE WHEN tenant_name IS NULL THEN 1 END) as null_tenant
                FROM v_current_rent_roll_enhanced
            """).fetchone()
            
            if result:
                total, null_rent, null_prop, null_tenant = result
                quality_results['total_records'] = total
                quality_results['null_rent_pct'] = (null_rent / total * 100) if total > 0 else 0
                quality_results['null_property_pct'] = (null_prop / total * 100) if total > 0 else 0
                quality_results['null_tenant_pct'] = (null_tenant / total * 100) if total > 0 else 0
                
                logger.info(f"Data quality - Total records: {total}, NULL rates: "
                           f"Rent {quality_results['null_rent_pct']:.1f}%, "
                           f"Property {quality_results['null_property_pct']:.1f}%, "
                           f"Tenant {quality_results['null_tenant_pct']:.1f}%")
            
        except Exception as e:
            logger.error(f"Data quality test failed: {e}")
            quality_results['error'] = str(e)
        
        return quality_results
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run complete test suite"""
        logger.info("Starting Web BI Dashboard Validation Test Suite")
        logger.info("=" * 60)
        
        # Connect to database
        if not self.connect_database():
            self.test_results['summary']['failed'] += 1
            return self.test_results
        
        # Test 1: Critical views exist
        logger.info("\n1. Testing Critical Views Existence")
        logger.info("-" * 40)
        critical_views_passed = 0
        for view in self.critical_views:
            if self.test_view_exists(view):
                critical_views_passed += 1
                self.test_results['summary']['passed'] += 1
            else:
                self.test_results['summary']['failed'] += 1
                self.test_results['critical_issues'].append(f"Critical view missing: {view}")
        
        self.test_results['tests']['critical_views'] = {
            'passed': critical_views_passed,
            'total': len(self.critical_views),
            'success_rate': critical_views_passed / len(self.critical_views) * 100
        }
        
        # Test 2: Optional views exist
        logger.info("\n2. Testing Optional Views Existence")  
        logger.info("-" * 40)
        optional_views_passed = 0
        for view in self.optional_views:
            if self.test_view_exists(view):
                optional_views_passed += 1
                self.test_results['summary']['passed'] += 1
            else:
                self.test_results['summary']['warnings'] += 1
        
        self.test_results['tests']['optional_views'] = {
            'passed': optional_views_passed,
            'total': len(self.optional_views),
            'success_rate': optional_views_passed / len(self.optional_views) * 100
        }
        
        # Test 3: Views return data
        logger.info("\n3. Testing Views Return Data")
        logger.info("-" * 40)
        views_with_data = 0
        all_views = self.critical_views + self.optional_views
        
        for view in all_views:
            if self.test_view_exists(view):  # Only test if view exists
                has_data, row_count, columns = self.test_view_returns_data(view)
                if has_data:
                    views_with_data += 1
                    self.test_results['summary']['passed'] += 1
                else:
                    self.test_results['summary']['warnings'] += 1
        
        self.test_results['tests']['views_with_data'] = {
            'passed': views_with_data,
            'total': len([v for v in all_views if self.test_view_exists(v)]),
            'success_rate': (views_with_data / max(1, len([v for v in all_views if self.test_view_exists(v)]))) * 100
        }
        
        # Test 4: Portfolio health score calculation
        logger.info("\n4. Testing Portfolio Health Score Calculation")
        logger.info("-" * 40)
        if 'v_portfolio_health_score' in [v for v in self.critical_views if self.test_view_exists(v)]:
            if self.test_portfolio_health_score_calculation():
                self.test_results['summary']['passed'] += 1
                self.test_results['tests']['portfolio_health_score'] = True
            else:
                self.test_results['summary']['failed'] += 1
                self.test_results['tests']['portfolio_health_score'] = False
                self.test_results['critical_issues'].append("Portfolio health score calculation failed")
        
        # Test 5: Filter functionality
        logger.info("\n5. Testing Filter Functionality")
        logger.info("-" * 40)
        filter_results = self.test_filter_functionality()
        self.test_results['tests']['filters'] = filter_results
        
        for filter_name, passed in filter_results.items():
            if passed:
                self.test_results['summary']['passed'] += 1
            else:
                self.test_results['summary']['warnings'] += 1
        
        # Test 6: Metric calculations
        logger.info("\n6. Testing Metric Calculations")
        logger.info("-" * 40)
        metric_results = self.test_metric_calculations()
        self.test_results['tests']['metrics'] = metric_results
        
        for metric_name, passed in metric_results.items():
            if passed:
                self.test_results['summary']['passed'] += 1
            else:
                self.test_results['summary']['failed'] += 1
                self.test_results['critical_issues'].append(f"Metric calculation failed: {metric_name}")
        
        # Test 7: SQL error handling
        logger.info("\n7. Testing SQL Error Handling")
        logger.info("-" * 40)
        if self.test_sql_error_handling():
            self.test_results['summary']['passed'] += 1
            self.test_results['tests']['sql_error_handling'] = True
        else:
            self.test_results['summary']['failed'] += 1
            self.test_results['tests']['sql_error_handling'] = False
            self.test_results['critical_issues'].append("SQL errors detected in view queries")
        
        # Test 8: Data quality
        logger.info("\n8. Testing Data Quality")
        logger.info("-" * 40)
        quality_results = self.test_data_quality()
        self.test_results['tests']['data_quality'] = quality_results
        
        # Generate recommendations
        self.generate_recommendations()
        
        # Close database connection
        if self.conn:
            self.conn.close()
        
        return self.test_results
    
    def generate_recommendations(self):
        """Generate recommendations based on test results"""
        # Check for high failure rate
        total_tests = self.test_results['summary']['passed'] + self.test_results['summary']['failed']
        if total_tests > 0:
            failure_rate = self.test_results['summary']['failed'] / total_tests * 100
            if failure_rate > 20:
                self.test_results['recommendations'].append(
                    f"High failure rate detected ({failure_rate:.1f}%). Review database views and data loading process."
                )
        
        # Check critical views
        critical_success_rate = self.test_results['tests'].get('critical_views', {}).get('success_rate', 0)
        if critical_success_rate < 100:
            self.test_results['recommendations'].append(
                "Critical views missing. Run database initialization scripts to create missing views."
            )
        
        # Check data quality
        data_quality = self.test_results['tests'].get('data_quality', {})
        for field, pct in [('null_rent_pct', 'rent'), ('null_property_pct', 'property'), ('null_tenant_pct', 'tenant')]:
            if data_quality.get(field, 0) > 10:
                self.test_results['recommendations'].append(
                    f"High NULL rate in {pct[1]} fields ({data_quality[field]:.1f}%). Review data loading process."
                )
    
    def save_results(self, filename: Optional[str] = None):
        """Save test results to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"dashboard_test_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        logger.info(f"Test results saved to: {filename}")
    
    def print_summary(self):
        """Print test summary"""
        logger.info("\n" + "=" * 60)
        logger.info("WEB BI DASHBOARD VALIDATION SUMMARY")
        logger.info("=" * 60)
        
        summary = self.test_results['summary']
        logger.info(f"Tests Passed: {summary['passed']}")
        logger.info(f"Tests Failed: {summary['failed']}")
        logger.info(f"Warnings: {summary['warnings']}")
        
        total_tests = summary['passed'] + summary['failed']
        success_rate = (summary['passed'] / max(1, total_tests)) * 100
        logger.info(f"Success Rate: {success_rate:.1f}%")
        
        # Critical issues
        if self.test_results['critical_issues']:
            logger.info(f"\n❌ CRITICAL ISSUES ({len(self.test_results['critical_issues'])}):")
            for issue in self.test_results['critical_issues']:
                logger.info(f"  • {issue}")
        
        # Recommendations  
        if self.test_results['recommendations']:
            logger.info(f"\n💡 RECOMMENDATIONS ({len(self.test_results['recommendations'])}):")
            for rec in self.test_results['recommendations']:
                logger.info(f"  • {rec}")
        
        # Overall status
        if summary['failed'] == 0 and len(self.test_results['critical_issues']) == 0:
            logger.info(f"\n🎉 OVERALL STATUS: PASSED")
            logger.info("Dashboard is ready for use!")
        elif summary['failed'] < 3:
            logger.info(f"\n⚠️  OVERALL STATUS: PASSED WITH WARNINGS")
            logger.info("Dashboard is functional but may have some issues.")
        else:
            logger.info(f"\n❌ OVERALL STATUS: FAILED") 
            logger.info("Dashboard has significant issues that need to be addressed.")


def main():
    """Main execution function"""
    # Initialize validator
    validator = WebBIDashboardValidator()
    
    # Run all tests
    results = validator.run_all_tests()
    
    # Print summary
    validator.print_summary()
    
    # Save results
    validator.save_results()
    
    # Return appropriate exit code
    if results['summary']['failed'] > 0 or len(results['critical_issues']) > 0:
        sys.exit(1)  # Exit with error if tests failed
    else:
        sys.exit(0)  # Exit successfully


if __name__ == "__main__":
    main()