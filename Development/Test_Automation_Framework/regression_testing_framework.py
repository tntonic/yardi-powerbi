#!/usr/bin/env python3
"""
Regression Testing Framework for PowerBI Solutions
==================================================

Comprehensive regression testing framework designed to prevent accuracy degradation
after implementing Fund 2 fixes and ongoing system changes.

KEY CAPABILITIES:
- Baseline establishment and change detection
- Automated regression test execution 
- Historical trend analysis and alerts
- CI/CD pipeline integration
- Performance regression detection
- Data quality regression monitoring

REGRESSION PROTECTION AREAS:
- Rent roll accuracy maintenance (95%+ target)
- DAX measure calculation consistency
- Data integrity preservation
- Performance benchmark maintenance
- Business rule compliance

Author: PowerBI Regression Test Specialist
Version: 1.0.0
Date: 2025-08-09
"""

import pandas as pd
import numpy as np
import json
import sqlite3
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
import hashlib
import subprocess
import traceback
import warnings
warnings.filterwarnings('ignore')

# Import other test frameworks
try:
    from powerbi_validation_suite import DataIntegrityValidator, ValidationResult
    from accuracy_validation_enhanced import EnhancedAccuracyValidator, AccuracyTestResult  
    from performance_test_suite import PerformanceTestSuite, PerformanceResult
    from data_quality_tests import DataQualityValidator, DataQualityResult
except ImportError as e:
    logging.warning(f"Could not import all test frameworks: {e}")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class BaselineMetric:
    """Baseline metric for regression testing"""
    metric_name: str
    metric_category: str
    baseline_value: float
    tolerance_pct: float
    measurement_date: datetime
    data_hash: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RegressionTestResult:
    """Regression test result with change detection"""
    test_id: str
    test_name: str
    category: str
    baseline_value: float
    current_value: float
    change_pct: float
    tolerance_pct: float
    status: str  # PASS/FAIL/WARNING/NEW_BASELINE
    severity: str  # CRITICAL/HIGH/MEDIUM/LOW
    trend_direction: str  # IMPROVING/DEGRADING/STABLE
    recommendations: List[str]
    execution_time: float
    timestamp: datetime

