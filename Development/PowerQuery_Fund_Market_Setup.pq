// Power Query Script for Fund, Market, and Region Filtering Setup
// This script establishes relationships and creates dimension tables for property filtering

// ============================================
// PART 1: CLEAN AND PREPARE EXISTING TABLES
// ============================================

// Clean dim_fp_buildingcustomdata table
let
    Source_BuildingData = Csv.Document(File.Contents("Data/Yardi_Tables/dim_fp_buildingcustomdata.csv"),[Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.None]),
    PromotedHeaders = Table.PromoteHeaders(Source_BuildingData, [PromoteAllScalars=true]),
    
    // Clean fund and market columns
    CleanedData = Table.TransformColumns(PromotedHeaders, {
        {"fund", each Text.Trim(_), type text},
        {"market", each Text.Trim(_), type text},
        {"status", each Text.Trim(_), type text}
    }),
    
    // Replace empty strings with null
    ReplaceEmptyWithNull = Table.ReplaceValue(CleanedData, "", null, Replacer.ReplaceValue, {"fund", "market"}),
    
    // Keep original column names for now (with spaces)
    // Will rename after establishing relationships
    TypedData = Table.TransformColumnTypes(ReplaceEmptyWithNull, {
        {"hmy property", Int64.Type},
        {"fund", type text},
        {"market", type text},
        {"status", type text},
        {"acq. date", type date},
        {"disposition date", type date}
    })
in
    TypedData

// ============================================
// PART 2: CREATE DIM_FUND TABLE
// ============================================

let
    // Get unique funds from building custom data
    Source = dim_fp_buildingcustomdata,
    
    // Select only fund column and remove nulls
    FundColumn = Table.SelectColumns(Source, {"fund"}),
    FilteredFunds = Table.SelectRows(FundColumn, each [fund] <> null),
    
    // Get distinct funds
    DistinctFunds = Table.Distinct(FilteredFunds),
    
    // Add fund attributes
    AddedFundID = Table.AddIndexColumn(DistinctFunds, "fund_id", 1, 1, Int64.Type),
    
    // Parse fund information (e.g., "FRG IX" -> Fund Name: FRG, Vehicle: IX)
    ParsedFunds = Table.AddColumn(AddedFundID, "fund_family", each 
        let
            parts = Text.Split([fund], " ")
        in
            if List.Count(parts) > 0 then parts{0} else [fund]
    ),
    
    AddedVehicle = Table.AddColumn(ParsedFunds, "fund_vehicle", each 
        let
            parts = Text.Split([fund], " ")
        in
            if List.Count(parts) > 1 then Text.Combine(List.Skip(parts, 1), " ") else null
    ),
    
    // Add fund type classification
    AddedFundType = Table.AddColumn(AddedVehicle, "fund_type", each
        if Text.Contains([fund], "FRG", Comparer.OrdinalIgnoreCase) then "Core Real Estate"
        else if Text.Contains([fund], "OPP", Comparer.OrdinalIgnoreCase) then "Opportunistic"
        else if Text.Contains([fund], "VALUE", Comparer.OrdinalIgnoreCase) then "Value-Add"
        else "Other"
    ),
    
    // Add display order for sorting
    AddedDisplayOrder = Table.AddColumn(AddedFundType, "display_order", each
        if [fund_family] = "FRG" then 1
        else if [fund_family] = "VALUE" then 2
        else if [fund_family] = "OPP" then 3
        else 99
    ),
    
    // Reorder columns
    FinalFundTable = Table.ReorderColumns(AddedDisplayOrder, {
        "fund_id", "fund", "fund_family", "fund_vehicle", "fund_type", "display_order"
    })
in
    FinalFundTable

// ============================================
// PART 3: CREATE DIM_MARKET_REGION TABLE
// ============================================

