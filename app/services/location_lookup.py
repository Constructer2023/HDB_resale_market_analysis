from __future__ import annotations
from functools import lru_cache
from pathlib import Path
from typing import Any
import pandas as pd

project_root = Path(__file__).resolve().parents[2]
aid_dir = project_root / 'data' / 'aid'
cache_path = aid_dir / 'hdb_geocode_cache.csv'
trx_geo_path = aid_dir / 'resale_trx_geo.csv'

location_feature_candidates = [
    'lat', 'lon', 'postal', 'subzone', 'zone_id',
    'nearest_mrt', 'mrt_lat', 'mrt_lon', 'to_mrt', 'to_city'
    ]

def _norm(s: Any):
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return ''
    return str(s).strip()

@lru_cache(maxsize = 1)
def load_geocode_cache():
    df = pd.read_csv(cache_path, low_memory = False)
    df['blk'] = df['blk'].map(_norm)
    df['st'] = df['st'].map(_norm)
    df = df[df['blk'].ne('') & df['st'].ne('')].copy()
    return df.reset_index(drop = True)

@lru_cache(maxsize = 1)
def load_transactions_geo():
    df = pd.read_csv(trx_geo_path, low_memory = False)
    df['blk'] = df['blk'].map(_norm)
    df['st'] = df['st'].map(_norm)
    return df

def list_streets():
    cache = load_geocode_cache()
    streets = sorted(cache['st'].dropna().unique().tolist())
    return [s for s in streets if s]

def list_blocks(street: str):
    cache = load_geocode_cache()
    st = _norm(street)
    blocks = cache.loc[cache['st'] == st, 'blk'].dropna().unique().tolist()
    return sorted(blocks, key = lambda x: (len(x), x))

def lookup_location(street: str, block: str):
    cache = load_geocode_cache()
    st, blk = _norm(street), _norm(block)
    hit = cache[(cache['st'] == st) & (cache['blk'] == blk)]
    if hit.empty:
        raise KeyError(f'Address not in geocode cache: blk = {blk!r} st = {st!r}')
    row = hit.iloc[0]
    if pd.isna(row.get('lat')) or pd.isna(row.get('lon')):
        raise KeyError(f'Address has no coordinates: blk = {blk!r} st = {st!r}')
    out: dict[str, Any] = {'blk': blk, 'st': st}
    for col in location_feature_candidates:
        if col in hit.columns:
            val = row[col]
            out[col] = None if pd.isna(val) else val
    return out

def unique_values(column: str, min_count: int = 1):
    trx = load_transactions_geo()
    trx.rename(columns = {'storey_midpoint': 'storey_range'}, inplace = True)
    if column not in trx.columns:
        return []
    vc = trx[column].dropna().astype(str).str.strip()
    vc = vc[vc.ne('')]
    counts = vc.value_counts()
    vals = counts[counts >= min_count].index.tolist()
    return sorted(vals)

def storey_options():
    trx = load_transactions_geo()
    trx.rename(columns = {'storey_midpoint': 'storey_range'}, inplace = True)
    return unique_values('storey_range')

def remaining_lease_to_months(value: Any):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        raise ValueError('Remaining lease is required.')
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        v = float(value)
        if v <= 0:
            raise ValueError('Remaining lease must be > 0.')
        if v <= 99:
            return int(round(v * 12))
        return int(round(v))
    return None
