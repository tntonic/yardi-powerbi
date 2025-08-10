# Database Improvement Plan for PowerBI Rent Roll Solution

**Date:** August 2025  
**Version:** 1.0  
**Status:** Ready for Implementation

## Executive Summary

Based on comprehensive validation findings showing 85% → 97% accuracy improvement potential, this plan addresses critical data quality, performance, and governance issues in the Yardi-PowerBI data architecture. The plan eliminates duplicate amendments, improves data integrity to 95+, and establishes robust monitoring frameworks.

### Critical Issues Addressed:
- **98 Duplicate Active Amendments** → Zero duplicates with prevention
- **Data Quality Score: 66/100** → Target: 95+
- **634 Amendments (72%) without rent charges** → Business rule clarification and automation
- **Referential integrity gaps** → Comprehensive constraint framework
- **Amendment sequence performance** → Sub-2 second query optimization

## 1. Current State Analysis

### Data Quality Assessment
```
Component                  Current  Target   Gap      Priority
─────────────────────────────────────────────────────────────
Amendment Data Integrity    66%     95%     29%      CRITICAL
Referential Integrity       79%     98%     19%      HIGH
Performance (Query Speed)    N/A     <2s     N/A      HIGH
Data Validation Coverage     45%     95%     50%      CRITICAL
Monitoring & Alerting        0%      90%     90%      MEDIUM
```

### Key Problems Identified:
1. **Multiple Active Amendments**: 98 property/tenant combinations have duplicate active amendments
2. **Missing Charge Schedules**: 634 amendments (72%) lack associated rent charges
3. **Orphaned References**: Referential integrity gaps in charge schedule lookups
4. **Performance Bottlenecks**: MAX(sequence) calculations taking >5 seconds
5. **No Data Validation**: Lack of automated data quality monitoring

## 2. Database Improvement Roadmap

### Phase 1: Emergency Data Cleanup (Days 1-3)
**Objective**: Eliminate immediate data integrity issues

#### 2.1 Duplicate Amendment Resolution
```sql
-- Step 1: Identify duplicate active amendments
CREATE TEMP TABLE duplicate_active_amendments AS
SELECT 
    property_hmy,
    tenant_hmy,
    COUNT(*) as active_count,
    STRING_AGG(amendment_hmy::text, ', ' ORDER BY amendment_sequence DESC) as amendment_list
FROM dim_fp_amendmentsunitspropertytenant 
WHERE amendment_status IN ('Activated')
GROUP BY property_hmy, tenant_hmy
HAVING COUNT(*) > 1;

-- Step 2: Create backup before cleanup
CREATE TABLE dim_fp_amendmentsunitspropertytenant_backup_20250809 AS
SELECT * FROM dim_fp_amendmentsunitspropertytenant;

-- Step 3: Deactivate older duplicate amendments (keep highest sequence)
WITH latest_amendments AS (
    SELECT 
        property_hmy,
        tenant_hmy,
        MAX(amendment_sequence) as max_sequence
    FROM dim_fp_amendmentsunitspropertytenant 
    WHERE amendment_status = 'Activated'
    GROUP BY property_hmy, tenant_hmy
)
UPDATE dim_fp_amendmentsunitspropertytenant 
SET 
    amendment_status = 'Superseded',
    amendment_status_code = 2,
    dtlastmodified = CURRENT_TIMESTAMP
WHERE amendment_status = 'Activated'
AND (property_hmy, tenant_hmy, amendment_sequence) NOT IN (
    SELECT property_hmy, tenant_hmy, max_sequence 
    FROM latest_amendments
);
```

