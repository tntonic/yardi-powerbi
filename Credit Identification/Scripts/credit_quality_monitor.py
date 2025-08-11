#!/usr/bin/env python3
"""
Ongoing monitoring script for credit report data quality.
Run regularly to track improvements and identify new issues.
"""

import pandas as pd
import os
from datetime import datetime
import json
import numpy as np

class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle numpy types."""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)

# Paths
CSV_PATH = "/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Credit Identification/Data/final_tenant_credit_with_ids.csv"
FOLDERS_DIR = "/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Credit Identification/Folders"
METRICS_FILE = "/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Credit Identification/Reports/quality_metrics_history.json"
OUTPUT_DIR = "/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Credit Identification/Reports"

class CreditQualityMonitor:
    def __init__(self):
        self.df = pd.read_csv(CSV_PATH)
        self.timestamp = datetime.now()
        self.metrics = {}
        
    def calculate_metrics(self):
        """Calculate all quality metrics."""
        
        total_records = len(self.df)
        
        # Customer ID metrics
        records_with_ids = self.df['customer_id'].notna().sum()
        records_without_ids = self.df['customer_id'].isna().sum()
        customer_id_coverage = (records_with_ids / total_records * 100) if total_records > 0 else 0
        
        # Credit match metrics
        records_with_credit = len(self.df[self.df['match_score'] > 0])
        records_no_match = len(self.df[self.df['match_score'] == 0])
        credit_coverage = (records_with_credit / total_records * 100) if total_records > 0 else 0
        
        # Match quality metrics
        high_confidence = len(self.df[self.df['match_score'] >= 90])
        medium_confidence = len(self.df[(self.df['match_score'] >= 70) & (self.df['match_score'] < 90)])
        low_confidence = len(self.df[(self.df['match_score'] > 0) & (self.df['match_score'] < 70)])
        
        # Manual corrections
        manual_corrections = len(self.df[self.df['match_method'] == 'Manual correction'])
        
        # Match method breakdown
        match_methods = {str(k): int(v) for k, v in self.df['match_method'].value_counts().to_dict().items()}
        
        # Folder metrics
        folder_metrics = self.analyze_folders()
        
        # Calculate quality score (0-100)
        quality_score = self.calculate_quality_score(
            customer_id_coverage, 
            credit_coverage, 
            high_confidence / records_with_credit * 100 if records_with_credit > 0 else 0
        )
        
        self.metrics = {
            'timestamp': self.timestamp.isoformat(),
            'total_records': int(total_records),
            'customer_id_metrics': {
                'with_ids': int(records_with_ids),
                'without_ids': int(records_without_ids),
                'coverage_pct': round(customer_id_coverage, 2)
            },
            'credit_match_metrics': {
                'with_credit': int(records_with_credit),
                'no_match': int(records_no_match),
                'coverage_pct': round(credit_coverage, 2)
            },
            'match_quality': {
                'high_confidence': int(high_confidence),
                'medium_confidence': int(medium_confidence),
                'low_confidence': int(low_confidence),
                'manual_corrections': int(manual_corrections)
            },
            'match_methods': match_methods,
            'folder_metrics': folder_metrics,
            'quality_score': round(quality_score, 2)
        }
        
        return self.metrics
    
    def analyze_folders(self):
        """Analyze folder structure and contents."""
        
        unique_customer_ids = self.df['customer_id'].dropna().unique()
        
        folders_exist = 0
        folders_empty = 0
        folders_with_files = 0
        total_pdfs = 0
        
        for customer_id in unique_customer_ids:
            folder_path = os.path.join(FOLDERS_DIR, customer_id)
            if os.path.exists(folder_path):
                folders_exist += 1
                files = [f for f in os.listdir(folder_path) if f.endswith('.pdf')]
                if files:
                    folders_with_files += 1
                    total_pdfs += len(files)
                else:
                    folders_empty += 1
        
        return {
            'total_customer_ids': len(unique_customer_ids),
            'folders_exist': folders_exist,
            'folders_missing': len(unique_customer_ids) - folders_exist,
            'folders_empty': folders_empty,
            'folders_with_files': folders_with_files,
            'total_pdfs': total_pdfs
        }
    
    def calculate_quality_score(self, id_coverage, credit_coverage, high_conf_pct):
        """Calculate overall quality score (0-100)."""
        
        # Weighted scoring
        id_weight = 0.3  # 30% weight for customer ID coverage
        credit_weight = 0.4  # 40% weight for credit coverage
        quality_weight = 0.3  # 30% weight for match quality
        
        score = (
            (id_coverage * id_weight) +
            (credit_coverage * credit_weight) +
            (high_conf_pct * quality_weight)
        )
        
        return min(100, max(0, score))
    
    def identify_issues(self):
        """Identify current data quality issues."""
        
        issues = []
        
        # Check for duplicate customer IDs
        duplicates = self.df[self.df.duplicated(subset=['customer_id', 'tenant_id'], keep=False)]
        if len(duplicates) > 0:
            issues.append({
                'type': 'DUPLICATE_RECORDS',
                'severity': 'HIGH',
                'count': len(duplicates),
                'description': f"Found {len(duplicates)} duplicate customer-tenant combinations"
            })
        
        # Check for very low confidence matches
        very_low = self.df[(self.df['match_score'] > 0) & (self.df['match_score'] < 50)]
        if len(very_low) > 0:
            issues.append({
                'type': 'VERY_LOW_CONFIDENCE',
                'severity': 'HIGH',
                'count': len(very_low),
                'description': f"Found {len(very_low)} matches with < 50% confidence"
            })
        
        # Check for missing critical data
        missing_both = self.df[(self.df['customer_id'].isna()) & (self.df['match_score'] == 0)]
        if len(missing_both) > 0:
            issues.append({
                'type': 'MISSING_BOTH',
                'severity': 'MEDIUM',
                'count': len(missing_both),
                'description': f"Found {len(missing_both)} records with no customer ID and no credit match"
            })
        
        # Check for folders without PDFs
        if self.metrics['folder_metrics']['folders_empty'] > 10:
            issues.append({
                'type': 'EMPTY_FOLDERS',
                'severity': 'LOW',
                'count': self.metrics['folder_metrics']['folders_empty'],
                'description': f"{self.metrics['folder_metrics']['folders_empty']} folders exist but are empty"
            })
        
        return issues
    
    def compare_with_history(self):
        """Compare current metrics with historical data."""
        
        if os.path.exists(METRICS_FILE):
            with open(METRICS_FILE, 'r') as f:
                history = json.load(f)
        else:
            history = []
        
        improvements = []
        regressions = []
        
        if history:
            last_metrics = history[-1]
            
            # Compare key metrics
            metrics_to_compare = [
                ('customer_id_coverage', ['customer_id_metrics', 'coverage_pct']),
                ('credit_coverage', ['credit_match_metrics', 'coverage_pct']),
                ('quality_score', ['quality_score']),
                ('high_confidence', ['match_quality', 'high_confidence'])
            ]
            
            for name, path in metrics_to_compare:
                current_val = self.metrics
                last_val = last_metrics
                
                for key in path:
                    current_val = current_val.get(key, 0)
                    last_val = last_val.get(key, 0)
                
                diff = current_val - last_val
                
                if diff > 0:
                    improvements.append(f"{name}: +{diff:.2f}")
                elif diff < 0:
                    regressions.append(f"{name}: {diff:.2f}")
        
        # Save current metrics to history
        history.append(self.metrics)
        
        # Keep only last 30 entries
        if len(history) > 30:
            history = history[-30:]
        
        with open(METRICS_FILE, 'w') as f:
            json.dump(history, f, indent=2, cls=NumpyEncoder)
        
        return improvements, regressions
    
    def generate_report(self):
        """Generate monitoring report."""
        
        issues = self.identify_issues()
        improvements, regressions = self.compare_with_history()
        
        timestamp_str = self.timestamp.strftime("%Y%m%d_%H%M%S")
        report_path = os.path.join(OUTPUT_DIR, f"quality_monitor_{timestamp_str}.md")
        
        report = f"""# Credit Report Quality Monitoring Report
