# Dashboard Slicer Configuration Guide
## For Fund, Market, and Regional Property Filtering

### Overview
This guide provides step-by-step instructions for configuring interactive slicers in Power BI dashboards to enable property filtering by fund, market, and region.

## Prerequisites
- [ ] Power Query scripts have been executed
- [ ] Dimension tables created (dim_fund, dim_market_region)
- [ ] Relationships established in the data model
- [ ] DAX measures imported and validated

## Table of Contents
1. [Basic Slicer Setup](#basic-slicer-setup)
2. [Advanced Slicer Configurations](#advanced-slicer-configurations)
3. [Hierarchy Slicer Setup](#hierarchy-slicer-setup)
4. [Cross-Filter Configuration](#cross-filter-configuration)
5. [Visual Interactions](#visual-interactions)
6. [Performance Optimization](#performance-optimization)

---

## 1. Basic Slicer Setup

### Fund Slicer
1. **Add Slicer Visual**
   - Insert → Slicer from Visualizations pane
   - Drag `dim_fund[fund]` to Field well

2. **Configure Slicer Settings**
   ```
   Format → Slicer Settings
   - Selection: Single select or Multi-select
   - Show "Select all": On
   - Search: On (for large fund lists)
   ```

3. **Sort Order**
   - Use `dim_fund[display_order]` for sorting
   - Funds will appear: FRG funds first, then VALUE, OPP, Others

4. **Visual Formatting**
   ```
   Format → Visual
   - Orientation: Vertical list or Dropdown
   - Items → Font size: 10pt
   - Header → Text: "Select Fund"
   ```

### Market Slicer
1. **Add Market Slicer**
   - Insert → Slicer
   - Drag `dim_market_region[market]` to Field well

2. **Configure for Better UX**
   ```
   Format → Slicer Settings
   - Selection: Multi-select with CTRL
   - Search: On (essential for many markets)
   - Single select: Use "clear" icon
   ```

3. **Sort by Market Tier**
   - Sort by `dim_market_region[display_order]`
   - Tier 1 markets appear first

### Region Slicer
1. **Add Region Slicer**
   - Insert → Slicer
   - Drag `dim_market_region[region]` to Field well

2. **Configure as Filter**
   ```
   Format → Slicer Settings
   - Selection: Single select
   - Style: Tile or Button
   ```

---

## 2. Advanced Slicer Configurations

### Dropdown Slicer for Space Efficiency
```
Format → Slicer Settings → Style
- Select: Dropdown
- Benefits: Saves dashboard space
- Best for: Fund and Market slicers
```

### Tile/Button Slicer for Key Selections
```
Format → Slicer Settings → Style
- Select: Tile
- Responsive: On
- Columns: 3-5 based on space
- Best for: Region selection
```

### Hierarchical Slicer
```
Fields Configuration:
1. dim_market_region[region]
2. dim_market_region[market_tier]
3. dim_market_region[market]
4. dim_market_region[submarket]

Enable: Expand/Collapse icons
```

### Search-Enabled Slicer
```
Format → Slicer Settings
- Search: On
- Placeholder text: "Type to search..."
Essential for: Markets with 20+ options
```

---

## 3. Hierarchy Slicer Setup

### Create Geographic Hierarchy
1. **In Fields Pane**
   ```
   Right-click dim_market_region table
   → New hierarchy
   → Name: "Geographic Hierarchy"
   ```

2. **Add Levels**
   ```
   Drag fields in order:
   1. Region (Level 1)
   2. Market Tier (Level 2)
   3. Market (Level 3)
   4. Submarket (Level 4)
   ```

3. **Configure Hierarchy Slicer**
   ```
   Add Slicer → Drag entire hierarchy
   Format → Selection controls
   - Show Expand/Collapse: On
   - Stepped layout offset: 20px
   - Indent: On
   ```

### Drill-Down Configuration
```
Enable drill-down buttons:
- Drill down one level
- Drill up
- Expand next level
- Go to next level in hierarchy
```

---

## 4. Cross-Filter Configuration

### Set Up Slicer Interactions
1. **Select Fund Slicer**
2. **Format Tab → Edit Interactions**
3. **Configure for each visual:**

| Target Visual | Fund Impact | Market Impact | Region Impact |
|--------------|------------|---------------|--------------|
| Property Table | Filter | Filter | Filter |
| NOI Chart | Filter | Filter | Filter |
| Occupancy Gauge | Filter | Filter | Filter |
| Map Visual | Filter | Filter | Highlight |
| Summary Cards | Filter | Filter | Filter |

### Bi-Directional Filtering Setup
```
Modeling Tab → Manage Relationships
- dim_property ← → dim_fp_buildingcustomdata
- Cross filter: Both
- Apply security filter: Both directions
```

### Sync Slicers Across Pages
1. **View Tab → Sync slicers**
2. **Configure sync groups:**
   ```
   Fund Slicer:
   - Visible on: All pages
   - Sync to: All pages
   
   Market Slicer:
   - Visible on: Overview, Market Analysis
   - Sync to: All analytical pages
   
   Region Slicer:
   - Visible on: Overview, Regional
   - Sync to: Geographic pages
   ```

---

## 5. Visual Interactions

### Configure Slicer-to-Visual Relationships

#### For Summary Cards
```
Interaction: Filter
Purpose: Show filtered totals
Example: "Total Properties: 45" (filtered from 150)
```

#### For Charts and Graphs
```
Interaction: Filter or Highlight
- Filter: Shows only selected data
- Highlight: Shows selection in context
Recommendation: Use Filter for clarity
```

#### For Maps
```
Interaction: Highlight
Purpose: Shows selected properties prominently
Non-selected: Grayed out but visible
```

#### For Tables
```
Interaction: Filter
Purpose: Show only relevant rows
Add measure: [Filter Status] to show context
```

### Cascading Filters Setup
```
Region → Market → Property
1. Region selection filters available markets
2. Market selection filters available properties
3. Clear filters button resets cascade
```

---

## 6. Performance Optimization

### Optimize Slicer Performance

#### Use Dimension Tables
```
DO: Use dim_fund[fund] for slicing
DON'T: Use dim_fp_buildingcustomdata[fund]
Reason: Smaller dimension tables = faster filtering
```

#### Limit Visual Interactions
```
Format → Edit interactions
- Disable unnecessary cross-filtering
- Use "None" for unrelated visuals
```

#### Pre-filter Large Lists
```
For markets with 100+ options:
1. Add market tier pre-filter
2. Use search functionality
3. Consider dropdown style
```

### Add Clear Filters Button
```
Insert → Button → Reset
Action: Bookmark (reset all slicers)
Bookmark settings:
- Data: Selected
- Display: Not selected
- Current page: Selected
```

### Performance Monitoring
```
View → Performance Analyzer
1. Start recording
2. Interact with slicers
3. Identify slow visuals
4. Optimize or replace
```

---

## 7. Best Practices

### Slicer Placement
```
Recommended Layout:
┌─────────────────────────────┐
│ Fund ▼  Market ▼  Region ▼  │ (Top horizontal bar)
├─────────────────────────────┤
│                             │
│     Main Dashboard Area     │
│                             │
└─────────────────────────────┘

Alternative:
┌──────┬──────────────────────┐
│Fund  │                      │
│Market│   Main Dashboard     │ (Left sidebar)
│Region│                      │
└──────┴──────────────────────┘
```

### Visual Consistency
- Use consistent slicer styles across pages
- Maintain same position for global filters
- Use consistent colors for selection states

### User Experience
- Provide clear labels for each slicer
- Add tooltips explaining filter impact
- Include reset/clear buttons
- Show filter context in visuals

### Mobile Optimization
```
Mobile Layout:
- Convert to dropdown slicers
- Stack vertically
- Increase touch target size (44x44px min)
- Enable responsive design
```

---

## 8. Troubleshooting Common Issues

### Issue: Slicers Not Filtering Correctly
**Solution:**
1. Check relationships in Model view
2. Verify cross-filter direction
3. Ensure proper field selection
4. Check for duplicate values in dimension tables

### Issue: Slow Slicer Response
**Solution:**
1. Use dimension tables instead of fact tables
2. Reduce number of items shown
3. Disable auto-refresh during selection
4. Consider using bookmarks for common selections

### Issue: Blank Values in Slicers
**Solution:**
1. Filter out blanks in Power Query
2. Use DAX: `NOT(ISBLANK())`
3. Set slicer to hide items with no data

### Issue: Hierarchy Not Working
**Solution:**
1. Verify hierarchy levels are in correct order
2. Check for missing relationships
3. Ensure all levels have data
4. Test with simple hierarchy first

---

## 9. Advanced Features

### Dynamic Slicer Titles
```dax
Slicer Title = 
"Fund (" & COUNTROWS(VALUES(dim_fund[fund])) & " selected)"
```

### Conditional Formatting in Slicers
```
Format → Conditional formatting
- Data bars: Show relative size
- Background color: Highlight top performers
- Font color: Indicate status
```

### Slicer Groups
```
For related filters:
1. Select multiple slicers
2. Format → Slicer group
3. Benefits: Move/format together
```

### Custom Slicer Visuals
Consider marketplace visuals:
- ChicletSlicer (Microsoft)
- HierarchySlicer (xViz)
- SmartFilter Pro

---

## 10. Testing Checklist

### Pre-Deployment Testing
- [ ] All slicers load without errors
- [ ] Cross-filtering works as expected
- [ ] Performance is acceptable (<2 sec response)
- [ ] Mobile view displays correctly
- [ ] Sync across pages functions properly
- [ ] Clear/Reset buttons work
- [ ] Search functionality operates correctly
- [ ] Hierarchies expand/collapse properly
- [ ] No unexpected blank values appear
- [ ] Visual interactions are configured correctly

### User Acceptance Testing
- [ ] Users can find desired selections easily
- [ ] Filter context is clear
- [ ] Performance meets requirements
- [ ] Mobile experience is satisfactory
- [ ] Training materials are adequate

---

## Appendix: Sample Slicer DAX Patterns

### Show Only Active Properties
```dax
Active Properties Filter = 
CALCULATE(
    COUNTROWS(dim_property),
    dim_fp_buildingcustomdata[status] = "Acquired",
    ISBLANK(dim_fp_buildingcustomdata[disposition_date])
) > 0
```

### Dynamic Default Selection
```dax
Default Fund = 
IF(
    ISBLANK(SELECTEDVALUE(dim_fund[fund])),
    "FRG IX",  // Default fund
    SELECTEDVALUE(dim_fund[fund])
)
```

### Slicer Item Count
```dax
Slicer Item Count = 
VAR SelectedItems = COUNTROWS(VALUES(dim_fund[fund]))
VAR TotalItems = COUNTROWS(ALL(dim_fund[fund]))
RETURN
SelectedItems & " of " & TotalItems & " funds"
```

---

This configuration guide ensures optimal setup of Power BI slicers for fund, market, and regional filtering, providing users with intuitive and performant property analysis capabilities.