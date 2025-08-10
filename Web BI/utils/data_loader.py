#!/usr/bin/env python3
"""
Data Loading Utilities
Helper functions for loading and processing Yardi data
"""

import pandas as pd
import duckdb
import os
from pathlib import Path
import logging
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class YardiDataLoader:
    """Utility class for loading Yardi CSV data into DuckDB"""
    
    def __init__(self, data_path: str, db_path: str):
        self.data_path = Path(data_path)
        self.db_path = Path(db_path)
        self.conn = None
        
    def connect(self):
        """Establish database connection"""
        self.conn = duckdb.connect(str(self.db_path))
        logger.info(f"Connected to database: {self.db_path}")
        
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            
    def get_csv_files(self) -> List[Path]:
        """Get list of CSV files to load"""
        csv_files = list(self.data_path.glob("*.csv"))
        
        # Filter out cleaned versions if original exists
        filtered_files = []
        for csv_file in csv_files:
            if "_cleaned" in csv_file.stem:
                original = self.data_path / f"{csv_file.stem.replace('_cleaned', '')}.csv"
                if not original.exists():
                    filtered_files.append(csv_file)
            else:
                filtered_files.append(csv_file)
                
        return filtered_files
    
    def load_csv_to_table(self, csv_file: Path) -> bool:
        """Load single CSV file to DuckDB table"""
        table_name = csv_file.stem.lower()
        
        try:
            # Use DuckDB's CSV auto-detection
            query = f"""
            CREATE OR REPLACE TABLE {table_name} AS 
            SELECT * FROM read_csv_auto('{csv_file}', 
                header=true,
                sample_size=10000,
                all_varchar=false,
                ignore_errors=true,
                null_padding=true)
            """
            
            self.conn.execute(query)
            
            # Get row count
            count = self.conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            logger.info(f"Loaded {table_name}: {count:,} rows from {csv_file.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading {csv_file.name}: {str(e)}")
            return False
    
    def load_all_csvs(self) -> Dict[str, int]:
        """Load all CSV files and return summary"""
        if not self.conn:
            self.connect()
            
        csv_files = self.get_csv_files()
        results = {}
        
        logger.info(f"Loading {len(csv_files)} CSV files...")
        
        for csv_file in csv_files:
            success = self.load_csv_to_table(csv_file)
            if success:
                count = self.conn.execute(f"SELECT COUNT(*) FROM {csv_file.stem.lower()}").fetchone()[0]
                results[csv_file.stem] = count
            else:
                results[csv_file.stem] = 0
                
        return results
    
    def validate_data_load(self) -> Dict[str, any]:
        """Validate the loaded data"""
        validation_results = {
            "total_tables": 0,
            "total_rows": 0,
            "critical_tables_present": True,
            "issues": []
        }
        
        # Check table count
        tables = self.conn.execute("""
            SELECT table_name, estimated_size 
            FROM duckdb_tables() 
            WHERE schema_name = 'main'
        """).fetchall()
        
        validation_results["total_tables"] = len(tables)
        validation_results["total_rows"] = sum([row[1] for row in tables])
        
        # Check for critical tables
        critical_tables = [
            'dim_fp_amendmentsunitspropertytenant',
            'dim_fp_amendmentchargeschedule', 
            'fact_total',
            'fact_occupancyrentarea',
            'dim_property',
            'dim_commcustomer'
        ]
        
        existing_tables = [row[0] for row in tables]
        
        for table in critical_tables:
            if table not in existing_tables:
                validation_results["critical_tables_present"] = False
                validation_results["issues"].append(f"Missing critical table: {table}")
        
        # Check for empty tables
        for table_name, size in tables:
            if size == 0:
                validation_results["issues"].append(f"Empty table: {table_name}")
        
        return validation_results
    
    def get_data_summary(self) -> pd.DataFrame:
        """Get summary of loaded data"""
        query = """
        SELECT 
            table_name,
            estimated_size as row_count,
            column_count,
            ROUND(total_size / 1024.0 / 1024.0, 2) as size_mb
        FROM duckdb_tables() 
        WHERE schema_name = 'main'
        ORDER BY estimated_size DESC
        """
        
        return self.conn.execute(query).df()

def quick_data_check(data_path: str) -> Dict[str, any]:
    """Quick check of CSV data without loading to database"""
    data_dir = Path(data_path)
    
    if not data_dir.exists():
        return {"error": f"Data directory not found: {data_path}"}
    
    csv_files = list(data_dir.glob("*.csv"))
    
    summary = {
        "csv_count": len(csv_files),
        "total_size_mb": 0,
        "files": []
    }
    
    for csv_file in csv_files:
        file_size_mb = csv_file.stat().st_size / 1024 / 1024
        summary["total_size_mb"] += file_size_mb
        
        # Quick row count estimate
        try:
            with open(csv_file, 'r') as f:
                line_count = sum(1 for _ in f) - 1  # Subtract header
        except:
            line_count = 0
            
        summary["files"].append({
            "name": csv_file.name,
            "size_mb": round(file_size_mb, 2),
            "estimated_rows": line_count
        })
    
    summary["total_size_mb"] = round(summary["total_size_mb"], 2)
    return summary

if __name__ == "__main__":
    # Example usage
    data_path = "../Data/Yardi_Tables"
    db_path = "database/yardi.duckdb"
    
    # Quick check first
    print("Checking CSV data...")
    summary = quick_data_check(data_path)
    print(f"Found {summary['csv_count']} CSV files, {summary['total_size_mb']}MB total")
    
    # Load data
    loader = YardiDataLoader(data_path, db_path)
    try:
        results = loader.load_all_csvs()
        print(f"\nLoaded {len(results)} tables:")
        for table, rows in results.items():
            print(f"  {table}: {rows:,} rows")
            
        # Validate
        validation = loader.validate_data_load()
        print(f"\nValidation Results:")
        print(f"  Tables: {validation['total_tables']}")
        print(f"  Total Rows: {validation['total_rows']:,}")
        print(f"  Critical Tables Present: {validation['critical_tables_present']}")
        
        if validation["issues"]:
            print("  Issues:")
            for issue in validation["issues"]:
                print(f"    - {issue}")
                
    finally:
        loader.close()