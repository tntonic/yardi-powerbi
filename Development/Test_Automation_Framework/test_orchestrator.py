#!/usr/bin/env python3
"""
PowerBI Test Automation Orchestrator
====================================

Master orchestration script that coordinates all PowerBI validation test suites
and generates comprehensive validation reports for production deployment.

ORCHESTRATED TEST SUITES:
1. Data Integrity Validation (powerbi_validation_suite.py)
2. Enhanced Accuracy Validation (accuracy_validation_enhanced.py)
3. Performance Testing (performance_test_suite.py)
4. Data Quality Testing (data_quality_tests.py)
5. Regression Testing (regression_testing_framework.py)

VALIDATION TARGETS:
- 95%+ rent roll accuracy vs Yardi exports
- <5 second query response times  
- Zero duplicate active amendments
- 100% charge schedule integration
- Data quality score >90%

Author: PowerBI Test Automation Orchestrator
Version: 1.0.0
Date: 2025-08-09
"""

import sys
import os
import json
import logging
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import traceback
import warnings
warnings.filterwarnings('ignore')

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import all test frameworks
try:
    from powerbi_validation_suite import DataIntegrityValidator, RentRollAccuracyValidator
    from accuracy_validation_enhanced import EnhancedAccuracyValidator
    from performance_test_suite import PerformanceTestSuite
    from data_quality_tests import DataQualityValidator
    from regression_testing_framework import RegressionTestFramework, ContinuousIntegrationIntegrator
