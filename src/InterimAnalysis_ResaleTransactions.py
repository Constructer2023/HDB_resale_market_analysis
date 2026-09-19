import pandas as pd
import numpy as np

def market_snapshot(data: pd.DataFrame):
    return {
        'total_transactions': len(data),
        'earliest_date': data['trx_date'].min() if 'trx_date' in data.columns else None,
        "latest_date": data['trx_date'].max() if 'trx_date' in data.columns else None,
        'mean_price': data['resale_price'].mean(),
        'median_price': data['resale_price'].median(),
        'mean_pps': data['price_per_sqm'].mean(),
        'median_pps': data['price_per_sqm'].median(),
        'mean_area': data['floor_area_sqm'].mean(),
        'median_area': data['floor_area_sqm'].median()
    }

def yearly_summary(data: pd.DataFrame):
    # Explicitly name the output column names using parameters
    g = data.groupby('trx_year').agg(
        transactions = ('resale_price', 'size'),
        mean_price = ('resale_price', 'mean'),
        median_price = ('resale_price', 'median'),
        mean_pps = ('price_per_sqm', 'mean'),
        median_pps = ('price_per_sqm', 'median'),
        mean_area = ('floor_area_sqm', 'mean'),
        median_area = ('floor_area_sqm', 'median'),
    ).reset_index()
    return g

def monthly_summary(data: pd.DataFrame):
    # Explicitly name the output column names using parameters
    g = data.groupby(['trx_year', 'trx_month']).agg(
        transactions = ('resale_price', 'size'),
        mean_price = ('resale_price', 'mean'),
        median_price = ('resale_price', 'median'),
        mean_pps = ('price_per_sqm', 'mean'),
        median_pps = ('price_per_sqm', 'median'),
        mean_area = ('floor_area_sqm', 'mean'),
        median_area = ('floor_area_sqm', 'median'),
    ).reset_index()
    return g

def town_summary(df: pd.DataFrame, min_trx: int = 100, by_col: str = 'median_price'):
    g = df.groupby('town').agg(
        transactions = ('resale_price', 'size'),
        mean_price = ('resale_price', 'mean'),
        median_price = ('resale_price', 'median'),
        mean_pps = ('price_per_sqm', 'mean'),
        median_pps = ('price_per_sqm', 'median'),
        mean_area = ('floor_area_sqm', 'mean'),
        median_area = ('floor_area_sqm', 'median')
    ).reset_index()
    return g[g['transactions'] >= min_trx].sort_values(by_col, ascending = False)

def flat_type_summary(df: pd.DataFrame):
    return (
        df.groupby('flat_type').agg(
            transactions = ('resale_price', 'size'),
            mean_price = ('resale_price', 'mean'),
            median_price = ('resale_price', 'median'),
            mean_pps = ('price_per_sqm', 'mean'),
            median_pps = ('price_per_sqm', 'median'),
            mean_area = ('floor_area_sqm', 'mean'),
            median_area = ('floor_area_sqm', 'median')
        ).reset_index().sort_values('median_price', ascending = False)
    )

def add_bands(df: pd.DataFrame):
    out = df.copy(deep = True)
    out['area_band'] = pd.cut(
        out['floor_area_sqm'],
        bins = [0, 60, 80, 100, 120, np.inf],
        labels = ['<60', '60-79', '80-99', '100-119', '120+'],
        right = False,
    )
    out['storey_band'] = pd.cut(
        out['storey_midpoint'],
        bins = [0, 3, 6, 9, 12, 15, 18, np.inf],
        labels = ['01-03', '04-06', '07-09', '10-12', '13-15', '16-18', '19+'],
        right = True,
    )
    out['age_band'] = pd.cut(
        out['flat_year'],
        bins = [0, 10, 20, 30, 40, 99],
        labels = ['0-9 yrs', '10-19 yrs', '20-29 yrs', '30-39 yrs', '40+ yrs'],
        right = False,
    )
    out['lease_band'] = pd.cut(
        out['remaining_lease_month'] / 12,
        bins = [0, 50, 60, 70, 80, 99],
        labels = ['<50 yrs', '50-59 yrs', '60-69 yrs', '70-79 yrs', '80+ yrs'],
        right = False,
    )
    return out