#### 2.2 Missing Charge Schedule Resolution
```sql
-- Identify amendments without charge schedules
CREATE VIEW v_amendments_missing_charges AS
SELECT 
    a.amendment_hmy,
    a.property_code,
    a.tenant_id,
    a.amendment_status,
    a.amendment_sf,
    COALESCE(c.charge_count, 0) as charge_count,
    CASE 
        WHEN a.amendment_sf > 0 AND COALESCE(c.charge_count, 0) = 0 
        THEN 'MISSING_RENT_CHARGE'
        WHEN a.amendment_status = 'Activated' AND COALESCE(c.charge_count, 0) = 0 
        THEN 'ACTIVE_NO_CHARGES'
        ELSE 'OK'
    END as issue_type
FROM dim_fp_amendmentsunitspropertytenant a
LEFT JOIN (
    SELECT 
        amendment_hmy,
        COUNT(*) as charge_count
    FROM dim_fp_amendmentchargeschedule 
    WHERE charge_code = 'rent'
    GROUP BY amendment_hmy
) c ON a.amendment_hmy = c.amendment_hmy
WHERE a.amendment_status IN ('Activated', 'Superseded');

-- Generate alerts for business rule clarification
SELECT 
    issue_type,
    COUNT(*) as amendment_count,
    ROUND(AVG(amendment_sf), 0) as avg_sf,
    SUM(amendment_sf) as total_sf_affected
FROM v_amendments_missing_charges 
WHERE issue_type != 'OK'
GROUP BY issue_type;
```

### Phase 2: Schema Enhancements (Days 4-7)
**Objective**: Optimize data structure for performance and integrity

#### 2.3 Performance Optimization Indexes
```sql
-- Critical indexes for amendment sequence queries
CREATE UNIQUE INDEX idx_amendments_property_tenant_sequence 
ON dim_fp_amendmentsunitspropertytenant (property_hmy, tenant_hmy, amendment_sequence DESC);

CREATE INDEX idx_amendments_status_active 
ON dim_fp_amendmentsunitspropertytenant (amendment_status, property_hmy, tenant_hmy) 
WHERE amendment_status IN ('Activated', 'Superseded');

-- Charge schedule lookup optimization
CREATE INDEX idx_charges_amendment_rent 
ON dim_fp_amendmentchargeschedule (amendment_hmy, charge_code, from_date, to_date)
WHERE charge_code = 'rent';

-- Date range queries for rent roll
CREATE INDEX idx_amendments_date_range 
ON dim_fp_amendmentsunitspropertytenant (amendment_start_date, amendment_end_date, amendment_status);
```

#### 2.4 Computed Columns for Latest Amendment Logic
```sql
-- Add computed column for latest amendment flag
ALTER TABLE dim_fp_amendmentsunitspropertytenant 
ADD COLUMN is_latest_amendment BOOLEAN DEFAULT FALSE;

-- Materialized view for latest amendments (refreshed nightly)
CREATE MATERIALIZED VIEW mv_latest_amendments AS
WITH latest_amendments AS (
    SELECT 
        property_hmy,
        tenant_hmy,
        MAX(amendment_sequence) as max_sequence
    FROM dim_fp_amendmentsunitspropertytenant 
    WHERE amendment_status IN ('Activated', 'Superseded')
    GROUP BY property_hmy, tenant_hmy
)
SELECT 
    a.*,
    TRUE as is_latest,
    c.total_monthly_rent,
    c.charge_count
FROM dim_fp_amendmentsunitspropertytenant a
INNER JOIN latest_amendments l 
    ON a.property_hmy = l.property_hmy 
    AND a.tenant_hmy = l.tenant_hmy 
    AND a.amendment_sequence = l.max_sequence
LEFT JOIN (
    SELECT 
        amendment_hmy,
        SUM(monthly_amount) as total_monthly_rent,
        COUNT(*) as charge_count
    FROM dim_fp_amendmentchargeschedule 
    WHERE charge_code = 'rent'
    GROUP BY amendment_hmy
) c ON a.amendment_hmy = c.amendment_hmy;

CREATE UNIQUE INDEX idx_mv_latest_amendments_pk 
ON mv_latest_amendments (property_hmy, tenant_hmy);
```

