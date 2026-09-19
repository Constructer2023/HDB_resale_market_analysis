import pandas as pd
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(script_dir, '..', 'data', 'processed')

def _read(name: str):
    path = data_path + '\\' + name
    if not os.path.isfile(path):
        raise FileNotFoundError(f'Missing: {path}')
    return pd.read_csv(path)

def load_resale_price_index():
    df = _read('resale_price_index.csv')
    df['trx_year'] = df['trx_quarter'].str[:4].astype(int)
    df['trx_qtr'] = df['trx_quarter'].str[-1].astype(int)
    df.rename(columns = {'trx_quarter': 'trx_date', 'resale_price_index': 'rpi'}, inplace = True)
    df['quarter_start'] = pd.PeriodIndex(df['trx_date'], freq = 'Q').to_timestamp()
    return df.sort_values('quarter_start').reset_index(drop = True)

def load_median_resale_prices():
    df = _read('median_resale_prices.csv')
    df['trx_year'] = df['trx_quarter'].str[:4].astype(int)
    df['trx_qtr'] = df['trx_quarter'].str[-1].astype(int)
    df.rename(columns = {'trx_quarter': 'trx_date'}, inplace = True)
    df['quarter_start'] = pd.PeriodIndex(df['trx_date'], freq = 'Q').to_timestamp()
    return df

def load_resale_applications():
    df = _read('resale_applications_by_flat_type.csv')
    df['trx_year'] = df['trx_quarter'].str[:4].astype(int)
    df['trx_qtr'] = df['trx_quarter'].str[-1].astype(int)
    df.rename(columns = {'trx_quarter': 'trx_period', 'no_of_resale_applications': 'num'}, inplace=True)
    df['quarter_start'] = pd.PeriodIndex(df['trx_period'], freq = 'Q').to_timestamp()
    return df

def load_applications_registered():
    df = _read('applications_registered.csv')
    df.rename(columns = {'applications_registered': 'num'}, inplace = True)
    return df

def load_demand_for_flats():
    df = _read('demand_for_flats.csv')
    df.rename(columns = {'demand_for_flats': 'num'}, inplace = True)
    return df
