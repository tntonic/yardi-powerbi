#!/usr/bin/env python3
"""
Net Absorption Calculator
Implements the methodology from NET_ABSORPTION_CALCULATION_GUIDE.md
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Set
import warnings
warnings.filterwarnings('ignore')

class NetAbsorptionCalculator:
    """Calculate net absorption between two rent roll periods"""
    
    def __init__(self):
        self.period1_data = None
        self.period2_data = None
        self.same_store_properties = set()
        self.results = {}
        
    def load_rent_roll(self, file_path: str, period_label: str) -> pd.DataFrame:
        """Load and standardize rent roll data"""
        print(f"\nLoading {period_label} rent roll from: {file_path}")
        
        # Try different header rows to find the data
        for header_row in [0, 1, 2, 3]:
            try:
                df = pd.read_excel(file_path, header=header_row)
                
                # Check if we have meaningful column names
                non_empty_cols = [col for col in df.columns if 'Unnamed' not in str(col)]
                if len(non_empty_cols) > 5:  # Likely found the right header
                    print(f"  ✓ Found data with header at row {header_row}")
                    break
            except:
                continue
        
        # Standardize column names
        df.columns = df.columns.str.strip()
        
        # Identify key columns
        property_col = self._find_column(df, ['property', 'building', 'address'])
        unit_col = self._find_column(df, ['unit', 'suite', 'space'])
        tenant_col = self._find_column(df, ['tenant', 'lessee', 'occupant', 'lease'])
        area_col = self._find_column(df, ['area', 'sf', 'square', 'feet', 'size'])
        
        if not all([property_col, tenant_col, area_col]):
            raise ValueError("Missing required columns in rent roll")
        
        # Create standardized dataframe
        standardized_df = pd.DataFrame({
            'property': df[property_col],
            'unit': df[unit_col] if unit_col else '',
            'tenant': df[tenant_col],
            'area': pd.to_numeric(df[area_col], errors='coerce')
        })
        
        # Clean data
        standardized_df['property'] = standardized_df['property'].astype(str).str.strip()
        standardized_df['unit'] = standardized_df['unit'].fillna('').astype(str).str.strip()
        standardized_df['tenant'] = standardized_df['tenant'].astype(str).str.strip().str.upper()
        
        # Create space identifier
        standardized_df['space_id'] = standardized_df['property'] + '|' + standardized_df['unit']
        
        # Remove invalid rows
        standardized_df = standardized_df[
            (standardized_df['area'] > 0) & 
            (standardized_df['property'] != 'nan') &
            (standardized_df['property'] != '')
        ].copy()
        
        print(f"  ✓ Loaded {len(standardized_df)} spaces totaling {standardized_df['area'].sum():,.0f} SF")
        
        return standardized_df
    
    def _find_column(self, df: pd.DataFrame, keywords: List[str]) -> str:
        """Find column name containing any of the keywords"""
        for col in df.columns:
            col_lower = str(col).lower()
            for keyword in keywords:
                if keyword in col_lower:
                    return col
        return None
    
    def identify_same_store_properties(self, df1: pd.DataFrame, df2: pd.DataFrame) -> Set[str]:
        """Identify properties present in both periods"""
        properties1 = set(df1['property'].unique())
        properties2 = set(df2['property'].unique())
        
        same_store = properties1.intersection(properties2)
        acquisitions = properties2 - properties1
        dispositions = properties1 - properties2
        
        print(f"\nProperty Analysis:")
        print(f"  Same-store properties: {len(same_store)}")
        print(f"  Acquisitions: {len(acquisitions)}")
        print(f"  Dispositions: {len(dispositions)}")
        
        self.results['property_analysis'] = {
            'same_store_count': len(same_store),
            'acquisitions': list(acquisitions),
            'dispositions': list(dispositions)
        }
        
        return same_store
    
    def calculate_lease_movements(self, df1: pd.DataFrame, df2: pd.DataFrame, 
                                 same_store: Set[str]) -> Dict:
        """Calculate lease expirations and commencements"""
        
        # Filter to same-store properties only
        df1_ss = df1[df1['property'].isin(same_store)].copy()
        df2_ss = df2[df2['property'].isin(same_store)].copy()
        
        # Create space lookup dictionaries
        # Handle duplicates by keeping first occurrence
        df1_ss_unique = df1_ss.drop_duplicates(subset=['space_id'], keep='first')
        df2_ss_unique = df2_ss.drop_duplicates(subset=['space_id'], keep='first')
        
        spaces1 = df1_ss_unique.set_index('space_id').to_dict('index')
        spaces2 = df2_ss_unique.set_index('space_id').to_dict('index')
        
        # Track movements
        expirations = []
        commencements = []
        tenant_changes = []
        
        # Check all spaces that exist in both periods
        all_spaces = set(spaces1.keys()).union(set(spaces2.keys()))
        
        for space_id in all_spaces:
            space1 = spaces1.get(space_id)
            space2 = spaces2.get(space_id)
            
            # Space existed in period 1
            if space1:
                tenant1 = space1['tenant']
                area1 = space1['area']
                is_vacant1 = self._is_vacant(tenant1)
                
                # Check if space exists in period 2
                if space2:
                    tenant2 = space2['tenant']
                    area2 = space2['area']
                    is_vacant2 = self._is_vacant(tenant2)
                    
                    # Lease expiration: occupied → vacant
                    if not is_vacant1 and is_vacant2:
                        expirations.append({
                            'space_id': space_id,
                            'property': space1['property'],
                            'unit': space1['unit'],
                            'tenant': tenant1,
                            'area': area1
                        })
                    
                    # Lease commencement: vacant → occupied
                    elif is_vacant1 and not is_vacant2:
                        commencements.append({
                            'space_id': space_id,
                            'property': space2['property'],
                            'unit': space2['unit'],
                            'tenant': tenant2,
                            'area': area2
                        })
                    
                    # Tenant change (counts as both expiration and commencement)
                    elif not is_vacant1 and not is_vacant2 and tenant1 != tenant2:
                        tenant_changes.append({
                            'space_id': space_id,
                            'property': space1['property'],
                            'unit': space1['unit'],
                            'old_tenant': tenant1,
                            'new_tenant': tenant2,
                            'area': area1
                        })
                        # Add to both lists
                        expirations.append({
                            'space_id': space_id,
                            'property': space1['property'],
                            'unit': space1['unit'],
                            'tenant': tenant1,
                            'area': area1
                        })
                        commencements.append({
                            'space_id': space_id,
                            'property': space2['property'],
                            'unit': space2['unit'],
                            'tenant': tenant2,
                            'area': area2
                        })
                
                # Space demolished/removed (was occupied)
                else:
                    if not is_vacant1:
                        expirations.append({
                            'space_id': space_id,
                            'property': space1['property'],
                            'unit': space1['unit'],
                            'tenant': tenant1,
                            'area': area1
                        })
            
            # New space in period 2 (new construction/expansion)
            elif space2:
                tenant2 = space2['tenant']
                area2 = space2['area']
                is_vacant2 = self._is_vacant(tenant2)
                
                if not is_vacant2:
                    commencements.append({
                        'space_id': space_id,
                        'property': space2['property'],
                        'unit': space2['unit'],
                        'tenant': tenant2,
                        'area': area2
                    })
        
        # Calculate totals
        total_expirations = sum(exp['area'] for exp in expirations)
        total_commencements = sum(com['area'] for com in commencements)
        net_absorption = total_commencements - total_expirations
        
        results = {
            'expirations': expirations,
            'commencements': commencements,
            'tenant_changes': tenant_changes,
            'total_expirations_sf': total_expirations,
            'total_commencements_sf': total_commencements,
            'net_absorption_sf': net_absorption,
            'expiration_count': len(expirations),
            'commencement_count': len(commencements),
            'tenant_change_count': len(tenant_changes)
        }
        
        return results
    
    def _is_vacant(self, tenant_name: str) -> bool:
        """Check if a tenant name indicates vacancy"""
        vacant_indicators = ['VACANT', 'AVAILABLE', 'EMPTY', 'NONE', 'N/A', 'TBD']
        tenant_upper = str(tenant_name).upper().strip()
        return any(indicator in tenant_upper for indicator in vacant_indicators)
    
    def validate_results(self, df1: pd.DataFrame, df2: pd.DataFrame, 
                        movements: Dict, same_store: Set[str]) -> Dict:
        """Validate calculation results"""
        
        # Calculate occupancy for same-store properties
        df1_ss = df1[df1['property'].isin(same_store)].copy()
        df2_ss = df2[df2['property'].isin(same_store)].copy()
        
        # Period 1 occupancy
        df1_ss['is_occupied'] = ~df1_ss['tenant'].apply(self._is_vacant)
        occupied1_sf = df1_ss[df1_ss['is_occupied']]['area'].sum()
        total1_sf = df1_ss['area'].sum()
        
        # Period 2 occupancy
        df2_ss['is_occupied'] = ~df2_ss['tenant'].apply(self._is_vacant)
        occupied2_sf = df2_ss[df2_ss['is_occupied']]['area'].sum()
        total2_sf = df2_ss['area'].sum()
        
        # Validation check
        expected_occupied2 = occupied1_sf + movements['total_commencements_sf'] - movements['total_expirations_sf']
        validation_diff = occupied2_sf - expected_occupied2
        
        validation = {
            'period1_occupied_sf': occupied1_sf,
            'period2_occupied_sf': occupied2_sf,
            'expected_period2_occupied': expected_occupied2,
            'validation_difference': validation_diff,
            'validation_pass': abs(validation_diff) < (total1_sf * 0.001),  # Within 0.1% tolerance
            'period1_occupancy_rate': (occupied1_sf / total1_sf * 100) if total1_sf > 0 else 0,
            'period2_occupancy_rate': (occupied2_sf / total2_sf * 100) if total2_sf > 0 else 0
        }
        
        return validation
    
    def generate_report(self, period1_label: str, period2_label: str) -> str:
        """Generate formatted report of results"""
        
        props = self.results['property_analysis']
        moves = self.results['movements']
        valid = self.results['validation']
        
        # Get largest movements for examples
        top_expirations = sorted(moves['expirations'], key=lambda x: x['area'], reverse=True)[:3]
        top_commencements = sorted(moves['commencements'], key=lambda x: x['area'], reverse=True)[:3]
        
        report = f"""