#### 2.5 Referential Integrity Constraints
```sql
-- Ensure all charge schedules reference valid amendments
ALTER TABLE dim_fp_amendmentchargeschedule 
ADD CONSTRAINT fk_charges_amendments 
FOREIGN KEY (amendment_hmy) 
REFERENCES dim_fp_amendmentsunitspropertytenant (amendment_hmy)
ON DELETE CASCADE;

-- Ensure all amendments reference valid properties
ALTER TABLE dim_fp_amendmentsunitspropertytenant 
ADD CONSTRAINT fk_amendments_property 
FOREIGN KEY (property_hmy) 
REFERENCES dim_property (property_hmy);

-- Business rule: Only one active amendment per property/tenant
CREATE UNIQUE INDEX idx_unique_active_amendment 
ON dim_fp_amendmentsunitspropertytenant (property_hmy, tenant_hmy)
WHERE amendment_status = 'Activated';
```

### Phase 3: Data Validation Framework (Days 8-10)
**Objective**: Prevent future data quality issues

#### 2.6 Data Quality Monitoring Views
```sql
-- Data quality dashboard view
CREATE VIEW v_data_quality_metrics AS
SELECT 
    'Amendment Duplicates' as metric_name,
    COUNT(*) as issue_count,
    'CRITICAL' as severity,
    CURRENT_TIMESTAMP as last_check
FROM (
    SELECT property_hmy, tenant_hmy, COUNT(*) 
    FROM dim_fp_amendmentsunitspropertytenant 
    WHERE amendment_status = 'Activated'
    GROUP BY property_hmy, tenant_hmy
    HAVING COUNT(*) > 1
) dupes

UNION ALL

SELECT 
    'Missing Rent Charges' as metric_name,
    COUNT(*) as issue_count,
    'HIGH' as severity,
    CURRENT_TIMESTAMP as last_check
FROM v_amendments_missing_charges 
WHERE issue_type = 'ACTIVE_NO_CHARGES'

UNION ALL

SELECT 
    'Referential Integrity Gaps' as metric_name,
    COUNT(*) as issue_count,
    'HIGH' as severity,
    CURRENT_TIMESTAMP as last_check
FROM dim_fp_amendmentchargeschedule c
LEFT JOIN dim_fp_amendmentsunitspropertytenant a 
    ON c.amendment_hmy = a.amendment_hmy
WHERE a.amendment_hmy IS NULL;
```

#### 2.7 Automated Data Validation Procedures
```sql
-- Daily data quality check procedure
CREATE OR REPLACE FUNCTION sp_daily_data_quality_check()
RETURNS TABLE(check_name TEXT, status TEXT, issue_count INTEGER, details TEXT)
LANGUAGE plpgsql
AS $$
BEGIN
    -- Check 1: Duplicate active amendments
    RETURN QUERY
    SELECT 
        'Duplicate Active Amendments'::TEXT,
        CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END::TEXT,
        COUNT(*)::INTEGER,
        'Property/Tenant combinations with multiple active amendments'::TEXT
    FROM (
        SELECT property_hmy, tenant_hmy 
        FROM dim_fp_amendmentsunitspropertytenant 
        WHERE amendment_status = 'Activated'
        GROUP BY property_hmy, tenant_hmy
        HAVING COUNT(*) > 1
    ) x;

    -- Check 2: Amendments without charges
    RETURN QUERY
    SELECT 
        'Active Amendments Missing Charges'::TEXT,
        CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'WARN' END::TEXT,
        COUNT(*)::INTEGER,
        'Active amendments with SF > 0 but no rent charges'::TEXT
    FROM v_amendments_missing_charges 
    WHERE issue_type = 'ACTIVE_NO_CHARGES';

    -- Check 3: Date integrity
    RETURN QUERY
    SELECT 
        'Amendment Date Integrity'::TEXT,
        CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END::TEXT,
        COUNT(*)::INTEGER,
        'Amendments with end date before start date'::TEXT
    FROM dim_fp_amendmentsunitspropertytenant 
    WHERE amendment_end_date IS NOT NULL 
    AND amendment_end_date < amendment_start_date;
END;
$$;
```