except ImportError as e:
    print(f"Warning: Could not import all test frameworks: {e}")
    print("Some test suites may not be available")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_orchestrator.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class PowerBITestOrchestrator:
    """Master test orchestrator for PowerBI validation"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.test_session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Initialize test frameworks
        self.frameworks = {}
        self._initialize_frameworks()
        
        # Test execution results
        self.orchestration_results = {
            'session_id': self.test_session_id,
            'start_time': datetime.now().isoformat(),
            'config': config,
            'frameworks_initialized': list(self.frameworks.keys()),
            'test_suite_results': {},
            'overall_summary': {},
            'final_recommendations': [],
            'deployment_readiness': 'UNKNOWN'
        }
    
    def _initialize_frameworks(self):
        """Initialize all available test frameworks"""
        logger.info("🔧 Initializing Test Frameworks...")
        
        framework_configs = [
            ('data_integrity', DataIntegrityValidator, "Data Integrity Validation"),
            ('rent_roll_accuracy', RentRollAccuracyValidator, "Rent Roll Accuracy Validation"),
            ('enhanced_accuracy', EnhancedAccuracyValidator, "Enhanced Accuracy Validation"),
            ('performance', PerformanceTestSuite, "Performance Testing Suite"),
            ('data_quality', DataQualityValidator, "Data Quality Validation"),
            ('regression', RegressionTestFramework, "Regression Testing Framework")
        ]
        
        for framework_key, framework_class, framework_name in framework_configs:
            try:
                if framework_class:
                    self.frameworks[framework_key] = {
                        'instance': framework_class(self.config),
                        'name': framework_name,
                        'status': 'READY'
                    }
                    logger.info(f"✅ {framework_name} initialized")
                else:
                    logger.warning(f"⚠️ {framework_name} class not available")
            except Exception as e:
                logger.error(f"❌ Failed to initialize {framework_name}: {e}")
                self.frameworks[framework_key] = {
                    'instance': None,
                    'name': framework_name,
                    'status': 'FAILED',
                    'error': str(e)
                }
        
        logger.info(f"📊 Initialized {len([f for f in self.frameworks.values() if f['status'] == 'READY'])} frameworks")
    
    def run_comprehensive_validation(self, test_suites: Optional[List[str]] = None) -> Dict[str, Any]:
        """Run comprehensive validation across all test suites"""
        logger.info("🚀 Starting Comprehensive PowerBI Validation")
        logger.info(f"📅 Session ID: {self.test_session_id}")
        
        # Default to all available test suites if none specified
        if test_suites is None:
            test_suites = list(self.frameworks.keys())
        
        # Execute test suites in logical order
        execution_order = [
            'data_quality',      # Foundation - ensure data quality first
            'data_integrity',    # Core integrity checks
            'enhanced_accuracy', # Fund 2 critical accuracy validation
            'rent_roll_accuracy',# Rent roll specific validation
            'performance',       # Performance benchmarking
            'regression'         # Regression protection
        ]
        
        # Filter to requested test suites and maintain order
        ordered_test_suites = [suite for suite in execution_order if suite in test_suites]
        ordered_test_suites.extend([suite for suite in test_suites if suite not in execution_order])
        
        # Execute each test suite
        for suite_name in ordered_test_suites:
            if suite_name in self.frameworks and self.frameworks[suite_name]['status'] == 'READY':
                logger.info(f"🔍 Executing {self.frameworks[suite_name]['name']}...")
                suite_results = self._execute_test_suite(suite_name)
                self.orchestration_results['test_suite_results'][suite_name] = suite_results
            else:
                logger.warning(f"⚠️ Skipping {suite_name} - framework not ready")
        
        # Generate overall summary and recommendations
        self.orchestration_results['overall_summary'] = self._generate_overall_summary()
        self.orchestration_results['final_recommendations'] = self._generate_final_recommendations()
        self.orchestration_results['deployment_readiness'] = self._assess_deployment_readiness()
        self.orchestration_results['end_time'] = datetime.now().isoformat()
        
        # Save comprehensive results
        self._save_orchestration_results()
        
        # Generate executive summary report
        self._generate_executive_report()
        
        return self.orchestration_results
    
    def _execute_test_suite(self, suite_name: str) -> Dict[str, Any]:
        """Execute a specific test suite"""
        suite_result = {
            'suite_name': suite_name,
            'framework_name': self.frameworks[suite_name]['name'],
            'start_time': datetime.now().isoformat(),
            'status': 'UNKNOWN',
            'results': None,
            'error': None,
            'execution_time': 0,
            'summary_metrics': {}
        }
        
        start_time = datetime.now()
        
        try:
            framework_instance = self.frameworks[suite_name]['instance']
            
            # Execute appropriate method based on framework type
            if suite_name == 'data_integrity':
                results = framework_instance.run_tests()
                suite_result['summary_metrics'] = self._summarize_data_integrity_results(results)
                
            elif suite_name == 'rent_roll_accuracy':
                results = framework_instance.run_tests()
                suite_result['summary_metrics'] = self._summarize_rent_roll_accuracy_results(results)
                
            elif suite_name == 'enhanced_accuracy':
                results = framework_instance.run_comprehensive_accuracy_validation()
                suite_result['summary_metrics'] = self._summarize_enhanced_accuracy_results(results)
                
            elif suite_name == 'performance':
                results = framework_instance.run_complete_performance_suite()
                suite_result['summary_metrics'] = self._summarize_performance_results(results)
                
            elif suite_name == 'data_quality':
                results = framework_instance.run_comprehensive_data_quality_validation()
                suite_result['summary_metrics'] = self._summarize_data_quality_results(results)
                
            elif suite_name == 'regression':
                results = framework_instance.run_regression_tests()
                suite_result['summary_metrics'] = self._summarize_regression_results(results)
                
            else:
                raise ValueError(f"Unknown test suite: {suite_name}")
            
            suite_result['results'] = results
            suite_result['status'] = 'COMPLETED'
            
        except Exception as e:
            logger.error(f"❌ Error executing {suite_name}: {e}")
            suite_result['status'] = 'FAILED'
            suite_result['error'] = str(e)
            suite_result['traceback'] = traceback.format_exc()
        
        suite_result['execution_time'] = (datetime.now() - start_time).total_seconds()
        suite_result['end_time'] = datetime.now().isoformat()
        
        return suite_result
    
    def _summarize_data_integrity_results(self, results: List[Any]) -> Dict[str, Any]:
        """Summarize data integrity test results"""
        if not results:
            return {'total_tests': 0, 'passed': 0, 'failed': 0, 'overall_score': 0}
        
        passed = len([r for r in results if r.status == 'PASS'])
        failed = len([r for r in results if r.status == 'FAIL'])
        overall_score = (passed / len(results) * 100) if results else 0
        
        return {
            'total_tests': len(results),
            'passed': passed,
            'failed': failed,
            'warnings': len(results) - passed - failed,
            'overall_score': overall_score,
            'critical_issues': [r.test_name for r in results if r.status == 'FAIL']
        }
    
    def _summarize_rent_roll_accuracy_results(self, results: List[Any]) -> Dict[str, Any]:
        """Summarize rent roll accuracy test results"""
        if not results:
            return {'total_tests': 0, 'passed': 0, 'failed': 0, 'overall_accuracy': 0}
        
        passed = len([r for r in results if r.status == 'PASS'])
        failed = len([r for r in results if r.status == 'FAIL'])
        
        # Calculate average accuracy
        accuracy_scores = [r.accuracy_pct for r in results if hasattr(r, 'accuracy_pct')]
        overall_accuracy = sum(accuracy_scores) / len(accuracy_scores) if accuracy_scores else 0
        
        return {
            'total_tests': len(results),
            'passed': passed,
            'failed': failed,
            'overall_accuracy': overall_accuracy,
            'target_accuracy': 95.0,
            'meets_target': overall_accuracy >= 95.0
        }
    
    def _summarize_enhanced_accuracy_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize enhanced accuracy validation results"""
        return {
            'overall_accuracy': results.get('overall_accuracy', 0),
            'target_accuracy': results.get('target_accuracy', 95.0),
            'critical_issues_resolved': results.get('critical_issues_resolved', 0),
            'test_summary': results.get('test_summary', {}),
            'meets_fund2_target': results.get('overall_accuracy', 0) >= 95.0
        }
    
    def _summarize_performance_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize performance test results"""
        overall_summary = results.get('overall_summary', {})
        
        return {
            'overall_grade': overall_summary.get('overall_grade', 'F'),
            'total_tests': overall_summary.get('total_tests', 0),
            'passed_tests': overall_summary.get('passed_tests', 0),
            'failed_tests': overall_summary.get('failed_tests', 0),
            'critical_performance_issues': overall_summary.get('critical_issues', []),
            'meets_performance_targets': overall_summary.get('overall_grade', 'F') in ['A', 'B', 'C']
        }
    
    def _summarize_data_quality_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize data quality validation results"""
        return {
            'overall_quality_score': results.get('overall_quality_score', 0),
            'total_tests': results.get('total_tests', 0),
            'passed_tests': results.get('passed_tests', 0),
            'failed_tests': results.get('failed_tests', 0),
            'critical_issues': results.get('critical_issues', 0),
            'high_issues': results.get('high_issues', 0),
            'meets_quality_target': results.get('overall_quality_score', 0) >= 90.0
        }
    
    def _summarize_regression_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize regression test results"""
        return {
            'overall_status': results.get('overall_status', 'UNKNOWN'),
            'total_tests': results.get('total_tests', 0),
            'passed_tests': results.get('passed_tests', 0),
            'failed_tests': results.get('failed_tests', 0),
            'regressions_detected': results.get('regressions_detected', 0),
            'improvements_detected': results.get('improvements_detected', 0),
            'no_regressions': results.get('overall_status', 'UNKNOWN') == 'PASS'
        }
    
    def _generate_overall_summary(self) -> Dict[str, Any]:
        """Generate overall validation summary"""
        summary = {
            'validation_date': datetime.now().isoformat(),
            'total_frameworks_executed': len(self.orchestration_results['test_suite_results']),
            'frameworks_passed': 0,
            'frameworks_failed': 0,
            'overall_validation_score': 0,
            'key_metrics': {},
            'critical_blockers': [],
            'fund2_status': 'UNKNOWN'
        }
        
        # Analyze each framework result
        framework_scores = []
        
        for suite_name, suite_result in self.orchestration_results['test_suite_results'].items():
            if suite_result['status'] == 'COMPLETED':
                summary['frameworks_passed'] += 1
                
                # Extract key scores
                suite_metrics = suite_result.get('summary_metrics', {})
                
                if 'overall_score' in suite_metrics:
                    framework_scores.append(suite_metrics['overall_score'])
                elif 'overall_accuracy' in suite_metrics:
                    framework_scores.append(suite_metrics['overall_accuracy'])
                elif 'overall_quality_score' in suite_metrics:
                    framework_scores.append(suite_metrics['overall_quality_score'])
                
                # Check for critical blockers
                critical_issues = suite_metrics.get('critical_issues', [])
                if critical_issues:
                    summary['critical_blockers'].extend([
                        f"{suite_name}: {issue}" for issue in critical_issues[:3]  # Limit to top 3
                    ])
                
            else:
                summary['frameworks_failed'] += 1
                summary['critical_blockers'].append(f"{suite_name}: Framework execution failed")
        
        # Calculate overall validation score
        if framework_scores:
            summary['overall_validation_score'] = sum(framework_scores) / len(framework_scores)
        
        # Extract key metrics for executive summary
        summary['key_metrics'] = self._extract_key_metrics()
        
        # Assess Fund 2 specific status
        summary['fund2_status'] = self._assess_fund2_status()
        
        return summary
    
    def _extract_key_metrics(self) -> Dict[str, Any]:
        """Extract key metrics for executive reporting"""
        key_metrics = {
            'rent_roll_accuracy': 0,
            'performance_grade': 'F',
            'data_quality_score': 0,
            'regressions_detected': 0,
            'critical_issues_count': 0
        }
        
        suite_results = self.orchestration_results['test_suite_results']
        
        # Rent roll accuracy
        if 'enhanced_accuracy' in suite_results:
            enhanced_metrics = suite_results['enhanced_accuracy'].get('summary_metrics', {})
            key_metrics['rent_roll_accuracy'] = enhanced_metrics.get('overall_accuracy', 0)
        
        # Performance grade
        if 'performance' in suite_results:
            perf_metrics = suite_results['performance'].get('summary_metrics', {})
            key_metrics['performance_grade'] = perf_metrics.get('overall_grade', 'F')
        
        # Data quality score
        if 'data_quality' in suite_results:
            dq_metrics = suite_results['data_quality'].get('summary_metrics', {})
            key_metrics['data_quality_score'] = dq_metrics.get('overall_quality_score', 0)
        
        # Regressions detected
        if 'regression' in suite_results:
            reg_metrics = suite_results['regression'].get('summary_metrics', {})
            key_metrics['regressions_detected'] = reg_metrics.get('regressions_detected', 0)
        
        # Count critical issues across all frameworks
        for suite_result in suite_results.values():
            suite_metrics = suite_result.get('summary_metrics', {})
            key_metrics['critical_issues_count'] += len(suite_metrics.get('critical_issues', []))
            key_metrics['critical_issues_count'] += suite_metrics.get('critical_issues', 0)  # For numeric counts
        
        return key_metrics
    
    def _assess_fund2_status(self) -> str:
        """Assess specific Fund 2 critical issues status"""
        suite_results = self.orchestration_results['test_suite_results']
        
        # Check enhanced accuracy results for Fund 2 targets
        if 'enhanced_accuracy' in suite_results:
            enhanced_metrics = suite_results['enhanced_accuracy'].get('summary_metrics', {})
            if enhanced_metrics.get('meets_fund2_target', False):
                return 'TARGETS_MET'
        
        # Check for Fund 2 specific issues
        fund2_issues = []
        
        # Data quality issues (duplicate amendments, etc.)
        if 'data_quality' in suite_results:
            dq_metrics = suite_results['data_quality'].get('summary_metrics', {})
            if dq_metrics.get('critical_issues', 0) > 0:
                fund2_issues.append('Data quality issues')
        
        # Accuracy below 95%
        key_metrics = self.orchestration_results['overall_summary'].get('key_metrics', {})
        if key_metrics.get('rent_roll_accuracy', 0) < 95.0:
            fund2_issues.append('Rent roll accuracy below 95%')
        
        if fund2_issues:
            return 'ISSUES_REMAIN'
        else:
            return 'RESOLVED'
    
    def _generate_final_recommendations(self) -> List[str]:
        """Generate final deployment recommendations"""
        recommendations = []
        
        overall_summary = self.orchestration_results['overall_summary']
        key_metrics = overall_summary.get('key_metrics', {})
        fund2_status = overall_summary.get('fund2_status', 'UNKNOWN')
        
        # Overall assessment
        overall_score = overall_summary.get('overall_validation_score', 0)
        if overall_score >= 95.0:
            recommendations.append("🎉 Excellent validation results - APPROVED for production deployment")
        elif overall_score >= 90.0:
            recommendations.append("✅ Good validation results - APPROVED with minor monitoring")  
        elif overall_score >= 80.0:
            recommendations.append("⚠️ Moderate validation results - CONDITIONAL approval with fixes")
        else:
            recommendations.append("❌ Poor validation results - DEPLOYMENT BLOCKED until issues resolved")
        
        # Fund 2 specific recommendations
        if fund2_status == 'TARGETS_MET':
            recommendations.append("🎯 Fund 2 accuracy targets achieved - critical issues resolved")
        elif fund2_status == 'ISSUES_REMAIN':
            recommendations.append("🚨 Fund 2 critical issues remain - immediate attention required")
        
        # Specific metric recommendations
        if key_metrics.get('rent_roll_accuracy', 0) < 95.0:
            recommendations.append(f"📊 Rent roll accuracy {key_metrics['rent_roll_accuracy']:.1f}% below 95% target")
            recommendations.append("🔧 Implement latest amendment WITH charges logic")
        
        if key_metrics.get('regressions_detected', 0) > 0:
            recommendations.append(f"📉 {key_metrics['regressions_detected']} regressions detected")
            recommendations.append("🔄 Address regression issues before deployment")
        
        if key_metrics.get('critical_issues_count', 0) > 0:
            recommendations.append(f"🚨 {key_metrics['critical_issues_count']} critical issues require resolution")
        
        # Performance recommendations
        perf_grade = key_metrics.get('performance_grade', 'F')
        if perf_grade in ['D', 'F']:
            recommendations.append(f"⏱️ Performance grade {perf_grade} - optimization required")
        
        # Data quality recommendations
        dq_score = key_metrics.get('data_quality_score', 0)
        if dq_score < 90.0:
            recommendations.append(f"📊 Data quality score {dq_score:.1f}% below 90% target")
        
        return recommendations
    
    def _assess_deployment_readiness(self) -> str:
        """Assess overall deployment readiness"""
        overall_summary = self.orchestration_results['overall_summary']
        key_metrics = overall_summary.get('key_metrics', {})
        critical_blockers = overall_summary.get('critical_blockers', [])
        fund2_status = overall_summary.get('fund2_status', 'UNKNOWN')
        
        # Critical blockers check
        if critical_blockers:
            return 'BLOCKED'
        
        # Fund 2 critical requirements
        if fund2_status == 'ISSUES_REMAIN':
            return 'BLOCKED'
        
        # Accuracy requirement (critical for Fund 2)
        if key_metrics.get('rent_roll_accuracy', 0) < 95.0:
            return 'BLOCKED'
        
        # Overall validation score
        overall_score = overall_summary.get('overall_validation_score', 0)
        if overall_score >= 95.0:
            return 'APPROVED'
        elif overall_score >= 90.0:
            return 'APPROVED_WITH_CONDITIONS'
        elif overall_score >= 80.0:
            return 'CONDITIONAL'
        else:
            return 'BLOCKED'
    
    def _save_orchestration_results(self):
        """Save comprehensive orchestration results"""
        try:
            # Create timestamped results file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_file = f"/Users/michaeltang/Documents/GitHub/BI/PBI v1.7/Test_Automation_Framework/orchestration_results_{timestamp}.json"
            
            # Convert any non-serializable objects
            serializable_results = self._make_json_serializable(self.orchestration_results)
            
            with open(results_file, 'w') as f:
                json.dump(serializable_results, f, indent=2, default=str)
            
            # Also save latest results
            latest_file = "/Users/michaeltang/Documents/GitHub/BI/PBI v1.7/Test_Automation_Framework/latest_orchestration_results.json"
            with open(latest_file, 'w') as f:
                json.dump(serializable_results, f, indent=2, default=str)
            
            logger.info(f"📄 Orchestration results saved to: {results_file}")
            
        except Exception as e:
            logger.error(f"Error saving orchestration results: {e}")
    
    def _make_json_serializable(self, obj):
        """Convert objects to JSON serializable format"""
        if hasattr(obj, '__dict__'):
            # Convert objects with attributes to dictionaries
            result = {}
            for key, value in obj.__dict__.items():
                result[key] = self._make_json_serializable(value)
            return result
        elif isinstance(obj, dict):
            return {key: self._make_json_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_serializable(item) for item in obj]
        elif isinstance(obj, (datetime,)):
            return obj.isoformat()
        else:
            return obj
    
    def _generate_executive_report(self):
        """Generate executive summary report"""
        try:
            report_file = f"/Users/michaeltang/Documents/GitHub/BI/PBI v1.7/Test_Automation_Framework/Executive_Validation_Report_{self.test_session_id}.md"
            
            overall_summary = self.orchestration_results['overall_summary']
            key_metrics = overall_summary.get('key_metrics', {})
            
            report_content = f"""# PowerBI Validation Executive Report
