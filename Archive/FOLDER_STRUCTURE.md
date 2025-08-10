# Power BI v1.6 - Folder Structure

## Overview
This repository contains a Power BI analytics solution for commercial real estate data from Yardi systems, featuring a 32-table data model with 122 production-ready DAX measures.

## Directory Structure

```
PBI v1.6/
├── README.md                    # Project overview
├── CLAUDE.md                    # Claude Code guidance
├── FOLDER_STRUCTURE.md          # This file
│
├── Documentation/               # All project documentation
│   ├── Core_Guides/            # Essential implementation guides
│   │   ├── Complete_Data_Model_Guide.md
│   │   ├── Complete_DAX_Library_Production_Ready.dax
│   │   ├── Data_Dictionary.md
│   │   └── Quick_Start_Checklist.md
│   │
│   ├── Dashboard_Templates/     # Pre-built dashboard designs
│   │   ├── Executive_Summary_Dashboard.md
│   │   ├── Financial_Performance_Dashboard.md
│   │   ├── Leasing_Activity_Dashboard.md
│   │   └── Rent_Roll_Dashboard.md
│   │
│   ├── Implementation/          # How-to guides and solutions
│   │   ├── Common_Issues_Solutions.md
│   │   ├── Leasing_Activity_Analysis.md
│   │   ├── Measure_Implementation_Guide.md
│   │   └── Rent_Roll_Implementation.md
│   │
│   ├── Reference/               # Technical references
│   │   ├── Account_Mapping_Reference.md
│   │   ├── Book_Strategy_Guide.md
│   │   ├── Business_Logic_Reference.md
│   │   ├── Calculation_Patterns_Reference.md
│   │   ├── Column_Name_Mapping_PowerBI_to_Yardi.md
│   │   ├── Granularity_Best_Practices.md
│   │   └── Table_Relationships_Reference.md
│   │
│   └── Validation/              # Testing and validation resources
│       ├── Architecture_Review_Report.md
│       ├── Business_Logic_Validation_Report.md
│       ├── Phase2_DAX_Testing_Results.md
│       ├── Validation_Progress.md
│       ├── Validation_and_Testing_Guide.md
│       └── Validation_Scripts/
│           ├── Phase1_Data_Model_Validation.sql
│           └── Phase2_DAX_Validation_Measures.dax
│
├── Data/                        # Sample data for testing
│   └── Yardi_Tables/           # CSV exports from Yardi
│       ├── fact_*              # Fact tables
│       └── dim_*               # Dimension tables
│
└── Archives/                    # Historical/deprecated files
    ├── HANDOFF_SUMMARY.md
    └── PowerBI_Validation_Report.md
```

## Quick Navigation

### Getting Started
1. Start with `Documentation/Core_Guides/Quick_Start_Checklist.md`
2. Review the data model in `Documentation/Core_Guides/Complete_Data_Model_Guide.md`
3. Import DAX measures from `Documentation/Core_Guides/Complete_DAX_Library_Production_Ready.dax`

### Building Dashboards
- Choose a template from `Documentation/Dashboard_Templates/`
- Follow implementation guides in `Documentation/Implementation/`
- Reference technical details in `Documentation/Reference/`

### Testing & Validation
- Use scripts in `Documentation/Validation/Validation_Scripts/`
- Follow the testing guide in `Documentation/Validation/Validation_and_Testing_Guide.md`

### Sample Data
- All test data is in `Data/Yardi_Tables/`
- 32 tables total (fact and dimension tables)

## Key Files

- **Complete_DAX_Library_Production_Ready.dax**: All 122 production-ready DAX measures
- **Complete_Data_Model_Guide.md**: Detailed 32-table architecture documentation
- **Quick_Start_Checklist.md**: Step-by-step implementation timeline
- **Data_Dictionary.md**: Complete field definitions and relationships