Generated: {self.timestamp.strftime("%Y-%m-%d %H:%M:%S")}

## 📊 Overall Quality Score: {self.metrics['quality_score']}/100

## Key Metrics

### Customer ID Coverage
- **Records with IDs**: {self.metrics['customer_id_metrics']['with_ids']} ({self.metrics['customer_id_metrics']['coverage_pct']}%)
- **Missing IDs**: {self.metrics['customer_id_metrics']['without_ids']}

### Credit Match Coverage
- **Records with Credit**: {self.metrics['credit_match_metrics']['with_credit']} ({self.metrics['credit_match_metrics']['coverage_pct']}%)
- **No Match**: {self.metrics['credit_match_metrics']['no_match']}

### Match Quality Distribution
- **High Confidence (≥90%)**: {self.metrics['match_quality']['high_confidence']}
- **Medium Confidence (70-89%)**: {self.metrics['match_quality']['medium_confidence']}
- **Low Confidence (<70%)**: {self.metrics['match_quality']['low_confidence']}
- **Manual Corrections**: {self.metrics['match_quality']['manual_corrections']}

### Folder Organization
- **Total Customer IDs**: {self.metrics['folder_metrics']['total_customer_ids']}
- **Folders Exist**: {self.metrics['folder_metrics']['folders_exist']}
- **Folders Missing**: {self.metrics['folder_metrics']['folders_missing']}
- **Empty Folders**: {self.metrics['folder_metrics']['folders_empty']}
- **Folders with PDFs**: {self.metrics['folder_metrics']['folders_with_files']}