let
    // Get unique markets from building custom data
    Source = dim_fp_buildingcustomdata,
    
    // Select market and city columns
    MarketColumns = Table.SelectColumns(Source, {"market", "city", "state"}),
    FilteredMarkets = Table.SelectRows(MarketColumns, each [market] <> null),
    
    // Get distinct combinations
    DistinctMarkets = Table.Distinct(FilteredMarkets),
    
    // Add market ID
    AddedMarketID = Table.AddIndexColumn(DistinctMarkets, "market_id", 1, 1, Int64.Type),
    
    // Define regions based on state
    AddedRegion = Table.AddColumn(AddedMarketID, "region", each
        let
            stateUpper = Text.Upper([state])
        in
            // Northeast
            if List.Contains({"NY", "NJ", "CT", "MA", "RI", "VT", "NH", "ME", "PA"}, stateUpper) then "Northeast"
            
            // Southeast
            else if List.Contains({"FL", "GA", "SC", "NC", "VA", "WV", "KY", "TN", "AL", "MS", "AR", "LA"}, stateUpper) then "Southeast"
            
            // Midwest
            else if List.Contains({"OH", "MI", "IN", "IL", "WI", "MN", "IA", "MO", "ND", "SD", "NE", "KS"}, stateUpper) then "Midwest"
            
            // Southwest
            else if List.Contains({"TX", "OK", "NM", "AZ"}, stateUpper) then "Southwest"
            
            // West
            else if List.Contains({"CA", "OR", "WA", "NV", "UT", "CO", "ID", "MT", "WY", "AK", "HI"}, stateUpper) then "West"
            
            else "Other"
    ),
    
    // Add submarket (initially same as market, can be refined later)
    AddedSubmarket = Table.AddColumn(AddedRegion, "submarket", each [market]),
    
    // Add metro area classifications
    AddedMetroArea = Table.AddColumn(AddedSubmarket, "metro_area", each
        let
            marketUpper = Text.Upper([market])
        in
            // Major metro areas
            if Text.Contains(marketUpper, "NEW YORK") or Text.Contains(marketUpper, "NYC") then "New York Metro"
            else if Text.Contains(marketUpper, "LOS ANGELES") or Text.Contains(marketUpper, "LA") then "Los Angeles Metro"
            else if Text.Contains(marketUpper, "CHICAGO") then "Chicago Metro"
            else if Text.Contains(marketUpper, "DALLAS") or Text.Contains(marketUpper, "FORT WORTH") then "Dallas-Fort Worth Metro"
            else if Text.Contains(marketUpper, "HOUSTON") then "Houston Metro"
            else if Text.Contains(marketUpper, "WASHINGTON") or Text.Contains(marketUpper, "DC") then "Washington DC Metro"
            else if Text.Contains(marketUpper, "MIAMI") or Text.Contains(marketUpper, "FORT LAUDERDALE") then "Miami Metro"
            else if Text.Contains(marketUpper, "PHILADELPHIA") then "Philadelphia Metro"
            else if Text.Contains(marketUpper, "ATLANTA") then "Atlanta Metro"
            else if Text.Contains(marketUpper, "PHOENIX") then "Phoenix Metro"
            else if Text.Contains(marketUpper, "BOSTON") then "Boston Metro"
            else if Text.Contains(marketUpper, "SAN FRANCISCO") or Text.Contains(marketUpper, "SF") then "San Francisco Metro"
            else if Text.Contains(marketUpper, "DETROIT") then "Detroit Metro"
            else if Text.Contains(marketUpper, "SEATTLE") then "Seattle Metro"
            else if Text.Contains(marketUpper, "MINNEAPOLIS") or Text.Contains(marketUpper, "ST PAUL") then "Minneapolis-St Paul Metro"
            else if Text.Contains(marketUpper, "SAN DIEGO") then "San Diego Metro"
            else if Text.Contains(marketUpper, "TAMPA") then "Tampa Metro"
            else if Text.Contains(marketUpper, "DENVER") then "Denver Metro"
            else if Text.Contains(marketUpper, "BALTIMORE") then "Baltimore Metro"
            else [market] & " Metro"
    ),
    
    // Add market tier classification
    AddedMarketTier = Table.AddColumn(AddedMetroArea, "market_tier", each
        let
            metroArea = [metro_area]
        in
            // Tier 1 markets
            if List.Contains({
                "New York Metro", "Los Angeles Metro", "Chicago Metro", 
                "Dallas-Fort Worth Metro", "Houston Metro", "Washington DC Metro"
            }, metroArea) then "Tier 1"
            
            // Tier 2 markets
            else if List.Contains({
                "Miami Metro", "Philadelphia Metro", "Atlanta Metro", "Phoenix Metro",
                "Boston Metro", "San Francisco Metro", "Detroit Metro", "Seattle Metro"
            }, metroArea) then "Tier 2"
            
            // Tier 3 markets
            else "Tier 3"
    ),
    
    // Add display order for sorting
    AddedDisplayOrder = Table.AddColumn(AddedMarketTier, "display_order", each
        if [market_tier] = "Tier 1" then 1
        else if [market_tier] = "Tier 2" then 2
        else 3
    ),
    
    // Reorder columns
    FinalMarketTable = Table.ReorderColumns(AddedDisplayOrder, {
        "market_id", "market", "submarket", "city", "state", "region", 
        "metro_area", "market_tier", "display_order"
    })
