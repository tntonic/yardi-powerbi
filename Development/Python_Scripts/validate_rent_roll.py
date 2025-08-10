#!/usr/bin/env python3
"""
Validate Generated Rent Roll Against Yardi Export
Compare the generated rent roll with the cleaned Yardi export
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime

# Define paths
base_path = "/Users/michaeltang/Documents/GitHub/BI/PBI v1.7"

# Files to compare
generated_file = os.path.join(base_path, "Generated_Rent_Rolls/fund2_rent_roll_generated_063025.csv")
yardi_cleaned_file = os.path.join(base_path, "cleaned_rent_roll_jun25.csv")

def load_data():
    """Load both rent roll files"""
    print("\nLOADING DATA FILES...")
    
    # Load generated rent roll
    generated_df = pd.read_csv(generated_file)
    print(f"  Generated rent roll: {len(generated_df)} rows")
    
    # Load Yardi cleaned rent roll
    yardi_df = pd.read_csv(yardi_cleaned_file)
    
    # Filter Yardi data for Fund 2 only
    yardi_fund2_df = yardi_df[yardi_df['fund'] == 'FUND 2'].copy()
    print(f"  Yardi rent roll (Fund 2): {len(yardi_fund2_df)} rows")
    
    return generated_df, yardi_fund2_df

def standardize_columns(df, source_name):
    """Standardize column names for comparison"""
    
    # Create mapping for common variations
    column_mapping = {
        # Generated columns -> Standard names
        'property code': 'property_code',
        'property name': 'property_name',
        'tenant id': 'tenant_code',
        'tenant hmy': 'tenant_hmy',
        'amendment sf': 'square_feet',
        'current_monthly_rent': 'monthly_rent',
        'current_annual_rent': 'annual_rent',
        'amendment_start_dt': 'lease_start',
        'amendment_end_dt': 'lease_end',
        'units under amendment': 'suite',
        
        # Yardi columns -> Standard names
        'property_code': 'property_code',
        'property': 'property_name',
        'suite': 'suite',
        'lease_start': 'lease_start',
        'lease_end': 'lease_end',
        'monthly': 'monthly_rent_str',
        'annual': 'annual_rent_str',
        'market': 'square_feet'  # This might be the SF field
    }
    
    # Apply mapping
    df_standardized = df.rename(columns=column_mapping)
    
    # Clean up monetary values in Yardi data
    if source_name == 'Yardi':
        # Convert monthly and annual rent strings to numeric
        if 'monthly_rent_str' in df_standardized.columns:
            df_standardized['monthly_rent'] = pd.to_numeric(
                df_standardized['monthly_rent_str'].astype(str).str.replace(',', '').str.replace('$', ''),
                errors='coerce'
            )
        if 'annual_rent_str' in df_standardized.columns:
            df_standardized['annual_rent'] = pd.to_numeric(
                df_standardized['annual_rent_str'].astype(str).str.replace(',', '').str.replace('$', ''),
                errors='coerce'
            )
    
    return df_standardized

def compare_totals(generated_df, yardi_df):
    """Compare total metrics between the two datasets"""
    print("\n" + "=" * 80)
    print("TOTAL METRICS COMPARISON")
    print("=" * 80)
    
    # Standardize columns
    gen_std = standardize_columns(generated_df, 'Generated')
    yardi_std = standardize_columns(yardi_df, 'Yardi')
    
    # Calculate totals
    metrics = {}
    
    # Record counts
    metrics['Record Count'] = {
        'Generated': len(gen_std),
        'Yardi': len(yardi_std),
        'Difference': len(gen_std) - len(yardi_std),
        'Match %': (min(len(gen_std), len(yardi_std)) / max(len(gen_std), len(yardi_std))) * 100
    }
    
    # Monthly rent totals
    if 'monthly_rent' in gen_std.columns and 'monthly_rent' in yardi_std.columns:
        gen_monthly = gen_std['monthly_rent'].sum()
        yardi_monthly = yardi_std['monthly_rent'].sum()
        metrics['Monthly Rent Total'] = {
            'Generated': gen_monthly,
            'Yardi': yardi_monthly,
            'Difference': gen_monthly - yardi_monthly,
            'Match %': (min(gen_monthly, yardi_monthly) / max(gen_monthly, yardi_monthly)) * 100 if yardi_monthly > 0 else 0
        }
    
    # Annual rent totals
    if 'annual_rent' in gen_std.columns and 'annual_rent' in yardi_std.columns:
        gen_annual = gen_std['annual_rent'].sum()
        yardi_annual = yardi_std['annual_rent'].sum()
        metrics['Annual Rent Total'] = {
            'Generated': gen_annual,
            'Yardi': yardi_annual,
            'Difference': gen_annual - yardi_annual,
            'Match %': (min(gen_annual, yardi_annual) / max(gen_annual, yardi_annual)) * 100 if yardi_annual > 0 else 0
        }
    
    # Square footage totals
    if 'square_feet' in gen_std.columns and 'square_feet' in yardi_std.columns:
        gen_sf = gen_std['square_feet'].sum()
        yardi_sf = yardi_std['square_feet'].sum()
        metrics['Square Feet Total'] = {
            'Generated': gen_sf,
            'Yardi': yardi_sf,
            'Difference': gen_sf - yardi_sf,
            'Match %': (min(gen_sf, yardi_sf) / max(gen_sf, yardi_sf)) * 100 if yardi_sf > 0 else 0
        }
    
    # Print comparison table
    for metric_name, values in metrics.items():
        print(f"\n{metric_name}:")
        if metric_name == 'Record Count':
            print(f"  Generated: {values['Generated']:,}")
            print(f"  Yardi:     {values['Yardi']:,}")
            print(f"  Difference: {values['Difference']:,}")
        elif 'Rent' in metric_name:
            print(f"  Generated: ${values['Generated']:,.2f}")
            print(f"  Yardi:     ${values['Yardi']:,.2f}")
            print(f"  Difference: ${values['Difference']:,.2f}")
        else:
            print(f"  Generated: {values['Generated']:,.0f}")
            print(f"  Yardi:     {values['Yardi']:,.0f}")
            print(f"  Difference: {values['Difference']:,.0f}")
        print(f"  Accuracy:  {values['Match %']:.1f}%")
    
    return metrics

def compare_properties(generated_df, yardi_df):
    """Compare at property level"""
    print("\n" + "=" * 80)
    print("PROPERTY-LEVEL COMPARISON")
    print("=" * 80)
    
    # Standardize columns
    gen_std = standardize_columns(generated_df, 'Generated')
    yardi_std = standardize_columns(yardi_df, 'Yardi')
    
    # Get unique properties
    gen_properties = set(gen_std['property_code'].unique())
    yardi_properties = set(yardi_std['property_code'].unique())
    
    print(f"\nProperty Coverage:")
    print(f"  Properties in Generated: {len(gen_properties)}")
    print(f"  Properties in Yardi:     {len(yardi_properties)}")
    print(f"  Common Properties:       {len(gen_properties & yardi_properties)}")
    print(f"  Only in Generated:       {len(gen_properties - yardi_properties)}")
    print(f"  Only in Yardi:          {len(yardi_properties - gen_properties)}")
    
    # Compare totals by property for common properties
    common_properties = gen_properties & yardi_properties
    
    if common_properties:
        print(f"\nTop 10 Properties by Rent Difference:")
        
        property_comparison = []
        for prop_code in common_properties:
            gen_prop = gen_std[gen_std['property_code'] == prop_code]
            yardi_prop = yardi_std[yardi_std['property_code'] == prop_code]
            
            gen_monthly = gen_prop['monthly_rent'].sum() if 'monthly_rent' in gen_prop.columns else 0
            yardi_monthly = yardi_prop['monthly_rent'].sum() if 'monthly_rent' in yardi_prop.columns else 0
            
            property_comparison.append({
                'property_code': prop_code,
                'gen_monthly': gen_monthly,
                'yardi_monthly': yardi_monthly,
                'difference': gen_monthly - yardi_monthly,
                'pct_diff': ((gen_monthly - yardi_monthly) / yardi_monthly * 100) if yardi_monthly > 0 else 0
            })
        
        # Sort by absolute difference
        property_comparison.sort(key=lambda x: abs(x['difference']), reverse=True)
        
        # Print top 10
        for i, prop in enumerate(property_comparison[:10], 1):
            print(f"\n  {i}. {prop['property_code']}:")
            print(f"     Generated: ${prop['gen_monthly']:,.2f}")
            print(f"     Yardi:     ${prop['yardi_monthly']:,.2f}")
            print(f"     Difference: ${prop['difference']:,.2f} ({prop['pct_diff']:.1f}%)")

def identify_discrepancies(generated_df, yardi_df):
    """Identify specific discrepancies between datasets"""
    print("\n" + "=" * 80)
    print("DISCREPANCY ANALYSIS")
    print("=" * 80)
    
    # Standardize columns
    gen_std = standardize_columns(generated_df, 'Generated')
    yardi_std = standardize_columns(yardi_df, 'Yardi')
    
    # Try to match records by property code and suite
    if 'property_code' in gen_std.columns and 'suite' in gen_std.columns:
        gen_std['match_key'] = gen_std['property_code'].astype(str) + '_' + gen_std['suite'].astype(str)
    if 'property_code' in yardi_std.columns and 'suite' in yardi_std.columns:
        yardi_std['match_key'] = yardi_std['property_code'].astype(str) + '_' + yardi_std['suite'].astype(str)
    
    if 'match_key' in gen_std.columns and 'match_key' in yardi_std.columns:
        gen_keys = set(gen_std['match_key'])
        yardi_keys = set(yardi_std['match_key'])
        
        print(f"\nRecord Matching (by Property + Suite):")
        print(f"  Matched Records:     {len(gen_keys & yardi_keys)}")
        print(f"  Only in Generated:   {len(gen_keys - yardi_keys)}")
        print(f"  Only in Yardi:      {len(yardi_keys - gen_keys)}")
        
        # Sample unmatched records
        only_gen = list(gen_keys - yardi_keys)[:5]
        only_yardi = list(yardi_keys - gen_keys)[:5]
        
        if only_gen:
            print(f"\n  Sample Records Only in Generated:")
            for key in only_gen:
                print(f"    - {key}")
        
        if only_yardi:
            print(f"\n  Sample Records Only in Yardi:")
            for key in only_yardi:
                print(f"    - {key}")

def calculate_accuracy_score(metrics):
    """Calculate overall accuracy score"""
    print("\n" + "=" * 80)
    print("OVERALL ACCURACY ASSESSMENT")
    print("=" * 80)
    
    scores = []
    weights = {
        'Record Count': 0.2,
        'Monthly Rent Total': 0.4,
        'Annual Rent Total': 0.3,
        'Square Feet Total': 0.1
    }
    
    for metric_name, weight in weights.items():
        if metric_name in metrics:
            scores.append(metrics[metric_name]['Match %'] * weight)
    
    overall_score = sum(scores)
    
    print(f"\nWeighted Accuracy Score: {overall_score:.1f}%")
    print("\nBreakdown:")
    for metric_name, weight in weights.items():
        if metric_name in metrics:
            weighted_score = metrics[metric_name]['Match %'] * weight
            print(f"  {metric_name}: {metrics[metric_name]['Match %']:.1f}% × {weight:.0%} = {weighted_score:.1f}%")
    
    print(f"\nAccuracy Assessment:")
    if overall_score >= 95:
        print("  ✓ EXCELLENT - Meets 95%+ accuracy target")
    elif overall_score >= 90:
        print("  ✓ GOOD - Close to target, minor adjustments needed")
    elif overall_score >= 80:
        print("  ⚠ FAIR - Significant discrepancies to investigate")
    else:
        print("  ✗ POOR - Major issues requiring investigation")
    
    return overall_score

def main():
    """Main validation function"""
    print("=" * 80)
    print("RENT ROLL VALIDATION")
    print("=" * 80)
    print(f"Comparing generated rent roll with Yardi export for Fund 2")
    print(f"Report Date: June 30, 2025")
    
    # Load data
    generated_df, yardi_df = load_data()
    
    # Compare totals
    metrics = compare_totals(generated_df, yardi_df)
    
    # Compare at property level
    compare_properties(generated_df, yardi_df)
    
    # Identify discrepancies
    identify_discrepancies(generated_df, yardi_df)
    
    # Calculate overall accuracy
    accuracy_score = calculate_accuracy_score(metrics)
    
    print("\n" + "=" * 80)
    print("VALIDATION COMPLETE")
    print("=" * 80)
    
    return accuracy_score

if __name__ == "__main__":
    main()