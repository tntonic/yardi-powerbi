# Leasing Activity Dashboard Template

## Overview
This template provides detailed specifications for creating a comprehensive Leasing Activity Dashboard in Power BI that replicates and enhances the native Yardi Leasing Activity Report functionality.

## Dashboard Structure (4 Pages)

### Page 1: Executive Summary
**Purpose**: High-level overview of leasing activity for executives and property managers

#### Layout Specifications

**Top Row - Key Metrics Cards (4 cards)**
```
┌─────────────┬─────────────┬─────────────┬─────────────┐
│ Total SF    │ New Leases  │ Renewals    │ Terminations│
│ [Metric]    │ [Count/SF]  │ [Count/SF]  │ [Count/SF]  │
│ [Trend ↑↓]  │ [Trend ↑↓]  │ [Trend ↑↓]  │ [Trend ↑↓]  │
└─────────────┴─────────────┴─────────────┴─────────────┘
```

**Middle Row - Activity Gauge & Net Activity**
```
┌─────────────────────────┬───────────────────────────────┐
│   Retention Rate %      │     Net Leasing Activity      │
│      [Gauge]            │        [Card + Trend]         │
│   Target: 75%+          │         [Graph]               │
└─────────────────────────┴───────────────────────────────┘
```

**Bottom Row - Activity Summary**
```
┌─────────────────────────────────────────────────────────┐
│            Leasing Activity Summary                     │
│  "New: 32 (1.0M SF) | Renewals: 56 (1.4M SF) |        │
│   Terms: 19 (0.5M SF) | Net: +1.9M SF"                 │
└─────────────────────────────────────────────────────────┘
```

#### Visual Specifications

**Card Visuals Configuration:**
- **Font**: Segoe UI, Bold, 24pt for numbers
- **Colors**: Green for positive metrics, Red for negative, Blue for neutral
- **Conditional Formatting**: 
  - Net Activity: Green if >0, Red if <0
  - Retention Rate: Green if >75%, Yellow 50-75%, Red <50%

**Gauge Visual (Retention Rate):**
- **Range**: 0-100%
- **Target Line**: 75%
- **Colors**: Red (0-50%), Yellow (50-75%), Green (75-100%)

### Page 2: Activity Details
**Purpose**: Detailed breakdown of leasing activity by property, unit type, and trends

#### Layout Specifications

**Top Section - Filters**
```
┌─────────────┬─────────────┬─────────────┬─────────────┐
│ Date Range  │ Property    │ Unit Type   │ Market      │
│ [Slicer]    │ [Slicer]    │ [Slicer]    │ [Slicer]    │
└─────────────┴─────────────┴─────────────┴─────────────┘
```

**Middle Section - Activity Table**
```
┌─────────────────────────────────────────────────────────┐
│              Activity by Property                       │
│ Property | New | Renewals | Terms | Net SF | Health    │
│ Prop A   |  5  |    12    |   3   | +125K  | Good      │
│ Prop B   |  8  |    15    |   2   | +180K  | Excellent │
└─────────────────────────────────────────────────────────┘
```

**Bottom Section - Trend Analysis**
```
┌────────────────────────┬────────────────────────────────┐
│   Monthly Activity     │      Activity by Unit Type     │
│      [Line Chart]      │       [Stacked Column]         │
└────────────────────────┴────────────────────────────────┘
```

#### Table Configuration

**Activity by Property Table:**
- **Columns**: Property Name, New Leases Count, Renewals Count, Terminations Count, Net SF, Health Status
- **Sorting**: By Net SF (descending)
- **Conditional Formatting**: 
  - Health column: Color coding based on activity health measure
  - Net SF: Data bars with green/red coloring
- **Totals**: Show totals row at bottom

### Page 3: Financial Analysis
**Purpose**: Rent analysis, financial metrics, and lease economics

#### Layout Specifications

