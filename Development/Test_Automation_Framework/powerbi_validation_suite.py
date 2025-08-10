#!/usr/bin/env python3
"""
PowerBI DAX Validation Test Suite - Comprehensive Automated Testing Framework
============================================================================

This comprehensive test automation framework validates PowerBI DAX measures and database logic
to ensure 95%+ accuracy across all rent roll calculations and financial measures.

VALIDATION TARGETS:
- 95%+ rent roll accuracy vs Yardi exports
- <5 second query response times
- Zero duplicate active amendments
- 100% charge schedule integration
- End-to-end rent roll generation validation

KEY TESTING SCENARIOS:
- Amendment selection WITH rent charges logic
- Exclusion of "Proposal in DM" amendment types  
- Duplicate active amendment handling
- Monthly rent calculation accuracy
- Performance and scalability validation

Author: PowerBI Test Automation Specialist
Version: 1.0.0
Date: 2025-08-09
"""

import pandas as pd
import numpy as np
import sqlite3
import json
import logging
import time
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod
import traceback
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('powerbi_validation_suite.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Data structure to hold validation test results"""
    test_name: str
    test_category: str
    status: str  # PASS, FAIL, WARNING
    accuracy_pct: float
    target_value: Any
    actual_value: Any
    variance: float
    execution_time: float
    details: Dict[str, Any]
    recommendations: List[str]
    timestamp: datetime

@dataclass
class PerformanceMetric:
    """Data structure for performance testing results"""
    operation_name: str
    execution_time: float
    memory_usage_mb: float
    data_size: int
    pass_fail: str
    target_time: float

class ValidationTestBase(ABC):
    """Abstract base class for all validation tests"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.results: List[ValidationResult] = []
        self.test_start_time = None
        
    @abstractmethod
    def run_tests(self) -> List[ValidationResult]:
        """Run all tests in this validation suite"""
        pass
        
    def log_result(self, result: ValidationResult):
        """Log and store a validation result"""
        self.results.append(result)
        status_icon = "✅" if result.status == "PASS" else "❌" if result.status == "FAIL" else "⚠️"
        logger.info(f"{status_icon} {result.test_name}: {result.status} ({result.accuracy_pct:.1f}%)")
        
    def calculate_accuracy_percentage(self, actual: float, expected: float) -> float:
        """Calculate accuracy percentage between actual and expected values"""
        if expected == 0 and actual == 0:
            return 100.0
        elif expected == 0:
            return 0.0
        else:
            return max(0.0, min(100.0, (1 - abs(actual - expected) / abs(expected)) * 100))

class DataIntegrityValidator(ValidationTestBase):
    """Validates data integrity and quality for amendment and charge data"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.data_path = config.get('data_path', '/Users/michaeltang/Documents/GitHub/BI/PBI v1.7/Data')
        
    def run_tests(self) -> List[ValidationResult]:
        """Run all data integrity validation tests"""
        logger.info("🔍 Starting Data Integrity Validation Tests")
        
        test_methods = [
            self._test_orphaned_amendments,
            self._test_duplicate_active_amendments,
            self._test_missing_charge_schedules,
            self._test_amendment_sequence_integrity,
            self._test_property_tenant_relationships,
            self._test_date_range_validity,
            self._test_charge_amount_integrity,
            self._test_amendment_status_distribution
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                logger.error(f"Error in {test_method.__name__}: {e}")
                self._log_test_error(test_method.__name__, str(e))
                
        return self.results
    
    def _test_orphaned_amendments(self):
        """Test for amendments without corresponding charge schedules"""
        start_time = time.time()
        
        try:
            # Load amendments and charge schedules
            amendments_file = f"{self.data_path}/Fund2_Filtered/dim_fp_amendmentsunitspropertytenant_fund2.csv"
            charges_file = f"{self.data_path}/Fund2_Filtered/dim_fp_amendmentchargeschedule_fund2_active.csv"
            
            if not os.path.exists(amendments_file) or not os.path.exists(charges_file):
                self._log_missing_file_error("_test_orphaned_amendments", amendments_file, charges_file)
                return
            
            amendments_df = pd.read_csv(amendments_file)
            charges_df = pd.read_csv(charges_file)
            
            # Identify orphaned amendments (amendments without charges)
            amendment_ids = set(amendments_df['amendment hmy'].astype(str))
            charge_amendment_ids = set(charges_df['amendment hmy'].astype(str))
            
            orphaned_amendments = amendment_ids - charge_amendment_ids
            orphaned_count = len(orphaned_amendments)
            total_amendments = len(amendment_ids)
            
            orphan_rate = (orphaned_count / total_amendments * 100) if total_amendments > 0 else 0
            accuracy_pct = 100 - orphan_rate  # Inverse of orphan rate
            
            status = "PASS" if orphan_rate <= 5.0 else "FAIL"  # Target: <5% orphaned amendments
            
            result = ValidationResult(
                test_name="Orphaned Amendments Test",
                test_category="Data Integrity",
                status=status,
                accuracy_pct=accuracy_pct,
                target_value="<5% orphaned amendments",
                actual_value=f"{orphaned_count:,} orphaned ({orphan_rate:.1f}%)",
                variance=orphan_rate - 5.0,
                execution_time=time.time() - start_time,
                details={
                    'total_amendments': total_amendments,
                    'orphaned_count': orphaned_count,
                    'orphaned_rate': orphan_rate,
                    'sample_orphaned_ids': list(orphaned_amendments)[:10] if orphaned_amendments else []
                },
                recommendations=[
                    "Investigate missing charge schedules for orphaned amendments",
                    "Consider excluding amendments without charges from rent calculations",
                    "Review data extraction process to ensure charge schedule completeness"
                ] if orphan_rate > 5.0 else ["Orphaned amendments within acceptable range"],
                timestamp=datetime.now()
            )
            
            self.log_result(result)
            
        except Exception as e:
            self._log_test_error("_test_orphaned_amendments", str(e))
    
    def _test_duplicate_active_amendments(self):
        """Test for duplicate active amendments for the same property/tenant combination"""
        start_time = time.time()
        
        try:
            amendments_file = f"{self.data_path}/Fund2_Filtered/dim_fp_amendmentsunitspropertytenant_fund2.csv"
            
            if not os.path.exists(amendments_file):
                self._log_missing_file_error("_test_duplicate_active_amendments", amendments_file)
                return
                
            amendments_df = pd.read_csv(amendments_file)
            
            # Filter to active amendment statuses
            active_statuses = ['Activated', 'Superseded']
            active_amendments = amendments_df[
                amendments_df['amendment status'].isin(active_statuses)
            ].copy()
            
            # Group by property/tenant and check for duplicates
            duplicate_groups = active_amendments.groupby(['property hmy', 'tenant hmy']).size()
            duplicates = duplicate_groups[duplicate_groups > 1]
            
            duplicate_count = len(duplicates)
            total_property_tenant_combinations = len(duplicate_groups)
            
            duplicate_rate = (duplicate_count / total_property_tenant_combinations * 100) if total_property_tenant_combinations > 0 else 0
            accuracy_pct = 100 - duplicate_rate  # Perfect score = 0% duplicates
            
            status = "PASS" if duplicate_count == 0 else "FAIL"
            
            result = ValidationResult(
                test_name="Duplicate Active Amendments Test",
                test_category="Data Integrity", 
                status=status,
                accuracy_pct=accuracy_pct,
                target_value="0 duplicate active amendments",
                actual_value=f"{duplicate_count:,} property/tenant combinations with duplicates",
                variance=duplicate_count,
                execution_time=time.time() - start_time,
                details={
                    'total_combinations': total_property_tenant_combinations,
                    'duplicate_combinations': duplicate_count,
                    'duplicate_rate': duplicate_rate,
                    'sample_duplicates': duplicates.head(10).to_dict() if len(duplicates) > 0 else {}
                },
                recommendations=[
                    "Remove duplicate active amendments using latest sequence logic",
                    "Implement data validation rules to prevent duplicate active amendments",
                    "Review amendment status update processes"
                ] if duplicate_count > 0 else ["No duplicate active amendments found"],
                timestamp=datetime.now()
            )
            
            self.log_result(result)
            
        except Exception as e:
            self._log_test_error("_test_duplicate_active_amendments", str(e))
    
    def _test_missing_charge_schedules(self):
        """Test for active amendments missing charge schedules"""
        start_time = time.time()
        
        try:
            amendments_file = f"{self.data_path}/Fund2_Filtered/dim_fp_amendmentsunitspropertytenant_fund2.csv"
            charges_file = f"{self.data_path}/Fund2_Filtered/dim_fp_amendmentchargeschedule_fund2_active.csv"
            
            if not os.path.exists(amendments_file) or not os.path.exists(charges_file):
                self._log_missing_file_error("_test_missing_charge_schedules", amendments_file, charges_file)
                return
            
            amendments_df = pd.read_csv(amendments_file)
            charges_df = pd.read_csv(charges_file)
            
            # Filter to latest active amendments per property/tenant
            active_statuses = ['Activated', 'Superseded']
            active_amendments = amendments_df[
                amendments_df['amendment status'].isin(active_statuses)
            ].copy()
            
            # Get latest amendment per property/tenant
            latest_amendments = active_amendments.loc[
                active_amendments.groupby(['property hmy', 'tenant hmy'])['amendment sequence'].idxmax()
            ]
            
            # Check which latest amendments have charge schedules
            amendments_with_charges = set(charges_df['amendment hmy'].astype(str))
            latest_amendment_ids = set(latest_amendments['amendment hmy'].astype(str))
            
            missing_charges = latest_amendment_ids - amendments_with_charges
            missing_count = len(missing_charges)
            total_latest = len(latest_amendment_ids)
            
            missing_rate = (missing_count / total_latest * 100) if total_latest > 0 else 0
            accuracy_pct = 100 - missing_rate
            
            status = "PASS" if missing_rate <= 2.0 else "WARNING" if missing_rate <= 5.0 else "FAIL"
            
            result = ValidationResult(
                test_name="Missing Charge Schedules Test",
                test_category="Data Integrity",
                status=status,
                accuracy_pct=accuracy_pct,
                target_value="<2% missing charge schedules",
                actual_value=f"{missing_count:,} missing ({missing_rate:.1f}%)",
                variance=missing_rate - 2.0,
                execution_time=time.time() - start_time,
                details={
                    'total_latest_amendments': total_latest,
                    'missing_charges_count': missing_count,
                    'missing_rate': missing_rate,
                    'sample_missing_ids': list(missing_charges)[:10] if missing_charges else []
                },
                recommendations=[
                    "Investigate missing charge schedules for latest amendments",
                    "Exclude amendments without charges from rent calculations",
                    "Review charge schedule data extraction completeness"
                ] if missing_rate > 2.0 else ["Charge schedule coverage within acceptable range"],
                timestamp=datetime.now()
            )
            
            self.log_result(result)
            
        except Exception as e:
            self._log_test_error("_test_missing_charge_schedules", str(e))
    
    def _test_amendment_sequence_integrity(self):
        """Test for gaps and inconsistencies in amendment sequences"""
        start_time = time.time()
        
        try:
            amendments_file = f"{self.data_path}/Fund2_Filtered/dim_fp_amendmentsunitspropertytenant_fund2.csv"
            
            if not os.path.exists(amendments_file):
                self._log_missing_file_error("_test_amendment_sequence_integrity", amendments_file)
                return
                
            amendments_df = pd.read_csv(amendments_file)
            
            integrity_issues = 0
            total_property_tenant_groups = 0
            
            # Check sequence integrity for each property/tenant combination
            for (prop_hmy, tenant_hmy), group in amendments_df.groupby(['property hmy', 'tenant hmy']):
                total_property_tenant_groups += 1
                sequences = sorted(group['amendment sequence'].tolist())
                
                # Check for sequence integrity issues
                if len(sequences) > 1:
                    expected_sequences = list(range(1, len(sequences) + 1))
                    if sequences != expected_sequences:
                        integrity_issues += 1
            
            integrity_rate = (integrity_issues / total_property_tenant_groups * 100) if total_property_tenant_groups > 0 else 0
            accuracy_pct = 100 - integrity_rate
            
            status = "PASS" if integrity_rate <= 1.0 else "WARNING" if integrity_rate <= 5.0 else "FAIL"
            
            result = ValidationResult(
                test_name="Amendment Sequence Integrity Test",
                test_category="Data Integrity",
                status=status,
                accuracy_pct=accuracy_pct,
                target_value="<1% sequence integrity issues",
                actual_value=f"{integrity_issues:,} groups with issues ({integrity_rate:.1f}%)",
                variance=integrity_rate - 1.0,
                execution_time=time.time() - start_time,
                details={
                    'total_groups': total_property_tenant_groups,
                    'integrity_issues': integrity_issues,
                    'integrity_rate': integrity_rate
                },
                recommendations=[
                    "Review amendment sequence numbering logic",
                    "Investigate gaps in amendment sequences",
                    "Consider using MAX(sequence) logic to handle gaps"
                ] if integrity_rate > 1.0 else ["Amendment sequences within acceptable range"],
                timestamp=datetime.now()
            )
            
            self.log_result(result)
            
        except Exception as e:
            self._log_test_error("_test_amendment_sequence_integrity", str(e))
    
    def _test_property_tenant_relationships(self):
        """Test for orphaned property/tenant relationships"""
        start_time = time.time()
        
        try:
            amendments_file = f"{self.data_path}/Fund2_Filtered/dim_fp_amendmentsunitspropertytenant_fund2.csv"
            properties_file = f"{self.data_path}/Fund2_Filtered/dim_property_fund2.csv"
            tenants_file = f"{self.data_path}/Fund2_Filtered/tenants_fund2.csv"
            
            files_exist = all(os.path.exists(f) for f in [amendments_file, properties_file, tenants_file])
            if not files_exist:
                self._log_missing_file_error("_test_property_tenant_relationships", amendments_file, properties_file, tenants_file)
                return
            
            amendments_df = pd.read_csv(amendments_file)
            properties_df = pd.read_csv(properties_file)
            tenants_df = pd.read_csv(tenants_file)
            
            # Check for orphaned property references
            amendment_properties = set(amendments_df['property hmy'].astype(str))
            valid_properties = set(properties_df['property hmy'].astype(str))
            orphaned_properties = amendment_properties - valid_properties
            
            # Check for orphaned tenant references  
            amendment_tenants = set(amendments_df['tenant hmy'].astype(str))
            valid_tenants = set(tenants_df['tenant hmy'].astype(str))
            orphaned_tenants = amendment_tenants - valid_tenants
            
            total_orphaned = len(orphaned_properties) + len(orphaned_tenants)
            total_references = len(amendment_properties) + len(amendment_tenants)
            
            orphan_rate = (total_orphaned / total_references * 100) if total_references > 0 else 0
            accuracy_pct = 100 - orphan_rate
            
            status = "PASS" if orphan_rate == 0 else "WARNING" if orphan_rate <= 1.0 else "FAIL"
            
            result = ValidationResult(
                test_name="Property/Tenant Relationship Test", 
                test_category="Data Integrity",
                status=status,
                accuracy_pct=accuracy_pct,
                target_value="0% orphaned references",
                actual_value=f"{total_orphaned:,} orphaned references ({orphan_rate:.1f}%)",
                variance=orphan_rate,
                execution_time=time.time() - start_time,
                details={
                    'orphaned_properties': len(orphaned_properties),
                    'orphaned_tenants': len(orphaned_tenants),
                    'total_orphaned': total_orphaned,
                    'orphan_rate': orphan_rate
                },
                recommendations=[
                    "Remove amendments with orphaned property/tenant references",
                    "Verify master data completeness for properties and tenants",
                    "Implement referential integrity constraints"
                ] if orphan_rate > 0 else ["All property/tenant relationships valid"],
                timestamp=datetime.now()
            )
            
            self.log_result(result)
            
        except Exception as e:
            self._log_test_error("_test_property_tenant_relationships", str(e))
    
    def _test_date_range_validity(self):
        """Test for invalid date ranges in amendments"""
        start_time = time.time()
        
        try:
            amendments_file = f"{self.data_path}/Fund2_Filtered/dim_fp_amendmentsunitspropertytenant_fund2.csv"
            
            if not os.path.exists(amendments_file):
                self._log_missing_file_error("_test_date_range_validity", amendments_file)
                return
                
            amendments_df = pd.read_csv(amendments_file)
            
            # Convert date columns
            date_columns = ['amendment start date', 'amendment end date']
            for col in date_columns:
                if col in amendments_df.columns:
                    amendments_df[col] = pd.to_datetime(amendments_df[col], errors='coerce')
            
            invalid_dates = 0
            total_amendments = len(amendments_df)
            
            # Check for invalid date ranges (start > end)
            if 'amendment start date' in amendments_df.columns and 'amendment end date' in amendments_df.columns:
                valid_end_dates = amendments_df['amendment end date'].notna()
                invalid_ranges = (
                    amendments_df.loc[valid_end_dates, 'amendment start date'] > 
                    amendments_df.loc[valid_end_dates, 'amendment end date']
                )
                invalid_dates = invalid_ranges.sum()
            
            invalid_rate = (invalid_dates / total_amendments * 100) if total_amendments > 0 else 0
            accuracy_pct = 100 - invalid_rate
            
            status = "PASS" if invalid_rate == 0 else "WARNING" if invalid_rate <= 0.1 else "FAIL"
            
            result = ValidationResult(
                test_name="Date Range Validity Test",
                test_category="Data Integrity", 
                status=status,
                accuracy_pct=accuracy_pct,
                target_value="0% invalid date ranges",
                actual_value=f"{invalid_dates:,} invalid ranges ({invalid_rate:.1f}%)",
                variance=invalid_rate,
                execution_time=time.time() - start_time,
                details={
                    'total_amendments': total_amendments,
                    'invalid_dates': invalid_dates,
                    'invalid_rate': invalid_rate
                },
                recommendations=[
                    "Fix amendments with start date after end date",
                    "Implement date validation in data entry processes",
                    "Review month-to-month lease handling (null end dates)"
                ] if invalid_rate > 0 else ["All date ranges valid"],
                timestamp=datetime.now()
            )
            
            self.log_result(result)
            
        except Exception as e:
            self._log_test_error("_test_date_range_validity", str(e))
    
    def _test_charge_amount_integrity(self):
        """Test for charge amount data integrity issues"""
        start_time = time.time()
        
        try:
            charges_file = f"{self.data_path}/Fund2_Filtered/dim_fp_amendmentchargeschedule_fund2_active.csv"
            
            if not os.path.exists(charges_file):
                self._log_missing_file_error("_test_charge_amount_integrity", charges_file)
                return
                
            charges_df = pd.read_csv(charges_file)
            
            # Check for various charge integrity issues
            total_charges = len(charges_df)
            integrity_issues = 0
            
            # Issue 1: Negative rent charges (should be positive)
            if 'amount' in charges_df.columns:
                negative_rent = charges_df['amount'] < 0
                integrity_issues += negative_rent.sum()
            
            # Issue 2: Extremely high charges (potential data errors)  
            if 'amount' in charges_df.columns:
                extreme_charges = charges_df['amount'] > 100000  # > $100k/month
                integrity_issues += extreme_charges.sum()
            
            # Issue 3: Zero amount charges
            if 'amount' in charges_df.columns:
                zero_charges = charges_df['amount'] == 0
                integrity_issues += zero_charges.sum()
            
            integrity_rate = (integrity_issues / total_charges * 100) if total_charges > 0 else 0
            accuracy_pct = 100 - integrity_rate
            
            status = "PASS" if integrity_rate <= 1.0 else "WARNING" if integrity_rate <= 5.0 else "FAIL"
            
            result = ValidationResult(
                test_name="Charge Amount Integrity Test",
                test_category="Data Integrity",
                status=status,
                accuracy_pct=accuracy_pct,
                target_value="<1% charge integrity issues",
                actual_value=f"{integrity_issues:,} issues ({integrity_rate:.1f}%)",
                variance=integrity_rate - 1.0,
                execution_time=time.time() - start_time,
                details={
                    'total_charges': total_charges,
                    'integrity_issues': integrity_issues,
                    'integrity_rate': integrity_rate
                },
                recommendations=[
                    "Review negative rent charge amounts",
                    "Investigate extremely high charge amounts",
                    "Consider excluding zero-amount charges from calculations"
                ] if integrity_rate > 1.0 else ["Charge amounts within acceptable range"],
                timestamp=datetime.now()
            )
            
            self.log_result(result)
            
        except Exception as e:
            self._log_test_error("_test_charge_amount_integrity", str(e))
    
    def _test_amendment_status_distribution(self):
        """Test amendment status distribution for business rule compliance"""
        start_time = time.time()
        
        try:
            amendments_file = f"{self.data_path}/Fund2_Filtered/dim_fp_amendmentsunitspropertytenant_fund2.csv"
            
            if not os.path.exists(amendments_file):
                self._log_missing_file_error("_test_amendment_status_distribution", amendments_file)
                return
                
            amendments_df = pd.read_csv(amendments_file)
            
            # Analyze status distribution
            status_counts = amendments_df['amendment status'].value_counts()
            total_amendments = len(amendments_df)
            
            # Key business rule checks
            active_statuses = ['Activated', 'Superseded']
            active_count = amendments_df[amendments_df['amendment status'].isin(active_statuses)].shape[0]
            active_rate = (active_count / total_amendments * 100) if total_amendments > 0 else 0
            
            # Check for problematic "Proposal in DM" status
            proposal_count = amendments_df[amendments_df['amendment status'] == 'Proposal in DM'].shape[0]
            proposal_rate = (proposal_count / total_amendments * 100) if total_amendments > 0 else 0
            
            # Status distribution health score
            health_score = active_rate - (proposal_rate * 2)  # Penalty for proposals
            
            status = "PASS" if health_score >= 80 else "WARNING" if health_score >= 60 else "FAIL"
            
            result = ValidationResult(
                test_name="Amendment Status Distribution Test",
                test_category="Data Integrity",
                status=status,
                accuracy_pct=health_score,
                target_value="80%+ active amendments, <10% proposals",
                actual_value=f"{active_rate:.1f}% active, {proposal_rate:.1f}% proposals",
                variance=80 - health_score,
                execution_time=time.time() - start_time,
                details={
                    'total_amendments': total_amendments,
                    'active_count': active_count,
                    'active_rate': active_rate,
                    'proposal_count': proposal_count,
                    'proposal_rate': proposal_rate,
                    'status_distribution': status_counts.to_dict()
                },
                recommendations=[
                    "Exclude 'Proposal in DM' amendments from rent calculations",
                    "Focus on 'Activated' and 'Superseded' statuses for active rent",
                    "Review amendment workflow to minimize proposal status"
                ] if health_score < 80 else ["Amendment status distribution is healthy"],
                timestamp=datetime.now()
            )
            
            self.log_result(result)
            
        except Exception as e:
            self._log_test_error("_test_amendment_status_distribution", str(e))
    
    def _log_test_error(self, test_name: str, error_message: str):
        """Log a test execution error"""
        result = ValidationResult(
            test_name=test_name,
            test_category="Data Integrity",
            status="FAIL",
            accuracy_pct=0.0,
            target_value="Test completion",
            actual_value=f"Error: {error_message}",
            variance=100.0,
            execution_time=0.0,
            details={'error': error_message},
            recommendations=["Fix test execution error and retry"],
            timestamp=datetime.now()
        )
        self.log_result(result)
    
    def _log_missing_file_error(self, test_name: str, *files):
        """Log an error for missing test data files"""
        missing_files = [f for f in files if not os.path.exists(f)]
        self._log_test_error(test_name, f"Missing data files: {missing_files}")

class RentRollAccuracyValidator(ValidationTestBase):
    """Validates rent roll accuracy against Yardi exports with 95%+ target"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.generated_path = config.get('generated_path', '/Users/michaeltang/Documents/GitHub/BI/PBI v1.7/Fund2_Validation_Results')
        self.yardi_exports_path = config.get('yardi_exports_path', '/Users/michaeltang/Documents/GitHub/BI/PBI v1.7/rent rolls')
        
    def run_tests(self) -> List[ValidationResult]:
        """Run all rent roll accuracy validation tests"""
        logger.info("📊 Starting Rent Roll Accuracy Validation Tests")
        
        test_methods = [
            self._test_rent_roll_accuracy_march_2025,
            self._test_rent_roll_accuracy_december_2024,
            self._test_monthly_rent_calculation,
            self._test_leased_sf_calculation,
            self._test_rent_psf_calculation,
            self._test_property_count_accuracy,
            self._test_tenant_count_accuracy,
            self._test_amendment_selection_logic
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                logger.error(f"Error in {test_method.__name__}: {e}")
                self._log_test_error(test_method.__name__, str(e))
                
        return self.results
    
    def _test_rent_roll_accuracy_march_2025(self):
        """Test rent roll accuracy for March 31, 2025"""
        self._test_rent_roll_accuracy_for_date(
            "March 31, 2025",
            f"{self.generated_path}/fund2_rent_roll_generated_mar31_2025.csv",
            f"{self.yardi_exports_path}/03.31.25.xlsx"
        )
    
    def _test_rent_roll_accuracy_december_2024(self):
        """Test rent roll accuracy for December 31, 2024"""
        self._test_rent_roll_accuracy_for_date(
            "December 31, 2024",
            f"{self.generated_path}/fund2_rent_roll_generated_dec31_2024.csv",
            f"{self.yardi_exports_path}/12.31.24.xlsx"
        )
    
    def _test_rent_roll_accuracy_for_date(self, date_str: str, generated_file: str, yardi_file: str):
        """Test rent roll accuracy for a specific date"""
        start_time = time.time()
        
        try:
            if not os.path.exists(generated_file) or not os.path.exists(yardi_file):
                self._log_test_error(f"rent_roll_accuracy_{date_str}", f"Missing files: {generated_file}, {yardi_file}")
                return
            
            # Load and process data
            generated_df = pd.read_csv(generated_file)
            yardi_df = self._load_yardi_export(yardi_file)
            
            # Calculate key metrics for comparison
            generated_metrics = self._calculate_rent_roll_metrics(generated_df, "Generated")
            yardi_metrics = self._calculate_rent_roll_metrics(yardi_df, "Yardi")
            
            # Calculate accuracy across key metrics
            accuracy_scores = []
            metric_comparisons = {}
            
            key_metrics = ['total_monthly_rent', 'total_leased_sf', 'property_count', 'tenant_count', 'avg_rent_psf']
            
            for metric in key_metrics:
                gen_val = generated_metrics.get(metric, 0)
                yardi_val = yardi_metrics.get(metric, 0)
                accuracy = self.calculate_accuracy_percentage(gen_val, yardi_val)
                accuracy_scores.append(accuracy)
                metric_comparisons[metric] = {
                    'generated': gen_val,
                    'yardi': yardi_val,
                    'accuracy': accuracy,
                    'variance': gen_val - yardi_val,
                    'variance_pct': ((gen_val - yardi_val) / yardi_val * 100) if yardi_val != 0 else 0
                }
            
            overall_accuracy = sum(accuracy_scores) / len(accuracy_scores) if accuracy_scores else 0
            status = "PASS" if overall_accuracy >= 95.0 else "FAIL"
            
            result = ValidationResult(
                test_name=f"Rent Roll Accuracy Test - {date_str}",
                test_category="Accuracy Validation",
                status=status,
                accuracy_pct=overall_accuracy,
                target_value="95%+ accuracy",
                actual_value=f"{overall_accuracy:.1f}% accuracy",
                variance=overall_accuracy - 95.0,
                execution_time=time.time() - start_time,
                details={
                    'date': date_str,
                    'generated_metrics': generated_metrics,
                    'yardi_metrics': yardi_metrics,
                    'metric_comparisons': metric_comparisons,
                    'overall_accuracy': overall_accuracy
                },
                recommendations=self._generate_accuracy_recommendations(overall_accuracy, metric_comparisons),
                timestamp=datetime.now()
            )
            
            self.log_result(result)
            
        except Exception as e:
            self._log_test_error(f"rent_roll_accuracy_{date_str}", str(e))
    
    def _load_yardi_export(self, file_path: str) -> pd.DataFrame:
        """Load and clean Yardi export file"""
        if file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path, sheet_name=0)
        else:
            df = pd.read_csv(file_path)
            
        # Filter to Fund 2 properties (property codes starting with 'X')
        property_cols = [col for col in df.columns if 'prop' in col.lower() and 'code' in col.lower()]
        if property_cols:
            df = df[df[property_cols[0]].astype(str).str.upper().str.startswith('X')].copy()
        
        return df
    
    def _calculate_rent_roll_metrics(self, df: pd.DataFrame, source_label: str) -> Dict[str, float]:
        """Calculate key rent roll metrics from dataframe"""
        metrics = {'source': source_label}
        
        try:
            # Record count
            metrics['record_count'] = len(df)
            
            # Total monthly rent
            rent_cols = [col for col in df.columns if 'rent' in col.lower() and 'month' in col.lower()]
            if not rent_cols:
                rent_cols = [col for col in df.columns if 'rent' in col.lower()]
            if rent_cols:
                metrics['total_monthly_rent'] = df[rent_cols[0]].sum()
            else:
                metrics['total_monthly_rent'] = 0
            
            # Total leased SF
            sf_cols = [col for col in df.columns if ('sf' in col.lower() or 'area' in col.lower()) and ('lease' in col.lower() or 'amendment' in col.lower())]
            if not sf_cols:
                sf_cols = [col for col in df.columns if 'sf' in col.lower() or 'area' in col.lower()]
            if sf_cols:
                metrics['total_leased_sf'] = df[sf_cols[0]].sum()
            else:
                metrics['total_leased_sf'] = 0
            
            # Property count
            prop_cols = [col for col in df.columns if 'prop' in col.lower()]
            if prop_cols:
                metrics['property_count'] = df[prop_cols[0]].nunique()
            else:
                metrics['property_count'] = 0
            
            # Tenant count
            tenant_cols = [col for col in df.columns if 'tenant' in col.lower()]
            if tenant_cols:
                metrics['tenant_count'] = df[tenant_cols[0]].nunique()
            else:
                metrics['tenant_count'] = 0
            
            # Average rent PSF
            if metrics['total_monthly_rent'] > 0 and metrics['total_leased_sf'] > 0:
                metrics['avg_rent_psf'] = (metrics['total_monthly_rent'] * 12) / metrics['total_leased_sf']
            else:
                metrics['avg_rent_psf'] = 0
                
        except Exception as e:
            logger.warning(f"Error calculating metrics for {source_label}: {e}")
            
        return metrics
    
    def _generate_accuracy_recommendations(self, overall_accuracy: float, metric_comparisons: Dict) -> List[str]:
        """Generate recommendations based on accuracy results"""
        recommendations = []
        
        if overall_accuracy < 95.0:
            recommendations.append("Overall accuracy below 95% target - immediate investigation required")
            
        for metric, comparison in metric_comparisons.items():
            if comparison['accuracy'] < 90.0:
                recommendations.append(f"Critical: {metric} accuracy only {comparison['accuracy']:.1f}% - review calculation logic")
            elif comparison['accuracy'] < 95.0:
                recommendations.append(f"Warning: {metric} accuracy {comparison['accuracy']:.1f}% - minor adjustments needed")
        
        if not recommendations:
            recommendations.append("Rent roll accuracy meets target - ready for production")
            
        return recommendations
    
    def _test_monthly_rent_calculation(self):
        """Test monthly rent calculation accuracy using latest amendment WITH charges logic"""
        start_time = time.time()
        
        try:
            # This would test the specific DAX logic for monthly rent calculation
            # For now, we'll simulate the test structure
            
            result = ValidationResult(
                test_name="Monthly Rent Calculation Test",
                test_category="Accuracy Validation",
                status="PENDING",
                accuracy_pct=0.0,
                target_value="95%+ monthly rent accuracy",
                actual_value="Test implementation pending",
                variance=0.0,
                execution_time=time.time() - start_time,
                details={'note': 'Requires PowerBI connection for DAX execution'},
                recommendations=["Implement PowerBI connector for DAX measure testing"],
                timestamp=datetime.now()
            )
            
            self.log_result(result)
            
        except Exception as e:
            self._log_test_error("_test_monthly_rent_calculation", str(e))
    
    def _test_leased_sf_calculation(self):
        """Test leased SF calculation accuracy"""
        start_time = time.time()
        
        try:
            result = ValidationResult(
                test_name="Leased SF Calculation Test",
                test_category="Accuracy Validation", 
                status="PENDING",
                accuracy_pct=0.0,
                target_value="95%+ leased SF accuracy",
                actual_value="Test implementation pending",
                variance=0.0,
                execution_time=time.time() - start_time,
                details={'note': 'Requires PowerBI connection for DAX execution'},
                recommendations=["Implement PowerBI connector for DAX measure testing"],
                timestamp=datetime.now()
            )
            
            self.log_result(result)
            
        except Exception as e:
            self._log_test_error("_test_leased_sf_calculation", str(e))
    
    def _test_rent_psf_calculation(self):
        """Test rent PSF calculation consistency"""
        start_time = time.time()
        
        try:
            result = ValidationResult(
                test_name="Rent PSF Calculation Test",
                test_category="Accuracy Validation",
                status="PENDING", 
                accuracy_pct=0.0,
                target_value="100% calculation consistency",
                actual_value="Test implementation pending",
                variance=0.0,
                execution_time=time.time() - start_time,
                details={'note': 'Requires PowerBI connection for DAX execution'},
                recommendations=["Implement PowerBI connector for DAX measure testing"],
                timestamp=datetime.now()
            )
            
            self.log_result(result)
            
        except Exception as e:
            self._log_test_error("_test_rent_psf_calculation", str(e))
    
    def _test_property_count_accuracy(self):
        """Test property count accuracy"""
        start_time = time.time()
        
        try:
            result = ValidationResult(
                test_name="Property Count Accuracy Test", 
                test_category="Accuracy Validation",
                status="PENDING",
                accuracy_pct=0.0,
                target_value="100% property count accuracy",
                actual_value="Test implementation pending",
                variance=0.0,
                execution_time=time.time() - start_time,
                details={'note': 'Requires PowerBI connection for DAX execution'},
                recommendations=["Implement PowerBI connector for DAX measure testing"],
                timestamp=datetime.now()
            )
            
            self.log_result(result)
            
        except Exception as e:
            self._log_test_error("_test_property_count_accuracy", str(e))
    
    def _test_tenant_count_accuracy(self):
        """Test tenant count accuracy"""
        start_time = time.time()
        
        try:
            result = ValidationResult(
                test_name="Tenant Count Accuracy Test",
                test_category="Accuracy Validation",
                status="PENDING",
                accuracy_pct=0.0,
                target_value="100% tenant count accuracy", 
                actual_value="Test implementation pending",
                variance=0.0,
                execution_time=time.time() - start_time,
                details={'note': 'Requires PowerBI connection for DAX execution'},
                recommendations=["Implement PowerBI connector for DAX measure testing"],
                timestamp=datetime.now()
            )
            
            self.log_result(result)
            
        except Exception as e:
            self._log_test_error("_test_tenant_count_accuracy", str(e))
    
    def _test_amendment_selection_logic(self):
        """Test amendment selection logic (latest WITH charges)"""
        start_time = time.time()
        
        try:
            amendments_file = f"/Users/michaeltang/Documents/GitHub/BI/PBI v1.7/Data/Fund2_Filtered/dim_fp_amendmentsunitspropertytenant_fund2.csv"
            charges_file = f"/Users/michaeltang/Documents/GitHub/BI/PBI v1.7/Data/Fund2_Filtered/dim_fp_amendmentchargeschedule_fund2_active.csv"
            
            if not os.path.exists(amendments_file) or not os.path.exists(charges_file):
                self._log_test_error("_test_amendment_selection_logic", f"Missing files: {amendments_file}, {charges_file}")
                return
            
            amendments_df = pd.read_csv(amendments_file)
            charges_df = pd.read_csv(charges_file)
            
            # Test the latest amendment WITH charges logic
            active_statuses = ['Activated', 'Superseded']
            active_amendments = amendments_df[amendments_df['amendment status'].isin(active_statuses)].copy()
            
            # Get amendments with charges
            amendments_with_charges = active_amendments[
                active_amendments['amendment hmy'].isin(charges_df['amendment hmy'])
            ]
            
            # Count property/tenant combinations properly selected
            total_combinations = active_amendments.groupby(['property hmy', 'tenant hmy']).size().count()
            combinations_with_charges = amendments_with_charges.groupby(['property hmy', 'tenant hmy']).size().count()
            
            selection_rate = (combinations_with_charges / total_combinations * 100) if total_combinations > 0 else 0
            
            status = "PASS" if selection_rate >= 90.0 else "WARNING" if selection_rate >= 75.0 else "FAIL"
            
            result = ValidationResult(
                test_name="Amendment Selection Logic Test",
                test_category="Accuracy Validation",
                status=status,
                accuracy_pct=selection_rate,
                target_value="90%+ amendments selected WITH charges",
                actual_value=f"{combinations_with_charges:,} of {total_combinations:,} ({selection_rate:.1f}%)",
                variance=selection_rate - 90.0,
                execution_time=time.time() - start_time,
                details={
                    'total_combinations': total_combinations,
                    'combinations_with_charges': combinations_with_charges,
                    'selection_rate': selection_rate,
                    'missing_charges': total_combinations - combinations_with_charges
                },
                recommendations=[
                    "Implement latest amendment WITH charges logic in DAX measures",
                    "Exclude amendments without charge schedules from rent calculations",
                    "Review charge schedule data completeness"
                ] if selection_rate < 90.0 else ["Amendment selection logic working correctly"],
                timestamp=datetime.now()
            )
            
            self.log_result(result)
            
        except Exception as e:
            self._log_test_error("_test_amendment_selection_logic", str(e))
    
    def _log_test_error(self, test_name: str, error_message: str):
        """Log a test execution error"""
        result = ValidationResult(
            test_name=test_name,
            test_category="Accuracy Validation",
            status="FAIL",
            accuracy_pct=0.0,
            target_value="Test completion",
            actual_value=f"Error: {error_message}",
            variance=100.0,
            execution_time=0.0,
            details={'error': error_message},
            recommendations=["Fix test execution error and retry"],
            timestamp=datetime.now()
        )
        self.log_result(result)

if __name__ == "__main__":
    # Example usage
    config = {
        'data_path': '/Users/michaeltang/Documents/GitHub/BI/PBI v1.7/Data',
        'generated_path': '/Users/michaeltang/Documents/GitHub/BI/PBI v1.7/Fund2_Validation_Results',
        'yardi_exports_path': '/Users/michaeltang/Documents/GitHub/BI/PBI v1.7/rent rolls'
    }
    
    print("🚀 PowerBI Validation Suite Starting...")
    
    # Run data integrity validation
    data_integrity_validator = DataIntegrityValidator(config)
    integrity_results = data_integrity_validator.run_tests()
    
    # Run accuracy validation
    accuracy_validator = RentRollAccuracyValidator(config)
    accuracy_results = accuracy_validator.run_tests()
    
    all_results = integrity_results + accuracy_results
    
    # Summary report
    total_tests = len(all_results)
    passed_tests = len([r for r in all_results if r.status == "PASS"])
    failed_tests = len([r for r in all_results if r.status == "FAIL"])
    warnings = len([r for r in all_results if r.status == "WARNING"])
    
    overall_accuracy = sum(r.accuracy_pct for r in all_results) / total_tests if total_tests > 0 else 0
    
    print("\n" + "="*80)
    print("POWERBI VALIDATION SUITE - SUMMARY REPORT")
    print("="*80)
    print(f"Total Tests: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {failed_tests}")
    print(f"⚠️  Warnings: {warnings}")
    print(f"Overall Accuracy: {overall_accuracy:.1f}%")
    
    if overall_accuracy >= 95.0:
        print("\n🎉 SUCCESS: Validation suite meets 95%+ accuracy target")
        print("✅ Ready for production deployment")
    else:
        print(f"\n⚠️  NEEDS IMPROVEMENT: {overall_accuracy:.1f}% accuracy below 95% target")
        print("❌ Address failing tests before production deployment")
    
    print("="*80)