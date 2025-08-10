#!/usr/bin/env python3
"""
Data Cleanup Execution Script
Implements the Data_Cleanup_Scripts.sql logic for CSV data files
Performs backup, cleanup, and validation operations
"""

import pandas as pd
import numpy as np
import os
import shutil
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataCleanupExecutor:
    def __init__(self, data_path="/Users/michaeltang/Documents/GitHub/BI/PBI v1.7/Data/Yardi_Tables"):
        self.data_path = data_path
        self.backup_path = f"{data_path}/backups_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.amendments_file = f"{data_path}/dim_fp_amendmentsunitspropertytenant.csv"
        self.charges_file = f"{data_path}/dim_fp_amendmentchargeschedule.csv"
        self.cleanup_stats = {}
        
    def create_backups(self):
        """Create safety backups of critical files"""
        logger.info("=== SECTION 1: CREATING SAFETY BACKUPS ===")
        
        os.makedirs(self.backup_path, exist_ok=True)
        
        # Backup amendments table
        if os.path.exists(self.amendments_file):
            backup_amendments = f"{self.backup_path}/dim_fp_amendmentsunitspropertytenant_backup.csv"
            shutil.copy2(self.amendments_file, backup_amendments)
            logger.info(f"Backed up amendments table to: {backup_amendments}")
            
        # Backup charge schedules table
        if os.path.exists(self.charges_file):
            backup_charges = f"{self.backup_path}/dim_fp_amendmentchargeschedule_backup.csv"
            shutil.copy2(self.charges_file, backup_charges)
            logger.info(f"Backed up charge schedules table to: {backup_charges}")
            
        logger.info(f"All backups created in: {self.backup_path}")
        return True
        
    def load_data(self):
        """Load the main data files"""
        logger.info("Loading data files...")
        
        # Load amendments with proper column name handling
        self.amendments_df = pd.read_csv(self.amendments_file, encoding='utf-8-sig')
        # Clean column names - remove BOM and extra spaces
        self.amendments_df.columns = [col.strip() for col in self.amendments_df.columns]
        
        # Load charge schedules
        self.charges_df = pd.read_csv(self.charges_file, encoding='utf-8-sig')
        self.charges_df.columns = [col.strip() for col in self.charges_df.columns]
        
        logger.info(f"Loaded {len(self.amendments_df)} amendments and {len(self.charges_df)} charge schedules")
        
        # Convert date columns
        date_columns = ['amendment start date', 'amendment end date', 'amendment sign date']
        for col in date_columns:
            if col in self.amendments_df.columns:
                self.amendments_df[col] = pd.to_datetime(self.amendments_df[col], errors='coerce')
                
        charge_date_columns = ['from date', 'to date']
        for col in charge_date_columns:
            if col in self.charges_df.columns:
                # Handle Excel serial dates with bounds checking
                self.charges_df[col] = pd.to_numeric(self.charges_df[col], errors='coerce')
                # Only convert valid Excel serial dates (between 1900 and reasonable future)
                valid_serials = (self.charges_df[col] > 1) & (self.charges_df[col] < 73050)  # ~year 2100
                
                # Initialize column with NaT
                converted_dates = pd.Series(pd.NaT, index=self.charges_df.index)
                
                # Convert only valid serial dates
                if valid_serials.any():
                    try:
                        converted_dates.loc[valid_serials] = pd.to_datetime('1899-12-30') + pd.to_timedelta(self.charges_df.loc[valid_serials, col], 'D')
                    except Exception as e:
                        logger.warning(f"Date conversion warning for {col}: {str(e)}")
                
                self.charges_df[col] = converted_dates
        
        return True
        
    def pre_cleanup_assessment(self):
        """Run comprehensive data quality assessment"""
        logger.info("=== SECTION 2: PRE-CLEANUP DATA QUALITY ASSESSMENT ===")
        
        assessment_results = []
        
        # 1. Check for duplicate active amendments
        active_amendments = self.amendments_df[self.amendments_df['amendment status'] == 'Activated']
        duplicate_active = active_amendments.groupby(['property hmy', 'tenant hmy']).size()
        duplicate_count = len(duplicate_active[duplicate_active > 1])
        
        assessment_results.append({
            'issue_type': 'Duplicate Active Amendments',
            'issue_count': duplicate_count,
            'severity': 'CRITICAL' if duplicate_count > 0 else 'OK',
            'description': 'Property/Tenant combinations with multiple active amendments'
        })
        
        # 2. Check for amendments missing rent charges
        active_with_sf = active_amendments[active_amendments['amendment sf'] > 0]
        rent_charges = self.charges_df[self.charges_df['charge code'] == 'rent']['amendment hmy'].unique()
        missing_rent = active_with_sf[~active_with_sf['amendment hmy'].isin(rent_charges)]
        
        assessment_results.append({
            'issue_type': 'Amendments Missing Rent Charges',
            'issue_count': len(missing_rent),
            'severity': 'HIGH' if len(missing_rent) > 0 else 'OK',
            'description': 'Active amendments with SF > 0 but no rent charges'
        })
        
        # 3. Check for invalid date sequences
        invalid_dates = self.amendments_df[
            (self.amendments_df['amendment end date'].notna()) &
            (self.amendments_df['amendment end date'] < self.amendments_df['amendment start date'])
        ]
        
        assessment_results.append({
            'issue_type': 'Invalid Date Sequences',
            'issue_count': len(invalid_dates),
            'severity': 'MEDIUM' if len(invalid_dates) > 0 else 'OK',
            'description': 'Amendments with end date before start date'
        })
        
        # 4. Check for orphaned charge schedules (THE BIG ONE - 164K records)
        amendment_hmys = set(self.amendments_df['amendment hmy'].unique())
        charge_hmys = set(self.charges_df['amendment hmy'].unique())
        orphaned_charges = self.charges_df[~self.charges_df['amendment hmy'].isin(amendment_hmys)]
        
        assessment_results.append({
            'issue_type': 'Orphaned Charge Schedules',
            'issue_count': len(orphaned_charges),
            'severity': 'CRITICAL' if len(orphaned_charges) > 0 else 'OK',
            'description': 'Charge schedules without corresponding amendments'
        })
        
        # Display assessment results
        logger.info("\\nPRE-CLEANUP ASSESSMENT RESULTS:")
        logger.info("-" * 80)
        for result in assessment_results:
            logger.info(f"{result['issue_type']:<35} | {result['issue_count']:<8} | {result['severity']:<8}")
            logger.info(f"  Description: {result['description']}")
            logger.info("-" * 80)
            
        self.cleanup_stats['pre_assessment'] = assessment_results
        return assessment_results
        
    def resolve_duplicate_amendments(self):
        """Resolve duplicate active amendments by superseding older versions"""
        logger.info("=== SECTION 3: RESOLVING DUPLICATE AMENDMENTS ===")
        
        # Find duplicate active amendments
        active_amendments = self.amendments_df[self.amendments_df['amendment status'] == 'Activated']
        duplicates = active_amendments.groupby(['property hmy', 'tenant hmy'])
        
        amendments_to_supersede = []
        
        for (property_hmy, tenant_hmy), group in duplicates:
            if len(group) > 1:
                # Sort by amendment sequence DESC, keep highest sequence (most recent)
                sorted_group = group.sort_values(['amendment sequence', 'amendment hmy'], ascending=[False, False])
                
                # Mark all but the first (highest sequence) for superseding
                to_supersede = sorted_group.iloc[1:]['amendment hmy'].tolist()
                amendments_to_supersede.extend(to_supersede)
                
                logger.info(f"Property {property_hmy}, Tenant {tenant_hmy}: Superseding {len(to_supersede)} duplicate amendments")
        
        # Update the dataframe - supersede duplicates
        superseded_count = len(amendments_to_supersede)
        if superseded_count > 0:
            mask = self.amendments_df['amendment hmy'].isin(amendments_to_supersede)
            self.amendments_df.loc[mask, 'amendment status'] = 'Superseded'
            self.amendments_df.loc[mask, 'amendment status code'] = 2
            
            # Add audit note
            current_date = datetime.now().strftime('%Y-%m-%d')
            note_addition = f" | Auto-superseded on {current_date} due to duplicate active status"
            self.amendments_df.loc[mask, 'amendment notes'] = self.amendments_df.loc[mask, 'amendment notes'].fillna('') + note_addition
            
        logger.info(f"Superseded {superseded_count} duplicate active amendments")
        self.cleanup_stats['amendments_superseded'] = superseded_count
        
        return superseded_count
        
    def cleanup_orphaned_charges(self):
        """Remove orphaned charge schedules (the 164K records)"""
        logger.info("=== SECTION 4: CLEANING UP ORPHANED CHARGE SCHEDULES ===")
        
        # Identify orphaned charges
        amendment_hmys = set(self.amendments_df['amendment hmy'].unique())
        orphaned_charges = self.charges_df[~self.charges_df['amendment hmy'].isin(amendment_hmys)]
        
        orphaned_count = len(orphaned_charges)
        logger.info(f"Found {orphaned_count:,} orphaned charge schedule records")
        
        if orphaned_count > 0:
            # Log orphaned charges for audit
            orphaned_log_file = f"{self.backup_path}/orphaned_charges_log.csv"
            orphaned_charges_with_reason = orphaned_charges.copy()
            orphaned_charges_with_reason['cleanup_reason'] = 'ORPHANED_AMENDMENT'
            orphaned_charges_with_reason['cleanup_timestamp'] = datetime.now()
            orphaned_charges_with_reason.to_csv(orphaned_log_file, index=False)
            logger.info(f"Logged orphaned charges to: {orphaned_log_file}")
            
            # Remove orphaned charges from main dataframe
            self.charges_df = self.charges_df[self.charges_df['amendment hmy'].isin(amendment_hmys)]
            
            logger.info(f"Removed {orphaned_count:,} orphaned charge schedule records")
            
        self.cleanup_stats['orphaned_charges_removed'] = orphaned_count
        return orphaned_count
        
    def fix_date_integrity_issues(self):
        """Fix invalid date sequences"""
        logger.info("=== SECTION 5: FIXING DATE INTEGRITY ISSUES ===")
        
        # Find records with invalid date sequences
        invalid_dates_mask = (
            self.amendments_df['amendment end date'].notna() &
            (self.amendments_df['amendment end date'] < self.amendments_df['amendment start date'])
        )
        
        invalid_count = invalid_dates_mask.sum()
        
        if invalid_count > 0:
            # Clear invalid end dates
            self.amendments_df.loc[invalid_dates_mask, 'amendment end date'] = pd.NaT
            
            # Add audit note
            current_date = datetime.now().strftime('%Y-%m-%d')
            note_addition = f" | End date cleared on {current_date} due to invalid date sequence"
            mask_with_notes = invalid_dates_mask
            self.amendments_df.loc[mask_with_notes, 'amendment notes'] = self.amendments_df.loc[mask_with_notes, 'amendment notes'].fillna('') + note_addition
            
            logger.info(f"Fixed {invalid_count} invalid date sequences")
        else:
            logger.info("No invalid date sequences found")
            
        self.cleanup_stats['dates_fixed'] = invalid_count
        return invalid_count
        
    def analyze_missing_charges(self):
        """Analyze amendments missing charge schedules"""
        logger.info("=== SECTION 6: ANALYZING MISSING CHARGES ===")
        
        # Get amendments without any charges
        amendment_with_charges = set(self.charges_df['amendment hmy'].unique())
        amendments_missing_charges = self.amendments_df[
            ~self.amendments_df['amendment hmy'].isin(amendment_with_charges)
        ]
        
        # Categorize by business logic
        categorized_missing = []
        for _, row in amendments_missing_charges.iterrows():
            if row['amendment sf'] > 0 and row['amendment status'] == 'Activated':
                category = 'RENT_EXPECTED'
                priority = 'CRITICAL'
            elif row['amendment sf'] > 0 and row['amendment status'] == 'Superseded':
                category = 'HISTORICAL_RENT'
                priority = 'HIGH'
            elif row['amendment sf'] == 0 and row['amendment type code'] == 4:
                category = 'TERMINATION_OK'
                priority = 'OK'
            elif row['amendment sf'] == 0 and row['amendment type code'] == 5:
                category = 'HOLDOVER_REVIEW'
                priority = 'MEDIUM'
            else:
                category = 'REVIEW_REQUIRED'
                priority = 'MEDIUM'
                
            categorized_missing.append({
                'amendment_hmy': row['amendment hmy'],
                'property_code': row['property code'],
                'tenant_id': row['tenant id'],
                'amendment_status': row['amendment status'],
                'amendment_sf': row['amendment sf'],
                'category': category,
                'priority': priority
            })
        
        # Generate summary report
        missing_charges_df = pd.DataFrame(categorized_missing)
        if len(missing_charges_df) > 0:
            summary = missing_charges_df.groupby(['category', 'priority']).agg({
                'amendment_hmy': 'count',
                'amendment_sf': 'sum'
            }).reset_index()
            summary.columns = ['Category', 'Priority', 'Amendment_Count', 'Total_SF']
            
            logger.info("\\nMISSING CHARGES ANALYSIS:")
            logger.info("-" * 80)
            for _, row in summary.iterrows():
                logger.info(f"{row['Category']:<20} | {row['Priority']:<8} | Count: {row['Amendment_Count']:<6} | SF: {row['Total_SF']:,.0f}")
            
            # Save detailed report
            missing_report_file = f"{self.backup_path}/missing_charges_business_review.csv"
            missing_charges_df.to_csv(missing_report_file, index=False)
            logger.info(f"\\nDetailed missing charges report saved to: {missing_report_file}")
            
        self.cleanup_stats['missing_charges_analysis'] = len(missing_charges_df)
        return missing_charges_df
        
    def save_cleaned_data(self):
        """Save cleaned data files"""
        logger.info("=== SAVING CLEANED DATA ===")
        
        # Save cleaned amendments
        cleaned_amendments_file = self.amendments_file.replace('.csv', '_cleaned.csv')
        self.amendments_df.to_csv(cleaned_amendments_file, index=False)
        logger.info(f"Saved cleaned amendments to: {cleaned_amendments_file}")
        
        # Save cleaned charge schedules
        cleaned_charges_file = self.charges_file.replace('.csv', '_cleaned.csv')
        self.charges_df.to_csv(cleaned_charges_file, index=False)
        logger.info(f"Saved cleaned charge schedules to: {cleaned_charges_file}")
        
        return cleaned_amendments_file, cleaned_charges_file
        
    def post_cleanup_validation(self):
        """Validate cleanup results"""
        logger.info("=== SECTION 7: POST-CLEANUP VALIDATION ===")
        
        validation_results = []
        
        # Re-check duplicate active amendments
        active_amendments = self.amendments_df[self.amendments_df['amendment status'] == 'Activated']
        duplicate_active = active_amendments.groupby(['property hmy', 'tenant hmy']).size()
        remaining_duplicates = len(duplicate_active[duplicate_active > 1])
        
        validation_results.append({
            'check': 'Duplicate Active Amendments',
            'count': remaining_duplicates,
            'status': 'RESOLVED' if remaining_duplicates == 0 else 'FAILED'
        })
        
        # Re-check invalid date sequences
        invalid_dates = self.amendments_df[
            (self.amendments_df['amendment end date'].notna()) &
            (self.amendments_df['amendment end date'] < self.amendments_df['amendment start date'])
        ]
        
        validation_results.append({
            'check': 'Invalid Date Sequences',
            'count': len(invalid_dates),
            'status': 'RESOLVED' if len(invalid_dates) == 0 else 'FAILED'
        })
        
        # Re-check orphaned charge schedules
        amendment_hmys = set(self.amendments_df['amendment hmy'].unique())
        orphaned_charges = self.charges_df[~self.charges_df['amendment hmy'].isin(amendment_hmys)]
        
        validation_results.append({
            'check': 'Orphaned Charge Schedules',
            'count': len(orphaned_charges),
            'status': 'RESOLVED' if len(orphaned_charges) == 0 else 'FAILED'
        })
        
        logger.info("\\nPOST-CLEANUP VALIDATION RESULTS:")
        logger.info("-" * 60)
        for result in validation_results:
            status_symbol = "✓" if result['status'] == 'RESOLVED' else "✗"
            logger.info(f"{status_symbol} {result['check']:<35} | {result['count']:<8} | {result['status']}")
            
        self.cleanup_stats['post_validation'] = validation_results
        return validation_results
        
    def generate_summary_report(self):
        """Generate comprehensive cleanup summary"""
        logger.info("\\n" + "=" * 80)
        logger.info("DATA CLEANUP SUMMARY REPORT")
        logger.info("=" * 80)
        logger.info(f"Cleanup completed at: {datetime.now()}")
        logger.info("")
        logger.info("ACTIONS TAKEN:")
        logger.info(f"  - Amendments superseded (duplicates): {self.cleanup_stats.get('amendments_superseded', 0):,}")
        logger.info(f"  - Invalid dates fixed: {self.cleanup_stats.get('dates_fixed', 0):,}")
        logger.info(f"  - Orphaned charges removed: {self.cleanup_stats.get('orphaned_charges_removed', 0):,}")
        logger.info("")
        logger.info("CURRENT DATA COUNTS:")
        logger.info(f"  - Total amendments: {len(self.amendments_df):,}")
        logger.info(f"  - Active amendments: {len(self.amendments_df[self.amendments_df['amendment status'] == 'Activated']):,}")
        logger.info(f"  - Total charge schedules: {len(self.charges_df):,}")
        logger.info("")
        logger.info("BACKUPS CREATED:")
        logger.info(f"  - Backup location: {self.backup_path}")
        logger.info("")
        logger.info("NEXT STEPS:")
        logger.info("  1. Review missing charges business report")
        logger.info("  2. Validate PowerBI calculations with cleaned data")
        logger.info("  3. Update DAX measures if needed")
        logger.info("=" * 80)
        
        return self.cleanup_stats

def main():
    """Execute complete data cleanup process"""
    logger.info("Starting Data Cleanup Execution")
    
    # Initialize cleanup executor
    cleaner = DataCleanupExecutor()
    
    try:
        # Step 1: Create backups
        cleaner.create_backups()
        
        # Step 2: Load data
        cleaner.load_data()
        
        # Step 3: Pre-cleanup assessment
        cleaner.pre_cleanup_assessment()
        
        # Step 4: Execute cleanup operations
        cleaner.resolve_duplicate_amendments()
        cleaner.cleanup_orphaned_charges()
        cleaner.fix_date_integrity_issues()
        
        # Step 5: Analyze missing charges
        cleaner.analyze_missing_charges()
        
        # Step 6: Save cleaned data
        cleaner.save_cleaned_data()
        
        # Step 7: Post-cleanup validation
        cleaner.post_cleanup_validation()
        
        # Step 8: Generate summary report
        final_stats = cleaner.generate_summary_report()
        
        logger.info("\\n*** DATA CLEANUP COMPLETED SUCCESSFULLY ***")
        return final_stats
        
    except Exception as e:
        logger.error(f"Data cleanup failed: {str(e)}")
        logger.error("Backups are available for rollback if needed")
        raise

if __name__ == "__main__":
    main()