**Top Row - Rent Metrics**
```
┌─────────────┬─────────────┬─────────────┬─────────────┐
│ Avg Rent    │ Rent Change │ Market Rent │ Rent Gap    │
│ New Leases  │ Renewals %  │ Comparison  │ Analysis    │
│ [Card]      │ [Card]      │ [Card]      │ [Card]      │
└─────────────┴─────────────┴─────────────┴─────────────┘
```

**Middle Section - Rent Analysis**
```
┌────────────────────────┬────────────────────────────────┐
│    Rent vs Size        │      Rent Trend Analysis       │
│   [Scatter Plot]       │       [Line Chart]             │
└────────────────────────┴────────────────────────────────┘
```

**Bottom Section - Top Transactions**
```
┌─────────────────────────────────────────────────────────┐
│                 Largest Lease Transactions              │
│ Property | Tenant | Size | Rent PSF | Term | Type      │
└─────────────────────────────────────────────────────────┘
```

#### Chart Specifications

**Scatter Plot (Rent vs Size):**
- **X-axis**: Amendment SF
- **Y-axis**: Rent PSF
- **Color**: By lease type (New/Renewal)
- **Size**: By lease term length
- **Tooltip**: Property, Tenant, Details

**Line Chart (Rent Trends):**
- **X-axis**: Month/Quarter
- **Y-axis**: Average Rent PSF
- **Series**: New Leases, Renewals, Market Rate
- **Trend Lines**: Show linear trend

### Page 4: Termination Analysis
**Purpose**: Analysis of lease terminations, move-out reasons, and retention strategies

#### Layout Specifications

**Top Row - Termination Overview**
```
┌─────────────┬─────────────┬─────────────┬─────────────┐
│ Total Terms │ Voluntary % │ Top Reason  │ Avg Notice  │
│ [Card]      │ [Card]      │ [Card]      │ [Card]      │
└─────────────┴─────────────┴─────────────┴─────────────┘
```

**Middle Section - Reason Analysis**
```
┌────────────────────────┬────────────────────────────────┐
│  Termination Reasons   │    Terms by Industry/Size      │
│     [Pie Chart]        │     [TreeMap or Bars]          │
└────────────────────────┴────────────────────────────────┘
```

**Bottom Section - Detailed Terminations**
```
┌─────────────────────────────────────────────────────────┐
│              Major Terminations (>10K SF)               │
│ Property | Tenant | Size | End Date | Reason | Impact  │
└─────────────────────────────────────────────────────────┘
```

## Global Elements

### Filters and Slicers

**Date Range Slicer:**
- **Type**: Between slicer with calendar dropdown
- **Default**: Current quarter
- **Quick Selections**: MTD, QTD, YTD, Last Quarter, Last Year

**Property Multi-Select:**
- **Type**: Dropdown with search
- **Default**: All properties selected
- **Hierarchy**: Market → Property for large portfolios

**Unit Type Slicer:**
- **Type**: Checkbox list
- **Options**: Industrial, Office, Retail, Mixed-Use, Other
- **Default**: All selected

### Navigation

**Page Navigation Bar:**
```
┌─────────────┬─────────────┬─────────────┬─────────────┐
│ Executive   │ Activity    │ Financial   │ Termination │
│ Summary     │ Details     │ Analysis    │ Analysis    │
└─────────────┴─────────────┴─────────────┴─────────────┘
```

**Bookmarks for Quick Views:**
- **MTD View**: Month-to-date activity
- **QTD View**: Quarter-to-date activity  
- **YTD View**: Year-to-date activity
- **Comparison View**: Prior period comparison

### Drill-Through Configuration

**Lease Detail Drill-Through Page:**
- **Triggered from**: Any lease count or SF measure
- **Filters**: Property, Date Range, Lease Type
- **Content**: 
  - Detailed lease list table
  - Individual lease metrics
  - Tenant information
  - Rent schedule details

## Color Scheme and Formatting

