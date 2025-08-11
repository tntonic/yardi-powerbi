# Low Confidence Credit Matches - Action Plan

## Executive Summary
**Total Mismatches Identified**: 50 out of 86 credit files (58%)
- **Critical Issues**: 4 records (completely wrong companies)
- **High Priority**: 4 records (industry confusion)  
- **Medium Priority**: 7 records (parent/subsidiary issues)
- **Low Priority**: 35 records (name variations)
- **Missing Customer IDs**: 10 records

## 🚨 CRITICAL - Immediate Replacement Required

These are completely wrong companies that need new credit reports:

### 1. Event Link (c0000270)
- **Current Wrong File**: EventLink, LLC subsidiary info
- **Similarity**: Only 24%
- **Action**: Delete EventLink PDF, obtain correct "Event Link" credit report
- **Note**: Appears to be a partial match confusion

### 2. Harimatec Inc. (NO CUSTOMER ID)
- **Current Wrong File**: Harimatec, Inc with parent company info
- **Similarity**: Only 24.7%
- **Action**: Assign customer ID first, then get correct credit report
- **Note**: Name appears similar but is wrong subsidiary

### 3. JL Services Group (c0000385)
- **Current Wrong File**: Precision Facility Group
- **Similarity**: Only 25.8%
- **Action**: Replace with correct JL Services Group credit report
- **Note**: Completely different company

### 4. Z.One Concept USA (c0000766)
- **Current Wrong File**: Has parent company extended info
- **Similarity**: Only 28.8%
- **Action**: Get simpler Z.One Concept USA report without parent details

## ⚠️ HIGH PRIORITY - Industry Confusion

These companies were matched to competitors or similar businesses:

### 5. Superior Supply Chain Management (c0000678)
- **Wrong**: IMI Management (47.3% match)
- **Fix**: Replace with correct Superior Supply Chain credit

### 6. KPower Global Logistics (c0000410)  
- **Wrong**: GEMACP Logistics (55% match)
- **Fix**: Different logistics company - need KPower specific report

### 7. Centerpoint Marketing (c0000178)
- **Wrong**: Marketing.com (55.6% match)
- **Fix**: Similar industry, wrong company

### 8. Mash Enterprise (c0000959)
- **Wrong**: Insight Enterprises (73.7% match)  
- **Fix**: Name similarity but different companies

## 📋 MEDIUM PRIORITY - Parent/Subsidiary Verification

These may be acceptable if parent companies guarantee:

| Customer | Tenant | Matched Credit | Action |
|----------|--------|----------------|--------|
| c0000586 | RD Foods America | RD Foods Americas (parent) | Verify if parent guarantee exists |
| c0001069 | Quench USA | Quench USA (Culligan sub) | Likely correct - verify |
| c0000771 | Marcolin Eyewear | Macrolin (typo in credit) | Fix typo in records |
| c0000746 | VIE DE France | Vie De France (parent) | Verify parent relationship |
| c0000147 | Blendco Systems | Momentum Exterior | Check if merger/acquisition |
| c0000759 | Xcision Medical | Viscot Medical | Verify if same company |
| c0000531 | Overhead Door | Chemed Corporation | Wrong - need Overhead Door credit |

## ✅ LOW PRIORITY - Name Variations

These appear to be the same company with name variations (35 records).
Sample requiring verification:
- Atlas Copco Compressors → Atlas Copco AB
- Werner Aero Services → Werner Aero, LLC  
- American Traffic Solutions → American Traffic Solutions (ATS)

## 🔍 Missing Customer IDs (10 Records)

Must assign customer IDs before creating folders:
1. Harimatec Inc.
2. American Traffic Solutions  
3. Digi America Inc.
4. Diagnostic Support Services (2 records)
5. On Time Express
6. Florida DeliCo
7. Atlantic Tape Company
8. Pro-Cam Georgia
9. SHLA Group

## Recommended Workflow

### Phase 1: Critical Fixes (This Week)
1. Fix the 4 critical mismatches
2. Assign customer IDs to 10 records
3. Create folders for new customer IDs

### Phase 2: High Priority (Next Week)
1. Replace 4 industry confusion cases
2. Verify and fix Overhead Door (c0000531)

### Phase 3: Verification (Within 2 Weeks)
1. Review parent/subsidiary relationships
2. Confirm name variations are correct
3. Update match methods to "Verified" for confirmed matches

## Scripts Available

- `identify_credit_mismatches.py` - Identifies all mismatches
- `analyze_all_mismatches.py` - Categorizes and prioritizes issues
- `fix_snaptire_credit.py` - Template for fixing individual records

## Success Metrics

Current state:
- Error rate: 58% (50/86)
- Critical errors: 4.7% (4/86)

Target after fixes:
- Error rate: < 10%
- Critical errors: 0%
- All records have customer IDs
- All folders have correct credit files

---

*Generated: August 10, 2025*  
*Next Review: After Phase 1 completion*