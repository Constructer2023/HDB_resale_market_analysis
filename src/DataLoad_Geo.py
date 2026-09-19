from __future__ import annotations
import os
import pandas as pd

script_dir = os.path.dirname(os.path.abspath(__file__))
processed_path = os.path.join(script_dir, '..', 'data', 'processed')
aid_path = os.path.join(script_dir, '..', 'data', 'aid')

def load_transactions_geo():
    resale_path = f'{processed_path}\\resale_transactions.csv'
    cache_path = f'{aid_path}\\hdb_geocode_cache.csv'
    df_resale = pd.read_csv(resale_path)
    df_cache = pd.read_csv(cache_path)
    df_resale.rename(columns = {'block': 'blk', 'street_name': 'st'}, inplace = True)
    shared_cols = ['blk', 'st']
    df = pd.merge(df_resale, df_cache, on = shared_cols, how = 'left')
    df['trx_date'] = pd.to_datetime(df['trx_date'], errors = 'coerce')
    for c in ['lat', 'lon', 'to_mrt', 'to_city', 'resale_price',
              'price_per_sqm', 'floor_area_sqm', 'mrt_lat', 'mrt_lon']:
        df[c] = pd.to_numeric(df[c], errors = 'coerce')
    for c in ['zone_id', 'trx_year', 'trx_month']:
        df[c] = pd.to_numeric(df[c], errors = 'coerce')
    df.drop(columns = ['storey_lower', 'storey_upper', 'town'], inplace = True)
    df.to_csv(f'{aid_path}\\resale_trx_geo.csv', index = False)
    print(f'Saved cleaned final file -> {aid_path}\\resale_trx_geo.csv')
    return df

def load_geocode_cache(path: str | None = None):
    if path == None:
        path = f'{aid_path}\\hdb_geocode_cache.csv'
    return pd.read_csv(path)

def load_mrt_stations(path: str | None = None):
    if path == None:
        path = f'{aid_path}\\mrt_stations_cleaned.csv'
    return pd.read_csv(path)