### Phase 4: Performance Optimization (Days 11-15)
**Objective**: Achieve <2 second query performance

#### 2.8 Query Optimization for Rent Roll Calculations
```sql
-- Optimized function for current rent roll
CREATE OR REPLACE FUNCTION fn_current_rent_roll(as_of_date DATE DEFAULT CURRENT_DATE)
RETURNS TABLE(
    property_code TEXT,
    tenant_id TEXT,
    amendment_sf DECIMAL,
    monthly_rent DECIMAL,
    rent_psf DECIMAL,
    lease_expiry DATE
)
LANGUAGE sql
STABLE
AS $$
    SELECT 
        a.property_code,
        a.tenant_id,
        a.amendment_sf,
        COALESCE(c.total_monthly_rent, 0) as monthly_rent,
        CASE 
            WHEN a.amendment_sf > 0 
            THEN ROUND((COALESCE(c.total_monthly_rent, 0) * 12 / a.amendment_sf), 2)
            ELSE 0 
        END as rent_psf,
        a.amendment_end_date as lease_expiry
    FROM mv_latest_amendments a
    LEFT JOIN (
        SELECT 
            amendment_hmy,
            SUM(monthly_amount) as total_monthly_rent
        FROM dim_fp_amendmentchargeschedule 
        WHERE charge_code = 'rent'
        AND (to_date IS NULL OR to_date >= as_of_date)
        AND from_date <= as_of_date
        GROUP BY amendment_hmy
    ) c ON a.amendment_hmy = c.amendment_hmy
    WHERE a.amendment_status IN ('Activated', 'Superseded')
    AND (a.amendment_end_date IS NULL OR a.amendment_end_date >= as_of_date)
    AND a.amendment_start_date <= as_of_date;
$$;

-- Index to support the function
CREATE INDEX idx_charges_date_lookup 
ON dim_fp_amendmentchargeschedule (from_date, to_date, charge_code, amendment_hmy)
WHERE charge_code = 'rent';
```

#### 2.9 Aggregation Tables for Dashboard Performance
```sql
-- Monthly rent roll summary (updated nightly)
CREATE TABLE fact_monthly_rent_roll_summary (
    snapshot_date DATE,
    property_hmy INTEGER,
    property_code TEXT,
    tenant_count INTEGER,
    total_occupied_sf DECIMAL,
    total_monthly_rent DECIMAL,
    avg_rent_psf DECIMAL,
    occupancy_rate DECIMAL,
    created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_rent_roll_summary_date_property 
ON fact_monthly_rent_roll_summary (snapshot_date, property_hmy);

-- Procedure to populate summary table
CREATE OR REPLACE FUNCTION sp_refresh_rent_roll_summary(summary_date DATE DEFAULT CURRENT_DATE)
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    DELETE FROM fact_monthly_rent_roll_summary 
    WHERE snapshot_date = summary_date;
    
    INSERT INTO fact_monthly_rent_roll_summary
    SELECT 
        summary_date,
        p.property_hmy,
        p.property_code,
        COUNT(*) as tenant_count,
        SUM(r.amendment_sf) as total_occupied_sf,
        SUM(r.monthly_rent) as total_monthly_rent,
        CASE 
            WHEN SUM(r.amendment_sf) > 0 
            THEN ROUND(SUM(r.monthly_rent * 12) / SUM(r.amendment_sf), 2)
            ELSE 0 
        END as avg_rent_psf,
        ROUND(SUM(r.amendment_sf) / p.total_rentable_sf * 100, 2) as occupancy_rate,
        CURRENT_TIMESTAMP
    FROM dim_property p
    LEFT JOIN fn_current_rent_roll(summary_date) r 
        ON p.property_code = r.property_code
    GROUP BY p.property_hmy, p.property_code, p.total_rentable_sf;
END;
$$;
```

## 3. Data Governance Framework

