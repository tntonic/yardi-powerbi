-- =====================================================
-- DOWNTIME VALIDATION QUERIES
-- Version: 5.1
-- Purpose: Validate lease vacancy downtime calculations
-- =====================================================

-- =====================================================
-- 1. VALIDATE DOWNTIME DATA AVAILABILITY
-- =====================================================

-- Check for new leases with prior lease data
WITH NewLeases AS (
    SELECT 
        fl.[Property HMY],
        fl.[Tenant Code],
        fl.[Proposal Type],
        fl.[Cash Flow Type],
        fl.[Deal Stage],
        fl.[dtStartDate] as NewLeaseStart,
        fl.[Starting Rent] as NewMonthlyRent,
        fl.[dArea] as NewLeaseSF
    FROM fact_leasingactivity fl
    WHERE fl.[Cash Flow Type] = 'Proposal'
        AND fl.[Proposal Type] = 'New Lease'
        AND fl.[Deal Stage] = 'Executed'
        AND fl.[dtStartDate] IS NOT NULL
),
PriorLeases AS (
    SELECT 
        fl.[Property HMY],
        fl.[Tenant Code],
        fl.[Cash Flow Type],
        fl.[dtEndDate] as PriorLeaseEnd,
        fl.[Starting Rent] as PriorMonthlyRent,
        fl.[dArea] as PriorLeaseSF
    FROM fact_leasingactivity fl
    WHERE fl.[Cash Flow Type] = 'Prior Lease'
        AND fl.[dtEndDate] IS NOT NULL
)
SELECT 
    COUNT(DISTINCT n.[Property HMY]) as PropertiesWithNewLeases,
    COUNT(DISTINCT p.[Property HMY]) as PropertiesWithPriorLeases,
    COUNT(DISTINCT n.[Property HMY]) - COUNT(DISTINCT 
        CASE WHEN p.[Property HMY] IS NOT NULL THEN n.[Property HMY] END) as PropertiesWithoutPriorData
FROM NewLeases n
LEFT JOIN PriorLeases p ON n.[Property HMY] = p.[Property HMY]
    AND p.PriorLeaseEnd < n.NewLeaseStart;

-- =====================================================
-- 2. CALCULATE DOWNTIME BY PROPERTY
-- =====================================================

WITH PropertyDowntime AS (
    SELECT 
        n.[Property HMY],
        n.NewLeaseStart,
        MAX(p.PriorLeaseEnd) as LastPriorLeaseEnd,
        DATEDIFF(MONTH, MAX(p.PriorLeaseEnd), n.NewLeaseStart) as DowntimeMonths,
        n.NewMonthlyRent,
        n.NewLeaseSF
    FROM (
        SELECT 
            [Property HMY],
            [dtStartDate] as NewLeaseStart,
            [Starting Rent] as NewMonthlyRent,
            [dArea] as NewLeaseSF
        FROM fact_leasingactivity
        WHERE [Cash Flow Type] = 'Proposal'
            AND [Proposal Type] = 'New Lease'
            AND [Deal Stage] = 'Executed'
            AND [dtStartDate] IS NOT NULL
    ) n
    LEFT JOIN (
        SELECT 
            [Property HMY],
            [dtEndDate] as PriorLeaseEnd
        FROM fact_leasingactivity
        WHERE [Cash Flow Type] = 'Prior Lease'
            AND [dtEndDate] IS NOT NULL
    ) p ON n.[Property HMY] = p.[Property HMY]
        AND p.PriorLeaseEnd < n.NewLeaseStart
    GROUP BY n.[Property HMY], n.NewLeaseStart, n.NewMonthlyRent, n.NewLeaseSF
)
SELECT 
    dp.[property name],
    pd.[Property HMY],
    pd.LastPriorLeaseEnd,
    pd.NewLeaseStart,
    pd.DowntimeMonths,
    pd.NewMonthlyRent,
    pd.DowntimeMonths * pd.NewMonthlyRent as LostRent,
    pd.NewLeaseSF
FROM PropertyDowntime pd
LEFT JOIN dim_property dp ON pd.[Property HMY] = dp.[id]
WHERE pd.DowntimeMonths IS NOT NULL
    AND pd.DowntimeMonths >= 0
ORDER BY pd.DowntimeMonths DESC;

-- =====================================================
-- 3. AGGREGATE DOWNTIME METRICS
-- =====================================================

WITH DowntimeCalc AS (
    SELECT 
        n.[Property HMY],
        dp.[Fund],
        DATEDIFF(MONTH, MAX(p.PriorLeaseEnd), n.NewLeaseStart) as DowntimeMonths,
        n.NewMonthlyRent,
        n.NewLeaseSF
    FROM (
        SELECT 
            [Property HMY],
            [dtStartDate] as NewLeaseStart,
            [Starting Rent] as NewMonthlyRent,
            [dArea] as NewLeaseSF
        FROM fact_leasingactivity
        WHERE [Cash Flow Type] = 'Proposal'
            AND [Proposal Type] = 'New Lease'
            AND [Deal Stage] = 'Executed'
            AND [dtStartDate] IS NOT NULL
    ) n
    LEFT JOIN (
        SELECT 
            [Property HMY],
            [dtEndDate] as PriorLeaseEnd
        FROM fact_leasingactivity
        WHERE [Cash Flow Type] = 'Prior Lease'
            AND [dtEndDate] IS NOT NULL
    ) p ON n.[Property HMY] = p.[Property HMY]
        AND p.PriorLeaseEnd < n.NewLeaseStart
    LEFT JOIN dim_property dp ON n.[Property HMY] = dp.[id]
    GROUP BY n.[Property HMY], dp.[Fund], n.NewLeaseStart, n.NewMonthlyRent, n.NewLeaseSF
)
SELECT 
    'Portfolio Total' as Level,
    COUNT(*) as NewLeaseCount,
    AVG(DowntimeMonths) as AvgDowntimeMonths,
    SUM(DowntimeMonths * NewMonthlyRent) as TotalLostRent,
    SUM(NewLeaseSF) as TotalNewLeaseSF
