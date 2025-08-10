#!/usr/bin/env python3
"""
Yardi Power BI Data Model Validation Script
============================================
Purpose: Comprehensive validation of the 32-table Yardi data model
Author: Yardi Power BI Data Model Integrity Specialist
Date: 2025-08-09
============================================
"""

import pandas as pd
import os
import sys
from pathlib import Path
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class YardiDataModelValidator:
    def __init__(self, data_path):
        self.data_path = Path(data_path)
        self.results = {}
        self.issues = []
        self.metrics = {}
        
        # Expected 32 tables from Phase1 validation script
        self.expected_tables = {
            # Dimension Tables (22)
            'dim_property', 'dim_unit', 'dim_account', 'dim_accounttree',
            'dim_accounttreeaccountmapping', 'dim_book', 'dim_date', 'dim_commcustomer',
            'dim_commlease', 'dim_commleasetype', 'dim_fp_amendmentsunitspropertytenant',
            'dim_fp_amendmentchargeschedule', 'dim_fp_chargecodetypeandgl',
            'dim_fp_buildingcustomdata', 'dim_moveoutreasons', 'dim_newleasereason',
            'dim_renewalreason', 'dim_tenant', 'dim_unittypelist', 'dim_assetstatus',
            'dim_marketsegment', 'dim_yearbuiltcategory',
            
            # Fact Tables (6)
            'fact_total', 'fact_occupancyrentarea', 'fact_expiringleaseunitarea',
            'fact_accountsreceivable', 'fact_leasingactivity', 'fact_marketrentsurvey',
            
            # Specialized Tables (4)
            'bridge_propertymarkets', 'external_market_growth_projections',
            'ref_book_override_logic', 'control_active_scenario'
        }
        
    def validate_table_inventory(self):
        """Validate which expected tables exist and identify missing/extra tables"""
        print("=" * 60)
        print("1. TABLE INVENTORY VALIDATION")
        print("=" * 60)
        
        # Get actual tables from CSV files
        csv_files = list(self.data_path.glob("*.csv"))
        actual_tables = {f.stem.lower() for f in csv_files}
        expected_tables_lower = {t.lower() for t in self.expected_tables}
        
        # Find missing and extra tables
        missing_tables = expected_tables_lower - actual_tables
        extra_tables = actual_tables - expected_tables_lower
        existing_tables = expected_tables_lower.intersection(actual_tables)
        
        # Results summary
        print(f"Expected Tables: {len(self.expected_tables)}")
        print(f"Actual Tables Found: {len(actual_tables)}")
        print(f"Missing Tables: {len(missing_tables)}")
        print(f"Extra Tables: {len(extra_tables)}")
        print(f"Matching Tables: {len(existing_tables)}")
        
        if missing_tables:
            print(f"\n❌ MISSING TABLES ({len(missing_tables)}):")
            for table in sorted(missing_tables):
                print(f"  - {table}")
                self.issues.append(f"Missing table: {table}")
        
        if extra_tables:
            print(f"\n📋 EXTRA TABLES ({len(extra_tables)}):")
            for table in sorted(extra_tables):
                print(f"  + {table}")
        
        self.results['table_inventory'] = {
            'expected_count': len(self.expected_tables),
            'actual_count': len(actual_tables),
            'missing_count': len(missing_tables),
            'extra_count': len(extra_tables),
            'match_count': len(existing_tables),
            'missing_tables': list(missing_tables),
            'extra_tables': list(extra_tables),
            'existing_tables': list(existing_tables)
        }
        
        return existing_tables
    
    def analyze_table_structures(self):
        """Analyze critical table structures and columns"""
        print("\n" + "=" * 60)
        print("2. TABLE STRUCTURE ANALYSIS")
        print("=" * 60)
        
        critical_tables = {
            'dim_property': ['property id', 'property code', 'property name'],
            'dim_fp_amendmentsunitspropertytenant': ['amendment hmy', 'property hmy', 'tenant hmy', 'amendment sequence', 'amendment status'],
            'dim_fp_amendmentchargeschedule': ['amendment hmy', 'charge code', 'monthly amount'],
            'fact_total': ['property id', 'book id', 'account id', 'month', 'amount'],
            'fact_occupancyrentarea': ['property id', 'first day of month', 'occupied area']
        }
        
        structure_results = {}
        
        for table_name, expected_cols in critical_tables.items():
            csv_path = self.data_path / f"{table_name}.csv"
            
            if not csv_path.exists():
                print(f"❌ {table_name}: FILE NOT FOUND")
                self.issues.append(f"Critical table missing: {table_name}")
                continue
                
            try:
                # Read just the header to check columns
                df = pd.read_csv(csv_path, nrows=0)
                actual_cols = [col.lower().strip() for col in df.columns]
                expected_cols_lower = [col.lower() for col in expected_cols]
                
                missing_cols = [col for col in expected_cols_lower if col not in actual_cols]
                
                print(f"\n📊 {table_name.upper()}:")
                print(f"   Total Columns: {len(actual_cols)}")
                print(f"   Expected Critical Columns: {len(expected_cols)}")
                
                if missing_cols:
                    print(f"   ❌ Missing Critical Columns: {missing_cols}")
                    for col in missing_cols:
                        self.issues.append(f"{table_name}: Missing column '{col}'")
                else:
                    print(f"   ✅ All critical columns present")
                
                # Check for data
                row_count = len(pd.read_csv(csv_path))
                print(f"   Record Count: {row_count:,}")
                
                structure_results[table_name] = {
                    'total_columns': len(actual_cols),
                    'missing_critical_columns': missing_cols,
                    'record_count': row_count,
                    'file_exists': True
                }
                
            except Exception as e:
                print(f"❌ {table_name}: Error reading file - {str(e)}")
                self.issues.append(f"{table_name}: Error reading file - {str(e)}")
                structure_results[table_name] = {'file_exists': False, 'error': str(e)}
        
        self.results['table_structures'] = structure_results
    
    def validate_amendment_duplicates(self):
        """Count duplicate active amendments per property/tenant"""
        print("\n" + "=" * 60)
        print("3. AMENDMENT DUPLICATE VALIDATION")
        print("=" * 60)
        
        amendment_file = self.data_path / "dim_fp_amendmentsunitspropertytenant.csv"
        
        if not amendment_file.exists():
            print("❌ Amendment table not found - cannot validate duplicates")
            self.issues.append("Cannot validate amendment duplicates - table missing")
            return
        
        try:
            df = pd.read_csv(amendment_file)
            
            # Normalize column names (handle variations)
            df.columns = df.columns.str.lower().str.strip()
            
            # Map potential column name variations
            column_mapping = {
                'property hmy': ['property hmy', 'property_hmy', 'propertyhmy'],
                'tenant hmy': ['tenant hmy', 'tenant_hmy', 'tenanthmy'],
                'amendment sequence': ['amendment sequence', 'amendment_sequence', 'amendmentsequence'],
                'amendment status': ['amendment status', 'amendment_status', 'amendmentstatus']
            }
            
            actual_columns = {}
            for expected, variations in column_mapping.items():
                found_col = None
                for var in variations:
                    if var in df.columns:
                        found_col = var
                        break
                actual_columns[expected] = found_col
            
            missing_cols = [k for k, v in actual_columns.items() if v is None]
            if missing_cols:
                print(f"❌ Missing required columns: {missing_cols}")
                for col in missing_cols:
                    self.issues.append(f"Amendment table missing column: {col}")
                return
            
            # Analyze amendment data
            print(f"Total Amendments: {len(df):,}")
            
            # Status distribution
            status_col = actual_columns['amendment status']
            status_dist = df[status_col].value_counts()
            print(f"\nAmendment Status Distribution:")
            for status, count in status_dist.items():
                print(f"   {status}: {count:,}")
            
            # Active amendments (Activated + Superseded)
            active_amendments = df[df[status_col].isin(['Activated', 'Superseded'])].copy()
            print(f"\nActive Amendments (Activated + Superseded): {len(active_amendments):,}")
            
            if len(active_amendments) == 0:
                print("❌ No active amendments found")
                self.issues.append("No active amendments found")
                return
            
            # Find latest amendments per property/tenant
            prop_col = actual_columns['property hmy']
            tenant_col = actual_columns['tenant hmy']
            seq_col = actual_columns['amendment sequence']
            
            # Get max sequence per property/tenant
            latest_sequences = active_amendments.groupby([prop_col, tenant_col])[seq_col].max().reset_index()
            
            # Find duplicates (multiple amendments with same latest sequence)
            duplicates = active_amendments.merge(
                latest_sequences,
                on=[prop_col, tenant_col, seq_col]
            ).groupby([prop_col, tenant_col]).size().reset_index(name='count')
            
            duplicate_latest = duplicates[duplicates['count'] > 1]
            
            print(f"\nLatest Amendment Analysis:")
            print(f"   Unique Property/Tenant Combinations: {len(latest_sequences):,}")
            print(f"   Duplicate Latest Amendments: {len(duplicate_latest):,}")
            
            if len(duplicate_latest) > 0:
                print(f"   ❌ Found {len(duplicate_latest)} property/tenant combinations with duplicate latest amendments")
                duplicate_pct = len(duplicate_latest) / len(latest_sequences) * 100
                print(f"   Duplicate Percentage: {duplicate_pct:.2f}%")
                
                self.issues.append(f"Duplicate latest amendments: {len(duplicate_latest)} combinations")
            else:
                print(f"   ✅ No duplicate latest amendments found")
            
            self.results['amendment_duplicates'] = {
                'total_amendments': len(df),
                'active_amendments': len(active_amendments),
                'unique_combinations': len(latest_sequences),
                'duplicate_latest': len(duplicate_latest),
                'duplicate_percentage': len(duplicate_latest) / len(latest_sequences) * 100 if len(latest_sequences) > 0 else 0
            }
            
        except Exception as e:
            print(f"❌ Error validating amendment duplicates: {str(e)}")
            self.issues.append(f"Error validating amendment duplicates: {str(e)}")
    
    def find_orphaned_records(self):
        """Find orphaned records in fact tables"""
        print("\n" + "=" * 60)
        print("4. ORPHANED RECORDS ANALYSIS")
        print("=" * 60)
        
        # Check fact_total orphaned records
        fact_total_file = self.data_path / "fact_total.csv"
        dim_property_file = self.data_path / "dim_property.csv"
        dim_account_file = self.data_path / "dim_account.csv"
        dim_book_file = self.data_path / "dim_book.csv"
        
        orphaned_results = {}
        
        if fact_total_file.exists():
            try:
                fact_total = pd.read_csv(fact_total_file)
                fact_total.columns = fact_total.columns.str.lower().str.strip()
                
                print(f"📊 FACT_TOTAL Analysis:")
                print(f"   Total Records: {len(fact_total):,}")
                
                # Check property orphans
                if dim_property_file.exists():
                    dim_property = pd.read_csv(dim_property_file)
                    dim_property.columns = dim_property.columns.str.lower().str.strip()
                    
                    # Find common property ID column
                    prop_id_col_fact = None
                    prop_id_col_dim = None
                    
                    for col in ['property id', 'property_id', 'propertyid']:
                        if col in fact_total.columns:
                            prop_id_col_fact = col
                            break
                    
                    for col in ['property id', 'property_id', 'propertyid']:
                        if col in dim_property.columns:
                            prop_id_col_dim = col
                            break
                    
                    if prop_id_col_fact and prop_id_col_dim:
                        orphaned_props = fact_total[~fact_total[prop_id_col_fact].isin(dim_property[prop_id_col_dim])]
                        orphan_pct = len(orphaned_props) / len(fact_total) * 100
                        
                        print(f"   Property Orphans: {len(orphaned_props):,} ({orphan_pct:.2f}%)")
                        
                        if len(orphaned_props) > 0:
                            self.issues.append(f"fact_total: {len(orphaned_props)} orphaned property records")
                            
                        orphaned_results['property_orphans'] = {
                            'count': len(orphaned_props),
                            'percentage': orphan_pct,
                            'total_records': len(fact_total)
                        }
                
                # Check account orphans
                if dim_account_file.exists():
                    dim_account = pd.read_csv(dim_account_file)
                    dim_account.columns = dim_account.columns.str.lower().str.strip()
                    
                    # Find common account ID column
                    acc_id_col_fact = None
                    acc_id_col_dim = None
                    
                    for col in ['account id', 'account_id', 'accountid']:
                        if col in fact_total.columns:
                            acc_id_col_fact = col
                            break
                    
                    for col in ['account id', 'account_id', 'accountid']:
                        if col in dim_account.columns:
                            acc_id_col_dim = col
                            break
                    
                    if acc_id_col_fact and acc_id_col_dim:
                        orphaned_accs = fact_total[~fact_total[acc_id_col_fact].isin(dim_account[acc_id_col_dim])]
                        orphan_pct = len(orphaned_accs) / len(fact_total) * 100
                        
                        print(f"   Account Orphans: {len(orphaned_accs):,} ({orphan_pct:.2f}%)")
                        
                        if len(orphaned_accs) > 0:
                            self.issues.append(f"fact_total: {len(orphaned_accs)} orphaned account records")
                            
                        orphaned_results['account_orphans'] = {
                            'count': len(orphaned_accs),
                            'percentage': orphan_pct,
                            'total_records': len(fact_total)
                        }
                
                self.results['orphaned_records'] = orphaned_results
                
            except Exception as e:
                print(f"❌ Error analyzing orphaned records: {str(e)}")
                self.issues.append(f"Error analyzing orphaned records: {str(e)}")
        else:
            print("❌ fact_total.csv not found")
            self.issues.append("fact_total table missing - cannot check orphaned records")
    
    def validate_amendment_rent_charges(self):
        """Identify amendments missing rent charges"""
        print("\n" + "=" * 60)
        print("5. AMENDMENT RENT CHARGES VALIDATION")
        print("=" * 60)
        
        amendment_file = self.data_path / "dim_fp_amendmentsunitspropertytenant.csv"
        charges_file = self.data_path / "dim_fp_amendmentchargeschedule.csv"
        
        if not amendment_file.exists():
            print("❌ Amendment table not found")
            self.issues.append("Amendment table missing - cannot validate rent charges")
            return
        
        if not charges_file.exists():
            print("❌ Charge schedule table not found")
            self.issues.append("Charge schedule table missing - cannot validate rent charges")
            return
        
        try:
            amendments = pd.read_csv(amendment_file)
            charges = pd.read_csv(charges_file)
            
            amendments.columns = amendments.columns.str.lower().str.strip()
            charges.columns = charges.columns.str.lower().str.strip()
            
            # Find amendment HMY column
            amendment_id_col = None
            for col in ['amendment hmy', 'amendment_hmy', 'amendmenthmy']:
                if col in amendments.columns:
                    amendment_id_col = col
                    break
            
            charges_amendment_col = None
            for col in ['amendment hmy', 'amendment_hmy', 'amendmenthmy']:
                if col in charges.columns:
                    charges_amendment_col = col
                    break
            
            if not amendment_id_col or not charges_amendment_col:
                print("❌ Cannot find amendment ID columns for linking")
                self.issues.append("Missing amendment ID columns for rent charge validation")
                return
            
            # Get active amendments
            status_col = None
            for col in ['amendment status', 'amendment_status', 'amendmentstatus']:
                if col in amendments.columns:
                    status_col = col
                    break
            
            if status_col:
                active_amendments = amendments[amendments[status_col].isin(['Activated', 'Superseded'])]
            else:
                active_amendments = amendments
            
            print(f"Active Amendments: {len(active_amendments):,}")
            print(f"Charge Records: {len(charges):,}")
            
            # Find amendments without charges
            amendments_with_charges = active_amendments[active_amendments[amendment_id_col].isin(charges[charges_amendment_col])]
            amendments_without_charges = active_amendments[~active_amendments[amendment_id_col].isin(charges[charges_amendment_col])]
            
            missing_charges_pct = len(amendments_without_charges) / len(active_amendments) * 100
            
            print(f"\nRent Charges Analysis:")
            print(f"   Amendments with Charges: {len(amendments_with_charges):,}")
            print(f"   Amendments without Charges: {len(amendments_without_charges):,}")
            print(f"   Missing Charges Percentage: {missing_charges_pct:.2f}%")
            
            if len(amendments_without_charges) > 0:
                print(f"   ❌ Found {len(amendments_without_charges)} amendments missing rent charges")
                self.issues.append(f"Amendments missing rent charges: {len(amendments_without_charges)}")
            else:
                print(f"   ✅ All amendments have associated charges")
            
            self.results['amendment_rent_charges'] = {
                'total_active_amendments': len(active_amendments),
                'amendments_with_charges': len(amendments_with_charges),
                'amendments_without_charges': len(amendments_without_charges),
                'missing_charges_percentage': missing_charges_pct
            }
            
        except Exception as e:
            print(f"❌ Error validating amendment rent charges: {str(e)}")
            self.issues.append(f"Error validating amendment rent charges: {str(e)}")
    
    def generate_baseline_metrics(self):
        """Generate baseline metrics and data quality indicators"""
        print("\n" + "=" * 60)
        print("6. BASELINE METRICS CALCULATION")
        print("=" * 60)
        
        total_records = 0
        table_metrics = {}
        
        # Count records in each table
        for csv_file in self.data_path.glob("*.csv"):
            try:
                df = pd.read_csv(csv_file)
                record_count = len(df)
                total_records += record_count
                
                table_metrics[csv_file.stem] = {
                    'record_count': record_count,
                    'column_count': len(df.columns),
                    'file_size_mb': csv_file.stat().st_size / 1024 / 1024
                }
                
            except Exception as e:
                print(f"❌ Error reading {csv_file.name}: {str(e)}")
                table_metrics[csv_file.stem] = {'error': str(e)}
        
        print(f"Total Records Across All Tables: {total_records:,}")
        print(f"Tables with Data: {len([t for t in table_metrics if 'record_count' in table_metrics[t]]):,}")
        
        # Top 10 largest tables by record count
        tables_by_size = sorted(
            [(name, metrics) for name, metrics in table_metrics.items() if 'record_count' in metrics],
            key=lambda x: x[1]['record_count'],
            reverse=True
        )[:10]
        
        print(f"\nTop 10 Tables by Record Count:")
        for name, metrics in tables_by_size:
            print(f"   {name}: {metrics['record_count']:,} records, {metrics['column_count']} columns")
        
        self.results['baseline_metrics'] = {
            'total_records': total_records,
            'total_tables': len(table_metrics),
            'table_metrics': table_metrics,
            'largest_tables': dict(tables_by_size)
        }
    
    def calculate_integrity_score(self):
        """Calculate overall data model integrity score"""
        print("\n" + "=" * 60)
        print("7. DATA MODEL INTEGRITY SCORE")
        print("=" * 60)
        
        score_components = {}
        total_weight = 0
        weighted_score = 0
        
        # Table completeness (30% weight)
        if 'table_inventory' in self.results:
            table_completeness = (self.results['table_inventory']['match_count'] / 
                                self.results['table_inventory']['expected_count']) * 100
            score_components['table_completeness'] = {
                'score': table_completeness,
                'weight': 30,
                'description': f"{self.results['table_inventory']['match_count']}/{self.results['table_inventory']['expected_count']} tables present"
            }
            weighted_score += table_completeness * 30
            total_weight += 30
        
        # Amendment integrity (25% weight)
        if 'amendment_duplicates' in self.results:
            amendment_integrity = max(0, 100 - self.results['amendment_duplicates']['duplicate_percentage'])
            score_components['amendment_integrity'] = {
                'score': amendment_integrity,
                'weight': 25,
                'description': f"{self.results['amendment_duplicates']['duplicate_percentage']:.2f}% duplicate amendments"
            }
            weighted_score += amendment_integrity * 25
            total_weight += 25
        
        # Orphaned records (20% weight)
        if 'orphaned_records' in self.results:
            max_orphan_pct = 0
            if 'property_orphans' in self.results['orphaned_records']:
                max_orphan_pct = max(max_orphan_pct, self.results['orphaned_records']['property_orphans']['percentage'])
            if 'account_orphans' in self.results['orphaned_records']:
                max_orphan_pct = max(max_orphan_pct, self.results['orphaned_records']['account_orphans']['percentage'])
                
            orphan_integrity = max(0, 100 - max_orphan_pct)
            score_components['orphan_integrity'] = {
                'score': orphan_integrity,
                'weight': 20,
                'description': f"{max_orphan_pct:.2f}% max orphaned records"
            }
            weighted_score += orphan_integrity * 20
            total_weight += 20
        
        # Rent charges integrity (15% weight)
        if 'amendment_rent_charges' in self.results:
            charges_integrity = max(0, 100 - self.results['amendment_rent_charges']['missing_charges_percentage'])
            score_components['charges_integrity'] = {
                'score': charges_integrity,
                'weight': 15,
                'description': f"{self.results['amendment_rent_charges']['missing_charges_percentage']:.2f}% missing charges"
            }
            weighted_score += charges_integrity * 15
            total_weight += 15
        
        # Critical tables present (10% weight)
        critical_tables_present = 0
        critical_tables = ['fact_total', 'dim_property', 'dim_fp_amendmentsunitspropertytenant', 'dim_fp_amendmentchargeschedule']
        for table in critical_tables:
            if (self.data_path / f"{table}.csv").exists():
                critical_tables_present += 1
        
        critical_score = (critical_tables_present / len(critical_tables)) * 100
        score_components['critical_tables'] = {
            'score': critical_score,
            'weight': 10,
            'description': f"{critical_tables_present}/{len(critical_tables)} critical tables present"
        }
        weighted_score += critical_score * 10
        total_weight += 10
        
        # Calculate final score
        final_score = weighted_score / total_weight if total_weight > 0 else 0
        
        print(f"Data Model Integrity Score: {final_score:.1f}/100")
        print(f"\nScore Breakdown:")
        for component, details in score_components.items():
            print(f"   {component.replace('_', ' ').title()}: {details['score']:.1f}/100 (weight: {details['weight']}%)")
            print(f"      {details['description']}")
        
        # Determine grade
        if final_score >= 95:
            grade = "A+ (Excellent)"
        elif final_score >= 90:
            grade = "A (Very Good)"
        elif final_score >= 85:
            grade = "B+ (Good)"
        elif final_score >= 80:
            grade = "B (Fair)"
        elif final_score >= 70:
            grade = "C (Needs Improvement)"
        else:
            grade = "D/F (Critical Issues)"
        
        print(f"\nOverall Grade: {grade}")
        
        self.results['integrity_score'] = {
            'final_score': final_score,
            'grade': grade,
            'components': score_components,
            'total_issues': len(self.issues)
        }
    
    def generate_final_report(self):
        """Generate comprehensive validation report"""
        print("\n" + "=" * 80)
        print("YARDI POWER BI DATA MODEL VALIDATION REPORT")
        print("=" * 80)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Data Path: {self.data_path}")
        
        if 'integrity_score' in self.results:
            print(f"\n🎯 OVERALL INTEGRITY SCORE: {self.results['integrity_score']['final_score']:.1f}/100")
            print(f"🏆 GRADE: {self.results['integrity_score']['grade']}")
        
        print(f"\n📊 SUMMARY STATISTICS:")
        if 'table_inventory' in self.results:
            print(f"   Expected Tables: {self.results['table_inventory']['expected_count']}")
            print(f"   Found Tables: {self.results['table_inventory']['actual_count']}")
            print(f"   Missing Tables: {self.results['table_inventory']['missing_count']}")
        
        if 'baseline_metrics' in self.results:
            print(f"   Total Records: {self.results['baseline_metrics']['total_records']:,}")
        
        print(f"\n🚨 CRITICAL ISSUES FOUND: {len(self.issues)}")
        if self.issues:
            for i, issue in enumerate(self.issues, 1):
                print(f"   {i}. {issue}")
        else:
            print("   ✅ No critical issues found!")
        
        print(f"\n📋 RECOMMENDATIONS:")
        if 'table_inventory' in self.results and self.results['table_inventory']['missing_count'] > 0:
            print(f"   1. Add missing tables: {', '.join(self.results['table_inventory']['missing_tables'])}")
        
        if 'amendment_duplicates' in self.results and self.results['amendment_duplicates']['duplicate_latest'] > 0:
            print(f"   2. Resolve {self.results['amendment_duplicates']['duplicate_latest']} duplicate amendment issues")
        
        if any('orphaned' in issue.lower() for issue in self.issues):
            print(f"   3. Clean up orphaned records in fact tables")
        
        if 'amendment_rent_charges' in self.results and self.results['amendment_rent_charges']['amendments_without_charges'] > 0:
            print(f"   4. Add missing rent charge records for {self.results['amendment_rent_charges']['amendments_without_charges']} amendments")
        
        print(f"\n✅ NEXT STEPS:")
        print(f"   1. Review and address critical issues listed above")
        print(f"   2. Run Phase 2 DAX validation after data cleanup")
        print(f"   3. Implement data quality monitoring")
        print(f"   4. Schedule regular validation runs")
        
        return self.results

def main():
    """Main execution function"""
    data_path = "/Users/michaeltang/Documents/GitHub/BI/PBI v1.7/Data/Yardi_Tables"
    
    print("🔍 Starting Yardi Power BI Data Model Validation")
    print(f"📁 Data Path: {data_path}")
    
    validator = YardiDataModelValidator(data_path)
    
    # Run all validation steps
    existing_tables = validator.validate_table_inventory()
    validator.analyze_table_structures()
    validator.validate_amendment_duplicates()
    validator.find_orphaned_records()
    validator.validate_amendment_rent_charges()
    validator.generate_baseline_metrics()
    validator.calculate_integrity_score()
    
    # Generate final report
    results = validator.generate_final_report()
    
    return results

if __name__ == "__main__":
    results = main()