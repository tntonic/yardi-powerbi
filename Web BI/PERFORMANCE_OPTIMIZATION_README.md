# Yardi Web BI Performance Optimization Guide

## Overview

This guide covers the comprehensive performance optimization system for the Yardi Web BI dashboard, designed to dramatically improve query performance and dashboard responsiveness through DuckDB-specific optimizations.

## 🚀 Quick Start

### 1. Run Complete Optimization
```bash
# Full optimization (recommended for first run)
python run_optimization.py --full

# Or directly
python database/optimize_performance.py
```

### 2. Get Performance Summary
```bash
python run_optimization.py --summary
```

### 3. Test Cache Performance
```bash
python run_optimization.py --cache-test
```

## 📊 What Gets Optimized

### 1. Column Statistics & Indexing
- **Critical columns analyzed**: Property HMY, Tenant HMY, Amendment Sequence, Account Codes
- **DuckDB ANALYZE statements**: Creates column statistics for query optimization
- **Sorted index tables**: Pre-sorted tables for faster lookups

### 2. Materialized Views
- **`mv_rent_roll_complete`**: Pre-computed rent roll with all metrics (credit scores, PSF, risk categories)
- **`mv_financial_summary_monthly`**: Pre-aggregated financial data by property/month
- **`mv_occupancy_metrics_complete`**: Pre-computed occupancy percentages and metrics
- **`mv_portfolio_health_components`**: Optimized portfolio health score components

### 3. Query Result Caching
- **In-memory cache**: 5-10 minute TTL for expensive queries
- **Automatic cache invalidation**: Time-based expiration
- **Cache hit statistics**: Monitor performance improvements

### 4. Portfolio Health Score Optimization
- **Problem**: Complex nested queries with multiple CTEs
- **Solution**: Pre-computed components in materialized views
- **Performance gain**: ~10-50x faster execution

## 🔧 Optimization Commands

### Full Optimization
```bash
python run_optimization.py --full
```
**What it does:**
- Creates column statistics for 20+ critical columns
- Builds 3 sorted index tables for fast lookups
- Creates 4 materialized views for expensive calculations
- Sets up query caching with TTL
- Optimizes portfolio health score view
- Runs performance analysis

### Materialized View Refresh
```bash
python run_optimization.py --refresh
```
**When to use:** After data updates or daily maintenance

### Performance Analysis
```bash
python run_optimization.py --analyze
```
**What it shows:**
- Table sizes and row counts
- View dependencies
- Cache performance metrics

### Custom Database Path
```bash
python run_optimization.py --full --db-path /path/to/custom.duckdb
```

## 📈 Expected Performance Improvements

| Component | Before | After | Improvement |
|-----------|--------|-------|-------------|
| Portfolio Health Score | 5-30s | 0.1-0.5s | 10-60x faster |
| Rent Roll Queries | 2-10s | 0.2-1s | 5-20x faster |
| Financial Summary | 1-5s | 0.1-0.5s | 5-25x faster |
| Dashboard Load Time | 15-60s | 3-10s | 3-10x faster |
| Query Cache Hits | N/A | 0.01-0.1s | 50-100x faster |

## 🏗️ Technical Architecture

### DuckDB-Specific Optimizations
1. **Column Statistics**: Uses `ANALYZE table(column)` instead of traditional indexes
2. **Sorted Tables**: Pre-sorted tables act as covering indexes
3. **Parallel Processing**: Configured for 4-thread parallel queries
4. **Memory Optimization**: 4GB memory limit with external processing disabled

### Materialized View Strategy
- **Amendment-based logic**: Latest sequence per property/tenant
- **Financial aggregations**: Pre-computed revenue, expenses, NOI by period
- **Credit risk integration**: Pre-joined credit scores and risk categories
- **Time-based partitioning**: Recent data prioritized for performance

### Caching Strategy
- **Application-level caching**: Python-based in-memory cache
- **TTL-based expiration**: 5-10 minutes for different query types
- **Thread-safe operations**: Concurrent cache access handling
- **Cache statistics**: Hit rate monitoring and reporting