## Session: {self.test_session_id}
## Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## Executive Summary

**Deployment Readiness: {self.orchestration_results['deployment_readiness']}**

**Overall Validation Score: {overall_summary.get('overall_validation_score', 0):.1f}%**

**Fund 2 Status: {overall_summary.get('fund2_status', 'UNKNOWN')}**

---

## Key Performance Indicators

| Metric | Value | Target | Status |
|--------|-------|---------|---------|
| Rent Roll Accuracy | {key_metrics.get('rent_roll_accuracy', 0):.1f}% | 95%+ | {'✅' if key_metrics.get('rent_roll_accuracy', 0) >= 95 else '❌'} |
| Performance Grade | {key_metrics.get('performance_grade', 'F')} | C or better | {'✅' if key_metrics.get('performance_grade', 'F') in ['A', 'B', 'C'] else '❌'} |
| Data Quality Score | {key_metrics.get('data_quality_score', 0):.1f}% | 90%+ | {'✅' if key_metrics.get('data_quality_score', 0) >= 90 else '❌'} |
| Regressions Detected | {key_metrics.get('regressions_detected', 0)} | 0 | {'✅' if key_metrics.get('regressions_detected', 0) == 0 else '❌'} |
| Critical Issues | {key_metrics.get('critical_issues_count', 0)} | 0 | {'✅' if key_metrics.get('critical_issues_count', 0) == 0 else '❌'} |