## 🔍 Current Issues

"""
        
        if issues:
            for issue in issues:
                emoji = "🔴" if issue['severity'] == 'HIGH' else "🟡" if issue['severity'] == 'MEDIUM' else "🟢"
                report += f"{emoji} **{issue['type']}**: {issue['description']}\n"
        else:
            report += "✅ No significant issues detected\n"
        
        report += "\n## 📈 Trend Analysis\n\n"
        
        if improvements:
            report += "### Improvements Since Last Check\n"
            for imp in improvements:
                report += f"- ✅ {imp}\n"
            report += "\n"
        
        if regressions:
            report += "### Regressions Since Last Check\n"
            for reg in regressions:
                report += f"- ⚠️ {reg}\n"
            report += "\n"
        
        if not improvements and not regressions:
            report += "First monitoring run - no historical data for comparison.\n"
        
        report += f"""

## Recommendations

1. **Priority Actions**:
   - Address HIGH severity issues first
   - Focus on obtaining credit reports for empty folders
   - Assign customer IDs to remaining records

2. **Quality Targets**:
   - Customer ID Coverage: 100% (current: {self.metrics['customer_id_metrics']['coverage_pct']}%)
   - Credit Coverage: 70% (current: {self.metrics['credit_match_metrics']['coverage_pct']}%)
   - High Confidence Matches: 90% (current: {self.metrics['match_quality']['high_confidence']}/{self.metrics['credit_match_metrics']['with_credit']})

3. **Next Review**: Run this monitor weekly to track progress
"""
        
        with open(report_path, 'w') as f:
            f.write(report)
        
        return report_path
    
    def print_summary(self):
        """Print summary to console."""
        
        print("\n" + "="*60)
        print(f"QUALITY SCORE: {self.metrics['quality_score']}/100")
        print("="*60)
        
        print(f"\n📊 Coverage Metrics:")
        print(f"  • Customer ID Coverage: {self.metrics['customer_id_metrics']['coverage_pct']}%")
        print(f"  • Credit Report Coverage: {self.metrics['credit_match_metrics']['coverage_pct']}%")
        
        print(f"\n📁 Folder Status:")
        print(f"  • Folders Exist: {self.metrics['folder_metrics']['folders_exist']}/{self.metrics['folder_metrics']['total_customer_ids']}")
        print(f"  • Empty Folders: {self.metrics['folder_metrics']['folders_empty']}")
        print(f"  • With PDFs: {self.metrics['folder_metrics']['folders_with_files']}")
        
        issues = self.identify_issues()
        if issues:
            print(f"\n⚠️  Issues Detected: {len(issues)}")
            for issue in issues[:3]:  # Show top 3
                print(f"  • {issue['type']}: {issue['count']} records")

def main():
    print("🔍 Credit Report Quality Monitor")
    print("="*60)
    
    monitor = CreditQualityMonitor()
    
    print("Calculating metrics...")
    monitor.calculate_metrics()
    
    print("Generating report...")
    report_path = monitor.generate_report()
    
    monitor.print_summary()
    
    print(f"\n📄 Report saved to: {report_path}")
    print(f"📊 Metrics history updated: {METRICS_FILE}")
    
    print("\n✅ Monitoring complete!")
    print("Run this script weekly to track improvements.")

if __name__ == "__main__":
    main()