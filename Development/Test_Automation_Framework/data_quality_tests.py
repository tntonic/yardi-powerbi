#!/usr/bin/env python3
"""
Data Quality Validation Test Suite
==================================

Comprehensive data quality testing framework for PowerBI data sources.
Focuses on critical data integrity issues that impact accuracy:

KEY DATA QUALITY AREAS:
- Amendment integrity and sequence validation
- Charge schedule completeness and accuracy
- Duplicate record detection and handling
- Referential integrity validation
- Date range and business rule compliance
- Data completeness and consistency

FUND 2 CRITICAL ISSUES ADDRESSED:
- 98 duplicate active amendments (now eliminated)
- Missing charge schedules (98%+ integration target)
- Amendment sequence gaps and inconsistencies  
- Orphaned property/tenant relationships
- Invalid date ranges and business rule violations

Author: PowerBI Data Quality Specialist
Version: 1.0.0
Date: 2025-08-09
"""

import pandas as pd
import numpy as np
import sqlite3
import json
import logging
import os
import sys
from datetime import datetime, timedelta, date
from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass
import traceback
import re
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class DataQualityResult:
    """Data structure for data quality test results"""
    test_id: str
    test_name: str
    category: str
    data_source: str
    total_records: int
    issues_found: int
    issue_rate: float
    severity: str  # CRITICAL/HIGH/MEDIUM/LOW
    status: str    # PASS/FAIL/WARNING
    quality_score: float
    issues_detail: List[Dict[str, Any]]
    recommendations: List[str]
    execution_time: float
    timestamp: datetime

@dataclass
class DataValidationRule:
    """Data validation rule definition"""
    rule_id: str
    rule_name: str
    rule_type: str  # COMPLETENESS/ACCURACY/CONSISTENCY/VALIDITY/UNIQUENESS
    description: str
    validation_function: callable
    severity: str
    target_threshold: float

