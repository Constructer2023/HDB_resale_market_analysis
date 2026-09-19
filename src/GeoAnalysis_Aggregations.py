from __future__ import annotations
import numpy as np
import pandas as pd

def add_geo_bands(df: pd.DataFrame):
    out = df.copy()
    if 'to_mrt' in out.columns:
        out['mrt_band'] = pd.cut(
            out['to_mrt'],
            bins = [-np.inf, 300, 500, 800, 1200, 2000, np.inf],
            labels = ['0-299m', '300-499m', '500-799m', '800-1199m', '1.2-2km', '2km+'],
            right = False
        )
    if 'to_city' in out.columns:
        out['city_band'] = pd.cut(
            out['to_city'],
            bins = [-np.inf, 5000, 10000, 15000, 20000, np.inf],
            labels = ['0-5km', '5-10km', '10-15km', '15-20km', '20km+'],
            right = False
        )
    if 'to_mrt' in out.columns:
        out['to_mrt_km'] = out['to_mrt'] / 1000.0
    if 'to_city' in out.columns:
        out['to_city_km'] = out['to_city'] / 1000.0
    return out

def summary_by_mrt_band(df: pd.DataFrame):
    d = add_geo_bands(df)
    g = (
        d.dropna(subset = ['mrt_band']).groupby('mrt_band', observed = True).agg(
            transactions = ('resale_price', 'size'),
            mean_price = ('resale_price', 'mean'),
            median_price = ('resale_price', 'median'),
            mean_pps = ('price_per_sqm', 'mean'),
            median_pps = ('price_per_sqm', 'median'),
            avg_to_mrt = ('to_mrt', 'mean')
        ).reset_index()
    )
    return g

def summary_by_city_band(df: pd.DataFrame):
    d = add_geo_bands(df)
    g = (
        d.dropna(subset = ['city_band']).groupby('city_band', observed = True).agg(
            transactions = ('resale_price', 'size'),
            mean_price = ('resale_price', 'mean'),
            median_price = ('resale_price', 'median'),
            mean_pps = ('price_per_sqm', 'mean'),
            median_pps = ('price_per_sqm', 'median'),
            avg_to_city = ('to_city', 'mean')
        ).reset_index()
    )
    return g

def summary_by_subzone(df: pd.DataFrame, min_n: int = 30):
    g = (
        df.dropna(subset = ['subzone']).groupby(
            ['zone_id', 'subzone'], dropna = False
        ).agg(
            transactions = ('resale_price', 'size'),
            mean_price = ('resale_price', 'mean'),
            median_price = ('resale_price', 'median'),
            mean_pps = ('price_per_sqm', 'mean'),
            median_pps = ('price_per_sqm', 'median'),
            avg_to_mrt = ('to_mrt', 'mean'),
            avg_to_city = ('to_city', 'mean')
        ).reset_index()
    )
    return g[g['transactions'] >= min_n].sort_values('median_pps', ascending = False)

def summary_by_nearest_mrt(df: pd.DataFrame, min_n: int = 30):
    g = (
        df.dropna(subset = ['nearest_mrt']).groupby('nearest_mrt').agg(
            transactions = ('resale_price', 'size'),
            mean_pps = ('price_per_sqm', 'mean'),
            median_pps = ('price_per_sqm', 'median'),
            mean_price = ('resale_price', 'mean'),
            avg_to_mrt = ('to_mrt', 'mean')
        ).reset_index()
    )
    return g[g['transactions'] >= min_n].sort_values('transactions', ascending = False)

def mrt_band_by_flat_type(df: pd.DataFrame, flat_type: str = '4 ROOM'):
    d = add_geo_bands(df)
    d = d[d['flat_type'] == flat_type]
    return (
        d.dropna(subset = ['mrt_band']).groupby('mrt_band', observed = True).agg(
            transactions = ('resale_price', 'size'),
            mean_pps = ('price_per_sqm', 'mean'),
            median_pps = ('price_per_sqm', 'median'),
            mean_price = ('resale_price', 'mean')
        ).reset_index()
    )

def joint_mrt_city_bands(df: pd.DataFrame, min_n: int = 20):
    d = add_geo_bands(df)
    g = (
        d.dropna(subset = ['mrt_band', 'city_band']).groupby(
            ['city_band', 'mrt_band'], observed = True
        ).agg(
            transactions = ('resale_price', 'size'),
            mean_pps = ('price_per_sqm', 'mean'),
            median_pps = ('price_per_sqm', 'median')
        ).reset_index()
    )
    return g[g['transactions'] >= min_n]

def geo_coverage(df: pd.DataFrame):
    n = len(df)
    return {
        'n': n,
        'pct_geocoded': 100 * df['lat'].notna().mean() if n else 0,
        'pct_zone_id': 100 * df['zone_id'].notna().mean() if n else 0,
        'pct_to_mrt': 100 * df['to_mrt'].notna().mean() if n else 0,
        'pct_to_city': 100 * df['to_city'].notna().mean() if n else 0,
        'median_to_mrt': float(df['to_mrt'].median()),
        'median_to_city': float(df['to_city'].median())
    }