---

## Test Suite Results

"""
            
            # Add test suite results
            for suite_name, suite_result in self.orchestration_results['test_suite_results'].items():
                status_icon = "✅" if suite_result['status'] == 'COMPLETED' else "❌"
                report_content += f"### {status_icon} {suite_result['framework_name']}\n"
                report_content += f"**Status:** {suite_result['status']}\n"
                report_content += f"**Execution Time:** {suite_result['execution_time']:.2f} seconds\n"
                
                # Add key metrics
                summary_metrics = suite_result.get('summary_metrics', {})
                if summary_metrics:
                    report_content += "**Key Metrics:**\n"
                    for key, value in summary_metrics.items():
                        if isinstance(value, (int, float)) and key.endswith(('_score', '_accuracy', '_count', '_tests')):
                            report_content += f"- {key.replace('_', ' ').title()}: {value}\n"
                
                report_content += "\n"
            
            # Add recommendations
            report_content += "## Final Recommendations\n\n"
            for i, recommendation in enumerate(self.orchestration_results['final_recommendations'], 1):
                report_content += f"{i}. {recommendation}\n"
            
            # Add critical blockers if any
            critical_blockers = overall_summary.get('critical_blockers', [])
            if critical_blockers:
                report_content += "\n## Critical Blockers\n\n"
                for i, blocker in enumerate(critical_blockers, 1):
                    report_content += f"{i}. 🚨 {blocker}\n"
            
            report_content += f"""
