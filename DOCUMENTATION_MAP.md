# Documentation Map - Yardi PowerBI Project

## Overview
This guide explains the purpose and contents of each folder in the Yardi PowerBI repository, helping you find the right resources quickly.

## 📁 Folder Structure and Purpose

### 🎯 Claude_AI_Reference/ (PRIMARY FOR CLAUDE.AI)
**Purpose**: Clean, self-contained reference library for Claude.ai projects
**When to use**: Upload this entire folder to Claude.ai when building Power BI dashboards
**Contents**:
- `DAX_Measures/` - Production v4.1 DAX library with 127 measures
- `Documentation/` - Core guides numbered 01-05 for easy reference
- `Dashboard_Templates/` - 4 ready-to-use dashboard specifications
- `Reference_Guides/` - Business logic, mappings, and patterns
- `Validation_Framework/` - SQL scripts and testing guides
- `README.md` - Complete usage guide for Claude.ai integration

### 📚 Documentation/ (EXTENDED TECHNICAL DOCS)
**Purpose**: Comprehensive technical documentation for developers
**When to use**: Deep dives into implementation details, troubleshooting complex issues
**Contents**:
- `Core_Guides/` - Detailed implementation guides and DAX library
- `Implementation/` - Step-by-step implementation instructions
- `Reference/` - Extended reference materials
- `Validation/` - Test results, edge cases, and validation reports
- SQL scripts for database operations

### 🔧 Development/ (ACTIVE DEVELOPMENT)
**Purpose**: Development tools, test scripts, and work-in-progress
**When to use**: Running validation tests, generating reports, debugging
**Contents**:
- `Python_Scripts/` - Validation and generation scripts
- `Test_Automation_Framework/` - Automated testing suite
- `Fund2_Validation_Results/` - Fund-specific test results
- `Working_Files/` - Temporary development files

### 📊 Data/ (SOURCE DATA)
**Purpose**: CSV exports from Yardi and filtered datasets
**When to use**: Reference data, testing with specific funds
**Contents**:
- `Yardi_Tables/` - 32 CSV table exports from Yardi
- `Fund2_Filtered/` - Fund 2 specific filtered data

### 🗄️ Archive/ (HISTORICAL VERSIONS)
**Purpose**: Previous versions and outdated documentation
**When to use**: Reference historical changes, recovery of old versions
**Contents**:
- `2025_08/` - Dated archive folders with reports and summaries
- `DAX_Versions/` - Historical DAX versions (v2, v3, v4, v5)
- `Implementation_Docs/` - Outdated implementation guides
- `Leasing_Activity_Backup/` - Redundant query files

### 📝 YSQL Tables/ (YARDI QUERIES)
**Purpose**: YSQL query templates and data dictionary
**When to use**: Creating new Yardi data extracts, understanding table structures
**Contents**:
- Query templates for various Yardi reports
- Data dictionary and table relationships
- Sample data exports

### 📈 rent rolls/ (VALIDATION DATA)
**Purpose**: Native Yardi rent roll exports for accuracy validation
**When to use**: Validating Power BI calculations against Yardi
**Contents**:
- Excel exports by quarter (e.g., 03.31.25.xlsx)
- Used for 95-99% accuracy validation targets

## 🚀 Quick Start Guide

### For Claude.ai Users:
1. Upload entire `Claude_AI_Reference/` folder to your Claude project
2. Reference specific files when asking questions
3. Start with `01_Quick_Start_Guide.md` for implementation

### For Developers:
1. Check `Documentation/` for detailed technical specs
2. Run validation scripts from `Development/Python_Scripts/`
3. Test with data from `Data/Yardi_Tables/`

### For Testing:
1. Use `Development/Test_Automation_Framework/` for automated tests
2. Validate against exports in `rent rolls/` folder
3. Check accuracy benchmarks in validation reports

## 📋 Key Files Reference

### Production DAX (v4.1):
- **Primary**: `Claude_AI_Reference/DAX_Measures/Complete_DAX_Library_v4.1_Production.dax`
- **Backup**: `Documentation/Core_Guides/Complete_DAX_Library_v4.1_Production.dax`
- **Top 20**: `Claude_AI_Reference/DAX_Measures/Top_20_Essential_Measures.dax`

### Critical Documentation:
- **Quick Start**: `Claude_AI_Reference/Documentation/01_Quick_Start_Guide.md`
- **Data Model**: `Claude_AI_Reference/Documentation/02_Data_Model_Guide.md`
- **Common Issues**: `Claude_AI_Reference/Documentation/05_Common_Issues_Solutions.md`

### Validation Scripts:
- **Complete Workflow**: `Development/Python_Scripts/run_complete_workflow.py`
- **Top 20 Accuracy**: `Development/Python_Scripts/top_20_measures_accuracy_test.py`
- **Test Orchestration**: `Development/Test_Automation_Framework/test_orchestrator.py`

## 🎯 Version Information

**Current Production Version**: 4.1 (YSQL Enhanced)
- **Total Measures**: 127
- **Accuracy Target**: 95-99% for rent roll
- **Last Updated**: 2025-08-10
- **Key Enhancement**: Month-to-month lease identification

## 📞 Support

For questions or issues:
1. Check `Claude_AI_Reference/Documentation/05_Common_Issues_Solutions.md`
2. Review validation reports in `Archive/2025_08/Validation_Reports/`
3. Run diagnostic scripts from `Development/Python_Scripts/`

---
*Documentation Map Version 1.0 - Created 2025-08-10*