NET ABSORPTION CALCULATION REPORT
================================

Period Comparison: {period1_label} to {period2_label}
Same-Store Properties: {props['same_store_count']}
Acquisitions: {len(props['acquisitions'])} properties
Dispositions: {len(props['dispositions'])} properties

Lease Activity (Same-Store):
- Expirations: {moves['expiration_count']} spaces, {moves['total_expirations_sf']:,.0f} square feet
- Commencements: {moves['commencement_count']} spaces, {moves['total_commencements_sf']:,.0f} square feet
- Tenant Changes: {moves['tenant_change_count']} spaces
- Net Absorption: {moves['net_absorption_sf']:,.0f} square feet ({moves['net_absorption_sf']/valid['period1_occupied_sf']*100:.1f}%)

Occupancy Rates:
- {period1_label}: {valid['period1_occupancy_rate']:.1f}%
- {period2_label}: {valid['period2_occupancy_rate']:.1f}%

Validation Check: {'PASSED' if valid['validation_pass'] else 'FAILED'}
- Expected Occupied SF: {valid['expected_period2_occupied']:,.0f}
- Actual Occupied SF: {valid['period2_occupied_sf']:,.0f}
- Difference: {valid['validation_difference']:,.0f} SF

Examples of Major Movements:
"""
        
        # Add expiration examples
        if top_expirations:
            report += "\nLargest Expirations:\n"
            for exp in top_expirations:
                report += f"- {exp['tenant']} vacated {exp['unit']} at {exp['property']} ({exp['area']:,.0f} sq ft)\n"
        
        # Add commencement examples
        if top_commencements:
            report += "\nLargest Commencements:\n"
            for com in top_commencements:
                report += f"- {com['tenant']} leased {com['unit']} at {com['property']} ({com['area']:,.0f} sq ft)\n"
        
        return report
    
    def calculate(self, file1: str, label1: str, file2: str, label2: str) -> str:
        """Main calculation method"""
        
        print(f"\nNET ABSORPTION CALCULATION")
        print("=" * 50)
        
        # Load data
        self.period1_data = self.load_rent_roll(file1, label1)
        self.period2_data = self.load_rent_roll(file2, label2)
        
        # Identify same-store properties
        self.same_store_properties = self.identify_same_store_properties(
            self.period1_data, self.period2_data
        )
        
        # Calculate movements
        print(f"\nCalculating lease movements...")
        self.results['movements'] = self.calculate_lease_movements(
            self.period1_data, self.period2_data, self.same_store_properties
        )
        
        # Validate results
        print(f"\nValidating results...")
        self.results['validation'] = self.validate_results(
            self.period1_data, self.period2_data, 
            self.results['movements'], self.same_store_properties
        )
        
        # Generate report
        report = self.generate_report(label1, label2)
        
        print(report)
        
        # Save detailed results
        self._save_detailed_results()
        
        return report
    
    def _save_detailed_results(self):
        """Save detailed movement data to Excel"""
        
        # Create dataframes for export
        exp_data = self.results['movements']['expirations']
        com_data = self.results['movements']['commencements']
        tc_data = self.results['movements']['tenant_changes']
        
        exp_df = pd.DataFrame(exp_data) if exp_data else pd.DataFrame()
        com_df = pd.DataFrame(com_data) if com_data else pd.DataFrame()
        tc_df = pd.DataFrame(tc_data) if tc_data else pd.DataFrame()
        
        # Save to Excel with multiple sheets
        with pd.ExcelWriter('net_absorption_details.xlsx', engine='openpyxl') as writer:
            if not exp_df.empty:
                exp_df.to_excel(writer, sheet_name='Expirations', index=False)
            if not com_df.empty:
                com_df.to_excel(writer, sheet_name='Commencements', index=False)
            if not tc_df.empty:
                tc_df.to_excel(writer, sheet_name='Tenant_Changes', index=False)
            
            # Summary sheet
            summary_data = {
                'Metric': [
                    'Total Expirations (SF)',
                    'Total Commencements (SF)',
                    'Net Absorption (SF)',
                    'Expiration Count',
                    'Commencement Count',
                    'Same-Store Properties',
                    'Period 1 Occupancy %',
                    'Period 2 Occupancy %'
                ],
                'Value': [
                    self.results['movements']['total_expirations_sf'],
                    self.results['movements']['total_commencements_sf'],
                    self.results['movements']['net_absorption_sf'],
                    self.results['movements']['expiration_count'],
                    self.results['movements']['commencement_count'],
                    self.results['property_analysis']['same_store_count'],
                    self.results['validation']['period1_occupancy_rate'],
                    self.results['validation']['period2_occupancy_rate']
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        print(f"\n✓ Detailed results saved to: net_absorption_details.xlsx")


# Example usage
if __name__ == "__main__":
    calculator = NetAbsorptionCalculator()
    
    # Example calculation
    print("Example: Calculating Q4 2024 to Q1 2025 net absorption")
    
    try:
        report = calculator.calculate(
            file1="/Users/michaeltang/Documents/GitHub/rent-roll/rent rolls/12.31.24.xlsx",
            label1="Q4 2024",
            file2="/Users/michaeltang/Documents/GitHub/rent-roll/rent rolls/03.31.25.xlsx",
            label2="Q1 2025"
        )
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure to provide valid rent roll file paths")