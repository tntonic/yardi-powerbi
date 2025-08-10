#!/usr/bin/env python3
"""
Comprehensive Rent Roll Data Cleaning Script
Handles various Excel formats and standardizes data for analysis
"""

import pandas as pd
import numpy as np
from datetime import datetime
import re
import warnings
import os
from typing import Dict, Optional, Tuple, List

warnings.filterwarnings('ignore')


class RentRollCleaner:
    """Clean and standardize rent roll Excel files."""
    
    def __init__(self, verbose: bool = True):
        """Initialize the cleaner with optional verbose output."""
        self.verbose = verbose
        self.cleaning_stats = {}
        
    def clean_rent_roll(self, file_path: str, output_path: Optional[str] = None) -> pd.DataFrame:
        """
        Main cleaning function that orchestrates all cleaning steps.
        
        Args:
            file_path: Path to the rent roll Excel file
            output_path: Optional path to save cleaned data
            
        Returns:
            Cleaned DataFrame
        """
        if self.verbose:
            print(f"\n{'='*80}")
            print(f"CLEANING RENT ROLL: {os.path.basename(file_path)}")
            print(f"{'='*80}")
        
        # Step 1: Load the data with proper header detection
        df = self._load_excel_with_header_detection(file_path)
        
        # Step 2: Standardize column names
        df = self._standardize_column_names(df)
        
        # Step 3: Extract and clean property information
        df = self._clean_property_data(df)
        
        # Step 4: Clean tenant information
        df = self._clean_tenant_data(df)
        
        # Step 5: Clean and validate numeric fields
        df = self._clean_numeric_fields(df)
        
        # Step 6: Clean and parse date fields
        df = self._clean_date_fields(df)
        
        # Step 7: Standardize status fields
        df = self._standardize_status_fields(df)
        
        # Step 8: Calculate derived fields
        df = self._calculate_derived_fields(df)
        
        # Step 9: Validate data integrity
        df = self._validate_data_integrity(df)
        
        # Step 10: Remove duplicates and sort
        df = self._finalize_dataframe(df)
        
        # Save if output path provided
        if output_path:
            self._save_cleaned_data(df, output_path)
        
        # Print summary
        if self.verbose:
            self._print_cleaning_summary(df)
        
        return df
    
    def _load_excel_with_header_detection(self, file_path: str) -> pd.DataFrame:
        """Load Excel file and automatically detect the header row."""
        if self.verbose:
            print("\n1. LOADING DATA...")
        
        # Try different skiprows values to find the actual data
        best_df = None
        best_score = 0
        best_skiprows = 0
        
        for skiprows in [0, 1, 2, 3, 4]:
            try:
                df = pd.read_excel(file_path, skiprows=skiprows)
                
                # Score based on meaningful column names and data
                score = 0
                
                # Check for meaningful column names
                meaningful_cols = sum(1 for col in df.columns 
                                     if not str(col).startswith('Unnamed') 
                                     and not pd.isna(col))
                score += meaningful_cols * 10
                
                # Check for actual data rows
                if len(df) > 10:
                    score += 20
                
                # Check for expected column patterns
                col_str = ' '.join(str(col).lower() for col in df.columns)
                expected_terms = ['property', 'tenant', 'area', 'rent', 'lease', 'square', 'fund']
                for term in expected_terms:
                    if term in col_str:
                        score += 5
                
                if score > best_score:
                    best_score = score
                    best_df = df
                    best_skiprows = skiprows
                    
            except Exception:
                continue
        
        if best_df is None:
            raise ValueError(f"Could not load Excel file: {file_path}")
        
        if self.verbose:
            print(f"   Loaded with skiprows={best_skiprows}")
            print(f"   Shape: {best_df.shape}")
            print(f"   Columns found: {len(best_df.columns)}")
        
        self.cleaning_stats['original_rows'] = len(best_df)
        self.cleaning_stats['original_columns'] = len(best_df.columns)
        
        return best_df
    
    def _standardize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize column names to consistent format."""
        if self.verbose:
            print("\n2. STANDARDIZING COLUMN NAMES...")
        
        # Create mapping for common column variations
        column_mapping = {
            # Property fields
            'property': ['property', 'property name', 'building', 'asset'],
            'property_code': ['property code', 'prop code', 'asset code', 'building code'],
            'address': ['address', 'property address', 'street address'],
            'market': ['market', 'submarket', 'region', 'area'],
            
            # Tenant fields
            'tenant_name': ['tenant', 'tenant name', 'lessee', 'company'],
            'suite': ['suite', 'unit', 'suite/unit', 'space'],
            
            # Space fields
            'square_feet': ['area', 'square feet', 'sf', 'rsf', 'square footage', 'rentable sf', 'leased sf'],
            
            # Financial fields
            'monthly_rent': ['monthly rent', 'base rent', 'monthly base rent', 'rent/month'],
            'annual_rent': ['annual rent', 'yearly rent', 'annual base rent', 'total rent'],
            'rent_psf': ['rent/sf', 'rent per sf', 'rate', '$/sf', 'rent psf'],
            'security_deposit': ['security deposit', 'deposit', 'security'],
            
            # Date fields
            'lease_start': ['lease from', 'lease start', 'commencement', 'start date', 'from'],
            'lease_end': ['lease to', 'lease end', 'expiration', 'end date', 'to'],
            'move_in_date': ['move in', 'move-in date', 'occupancy date'],
            'move_out_date': ['move out', 'move-out date', 'vacancy date'],
            
            # Status fields
            'status': ['status', 'lease status', 'occupancy status', 'occ status'],
            'lease_type': ['lease type', 'type', 'lease classification'],
            
            # Fund fields
            'fund': ['fund', 'vehicle', 'portfolio', 'owner']
        }
        
        # Create reverse mapping
        new_columns = {}
        for col in df.columns:
            col_lower = str(col).lower().strip()
            
            # Check each standard name
            mapped = False
            for standard_name, variations in column_mapping.items():
                for variation in variations:
                    if variation in col_lower or col_lower == variation:
                        new_columns[col] = standard_name
                        mapped = True
                        break
                if mapped:
                    break
            
            # Keep original if no mapping found
            if not mapped:
                # Clean up unnamed columns
                if 'unnamed' in col_lower:
                    new_columns[col] = f'column_{len(new_columns)}'
                else:
                    new_columns[col] = col_lower.replace(' ', '_').replace('/', '_')
        
        df = df.rename(columns=new_columns)
        
        if self.verbose:
            print(f"   Standardized {len(new_columns)} column names")
        
        return df
    
    def _clean_property_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract property codes and clean property information."""
        if self.verbose:
            print("\n3. CLEANING PROPERTY DATA...")
        
        # Extract property code from property name if not separate
        if 'property' in df.columns and 'property_code' not in df.columns:
            # Extract code from parentheses: "Property Name (CODE)"
            df['property_code'] = df['property'].str.extract(r'\(([^)]+)\)')
            
            # Clean property name (remove code in parentheses)
            df['property_name_clean'] = df['property'].str.replace(r'\s*\([^)]+\)', '', regex=True).str.strip()
        elif 'property' in df.columns:
            df['property_name_clean'] = df['property'].str.strip()
        
        # Classify fund based on property code
        if 'property_code' in df.columns:
            df['fund_derived'] = df['property_code'].apply(self._classify_fund)
            
            # Use derived fund if original fund column is missing or has many nulls
            if 'fund' not in df.columns or df['fund'].isna().sum() > len(df) * 0.5:
                df['fund'] = df['fund_derived']
        
        # Standardize fund names
        if 'fund' in df.columns:
            df['fund'] = df['fund'].apply(self._standardize_fund_name)
        
        if self.verbose:
            if 'property_code' in df.columns:
                print(f"   Extracted property codes: {df['property_code'].notna().sum()}")
            if 'fund' in df.columns:
                print(f"   Fund distribution: {df['fund'].value_counts().to_dict()}")
        
        return df
    
    def _classify_fund(self, code: str) -> str:
        """Classify fund based on property code pattern."""
        if pd.isna(code):
            return 'Unknown'
        
        code_str = str(code).strip().upper()
        
        if code_str.startswith('X'):
            return 'Fund 2'
        elif code_str.startswith('3'):
            return 'Fund 3'
        else:
            return 'Other'
    
    def _standardize_fund_name(self, fund: str) -> str:
        """Standardize fund naming conventions."""
        if pd.isna(fund):
            return 'Unknown'
        
        fund_str = str(fund).upper().strip()
        
        # Map various fund names to standard names
        fund_mapping = {
            'FUND 2': ['FUND 2', 'FRG X', 'FUND II', 'II', 'FUND2'],
            'FUND 3': ['FUND 3', 'FUND III', 'III', 'FUND3'],
        }
        
        for standard_name, variations in fund_mapping.items():
            for variation in variations:
                if variation in fund_str:
                    return standard_name
        
        return fund if fund else 'Unknown'
    
    def _clean_tenant_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean tenant names and information."""
        if self.verbose:
            print("\n4. CLEANING TENANT DATA...")
        
        if 'tenant_name' in df.columns:
            # Clean tenant names
            df['tenant_name'] = df['tenant_name'].str.strip()
            
            # Mark vacant units
            df['is_vacant'] = (
                df['tenant_name'].isna() | 
                (df['tenant_name'].str.lower().isin(['vacant', 'vacancy', 'empty', '']))
            )
            
            # Clean suite/unit numbers
            if 'suite' in df.columns:
                df['suite'] = df['suite'].astype(str).str.strip()
                df['suite'] = df['suite'].replace(['nan', 'None', ''], np.nan)
            
            if self.verbose:
                vacant_count = df['is_vacant'].sum()
                occupied_count = (~df['is_vacant']).sum()
                print(f"   Vacant units: {vacant_count}")
                print(f"   Occupied units: {occupied_count}")
        
        return df
    
    def _clean_numeric_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate numeric fields."""
        if self.verbose:
            print("\n5. CLEANING NUMERIC FIELDS...")
        
        numeric_fields = {
            'square_feet': {'min': 0, 'max': 1000000},
            'monthly_rent': {'min': 0, 'max': 10000000},
            'annual_rent': {'min': 0, 'max': 120000000},
            'rent_psf': {'min': 0, 'max': 1000},
            'security_deposit': {'min': 0, 'max': 100}
        }
        
        for field, limits in numeric_fields.items():
            if field in df.columns:
                # Convert to numeric
                df[field] = pd.to_numeric(df[field], errors='coerce')
                
                # Apply limits (set outliers to NaN)
                if 'min' in limits:
                    df.loc[df[field] < limits['min'], field] = np.nan
                if 'max' in limits:
                    df.loc[df[field] > limits['max'], field] = np.nan
                
                if self.verbose:
                    valid_count = df[field].notna().sum()
                    print(f"   {field}: {valid_count} valid values")
        
        return df
    
    def _clean_date_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """Parse and validate date fields."""
        if self.verbose:
            print("\n6. CLEANING DATE FIELDS...")
        
        date_fields = ['lease_start', 'lease_end', 'move_in_date', 'move_out_date']
        
        for field in date_fields:
            if field in df.columns:
                # Parse dates
                df[field] = pd.to_datetime(df[field], errors='coerce')
                
                # Remove unrealistic dates (before 1990 or after 2050)
                df.loc[df[field] < pd.Timestamp('1990-01-01'), field] = pd.NaT
                df.loc[df[field] > pd.Timestamp('2050-12-31'), field] = pd.NaT
                
                if self.verbose:
                    valid_count = df[field].notna().sum()
                    print(f"   {field}: {valid_count} valid dates")
        
        # Validate lease date logic
        if 'lease_start' in df.columns and 'lease_end' in df.columns:
            # Fix cases where end is before start
            invalid_mask = (df['lease_end'] < df['lease_start']) & df['lease_end'].notna() & df['lease_start'].notna()
            if invalid_mask.any():
                if self.verbose:
                    print(f"   Fixed {invalid_mask.sum()} invalid lease periods")
                # Swap the dates
                df.loc[invalid_mask, ['lease_start', 'lease_end']] = df.loc[invalid_mask, ['lease_end', 'lease_start']].values
        
        return df
    
    def _standardize_status_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize status and categorical fields."""
        if self.verbose:
            print("\n7. STANDARDIZING STATUS FIELDS...")
        
        if 'status' in df.columns:
            # Create status mapping
            status_mapping = {
                'occupied': 'Occupied',
                'occ': 'Occupied',
                'leased': 'Occupied',
                'vacant': 'Vacant',
                'vac': 'Vacant',
                'empty': 'Vacant',
                'vacancy': 'Vacant',
                'month-to-month': 'Month-to-Month',
                'mtm': 'Month-to-Month',
                'm2m': 'Month-to-Month',
                'notice': 'Notice Given',
                'notice given': 'Notice Given',
                'terminating': 'Notice Given'
            }
            
            # Apply mapping
            df['status'] = df['status'].str.lower().str.strip().map(status_mapping).fillna(df['status'])
            
            # Set status based on vacancy flag if available
            if 'is_vacant' in df.columns:
                df.loc[df['is_vacant'] & df['status'].isna(), 'status'] = 'Vacant'
                df.loc[~df['is_vacant'] & df['status'].isna(), 'status'] = 'Occupied'
            
            if self.verbose:
                print(f"   Status distribution: {df['status'].value_counts().to_dict()}")
        
        return df
    
    def _calculate_derived_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate additional fields from existing data."""
        if self.verbose:
            print("\n8. CALCULATING DERIVED FIELDS...")
        
        # Calculate annual rent from monthly if missing
        if 'monthly_rent' in df.columns and 'annual_rent' in df.columns:
            mask = df['annual_rent'].isna() & df['monthly_rent'].notna()
            df.loc[mask, 'annual_rent'] = df.loc[mask, 'monthly_rent'] * 12
            
            mask = df['monthly_rent'].isna() & df['annual_rent'].notna()
            df.loc[mask, 'monthly_rent'] = df.loc[mask, 'annual_rent'] / 12
        
        # Calculate rent per square foot
        if all(col in df.columns for col in ['annual_rent', 'square_feet']):
            mask = (df['square_feet'] > 0) & df['annual_rent'].notna()
            df.loc[mask, 'rent_psf_calculated'] = df.loc[mask, 'annual_rent'] / df.loc[mask, 'square_feet']
            
            # Use calculated if original is missing
            if 'rent_psf' not in df.columns:
                df['rent_psf'] = df['rent_psf_calculated']
            else:
                df['rent_psf'] = df['rent_psf'].fillna(df['rent_psf_calculated'])
        
        # Calculate lease term in months
        if 'lease_start' in df.columns and 'lease_end' in df.columns:
            df['lease_term_months'] = (
                (df['lease_end'] - df['lease_start']).dt.days / 30.44
            ).round(1)
            
            # Calculate remaining term
            today = pd.Timestamp.now()
            df['remaining_term_months'] = (
                (df['lease_end'] - today).dt.days / 30.44
            ).round(1)
            df.loc[df['remaining_term_months'] < 0, 'remaining_term_months'] = 0
        
        # Create unique tenant ID
        if 'property_code' in df.columns and 'tenant_name' in df.columns:
            df['tenant_id'] = (
                df['property_code'].astype(str) + '_' + 
                df['tenant_name'].astype(str).str.replace(' ', '_').str.upper()
            )
        
        if self.verbose:
            if 'rent_psf' in df.columns:
                print(f"   Calculated rent PSF for {df['rent_psf'].notna().sum()} records")
            if 'lease_term_months' in df.columns:
                print(f"   Calculated lease terms for {df['lease_term_months'].notna().sum()} records")
        
        return df
    
    def _validate_data_integrity(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate data integrity and flag issues."""
        if self.verbose:
            print("\n9. VALIDATING DATA INTEGRITY...")
        
        df['data_quality_flag'] = ''
        issues = []
        
        # Check for missing critical fields
        critical_fields = ['property', 'square_feet']
        for field in critical_fields:
            if field in df.columns:
                mask = df[field].isna()
                if mask.any():
                    df.loc[mask, 'data_quality_flag'] += f'missing_{field}; '
                    issues.append(f"Missing {field}: {mask.sum()} records")
        
        # Check for lease date issues
        if 'lease_start' in df.columns and 'lease_end' in df.columns:
            mask = (df['lease_end'] < df['lease_start']) & df['lease_end'].notna() & df['lease_start'].notna()
            if mask.any():
                df.loc[mask, 'data_quality_flag'] += 'invalid_lease_period; '
                issues.append(f"Invalid lease periods: {mask.sum()} records")
        
        # Check for rent calculation mismatches
        if all(col in df.columns for col in ['monthly_rent', 'annual_rent']):
            expected_annual = df['monthly_rent'] * 12
            mask = (abs(df['annual_rent'] - expected_annual) > 1) & df['annual_rent'].notna() & df['monthly_rent'].notna()
            if mask.any():
                df.loc[mask, 'data_quality_flag'] += 'rent_mismatch; '
                issues.append(f"Rent calculation mismatches: {mask.sum()} records")
        
        # Check for unrealistic values
        if 'square_feet' in df.columns:
            mask = (df['square_feet'] <= 0) & df['square_feet'].notna()
            if mask.any():
                df.loc[mask, 'data_quality_flag'] += 'invalid_square_feet; '
                issues.append(f"Invalid square feet: {mask.sum()} records")
        
        if self.verbose and issues:
            print("   Issues found:")
            for issue in issues:
                print(f"     - {issue}")
        
        self.cleaning_stats['data_quality_issues'] = len(issues)
        
        return df
    
    def _finalize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove duplicates, sort, and finalize the dataframe."""
        if self.verbose:
            print("\n10. FINALIZING DATAFRAME...")
        
        # Remove complete duplicates
        initial_len = len(df)
        df = df.drop_duplicates()
        duplicates_removed = initial_len - len(df)
        
        if self.verbose and duplicates_removed > 0:
            print(f"   Removed {duplicates_removed} duplicate records")
        
        # Sort by property and tenant
        sort_columns = []
        if 'fund' in df.columns:
            sort_columns.append('fund')
        if 'property_code' in df.columns:
            sort_columns.append('property_code')
        if 'tenant_name' in df.columns:
            sort_columns.append('tenant_name')
        
        if sort_columns:
            df = df.sort_values(sort_columns)
        
        # Reset index
        df = df.reset_index(drop=True)
        
        # Select and order final columns
        priority_columns = [
            'fund', 'property_code', 'property', 'property_name_clean',
            'tenant_name', 'tenant_id', 'suite', 'status',
            'square_feet', 'monthly_rent', 'annual_rent', 'rent_psf',
            'lease_start', 'lease_end', 'lease_term_months', 'remaining_term_months',
            'security_deposit', 'market', 'address',
            'is_vacant', 'data_quality_flag'
        ]
        
        final_columns = [col for col in priority_columns if col in df.columns]
        other_columns = [col for col in df.columns if col not in final_columns]
        df = df[final_columns + other_columns]
        
        self.cleaning_stats['final_rows'] = len(df)
        self.cleaning_stats['final_columns'] = len(df.columns)
        
        return df
    
    def _save_cleaned_data(self, df: pd.DataFrame, output_path: str):
        """Save cleaned data to file."""
        if self.verbose:
            print(f"\n11. SAVING CLEANED DATA...")
        
        if output_path.endswith('.xlsx'):
            df.to_excel(output_path, index=False)
        elif output_path.endswith('.csv'):
            df.to_csv(output_path, index=False)
        else:
            # Default to CSV
            output_path = output_path + '.csv'
            df.to_csv(output_path, index=False)
        
        if self.verbose:
            print(f"   Saved to: {output_path}")
    
    def _print_cleaning_summary(self, df: pd.DataFrame):
        """Print summary of cleaning operations."""
        print(f"\n{'='*80}")
        print("CLEANING SUMMARY")
        print(f"{'='*80}")
        
        print(f"Original shape: {self.cleaning_stats.get('original_rows', 'N/A')} rows × {self.cleaning_stats.get('original_columns', 'N/A')} columns")
        print(f"Final shape: {self.cleaning_stats.get('final_rows', 'N/A')} rows × {self.cleaning_stats.get('final_columns', 'N/A')} columns")
        
        if 'data_quality_issues' in self.cleaning_stats:
            print(f"Data quality issues found: {self.cleaning_stats['data_quality_issues']}")
        
        # Data completeness
        print(f"\nData Completeness:")
        important_fields = ['property', 'tenant_name', 'square_feet', 'annual_rent', 'lease_end']
        for field in important_fields:
            if field in df.columns:
                completeness = (df[field].notna().sum() / len(df)) * 100
                print(f"  {field}: {completeness:.1f}%")
        
        # Fund distribution
        if 'fund' in df.columns:
            print(f"\nFund Distribution:")
            for fund, count in df['fund'].value_counts().items():
                pct = (count / len(df)) * 100
                print(f"  {fund}: {count} records ({pct:.1f}%)")
        
        # Occupancy
        if 'status' in df.columns:
            print(f"\nOccupancy Status:")
            for status, count in df['status'].value_counts().items():
                pct = (count / len(df)) * 100
                print(f"  {status}: {count} records ({pct:.1f}%)")
        
        print(f"\n{'='*80}")


def main():
    """Main execution function with example usage."""
    
    # Example usage
    cleaner = RentRollCleaner(verbose=True)
    
    # Process a single file
    input_file = "rent rolls/06.30.25.xlsx"
    output_file = "cleaned_rent_roll_jun25.csv"
    
    if os.path.exists(input_file):
        cleaned_df = cleaner.clean_rent_roll(input_file, output_file)
        
        # Display sample of cleaned data
        print("\nSAMPLE OF CLEANED DATA:")
        print(cleaned_df.head())
        
        # Display data types
        print("\nDATA TYPES:")
        print(cleaned_df.dtypes)
    else:
        print(f"File not found: {input_file}")
        print("\nExample usage:")
        print("  python clean_rent_roll.py")
        print("\nOr import and use in your code:")
        print("  from clean_rent_roll import RentRollCleaner")
        print("  cleaner = RentRollCleaner()")
        print("  df = cleaner.clean_rent_roll('your_file.xlsx')")


if __name__ == "__main__":
    main()