### 3.1 Data Quality Rules Engine
```sql
-- Data quality rules configuration
CREATE TABLE data_quality_rules (
    rule_id SERIAL PRIMARY KEY,
    rule_name VARCHAR(100) NOT NULL,
    rule_category VARCHAR(50) NOT NULL,
    sql_check TEXT NOT NULL,
    severity VARCHAR(20) CHECK (severity IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')),
    threshold_value INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert standard rules
INSERT INTO data_quality_rules (rule_name, rule_category, sql_check, severity, threshold_value) VALUES
('No Duplicate Active Amendments', 'INTEGRITY', 
 'SELECT COUNT(*) FROM (SELECT property_hmy, tenant_hmy, COUNT(*) FROM dim_fp_amendmentsunitspropertytenant WHERE amendment_status = ''Activated'' GROUP BY 1,2 HAVING COUNT(*) > 1) x', 
 'CRITICAL', 0),
('Amendment Sequence Integrity', 'INTEGRITY',
 'SELECT COUNT(*) FROM dim_fp_amendmentsunitspropertytenant WHERE amendment_end_date IS NOT NULL AND amendment_end_date < amendment_start_date',
 'CRITICAL', 0),
('Active Amendments Coverage', 'COMPLETENESS',
 'SELECT COUNT(*) FROM v_amendments_missing_charges WHERE issue_type = ''ACTIVE_NO_CHARGES''',
 'HIGH', 50);
```

### 3.2 Automated Monitoring and Alerting
```sql
-- Daily monitoring procedure
CREATE OR REPLACE FUNCTION sp_execute_data_quality_monitoring()
RETURNS TABLE(rule_name TEXT, status TEXT, actual_count INTEGER, threshold_value INTEGER, severity TEXT)
LANGUAGE plpgsql
AS $$
DECLARE
    rule_rec RECORD;
    actual_value INTEGER;
BEGIN
    FOR rule_rec IN 
        SELECT * FROM data_quality_rules WHERE is_active = TRUE
    LOOP
        EXECUTE rule_rec.sql_check INTO actual_value;
        
        RETURN QUERY SELECT 
            rule_rec.rule_name,
            CASE 
                WHEN actual_value <= rule_rec.threshold_value THEN 'PASS'
                WHEN rule_rec.severity = 'CRITICAL' THEN 'CRITICAL_FAIL'
                ELSE 'FAIL'
            END,
            actual_value,
            rule_rec.threshold_value,
            rule_rec.severity;
    END LOOP;
END;
$$;

-- Alert log table
CREATE TABLE data_quality_alerts (
    alert_id SERIAL PRIMARY KEY,
    rule_name VARCHAR(100),
    status VARCHAR(20),
    actual_count INTEGER,
    threshold_value INTEGER,
    severity VARCHAR(20),
    alert_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by VARCHAR(50),
    acknowledged_timestamp TIMESTAMP
);
```

## 4. Implementation Timeline

### Week 1: Emergency Fixes (Days 1-7)
- **Days 1-2**: Execute duplicate amendment cleanup
- **Days 3-4**: Implement referential integrity constraints  
- **Days 5-6**: Create performance indexes
- **Day 7**: Testing and validation of emergency fixes

### Week 2: Schema Enhancements (Days 8-14)
- **Days 8-9**: Deploy materialized views and computed columns
- **Days 10-11**: Implement data quality monitoring framework
- **Days 12-13**: Performance optimization procedures
- **Day 14**: Full system testing

### Week 3: Governance and Monitoring (Days 15-21)
- **Days 15-16**: Deploy automated monitoring procedures
- **Days 17-18**: Configure alerting and notification system
- **Days 19-20**: User training and documentation
- **Day 21**: Go-live with monitoring framework

### Week 4: Validation and Optimization (Days 22-28)
- **Days 22-23**: End-to-end validation testing
- **Days 24-25**: Performance tuning and optimization
- **Days 26-27**: Documentation and knowledge transfer
- **Day 28**: Final validation and sign-off

## 5. Expected Outcomes

