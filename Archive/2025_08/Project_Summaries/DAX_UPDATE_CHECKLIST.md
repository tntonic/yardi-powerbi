# DAX Update Checklist - Quick Reference

## 🚨 Critical Fixes Required

### Fix #1: Rent Roll Measures - Add MAX(sequence) Filter
```dax
// Add this filter to ALL rent roll measures:
FILTER(
    ALL(dim_fp_amendmentsunitspropertytenant),
    dim_fp_amendmentsunitspropertytenant[amendment sequence] = 
    CALCULATE(
        MAX(dim_fp_amendmentsunitspropertytenant[amendment sequence]),
        ALLEXCEPT(
            dim_fp_amendmentsunitspropertytenant,
            dim_fp_amendmentsunitspropertytenant[property hmy],
            dim_fp_amendmentsunitspropertytenant[tenant hmy]
        )
    )
)
```

### Fix #2: Include "Superseded" Status
```dax
// Change ALL status filters from:
[amendment status] = "Activated"

// To:
[amendment status] IN {"Activated", "Superseded"}
```

### Fix #3: Revenue Sign Convention
```dax
// For revenue accounts (4xxxx):
SUM(fact_total[amount]) * -1
```

## ✅ Measures to Update

### Rent Roll Category (15+ measures)
- [ ] Current Monthly Rent
- [ ] Current Annual Rent
- [ ] Current Rent Roll PSF
- [ ] Current Leased SF
- [ ] WALT (Months)
- [ ] Leases Expiring (Next 12 Months)
- [ ] Expiring Lease SF (Next 12 Months)
- [ ] Average Base Rent
- [ ] Effective Rent
- [ ] Market Rent Comparison

### Leasing Activity Category (15+ measures)
- [ ] New Leases Count
- [ ] New Leases SF
- [ ] Renewals Count
- [ ] Renewals SF
- [ ] Terminations Count
- [ ] Terminations SF
- [ ] Net Leasing Activity SF
- [ ] Retention Rate %
- [ ] Leasing Velocity
- [ ] Average Deal Size

### Financial Category (8+ measures)
- [ ] Total Revenue
- [ ] Operating Expenses
- [ ] NOI (Net Operating Income)
- [ ] NOI Margin %
- [ ] FPR NOI
- [ ] Revenue per SF
- [ ] Expense per SF
- [ ] NOI per SF

## 📊 Expected Accuracy Improvements

| Category | Current | After Fixes | Target |
|----------|---------|-------------|--------|
| Rent Roll | 93% | **97%** | 95-99% |
| Leasing | 91% | **96%** | 95-98% |
| Financial | 79% | **98%** | 98%+ |
| **Overall** | 85% | **97%** | 95%+ |

## 🔍 Quick Validation Tests

1. **Amendment Sequence Test**: Count unique property/tenant combos
2. **Status Test**: Compare counts with/without "Superseded"
3. **Revenue Sign Test**: Verify negative values for 4xxxx accounts
4. **Date Filter Test**: Check charge schedule date ranges

## 📁 Key Files

- **DAX Library**: `/Documentation/Core_Guides/Complete_DAX_Library_Production_Ready.dax`
- **Python Logic**: `/python scripts/generate_rent_roll_from_yardi.py`
- **Full Documentation**: `/Documentation/Implementation/Rent_Roll_Logic_Complete.md`

---
*Use this checklist to systematically update all DAX measures*
*Target completion: 4-6 hours of focused work*