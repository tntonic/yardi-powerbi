import pandas as pd
import warnings
warnings.filterwarnings('ignore')

# Read with skiprows=2 which seems to have the right structure
df = pd.read_excel('rent rolls/06.30.25.xlsx', skiprows=2)
print('=== Rent Roll Structure Analysis ===')
print(f'Total rows: {len(df)}')
print(f'Total columns: {len(df.columns)}')

# Clean column names
df.columns = df.columns.str.strip()

# Get property column
prop_col = 'Property'
if prop_col in df.columns:
    # Filter out rows where Property is NaN
    df_clean = df[df[prop_col].notna()].copy()
    print(f'\nRows with property data: {len(df_clean)}')
    
    # Extract fund information from property codes
    df_clean['fund_code'] = df_clean[prop_col].str.extract(r'\(([x3][a-z0-9]+)\)', expand=False)
    df_clean['fund'] = df_clean['fund_code'].apply(lambda x: 'Fund 2' if str(x).startswith('x') else 'Fund 3' if str(x).startswith('3') else 'Unknown')
    
    print('\nFund Distribution:')
    print(df_clean['fund'].value_counts())
    
    print('\nSample properties by fund:')
    for fund in df_clean['fund'].unique():
        if fund \!= 'Unknown':
            sample = df_clean[df_clean['fund'] == fund][prop_col].head(3).tolist()
            print(f'{fund}: {sample}')
    
    # Check key columns
    print('\nKey columns with data:')
    key_cols = ['Property', 'Lease', 'Area', 'Monthly', 'Annual']
    for col in key_cols:
        if col in df_clean.columns:
            non_null = df_clean[col].notna().sum()
            print(f'  {col}: {non_null} non-null values')
    
    # Calculate some metrics
    if 'Area' in df_clean.columns:
        total_area = df_clean["Area"].sum()
        print(f'\nTotal leased area: {total_area:,.0f} SF')
    
    # Check for tenant information
    if 'Lease' in df_clean.columns:
        unique_tenants = df_clean['Lease'].nunique()
        print(f'Unique tenants: {unique_tenants}')

    # Show all column names
    print('\nAll columns:')
    for col in df.columns:
        print(f'  - {col}')
