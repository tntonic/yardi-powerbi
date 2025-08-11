#!/usr/bin/env python3
"""
Quick Performance Optimization Runner
=====================================

Simple script to run database performance optimizations with options.
"""

import sys
import os
from pathlib import Path

# Add the database directory to the path
sys.path.append(str(Path(__file__).parent / "database"))

from optimize_performance import YardiPerformanceOptimizer
import logging

def main():
    """Main execution function with command line options"""
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('optimization.log')
        ]
    )
    
    logger = logging.getLogger(__name__)
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help" or sys.argv[1] == "-h":
            print("""
Yardi Performance Optimization Tool
==================================

Usage:
    python run_optimization.py [options]

Options:
    --full          Run complete optimization (default)
    --refresh       Refresh materialized views only
    --analyze       Run performance analysis only
    --summary       Get performance summary only
    --cache-test    Test query caching performance
    --db-path PATH  Use custom database path (default: yardi.duckdb)

Examples:
    python run_optimization.py --full
    python run_optimization.py --refresh
    python run_optimization.py --db-path /path/to/custom.duckdb
    python run_optimization.py --summary
            """)
            return
        
        db_path = "yardi.duckdb"
        operation = "full"
        
        # Parse arguments
        for i, arg in enumerate(sys.argv[1:], 1):
            if arg == "--db-path" and i + 1 < len(sys.argv):
                db_path = sys.argv[i + 1]
            elif arg in ["--full", "--refresh", "--analyze", "--summary", "--cache-test"]:
                operation = arg.replace("--", "")
    else:
        db_path = "yardi.duckdb"
        operation = "full"
    
    # Check if database exists
    if not Path(db_path).exists():
        logger.error(f"Database file not found: {db_path}")
        logger.info("Please run the database initialization first:")
        logger.info("  python database/init_db.py")
        return
    
    # Initialize optimizer
    optimizer = YardiPerformanceOptimizer(db_path)
    
    try:
        if operation == "full":
            logger.info("Running full performance optimization...")
            optimizer.optimize_database()
            
        elif operation == "refresh":
            logger.info("Refreshing materialized views...")
            optimizer.refresh_materialized_views()
            
        elif operation == "analyze":
            logger.info("Running performance analysis...")
            optimizer.connect()
            report = optimizer.run_performance_analysis()
            logger.info(f"Analysis complete. Found {len(report)} metrics.")
            
        elif operation == "summary":
            logger.info("Getting performance summary...")
            summary = optimizer.get_performance_summary()
            
            print("\n" + "="*50)
            print("PERFORMANCE SUMMARY")
            print("="*50)
            
            if 'error' in summary:
                print(f"Error: {summary['error']}")
            else:
                portfolio = summary.get('portfolio_summary', {})
                financial = summary.get('financial_summary', {})
                occupancy = summary.get('occupancy_summary', {})
                cache = summary.get('cache_stats', {})
                
                print(f"Portfolio Overview:")
                print(f"  Properties: {portfolio.get('property_count', 'N/A'):,}")
                print(f"  Tenants: {portfolio.get('tenant_count', 'N/A'):,}")
                print(f"  Monthly Rent: ${portfolio.get('total_monthly_rent', 0):,.0f}")
                print(f"  Leased SF: {portfolio.get('total_leased_sf', 0):,.0f}")
                print(f"  Avg Rent PSF: ${portfolio.get('avg_rent_psf', 0):.2f}")
                
                print(f"\nFinancial Performance:")
                print(f"  Annual Revenue: ${financial.get('portfolio_revenue', 0):,.0f}")
                print(f"  Net Operating Income: ${financial.get('portfolio_noi', 0):,.0f}")
                print(f"  NOI Margin: {financial.get('avg_noi_margin', 0):.1f}%")
                
                print(f"\nOccupancy Metrics:")
                print(f"  Physical Occupancy: {occupancy.get('avg_physical_occupancy', 0):.1f}%")
                print(f"  Economic Occupancy: {occupancy.get('avg_economic_occupancy', 0):.1f}%")
                print(f"  Total Rentable SF: {occupancy.get('total_rentable_sf', 0):,.0f}")
                
                print(f"\nCache Performance:")
                print(f"  Active Entries: {cache.get('active_entries', 0)}")
                print(f"  Cache Status: {'Enabled' if cache.get('active_entries', 0) > 0 else 'Empty'}")
            
        elif operation == "cache-test":
            logger.info("Testing query cache performance...")
            optimizer.connect()
            optimizer.create_cached_query_functions()
            
            import time
            
            # Test cache performance
            print("\nTesting query cache performance...")
            
            # First call (cache miss)
            start_time = time.time()
            result1 = optimizer.get_portfolio_summary(optimizer)
            first_call_time = time.time() - start_time
            
            # Second call (cache hit)  
            start_time = time.time()
            result2 = optimizer.get_portfolio_summary(optimizer)
            second_call_time = time.time() - start_time
            
            print(f"First call (cache miss): {first_call_time:.3f}s")
            print(f"Second call (cache hit): {second_call_time:.3f}s")
            print(f"Speed improvement: {first_call_time/second_call_time:.1f}x faster")
            print(f"Cache working: {'✓' if second_call_time < first_call_time else '✗'}")
            
        logger.info("Operation completed successfully!")
        
    except KeyboardInterrupt:
        logger.info("Operation interrupted by user")
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        sys.exit(1)
    finally:
        if hasattr(optimizer, 'conn') and optimizer.conn:
            optimizer.close()

if __name__ == "__main__":
    main()