in
    FinalMarketTable

// ============================================
// PART 4: CREATE REGION HIERARCHY TABLE
// ============================================

let
    // Create a pure hierarchy table for region drilling
    Source = dim_market_region,
    
    // Get unique regions
    UniqueRegions = Table.Distinct(Table.SelectColumns(Source, {"region"})),
    AddedRegionID = Table.AddIndexColumn(UniqueRegions, "region_id", 1, 1, Int64.Type),
    
    // Create region display order
    AddedOrder = Table.AddColumn(AddedRegionID, "region_display_order", each
        if [region] = "Northeast" then 1
        else if [region] = "Southeast" then 2
        else if [region] = "Midwest" then 3
        else if [region] = "Southwest" then 4
        else if [region] = "West" then 5
        else 99
    ),
    
    FinalRegionTable = Table.Sort(AddedOrder, {{"region_display_order", Order.Ascending}})
in
    FinalRegionTable

// ============================================
// PART 5: ENHANCED PROPERTY TABLE WITH FUND/MARKET
// ============================================

let
    // Join property table with building custom data
    PropertySource = dim_property,
    BuildingDataSource = dim_fp_buildingcustomdata,
    
    // Perform left outer join on property_id = hmy_property
    JoinedData = Table.NestedJoin(
        PropertySource, {"property id"}, 
        BuildingDataSource, {"hmy property"}, 
        "BuildingData", 
        JoinKind.LeftOuter
    ),
    
    // Expand building data columns
    ExpandedData = Table.ExpandTableColumn(JoinedData, "BuildingData", {
        "fund", "market", "status", "acq. date", "disposition date",
        "year built", "% office", "land (acres)", "# parking spots"
    }, {
        "fund", "market", "property_status", "acquisition_date", "disposition_date",
        "year_built_extended", "percent_office", "land_acres", "parking_spots"
    }),
    
    // Add calculated columns
    AddedActiveFlag = Table.AddColumn(ExpandedData, "is_active_property", each
        if [property_status] = "Acquired" and [disposition_date] = null then true
        else false
    ),
    
    AddedHoldingPeriod = Table.AddColumn(AddedActiveFlag, "holding_period_months", each
        if [acquisition_date] <> null then
            if [disposition_date] <> null then
                Duration.Days([disposition_date] - [acquisition_date]) / 30.44
            else
                Duration.Days(DateTime.Date(DateTime.LocalNow()) - [acquisition_date]) / 30.44
        else null
    ),
    
    FinalPropertyTable = Table.TransformColumnTypes(AddedHoldingPeriod, {
        {"holding_period_months", type number}
    })
in
    FinalPropertyTable