### Corporate Color Palette
```
Primary Blue:    #1F4E79 (Headers, Navigation)
Secondary Blue:  #5B9BD5 (Charts, Accents)
Success Green:   #70AD47 (Positive metrics)
Warning Yellow:  #FFC000 (Neutral/Warning)
Alert Red:       #C5504B (Negative metrics)
Light Gray:      #F2F2F2 (Backgrounds)
Dark Gray:       #404040 (Text)
```

### Typography Standards
- **Headers**: Segoe UI, Bold, 14-16pt
- **Metrics**: Segoe UI, Bold, 18-24pt
- **Body Text**: Segoe UI, Regular, 10-12pt
- **Table Headers**: Segoe UI, Semibold, 11pt

### Chart Styling
- **Background**: White or light gray
- **Grid Lines**: Light gray, minimal
- **Data Colors**: Use corporate palette consistently
- **Tooltips**: Include relevant context and formatting

## Interactive Features

### Cross-Filtering Behavior
- **Date Slicer**: Filters all visuals on all pages
- **Property Slicer**: Filters all relevant visuals
- **Chart Selections**: Cross-filter related visuals on same page
- **Drill-Down**: Click through from summary to detail level

### Conditional Formatting Rules

**Health Status Indicators:**
- **Excellent**: Green background, Net Activity >$1M, Retention >80%
- **Good**: Light green, Net Activity >$0, Retention >60%
- **Fair**: Yellow, Net Activity ≥$0, Retention >40%
- **Needs Attention**: Red, Net Activity <$0 or Retention <40%

**Trend Indicators:**
- **Up Arrow (↗)**: Green, increase from prior period
- **Down Arrow (↘)**: Red, decrease from prior period  
- **Flat Arrow (→)**: Gray, minimal change (<5%)

## Performance Optimization

### Data Model Optimization
- **Summarized Tables**: Create monthly/quarterly summary tables for historical data
- **Relationship Direction**: Single direction except for date table
- **Calculated Columns**: Minimize use, prefer measures
- **Indexing**: Ensure proper indexing on join columns

### Visual Optimization
- **Limit Visuals**: Maximum 8-10 visuals per page
- **Reduce Data Points**: Use TOP N filtering for large datasets
- **Aggregation**: Pre-aggregate at appropriate grain
- **Refresh Strategy**: Incremental refresh for large datasets

## Export and Sharing

### Excel Export Template
Create export that matches original Yardi format:

**Sheet 1: Executive Summary**
- Key metrics and totals
- Period-over-period comparisons
- Health indicators

**Sheet 2: New Leases Detail**
- Property, Unit, Tenant, Date, Size, Rent
- Industry classification
- Lease terms

**Sheet 3: Renewals Detail**
- Renewal transactions with rent changes
- Retention analysis
- Upcoming expirations

**Sheet 4: Terminations Detail**
- Terminated leases with reasons
- Notice periods
- Impact analysis

### Automated Distribution
- **Daily Refresh**: 6:00 AM daily
- **Email Distribution**: Automated email to leasing team
- **Alerts**: Notifications for significant changes
- **Mobile Access**: Optimized for mobile viewing

## Implementation Checklist

### Phase 1: Basic Dashboard
- [ ] Import DAX measures
- [ ] Create basic page layouts
- [ ] Configure slicers and filters
- [ ] Test data refresh
- [ ] Validate calculations

### Phase 2: Enhanced Features
- [ ] Add drill-through pages
- [ ] Implement bookmarks
- [ ] Configure conditional formatting
- [ ] Add trend analysis
- [ ] Create export functionality

### Phase 3: Production Deployment
- [ ] User acceptance testing
- [ ] Performance optimization
- [ ] Security configuration
- [ ] Training materials
- [ ] Go-live and monitoring

This template provides a comprehensive blueprint for implementing a production-ready Leasing Activity Dashboard that exceeds the capabilities of the native Yardi report while maintaining familiar formatting and structure.