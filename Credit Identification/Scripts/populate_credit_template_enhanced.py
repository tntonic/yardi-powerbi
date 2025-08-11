#!/usr/bin/env python3
"""
Enhanced version: Populate the Tenant Credit Upload template with all available information
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os

def format_number(value):
    """Format numbers with commas"""
    if pd.isna(value) or value == 'null' or value == '':
        return ''
    try:
        # Remove any existing commas and convert to float
        clean_value = str(value).replace(',', '')
        num = float(clean_value)
        # Format with commas, no decimals
        return f'{num:,.0f}'
    except:
        return str(value)

def format_date(date_value):
    """Format date as MM/DD/YY"""
    if pd.isna(date_value) or date_value == '' or date_value == 'null':
        return ''
    try:
        date_obj = pd.to_datetime(date_value)
        return date_obj.strftime('%m/%d/%y')
    except:
        return str(date_value)

def main():
    print("📋 Enhanced: Populating Tenant Credit Upload Template")
    print("=" * 60)
    
    # Read our credit identification data
    credit_data = pd.read_csv('/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Credit Identification/Data/final_tenant_credit_with_ids.csv')
    
    # Read the credit score data with company details
    credit_scores = pd.read_csv('/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Data/Yardi_Tables/dim_fp_customercreditscorecustomdata.csv')
    
    print(f"✅ Loaded {len(credit_scores)} credit score records")
    
    # Create a mapping dictionary from customer code to credit info
    credit_info_map = {}
    for _, row in credit_scores.iterrows():
        cust_code = row['customer code']
        if pd.notna(cust_code):
            credit_info_map[cust_code] = row
    
    # Create new rows for our data
    new_rows = []
    
    # Process each record that has a customer ID
    records_with_ids = credit_data[credit_data['customer_id'].notna()].copy()
    
    print(f"\n📊 Processing {len(records_with_ids)} records with customer IDs...")
    
    populated_count = 0
    
    for _, row in records_with_ids.iterrows():
        customer_id = row['customer_id']
        tenant_name = row['tenant_name']
        
        # Create template row with defaults
        template_row = {
            'Customer ID': customer_id,
            'File Name': '',
            'Company Name/s': tenant_name,
            'Credit Check Date ': '',
            'HQ  Location': '',
            'Annual Revenues': '',
            'Year Founded': '',
            'Website': '',
            'Description': '',
            'Ownership': '',
            'Primary Industry': '',
            'Competitive Position Industry Group': '',
            'Credit Rating': '',
            'Gross Profit': '',
            'EBIT': '',
            'EBITDA': '',
            'Total Assets': '',
            'Total Debt': '',
            'Current Ratio': '',
            'Quick Ratio': '',
            'Net Debt / EBITDA': '',
            'Debt / Assets': '',
            'Report Attachment Link': '',
            'General Notes ': ''
        }
        
        # Check if we have credit information for this customer
        if customer_id in credit_info_map:
            credit_info = credit_info_map[customer_id]
            populated_count += 1
            
            # Populate all available fields
            template_row['Credit Check Date '] = format_date(credit_info.get('date'))
            
            # Credit score
            if pd.notna(credit_info.get('credit score')) and credit_info.get('credit score') != 'null':
                template_row['Credit Rating'] = credit_info['credit score']
            
            # Company information
            if pd.notna(credit_info.get('company location')) and credit_info.get('company location') != 'null':
                template_row['HQ  Location'] = credit_info['company location']
            
            if pd.notna(credit_info.get('annual revenue')) and credit_info.get('annual revenue') != 'null':
                template_row['Annual Revenues'] = format_number(credit_info['annual revenue'])
            
            if pd.notna(credit_info.get('year founded')) and credit_info.get('year founded') != 'null':
                template_row['Year Founded'] = credit_info['year founded']
            
            if pd.notna(credit_info.get('company website')) and credit_info.get('company website') != 'null':
                template_row['Website'] = credit_info['company website']
            
            if pd.notna(credit_info.get('description')) and credit_info.get('description') != 'null':
                template_row['Description'] = credit_info['description']
            
            if pd.notna(credit_info.get('ownership')) and credit_info.get('ownership') != 'null':
                template_row['Ownership'] = credit_info['ownership']
            
            if pd.notna(credit_info.get('primary industry')) and credit_info.get('primary industry') != 'null':
                template_row['Primary Industry'] = credit_info['primary industry']
            
            if pd.notna(credit_info.get('comp. position industry group')) and credit_info.get('comp. position industry group') != 'null':
                template_row['Competitive Position Industry Group'] = credit_info['comp. position industry group']
            
            # Financial metrics
            if pd.notna(credit_info.get('gross profit')) and credit_info.get('gross profit') != 'null':
                template_row['Gross Profit'] = format_number(credit_info['gross profit'])
            
            if pd.notna(credit_info.get('ebit')) and credit_info.get('ebit') != 'null':
                template_row['EBIT'] = format_number(credit_info['ebit'])
            
            if pd.notna(credit_info.get('ebitda')) and credit_info.get('ebitda') != 'null':
                template_row['EBITDA'] = format_number(credit_info['ebitda'])
            
            if pd.notna(credit_info.get('total assets')) and credit_info.get('total assets') != 'null':
                template_row['Total Assets'] = format_number(credit_info['total assets'])
            
            if pd.notna(credit_info.get('total debt')) and credit_info.get('total debt') != 'null':
                template_row['Total Debt'] = format_number(credit_info['total debt'])
            
            # Report link
            if pd.notna(credit_info.get('report link')) and credit_info.get('report link') not in ['0', 'null', '']:
                template_row['Report Attachment Link'] = credit_info['report link']
            
            # Notes
            if pd.notna(credit_info.get('notes')) and credit_info.get('notes') != 'null':
                template_row['General Notes '] = credit_info['notes']
            
            # Add file name if available
            if pd.notna(credit_info.get('customer name')):
                # Try to construct a file name pattern
                template_row['File Name'] = f"FP TCE - {credit_info['customer name']}.xlsm"
        
        # Add credit match info if available
        if pd.notna(row.get('matched_credit_name')):
            if template_row['General Notes ']:
                template_row['General Notes '] += f'; Credit match: {row["matched_credit_name"]}'
            else:
                template_row['General Notes '] = f'Credit match: {row["matched_credit_name"]}'
        
        new_rows.append(template_row)
    
    # Create DataFrame from new rows
    output_df = pd.DataFrame(new_rows)
    
    # Sort by customer ID
    output_df = output_df.sort_values('Customer ID')
    
    # Save the populated template
    output_path = '/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Credit Identification/Tenant_Credit_Upload_Enhanced.csv'
    
    # Create the header rows to match the template format
    header_rows = pd.DataFrame([
        ['Required field?', 'N/A', 'N/A', 'No', 'Yes', 'NO', 'NO', 'NO', 'NO', 'NO', 'NO', 'NO', 'NO', 
         'Yes', 'NO', 'NO', 'NO', 'NO', 'NO', '', '', '', '', '', ''],
        ['Field Type', 'ID Field for loader- Only load items that have the ID', 'Ignore-for internal use only', 
         'Free Text-short (1-2 rows)\nNote for the Internal team- this field is taken from the Tenant column on the report', 
         'Date', 'Free Text-short (1-2 rows)', 'Number', 'Number', 'Hyperlink/Free text', 'Free Text-long (paragraph)',
         'Free Text-short (1-2 rows)', 'Free Text-short (1-2 rows)', 'Free Text-short (1-2 rows)', 'Number', 'Number',
         'Number', 'Number', 'Number', 'Number', '', '', '', '', 'Hyperlink/Free text', 'Free Text-long (paragraph)'],
        ['Field Name'] + list(output_df.columns)
    ])
    
    # Combine header with data
    final_output = pd.concat([header_rows, output_df], ignore_index=True)
    
    # Save to CSV
    final_output.to_csv(output_path, index=False, header=False)
    
    # Summary statistics
    print("\n" + "=" * 60)
    print("📊 SUMMARY:")
    print(f"   Total records processed: {len(new_rows)}")
    print(f"   Records with credit data: {populated_count}")
    
    # Count populated fields
    credit_rating_count = sum(1 for row in new_rows if row['Credit Rating'] != '')
    date_count = sum(1 for row in new_rows if row['Credit Check Date '] != '')
    location_count = sum(1 for row in new_rows if row['HQ  Location'] != '')
    revenue_count = sum(1 for row in new_rows if row['Annual Revenues'] != '')
    website_count = sum(1 for row in new_rows if row['Website'] != '')
    industry_count = sum(1 for row in new_rows if row['Primary Industry'] != '')
    ownership_count = sum(1 for row in new_rows if row['Ownership'] != '')
    
    print(f"\n📋 FIELD POPULATION:")
    print(f"   Customer IDs: {len(new_rows)} (100%)")
    print(f"   Company Names: {len(new_rows)} (100%)")
    print(f"   Credit Ratings: {credit_rating_count} ({credit_rating_count/len(new_rows)*100:.1f}%)")
    print(f"   Credit Check Dates: {date_count} ({date_count/len(new_rows)*100:.1f}%)")
    print(f"   HQ Locations: {location_count} ({location_count/len(new_rows)*100:.1f}%)")
    print(f"   Annual Revenues: {revenue_count} ({revenue_count/len(new_rows)*100:.1f}%)")
    print(f"   Websites: {website_count} ({website_count/len(new_rows)*100:.1f}%)")
    print(f"   Primary Industry: {industry_count} ({industry_count/len(new_rows)*100:.1f}%)")
    print(f"   Ownership: {ownership_count} ({ownership_count/len(new_rows)*100:.1f}%)")
    
    print(f"\n✅ Enhanced template populated and saved to:")
    print(f"   {output_path}")
    
    # List companies with complete credit data
    complete_records = []
    for row in new_rows:
        if row['Credit Rating'] != '' and row['Credit Check Date '] != '':
            complete_records.append(f"{row['Customer ID']} - {row['Company Name/s']}")
    
    if complete_records:
        print(f"\n📊 COMPANIES WITH COMPLETE CREDIT DATA ({len(complete_records)}):")
        for i, company in enumerate(complete_records[:10], 1):
            print(f"   {i}. {company}")
        if len(complete_records) > 10:
            print(f"   ... and {len(complete_records) - 10} more")
    
    print("\n💡 Next steps:")
    print("   1. Review and validate populated data")
    print("   2. Obtain credit reports for companies without data")
    print("   3. Update SharePoint links for existing reports")
    print("   4. Fill any remaining required fields manually")

if __name__ == "__main__":
    main()