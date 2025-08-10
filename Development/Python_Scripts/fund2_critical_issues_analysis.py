#!/usr/bin/env python3
"""
Fund 2 Critical Issues Deep Dive Analysis
==========================================

Detailed analysis of the critical data integrity issues found in Fund 2 data:
1. Multiple active amendments for same property/tenant combinations
2. Invalid amendment statuses 
3. Invalid date ranges in charge schedules

Author: Yardi PowerBI Data Integrity Validator
Date: 2025-08-09
"""

import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class Fund2CriticalIssuesAnalyzer:
    def __init__(self, data_path):
        self.data_path = data_path
        self.load_data()
    
    def load_data(self):
        """Load all Fund 2 data files"""
        print("Loading Fund 2 data for critical issue analysis...")
        
        self.properties = pd.read_csv(f"{self.data_path}/Fund2_Filtered/dim_property_fund2.csv")
        self.amendments = pd.read_csv(f"{self.data_path}/Fund2_Filtered/dim_fp_amendmentsunitspropertytenant_fund2.csv")
        self.charges_active = pd.read_csv(f"{self.data_path}/Fund2_Filtered/dim_fp_amendmentchargeschedule_fund2_active.csv")
        self.charges_all = pd.read_csv(f"{self.data_path}/Fund2_Filtered/dim_fp_amendmentchargeschedule_fund2_all.csv")
        
        print(f"✓ Loaded data for analysis")
    
    def analyze_duplicate_active_amendments(self):
        """Analyze the 98 property/tenant combinations with multiple active amendments"""
        print("\n" + "="*70)
        print("CRITICAL ISSUE #1: DUPLICATE ACTIVE AMENDMENTS")
        print("="*70)
        
        # Find property/tenant combinations with multiple active amendments
        active_amendments = self.amendments[self.amendments['amendment status'] == 'Activated']
        
        # Use simpler aggregation to avoid data type issues
        duplicates = active_amendments.groupby(['property hmy', 'tenant hmy']).size().reset_index(name='active_count')
        duplicates = duplicates[duplicates['active_count'] > 1]
        
        # Add additional details
        details = active_amendments.groupby(['property hmy', 'tenant hmy']).agg({
            'property code': 'first',
            'tenant id': 'first',
            'amendment sequence': ['min', 'max']
        }).reset_index()
        
        # Flatten column names
        details.columns = ['property_hmy', 'tenant_hmy', 'property_code', 'tenant_id', 'min_sequence', 'max_sequence']
        
        # Merge the details
        duplicates = duplicates.merge(details, on=['property_hmy', 'tenant_hmy'])
        
        print(f"Found {len(duplicates)} property/tenant combinations with multiple active amendments")
        print(f"This affects {duplicates['active_count'].sum()} total amendment records")
        
        # Show the top 10 most problematic cases
        print(f"\nTop 10 cases with most active amendments:")
        top_cases = duplicates.nlargest(10, 'active_count')
        print(top_cases[['property_code', 'tenant_id', 'active_count', 'min_sequence', 'max_sequence']].to_string(index=False))
        
        # Analyze the impact on rent roll calculations
        print(f"\n🎯 IMPACT ON RENT ROLL:")
        print(f"• These duplicate active amendments will cause rent to be counted multiple times")
        print(f"• Rent roll totals will be inflated by {duplicates['active_count'].sum() - len(duplicates)} records")
        print(f"• This directly impacts accuracy of occupancy and revenue calculations")
        
        # Show detailed examples
        print(f"\n📋 DETAILED EXAMPLES (First 5 cases):")
        for i, row in duplicates.head(5).iterrows():
            print(f"\n{i+1}. Property: {row['property_code']} | Tenant: {row['tenant_id']}")
            print(f"   Active amendments: {int(row['active_count'])}")
            print(f"   Sequence range: {int(row['min_sequence'])} to {int(row['max_sequence'])}")
            
            # Get the actual amendment records for this property/tenant
            prop_tenant_amendments = active_amendments[
                (active_amendments['property hmy'] == row['property_hmy']) &
                (active_amendments['tenant hmy'] == row['tenant_hmy'])
            ][['amendment hmy', 'amendment sequence', 'amendment type', 'amendment start date', 'amendment end date']]
            
            print("   Amendment details:")
            print(prop_tenant_amendments.to_string(index=False))
        
        # Remediation recommendations
        print(f"\n💡 REMEDIATION RECOMMENDATIONS:")
        print(f"1. IMMEDIATE: Identify which amendment should be 'Activated' vs 'Superseded'")
        print(f"2. BUSINESS RULE: Only the LATEST sequence should be 'Activated'")  
        print(f"3. DATA FIX: Change older sequences to 'Superseded' status")
        print(f"4. VALIDATION: Implement constraint to prevent multiple active amendments")
        
        return duplicates
    
    def analyze_invalid_statuses(self):
        """Analyze amendments with invalid statuses"""
        print("\n" + "="*70)
        print("CRITICAL ISSUE #2: INVALID AMENDMENT STATUSES")
        print("="*70)
        
        valid_statuses = ['Activated', 'Superseded', 'Cancelled', 'Pending']
        invalid_amendments = self.amendments[~self.amendments['amendment status'].isin(valid_statuses)]
        
        print(f"Found {len(invalid_amendments)} amendments with invalid statuses")
        
        # Show status breakdown
        status_counts = invalid_amendments['amendment status'].value_counts()
        print(f"\nInvalid status breakdown:")
        for status, count in status_counts.items():
            print(f"  '{status}': {count} amendments")
        
        # Show examples
        print(f"\n📋 EXAMPLES OF INVALID STATUSES:")
        examples = invalid_amendments[['amendment hmy', 'property code', 'tenant id', 'amendment status', 'amendment type']].head(10)
        print(examples.to_string(index=False))
        
        print(f"\n💡 REMEDIATION RECOMMENDATIONS:")
        print(f"1. IMMEDIATE: Review 'In Process' amendments - likely should be 'Pending' or 'Activated'")
        print(f"2. DATA CLEANUP: Map invalid statuses to valid ones based on business rules")
        print(f"3. SYSTEM FIX: Implement data validation to prevent invalid statuses")
        
        return invalid_amendments
    
    def analyze_invalid_date_ranges(self):
        """Analyze charges with invalid date ranges"""
        print("\n" + "="*70) 
        print("CRITICAL ISSUE #3: INVALID CHARGE DATE RANGES")
        print("="*70)
        
        # Convert dates for analysis
        charges_analysis = self.charges_all.copy()
        
        # Handle different date formats that might exist
        def safe_date_convert(date_col):
            if pd.api.types.is_numeric_dtype(date_col):
                # Excel serial date numbers
                return pd.to_datetime('1900-01-01') + pd.to_timedelta(date_col - 2, unit='D')
            else:
                # String dates
                return pd.to_datetime(date_col, errors='coerce')
        
        charges_analysis['from_date_parsed'] = safe_date_convert(charges_analysis['from date'])
        charges_analysis['to_date_parsed'] = safe_date_convert(charges_analysis['to date'])
        
        # Find various types of date issues
        issues = {}
        
        # Issue 1: From date > To date
        invalid_range = charges_analysis[
            (charges_analysis['from_date_parsed'] > charges_analysis['to_date_parsed']) &
            charges_analysis['from_date_parsed'].notna() &
            charges_analysis['to_date_parsed'].notna()
        ]
        issues['from_after_to'] = len(invalid_range)
        
        # Issue 2: Missing from dates
        missing_from = charges_analysis[charges_analysis['from_date_parsed'].isnull()]
        issues['missing_from_date'] = len(missing_from)
        
        # Issue 3: Missing to dates
        missing_to = charges_analysis[charges_analysis['to_date_parsed'].isnull()]
        issues['missing_to_date'] = len(missing_to)
        
        # Issue 4: Dates in the future (beyond reasonable lease terms)
        future_cutoff = datetime(2035, 12, 31)  # Reasonable future limit
        far_future = charges_analysis[
            (charges_analysis['to_date_parsed'] > future_cutoff) |
            (charges_analysis['from_date_parsed'] > future_cutoff)
        ]
        issues['far_future_dates'] = len(far_future)
        
        # Issue 5: Dates too far in the past
        past_cutoff = datetime(1990, 1, 1)  # Reasonable past limit
        far_past = charges_analysis[
            (charges_analysis['to_date_parsed'] < past_cutoff) |
            (charges_analysis['from_date_parsed'] < past_cutoff)
        ]
        issues['far_past_dates'] = len(far_past)
        
        total_issues = sum(issues.values())
        
        print(f"Found {total_issues} charges with date range issues:")
        for issue_type, count in issues.items():
            if count > 0:
                print(f"  {issue_type.replace('_', ' ').title()}: {count}")
        
        # Show examples of each issue type
        if issues['from_after_to'] > 0:
            print(f"\n📋 EXAMPLES - From Date After To Date ({issues['from_after_to']} cases):")
            examples = invalid_range[['property code', 'amendment hmy', 'charge code desc', 'from date', 'to date']].head(5)
            print(examples.to_string(index=False))
        
        if issues['missing_from_date'] > 0:
            print(f"\n📋 EXAMPLES - Missing From Date ({issues['missing_from_date']} cases):")
            examples = missing_from[['property code', 'amendment hmy', 'charge code desc', 'from date', 'to date', 'amount']].head(5)
            print(examples.to_string(index=False))
        
        # Analyze impact by charge type
        print(f"\n🎯 IMPACT BY CHARGE TYPE:")
        if total_issues > 0:
            invalid_charges = charges_analysis[
                charges_analysis['from_date_parsed'].isnull() |
                charges_analysis['to_date_parsed'].isnull() |
                (charges_analysis['from_date_parsed'] > charges_analysis['to_date_parsed'])
            ]
            charge_type_impact = invalid_charges['charge code desc'].value_counts()
            print(charge_type_impact.head(10).to_string())
        
        print(f"\n💡 REMEDIATION RECOMMENDATIONS:")
        print(f"1. IMMEDIATE: Review date formats - may need proper Excel serial date conversion")
        print(f"2. DATA CLEANUP: Fix charges where from_date > to_date")
        print(f"3. BUSINESS REVIEW: Validate missing dates with property managers")
        print(f"4. SYSTEM FIX: Implement date validation rules in data entry")
        
        return {
            'invalid_range': invalid_range,
            'missing_from': missing_from, 
            'missing_to': missing_to,
            'issues_summary': issues
        }
    
    def generate_action_plan(self):
        """Generate comprehensive action plan for fixing critical issues"""
        print("\n" + "="*70)
        print("COMPREHENSIVE ACTION PLAN")
        print("="*70)
        
        print("🚨 PRIORITY 1 - IMMEDIATE ACTIONS (Business Impact: HIGH)")
        print("-" * 50)
        print("1. FIX DUPLICATE ACTIVE AMENDMENTS:")
        print("   • Query: Find all property/tenant combinations with >1 active amendment")
        print("   • Action: Change all but the LATEST sequence to 'Superseded' status")
        print("   • SQL: UPDATE amendments SET status = 'Superseded' WHERE sequence < max_sequence")
        print("   • Validation: Confirm only 1 active amendment per property/tenant")
        
        print("\n2. RESOLVE INVALID AMENDMENT STATUSES:")
        print("   • Query: SELECT * FROM amendments WHERE status = 'In Process'")
        print("   • Action: Review each case and assign proper status (Activated/Pending)")
        print("   • Business Rule: 'In Process' likely means 'Pending' or ready to 'Activate'")
        
        print("\n⚠️  PRIORITY 2 - DATA QUALITY IMPROVEMENTS")
        print("-" * 50)
        print("3. FIX INVALID DATE RANGES:")
        print("   • Review Excel serial date conversion logic")
        print("   • Fix charges where from_date > to_date")
        print("   • Populate missing critical dates")
        print("   • Validate date ranges make business sense")
        
        print("\n4. INVESTIGATE CHARGES WITHOUT RENT:")
        print("   • 634 amendments lack rent charges - review if intentional")
        print("   • May impact rent roll completeness")
        print("   • Validate with property management business rules")
        
        print("\n📊 PRIORITY 3 - PREVENTIVE MEASURES")
        print("-" * 50)
        print("5. IMPLEMENT DATA VALIDATION RULES:")
        print("   • Constraint: Only 1 active amendment per property/tenant")
        print("   • Validation: Amendment status must be in valid list")
        print("   • Check: From date must be <= To date")
        print("   • Audit: Regular data integrity checks")
        
        print("\n6. MONITORING AND GOVERNANCE:")
        print("   • Weekly data integrity reports")
        print("   • Exception alerts for data quality issues")
        print("   • Business user training on proper data entry")
        
        print("\n🎯 SUCCESS METRICS:")
        print("-" * 20)
        print("• Data Integrity Score: Target 95+ (currently 66)")
        print("• Duplicate Active Amendments: 0 (currently 98)")
        print("• Invalid Statuses: 0 (currently 1)")  
        print("• Invalid Date Ranges: <5% (currently 366/7837 = 4.7%)")
        print("• Rent Roll Accuracy: >98% vs Yardi native reports")

def main():
    """Main execution function"""
    data_path = "/Users/michaeltang/Documents/GitHub/BI/PBI v1.7/Data"
    
    print("Fund 2 Critical Issues Deep Dive Analysis")
    print("="*50)
    print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        analyzer = Fund2CriticalIssuesAnalyzer(data_path)
        
        # Analyze each critical issue in detail
        analyzer.analyze_duplicate_active_amendments()
        analyzer.analyze_invalid_statuses()
        analyzer.analyze_invalid_date_ranges()
        
        # Generate comprehensive action plan
        analyzer.generate_action_plan()
        
        print(f"\n✅ Critical issues analysis completed!")
        
    except Exception as e:
        print(f"❌ Analysis failed with error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()