---

## Deployment Decision

Based on the comprehensive validation results:

**Recommendation: {self._get_deployment_recommendation()}**

---

*Report generated by PowerBI Test Automation Orchestrator v1.0.0*
*Session ID: {self.test_session_id}*
"""
            
            with open(report_file, 'w') as f:
                f.write(report_content)
            
            logger.info(f"📊 Executive report saved to: {report_file}")
            
        except Exception as e:
            logger.error(f"Error generating executive report: {e}")
    
    def _get_deployment_recommendation(self) -> str:
        """Get deployment recommendation text"""
        readiness = self.orchestration_results['deployment_readiness']
        
        recommendations = {
            'APPROVED': "✅ **APPROVED FOR PRODUCTION DEPLOYMENT** - All validation criteria met",
            'APPROVED_WITH_CONDITIONS': "✅ **APPROVED WITH CONDITIONS** - Deploy with monitoring",
            'CONDITIONAL': "⚠️ **CONDITIONAL APPROVAL** - Address identified issues before deployment",
            'BLOCKED': "❌ **DEPLOYMENT BLOCKED** - Critical issues must be resolved first"
        }
        
        return recommendations.get(readiness, "❓ **UNKNOWN** - Review validation results")

def main():
    """Main orchestrator execution"""
    parser = argparse.ArgumentParser(description='PowerBI Test Automation Orchestrator')
    parser.add_argument('--config', type=str, default=None, help='Path to configuration file')
    parser.add_argument('--suites', nargs='+', help='Specific test suites to run')
    parser.add_argument('--data-path', type=str, default='/Users/michaeltang/Documents/GitHub/BI/PBI v1.7/Data', help='Path to test data')
    parser.add_argument('--ci-mode', action='store_true', help='Run in CI/CD mode')
    parser.add_argument('--establish-baselines', action='store_true', help='Establish regression baselines')
    
    args = parser.parse_args()
    
    # Load configuration
    config = {
        'data_path': args.data_path,
        'results_path': '/Users/michaeltang/Documents/GitHub/BI/PBI v1.7/Fund2_Validation_Results',
        'yardi_path': '/Users/michaeltang/Documents/GitHub/BI/PBI v1.7/rent rolls'
    }
    
    if args.config and os.path.exists(args.config):
        with open(args.config, 'r') as f:
            file_config = json.load(f)
            config.update(file_config)
    
    # Handle special modes
    if args.establish_baselines:
        logger.info("📊 Establishing Regression Baselines...")
        regression_framework = RegressionTestFramework(config)
        baseline_results = regression_framework.establish_baselines()
        print(f"✅ Created {baseline_results['baselines_created']} baseline metrics")
        return 0
    
    if args.ci_mode:
        logger.info("🔄 Running in CI/CD Mode...")
        ci_integrator = ContinuousIntegrationIntegrator(config)
        ci_results = ci_integrator.run_ci_regression_check()
        
        print(f"CI Status: {ci_results['ci_status']}")
        print(f"Exit Code: {ci_results['exit_code']}")
        
        if ci_results['blocking_issues']:
            print("Blocking Issues:")
            for issue in ci_results['blocking_issues']:
                print(f"  - {issue}")
        
        return ci_results['exit_code']
    
    # Run comprehensive validation
    orchestrator = PowerBITestOrchestrator(config)
    results = orchestrator.run_comprehensive_validation(args.suites)
    
    # Print summary results
    print("\n" + "="*100)
    print("POWERBI COMPREHENSIVE VALIDATION RESULTS")
    print("="*100)
    
    overall_summary = results['overall_summary']
    key_metrics = overall_summary.get('key_metrics', {})
    
    print(f"Session ID: {results['session_id']}")
    print(f"Deployment Readiness: {results['deployment_readiness']}")
    print(f"Overall Validation Score: {overall_summary.get('overall_validation_score', 0):.1f}%")
    print(f"Fund 2 Status: {overall_summary.get('fund2_status', 'UNKNOWN')}")
    
    print(f"\nKey Metrics:")
    print(f"  📊 Rent Roll Accuracy: {key_metrics.get('rent_roll_accuracy', 0):.1f}%")
    print(f"  ⏱️ Performance Grade: {key_metrics.get('performance_grade', 'F')}")
    print(f"  📈 Data Quality Score: {key_metrics.get('data_quality_score', 0):.1f}%")
    print(f"  🔄 Regressions Detected: {key_metrics.get('regressions_detected', 0)}")
    print(f"  🚨 Critical Issues: {key_metrics.get('critical_issues_count', 0)}")
    
    print(f"\nFrameworks Executed: {overall_summary.get('frameworks_passed', 0)}/{overall_summary.get('total_frameworks_executed', 0)}")
    
    # Print critical blockers
    critical_blockers = overall_summary.get('critical_blockers', [])
    if critical_blockers:
        print(f"\n🚨 Critical Blockers:")
        for blocker in critical_blockers[:5]:  # Top 5 blockers
            print(f"  - {blocker}")
    
    # Print top recommendations
    print(f"\n📋 Top Recommendations:")
    for i, rec in enumerate(results['final_recommendations'][:5], 1):
        print(f"  {i}. {rec}")
    
    print("\n" + "="*100)
    
    # Return appropriate exit code
    if results['deployment_readiness'] == 'BLOCKED':
        return 1
    elif results['deployment_readiness'] in ['CONDITIONAL', 'APPROVED_WITH_CONDITIONS']:
        return 2
    else:
        return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)