class BaselineManager:
    """Manages baseline metrics for regression testing"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.baseline_db_path = config.get(
            'baseline_db_path', 
            '/Users/michaeltang/Documents/GitHub/BI/PBI v1.7/Test_Automation_Framework/baselines.db'
        )
        self._initialize_baseline_database()
    
    def _initialize_baseline_database(self):
        """Initialize SQLite database for storing baselines"""
        try:
            conn = sqlite3.connect(self.baseline_db_path)
            cursor = conn.cursor()
            
            # Create baselines table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS baselines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT NOT NULL,
                    metric_category TEXT NOT NULL,
                    baseline_value REAL NOT NULL,
                    tolerance_pct REAL NOT NULL,
                    measurement_date TEXT NOT NULL,
                    data_hash TEXT NOT NULL,
                    metadata TEXT,
                    created_date TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1
                )
            ''')
            
            # Create regression results table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS regression_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_id TEXT NOT NULL,
                    test_name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    baseline_value REAL NOT NULL,
                    current_value REAL NOT NULL,
                    change_pct REAL NOT NULL,
                    tolerance_pct REAL NOT NULL,
                    status TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    trend_direction TEXT NOT NULL,
                    recommendations TEXT,
                    execution_time REAL NOT NULL,
                    timestamp TEXT NOT NULL
                )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error initializing baseline database: {e}")
    
    def save_baseline(self, metric: BaselineMetric):
        """Save a baseline metric"""
        try:
            conn = sqlite3.connect(self.baseline_db_path)
            cursor = conn.cursor()
            
            # Deactivate existing baselines for this metric
            cursor.execute('''
                UPDATE baselines 
                SET is_active = 0 
                WHERE metric_name = ? AND metric_category = ?
            ''', (metric.metric_name, metric.metric_category))
            
            # Insert new baseline
            cursor.execute('''
                INSERT INTO baselines 
                (metric_name, metric_category, baseline_value, tolerance_pct, 
                 measurement_date, data_hash, metadata, created_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                metric.metric_name, metric.metric_category, metric.baseline_value,
                metric.tolerance_pct, metric.measurement_date.isoformat(),
                metric.data_hash, json.dumps(metric.metadata), datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Saved baseline for {metric.metric_name}: {metric.baseline_value}")
            
        except Exception as e:
            logger.error(f"Error saving baseline: {e}")
    
    def get_baseline(self, metric_name: str, metric_category: str) -> Optional[BaselineMetric]:
        """Get active baseline for a metric"""
        try:
            conn = sqlite3.connect(self.baseline_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT metric_name, metric_category, baseline_value, tolerance_pct,
                       measurement_date, data_hash, metadata
                FROM baselines
                WHERE metric_name = ? AND metric_category = ? AND is_active = 1
                ORDER BY created_date DESC
                LIMIT 1
            ''', (metric_name, metric_category))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return BaselineMetric(
                    metric_name=row[0],
                    metric_category=row[1], 
                    baseline_value=row[2],
                    tolerance_pct=row[3],
                    measurement_date=datetime.fromisoformat(row[4]),
                    data_hash=row[5],
                    metadata=json.loads(row[6]) if row[6] else {}
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting baseline: {e}")
            return None
    
    def save_regression_result(self, result: RegressionTestResult):
        """Save regression test result"""
        try:
            conn = sqlite3.connect(self.baseline_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO regression_results
                (test_id, test_name, category, baseline_value, current_value,
                 change_pct, tolerance_pct, status, severity, trend_direction,
                 recommendations, execution_time, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                result.test_id, result.test_name, result.category,
                result.baseline_value, result.current_value, result.change_pct,
                result.tolerance_pct, result.status, result.severity,
                result.trend_direction, json.dumps(result.recommendations),
                result.execution_time, result.timestamp.isoformat()
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error saving regression result: {e}")
    
    def get_metric_history(self, metric_name: str, metric_category: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get metric history for trend analysis"""
        try:
            conn = sqlite3.connect(self.baseline_db_path)
            
            # Get recent regression results
            query = '''
                SELECT current_value, change_pct, status, timestamp
                FROM regression_results
                WHERE test_name = ? AND category = ?
                AND datetime(timestamp) >= datetime('now', '-{} days')
                ORDER BY timestamp DESC
            '''.format(days)
            
            df = pd.read_sql_query(query, conn, params=(metric_name, metric_category))
            conn.close()
            
            return df.to_dict('records')
            
        except Exception as e:
            logger.error(f"Error getting metric history: {e}")
            return []

