# Credit Report Needs Analysis
Generated: 2025-08-10 18:02:38

## Summary Statistics

- **Total Companies Needing Credit Reports**: 96
- **Critical Priority**: 6
- **High Priority**: 15
- **Medium Priority**: 31
- **Low Priority**: 19
- **Need Review**: 0
- **Need Customer ID First**: 25

## Priority Categories

### 🚨 CRITICAL - Immediate Action Required
These are companies where we removed wrong credit reports and need replacements:

| Customer ID | Company Name | Property | Folder Status |
|-------------|--------------|----------|---------------|
| c0000178 | Centerpoint Marketing Inc. | 2101 Arthur Avenue | HAS_1_FILES |
| c0000270 | Event Link | 770 Arthur Avenue | HAS_1_FILES |
| c0000385 | JL Services Group, Inc. | 201 James Street | NO_FOLDER |
| c0000410 | KPower Global Logistics, LLC | 4290 Delp Street | HAS_1_FILES |
| c0000959 | Mash Enterprise, LLC | 3905 Steve Reynolds Blvd | NO_FOLDER |
| c0000678 | Superior Supply Chain Management Inc | 4600&4630 Frederick Drive | HAS_1_FILES |


### ⚠️ HIGH - New Customer IDs
Companies with newly assigned customer IDs needing first credit reports:

| Customer ID | Company Name | Property | Folder Status |
|-------------|--------------|----------|---------------|
| c0001071 | American Traffic Solutions, Inc. | 9 S. Forrest Avenue | EMPTY |
| c0001076 | Atlantic Tape Company, Inc. | 6704 N 54th St | EMPTY |
| c0001073 | Diagnostic Support Services, Inc. | 1064 N Garfield | EMPTY |
| c0001073 | Diagnostic Support Services, Inc. | 1064 N Garfield | EMPTY |
| c0001072 | Digi America Inc. | 155 Pierce Street | EMPTY |
| c0001075 | Florida DeliCo, LLC | 7720 Philips Highway | EMPTY |
| c0001048 | Flower Shop El Chapin LLC | 10755 Sanden Drive | HAS_1_FILES |
| c0001036 | Genband Industries, LLC | 1100-1150 Howard | HAS_1_FILES |
| c0001070 | Harimatec Inc. | 1965 Evergreen Boulevard | EMPTY |
| c0001058 | Innoved Institute LLC | 770 Arthur Avenue | HAS_1_FILES |

*Plus 5 more...*


### 📋 MEDIUM - Fund 2 Companies
Important Fund 2 companies without credit reports:

| Customer ID | Company Name | Property |
|-------------|--------------|----------|
| c0000075 | AFS World Truck Repair LP | 3041 Marwin Road |
| c0000100 | Amphenol EEC, Inc. | 1701 Birchwood |
| c0000177 | CCL Label, INC. | 390 New Albany Road |
| c0000164 | Cablevision of Oakland | 40 Potash Road |
| c0000193 | Clingan Steel, Inc. | 2101 Arthur Avenue |
| c0000199 | Combocap Inc. | 125 Algonquin Parkway |
| c0000206 | Content Critical Solutions, Inc. | 121 Moonachie Ave |
| c0000795 | Darby Dental Supply, LLC | 4290 Delp Street |
| c0000245 | EA Engineering, Science, and Technology, Inc. | 1601-1641 Sherman Avenue |
| c0000251 | Economy Tire, Inc. | 11839 Shiloh Rd |

*Plus 21 more...*


### 📊 Statistics by Fund

| Fund | Need Credit Reports | Percentage of Fund |
|------|-------------------|-------------------|
| Fund 2 | 51 | - |
| Fund 3 | 45 | - |


## Recommended Action Plan

### Week 1 - Critical & High Priority
1. **Obtain credit reports for 6 critical companies** where wrong reports were removed
2. **Process credit reports for 9 new customer IDs** with empty folders ready

### Week 2-3 - Medium Priority
1. **Fund 2 companies** - Focus on high-value tenants
2. **Create folders** for companies without them
3. **Assign remaining customer IDs** to companies missing them

### Week 4 - Low Priority & Review
1. **Review low confidence matches** to determine if replacement needed
2. **Process remaining low priority** companies

## Export Files

- **Full List**: `{csv_path}`
- **This Report**: `{report_path}`

## Folder Readiness

- **Empty Folders (Ready)**: {len(needs_df[needs_df['folder_status'] == 'EMPTY'])}
- **No Folder Yet**: {len(needs_df[needs_df['folder_status'] == 'NO_FOLDER'])}
- **Has Files (Need Cleanup)**: {len(needs_df[needs_df['folder_status'].str.startswith('HAS_') == True]) if 'folder_status' in needs_df.columns else 0}
- **No Customer ID**: {len(needs_df[needs_df['folder_status'] == 'NO_ID'])}
