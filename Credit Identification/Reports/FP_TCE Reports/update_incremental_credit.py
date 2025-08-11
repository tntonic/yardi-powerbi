import pandas as pd
import numpy as np
from datetime import datetime

def update_incremental_credit():
    """Update the CSV with incremental credit information from Q2 2025 PDFs"""
    
    # Read the existing CSV
    csv_path = '/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Data/new_tenants_fund2_fund3_since_2025_populated.csv'
    df = pd.read_csv(csv_path)
    
    print("Original CSV shape:", df.shape)
    print("=" * 50)
    
    # Add Olive My Pickle (missing from CSV but in Fund 2 Q2 2025)
    new_tenant = {
        'customer_id': np.nan,  # Will need to be assigned
        'tenant_id': 't0001700',  # Next available ID
        'tenant_name': 'Olive My Pickle',
        'property_address': 'nan Jacksonville, FL 32256.0',
        'property_name': '7720 Philips Highway',
        'property_code': 'xfl7720p',
        'fund': 2,
        'naics': np.nan,
        'lease_id': np.nan,
        'credit_score': 5.0,  # From Q2 PDF
        'credit_score_date': '2025-07-01',  # Q2 2025
        'parent_customer_id': np.nan,
        'tenant_risk': np.nan,
        'amendment_start_date': '2025-07-01',
        'amendment_type': 'New',
        'amendment_status': 'Activated'
    }
    
    # Check if Olive My Pickle already exists (to avoid duplicates)
    if not df[df['tenant_name'] == 'Olive My Pickle'].empty:
        print("⚠️  Olive My Pickle already exists in the CSV")
    else:
        # Add the new tenant
        df = pd.concat([df, pd.DataFrame([new_tenant])], ignore_index=True)
        print("✅ Added: Olive My Pickle (New tenant from Fund 2 Q2 2025)")
    
    # Update credit scores from Q2 2025 PDFs
    credit_updates = [
        # Fund 2 Q2 2025
        ('Trident ExIm LLC', 4.0),
        ('EA Engineering, Science, and Technology, Inc.', 5.0),
        ('Kreg Therapeutics, Inc', 4.5),  # KREG in PDF
        ('International General Trading Corp', 3.5),
        
        # Fund 3 Q2 2025 (selected important ones)
        ('Pacesetter Steel Service, Inc.', 3.0),
        ('Koontz Electric Company, Inc.', 6.0),
        ('USCutter Inc.', 4.0),
        ('Dematic Corp.', np.nan),  # "Not Completed" in PDF
        ('Aluma-Form, Inc.', 5.0),
        ('All-N-Express, LLC', np.nan),  # Small deal
        ('Marcolin U.S.A. Eyewear Corp.', 5.5),
        ('Digi America Inc.', 5.0),
        ('American Builders & Contractor Supply Co. TN', np.nan)  # "Not Completed"
    ]
    
    print("\n" + "=" * 50)
    print("Updating credit scores from Q2 2025 PDFs:")
    print("-" * 50)
    
    updates_made = 0
    for tenant_name, new_score in credit_updates:
        # Find matching tenant
        mask = df['tenant_name'].str.contains(tenant_name.split(',')[0], case=False, na=False)
        
        if mask.any():
            # Update credit score if different or missing
            for idx in df[mask].index:
                old_score = df.loc[idx, 'credit_score']
                if pd.isna(old_score) or old_score == '':
                    df.loc[idx, 'credit_score'] = new_score
                    df.loc[idx, 'credit_score_date'] = '2025-07-01'
                    print(f"  ✅ {tenant_name}: Added score {new_score}")
                    updates_made += 1
                elif old_score != new_score and not pd.isna(new_score):
                    print(f"  ⚠️  {tenant_name}: Existing score {old_score} → {new_score} (Updated)")
                    df.loc[idx, 'credit_score'] = new_score
                    df.loc[idx, 'credit_score_date'] = '2025-07-01'
                    updates_made += 1
                else:
                    print(f"  ℹ️  {tenant_name}: Score unchanged ({old_score})")
        else:
            print(f"  ❌ {tenant_name}: Not found in CSV")
    
    print("-" * 50)
    print(f"Total updates made: {updates_made}")
    
    # Save the updated CSV
    output_path = '/Users/michaeltang/Downloads/Credit/FP_TCE Reports/new_tenants_with_q2_2025_updates.csv'
    df.to_csv(output_path, index=False)
    
    print("\n" + "=" * 50)
    print(f"✅ Updated CSV saved to: {output_path}")
    print(f"Final shape: {df.shape}")
    
    # Summary statistics
    print("\n" + "=" * 50)
    print("Summary Statistics:")
    print(f"- Total tenants: {len(df)}")
    print(f"- Fund 2 tenants: {len(df[df['fund'] == 2])}")
    print(f"- Fund 3 tenants: {len(df[df['fund'] == 3])}")
    print(f"- Tenants with credit scores: {df['credit_score'].notna().sum()}")
    print(f"- Average credit score: {df['credit_score'].mean():.2f}")
    
    return df

if __name__ == "__main__":
    updated_df = update_incremental_credit()