class RegressionTestFramework:
    """Main regression testing framework"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.baseline_manager = BaselineManager(config)
        self.results: List[RegressionTestResult] = []
        
        # Initialize test frameworks
        self.accuracy_validator = None
        self.performance_suite = None
        self.data_quality_validator = None
        
        try:
            self.accuracy_validator = EnhancedAccuracyValidator(config)
            self.performance_suite = PerformanceTestSuite(config)
            self.data_quality_validator = DataQualityValidator(config)
        except Exception as e:
            logger.warning(f"Could not initialize all test frameworks: {e}")
    
    def establish_baselines(self) -> Dict[str, Any]:
        """Establish baseline metrics from current system state"""
        logger.info("📊 Establishing Baseline Metrics for Regression Testing")
        
        baseline_results = {
            'baselines_created': 0,
            'accuracy_baselines': [],
            'performance_baselines': [],
            'data_quality_baselines': [],
            'creation_timestamp': datetime.now().isoformat()
        }
        
        # Establish accuracy baselines
        if self.accuracy_validator:
            accuracy_baselines = self._establish_accuracy_baselines()
            baseline_results['accuracy_baselines'] = accuracy_baselines
            baseline_results['baselines_created'] += len(accuracy_baselines)
        
        # Establish performance baselines
        if self.performance_suite:
            performance_baselines = self._establish_performance_baselines()
            baseline_results['performance_baselines'] = performance_baselines
            baseline_results['baselines_created'] += len(performance_baselines)
        
        # Establish data quality baselines
        if self.data_quality_validator:
            data_quality_baselines = self._establish_data_quality_baselines()
            baseline_results['data_quality_baselines'] = data_quality_baselines
            baseline_results['baselines_created'] += len(data_quality_baselines)
        
        logger.info(f"✅ Established {baseline_results['baselines_created']} baseline metrics")
        
        return baseline_results
    
    def _establish_accuracy_baselines(self) -> List[Dict[str, Any]]:
        """Establish accuracy baselines"""
        baselines = []
        
        try:
            # Run accuracy validation to get current state
            accuracy_results = self.accuracy_validator.run_comprehensive_accuracy_validation()
            
            # Create baselines for key accuracy metrics
            key_metrics = [
                ('overall_accuracy', 'Accuracy', 95.0, 2.0),  # 95% target, 2% tolerance
                ('amendment_selection_accuracy', 'Accuracy', 90.0, 3.0),
                ('charge_integration_rate', 'Accuracy', 98.0, 1.0),
                ('rent_roll_accuracy', 'Accuracy', 95.0, 2.0)
            ]
            
            for metric_name, category, target_value, tolerance in key_metrics:
                # Extract current value from results
                current_value = accuracy_results.get('overall_accuracy', target_value)
                
                if metric_name == 'amendment_selection_accuracy':
                    # Find amendment selection test result
                    for test in accuracy_results.get('tests', []):
                        if hasattr(test, 'test_name') and 'Amendment Selection' in test.test_name:
                            current_value = test.actual_accuracy
                            break
                elif metric_name == 'charge_integration_rate':
                    # Find charge integration test result  
                    for test in accuracy_results.get('tests', []):
                        if hasattr(test, 'test_name') and 'Charge Integration' in test.test_name:
                            current_value = test.actual_accuracy
                            break
                
                # Create baseline metric
                baseline = BaselineMetric(
                    metric_name=metric_name,
                    metric_category=category,
                    baseline_value=current_value,
                    tolerance_pct=tolerance,
                    measurement_date=datetime.now(),
                    data_hash=self._calculate_data_hash(),
                    metadata={'target_value': target_value, 'framework': 'accuracy'}
                )
                
                self.baseline_manager.save_baseline(baseline)
                baselines.append({
                    'metric_name': metric_name,
                    'baseline_value': current_value,
                    'tolerance_pct': tolerance
                })
                
        except Exception as e:
            logger.error(f"Error establishing accuracy baselines: {e}")
        
        return baselines
    
    def _establish_performance_baselines(self) -> List[Dict[str, Any]]:
        """Establish performance baselines"""
        baselines = []
        
        try:
            # Run performance tests to get current state
            performance_results = self.performance_suite.run_complete_performance_suite()
            
            # Create baselines for key performance metrics
            dax_results = performance_results.get('dax_measure_results', [])
            
            for result in dax_results:
                if hasattr(result, 'test_name') and hasattr(result, 'execution_time'):
                    baseline = BaselineMetric(
                        metric_name=f"{result.test_name}_execution_time",
                        metric_category="Performance",
                        baseline_value=result.execution_time,
                        tolerance_pct=20.0,  # 20% performance tolerance
                        measurement_date=datetime.now(),
                        data_hash=self._calculate_data_hash(),
                        metadata={
                            'target_time': result.target_time,
                            'framework': 'performance',
                            'test_category': result.category
                        }
                    )
                    
                    self.baseline_manager.save_baseline(baseline)
                    baselines.append({
                        'metric_name': baseline.metric_name,
                        'baseline_value': result.execution_time,
                        'tolerance_pct': 20.0
                    })
            
        except Exception as e:
            logger.error(f"Error establishing performance baselines: {e}")
        
        return baselines
    
    def _establish_data_quality_baselines(self) -> List[Dict[str, Any]]:
        """Establish data quality baselines"""
        baselines = []
        
        try:
            # Run data quality validation to get current state
            dq_results = self.data_quality_validator.run_comprehensive_data_quality_validation()
            
            # Create baseline for overall quality score
            overall_score = dq_results.get('overall_quality_score', 0)
            
            baseline = BaselineMetric(
                metric_name="overall_data_quality_score",
                metric_category="Data Quality",
                baseline_value=overall_score,
                tolerance_pct=5.0,  # 5% data quality tolerance
                measurement_date=datetime.now(),
                data_hash=self._calculate_data_hash(),
                metadata={'framework': 'data_quality'}
            )
            
            self.baseline_manager.save_baseline(baseline)
            baselines.append({
                'metric_name': "overall_data_quality_score",
                'baseline_value': overall_score,
                'tolerance_pct': 5.0
            })
            
            # Create baselines for individual data quality tests
            for test_result in dq_results.get('test_results', []):
                if hasattr(test_result, 'quality_score'):
                    baseline = BaselineMetric(
                        metric_name=f"dq_{test_result.test_id.lower()}_score",
                        metric_category="Data Quality",
                        baseline_value=test_result.quality_score,
                        tolerance_pct=10.0,  # 10% tolerance for individual tests
                        measurement_date=datetime.now(),
                        data_hash=self._calculate_data_hash(),
                        metadata={
                            'test_id': test_result.test_id,
                            'framework': 'data_quality',
                            'severity': test_result.severity
                        }
                    )
                    
                    self.baseline_manager.save_baseline(baseline)
                    baselines.append({
                        'metric_name': baseline.metric_name,
                        'baseline_value': test_result.quality_score,
                        'tolerance_pct': 10.0
                    })
            
        except Exception as e:
            logger.error(f"Error establishing data quality baselines: {e}")
        
        return baselines
    
    def run_regression_tests(self) -> Dict[str, Any]:
        """Run regression tests against established baselines"""
        logger.info("🔄 Running Regression Tests Against Baselines")
        
        regression_results = {
            'overall_status': 'UNKNOWN',
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'warning_tests': 0,
            'regressions_detected': 0,
            'improvements_detected': 0,
            'test_results': [],
            'recommendations': [],
            'execution_timestamp': datetime.now().isoformat()
        }
        
        # Run accuracy regression tests
        accuracy_regression_results = self._run_accuracy_regression_tests()
        regression_results['test_results'].extend(accuracy_regression_results)
        
        # Run performance regression tests
        performance_regression_results = self._run_performance_regression_tests()
        regression_results['test_results'].extend(performance_regression_results)
        
        # Run data quality regression tests
        dq_regression_results = self._run_data_quality_regression_tests()
        regression_results['test_results'].extend(dq_regression_results)
        
        # Calculate summary statistics
        all_results = regression_results['test_results']
        regression_results['total_tests'] = len(all_results)
        
        for result in all_results:
            if result.status == 'PASS':
                regression_results['passed_tests'] += 1
            elif result.status == 'FAIL':
                regression_results['failed_tests'] += 1
            elif result.status == 'WARNING':
                regression_results['warning_tests'] += 1
            
            if result.trend_direction == 'DEGRADING':
                regression_results['regressions_detected'] += 1
            elif result.trend_direction == 'IMPROVING':
                regression_results['improvements_detected'] += 1
        
        # Determine overall status
        if regression_results['failed_tests'] == 0:
            regression_results['overall_status'] = 'PASS'
        elif regression_results['failed_tests'] <= regression_results['total_tests'] * 0.1:  # <10% failures
            regression_results['overall_status'] = 'WARNING'
        else:
            regression_results['overall_status'] = 'FAIL'
        
        # Generate recommendations
        regression_results['recommendations'] = self._generate_regression_recommendations(regression_results)
        
        # Save results
        self._save_regression_results(regression_results)
        
        return regression_results
    
    def _run_accuracy_regression_tests(self) -> List[RegressionTestResult]:
        """Run accuracy regression tests"""
        results = []
        
        try:
            if not self.accuracy_validator:
                return results
            
            # Get current accuracy results
            current_results = self.accuracy_validator.run_comprehensive_accuracy_validation()
            
            # Test key accuracy metrics against baselines
            accuracy_metrics = [
                ('overall_accuracy', current_results.get('overall_accuracy', 0)),
            ]
            
            # Extract accuracy from individual tests
            for test in current_results.get('tests', []):
                if hasattr(test, 'test_name') and hasattr(test, 'actual_accuracy'):
                    test_metric_name = f"{test.test_name.lower().replace(' ', '_')}_accuracy"
                    accuracy_metrics.append((test_metric_name, test.actual_accuracy))
            
            for metric_name, current_value in accuracy_metrics:
                baseline = self.baseline_manager.get_baseline(metric_name, 'Accuracy')
                
                if baseline:
                    result = self._compare_against_baseline(
                        test_id=f"ACC_REG_{metric_name.upper()}",
                        test_name=f"Accuracy Regression - {metric_name.replace('_', ' ').title()}",
                        category="Accuracy",
                        baseline=baseline,
                        current_value=current_value
                    )
                    results.append(result)
                    self.baseline_manager.save_regression_result(result)
                
        except Exception as e:
            logger.error(f"Error in accuracy regression tests: {e}")
        
        return results
    
    def _run_performance_regression_tests(self) -> List[RegressionTestResult]:
        """Run performance regression tests"""
        results = []
        
        try:
            if not self.performance_suite:
                return results
            
            # Get current performance results
            current_results = self.performance_suite.run_complete_performance_suite()
            
            # Test performance metrics against baselines
            for dax_result in current_results.get('dax_measure_results', []):
                if hasattr(dax_result, 'test_name') and hasattr(dax_result, 'execution_time'):
                    metric_name = f"{dax_result.test_name}_execution_time"
                    baseline = self.baseline_manager.get_baseline(metric_name, 'Performance')
                    
                    if baseline:
                        result = self._compare_against_baseline(
                            test_id=f"PERF_REG_{dax_result.test_name.replace(' ', '_').upper()}",
                            test_name=f"Performance Regression - {dax_result.test_name}",
                            category="Performance",
                            baseline=baseline,
                            current_value=dax_result.execution_time
                        )
                        results.append(result)
                        self.baseline_manager.save_regression_result(result)
            
        except Exception as e:
            logger.error(f"Error in performance regression tests: {e}")
        
        return results
    
    def _run_data_quality_regression_tests(self) -> List[RegressionTestResult]:
        """Run data quality regression tests"""
        results = []
        
        try:
            if not self.data_quality_validator:
                return results
            
            # Get current data quality results
            current_results = self.data_quality_validator.run_comprehensive_data_quality_validation()
            
            # Test overall quality score against baseline
            overall_score = current_results.get('overall_quality_score', 0)
            baseline = self.baseline_manager.get_baseline('overall_data_quality_score', 'Data Quality')
            
            if baseline:
                result = self._compare_against_baseline(
                    test_id="DQ_REG_OVERALL",
                    test_name="Data Quality Regression - Overall Score",
                    category="Data Quality", 
                    baseline=baseline,
                    current_value=overall_score
                )
                results.append(result)
                self.baseline_manager.save_regression_result(result)
            
            # Test individual data quality metrics
            for test_result in current_results.get('test_results', []):
                if hasattr(test_result, 'quality_score'):
                    metric_name = f"dq_{test_result.test_id.lower()}_score"
                    baseline = self.baseline_manager.get_baseline(metric_name, 'Data Quality')
                    
                    if baseline:
                        result = self._compare_against_baseline(
                            test_id=f"DQ_REG_{test_result.test_id}",
                            test_name=f"Data Quality Regression - {test_result.test_name}",
                            category="Data Quality",
                            baseline=baseline,
                            current_value=test_result.quality_score
                        )
                        results.append(result)
                        self.baseline_manager.save_regression_result(result)
            
        except Exception as e:
            logger.error(f"Error in data quality regression tests: {e}")
        
        return results
    
    def _compare_against_baseline(self, test_id: str, test_name: str, category: str, 
                                 baseline: BaselineMetric, current_value: float) -> RegressionTestResult:
        """Compare current value against baseline"""
        start_time = datetime.now()
        
        # Calculate change
        if baseline.baseline_value != 0:
            change_pct = ((current_value - baseline.baseline_value) / baseline.baseline_value) * 100
        else:
            change_pct = 100.0 if current_value > 0 else 0.0
        
        # Determine status based on tolerance
        abs_change_pct = abs(change_pct)
        
        if abs_change_pct <= baseline.tolerance_pct:
            status = "PASS"
            severity = "LOW"
        elif abs_change_pct <= baseline.tolerance_pct * 2:
            status = "WARNING"
            severity = "MEDIUM"
        else:
            status = "FAIL"
            severity = "HIGH" if abs_change_pct <= baseline.tolerance_pct * 3 else "CRITICAL"
        
        # Determine trend direction
        if change_pct > baseline.tolerance_pct:
            if category in ['Accuracy', 'Data Quality']:  # Higher is better
                trend_direction = "IMPROVING"
            else:  # Performance - lower is better
                trend_direction = "DEGRADING"
        elif change_pct < -baseline.tolerance_pct:
            if category in ['Accuracy', 'Data Quality']:  # Higher is better
                trend_direction = "DEGRADING"
            else:  # Performance - lower is better  
                trend_direction = "IMPROVING"
        else:
            trend_direction = "STABLE"
        
        # Generate recommendations
        recommendations = self._generate_metric_recommendations(
            category, change_pct, baseline.tolerance_pct, trend_direction
        )
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return RegressionTestResult(
            test_id=test_id,
            test_name=test_name,
            category=category,
            baseline_value=baseline.baseline_value,
            current_value=current_value,
            change_pct=change_pct,
            tolerance_pct=baseline.tolerance_pct,
            status=status,
            severity=severity,
            trend_direction=trend_direction,
            recommendations=recommendations,
            execution_time=execution_time,
            timestamp=start_time
        )
    
    def _generate_metric_recommendations(self, category: str, change_pct: float, 
                                       tolerance_pct: float, trend_direction: str) -> List[str]:
        """Generate recommendations based on metric changes"""
        recommendations = []
        
        if trend_direction == "DEGRADING":
            if category == "Accuracy":
                recommendations.append("🚨 Accuracy degradation detected - investigate DAX measure changes")
                recommendations.append("Review recent amendment selection logic modifications")
                recommendations.append("Validate charge integration completeness")
            elif category == "Performance":
                recommendations.append("⏱️ Performance regression detected - optimize slow measures")  
                recommendations.append("Check for increased data volume or complexity")
                recommendations.append("Review recent DAX measure optimizations")
            elif category == "Data Quality":
                recommendations.append("📊 Data quality degradation detected - check data sources")
                recommendations.append("Review recent data extraction changes")
                recommendations.append("Validate data integrity rules")
        
        elif trend_direction == "IMPROVING":
            recommendations.append(f"✅ {category} improvement detected - maintain current practices")
        
        else:  # STABLE
            recommendations.append(f"📈 {category} stable within tolerance - continue monitoring")
        
        # Add severity-based recommendations
        abs_change = abs(change_pct)
        if abs_change > tolerance_pct * 3:
            recommendations.append("🚨 CRITICAL: Immediate investigation required")
        elif abs_change > tolerance_pct * 2:
            recommendations.append("⚠️ HIGH: Address within 24 hours")
        
        return recommendations
    
    def _generate_regression_recommendations(self, regression_results: Dict[str, Any]) -> List[str]:
        """Generate overall regression test recommendations"""
        recommendations = []
        
        overall_status = regression_results.get('overall_status', 'UNKNOWN')
        regressions_detected = regression_results.get('regressions_detected', 0)
        improvements_detected = regression_results.get('improvements_detected', 0)
        failed_tests = regression_results.get('failed_tests', 0)
        
        # Overall assessment
        if overall_status == 'PASS':
            recommendations.append("✅ No significant regressions detected - system is stable")
        elif overall_status == 'WARNING':
            recommendations.append("⚠️ Minor regressions detected - monitor closely")
        else:
            recommendations.append("🚨 Significant regressions detected - immediate action required")
        
        # Specific recommendations
        if regressions_detected > 0:
            recommendations.append(f"📉 {regressions_detected} metrics showing degradation")
            recommendations.append("Review recent changes to DAX measures, data sources, or system configuration")
        
        if improvements_detected > 0:
            recommendations.append(f"📈 {improvements_detected} metrics showing improvement")
        
        if failed_tests > 0:
            recommendations.append(f"❌ {failed_tests} tests failed regression criteria")
            recommendations.append("Prioritize failed tests by severity for investigation")
        
        # Fund 2 specific recommendations
        accuracy_failures = [r for r in regression_results.get('test_results', []) 
                           if r.category == 'Accuracy' and r.status == 'FAIL']
        if accuracy_failures:
            recommendations.append("🔧 FUND 2 ALERT: Accuracy regressions detected - protect 95%+ target")
        
        return recommendations
    
    def _calculate_data_hash(self) -> str:
        """Calculate hash of current data state for change detection"""
        try:
            # Get file modification times and sizes for key data files
            data_files = [
                f"{self.config.get('data_path', '')}/Fund2_Filtered/dim_fp_amendmentsunitspropertytenant_fund2.csv",
                f"{self.config.get('data_path', '')}/Fund2_Filtered/dim_fp_amendmentchargeschedule_fund2_active.csv"
            ]
            
            hash_input = ""
            for file_path in data_files:
                if os.path.exists(file_path):
                    stat = os.stat(file_path)
                    hash_input += f"{file_path}:{stat.st_mtime}:{stat.st_size};"
            
            return hashlib.md5(hash_input.encode()).hexdigest()
            
        except Exception as e:
            logger.warning(f"Could not calculate data hash: {e}")
            return datetime.now().isoformat()
    
    def _save_regression_results(self, regression_results: Dict[str, Any]):
        """Save regression test results"""
        try:
            output_file = "/Users/michaeltang/Documents/GitHub/BI/PBI v1.7/Test_Automation_Framework/regression_test_results.json"
            
            # Convert RegressionTestResult objects to dictionaries
            serializable_results = []
            for result in regression_results.get('test_results', []):
                result_dict = {
                    'test_id': result.test_id,
                    'test_name': result.test_name,
                    'category': result.category,
                    'baseline_value': result.baseline_value,
                    'current_value': result.current_value,
                    'change_pct': result.change_pct,
                    'tolerance_pct': result.tolerance_pct,
                    'status': result.status,
                    'severity': result.severity,
                    'trend_direction': result.trend_direction,
                    'recommendations': result.recommendations,
                    'execution_time': result.execution_time,
                    'timestamp': result.timestamp.isoformat()
                }
                serializable_results.append(result_dict)
            
            regression_results['test_results'] = serializable_results
            
            with open(output_file, 'w') as f:
                json.dump(regression_results, f, indent=2, default=str)
            
            logger.info(f"Regression test results saved to: {output_file}")
            
        except Exception as e:
            logger.error(f"Error saving regression results: {e}")
    
    def generate_trend_report(self, days: int = 30) -> Dict[str, Any]:
        """Generate trend analysis report"""
        logger.info(f"📈 Generating Trend Analysis Report ({days} days)")
        
        trend_report = {
            'analysis_period_days': days,
            'report_generation_date': datetime.now().isoformat(),
            'metrics_analyzed': 0,
            'trending_metrics': [],
            'alerts': [],
            'recommendations': []
        }
        
        # Get all active baselines
        try:
            conn = sqlite3.connect(self.baseline_manager.baseline_db_path)
            baselines_df = pd.read_sql_query('''
                SELECT DISTINCT metric_name, metric_category 
                FROM baselines 
                WHERE is_active = 1
            ''', conn)
            
            for _, row in baselines_df.iterrows():
                metric_name = row['metric_name']
                metric_category = row['metric_category']
                
                history = self.baseline_manager.get_metric_history(metric_name, metric_category, days)
                
                if len(history) >= 3:  # Need at least 3 data points for trend
                    trend_analysis = self._analyze_metric_trend(metric_name, metric_category, history)
                    trend_report['trending_metrics'].append(trend_analysis)
                    
                    # Generate alerts for concerning trends
                    if trend_analysis.get('trend_direction') == 'DEGRADING' and trend_analysis.get('significance') == 'HIGH':
                        trend_report['alerts'].append({
                            'metric': metric_name,
                            'alert_level': 'HIGH',
                            'message': f"{metric_name} showing significant degradation over {days} days"
                        })
            
            trend_report['metrics_analyzed'] = len(trend_report['trending_metrics'])
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error generating trend report: {e}")
        
        return trend_report
    
    def _analyze_metric_trend(self, metric_name: str, metric_category: str, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze trend for a specific metric"""
        try:
            # Convert to DataFrame for analysis
            df = pd.DataFrame(history)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            
            # Calculate trend statistics
            values = df['current_value'].values
            trend_slope = np.polyfit(range(len(values)), values, 1)[0]
            
            # Determine trend direction and significance
            recent_change = abs(values[-1] - values[0]) / values[0] * 100 if values[0] != 0 else 0
            
            if abs(trend_slope) < 0.01:
                trend_direction = 'STABLE'
                significance = 'LOW'
            elif trend_slope > 0:
                trend_direction = 'IMPROVING' if metric_category in ['Accuracy', 'Data Quality'] else 'DEGRADING'
            else:
                trend_direction = 'DEGRADING' if metric_category in ['Accuracy', 'Data Quality'] else 'IMPROVING'
            
            # Determine significance
            if recent_change > 10:
                significance = 'HIGH'
            elif recent_change > 5:
                significance = 'MEDIUM'
            else:
                significance = 'LOW'
            
            return {
                'metric_name': metric_name,
                'metric_category': metric_category,
                'data_points': len(values),
                'trend_slope': trend_slope,
                'trend_direction': trend_direction,
                'significance': significance,
                'recent_change_pct': recent_change,
                'current_value': values[-1],
                'historical_avg': values.mean(),
                'volatility': values.std()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing trend for {metric_name}: {e}")
            return {'metric_name': metric_name, 'error': str(e)}

class ContinuousIntegrationIntegrator:
    """CI/CD pipeline integration for automated regression testing"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.regression_framework = RegressionTestFramework(config)
    
    def run_ci_regression_check(self) -> Dict[str, Any]:
        """Run regression check suitable for CI/CD pipeline"""
        logger.info("🔄 Running CI/CD Regression Check")
        
        ci_results = {
            'ci_status': 'UNKNOWN',
            'exit_code': 1,
            'summary': {},
            'blocking_issues': [],
            'warnings': [],
            'execution_time': 0
        }
        
        start_time = datetime.now()
        
        try:
            # Run regression tests
            regression_results = self.regression_framework.run_regression_tests()
            
            # Determine CI status
            failed_tests = regression_results.get('failed_tests', 0)
            critical_regressions = len([r for r in regression_results.get('test_results', []) 
                                      if r.severity == 'CRITICAL' and r.status == 'FAIL'])
            
            if critical_regressions > 0:
                ci_results['ci_status'] = 'BLOCKED'
                ci_results['exit_code'] = 2
                ci_results['blocking_issues'] = [
                    f"{critical_regressions} critical regressions detected",
                    "Deployment blocked until issues are resolved"
                ]
            elif failed_tests > 0:
                ci_results['ci_status'] = 'WARNING'
                ci_results['exit_code'] = 1
                ci_results['warnings'] = [
                    f"{failed_tests} regression tests failed",
                    "Review failures before deployment"
                ]
            else:
                ci_results['ci_status'] = 'PASS'
                ci_results['exit_code'] = 0
            
            ci_results['summary'] = {
                'total_tests': regression_results.get('total_tests', 0),
                'passed_tests': regression_results.get('passed_tests', 0),
                'failed_tests': failed_tests,
                'regressions_detected': regression_results.get('regressions_detected', 0)
            }
            
        except Exception as e:
            logger.error(f"Error in CI regression check: {e}")
            ci_results['ci_status'] = 'ERROR'
            ci_results['exit_code'] = 3
            ci_results['blocking_issues'] = [f"Regression test execution error: {e}"]
        
        ci_results['execution_time'] = (datetime.now() - start_time).total_seconds()
        
        return ci_results

if __name__ == "__main__":
    # Example usage
    config = {
        'data_path': '/Users/michaeltang/Documents/GitHub/BI/PBI v1.7/Data'
    }
    
    regression_framework = RegressionTestFramework(config)
    
    # Establish baselines (run once after Fund 2 fixes)
    if len(sys.argv) > 1 and sys.argv[1] == '--establish-baselines':
        print("📊 Establishing Baseline Metrics...")
        baseline_results = regression_framework.establish_baselines()
        print(f"✅ Created {baseline_results['baselines_created']} baselines")
    
    # Run regression tests
    else:
        print("🔄 Running Regression Tests...")
        regression_results = regression_framework.run_regression_tests()
        
        print("\n" + "="*80)
        print("REGRESSION TEST RESULTS")
        print("="*80)
        print(f"Overall Status: {regression_results['overall_status']}")
        print(f"Total Tests: {regression_results['total_tests']}")
        print(f"✅ Passed: {regression_results['passed_tests']}")
        print(f"❌ Failed: {regression_results['failed_tests']}")
        print(f"⚠️  Warnings: {regression_results['warning_tests']}")
        print(f"📉 Regressions: {regression_results['regressions_detected']}")
        print(f"📈 Improvements: {regression_results['improvements_detected']}")
        
        print(f"\nTop Recommendations:")
        for i, rec in enumerate(regression_results['recommendations'][:5], 1):
            print(f"  {i}. {rec}")
        
        # Generate trend report
        print("\n📈 Generating Trend Report...")
        trend_report = regression_framework.generate_trend_report(30)
        print(f"Analyzed {trend_report['metrics_analyzed']} metrics over 30 days")
        
        if trend_report['alerts']:
            print("\n🚨 Trend Alerts:")
            for alert in trend_report['alerts']:
                print(f"  - {alert['message']}")
        
        print("="*80)