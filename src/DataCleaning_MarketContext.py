import pandas as pd
import numpy as np
import os
import re

script_dir = os.path.dirname(os.path.abspath(__file__))
raw_path = os.path.join(script_dir, '..', 'data', 'raw')
processed_path = os.path.join(script_dir, '..', 'data', 'processed')

def standardise_flat_type(s: str):
    if pd.isna(s):
        return np.nan
    s = str(s).strip().upper().replace("-", " ")
    s = re.sub(r'\s+', ' ', s)
    mapping = {'MULTI GENERATION': 'MULTI-GENERATION'}
    return mapping.get(s, s)

def standardise_town(s: str):
    if pd.isna(s):
        return np.nan
    s = str(s).strip().upper()
    s = re.sub(r'\s+', ' ', s)
    aliases = {
        "CENTRAL": "CENTRAL AREA",
        "KALLANG/WHAMPOA": "KALLANG/WHAMPOA",
        "KALLANG WHAMPOA": "KALLANG/WHAMPOA"
    }
    return aliases.get(s, s)

def to_missing(series: pd.Series):
    """
    Convert 'na', '-', '', 'NA', 'N/A' etc. to real missing values.
    """
    return series.replace(
        to_replace = [r'(?i)^na$', r'(?i)^n/a$', r'^-$', r'^\s*$'],
        value = np.nan,
        regex = True,
    )

def parse_quarter(q: str):
    if pd.isna(q):
        return pd.NaT
    q = str(q).strip().upper().replace('-', '')
    if re.match(r'^\d{4}Q[1-4]$', q):
        return pd.Period(q, freq = 'Q')
    return pd.NaT

# ------------------------------------Delimiter------------------------------------

def clean_resale_price_index():
    path = raw_path + '\\' + 'Housing_and_Development_Board_HDB_Resale_Price_Index_Quarterly.csv'
    df = pd.read_csv(path)
    id_col = df.columns[0]
    long = df.melt(id_vars = id_col, var_name = 'quarter_raw', value_name = 'resale_price_index')
    long = long.rename(columns = {id_col: 'series'})
    # Parse 20262Q → year=2026, quarter=2
    def parse_hdb_quarter(x):
        x = str(x).strip()
        m = re.match(r'^(\d{4})(\d)Q$', x)
        if m:
            year, q = m.groups()
            return pd.Period(f'{year}Q{q}', freq = 'Q')
        return pd.NaT
    long['trx_quarter'] = long['quarter_raw'].apply(parse_hdb_quarter)
    long['resale_price_index'] = pd.to_numeric(long['resale_price_index'], errors = 'coerce')
    long = long.dropna(subset = ['trx_quarter'])
    long = long.loc[:, ['trx_quarter', 'resale_price_index']]
    long = long.sort_values('trx_quarter')
    long = long.reset_index(drop = True)
    out = processed_path + '\\' + 'resale_price_index.csv'
    long.to_csv(out, index = False)
    print(f'Saved {out} \n shape = {long.shape}')
    return long

def clean_median_resale_prices():
    path = raw_path + '\\' + 'Median_Resale_Prices_for_Registered_Applications_by_Town_and_Flat_Type.csv'
    df = pd.read_csv(path)
    df['price'] = to_missing(df['price'])
    df['price'] = pd.to_numeric(df['price'], errors = 'coerce')
    df['town'] = df['town'].apply(standardise_town)
    df['flat_type'] = df['flat_type'].apply(standardise_flat_type)
    df['trx_quarter'] = df['quarter'].apply(parse_quarter)
    df = df.dropna(subset = ['trx_quarter']).copy()
    df = df.loc[:, ['trx_quarter', 'town', 'flat_type', 'price']]
    df = df.rename(columns = {'price': 'median_resale_price'})
    df = df.sort_values(['trx_quarter', 'town', 'flat_type']).reset_index(drop = True)
    out = processed_path + '\\' + 'median_resale_prices.csv'
    df.to_csv(out, index = False)
    print(f'Saved {out} \n shape = {df.shape}')
    return df

def clean_resale_applications():
    path = raw_path + '\\' + 'Number_of_Resale_Applications_Registered_by_Flat_Type.csv'
    df = pd.read_csv(path)
    df['no_of_resale_applications'] = to_missing(df['no_of_resale_applications'])
    df['no_of_resale_applications'] = pd.to_numeric(df['no_of_resale_applications'], errors = 'coerce')
    df['flat_type'] = df['flat_type'].apply(standardise_flat_type)
    df['trx_quarter'] = df['quarter'].apply(parse_quarter)
    df = df.dropna(subset = ['trx_quarter']).copy()
    df = df.loc[:, ['trx_quarter', 'flat_type', 'no_of_resale_applications']]
    df = df.sort_values(['trx_quarter', 'flat_type']).reset_index(drop = True)
    out = processed_path + '\\' + 'resale_applications_by_flat_type.csv'
    df.to_csv(out, index = False)
    print(f'Saved {out} \n shape={df.shape}')
    return df

def clean_applications_registered():
    path = raw_path + '\\' + 'Applications_Registered_for_Resale_Flats_and_Rental_Flats.csv'
    df = pd.read_csv(path)
    df['applications_registered'] = pd.to_numeric(df['applications_registered'], errors = 'coerce')
    df['type'] = df['type'].str.strip().str.lower()
    df = df.rename(columns = {'financial_year': 'year'})
    df = df.sort_values(['year', 'type']).reset_index(drop = True)
    out = processed_path + '\\' + 'applications_registered.csv'
    df.to_csv(out, index = False)
    print(f'Saved {out} \n shape={df.shape}')
    return df

def clean_demand():
    path = raw_path + '\\' + 'Demand_for_Rental_and_Sold_Flats.csv'
    df = pd.read_csv(path)
    df['demand_for_flats'] = pd.to_numeric(df['demand_for_flats'], errors = 'coerce')
    df['flat_type'] = df['flat_type'].str.strip().str.lower()
    df['mid_year'] = ((df['start_year'] + df['end_year']) / 2).round().astype(int)
    df = df.sort_values(['start_year', 'flat_type']).reset_index(drop = True)
    out = processed_path + '\\' + 'demand_for_flats.csv'
    df.to_csv(out, index = False)
    print(f'Saved {out} \n shape={df.shape}')
    return df


if __name__ == "__main__":
    print('Cleaning auxiliary datasets...\n')
    rpi = clean_resale_price_index()
    med = clean_median_resale_prices()
    apps = clean_resale_applications()
    reg = clean_applications_registered()
    dem = clean_demand()
    # test below
    print('\n=== Quick checks ===')
    print('Resale Price Index sample:')
    print(rpi.head())
    print('\nMedian prices – unique flat_type:', sorted(med['flat_type'].dropna().unique()))
    print('Median prices – sample towns:', sorted(med['town'].dropna().unique())[:8])
    print('\nDone.')
