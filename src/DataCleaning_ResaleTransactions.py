import pandas as pd
import numpy as np
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(script_dir, '..', 'data', 'raw', 'Resale_Flat_Prices_based_on_Registration_Date_from_Jan2017_onwards.csv')
data = pd.read_csv(data_path, header = 0)

def duplicate_remove(df):
    duplicate_mask = df.duplicated()
    removed_ids = df.index[duplicate_mask]
    df_cleaned = df.drop_duplicates()
    return df_cleaned, removed_ids

def col_transform(df):
    # todo 1: month(str) -> trx_year(int), trx_month(int)
    split_dates = df['month'].str.split('-', expand = True)
    df['trx_year'] = split_dates[0].astype(int)
    df['trx_month'] = split_dates[1].astype(int)
    df.rename(columns = {'month': 'trx_date'}, inplace = True)
    # todo 2: storey_range(str) -> storey_list(list)
    df['storey_lower'] = [xx for xx in df['storey_range'].str.split(' TO ').str[0].astype(int)]
    df['storey_upper'] = [xx + 2 for xx in df['storey_range'].str.split(' TO ').str[0].astype(int)]
    df['storey_midpoint'] = [xx + 1 for xx in df['storey_range'].str.split(' TO ').str[0].astype(int)]
    df.drop(columns = ['storey_range'], inplace = True)
    # todo 3: remaining_lease(str) -> remaining_lease_month(int)
    years = df['remaining_lease'].str.extract(r'(\d+)\s+year?', expand = False)
    years = years.fillna(0)
    years = years.astype(int)
    months = df['remaining_lease'].str.extract(r'(\d+)\s+month?', expand = False)
    months = months.fillna(0)
    months = months.astype(int)
    df['remaining_lease_month'] = (years * 12) + months
    df.drop('remaining_lease', axis = 1, inplace = True)
    df.rename(columns = {'lease_commence_date': 'lease_commence'}, inplace = True)
    # todo 4: resale_price(float), floor_area_sqm(float) -> price_per_sqm(float)
    df['price_per_sqm'] = np.round(df['resale_price'] / df['floor_area_sqm'], 2)
    # todo 5: trx_year(int), lease_commence(int) -> flat_year(int)
    df['flat_year'] = df['trx_year'] - df['lease_commence']
    # todo 6: trx_date(str) -> trx_date(date)
    df['trx_date'] = pd.to_datetime(df['trx_date'], format = '%Y-%m')
    return df

def col_shuffle(df):
    index_order = ['trx_date', 'trx_year', 'trx_month', 'lease_commence',
                   'flat_year', 'remaining_lease_month',
                   'flat_type', 'flat_model', 'town', 'street_name', 'block',
                   'storey_lower', 'storey_midpoint', 'storey_upper',
                   'price_per_sqm', 'floor_area_sqm', 'resale_price']
    df = df[index_order]
    return df


if __name__ == '__main__':
    data, seq = duplicate_remove(data)
    data = col_transform(data)
    data_cleaned = col_shuffle(data)
    save_flag = True
    if save_flag:
        file_path = '../data/processed/resale_transactions.csv'
        data_cleaned.to_csv(file_path, index = False)
    print(data_cleaned.info())
