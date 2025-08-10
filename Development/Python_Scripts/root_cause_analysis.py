#!/usr/bin/env python3
"""
Root Cause Analysis for Rent Roll Accuracy Issues
Investigate why calculated rent values are $0 for many properties
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime

class RootCauseAnalyzer:
    """Analyze root causes of rent roll calculation discrepancies"""
    
    def __init__(self, base_path="/Users/michaeltang/Documents/GitHub/BI/PBI v1.7", verbose=True):
        self.base_path = base_path
        self.verbose = verbose
        
        # Test date for analysis (using Dec 31, 2024)
        self.test_date = {
            'excel_serial': 45657,  # December 31, 2024  
            'date_str': '12/31/2024',
            'timestamp': pd.Timestamp('2024-12-31')
        }
    
    def log(self, message):
        """Logging function"""
        if self.verbose:
            print(message)
    
    def load_data(self):
        """Load all necessary data for analysis"""
        self.log("\n" + "="*80)
        self.log("LOADING DATA FOR ROOT CAUSE ANALYSIS")
        self.log("="*80)
        
        fund2_path = os.path.join(self.base_path, "Data/Fund2_Filtered")
        
        # Load amendments
        self.amendments_df = pd.read_csv(
            os.path.join(fund2_path, "dim_fp_amendmentsunitspropertytenant_fund2.csv")
        )
        self.log(f"✓ Loaded {len(self.amendments_df)} amendment records")
        
        # Load charges (both active and all)
        self.charges_active_df = pd.read_csv(
            os.path.join(fund2_path, "dim_fp_amendmentchargeschedule_fund2_active.csv")
        )
        self.charges_all_df = pd.read_csv(
            os.path.join(fund2_path, "dim_fp_amendmentchargeschedule_fund2_all.csv")
        )
        self.log(f"✓ Loaded {len(self.charges_active_df)} active charges, {len(self.charges_all_df)} total charges")
        
        # Load properties
        self.properties_df = pd.read_csv(
            os.path.join(fund2_path, "dim_property_fund2.csv")
        )
        self.log(f"✓ Loaded {len(self.properties_df)} properties")
    
    def analyze_amendment_filtering(self):
        """Analyze how amendment filtering affects the data"""
        self.log("\n--- AMENDMENT FILTERING ANALYSIS ---")
        
        initial_count = len(self.amendments_df)
        self.log(f"Initial amendments: {initial_count}")
        
        # Filter 1: Status
        valid_statuses = ['Activated', 'Superseded']
        status_filtered = self.amendments_df[
            self.amendments_df['amendment status'].isin(valid_statuses)
        ]
        self.log(f"After status filter ({valid_statuses}): {len(status_filtered)} ({len(status_filtered)/initial_count*100:.1f}%)")
        
        # Check status distribution
        status_dist = self.amendments_df['amendment status'].value_counts()
        self.log(f"Status distribution: {status_dist.to_dict()}")
        
        # Filter 2: Type
        type_filtered = status_filtered[
            status_filtered['amendment type'] != 'Termination'
        ]
        self.log(f"After excluding terminations: {len(type_filtered)} ({len(type_filtered)/initial_count*100:.1f}%)")
        
        # Check type distribution
        type_dist = self.amendments_df['amendment type'].value_counts()
        self.log(f"Type distribution (top 10): {type_dist.head(10).to_dict()}")
        
        # Filter 3: Date active
        date_filtered = type_filtered[
            (type_filtered['amendment start date serial'] <= self.test_date['excel_serial']) &
            ((type_filtered['amendment end date serial'] >= self.test_date['excel_serial']) | 
             type_filtered['amendment end date serial'].isna())
        ]
        self.log(f"After date filter (active on {self.test_date['date_str']}): {len(date_filtered)} ({len(date_filtered)/initial_count*100:.1f}%)")
        
        # Analyze date ranges
        self.log(f"\nDate Range Analysis:")
        self.log(f"  Target date serial: {self.test_date['excel_serial']}")
        self.log(f"  Start dates - Min: {type_filtered['amendment start date serial'].min()}, Max: {type_filtered['amendment start date serial'].max()}")
        self.log(f"  End dates - Min: {type_filtered['amendment end date serial'].min()}, Max: {type_filtered['amendment end date serial'].max()}")
        self.log(f"  Null end dates: {type_filtered['amendment end date serial'].isna().sum()}")
        
        return date_filtered
    
    def analyze_latest_amendment_selection(self, valid_amendments):
        """Analyze latest amendment selection logic"""
        self.log("\n--- LATEST AMENDMENT SELECTION ANALYSIS ---")
        
        # Group by property and tenant to find sequences
        sequence_analysis = valid_amendments.groupby(['property hmy', 'tenant hmy']).agg({
            'amendment sequence': ['count', 'min', 'max']
        }).reset_index()
        sequence_analysis.columns = ['property_hmy', 'tenant_hmy', 'seq_count', 'seq_min', 'seq_max']
        
        self.log(f"Property/Tenant combinations: {len(sequence_analysis)}")
        self.log(f"Single sequence amendments: {(sequence_analysis['seq_count'] == 1).sum()}")
        self.log(f"Multiple sequence amendments: {(sequence_analysis['seq_count'] > 1).sum()}")
        
        # Example of sequence selection
        multi_seq = sequence_analysis[sequence_analysis['seq_count'] > 1].head(3)
        for _, row in multi_seq.iterrows():
            prop_hmy = row['property_hmy']
            tenant_hmy = row['tenant_hmy']
            examples = valid_amendments[
                (valid_amendments['property hmy'] == prop_hmy) & 
                (valid_amendments['tenant hmy'] == tenant_hmy)
            ][['property code', 'tenant id', 'amendment sequence', 'amendment status', 'amendment type']]
            self.log(f"\nExample - Property {prop_hmy}, Tenant {tenant_hmy}:")
            self.log(f"  Sequences: {examples['amendment sequence'].tolist()}")
            self.log(f"  Statuses: {examples['amendment status'].tolist()}")
        
        # Select latest amendments
        latest_sequences = valid_amendments.groupby(
            ['property hmy', 'tenant hmy']
        )['amendment sequence'].max().reset_index()
        latest_sequences.rename(columns={'amendment sequence': 'max_sequence'}, inplace=True)
        
        latest_amendments = pd.merge(
            valid_amendments,
            latest_sequences,
            left_on=['property hmy', 'tenant hmy', 'amendment sequence'],
            right_on=['property hmy', 'tenant hmy', 'max_sequence'],
            how='inner'
        )
        
        self.log(f"Latest amendments selected: {len(latest_amendments)}")
        
        return latest_amendments
    
    def analyze_charge_schedule_join(self, latest_amendments):
        """Analyze the charge schedule join and filtering"""
        self.log("\n--- CHARGE SCHEDULE JOIN ANALYSIS ---")
        
        # Analyze charge codes
        self.log(f"Total charges (all): {len(self.charges_all_df)}")
        self.log(f"Active charges: {len(self.charges_active_df)}")
        
        charge_codes_all = self.charges_all_df['charge code'].value_counts()
        self.log(f"Charge codes (all data): {charge_codes_all.to_dict()}")
        
        charge_codes_active = self.charges_active_df['charge code'].value_counts()
        self.log(f"Charge codes (active): {charge_codes_active.to_dict()}")
        
        # Focus on rent charges
        rent_charges_all = self.charges_all_df[self.charges_all_df['charge code'] == 'rent']
        rent_charges_active = self.charges_active_df[self.charges_active_df['charge code'] == 'rent']
        
        self.log(f"\nRent charges (all): {len(rent_charges_all)}")
        self.log(f"Rent charges (active): {len(rent_charges_active)}")
        
        # Date filtering on rent charges
        rent_charges_date_filtered = rent_charges_all[
            (rent_charges_all['from date'] <= self.test_date['excel_serial']) &
            ((rent_charges_all['to date'] >= self.test_date['excel_serial']) | 
             rent_charges_all['to date'].isna())
        ]
        self.log(f"Rent charges active on {self.test_date['date_str']}: {len(rent_charges_date_filtered)}")
        
        # Analyze date ranges in charges
        self.log(f"\nCharge Date Analysis:")
        self.log(f"  From dates - Min: {rent_charges_all['from date'].min()}, Max: {rent_charges_all['from date'].max()}")
        self.log(f"  To dates - Min: {rent_charges_all['to date'].min()}, Max: {rent_charges_all['to date'].max()}")
        self.log(f"  Null to dates: {rent_charges_all['to date'].isna().sum()}")
        
        # Join analysis
        amendment_hmys = set(latest_amendments['amendment hmy'])
        charge_hmys = set(rent_charges_date_filtered['amendment hmy'])
        common_hmys = amendment_hmys & charge_hmys
        
        self.log(f"\nJoin Analysis:")
        self.log(f"  Amendment HMYs: {len(amendment_hmys)}")
        self.log(f"  Charge HMYs: {len(charge_hmys)}")  
        self.log(f"  Common HMYs: {len(common_hmys)}")
        self.log(f"  Join success rate: {len(common_hmys)/len(amendment_hmys)*100:.1f}%")
        
        # Examples of missing joins
        missing_hmys = amendment_hmys - charge_hmys
        if missing_hmys:
            sample_missing = list(missing_hmys)[:5]
            self.log(f"\nSample missing charge HMYs: {sample_missing}")
            
            for hmy in sample_missing[:2]:
                amendment_info = latest_amendments[latest_amendments['amendment hmy'] == hmy][
                    ['property code', 'tenant id', 'amendment status', 'amendment type']
                ].iloc[0]
                self.log(f"  HMY {hmy}: {amendment_info.to_dict()}")
        
        # Successful joins
        merged_data = pd.merge(
            latest_amendments,
            rent_charges_date_filtered[['amendment hmy', 'monthly amount']],
            on='amendment hmy',
            how='left'
        )
        
        has_rent = merged_data['monthly amount'].notna().sum()
        self.log(f"\nAmendments with rent charges: {has_rent}/{len(merged_data)} ({has_rent/len(merged_data)*100:.1f}%)")
        
        # Analyze zero rent amounts
        zero_rent = (merged_data['monthly amount'] == 0).sum()
        positive_rent = (merged_data['monthly amount'] > 0).sum()
        self.log(f"Zero rent amounts: {zero_rent}")
        self.log(f"Positive rent amounts: {positive_rent}")
        
        if positive_rent > 0:
            rent_stats = merged_data[merged_data['monthly amount'] > 0]['monthly amount'].describe()
            self.log(f"Rent statistics (positive only):")
            self.log(f"  Mean: ${rent_stats['mean']:,.2f}")
            self.log(f"  Median: ${rent_stats['50%']:,.2f}")
            self.log(f"  Min: ${rent_stats['min']:,.2f}")
            self.log(f"  Max: ${rent_stats['max']:,.2f}")
        
        return merged_data
    
    def analyze_specific_problem_properties(self):
        """Analyze specific properties with known issues"""
        self.log("\n--- SPECIFIC PROPERTY ANALYSIS ---")
        
        # Problem properties from the accuracy test
        problem_properties = [
            'xnj19nev', 'xpa18rai', 'xil1600', 'xnj17pol', 'xnj5thor',
            'xtx4201n', 'xohmost', 'xtx1709s', 'xil770ar', 'xnj125al'
        ]
        
        for prop_code in problem_properties[:3]:  # Analyze top 3
            self.log(f"\n--- ANALYZING PROPERTY: {prop_code} ---")
            
            # Find amendments for this property
            prop_amendments = self.amendments_df[
                self.amendments_df['property code'] == prop_code
            ]
            self.log(f"Total amendments for {prop_code}: {len(prop_amendments)}")
            
            if len(prop_amendments) == 0:
                self.log(f"  No amendments found in data!")
                continue
            
            # Show amendment details
            for _, amendment in prop_amendments.head(3).iterrows():
                self.log(f"  Amendment {amendment['amendment hmy']}:")
                self.log(f"    Status: {amendment['amendment status']}")
                self.log(f"    Type: {amendment['amendment type']}")
                self.log(f"    Sequence: {amendment['amendment sequence']}")
                self.log(f"    Dates: {amendment['amendment start date']} to {amendment['amendment end date']}")
                
                # Find charges for this amendment
                amendment_charges = self.charges_all_df[
                    self.charges_all_df['amendment hmy'] == amendment['amendment hmy']
                ]
                self.log(f"    Charges found: {len(amendment_charges)}")
                
                if len(amendment_charges) > 0:
                    for _, charge in amendment_charges.iterrows():
                        self.log(f"      {charge['charge code']}: ${charge['monthly amount']:.2f} ({charge['from date']} to {charge['to date']})")
    
    def analyze_date_serial_conversion(self):
        """Analyze potential issues with date serial conversion"""
        self.log("\n--- DATE SERIAL CONVERSION ANALYSIS ---")
        
        # Check date serial fields
        amendments_with_dates = self.amendments_df[
            self.amendments_df['amendment start date serial'].notna() &
            self.amendments_df['amendment end date serial'].notna()
        ]
        
        self.log(f"Amendments with valid date serials: {len(amendments_with_dates)}")
        
        # Convert some serials back to dates to verify
        sample_amendments = amendments_with_dates.head(5)
        for _, amendment in sample_amendments.iterrows():
            start_serial = amendment['amendment start date serial']
            end_serial = amendment['amendment end date serial']
            
            # Convert Excel serial to date (Excel epoch is 1900-01-01, but with leap year bug)
            start_date = pd.Timestamp('1900-01-01') + pd.Timedelta(days=start_serial-2)
            end_date = pd.Timestamp('1900-01-01') + pd.Timedelta(days=end_serial-2)
            
            self.log(f"Amendment {amendment['amendment hmy']}:")
            self.log(f"  Serial {start_serial} -> {start_date.date()} (should be {amendment['amendment start date']})")
            self.log(f"  Serial {end_serial} -> {end_date.date()} (should be {amendment['amendment end date']})")
        
        # Check charges dates
        charges_with_dates = self.charges_all_df[
            self.charges_all_df['from date'].notna() &
            self.charges_all_df['to date'].notna()
        ]
        
        self.log(f"\nCharges with valid dates: {len(charges_with_dates)}")
        
        sample_charges = charges_with_dates.head(3)
        for _, charge in sample_charges.iterrows():
            from_serial = charge['from date']
            to_serial = charge['to date']
            
            from_date = pd.Timestamp('1900-01-01') + pd.Timedelta(days=from_serial-2)
            to_date = pd.Timestamp('1900-01-01') + pd.Timedelta(days=to_serial-2)
            
            self.log(f"Charge {charge['record hmy']}:")
            self.log(f"  Serial {from_serial} -> {from_date.date()}")
            self.log(f"  Serial {to_serial} -> {to_date.date()}")
    
    def generate_recommendations(self):
        """Generate specific recommendations for fixing the issues"""
        self.log("\n" + "="*80)
        self.log("ROOT CAUSE ANALYSIS RECOMMENDATIONS")
        self.log("="*80)
        
        self.log("\nKey Issues Identified:")
        self.log("1. Low charge schedule join success rate - many amendments lack rent charges")
        self.log("2. Date filtering may be too restrictive or date serials have conversion issues")
        self.log("3. Some properties have amendments but no active rent charges for the test date")
        
        self.log("\nRecommended Fixes:")
        self.log("1. CHARGE SCHEDULE DATA QUALITY:")
        self.log("   - Verify charge schedule completeness for all active amendments")
        self.log("   - Check if 'active' filter in charge schedule is too restrictive")
        self.log("   - Consider using all charge data with proper date filtering")
        
        self.log("\n2. DATE FILTERING LOGIC:")
        self.log("   - Verify date serial conversion accuracy")
        self.log("   - Consider using date ranges instead of exact date matching")
        self.log("   - Test with current date (TODAY()) instead of historical test dates")
        
        self.log("\n3. AMENDMENT STATUS LOGIC:")
        self.log("   - Verify that 'Activated' + 'Superseded' is the correct filter")
        self.log("   - Consider including additional statuses if appropriate")
        self.log("   - Check if 'Superseded' amendments should have rent charges")
        
        self.log("\n4. BUSINESS LOGIC VALIDATION:")
        self.log("   - Confirm with business users that $0 rent is never valid")
        self.log("   - Verify amendment sequence selection logic")
        self.log("   - Check if terminated leases should still show in rent roll")
        
        self.log("\n5. IMMEDIATE TESTING IMPROVEMENTS:")
        self.log("   - Use 'all charges' dataset with proper date filtering")
        self.log("   - Implement fallback logic for missing rent charges")
        self.log("   - Add data quality alerts for $0 rent calculations")
    
    def run_analysis(self):
        """Run complete root cause analysis"""
        self.log("🔍 STARTING ROOT CAUSE ANALYSIS FOR RENT ROLL DISCREPANCIES")
        self.log("="*80)
        
        # Load data
        self.load_data()
        
        # Step-by-step analysis
        valid_amendments = self.analyze_amendment_filtering()
        latest_amendments = self.analyze_latest_amendment_selection(valid_amendments)
        merged_data = self.analyze_charge_schedule_join(latest_amendments)
        
        # Specific analyses
        self.analyze_specific_problem_properties()
        self.analyze_date_serial_conversion()
        
        # Generate recommendations
        self.generate_recommendations()
        
        self.log("\n" + "="*80)
        self.log("ROOT CAUSE ANALYSIS COMPLETE")
        self.log("="*80)


def main():
    """Main execution function"""
    analyzer = RootCauseAnalyzer(verbose=True)
    analyzer.run_analysis()
    
    return 0


if __name__ == "__main__":
    exit(main())