FROM DowntimeCalc
WHERE DowntimeMonths IS NOT NULL
    AND DowntimeMonths >= 0

UNION ALL

SELECT 
    'Fund ' + [Fund] as Level,
    COUNT(*) as NewLeaseCount,
    AVG(DowntimeMonths) as AvgDowntimeMonths,
    SUM(DowntimeMonths * NewMonthlyRent) as TotalLostRent,
    SUM(NewLeaseSF) as TotalNewLeaseSF
FROM DowntimeCalc
WHERE DowntimeMonths IS NOT NULL
    AND DowntimeMonths >= 0
    AND [Fund] IS NOT NULL
GROUP BY [Fund];

-- =====================================================
-- 4. VALIDATE WEIGHTED RENT CALCULATIONS
-- =====================================================

-- Compare simple average vs weighted average
WITH ExecutedLeases AS (
    SELECT 
        [Starting Rent] * 12 as AnnualRent,
        [dArea] as SF,
        dp.[Fund]
    FROM fact_leasingactivity fl
    LEFT JOIN dim_property dp ON fl.[Property HMY] = dp.[id]
    WHERE fl.[Deal Stage] = 'Executed'
        AND fl.[dArea] > 0
        AND fl.[Starting Rent] IS NOT NULL
)
SELECT 
    'Simple Average' as CalculationType,
    AVG(AnnualRent / NULLIF(SF, 0)) as RentPSF
FROM ExecutedLeases

UNION ALL

SELECT 
    'Weighted Average' as CalculationType,
    SUM(AnnualRent) / NULLIF(SUM(SF), 0) as RentPSF
FROM ExecutedLeases;

-- =====================================================
-- 5. VALIDATE LEASE SPREADS
-- =====================================================

WITH SpreadCalc AS (
    SELECT 
        curr.[Property HMY],
        curr.CurrentRent,
        curr.CurrentSF,
        prior.PriorRent,
        prior.PriorSF
    FROM (
        SELECT 
            [Property HMY],
            [Starting Rent] as CurrentRent,
            [dArea] as CurrentSF
        FROM fact_leasingactivity
        WHERE [Cash Flow Type] = 'Proposal'
            AND [Deal Stage] = 'Executed'
            AND [dArea] > 0
    ) curr
    LEFT JOIN (
        SELECT 
            [Property HMY],
            [Starting Rent] as PriorRent,
            [dArea] as PriorSF
        FROM fact_leasingactivity
        WHERE [Cash Flow Type] = 'Prior Lease'
            AND [dArea] > 0
    ) prior ON curr.[Property HMY] = prior.[Property HMY]
)
SELECT 
    COUNT(*) as TotalDeals,
    -- Simple average spread
    AVG((CurrentRent - PriorRent) / NULLIF(PriorRent, 0) * 100) as SimpleAvgSpread,
    -- Weighted average spread
    (SUM(CurrentRent * CurrentSF) / NULLIF(SUM(CurrentSF), 0) - 
     SUM(PriorRent * PriorSF) / NULLIF(SUM(PriorSF), 0)) / 
    NULLIF(SUM(PriorRent * PriorSF) / NULLIF(SUM(PriorSF), 0), 0) * 100 as WeightedAvgSpread
FROM SpreadCalc
WHERE PriorRent IS NOT NULL;

-- =====================================================
-- 6. DATA QUALITY CHECKS
-- =====================================================

-- Check for overlapping leases (negative downtime)
WITH Overlaps AS (
    SELECT 
        n.[Property HMY],
        n.NewLeaseStart,
        MAX(p.PriorLeaseEnd) as LastPriorLeaseEnd,
        DATEDIFF(MONTH, MAX(p.PriorLeaseEnd), n.NewLeaseStart) as DowntimeMonths
    FROM (
        SELECT 
            [Property HMY],
            [dtStartDate] as NewLeaseStart
        FROM fact_leasingactivity
        WHERE [Cash Flow Type] = 'Proposal'
            AND [Proposal Type] = 'New Lease'
            AND [Deal Stage] = 'Executed'
    ) n
    LEFT JOIN (
        SELECT 
            [Property HMY],
            [dtEndDate] as PriorLeaseEnd
        FROM fact_leasingactivity
        WHERE [Cash Flow Type] = 'Prior Lease'
    ) p ON n.[Property HMY] = p.[Property HMY]
        AND p.PriorLeaseEnd < n.NewLeaseStart
    GROUP BY n.[Property HMY], n.NewLeaseStart
)
SELECT 
    COUNT(*) as OverlappingLeases,
    MIN(DowntimeMonths) as MaxOverlapMonths
FROM Overlaps
WHERE DowntimeMonths < 0;

-- =====================================================
-- END OF VALIDATION QUERIES
-- =====================================================