class DataQualityValidator:
    """Comprehensive data quality validation framework"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.data_path = config.get('data_path', '/Users/michaeltang/Documents/GitHub/BI/PBI v1.7/Data')
        self.results: List[DataQualityResult] = []
        
        # Initialize validation rules
        self.validation_rules = self._initialize_validation_rules()
    
    def _initialize_validation_rules(self) -> List[DataValidationRule]:
        """Initialize comprehensive data validation rules"""
        return [
            # Amendment Data Validation Rules
            DataValidationRule(
                rule_id="AMN_001",
                rule_name="Amendment HMY Uniqueness",
                rule_type="UNIQUENESS", 
                description="Amendment HMY should be unique across all amendments",
                validation_function=self._validate_amendment_hmy_uniqueness,
                severity="CRITICAL",
                target_threshold=100.0
            ),
            DataValidationRule(
                rule_id="AMN_002",
                rule_name="Amendment Sequence Integrity",
                rule_type="CONSISTENCY",
                description="Amendment sequences should be sequential per property/tenant",
                validation_function=self._validate_amendment_sequence_integrity,
                severity="HIGH",
                target_threshold=95.0
            ),
            DataValidationRule(
                rule_id="AMN_003",
                rule_name="Amendment Status Validity",
                rule_type="VALIDITY",
                description="Amendment status should be from valid business values",
                validation_function=self._validate_amendment_status_validity,
                severity="HIGH",
                target_threshold=98.0
            ),
            DataValidationRule(
                rule_id="AMN_004",
                rule_name="Amendment Date Range Validity",
                rule_type="VALIDITY",
                description="Amendment start date should be <= end date",
                validation_function=self._validate_amendment_date_ranges,
                severity="HIGH",
                target_threshold=99.0
            ),
            DataValidationRule(
                rule_id="AMN_005",
                rule_name="Duplicate Active Amendments",
                rule_type="UNIQUENESS",
                description="No duplicate active amendments per property/tenant",
                validation_function=self._validate_duplicate_active_amendments,
                severity="CRITICAL",
                target_threshold=100.0
            ),
            
            # Charge Schedule Validation Rules
            DataValidationRule(
                rule_id="CHG_001",
                rule_name="Charge Amount Validity",
                rule_type="VALIDITY",
                description="Charge amounts should be positive and reasonable",
                validation_function=self._validate_charge_amounts,
                severity="HIGH",
                target_threshold=95.0
            ),
            DataValidationRule(
                rule_id="CHG_002",
                rule_name="Charge Schedule Completeness",
                rule_type="COMPLETENESS",
                description="Active amendments should have charge schedules",
                validation_function=self._validate_charge_completeness,
                severity="CRITICAL",
                target_threshold=98.0
            ),
            DataValidationRule(
                rule_id="CHG_003",
                rule_name="Amendment-Charge Relationship",
                rule_type="CONSISTENCY",
                description="All charges should reference valid amendments",
                validation_function=self._validate_amendment_charge_relationship,
                severity="CRITICAL",
                target_threshold=100.0
            ),
            
            # Property/Tenant Validation Rules
            DataValidationRule(
                rule_id="REF_001",
                rule_name="Property Reference Integrity",
                rule_type="CONSISTENCY",
                description="All property references should be valid",
                validation_function=self._validate_property_references,
                severity="CRITICAL",
                target_threshold=100.0
            ),
            DataValidationRule(
                rule_id="REF_002", 
                rule_name="Tenant Reference Integrity",
                rule_type="CONSISTENCY",
                description="All tenant references should be valid",
                validation_function=self._validate_tenant_references,
                severity="CRITICAL",
                target_threshold=100.0
            ),
            
            # Completeness Validation Rules
            DataValidationRule(
                rule_id="COM_001",
                rule_name="Required Field Completeness",
                rule_type="COMPLETENESS",
                description="Critical fields should not be null",
                validation_function=self._validate_required_fields,
                severity="HIGH",
                target_threshold=95.0
            ),
            
            # Business Rule Validation Rules
            DataValidationRule(
                rule_id="BUS_001",
                rule_name="Fund 2 Property Code Validation",
                rule_type="VALIDITY",
                description="Fund 2 properties should have codes starting with 'X'",
                validation_function=self._validate_fund2_property_codes,
                severity="MEDIUM",
                target_threshold=100.0
            )
        ]
    
    def run_comprehensive_data_quality_validation(self) -> Dict[str, Any]:
        """Run comprehensive data quality validation"""
        logger.info("🔍 Starting Comprehensive Data Quality Validation")
        
        validation_summary = {
            'overall_quality_score': 0.0,
            'critical_issues': 0,
            'high_issues': 0,
            'medium_issues': 0,
            'low_issues': 0,
            'total_tests': len(self.validation_rules),
            'passed_tests': 0,
            'failed_tests': 0,
            'test_results': [],
            'recommendations': []
        }
        
        # Run each validation rule
        for rule in self.validation_rules:
            try:
                logger.info(f"🔍 Running {rule.rule_name}...")
                result = rule.validation_function(rule)
                validation_summary['test_results'].append(result)
                
                # Count issues by severity
                if result.severity == "CRITICAL" and result.status != "PASS":
                    validation_summary['critical_issues'] += 1
                elif result.severity == "HIGH" and result.status != "PASS":
                    validation_summary['high_issues'] += 1
                elif result.severity == "MEDIUM" and result.status != "PASS":
                    validation_summary['medium_issues'] += 1
                elif result.severity == "LOW" and result.status != "PASS":
                    validation_summary['low_issues'] += 1
                
                # Count pass/fail
                if result.status == "PASS":
                    validation_summary['passed_tests'] += 1
                else:
                    validation_summary['failed_tests'] += 1
                    
            except Exception as e:
                logger.error(f"Error running {rule.rule_name}: {e}")
                error_result = self._create_error_result(rule, str(e))
                validation_summary['test_results'].append(error_result)
                validation_summary['failed_tests'] += 1
        
        # Calculate overall quality score
        quality_scores = [result.quality_score for result in validation_summary['test_results']]
        validation_summary['overall_quality_score'] = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        # Generate recommendations
        validation_summary['recommendations'] = self._generate_data_quality_recommendations(validation_summary)
        
        # Save results
        self._save_data_quality_results(validation_summary)
        
        return validation_summary
    
    # Amendment Validation Methods
    def _validate_amendment_hmy_uniqueness(self, rule: DataValidationRule) -> DataQualityResult:
        """Validate amendment HMY uniqueness"""
        start_time = datetime.now()
        
        try:
            amendments_file = f"{self.data_path}/Fund2_Filtered/dim_fp_amendmentsunitspropertytenant_fund2.csv"
            
            if not os.path.exists(amendments_file):
                return self._create_missing_file_result(rule, amendments_file)
            
            amendments_df = pd.read_csv(amendments_file)
            total_records = len(amendments_df)
            
            # Check for duplicate amendment HMY values
            if 'amendment hmy' in amendments_df.columns:
                duplicate_hmys = amendments_df['amendment hmy'].duplicated()
                duplicate_count = duplicate_hmys.sum()
                
                # Get details of duplicate HMYs
                if duplicate_count > 0:
                    duplicate_hmys_list = amendments_df[duplicate_hmys]['amendment hmy'].tolist()
                    issues_detail = [
                        {'duplicate_hmy': hmy} for hmy in set(duplicate_hmys_list[:10])
                    ]
                else:
                    issues_detail = []
            else:
                duplicate_count = total_records  # Treat missing column as all duplicates
                issues_detail = [{'error': 'amendment hmy column not found'}]
            
            issue_rate = (duplicate_count / total_records * 100) if total_records > 0 else 100
            quality_score = 100 - issue_rate
            
            status = "PASS" if duplicate_count == 0 else "FAIL"
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return DataQualityResult(
                test_id=rule.rule_id,
                test_name=rule.rule_name,
                category=rule.rule_type,
                data_source="dim_fp_amendmentsunitspropertytenant_fund2",
                total_records=total_records,
                issues_found=duplicate_count,
                issue_rate=issue_rate,
                severity=rule.severity,
                status=status,
                quality_score=quality_score,
                issues_detail=issues_detail,
                recommendations=[
                    "Remove duplicate amendment HMY records",
                    "Implement unique constraint on amendment HMY",
                    "Review data extraction process for duplicates"
                ] if duplicate_count > 0 else ["Amendment HMY uniqueness maintained"],
                execution_time=execution_time,
                timestamp=start_time
            )
            
        except Exception as e:
            return self._create_error_result(rule, str(e))
    
    def _validate_amendment_sequence_integrity(self, rule: DataValidationRule) -> DataQualityResult:
        """Validate amendment sequence integrity per property/tenant"""
        start_time = datetime.now()
        
        try:
            amendments_file = f"{self.data_path}/Fund2_Filtered/dim_fp_amendmentsunitspropertytenant_fund2.csv"
            
            if not os.path.exists(amendments_file):
                return self._create_missing_file_result(rule, amendments_file)
            
            amendments_df = pd.read_csv(amendments_file)
            total_records = len(amendments_df)
            
            sequence_issues = 0
            issues_detail = []
            
            # Check sequence integrity for each property/tenant combination
            for (prop_hmy, tenant_hmy), group in amendments_df.groupby(['property hmy', 'tenant hmy']):
                sequences = sorted(group['amendment sequence'].tolist())
                
                # Check for gaps in sequence
                if len(sequences) > 1:
                    expected_sequences = list(range(1, len(sequences) + 1))
                    if sequences != expected_sequences:
                        sequence_issues += len(group)
                        issues_detail.append({
                            'property_hmy': prop_hmy,
                            'tenant_hmy': tenant_hmy,
                            'actual_sequences': sequences,
                            'expected_sequences': expected_sequences,
                            'issue_type': 'sequence_gap'
                        })
                        
                        if len(issues_detail) >= 20:  # Limit detail records
                            break
            
            issue_rate = (sequence_issues / total_records * 100) if total_records > 0 else 0
            quality_score = 100 - issue_rate
            
            status = "PASS" if issue_rate <= (100 - rule.target_threshold) else "FAIL"
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return DataQualityResult(
                test_id=rule.rule_id,
                test_name=rule.rule_name,
                category=rule.rule_type,
                data_source="dim_fp_amendmentsunitspropertytenant_fund2",
                total_records=total_records,
                issues_found=sequence_issues,
                issue_rate=issue_rate,
                severity=rule.severity,
                status=status,
                quality_score=quality_score,
                issues_detail=issues_detail,
                recommendations=[
                    "Review amendment sequence numbering process",
                    "Implement sequential validation in data entry",
                    "Use MAX(sequence) logic to handle gaps gracefully"
                ] if issue_rate > (100 - rule.target_threshold) else ["Amendment sequences are properly maintained"],
                execution_time=execution_time,
                timestamp=start_time
            )
            
        except Exception as e:
            return self._create_error_result(rule, str(e))
    
    def _validate_amendment_status_validity(self, rule: DataValidationRule) -> DataQualityResult:
        """Validate amendment status values against business rules"""
        start_time = datetime.now()
        
        try:
            amendments_file = f"{self.data_path}/Fund2_Filtered/dim_fp_amendmentsunitspropertytenant_fund2.csv"
            
            if not os.path.exists(amendments_file):
                return self._create_missing_file_result(rule, amendments_file)
            
            amendments_df = pd.read_csv(amendments_file)
            total_records = len(amendments_df)
            
            # Define valid amendment statuses
            valid_statuses = {
                'Activated', 'Superseded', 'Terminated', 'Expired', 
                'Draft', 'Proposal in DM', 'Cancelled', 'Pending'
            }
            
            if 'amendment status' in amendments_df.columns:
                # Find invalid statuses
                invalid_status_mask = ~amendments_df['amendment status'].isin(valid_statuses)
                invalid_count = invalid_status_mask.sum()
                
                # Get details of invalid statuses
                if invalid_count > 0:
                    invalid_statuses = amendments_df[invalid_status_mask]['amendment status'].value_counts()
                    issues_detail = [
                        {'invalid_status': status, 'count': count} 
                        for status, count in invalid_statuses.head(10).items()
                    ]
                else:
                    issues_detail = []
            else:
                invalid_count = total_records
                issues_detail = [{'error': 'amendment status column not found'}]
            
            issue_rate = (invalid_count / total_records * 100) if total_records > 0 else 100
            quality_score = 100 - issue_rate
            
            status = "PASS" if issue_rate <= (100 - rule.target_threshold) else "FAIL"
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return DataQualityResult(
                test_id=rule.rule_id,
                test_name=rule.rule_name,
                category=rule.rule_type,
                data_source="dim_fp_amendmentsunitspropertytenant_fund2",
                total_records=total_records,
                issues_found=invalid_count,
                issue_rate=issue_rate,
                severity=rule.severity,
                status=status,
                quality_score=quality_score,
                issues_detail=issues_detail,
                recommendations=[
                    "Standardize amendment status values",
                    "Implement status validation in data entry",
                    "Create data cleansing rules for invalid statuses"
                ] if issue_rate > (100 - rule.target_threshold) else ["Amendment statuses are valid"],
                execution_time=execution_time,
                timestamp=start_time
            )
            
        except Exception as e:
            return self._create_error_result(rule, str(e))
    
    def _validate_amendment_date_ranges(self, rule: DataValidationRule) -> DataQualityResult:
        """Validate amendment date ranges (start <= end)"""
        start_time = datetime.now()
        
        try:
            amendments_file = f"{self.data_path}/Fund2_Filtered/dim_fp_amendmentsunitspropertytenant_fund2.csv"
            
            if not os.path.exists(amendments_file):
                return self._create_missing_file_result(rule, amendments_file)
            
            amendments_df = pd.read_csv(amendments_file)
            total_records = len(amendments_df)
            
            # Convert date columns
            date_columns = ['amendment start date', 'amendment end date']
            for col in date_columns:
                if col in amendments_df.columns:
                    amendments_df[col] = pd.to_datetime(amendments_df[col], errors='coerce')
            
            invalid_dates = 0
            issues_detail = []
            
            if all(col in amendments_df.columns for col in date_columns):
                # Find records where start > end (excluding null end dates)
                valid_end_dates = amendments_df['amendment end date'].notna()
                invalid_date_mask = (
                    amendments_df.loc[valid_end_dates, 'amendment start date'] > 
                    amendments_df.loc[valid_end_dates, 'amendment end date']
                )
                
                invalid_dates = invalid_date_mask.sum()
                
                if invalid_dates > 0:
                    invalid_records = amendments_df[valid_end_dates][invalid_date_mask]
                    for _, record in invalid_records.head(10).iterrows():
                        issues_detail.append({
                            'amendment_hmy': record.get('amendment hmy', 'Unknown'),
                            'start_date': record['amendment start date'].isoformat() if pd.notna(record['amendment start date']) else None,
                            'end_date': record['amendment end date'].isoformat() if pd.notna(record['amendment end date']) else None,
                            'issue_type': 'start_after_end'
                        })
            else:
                # Missing required date columns
                invalid_dates = total_records
                issues_detail = [{'error': 'Required date columns not found'}]
            
            issue_rate = (invalid_dates / total_records * 100) if total_records > 0 else 100
            quality_score = 100 - issue_rate
            
            status = "PASS" if issue_rate <= (100 - rule.target_threshold) else "FAIL"
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return DataQualityResult(
                test_id=rule.rule_id,
                test_name=rule.rule_name,
                category=rule.rule_type,
                data_source="dim_fp_amendmentsunitspropertytenant_fund2",
                total_records=total_records,
                issues_found=invalid_dates,
                issue_rate=issue_rate,
                severity=rule.severity,
                status=status,
                quality_score=quality_score,
                issues_detail=issues_detail,
                recommendations=[
                    "Fix amendments with invalid date ranges",
                    "Implement date validation in data entry forms",
                    "Review month-to-month lease handling (null end dates)"
                ] if issue_rate > (100 - rule.target_threshold) else ["Amendment date ranges are valid"],
                execution_time=execution_time,
                timestamp=start_time
            )
            
        except Exception as e:
            return self._create_error_result(rule, str(e))
    
    def _validate_duplicate_active_amendments(self, rule: DataValidationRule) -> DataQualityResult:
        """Validate for duplicate active amendments (Fund 2 critical issue)"""
        start_time = datetime.now()
        
        try:
            amendments_file = f"{self.data_path}/Fund2_Filtered/dim_fp_amendmentsunitspropertytenant_fund2.csv"
            
            if not os.path.exists(amendments_file):
                return self._create_missing_file_result(rule, amendments_file)
            
            amendments_df = pd.read_csv(amendments_file)
            total_records = len(amendments_df)
            
            # Filter to active amendment statuses
            active_statuses = ['Activated', 'Superseded']
            active_amendments = amendments_df[
                amendments_df['amendment status'].isin(active_statuses)
            ].copy()
            
            # Group by property/tenant and find duplicates
            duplicate_groups = active_amendments.groupby(['property hmy', 'tenant hmy']).size()
            duplicates = duplicate_groups[duplicate_groups > 1]
            
            duplicate_count = len(duplicates)
            issues_detail = []
            
            if duplicate_count > 0:
                for (prop_hmy, tenant_hmy), count in duplicates.head(10).items():
                    duplicate_records = active_amendments[
                        (active_amendments['property hmy'] == prop_hmy) &
                        (active_amendments['tenant hmy'] == tenant_hmy)
                    ]
                    
                    issues_detail.append({
                        'property_hmy': prop_hmy,
                        'tenant_hmy': tenant_hmy,
                        'duplicate_count': count,
                        'amendment_sequences': duplicate_records['amendment sequence'].tolist(),
                        'amendment_statuses': duplicate_records['amendment status'].tolist(),
                        'issue_type': 'multiple_active_amendments'
                    })
            
            # Calculate issue rate based on property/tenant combinations
            total_combinations = len(active_amendments.groupby(['property hmy', 'tenant hmy']))
            issue_rate = (duplicate_count / total_combinations * 100) if total_combinations > 0 else 0
            quality_score = 100 - issue_rate
            
            # Fund 2 had 98 duplicates - this is critical
            status = "PASS" if duplicate_count == 0 else "FAIL"
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return DataQualityResult(
                test_id=rule.rule_id,
                test_name=rule.rule_name,
                category=rule.rule_type,
                data_source="dim_fp_amendmentsunitspropertytenant_fund2",
                total_records=total_records,
                issues_found=duplicate_count,
                issue_rate=issue_rate,
                severity=rule.severity,
                status=status,
                quality_score=quality_score,
                issues_detail=issues_detail,
                recommendations=[
                    "Remove duplicate active amendments using latest sequence logic",
                    "Implement data validation to prevent multiple active amendments",
                    "Use MAX(amendment sequence) to select single amendment per property/tenant",
                    "This was a critical Fund 2 issue - ensure it's resolved"
                ] if duplicate_count > 0 else ["No duplicate active amendments found - Fund 2 issue resolved"],
                execution_time=execution_time,
                timestamp=start_time
            )
            
        except Exception as e:
            return self._create_error_result(rule, str(e))
    
    # Charge Schedule Validation Methods
    def _validate_charge_amounts(self, rule: DataValidationRule) -> DataQualityResult:
        """Validate charge amounts for validity and reasonableness"""
        start_time = datetime.now()
        
        try:
            charges_file = f"{self.data_path}/Fund2_Filtered/dim_fp_amendmentchargeschedule_fund2_active.csv"
            
            if not os.path.exists(charges_file):
                return self._create_missing_file_result(rule, charges_file)
            
            charges_df = pd.read_csv(charges_file)
            total_records = len(charges_df)
            
            invalid_amounts = 0
            issues_detail = []
            
            if 'amount' in charges_df.columns:
                # Check for various charge amount issues
                negative_amounts = charges_df['amount'] < 0
                zero_amounts = charges_df['amount'] == 0
                extreme_amounts = charges_df['amount'] > 100000  # >$100k/month
                
                invalid_amounts = negative_amounts.sum() + zero_amounts.sum() + extreme_amounts.sum()
                
                # Collect issue details
                if negative_amounts.sum() > 0:
                    issues_detail.append({
                        'issue_type': 'negative_amounts',
                        'count': negative_amounts.sum(),
                        'severity': 'HIGH'
                    })
                
                if zero_amounts.sum() > 0:
                    issues_detail.append({
                        'issue_type': 'zero_amounts',
                        'count': zero_amounts.sum(),
                        'severity': 'MEDIUM'
                    })
                
                if extreme_amounts.sum() > 0:
                    issues_detail.append({
                        'issue_type': 'extreme_amounts',
                        'count': extreme_amounts.sum(),
                        'threshold': 100000,
                        'severity': 'HIGH'
                    })
            else:
                invalid_amounts = total_records
                issues_detail = [{'error': 'amount column not found'}]
            
            issue_rate = (invalid_amounts / total_records * 100) if total_records > 0 else 100
            quality_score = 100 - issue_rate
            
            status = "PASS" if issue_rate <= (100 - rule.target_threshold) else "FAIL"
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return DataQualityResult(
                test_id=rule.rule_id,
                test_name=rule.rule_name,
                category=rule.rule_type,
                data_source="dim_fp_amendmentchargeschedule_fund2_active",
                total_records=total_records,
                issues_found=invalid_amounts,
                issue_rate=issue_rate,
                severity=rule.severity,
                status=status,
                quality_score=quality_score,
                issues_detail=issues_detail,
                recommendations=[
                    "Review negative charge amounts for data entry errors",
                    "Investigate zero-amount charges",
                    "Validate extreme charge amounts (>$100k/month)",
                    "Implement charge amount validation rules"
                ] if issue_rate > (100 - rule.target_threshold) else ["Charge amounts are within expected ranges"],
                execution_time=execution_time,
                timestamp=start_time
            )
            
        except Exception as e:
            return self._create_error_result(rule, str(e))
    
    def _validate_charge_completeness(self, rule: DataValidationRule) -> DataQualityResult:
        """Validate charge schedule completeness vs amendments (Fund 2 critical)"""
        start_time = datetime.now()
        
        try:
            amendments_file = f"{self.data_path}/Fund2_Filtered/dim_fp_amendmentsunitspropertytenant_fund2.csv"
            charges_file = f"{self.data_path}/Fund2_Filtered/dim_fp_amendmentchargeschedule_fund2_active.csv"
            
            if not os.path.exists(amendments_file) or not os.path.exists(charges_file):
                return self._create_missing_file_result(rule, [amendments_file, charges_file])
            
            amendments_df = pd.read_csv(amendments_file)
            charges_df = pd.read_csv(charges_file)
            
            # Focus on active amendments that should have charges
            active_statuses = ['Activated', 'Superseded']
            active_amendments = amendments_df[
                amendments_df['amendment status'].isin(active_statuses)
            ]
            
            total_active_amendments = len(active_amendments)
            
            # Check how many have charge schedules
            amendments_with_charges = active_amendments[
                active_amendments['amendment hmy'].isin(charges_df['amendment hmy'])
            ]
            
            amendments_with_charges_count = len(amendments_with_charges)
            missing_charges = total_active_amendments - amendments_with_charges_count
            
            # Get latest amendment per property/tenant for more accurate assessment
            latest_amendments = active_amendments.loc[
                active_amendments.groupby(['property hmy', 'tenant hmy'])['amendment sequence'].idxmax()
            ]
            
            latest_with_charges = latest_amendments[
                latest_amendments['amendment hmy'].isin(charges_df['amendment hmy'])
            ]
            
            issue_rate = (missing_charges / total_active_amendments * 100) if total_active_amendments > 0 else 100
            quality_score = 100 - issue_rate
            
            # Fund 2 target: 98%+ charge completeness
            status = "PASS" if issue_rate <= (100 - rule.target_threshold) else "FAIL"
            
            issues_detail = [
                {
                    'total_active_amendments': total_active_amendments,
                    'amendments_with_charges': amendments_with_charges_count,
                    'missing_charges': missing_charges,
                    'latest_amendments': len(latest_amendments),
                    'latest_with_charges': len(latest_with_charges),
                    'issue_type': 'missing_charge_schedules'
                }
            ]
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return DataQualityResult(
                test_id=rule.rule_id,
                test_name=rule.rule_name,
                category=rule.rule_type,
                data_source="amendment_charge_relationship",
                total_records=total_active_amendments,
                issues_found=missing_charges,
                issue_rate=issue_rate,
                severity=rule.severity,
                status=status,
                quality_score=quality_score,
                issues_detail=issues_detail,
                recommendations=[
                    f"Address {missing_charges:,} missing charge schedules for active amendments",
                    "Improve charge schedule extraction from source system",
                    "Target: 98%+ charge completeness for Fund 2 accuracy",
                    "Focus on latest amendments per property/tenant combination"
                ] if issue_rate > (100 - rule.target_threshold) else ["Charge schedule completeness meets Fund 2 target"],
                execution_time=execution_time,
                timestamp=start_time
            )
            
        except Exception as e:
            return self._create_error_result(rule, str(e))
    
    def _validate_amendment_charge_relationship(self, rule: DataValidationRule) -> DataQualityResult:
        """Validate amendment-charge relationship integrity"""
        start_time = datetime.now()
        
        try:
            amendments_file = f"{self.data_path}/Fund2_Filtered/dim_fp_amendmentsunitspropertytenant_fund2.csv"
            charges_file = f"{self.data_path}/Fund2_Filtered/dim_fp_amendmentchargeschedule_fund2_active.csv"
            
            if not os.path.exists(amendments_file) or not os.path.exists(charges_file):
                return self._create_missing_file_result(rule, [amendments_file, charges_file])
            
            amendments_df = pd.read_csv(amendments_file)
            charges_df = pd.read_csv(charges_file)
            
            total_charges = len(charges_df)
            
            # Check for orphaned charges (charges without corresponding amendments)
            charge_amendment_ids = set(charges_df['amendment hmy'].astype(str))
            valid_amendment_ids = set(amendments_df['amendment hmy'].astype(str))
            
            orphaned_charges = charge_amendment_ids - valid_amendment_ids
            orphaned_count = len(orphaned_charges)
            
            issue_rate = (orphaned_count / total_charges * 100) if total_charges > 0 else 0
            quality_score = 100 - issue_rate
            
            status = "PASS" if orphaned_count == 0 else "FAIL"
            
            issues_detail = []
            if orphaned_count > 0:
                issues_detail.append({
                    'issue_type': 'orphaned_charges',
                    'orphaned_count': orphaned_count,
                    'sample_orphaned_ids': list(orphaned_charges)[:10]
                })
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return DataQualityResult(
                test_id=rule.rule_id,
                test_name=rule.rule_name,
                category=rule.rule_type,
                data_source="amendment_charge_relationship",
                total_records=total_charges,
                issues_found=orphaned_count,
                issue_rate=issue_rate,
                severity=rule.severity,
                status=status,
                quality_score=quality_score,
                issues_detail=issues_detail,
                recommendations=[
                    "Remove orphaned charges without valid amendments",
                    "Implement referential integrity constraints",
                    "Review charge extraction process"
                ] if orphaned_count > 0 else ["All charges reference valid amendments"],
                execution_time=execution_time,
                timestamp=start_time
            )
            
        except Exception as e:
            return self._create_error_result(rule, str(e))
    
    # Reference Integrity Validation Methods
    def _validate_property_references(self, rule: DataValidationRule) -> DataQualityResult:
        """Validate property reference integrity"""
        start_time = datetime.now()
        
        try:
            amendments_file = f"{self.data_path}/Fund2_Filtered/dim_fp_amendmentsunitspropertytenant_fund2.csv"
            properties_file = f"{self.data_path}/Fund2_Filtered/dim_property_fund2.csv"
            
            if not os.path.exists(amendments_file) or not os.path.exists(properties_file):
                return self._create_missing_file_result(rule, [amendments_file, properties_file])
            
            amendments_df = pd.read_csv(amendments_file)
            properties_df = pd.read_csv(properties_file)
            
            total_amendments = len(amendments_df)
            
            # Check for orphaned property references
            amendment_properties = set(amendments_df['property hmy'].astype(str))
            valid_properties = set(properties_df['property hmy'].astype(str))
            
            orphaned_properties = amendment_properties - valid_properties
            orphaned_count = len(orphaned_properties)
            
            issue_rate = (orphaned_count / len(amendment_properties) * 100) if len(amendment_properties) > 0 else 0
            quality_score = 100 - issue_rate
            
            status = "PASS" if orphaned_count == 0 else "FAIL"
            
            issues_detail = []
            if orphaned_count > 0:
                issues_detail.append({
                    'issue_type': 'orphaned_property_references',
                    'orphaned_count': orphaned_count,
                    'sample_orphaned_properties': list(orphaned_properties)[:10]
                })
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return DataQualityResult(
                test_id=rule.rule_id,
                test_name=rule.rule_name,
                category=rule.rule_type,
                data_source="property_references",
                total_records=total_amendments,
                issues_found=orphaned_count,
                issue_rate=issue_rate,
                severity=rule.severity,
                status=status,
                quality_score=quality_score,
                issues_detail=issues_detail,
                recommendations=[
                    "Remove amendments with orphaned property references",
                    "Ensure property master data completeness",
                    "Implement foreign key constraints"
                ] if orphaned_count > 0 else ["All property references are valid"],
                execution_time=execution_time,
                timestamp=start_time
            )
            
        except Exception as e:
            return self._create_error_result(rule, str(e))
    
    def _validate_tenant_references(self, rule: DataValidationRule) -> DataQualityResult:
        """Validate tenant reference integrity"""
        start_time = datetime.now()
        
        try:
            amendments_file = f"{self.data_path}/Fund2_Filtered/dim_fp_amendmentsunitspropertytenant_fund2.csv"
            tenants_file = f"{self.data_path}/Fund2_Filtered/tenants_fund2.csv"
            
            if not os.path.exists(amendments_file) or not os.path.exists(tenants_file):
                return self._create_missing_file_result(rule, [amendments_file, tenants_file])
            
            amendments_df = pd.read_csv(amendments_file)
            tenants_df = pd.read_csv(tenants_file)
            
            total_amendments = len(amendments_df)
            
            # Check for orphaned tenant references
            amendment_tenants = set(amendments_df['tenant hmy'].astype(str))
            valid_tenants = set(tenants_df['tenant hmy'].astype(str))
            
            orphaned_tenants = amendment_tenants - valid_tenants
            orphaned_count = len(orphaned_tenants)
            
            issue_rate = (orphaned_count / len(amendment_tenants) * 100) if len(amendment_tenants) > 0 else 0
            quality_score = 100 - issue_rate
            
            status = "PASS" if orphaned_count == 0 else "FAIL"
            
            issues_detail = []
            if orphaned_count > 0:
                issues_detail.append({
                    'issue_type': 'orphaned_tenant_references',
                    'orphaned_count': orphaned_count,
                    'sample_orphaned_tenants': list(orphaned_tenants)[:10]
                })
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return DataQualityResult(
                test_id=rule.rule_id,
                test_name=rule.rule_name,
                category=rule.rule_type,
                data_source="tenant_references",
                total_records=total_amendments,
                issues_found=orphaned_count,
                issue_rate=issue_rate,
                severity=rule.severity,
                status=status,
                quality_score=quality_score,
                issues_detail=issues_detail,
                recommendations=[
                    "Remove amendments with orphaned tenant references",
                    "Ensure tenant master data completeness",
                    "Implement foreign key constraints"
                ] if orphaned_count > 0 else ["All tenant references are valid"],
                execution_time=execution_time,
                timestamp=start_time
            )
            
        except Exception as e:
            return self._create_error_result(rule, str(e))
    
    # Completeness Validation Methods
    def _validate_required_fields(self, rule: DataValidationRule) -> DataQualityResult:
        """Validate completeness of required fields"""
        start_time = datetime.now()
        
        try:
            amendments_file = f"{self.data_path}/Fund2_Filtered/dim_fp_amendmentsunitspropertytenant_fund2.csv"
            
            if not os.path.exists(amendments_file):
                return self._create_missing_file_result(rule, amendments_file)
            
            amendments_df = pd.read_csv(amendments_file)
            total_records = len(amendments_df)
            
            # Define required fields
            required_fields = [
                'amendment hmy',
                'property hmy',
                'tenant hmy', 
                'amendment sequence',
                'amendment status',
                'amendment start date'
            ]
            
            completeness_issues = 0
            issues_detail = []
            
            for field in required_fields:
                if field in amendments_df.columns:
                    null_count = amendments_df[field].isnull().sum()
                    if null_count > 0:
                        completeness_issues += null_count
                        issues_detail.append({
                            'field': field,
                            'null_count': null_count,
                            'completeness_pct': ((total_records - null_count) / total_records * 100)
                        })
                else:
                    completeness_issues += total_records
                    issues_detail.append({
                        'field': field,
                        'error': 'field_missing',
                        'completeness_pct': 0.0
                    })
            
            issue_rate = (completeness_issues / (total_records * len(required_fields)) * 100) if total_records > 0 else 100
            quality_score = 100 - issue_rate
            
            status = "PASS" if issue_rate <= (100 - rule.target_threshold) else "FAIL"
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return DataQualityResult(
                test_id=rule.rule_id,
                test_name=rule.rule_name,
                category=rule.rule_type,
                data_source="dim_fp_amendmentsunitspropertytenant_fund2",
                total_records=total_records,
                issues_found=completeness_issues,
                issue_rate=issue_rate,
                severity=rule.severity,
                status=status,
                quality_score=quality_score,
                issues_detail=issues_detail,
                recommendations=[
                    "Address null values in required fields",
                    "Implement data entry validation",
                    "Review data extraction completeness"
                ] if issue_rate > (100 - rule.target_threshold) else ["Required fields completeness is adequate"],
                execution_time=execution_time,
                timestamp=start_time
            )
            
        except Exception as e:
            return self._create_error_result(rule, str(e))
    
    # Business Rule Validation Methods
    def _validate_fund2_property_codes(self, rule: DataValidationRule) -> DataQualityResult:
        """Validate Fund 2 property codes start with 'X'"""
        start_time = datetime.now()
        
        try:
            properties_file = f"{self.data_path}/Fund2_Filtered/dim_property_fund2.csv"
            
            if not os.path.exists(properties_file):
                return self._create_missing_file_result(rule, properties_file)
            
            properties_df = pd.read_csv(properties_file)
            total_properties = len(properties_df)
            
            invalid_codes = 0
            issues_detail = []
            
            # Check for property codes that don't start with 'X' (Fund 2 convention)
            if 'property code' in properties_df.columns:
                invalid_code_mask = ~properties_df['property code'].astype(str).str.upper().str.startswith('X')
                invalid_codes = invalid_code_mask.sum()
                
                if invalid_codes > 0:
                    invalid_code_samples = properties_df[invalid_code_mask]['property code'].head(10).tolist()
                    issues_detail.append({
                        'issue_type': 'invalid_fund2_property_codes',
                        'invalid_count': invalid_codes,
                        'sample_invalid_codes': invalid_code_samples
                    })
            else:
                invalid_codes = total_properties
                issues_detail.append({'error': 'property code column not found'})
            
            issue_rate = (invalid_codes / total_properties * 100) if total_properties > 0 else 100
            quality_score = 100 - issue_rate
            
            status = "PASS" if invalid_codes == 0 else "WARNING"  # This is business rule, not critical
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return DataQualityResult(
                test_id=rule.rule_id,
                test_name=rule.rule_name,
                category=rule.rule_type,
                data_source="dim_property_fund2",
                total_records=total_properties,
                issues_found=invalid_codes,
                issue_rate=issue_rate,
                severity=rule.severity,
                status=status,
                quality_score=quality_score,
                issues_detail=issues_detail,
                recommendations=[
                    "Verify Fund 2 property code convention (should start with 'X')",
                    "Review property filtering logic",
                    "Confirm this is the correct Fund 2 dataset"
                ] if invalid_codes > 0 else ["Fund 2 property codes follow convention"],
                execution_time=execution_time,
                timestamp=start_time
            )
            
        except Exception as e:
            return self._create_error_result(rule, str(e))
    
    # Helper Methods
    def _create_error_result(self, rule: DataValidationRule, error_message: str) -> DataQualityResult:
        """Create error result for failed validation rules"""
        return DataQualityResult(
            test_id=rule.rule_id,
            test_name=rule.rule_name,
            category=rule.rule_type,
            data_source="ERROR",
            total_records=0,
            issues_found=0,
            issue_rate=100.0,
            severity=rule.severity,
            status="FAIL",
            quality_score=0.0,
            issues_detail=[{'error': error_message, 'traceback': traceback.format_exc()}],
            recommendations=["Fix validation rule execution error"],
            execution_time=0.0,
            timestamp=datetime.now()
        )
    
    def _create_missing_file_result(self, rule: DataValidationRule, missing_files: Any) -> DataQualityResult:
        """Create result for missing data files"""
        if isinstance(missing_files, str):
            missing_files = [missing_files]
            
        return DataQualityResult(
            test_id=rule.rule_id,
            test_name=rule.rule_name,
            category=rule.rule_type,
            data_source="MISSING_FILES",
            total_records=0,
            issues_found=len(missing_files),
            issue_rate=100.0,
            severity=rule.severity,
            status="FAIL",
            quality_score=0.0,
            issues_detail=[{'missing_files': missing_files}],
            recommendations=["Ensure required data files are available for validation"],
            execution_time=0.0,
            timestamp=datetime.now()
        )
    
    def _generate_data_quality_recommendations(self, validation_summary: Dict[str, Any]) -> List[str]:
        """Generate comprehensive data quality recommendations"""
        recommendations = []
        
        overall_score = validation_summary.get('overall_quality_score', 0)
        critical_issues = validation_summary.get('critical_issues', 0)
        high_issues = validation_summary.get('high_issues', 0)
        
        # Overall assessment
        if overall_score >= 95.0:
            recommendations.append("🎉 Excellent data quality - meets production standards")
        elif overall_score >= 85.0:
            recommendations.append("✅ Good data quality - minor improvements needed")
        elif overall_score >= 75.0:
            recommendations.append("⚠️ Moderate data quality - address identified issues")
        else:
            recommendations.append("❌ Poor data quality - critical remediation required")
        
        # Priority-based recommendations
        if critical_issues > 0:
            recommendations.append(f"🚨 CRITICAL: Address {critical_issues} critical data quality issues immediately")
            recommendations.append("Critical issues block production deployment")
        
        if high_issues > 0:
            recommendations.append(f"⚠️ HIGH: Resolve {high_issues} high-priority data quality issues")
        
        # Specific Fund 2 recommendations
        test_results = validation_summary.get('test_results', [])
        duplicate_amendment_test = next((r for r in test_results if r.test_id == "AMN_005"), None)
        if duplicate_amendment_test and duplicate_amendment_test.status == "FAIL":
            recommendations.append("🔧 FUND 2 CRITICAL: Remove duplicate active amendments (was 98 duplicates)")
        
        charge_completeness_test = next((r for r in test_results if r.test_id == "CHG_002"), None)
        if charge_completeness_test and charge_completeness_test.status == "FAIL":
            recommendations.append("🔧 FUND 2 CRITICAL: Improve charge schedule completeness to 98%+")
        
        return recommendations
    
    def _save_data_quality_results(self, validation_summary: Dict[str, Any]):
        """Save data quality validation results"""
        try:
            output_file = "/Users/michaeltang/Documents/GitHub/BI/PBI v1.7/Test_Automation_Framework/data_quality_results.json"
            
            # Convert DataQualityResult objects to dictionaries
            serializable_results = []
            for result in validation_summary.get('test_results', []):
                result_dict = {
                    'test_id': result.test_id,
                    'test_name': result.test_name,
                    'category': result.category,
                    'data_source': result.data_source,
                    'total_records': result.total_records,
                    'issues_found': result.issues_found,
                    'issue_rate': result.issue_rate,
                    'severity': result.severity,
                    'status': result.status,
                    'quality_score': result.quality_score,
                    'issues_detail': result.issues_detail,
                    'recommendations': result.recommendations,
                    'execution_time': result.execution_time,
                    'timestamp': result.timestamp.isoformat()
                }
                serializable_results.append(result_dict)
            
            validation_summary['test_results'] = serializable_results
            
            with open(output_file, 'w') as f:
                json.dump(validation_summary, f, indent=2, default=str)
            
            logger.info(f"Data quality results saved to: {output_file}")
            
        except Exception as e:
            logger.error(f"Error saving data quality results: {e}")

if __name__ == "__main__":
    # Example usage
    config = {
        'data_path': '/Users/michaeltang/Documents/GitHub/BI/PBI v1.7/Data'
    }
    
    validator = DataQualityValidator(config)
    results = validator.run_comprehensive_data_quality_validation()
    
    print("\n" + "="*80)
    print("DATA QUALITY VALIDATION RESULTS")
    print("="*80)
    print(f"Overall Quality Score: {results['overall_quality_score']:.1f}%")
    print(f"Total Tests: {results['total_tests']}")
    print(f"✅ Passed: {results['passed_tests']}")
    print(f"❌ Failed: {results['failed_tests']}")
    print(f"🚨 Critical Issues: {results['critical_issues']}")
    print(f"⚠️  High Issues: {results['high_issues']}")
    print(f"📋 Medium Issues: {results['medium_issues']}")
    
    print(f"\nTop Recommendations:")
    for i, rec in enumerate(results['recommendations'][:5], 1):
        print(f"  {i}. {rec}")
    
    print("="*80)