## 🛠️ Maintenance

### Daily Maintenance
```bash
# Refresh materialized views after data updates
python run_optimization.py --refresh
```

### Weekly Maintenance
```bash
# Full re-optimization
python run_optimization.py --full
```

### Monitoring
```bash
# Check performance metrics
python run_optimization.py --summary

# View detailed analysis
python run_optimization.py --analyze
```

## 🚨 Troubleshooting

### Common Issues

**1. "Database file not found"**
```bash
# Initialize database first
python database/init_db.py
```

**2. "Out of memory" during optimization**
- Reduce DuckDB memory limit in `optimize_performance.py`
- Process tables in smaller batches

**3. "View dependency errors"**
```bash
# Re-run base view creation
python database/init_db.py
```

**4. Slow materialized view creation**
- Check available system memory
- Verify source tables have data
- Review query execution plan

### Performance Monitoring
```python
# Check cache statistics
from database.optimize_performance import YardiPerformanceOptimizer
optimizer = YardiPerformanceOptimizer()
optimizer.connect()
stats = optimizer.cache.get_stats()
print(f"Cache entries: {stats['active_entries']}")
```

## 📋 Configuration Options

### Memory Settings (in optimize_performance.py)
```python
# Adjust based on available system memory
"SET memory_limit='4GB'",
"SET max_memory='4GB'",
"SET threads TO 4",
```

### Cache Settings
```python
# Default cache TTL (seconds)
self.cache = QueryCache(default_ttl=300)  # 5 minutes

# Per-query cache TTL
@cached_query(self.cache, ttl=600)  # 10 minutes
```

### Materialized View Refresh Frequency
- **Real-time dashboards**: Every 5-15 minutes
- **Executive reporting**: Every hour
- **Historical analysis**: Daily

## 🔍 Performance Metrics

The optimization system tracks:
- **Execution times**: For each materialized view creation
- **Row counts**: For all optimized tables and views
- **Cache statistics**: Hit rates and active entries
- **Memory usage**: DuckDB memory consumption
- **Query performance**: Before/after execution times

### Metrics File
Performance metrics are saved to: `database/performance_metrics.json`

```json
{
  "mv_rent_roll_complete": {
    "row_count": 1250,
    "creation_time": 2.45,
    "created_at": "2025-01-15T10:30:00"
  },
  "analysis": {
    "table_sizes": {...},
    "cache_performance": {...}
  }
}
```

## 🎯 Best Practices

### 1. Initial Setup
- Run full optimization after database initialization
- Test with a subset of data first
- Monitor system resources during optimization

### 2. Ongoing Maintenance
- Refresh materialized views after data loads
- Clear cache when schema changes occur
- Monitor query performance regularly

### 3. Dashboard Integration
- Use materialized views for dashboard queries
- Implement caching in dashboard components
- Add performance monitoring to dashboards

### 4. Scaling Considerations
- Adjust memory limits based on data volume
- Consider partitioning large tables by date
- Monitor disk space for materialized views

## 🔗 Integration with Dashboard Components

The optimized views can be used directly in dashboard components:

```python
# In dashboard components (e.g., executive_summary.py)
query = """
SELECT 
    portfolio_health_score,
    health_category,
    avg_occupancy,
    avg_noi_margin
FROM v_portfolio_health_score_optimized
"""

# Use cached query functions
summary = optimizer.get_portfolio_summary()
```

## 📚 Additional Resources

- **DuckDB Documentation**: [duckdb.org/docs](https://duckdb.org/docs/)
- **Performance Tuning**: Check `database/performance_metrics.json` for detailed timing
- **Query Analysis**: Use DuckDB's `EXPLAIN ANALYZE` for query optimization
- **Memory Profiling**: Monitor system resources during heavy queries

---

**Need Help?**
- Check logs in `optimization.log`
- Review performance metrics in `database/performance_metrics.json` 
- Run `python run_optimization.py --help` for command options