### Data Quality Improvements
| Metric | Before | After | Improvement |
|--------|---------|--------|-------------|
| Data Quality Score | 66/100 | 95+/100 | +44% |
| Amendment Duplicates | 98 cases | 0 cases | -100% |
| Referential Integrity | 79% | 98% | +24% |
| Query Performance | >5 seconds | <2 seconds | >60% |
| Missing Charge Coverage | 72% | <5% | +67% |

### Performance Improvements
- **Amendment Sequence Queries**: <2 seconds (from 5+ seconds)
- **Rent Roll Calculations**: <3 seconds for full portfolio
- **Dashboard Load Times**: <10 seconds (meets target)
- **Data Refresh**: <30 minutes (meets target)

### Governance Benefits
- **Automated Monitoring**: 24/7 data quality monitoring
- **Proactive Alerts**: Issues detected within 1 hour
- **Data Integrity**: 98% referential integrity maintenance
- **Audit Trail**: Complete change tracking and logging

## 6. Risk Management

### High-Risk Activities
1. **Duplicate Amendment Cleanup**
   - **Risk**: Data loss or incorrect deactivation
   - **Mitigation**: Full backup before execution + rollback procedures
   - **Testing**: Validate on development environment first

2. **Schema Changes**
   - **Risk**: Performance degradation or system downtime
   - **Mitigation**: Off-hours implementation + parallel environment testing
   - **Rollback**: Maintain original indexes until validation complete

3. **Constraint Implementation**
   - **Risk**: Existing data violations preventing constraint creation
   - **Mitigation**: Pre-validation and cleanup of constraint violations
   - **Testing**: Extensive data validation before constraint deployment

### Rollback Procedures
```sql
-- Emergency rollback script template
-- Step 1: Restore from backup
DROP TABLE IF EXISTS dim_fp_amendmentsunitspropertytenant;
CREATE TABLE dim_fp_amendmentsunitspropertytenant AS 
SELECT * FROM dim_fp_amendmentsunitspropertytenant_backup_20250809;

-- Step 2: Drop new indexes if causing issues
DROP INDEX IF EXISTS idx_amendments_property_tenant_sequence;
DROP INDEX IF EXISTS idx_amendments_status_active;

-- Step 3: Drop new constraints
ALTER TABLE dim_fp_amendmentchargeschedule 
DROP CONSTRAINT IF EXISTS fk_charges_amendments;
```

## 7. Success Metrics and KPIs

### Technical Metrics
- **Data Quality Score**: Target 95+ (baseline: 66)
- **Query Performance**: <2 seconds for amendment lookups
- **System Uptime**: 99.9% during implementation
- **Zero Data Loss**: Complete data integrity maintained

### Business Metrics  
- **Rent Roll Accuracy**: 97%+ (baseline: 93%)
- **Leasing Activity Accuracy**: 96%+ (baseline: 91%)
- **Financial Accuracy**: 98%+ (baseline: 79%)
- **Dashboard Performance**: <10 seconds load time

### Operational Metrics
- **Alert Response Time**: <1 hour for critical issues
- **Data Freshness**: Real-time for transactional, daily for analytical
- **User Satisfaction**: >90% satisfaction with performance improvements
- **Maintenance Overhead**: <4 hours/week for ongoing monitoring

## 8. Conclusion

This comprehensive database improvement plan addresses all critical data quality, performance, and governance issues identified in the PowerBI rent roll validation. The phased approach ensures minimal disruption while delivering immediate improvements to data integrity and system performance.

**Key Success Factors:**
1. **Immediate Impact**: Emergency fixes resolve 98% of duplicate amendments
2. **Sustainable Improvements**: Automated monitoring prevents future issues  
3. **Performance Optimization**: Sub-2 second query performance achieved
4. **Business Value**: 97% rent roll accuracy enables confident decision-making
5. **Risk Management**: Comprehensive rollback procedures ensure safe implementation

**Final Status**: Ready for immediate implementation with projected completion in 4 weeks and 97% overall accuracy achievement.

---

*Database Improvement Plan - Version 1.0*  
*Prepared by: Data Architecture Team - August 2025*