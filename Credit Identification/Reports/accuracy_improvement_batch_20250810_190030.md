# Credit Match Accuracy Improvement Report
Generated: 2025-08-10 19:00:30
Mode: Automatic Batch Processing

## Executive Summary
Automatically analyzed and cleaned credit matches to improve overall data accuracy.
Removed matches with < 40% name similarity.

## 🎯 Key Results

### Matches Removed: 35
- **Before**: 80 total matches
- **After**: 45 total matches
- **Improvement**: 30.0% accuracy increase

## 📊 Quality Distribution

### Before Cleaning
- High Confidence (≥90%): 40
- Medium Confidence (70-89%): 40
- Low Confidence (<70%): 0

### After Cleaning
- High Confidence (≥90%): 36
- Medium Confidence (70-89%): 9
- Low Confidence (<70%): 0

## 📋 Analysis Summary

### Actions Taken
- **REMOVE**: 35 records
- **KEEP**: 33 records
- **REVIEW**: 12 records


## 🗑️ Records Cleaned

### Top 20 Removed Matches
| Customer ID | Tenant Name | Removed Match | Similarity |
|-------------|-------------|---------------|------------|
| c0000181 | CF17 Management, LLC | WeldFit Management Holdin | 57.1% |
| c0000215 | Cryovation LLC | Motorvation LLC | 66.7% |
| c0000726 | Turbo Systems US Inc. | Beard Integrated Systems, | 50.0% |
| c0000367 | Insight North America, In | ACTEGA North America, Inc | 29.7% |
| c0000147 | Blendco Systems, LLC | Momentum Exterior Systems | 40.7% |
| c0000209 | Corporate Facility Servic | Precision Facility Group, | 41.7% |
| c0000586 | RD Foods America, Inc. | RD Foods Americas Inc. (w | 48.5% |
| c0000142 | Biogen Laboratory Corpora | Chemed Corporation | 46.2% |
| c0000746 | VIE DE France Yamazaki In | Vie De France Yamazaki, I | 48.9% |
| c0000632 | Sigma Global, Inc. | Global Packaging, Inc. | 42.9% |
| c0000645 | South State, Inc. | Seal South, Inc. | 47.6% |
| c0000095 | American HVAC Inc | American Musical Supply,  | 47.6% |
| c0000330 | Greif Packaging LLC | GC Packaging, LLC (GCP) - | 33.8% |
| c0000418 | L&W Supply Corporation | ABC Supply Holding Corpor | 68.2% |
| c0000622 | Setzer's and Co. Inc. | SABBOW AND CO., INC. | 45.5% |
| c0000531 | Overhead Door Corporation | Chemed Corporation | 62.9% |
| c0000522 | OEM Accessories  Incorpor | Corning Incorporated | 66.7% |
| c0001036 | Genband Industries, LLC | 945 Industries, LLC | 68.8% |
| c0001076 | Atlantic Tape Company, In | Currey & Company, Inc. | 19.0% |
| c0001069 | Quench USA, Inc. | Quench USA, Inc (sub of C | 33.9% |


## ✅ Records Kept (High Confidence)

### Top 10 Best Matches
| Customer ID | Tenant Name | Credit Match | Similarity |
|-------------|-------------|--------------|------------|
| c0000494 | Motorvation LLC | Motorvation LLC | 100.0% |
| c0000056 | True World Foods Columbus | True World Foods Columbus | 100.0% |
| c0000279 | Fastenal Company | Fastenal Company | 100.0% |
| c0000136 | Bengal Converting Service | Bengal Converting Service | 100.0% |
| c0000378 | Jade Carpentry Contractor | Jade Carpentry Contractor | 100.0% |
| c0000159 | Bunting Magnetics Company | Bunting Magnetics Co. | 100.0% |
| c0000638 | Snap Tire, Inc. | Snap Tire, Inc. | 100.0% |
| c0000793 | NJ/NY Gotham Football Clu | NJ/NY Gotham Football Clu | 100.0% |
| c0000056 | True World Foods Columbus | True World Foods Columbus | 100.0% |
| c0001058 | Innoved Institute LLC | Innoved Institute, LLC | 100.0% |


## 📈 Improvement Metrics

1. **Accuracy Increase**: 30.0%
2. **Bad Matches Removed**: 35
3. **Average Similarity Before**: 72.5%
4. **Average Similarity After**: 91.5%

## 🎯 Next Steps

1. **Obtain Credit Reports**: Get correct reports for the 35 companies whose matches were removed
2. **Review Medium Matches**: 12 records marked for review may need manual verification
3. **Update Threshold**: Recommend updating system threshold to 85% minimum
4. **Monitor Quality**: Run quality monitor to track improvements

## Files Generated

- Analysis Details: `accuracy_analysis_20250810_190030.csv`
- Removed Records: `removed_matches_20250810_190030.csv`
- This Report: `/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Credit Identification/Reports/accuracy_improvement_batch_20250810_190030.md`
