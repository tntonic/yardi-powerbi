#!/usr/bin/env python3
"""
Populate the Tenant Credit Upload template with available information
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os

def main():
    print("📋 Populating Tenant Credit Upload Template")
    print("=" * 60)
    
    # Read our credit identification data
    credit_data = pd.read_csv('/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Credit Identification/Data/final_tenant_credit_with_ids.csv')
    
    # Read the credit score data with company details
    yardi_credit_path = '/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Data/Yardi_Tables/dim_fp_customercreditscorecustomdata.csv'
    if os.path.exists(yardi_credit_path):
        credit_scores = pd.read_csv(yardi_credit_path)
    else:
        print("⚠️  Credit score data not found, using limited information")
        credit_scores = pd.DataFrame()
    
    # Read the template to get the structure
    template = pd.read_csv('/Users/michaeltang/Downloads/Tenant Credit Upload (02.25.25).csv', skiprows=3)
    
    # Create new rows for our data
    new_rows = []
    
    # Process each record that has a customer ID and credit match
    matched_data = credit_data[
        (credit_data['customer_id'].notna()) & 
        (credit_data['matched_credit_name'].notna())
    ].copy()
    
    print(f"\n📊 Processing {len(matched_data)} records with credit matches...")
    
    for _, row in matched_data.iterrows():
        customer_id = row['customer_id']
        tenant_name = row['tenant_name']
        credit_name = row['matched_credit_name']
        
        # Create template row
        template_row = {
            'Customer ID': customer_id,
            'File Name': '',  # We don't have the exact file names
            'Company Name/s': tenant_name,
            'Credit Check Date ': '',  # Will populate if we have it
            'HQ  Location': '',
            'Annual Revenues': '',
            'Year Founded': '',
            'Website': '',
            'Description': '',
            'Ownership': '',
            'Primary Industry': '',
            'Competitive Position Industry Group': '',
            'Credit Rating': '',  # Will populate from credit scores
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
            'General Notes ': f'Credit match: {credit_name}'
        }
        
        # Try to find additional information from credit scores
        if not credit_scores.empty:
            # Extract customer numeric ID from customer_id (e.g., c0000056 -> 56)
            try:
                cust_num = int(customer_id.replace('c', '').lstrip('0'))
                
                # Look for matching record in credit scores
                credit_match = credit_scores[credit_scores['hmyperson_customer'] == cust_num]
                
                if not credit_match.empty:
                    credit_info = credit_match.iloc[0]
                    
                    # Populate available fields
                    if pd.notna(credit_info.get('date')):
                        # Parse date and format as MM/DD/YY
                        try:
                            date_obj = pd.to_datetime(credit_info['date'])
                            template_row['Credit Check Date '] = date_obj.strftime('%m/%d/%y')
                        except:
                            pass
                    
                    if pd.notna(credit_info.get('credit score')):
                        template_row['Credit Rating'] = credit_info['credit score']
                    
                    if pd.notna(credit_info.get('company location')):
                        template_row['HQ  Location'] = credit_info['company location']
                    
                    if pd.notna(credit_info.get('annual revenue')):
                        # Format revenue with commas
                        try:
                            revenue = float(credit_info['annual revenue'])
                            template_row['Annual Revenues'] = f'{revenue:,.0f}'
                        except:
                            template_row['Annual Revenues'] = credit_info['annual revenue']
                    
                    if pd.notna(credit_info.get('primary industry')):
                        template_row['Primary Industry'] = credit_info['primary industry']
                    
                    if pd.notna(credit_info.get('ownership')):
                        template_row['Ownership'] = credit_info['ownership']
                    
                    # Add company name from credit data if different
                    if pd.notna(credit_info.get('customer name')):
                        if credit_info['customer name'] != tenant_name:
                            template_row['General Notes '] += f'; Credit name: {credit_info["customer name"]}'
            except:
                pass
        
        # Check if we have a folder path for potential PDF
        if pd.notna(row.get('folder_path')):
            template_row['General Notes '] += f'; Folder: {row["folder_path"]}'
        
        new_rows.append(template_row)
    
    # Also add records with customer IDs but no credit matches (for future population)
    no_match_data = credit_data[
        (credit_data['customer_id'].notna()) & 
        (credit_data['matched_credit_name'].isna())
    ].copy()
    
    print(f"\n📋 Adding {len(no_match_data)} records without credit matches (for future population)...")
    
    for _, row in no_match_data.iterrows():
        template_row = {
            'Customer ID': row['customer_id'],
            'File Name': '',
            'Company Name/s': row['tenant_name'],
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
            'General Notes ': 'No credit report available'
        }
        new_rows.append(template_row)
    
    # Create DataFrame from new rows
    output_df = pd.DataFrame(new_rows)
    
    # Sort by customer ID
    output_df = output_df.sort_values('Customer ID')
    
    # Save the populated template
    output_path = '/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Credit Identification/Tenant_Credit_Upload_Populated.csv'
    
    # Create the header rows
    header_rows = pd.DataFrame([
        ['Required field?', 'N/A', 'N/A', 'No', 'Yes', 'NO', 'NO', 'NO', 'NO', 'NO', 'NO', 'NO', 'NO', 'Yes', 'NO', 'NO', 'NO', 'NO', 'NO', '', '', '', '', '', ''],
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
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY:")
    print(f"   Total records processed: {len(new_rows)}")
    print(f"   - With credit matches: {len(matched_data)}")
    print(f"   - Without matches (placeholder): {len(no_match_data)}")
    
    # Count populated fields
    credit_rating_count = sum(1 for row in new_rows if row['Credit Rating'] != '')
    date_count = sum(1 for row in new_rows if row['Credit Check Date '] != '')
    location_count = sum(1 for row in new_rows if row['HQ  Location'] != '')
    
    print(f"\n📋 FIELD POPULATION:")
    print(f"   Customer IDs: {len(new_rows)} (100%)")
    print(f"   Company Names: {len(new_rows)} (100%)")
    print(f"   Credit Ratings: {credit_rating_count}")
    print(f"   Credit Check Dates: {date_count}")
    print(f"   HQ Locations: {location_count}")
    
    print(f"\n✅ Template populated and saved to:")
    print(f"   {output_path}")
    
    print("\n💡 Next steps:")
    print("   1. Fill in missing Credit Check Dates (required field)")
    print("   2. Fill in missing Credit Ratings (required field)")
    print("   3. Add file names for existing credit reports")
    print("   4. Add SharePoint attachment links")
    print("   5. Obtain credit reports for companies without matches")

if __name__ == "__main__":
    main()